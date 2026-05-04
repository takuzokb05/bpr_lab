"""
FX自動取引システム — レジーム検出モジュール

市場をトレンド/レンジ/高ボラティリティの3レジームに分類し、
レジームに応じたエクスポージャー倍率を算出する。
@loopdom（AI-native fund構築者）の設計思想に基づく。

Phase 3 追加。
"""

import enum
import logging
from dataclasses import dataclass

import pandas as pd
import pandas_ta as ta

from src.config import (
    ADX_PERIOD,
    ATR_PERIOD,
    REGIME_ADX_RANGING,
    REGIME_ADX_TRENDING,
    REGIME_ATR_VOLATILE_RATIO,
    REGIME_BBW_SQUEEZE_RATIO,
)

logger = logging.getLogger(__name__)


class RegimeType(enum.Enum):
    """市場レジームの分類"""

    TRENDING = "trending"   # トレンド相場（MA crossoverが有効）
    RANGING = "ranging"     # レンジ相場（ダマシが多い、エクスポージャー縮小）
    VOLATILE = "volatile"   # 高ボラティリティ（キルスイッチ候補、取引停止）
    UNKNOWN = "unknown"     # 判定不能


@dataclass
class RegimeInfo:
    """レジーム判定結果"""

    regime: RegimeType
    confidence: float           # 0.0-1.0 判定の確信度
    adx: float                  # 現在ADX値
    atr_ratio: float            # ATR / 中央値ATR
    bbw_ratio: float            # BBW / 平均BBW
    exposure_multiplier: float  # 推奨エクスポージャー倍率
    reasoning: str              # 判定理由（日本語）


