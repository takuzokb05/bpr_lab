"""
確信度スコア（Conviction Score）モジュール

複数のテクニカル指標の「合流」（confluence）度合いからスコアを計算し、
ポジションサイズの調整判断を行う。

@loopdom（AI-native fund構築者）の設計思想に基づく:
- 各トレードに conviction score (1-10) を付与
- スコアに応じてポジションサイズを調整
- テクニカル指標の合流度合いでスコア計算

Phase 3 追加。
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd
import pandas_ta as ta

from src.config import (
    ADX_PERIOD,
    MA_LONG_PERIOD,
    MIN_CONVICTION_SCORE,
    MFI_PERIOD,
    RSI_PERIOD,
)
from src.strategy.base import Signal

logger = logging.getLogger(__name__)


@dataclass
class ConvictionResult:
    """確信度スコアの計算結果"""

    score: int  # 1-10
    position_size_multiplier: float  # ポジションサイズ倍率
    components: dict  # 各要素の得点内訳
    reasoning: str  # 判定理由（日本語）
    should_trade: bool  # スコア >= MIN_CONVICTION_SCORE


class ConvictionScorer:
    """
    テクニカル指標の合流度合いから確信度スコアを計算する。

    スコアリングロジック（10点満点）:
    - トレンド一致: シグナル方向とMA長期の傾きが一致 (0-2)
    - ADX強度: トレンドの強さ (0-2)
    - RSI位置: 適切なRSI水準 (0-2)
    - MFI確認: シグナル方向とMFIの一致 (0-2)
    - レジーム: 市場環境 (0-2)
    """

    def score(
        self,
        data: pd.DataFrame,
        signal: Signal,
        regime: Optional[Any] = None,
        indicators: dict | None = None,
    ) -> ConvictionResult:
        """
        テクニカル指標の合流度合いからconviction scoreを計算する。

        Args:
            data: OHLCV形式のDataFrame（high, low, close, volume列が必要）
            signal: 取引シグナル（BUY/SELL/HOLD）
            regime: RegimeInfo オブジェクト（未実装の場合はNone）。
                    regime.regime 属性に "TRENDING" / "RANGING" / "UNKNOWN" を期待する。
            indicators: IndicatorCache辞書（キャッシュがあればpandas_ta計算をスキップ）

        Returns:
            ConvictionResult: スコア・倍率・内訳・理由・トレード可否
        """
        components: dict[str, int] = {}
        reasons: list[str] = []

        # HOLDシグナルの場合はスコア0で即返却
        if signal == Signal.HOLD:
            return ConvictionResult(
                score=1,
                position_size_multiplier=0.0,
                components={"trend": 0, "adx": 0, "rsi": 0, "mfi": 0, "regime": 0},
                reasoning="シグナルがHOLDのため見送り",
                should_trade=False,
            )

        is_buy = signal == Signal.BUY

        # --- 1. トレンド一致（0-2） ---
        trend_score = self._score_trend(data, is_buy, indicators=indicators)
        components["trend"] = trend_score
        if trend_score == 2:
            reasons.append("MA長期の傾きがシグナル方向と一致")
        elif trend_score == 1:
            reasons.append("MA長期の傾きがほぼ横ばい")
        else:
            reasons.append("MA長期の傾きがシグナル方向と逆行")

        # --- 2. ADX強度（0-2） ---
        adx_score = self._score_adx(data, indicators=indicators)
        components["adx"] = adx_score
        if adx_score == 2:
            reasons.append("ADX強（トレンド明確）")
        elif adx_score == 1:
            reasons.append("ADX中程度")
        else:
            reasons.append("ADX弱（トレンド不明瞭）")

        # --- 3. RSI位置（0-2） ---
        rsi_score = self._score_rsi(data, is_buy, indicators=indicators)
        components["rsi"] = rsi_score
        if rsi_score == 2:
            reasons.append("RSIが理想的な水準")
        elif rsi_score == 1:
            reasons.append("RSIが許容範囲内")
        else:
            reasons.append("RSIが不適切な水準")

        # --- 4. MFI確認（0-2） ---
        mfi_score = self._score_mfi(data, is_buy, indicators=indicators)
        components["mfi"] = mfi_score
        if mfi_score == 2:
            reasons.append("MFIがシグナル方向を強く支持")
        elif mfi_score == 1:
            reasons.append("MFIが中立")
        else:
            reasons.append("MFIがシグナル方向と矛盾")

        # --- 5. レジーム（0-2） ---
        regime_score = self._score_regime(regime)
        components["regime"] = regime_score
        if regime_score == 2:
            reasons.append("トレンド相場")
        elif regime_score == 1:
            reasons.append("レジーム不明")
        else:
            reasons.append("レンジ相場")

        # 合計スコア（1-10にクランプ）
        raw_score = sum(components.values())
        final_score = max(1, min(10, raw_score))

        # ポジションサイズ倍率
        multiplier = self._calc_multiplier(final_score)

        # トレード可否
        should_trade = final_score >= MIN_CONVICTION_SCORE

        # 判定理由の組み立て
        direction_str = "買い" if is_buy else "売り"
        reasoning = (
            f"{direction_str}シグナル: 確信度{final_score}/10。"
            f"{', '.join(reasons)}。"
            f"{'エントリー実行' if should_trade else '確信度不足のため見送り'}（倍率{multiplier}x）"
        )

        logger.info(
            "確信度スコア: %d/10 (trend=%d, adx=%d, rsi=%d, mfi=%d, regime=%d) → 倍率%.1fx, %s",
            final_score,
            components["trend"],
            components["adx"],
            components["rsi"],
            components["mfi"],
            components["regime"],
            multiplier,
            "TRADE" if should_trade else "SKIP",
        )

        return ConvictionResult(
            score=final_score,
            position_size_multiplier=multiplier,
            components=components,
            reasoning=reasoning,
            should_trade=should_trade,
        )

    # 監査P0-#2: 「横ばい」判定の相対閾値（価格スケール非依存）。
    # 旧 1e-8 は USDJPY=156 で相対 6e-9 % 未満を要求しており、float精度的に
    # 実現不可能 → 「横ばい(=1点)」が永遠に出ず、is_buy 分岐が二択化していた。
    # 1バーあたり相対 0.001% 未満を「横ばい」とみなす（USDJPY=156 で slope<0.00156、
    # EURUSD=1.10 で slope<1.1e-5 相当）。
    _FLAT_SLOPE_REL = 1e-5

    def _score_trend(self, data: pd.DataFrame, is_buy: bool, indicators: dict | None = None) -> int:
        """トレンド一致スコア: シグナル方向とMA長期の傾きが一致するか"""
        # キャッシュからMA長期を取得（あればpandas_ta計算をスキップ）
        if indicators is not None and indicators.get("ma_long") is not None:
            ma_long = indicators["ma_long"]
        else:
            ma_long = ta.sma(data["close"], length=MA_LONG_PERIOD)
        if ma_long is None or len(ma_long) < 2:
            return 0

        current = ma_long.iloc[-1]
        prev = ma_long.iloc[-2]

        if pd.isna(current) or pd.isna(prev):
            return 0

        slope = current - prev
        flat_threshold = abs(current) * self._FLAT_SLOPE_REL

        # 買いならMAが上向き、売りならMAが下向きで一致
        if is_buy:
            if slope > flat_threshold:
                return 2  # 一致
            elif abs(slope) <= flat_threshold:
                return 1  # 横ばい
            else:
                return 0  # 逆行
        else:
            if slope < -flat_threshold:
                return 2  # 一致
            elif abs(slope) <= flat_threshold:
                return 1  # 横ばい
            else:
                return 0  # 逆行

    def _score_adx(self, data: pd.DataFrame, indicators: dict | None = None) -> int:
        """ADX強度スコア: ADX >= 30 → 2, >= 25 → 1, < 25 → 0"""
        # キャッシュからcurrent_adxを取得（あればpandas_ta計算をスキップ）
        if indicators is not None and indicators.get("current_adx") is not None:
            current_adx = indicators["current_adx"]
        else:
            adx_df = ta.adx(data["high"], data["low"], data["close"], length=ADX_PERIOD)
            if adx_df is None:
                return 0

            adx_col = f"ADX_{ADX_PERIOD}"
            if adx_col not in adx_df.columns:
                return 0

            current_adx = adx_df[adx_col].iloc[-1]
        if pd.isna(current_adx):
            return 0

        if current_adx >= 30:
            return 2
        elif current_adx >= 25:
            return 1
        else:
            return 0

    def _score_rsi(self, data: pd.DataFrame, is_buy: bool, indicators: dict | None = None) -> int:
        """
        RSI位置スコア（監査P0-#1: BUY/SELL を非対称化）

        本番戦略 (MTFPullback / BollingerReversal) は平均回帰系で、
        BUY を RSI<35（売られすぎ）、SELL を RSI>65（買われすぎ）で発火させる。
        旧実装は BUY/SELL 同じ「40-60=2点, 30-70=1点」で `is_buy` 分岐が
        意味を持たず、戦略の発火直後 RSI=33 は常に 1点しか取れなかった。

        修正後: 戦略エントリー方向に対する「平均回帰の早期段階か」を評価する:
        - BUY: RSI 25-50（売られすぎ〜中立）= 2点。20-60 = 1点。
        - SELL: RSI 50-75（中立〜買われすぎ）= 2点。40-80 = 1点。
        """
        # キャッシュからcurrent_rsiを取得（あればpandas_ta計算をスキップ）
        if indicators is not None and indicators.get("current_rsi") is not None:
            current_rsi = indicators["current_rsi"]
        else:
            rsi = ta.rsi(data["close"], length=RSI_PERIOD)
            if rsi is None:
                return 0

            current_rsi = rsi.iloc[-1]
        if pd.isna(current_rsi):
            return 0

        if is_buy:
            # 買い: 売られすぎ〜中立帯にあれば「平均回帰の初動」として評価
            if 25 <= current_rsi <= 50:
                return 2
            elif 20 <= current_rsi <= 60:
                return 1
            else:
                return 0
        else:
            # 売り: 買われすぎ〜中立帯にあれば「平均回帰の初動」として評価
            if 50 <= current_rsi <= 75:
                return 2
            elif 40 <= current_rsi <= 80:
                return 1
            else:
                return 0

    def _score_mfi(self, data: pd.DataFrame, is_buy: bool, indicators: dict | None = None) -> int:
        """
        MFI確認スコア: シグナル方向とMFIが一致するか
        - 買い: MFI < 40 → 2（資金流入余地大）, 40-60 → 1, > 60 → 0
        - 売り: MFI > 60 → 2（資金流出余地大）, 40-60 → 1, < 40 → 0
        """
        # キャッシュからcurrent_mfiを取得（あればpandas_ta計算をスキップ）
        if indicators is not None and indicators.get("current_mfi") is not None:
            current_mfi = indicators["current_mfi"]
        else:
            # volume列がない場合はデフォルト1点
            if "volume" not in data.columns:
                return 1

            mfi = ta.mfi(data["high"], data["low"], data["close"], data["volume"], length=MFI_PERIOD)
            if mfi is None:
                return 1

            current_mfi = mfi.iloc[-1]
        if pd.isna(current_mfi):
            return 1

        if is_buy:
            if current_mfi < 40:
                return 2  # 資金流入余地大
            elif current_mfi <= 60:
                return 1  # 中立
            else:
                return 0  # 既に買われすぎ
        else:
            if current_mfi > 60:
                return 2  # 資金流出余地大
            elif current_mfi >= 40:
                return 1  # 中立
            else:
                return 0  # 既に売られすぎ

    def _score_regime(self, regime: Optional[Any]) -> int:
        """
        レジームスコア: TRENDING → 2, UNKNOWN → 1, RANGING → 0

        regime_detector.py が未実装の場合はNoneが渡されるため、デフォルト1を返す。
        """
        if regime is None:
            return 1

        # RegimeInfo.regime 属性を参照
        regime_value = getattr(regime, "regime", None)
        if regime_value is None:
            return 1

        # 文字列比較（enum.value でも .name でも対応）
        regime_str = str(regime_value).upper()
        if "TRENDING" in regime_str:
            return 2
        elif "RANGING" in regime_str:
            return 0
        else:
            return 1

    @staticmethod
    def _calc_multiplier(score: int) -> float:
        """
        スコアからポジションサイズ倍率を算出する。

        - score >= 8 → 1.5（高確信、ポジション1.5倍）
        - score >= 7 → 1.0（標準サイズ）
        - score >= 5 → 0.5（半分サイズ）
        - score >= 4 → 0.3（最小サイズ）
        - score < 4 → 0.0（見送り）
        """
        if score >= 8:
            return 1.5
        elif score >= 7:
            return 1.0
        elif score >= 5:
            return 0.5
        elif score >= 4:
            return 0.3
        else:
            return 0.0
