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


# チェック項目の総数
_NUM_CHECKS = 5


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
    ) -> BearVerdict:
        """
        シグナルに対する反対論拠を検証する。

        Args:
            data: OHLCV形式のDataFrame
            signal: BUY/SELL/HOLDシグナル
            regime: RegimeInfoオブジェクト（オプション）

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

        # --- 5つのチェック実行 ---
        divergence = self._check_divergence(data, is_buy)
        if divergence:
            risk_factors.append(divergence)

        sr_risk = self._check_support_resistance(data, is_buy)
        if sr_risk:
            risk_factors.append(sr_risk)

        htf_risk = self._check_higher_timeframe(data, is_buy)
        if htf_risk:
            risk_factors.append(htf_risk)

        vol_risk = self._check_volume_confirmation(data, is_buy)
        if vol_risk:
            risk_factors.append(vol_risk)

        bb_risk = self._check_bb_squeeze(data)
        if bb_risk:
            risk_factors.append(bb_risk)

        # --- severity / penalty 計算 ---
        severity = len(risk_factors) / _NUM_CHECKS
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
            "Bear Researcher: %sシグナル → リスク%d/%d件 severity=%.1f penalty=%.2f",
            signal.value,
            len(risk_factors),
            _NUM_CHECKS,
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

    def _check_divergence(self, data: pd.DataFrame, is_buy: bool) -> Optional[str]:
        """
        ダイバージェンス検出: 価格とRSIの方向が乖離しているか。

        直近N本の最初と最後で価格・RSIの方向を比較する。
        """
        lookback = BEAR_DIVERGENCE_LOOKBACK
        rsi = ta.rsi(data["close"], length=RSI_PERIOD)
        if rsi is None or len(rsi) < lookback:
            return None

        # 直近lookback本の価格とRSIを取得
        recent_close = data["close"].iloc[-lookback:]
        recent_rsi = rsi.iloc[-lookback:]

        # NaN含む場合はスキップ
        if recent_rsi.isna().any():
            return None

        price_change = float(recent_close.iloc[-1] - recent_close.iloc[0])
        rsi_change = float(recent_rsi.iloc[-1] - recent_rsi.iloc[0])

        if is_buy:
            # BUYシグナル: 価格上昇 + RSI下降 → bearish divergence
            if price_change > 0 and rsi_change < 0:
                return "ベアリッシュ・ダイバージェンス（価格↑+RSI↓）"
        else:
            # SELLシグナル: 価格下降 + RSI上昇 → bullish divergence
            if price_change < 0 and rsi_change > 0:
                return "ブリッシュ・ダイバージェンス（価格↓+RSI↑）"

        return None

    def _check_support_resistance(
        self, data: pd.DataFrame, is_buy: bool
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

        # ATRを距離の基準に使う
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
        self, data: pd.DataFrame, is_buy: bool
    ) -> Optional[str]:
        """
        上位足矛盾: MA長期（50期間）の傾きがシグナル方向と逆か。
        """
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
        self, data: pd.DataFrame, is_buy: bool
    ) -> Optional[str]:
        """
        ボリューム不支持: MFIが中立帯(40-60)にある場合、
        資金フローが方向性を支持していない。
        """
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

    def _check_bb_squeeze(self, data: pd.DataFrame) -> Optional[str]:
        """
        BBスクイーズ直後: BBW/平均BBWがREGIME_BBW_SQUEEZE_RATIO未満の場合、
        ブレイクアウト方向が不確実。
        """
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