class RegimeDetector:
    """
    市場レジーム検出器

    ADX・ATR・ボリンジャーバンド幅の3指標を組み合わせて
    現在の市場レジームを判定し、推奨エクスポージャー倍率を返す。

    判定ロジック:
      1. ATR変化率 > REGIME_ATR_VOLATILE_RATIO → VOLATILE（最優先）
      2. ADX >= REGIME_ADX_TRENDING → TRENDING
      3. ADX < REGIME_ADX_RANGING → RANGING
      4. グレーゾーン（RANGING <= ADX < TRENDING）→ BBW で補助判定
    """

    def __init__(
        self,
        adx_period: int = ADX_PERIOD,
        atr_period: int = ATR_PERIOD,
        bb_length: int = 20,
        bb_std: float = 2.0,
    ) -> None:
        """
        Args:
            adx_period: ADX計算期間
            atr_period: ATR計算期間
            bb_length: ボリンジャーバンドの期間
            bb_std: ボリンジャーバンドの標準偏差倍率
        """
        self._adx_period = adx_period
        self._atr_period = atr_period
        self._bb_length = bb_length
        self._bb_std = bb_std

    def detect(
        self,
        data: pd.DataFrame,
        indicators: dict | None = None,
        pair_config: dict | None = None,
    ) -> RegimeInfo:
        """
        OHLCVデータからレジームを判定する。

        Args:
            data: OHLCV形式のDataFrame（high, low, close列が必須）
            indicators: IndicatorCache辞書（キャッシュがあればpandas_ta計算をスキップ）
            pair_config: ペア別設定。次のキーで閾値をオーバーライド可能:
                - regime_adx_trending: ADXトレンド判定閾値（未指定時 REGIME_ADX_TRENDING）
                - regime_adx_ranging: ADXレンジ判定閾値（未指定時 REGIME_ADX_RANGING）
                - regime_atr_volatile_ratio: ATRボラティリティ閾値（未指定時 REGIME_ATR_VOLATILE_RATIO）
                - regime_bbw_squeeze_ratio: BBWスクイーズ閾値（未指定時 REGIME_BBW_SQUEEZE_RATIO）

        Returns:
            RegimeInfo: 判定結果
        """
        # 監査A4: pair_config が与えられたらペア別閾値を優先、なければ全ペア共通の
        # config.py グローバル値を使う。これによりペア別 ADX 基準を尊重しつつ
        # 後方互換性を保つ。
        cfg = pair_config or {}
        adx_trending = cfg.get("regime_adx_trending", REGIME_ADX_TRENDING)
        adx_ranging = cfg.get("regime_adx_ranging", REGIME_ADX_RANGING)
        atr_volatile_ratio = cfg.get("regime_atr_volatile_ratio", REGIME_ATR_VOLATILE_RATIO)
        bbw_squeeze_ratio = cfg.get("regime_bbw_squeeze_ratio", REGIME_BBW_SQUEEZE_RATIO)

        # 必要な最小データ数（各指標の計算に十分な行数）
        min_rows = max(self._adx_period, self._atr_period, self._bb_length) * 2
        if len(data) < min_rows:
            logger.warning(
                "データ行数が不足しています（%d行 < 必要最低%d行）。UNKNOWNを返します。",
                len(data),
                min_rows,
            )
            return RegimeInfo(
                regime=RegimeType.UNKNOWN,
                confidence=0.0,
                adx=0.0,
                atr_ratio=0.0,
                bbw_ratio=0.0,
                exposure_multiplier=0.5,
                reasoning=f"データ不足（{len(data)}行 < 必要{min_rows}行）",
            )

        # --- ADX 計算（キャッシュ優先） ---
        if indicators is not None and indicators.get("current_adx") is not None:
            adx_value = indicators["current_adx"]
        else:
            adx_value = self._calc_adx(data)
        if adx_value is None:
            return self._unknown_result("ADX計算に失敗")

        # --- ATR 計算 + 変化率（キャッシュ優先） ---
        if indicators is not None and indicators.get("atr_ratio") is not None:
            atr_ratio = indicators["atr_ratio"]
        else:
            atr_ratio = self._calc_atr_ratio(data)
        if atr_ratio is None:
            return self._unknown_result("ATR計算に失敗")

        # --- BBW 計算 + 比率（キャッシュ優先） ---
        if indicators is not None and indicators.get("bbw_ratio") is not None:
            bbw_ratio = indicators["bbw_ratio"]
        else:
            bbw_ratio = self._calc_bbw_ratio(data)
        if bbw_ratio is None:
            return self._unknown_result("ボリンジャーバンド計算に失敗")

        # --- レジーム判定（優先度順） ---

        # 1. ボラティリティ判定（最優先）
        if atr_ratio > atr_volatile_ratio:
            confidence = min(1.0, (atr_ratio - atr_volatile_ratio) / 1.0 + 0.7)
            return RegimeInfo(
                regime=RegimeType.VOLATILE,
                confidence=confidence,
                adx=adx_value,
                atr_ratio=atr_ratio,
                bbw_ratio=bbw_ratio,
                exposure_multiplier=0.0,
                reasoning=(
                    f"異常ボラティリティ検出: ATR比率={atr_ratio:.2f}"
                    f"（閾値{atr_volatile_ratio}超）。取引停止推奨。"
                ),
            )

        # 2. ADX による明確なトレンド判定
        if adx_value >= adx_trending:
            confidence = min(1.0, (adx_value - adx_trending) / 15.0 + 0.7)
            multiplier = 1.2 if confidence > 0.7 else 1.0
            return RegimeInfo(
                regime=RegimeType.TRENDING,
                confidence=confidence,
                adx=adx_value,
                atr_ratio=atr_ratio,
                bbw_ratio=bbw_ratio,
                exposure_multiplier=multiplier,
                reasoning=(
                    f"トレンド相場: ADX={adx_value:.1f}"
                    f"（閾値{adx_trending}以上）。"
                    f"エクスポージャー倍率{multiplier}。"
                ),
            )

        # 3. ADX による明確なレンジ判定
        if adx_value < adx_ranging:
            confidence = min(1.0, (adx_ranging - adx_value) / 10.0 + 0.7)
            return RegimeInfo(
                regime=RegimeType.RANGING,
                confidence=confidence,
                adx=adx_value,
                atr_ratio=atr_ratio,
                bbw_ratio=bbw_ratio,
                exposure_multiplier=0.3,
                reasoning=(
                    f"レンジ相場: ADX={adx_value:.1f}"
                    f"（閾値{adx_ranging}未満）。"
                    "ダマシ回避のためエクスポージャー30%に縮小。"
                ),
            )

        # 4. グレーゾーン（adx_ranging <= ADX < adx_trending）→ BBW で補助判定
        if bbw_ratio < bbw_squeeze_ratio:
            # スクイーズ状態 → レンジ寄りと判断
            confidence = 0.5 + (bbw_squeeze_ratio - bbw_ratio) * 0.3
            confidence = min(1.0, max(0.3, confidence))
            return RegimeInfo(
                regime=RegimeType.RANGING,
                confidence=confidence,
                adx=adx_value,
                atr_ratio=atr_ratio,
                bbw_ratio=bbw_ratio,
                exposure_multiplier=0.3,
                reasoning=(
                    f"グレーゾーン→レンジ判定: ADX={adx_value:.1f}"
                    f"（{adx_ranging}〜{adx_trending}）、"
                    f"BBW比率={bbw_ratio:.2f}（スクイーズ閾値{bbw_squeeze_ratio}未満）。"
                    "ダマシ回避のためエクスポージャー30%に縮小。"
                ),
            )

        # グレーゾーン + BBWスクイーズなし → 弱トレンド
        adx_range = adx_trending - adx_ranging
        adx_position = (adx_value - adx_ranging) / adx_range if adx_range > 0 else 0.5
        confidence = 0.3 + adx_position * 0.3
        return RegimeInfo(
            regime=RegimeType.TRENDING,
            confidence=confidence,
            adx=adx_value,
            atr_ratio=atr_ratio,
            bbw_ratio=bbw_ratio,
            exposure_multiplier=1.0,
            reasoning=(
                f"グレーゾーン→弱トレンド判定: ADX={adx_value:.1f}"
                f"（{adx_ranging}〜{adx_trending}）、"
                f"BBW比率={bbw_ratio:.2f}（スクイーズなし）。"
                "確信度低のためエクスポージャー等倍。"
            ),
        )

    # ================================================================
    # 内部ヘルパー
    # ================================================================

    def _calc_adx(self, data: pd.DataFrame) -> float | None:
        """ADX値を算出する。計算失敗時はNoneを返す。"""
        adx_df = ta.adx(
            data["high"], data["low"], data["close"],
            length=self._adx_period,
        )
        if adx_df is None:
            logger.warning("ADX計算に失敗しました。")
            return None

        adx_col = f"ADX_{self._adx_period}"
        if adx_col not in adx_df.columns:
            logger.warning("ADX列が見つかりません: %s", adx_col)
            return None

        value = adx_df[adx_col].iloc[-1]
        if pd.isna(value):
            logger.warning("ADX値がNaNです。")
            return None

        return float(value)

    def _calc_atr_ratio(self, data: pd.DataFrame) -> float | None:
        """現在ATR / 中央値ATR の比率を算出する。計算失敗時はNoneを返す。"""
        atr = ta.atr(
            data["high"], data["low"], data["close"],
            length=self._atr_period,
        )
        if atr is None:
            logger.warning("ATR計算に失敗しました。")
            return None

        # NaN を除いた有効値のみで中央値を算出
        valid_atr = atr.dropna()
        if len(valid_atr) < 2:
            logger.warning("有効なATR値が不足しています。")
            return None

        current_atr = valid_atr.iloc[-1]
        median_atr = valid_atr.median()

        if median_atr == 0:
            logger.warning("ATR中央値がゼロです。")
            return None

        return float(current_atr / median_atr)

    def _calc_bbw_ratio(self, data: pd.DataFrame) -> float | None:
        """BBW / 平均BBW の比率を算出する。計算失敗時はNoneを返す。"""
        bbands = ta.bbands(
            data["close"],
            length=self._bb_length,
            std=self._bb_std,
        )
        if bbands is None:
            logger.warning("ボリンジャーバンド計算に失敗しました。")
            return None

        # BBW列名: BBB_{length}_{std} （Bandwidth）
        bbw_col = f"BBB_{self._bb_length}_{self._bb_std}"
        if bbw_col not in bbands.columns:
            # pandas_ta のバージョンにより列名が異なる場合がある
            bbw_candidates = [c for c in bbands.columns if c.startswith("BBB_")]
            if not bbw_candidates:
                logger.warning(
                    "BBW列が見つかりません。利用可能な列: %s",
                    list(bbands.columns),
                )
                return None
            bbw_col = bbw_candidates[0]

        bbw = bbands[bbw_col].dropna()
        if len(bbw) < 2:
            logger.warning("有効なBBW値が不足しています。")
            return None

        current_bbw = bbw.iloc[-1]
        mean_bbw = bbw.mean()

        if mean_bbw == 0:
            logger.warning("BBW平均値がゼロです。")
            return None

        return float(current_bbw / mean_bbw)

    def _unknown_result(self, reason: str) -> RegimeInfo:
        """判定不能時のRegimeInfoを生成する。"""
        logger.warning("レジーム判定不能: %s", reason)
        return RegimeInfo(
            regime=RegimeType.UNKNOWN,
            confidence=0.0,
            adx=0.0,
            atr_ratio=0.0,
            bbw_ratio=0.0,
            exposure_multiplier=0.5,
            reasoning=f"判定不能: {reason}",
        )
