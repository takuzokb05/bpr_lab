"""
FX自動取引システム — Bear Researcher（逆張り検証）モジュール

TradingAgents (Bull/Bear対立) + @loopdom（AI-native fund構築者）の設計思想に基づく。
conviction score生成後に「このトレードが失敗する理由」を
テクニカル指標から検証し、見落としたリスクを検出する。

LLMは使わない（コスト/レイテンシ回避）。
Phase 3 追加。
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd
import pandas_ta as ta

from src.config import (
    ATR_PERIOD,
    BEAR_DIVERGENCE_LOOKBACK,
    BEAR_MAX_PENALTY,
    BEAR_SEVERITY_THRESHOLD,
    BEAR_SR_ATR_MULTIPLIER,
    MA_LONG_PERIOD,
    MFI_PERIOD,
    REGIME_BBW_SQUEEZE_RATIO,
    RSI_PERIOD,
)
from src.strategy.base import Signal

logger = logging.getLogger(__name__)


@dataclass
class BearVerdict:
    """Bear Researcherの検証結果"""

    risk_factors: list[str] = field(default_factory=list)
    severity: float = 0.0                # 0.0-1.0 リスク深刻度（検出数/チェック項目数）
    penalty_multiplier: float = 1.0      # conviction倍率への減点 (0.5-1.0)
    reasoning: str = ""                  # 判定理由（日本語）


# 監査P1-#4: チェック項目の重み付け（合計 1.0）
# 旧実装は等価カウント (severity = len(risks) / 5) で「上位足矛盾(重大)」と
# 「MFI 中立帯(軽微)」が同じ 0.2 寄与だった。ここでは「シグナル方向と直接
# 矛盾する根拠ほど重く」をルールに重み付けする。
#
# 設計根拠:
# - higher_timeframe (上位足矛盾): MA200 がシグナル方向と逆 → 最強の反対論拠 → 0.35
# - divergence (ダイバージェンス): 価格と RSI 乖離 → 反転の典型サイン → 0.25
# - support_resistance (サポレジ接近): 上値/下値余地少ない → 直接の利食い障害 → 0.20
# - bb_squeeze (BB スクイーズ): ブレイク方向不確実 → 軽い → 0.15
# - volume_confirmation (MFI 中立帯): 単に "支持薄" であって直接矛盾ではない → 0.05
_RISK_WEIGHTS: dict[str, float] = {
    "higher_timeframe": 0.35,
    "divergence": 0.25,
    "support_resistance": 0.20,
    "bb_squeeze": 0.15,
    "volume_confirmation": 0.05,
}


class BearResearcher:
    """
    テクニカル指標からシグナルの反対論拠を構築する。

    チェック項目（5つ）:
    1. ダイバージェンス: 価格↑+RSI↓ = bearish divergence（またはその逆）
    2. サポレジ接近: 買いシグナルだがレジスタンスに近い（ATRの1.5倍以内）
    3. 上位足矛盾: MA長期(50)の傾きがシグナル方向と逆
    4. ボリューム不支持: MFIが中立帯(40-60)にある（確信が持てない）
    5. BBスクイーズ直後: BBW比率が低い（ブレイクアウト方向の不確実性）
    """

    def verify(
        self,
        data: pd.DataFrame,
        signal: Signal,
        regime: Optional[Any] = None,
        indicators: dict | None = None,
    ) -> BearVerdict:
        """
        シグナルに対する反対論拠を検証する。

        Args:
            data: OHLCV形式のDataFrame
            signal: BUY/SELL/HOLDシグナル
            regime: RegimeInfoオブジェクト（オプション）
            indicators: IndicatorCache辞書（キャッシュがあればpandas_ta計算をスキップ）

        Returns:
            BearVerdict: 検証結果
        """
        # HOLDシグナルの場合はリスク0で即返却
        if signal == Signal.HOLD:
            return BearVerdict(
                risk_factors=[],
                severity=0.0,
                penalty_multiplier=1.0,
                reasoning="HOLDシグナルのため検証不要",
            )

        # データ不足の場合はデフォルト（リスク0）
        min_rows = max(MA_LONG_PERIOD, 20) + 5  # MA50 + サポレジ20 + 余裕
        if len(data) < min_rows:
            logger.warning(
                "Bear Researcher: データ不足（%d行 < 必要%d行）。デフォルト返却。",
                len(data),
                min_rows,
            )
            return BearVerdict(
                risk_factors=[],
                severity=0.0,
                penalty_multiplier=1.0,
                reasoning=f"データ不足（{len(data)}行 < 必要{min_rows}行）のため検証スキップ",
            )

        is_buy = signal == Signal.BUY
        risk_factors: list[str] = []
        # 監査P1-#4: 発火したチェック ID を保持して重み付け severity を算出
        fired_checks: list[str] = []

        # --- 5つのチェック実行（指標キャッシュを各チェックに渡す） ---
        divergence = self._check_divergence(data, is_buy, indicators=indicators)
        if divergence:
            risk_factors.append(divergence)
            fired_checks.append("divergence")

        sr_risk = self._check_support_resistance(data, is_buy, indicators=indicators)
        if sr_risk:
            risk_factors.append(sr_risk)
            fired_checks.append("support_resistance")

        htf_risk = self._check_higher_timeframe(data, is_buy, indicators=indicators)
        if htf_risk:
            risk_factors.append(htf_risk)
            fired_checks.append("higher_timeframe")

        vol_risk = self._check_volume_confirmation(data, is_buy, indicators=indicators)
        if vol_risk:
            risk_factors.append(vol_risk)
            fired_checks.append("volume_confirmation")

        bb_risk = self._check_bb_squeeze(data, indicators=indicators)
        if bb_risk:
            risk_factors.append(bb_risk)
            fired_checks.append("bb_squeeze")

        # --- severity / penalty 計算（監査P1-#4: 重み付け化） ---
        severity = sum(_RISK_WEIGHTS.get(name, 0.0) for name in fired_checks)
        # 0..1 にクランプ（重み合計が 1.0 設計だが将来的な追加に対する保険）
        severity = min(1.0, max(0.0, severity))
        penalty_multiplier = max(BEAR_MAX_PENALTY, 1.0 - severity * 0.5)

        # 判定理由の組み立て
        direction_str = "買い" if is_buy else "売り"
        if risk_factors:
            reasoning = (
                f"{direction_str}シグナルに対し{len(risk_factors)}件のリスク検出: "
                f"{'; '.join(risk_factors)}。"
                f"severity={severity:.1f}, penalty={penalty_multiplier:.2f}"
            )
        else:
            reasoning = f"{direction_str}シグナルに対する反対論拠なし。conviction維持。"

        logger.info(
            "Bear Researcher: %sシグナル → リスク%d/%d件 fired=%s severity=%.2f penalty=%.2f",
            signal.value,
            len(risk_factors),
            len(_RISK_WEIGHTS),
            ",".join(fired_checks) if fired_checks else "-",
            severity,
            penalty_multiplier,
        )

        return BearVerdict(
            risk_factors=risk_factors,
            severity=severity,
            penalty_multiplier=penalty_multiplier,
            reasoning=reasoning,
        )

    # ================================================================
    # チェック項目の実装
    # ================================================================

    def _check_divergence(
        self, data: pd.DataFrame, is_buy: bool, indicators: dict | None = None,
    ) -> Optional[str]:
        """
        ダイバージェンス検出（監査P1-#5: ピーク/トラフ検出ベースに刷新）

        旧実装: 直近 N 本の **最初と最後だけ**で方向比較 → 短期ノイズで誤検出多発
        新実装: scipy.signal.find_peaks で直近 ~3×lookback 本のピーク/トラフを
        検出し、**直近2つのピーク（SELL想定）or トラフ（BUY想定）**を比較。

        - BUYシグナル想定の bearish divergence:
          直近の高値 > 前回の高値 だが、対応する RSI 高値 < 前回の RSI 高値
          → 価格は上昇継続するも勢いが減衰 = 反転の典型サイン
        - SELLシグナル想定の bullish divergence:
          直近の安値 < 前回の安値 だが、対応する RSI 安値 > 前回の RSI 安値
        """
        from scipy.signal import find_peaks  # local import: scipy は既に依存

        lookback = BEAR_DIVERGENCE_LOOKBACK
        window = max(lookback * 3, 30)  # ピーク2つ取れる程度の窓

        if indicators is not None and indicators.get("rsi") is not None:
            rsi = indicators["rsi"]
        else:
            rsi = ta.rsi(data["close"], length=RSI_PERIOD)
        if rsi is None or len(rsi) < window:
            return None

        recent_close = data["close"].iloc[-window:].to_numpy()
        recent_rsi = rsi.iloc[-window:].to_numpy()

        # NaN を含む位置は除外（ピーク検出が破綻する）
        valid_mask = ~(pd.isna(recent_close) | pd.isna(recent_rsi))
        if valid_mask.sum() < 10:
            return None

        # ピーク/トラフの最低距離 = lookback 本（同じピークを二重検出しない）
        if is_buy:
            # BUY 想定 → bearish divergence (価格高値↑, RSI高値↓)
            peaks_p, _ = find_peaks(recent_close, distance=lookback)
            peaks_r, _ = find_peaks(recent_rsi, distance=lookback)
            if len(peaks_p) < 2 or len(peaks_r) < 2:
                return None
            p_last, p_prev = peaks_p[-1], peaks_p[-2]
            r_last, r_prev = peaks_r[-1], peaks_r[-2]
            if (
                recent_close[p_last] > recent_close[p_prev]
                and recent_rsi[r_last] < recent_rsi[r_prev]
            ):
                return (
                    f"ベアリッシュ・ダイバージェンス（価格高値"
                    f"{recent_close[p_prev]:.5f}→{recent_close[p_last]:.5f}↑、"
                    f"RSI高値{recent_rsi[r_prev]:.1f}→{recent_rsi[r_last]:.1f}↓）"
                )
        else:
            # SELL 想定 → bullish divergence (価格安値↓, RSI安値↑)
            troughs_p, _ = find_peaks(-recent_close, distance=lookback)
            troughs_r, _ = find_peaks(-recent_rsi, distance=lookback)
            if len(troughs_p) < 2 or len(troughs_r) < 2:
                return None
            p_last, p_prev = troughs_p[-1], troughs_p[-2]
            r_last, r_prev = troughs_r[-1], troughs_r[-2]
            if (
                recent_close[p_last] < recent_close[p_prev]
                and recent_rsi[r_last] > recent_rsi[r_prev]
            ):
                return (
                    f"ブリッシュ・ダイバージェンス（価格安値"
                    f"{recent_close[p_prev]:.5f}→{recent_close[p_last]:.5f}↓、"
                    f"RSI安値{recent_rsi[r_prev]:.1f}→{recent_rsi[r_last]:.1f}↑）"
                )
        return None

    def _check_support_resistance(
        self, data: pd.DataFrame, is_buy: bool, indicators: dict | None = None
    ) -> Optional[str]:
        """
        サポレジ接近: 直近20本の高値/安値からサポレジを推定し、
        現在価格が近すぎないかチェックする。
        """
        lookback = 20
        if len(data) < lookback:
            return None

        recent = data.iloc[-lookback:]
        resistance = float(recent["high"].max())
        support = float(recent["low"].min())
        current_price = float(data["close"].iloc[-1])

        # ATRを距離の基準に使う（キャッシュ優先）
        if indicators is not None and indicators.get("atr") is not None:
            atr = indicators["atr"]
        else:
            atr = ta.atr(data["high"], data["low"], data["close"], length=ATR_PERIOD)
        if atr is None:
            return None

        current_atr = atr.iloc[-1]
        if pd.isna(current_atr) or current_atr == 0:
            return None

        threshold = float(current_atr) * BEAR_SR_ATR_MULTIPLIER

        if is_buy:
            # 買い: レジスタンスに近い → 上値余地が少ない
            distance_to_resistance = resistance - current_price
            if 0 <= distance_to_resistance <= threshold:
                return (
                    f"レジスタンス接近（現在値{current_price:.5f}、"
                    f"レジスタンス{resistance:.5f}、距離{distance_to_resistance:.5f} < ATR×{BEAR_SR_ATR_MULTIPLIER}）"
                )
        else:
            # 売り: サポートに近い → 下値余地が少ない
            distance_to_support = current_price - support
            if 0 <= distance_to_support <= threshold:
                return (
                    f"サポート接近（現在値{current_price:.5f}、"
                    f"サポート{support:.5f}、距離{distance_to_support:.5f} < ATR×{BEAR_SR_ATR_MULTIPLIER}）"
                )

        return None

    def _check_higher_timeframe(
        self, data: pd.DataFrame, is_buy: bool, indicators: dict | None = None
    ) -> Optional[str]:
        """
        上位足矛盾: MA長期（50期間）の傾きがシグナル方向と逆か。
        """
        # キャッシュからMA長期を取得（あればpandas_ta計算をスキップ）
        if indicators is not None and indicators.get("ma_long") is not None:
            ma_long = indicators["ma_long"]
        else:
            ma_long = ta.sma(data["close"], length=MA_LONG_PERIOD)
        if ma_long is None or len(ma_long) < 2:
            return None

        current = ma_long.iloc[-1]
        prev = ma_long.iloc[-2]

        if pd.isna(current) or pd.isna(prev):
            return None

        slope = float(current - prev)

        if is_buy and slope < 0:
            return f"MA{MA_LONG_PERIOD}が下降中（傾き{slope:.6f}）に買いシグナル"
        elif not is_buy and slope > 0:
            return f"MA{MA_LONG_PERIOD}が上昇中（傾き{slope:.6f}）に売りシグナル"

        return None

    def _check_volume_confirmation(
        self, data: pd.DataFrame, is_buy: bool, indicators: dict | None = None
    ) -> Optional[str]:
        """
        ボリューム不支持: MFIが中立帯(40-60)にある場合、
        資金フローが方向性を支持していない。
        """
        # キャッシュからcurrent_mfiを取得（あればpandas_ta計算をスキップ）
        if indicators is not None and indicators.get("current_mfi") is not None:
            current_mfi = indicators["current_mfi"]
        else:
            # volume列がない場合はスキップ（リスクとしてカウントしない）
            if "volume" not in data.columns:
                return None

            mfi = ta.mfi(
                data["high"], data["low"], data["close"], data["volume"],
                length=MFI_PERIOD,
            )
            if mfi is None:
                return None

            current_mfi = mfi.iloc[-1]
        if pd.isna(current_mfi):
            return None

        if 40 <= current_mfi <= 60:
            return f"MFI中立帯（{current_mfi:.1f}）で資金フローが方向性を支持していない"

        return None

    def _check_bb_squeeze(self, data: pd.DataFrame, indicators: dict | None = None) -> Optional[str]:
        """
        BBスクイーズ直後: BBW/平均BBWがREGIME_BBW_SQUEEZE_RATIO未満の場合、
        ブレイクアウト方向が不確実。
        """
        # キャッシュからbbw_ratioを取得（あればpandas_ta計算をスキップ）
        if indicators is not None and indicators.get("bbw_ratio") is not None:
            bbw_ratio = indicators["bbw_ratio"]
        else:
            bbands = ta.bbands(data["close"], length=20, std=2.0)
            if bbands is None:
                return None

            # BBW（Bandwidth）列を探す
            bbw_col = "BBB_20_2.0"
            if bbw_col not in bbands.columns:
                bbw_candidates = [c for c in bbands.columns if c.startswith("BBB_")]
                if not bbw_candidates:
                    return None
                bbw_col = bbw_candidates[0]

            bbw = bbands[bbw_col].dropna()
            if len(bbw) < 2:
                return None

            current_bbw = float(bbw.iloc[-1])
            mean_bbw = float(bbw.mean())

            if mean_bbw == 0:
                return None

            bbw_ratio = current_bbw / mean_bbw

        if bbw_ratio < REGIME_BBW_SQUEEZE_RATIO:
            return (
                f"BBスクイーズ検出（BBW比率{bbw_ratio:.2f} < "
                f"閾値{REGIME_BBW_SQUEEZE_RATIO}）、ブレイクアウト方向が不確実"
            )

        return None
