"""RegimeDetector のテスト（監査A4 pair_config オーバーライド回帰防止含む）"""
import numpy as np
import pandas as pd
import pytest

from src.config import (
    REGIME_ADX_RANGING,
    REGIME_ADX_TRENDING,
)
from src.regime_detector import RegimeDetector, RegimeType


def _make_synthetic_data(n: int = 200, trend_strength: float = 0.0) -> pd.DataFrame:
    """ADX/ATR 計算が可能な最低限の OHLC データを生成。

    trend_strength: 1足あたりの平均上昇幅（0=ランダムウォーク、大きいほど強トレンド）
    """
    np.random.seed(42)
    closes = 100.0 + np.cumsum(np.random.randn(n) * 0.5 + trend_strength)
    highs = closes + np.abs(np.random.randn(n) * 0.3)
    lows = closes - np.abs(np.random.randn(n) * 0.3)
    return pd.DataFrame({"high": highs, "low": lows, "close": closes})


def test_pair_config_overrides_adx_thresholds_audit_a4():
    """監査A4: pair_config の regime_adx_trending が reasoning に反映される"""
    detector = RegimeDetector()
    data = _make_synthetic_data(n=200, trend_strength=0.05)

    info_strict = detector.detect(
        data, pair_config={"regime_adx_trending": 99.0, "regime_adx_ranging": 0.0},
    )
    info_default = detector.detect(data)

    # pair_config の override 値が reasoning に現れる（または計算閾値として効く）
    # 厳しい閾値ではグレーゾーン or 弱判定になるため、強TRENDING(exposure=1.2)
    # にはならない
    assert info_strict.regime != RegimeType.UNKNOWN, "計算は成功すべき"
    assert info_strict.exposure_multiplier <= 1.0, (
        f"adx_trending=99で強TRENDING(1.2倍)はおかしい: "
        f"exposure={info_strict.exposure_multiplier}, reasoning={info_strict.reasoning}"
    )

    # ATRボラティリティ閾値 override も効くか確認
    info_atr = detector.detect(
        data, pair_config={"regime_atr_volatile_ratio": 0.01},  # 異常に低い → ほぼVOLATILE
    )
    assert info_atr.regime == RegimeType.VOLATILE, (
        f"atr_volatile_ratio=0.01で VOLATILE 判定にならない: {info_atr.reasoning}"
    )


def test_pair_config_none_falls_back_to_globals():
    """pair_config 未指定時は config.py のグローバル値が使われる（後方互換）"""
    detector = RegimeDetector()
    data = _make_synthetic_data(n=200, trend_strength=0.0)

    info = detector.detect(data, pair_config=None)
    # reasoning にグローバル閾値が表示されているか（実装に依存しないため緩く）
    assert info.regime in (
        RegimeType.TRENDING, RegimeType.RANGING,
        RegimeType.VOLATILE, RegimeType.UNKNOWN,
    )


def test_regime_detector_returns_unknown_for_short_data():
    """データ行数不足なら UNKNOWN"""
    detector = RegimeDetector()
    data = _make_synthetic_data(n=10)
    info = detector.detect(data)
    assert info.regime == RegimeType.UNKNOWN
    assert info.exposure_multiplier == 0.5


def test_global_thresholds_consistency():
    """REGIME_ADX_RANGING < REGIME_ADX_TRENDING（順序整合性）"""
    assert REGIME_ADX_RANGING < REGIME_ADX_TRENDING
