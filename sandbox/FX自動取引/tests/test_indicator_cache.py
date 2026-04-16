"""
テクニカル指標キャッシュモジュールのテスト

R1: IndicatorCache の単体テスト
- 全期待キーが返却されること
- 最小データ（MA_LONG_PERIOD未満）で関連フィールドがNoneになること
- volume列なしでmfi=Noneになること
- キャッシュ値が個別計算値と一致すること
"""

import numpy as np
import pandas as pd
import pandas_ta as ta
import pytest

from src.config import (
    ADX_PERIOD,
    ATR_PERIOD,
    MA_LONG_PERIOD,
    MA_SHORT_PERIOD,
    MFI_PERIOD,
    RSI_PERIOD,
)
from src.indicator_cache import compute_indicators


# ============================================================
# テスト用ヘルパー
# ============================================================


def _make_ohlcv(n: int = 100, base_price: float = 100.0, with_volume: bool = True) -> pd.DataFrame:
    """テスト用OHLCVデータを生成する。"""
    np.random.seed(42)
    close = base_price + np.cumsum(np.random.randn(n) * 0.5)
    spread = 0.3
    df = pd.DataFrame({
        "open": close - np.random.rand(n) * spread,
        "high": close + np.abs(np.random.randn(n)) * spread,
        "low": close - np.abs(np.random.randn(n)) * spread,
        "close": close,
    })
    if with_volume:
        df["volume"] = np.random.randint(500, 2000, size=n).astype(float)
    return df


# ============================================================
# テストケース
# ============================================================


class TestComputeIndicators:
    """compute_indicators() の基本テスト"""

    def test_returns_all_expected_keys(self) -> None:
        """全ての期待キーがdictに含まれること"""
        data = _make_ohlcv(100)
        result = compute_indicators(data)

        expected_keys = {
            "rsi", "atr", "ma_short", "ma_long", "mfi",
            "adx_df", "bbands",
            "current_rsi", "current_adx", "current_atr", "current_mfi",
            "ma_short_current", "ma_long_current",
            "ma_short_prev", "ma_long_prev",
            "atr_ratio", "bbw_ratio",
        }
        assert set(result.keys()) == expected_keys

    def test_all_values_not_none_with_sufficient_data(self) -> None:
        """十分なデータがあれば全指標がNoneでないこと"""
        data = _make_ohlcv(100)
        result = compute_indicators(data)

        for key in ["rsi", "atr", "ma_short", "ma_long", "mfi",
                     "adx_df", "bbands",
                     "current_rsi", "current_adx", "current_atr", "current_mfi",
                     "ma_short_current", "ma_long_current",
                     "ma_short_prev", "ma_long_prev",
                     "atr_ratio", "bbw_ratio"]:
            assert result[key] is not None, f"{key} がNoneです"

    def test_minimal_data_returns_none_for_long_period_fields(self) -> None:
        """MA_LONG_PERIOD未満のデータではMA長期関連がNoneになること"""
        # MA_LONG_PERIOD = 50 なので、10行のデータを使う
        data = _make_ohlcv(10)
        result = compute_indicators(data)

        # MA長期は計算できてもNaN値が多い → current値がNoneになる
        assert result["ma_long_current"] is None
        assert result["ma_long_prev"] is None

    def test_no_volume_column_returns_mfi_none(self) -> None:
        """volume列がないDataFrameではmfi=Noneになること"""
        data = _make_ohlcv(100, with_volume=False)
        result = compute_indicators(data)

        assert result["mfi"] is None
        assert result["current_mfi"] is None

    def test_empty_dataframe(self) -> None:
        """空のDataFrameでは全てNoneが返ること"""
        data = pd.DataFrame()
        result = compute_indicators(data)

        for key, value in result.items():
            assert value is None, f"{key} がNoneではありません: {value}"

    def test_cached_rsi_matches_independent(self) -> None:
        """キャッシュのRSI値が個別計算と一致すること"""
        data = _make_ohlcv(100)
        result = compute_indicators(data)

        # 個別計算
        rsi_independent = ta.rsi(data["close"], length=RSI_PERIOD)
        assert rsi_independent is not None

        # 最終値が一致
        assert abs(result["current_rsi"] - float(rsi_independent.iloc[-1])) < 1e-10

    def test_cached_atr_matches_independent(self) -> None:
        """キャッシュのATR値が個別計算と一致すること"""
        data = _make_ohlcv(100)
        result = compute_indicators(data)

        atr_independent = ta.atr(data["high"], data["low"], data["close"], length=ATR_PERIOD)
        assert atr_independent is not None

        assert abs(result["current_atr"] - float(atr_independent.iloc[-1])) < 1e-10

    def test_cached_adx_matches_independent(self) -> None:
        """キャッシュのADX値が個別計算と一致すること"""
        data = _make_ohlcv(100)
        result = compute_indicators(data)

        adx_df = ta.adx(data["high"], data["low"], data["close"], length=ADX_PERIOD)
        adx_col = f"ADX_{ADX_PERIOD}"
        expected_adx = float(adx_df[adx_col].iloc[-1])

        assert abs(result["current_adx"] - expected_adx) < 1e-10

    def test_cached_ma_matches_independent(self) -> None:
        """キャッシュのMA値が個別計算と一致すること"""
        data = _make_ohlcv(100)
        result = compute_indicators(data)

        ma_short = ta.sma(data["close"], length=MA_SHORT_PERIOD)
        ma_long = ta.sma(data["close"], length=MA_LONG_PERIOD)

        assert abs(result["ma_short_current"] - float(ma_short.iloc[-1])) < 1e-10
        assert abs(result["ma_long_current"] - float(ma_long.iloc[-1])) < 1e-10
        assert abs(result["ma_short_prev"] - float(ma_short.iloc[-2])) < 1e-10
        assert abs(result["ma_long_prev"] - float(ma_long.iloc[-2])) < 1e-10

    def test_cached_mfi_matches_independent(self) -> None:
        """キャッシュのMFI値が個別計算と一致すること"""
        data = _make_ohlcv(100)
        result = compute_indicators(data)

        mfi_independent = ta.mfi(
            data["high"], data["low"], data["close"], data["volume"],
            length=MFI_PERIOD,
        )
        assert mfi_independent is not None

        assert abs(result["current_mfi"] - float(mfi_independent.iloc[-1])) < 1e-10

    def test_tick_volume_column_used_for_mfi(self) -> None:
        """tick_volume列がある場合にMFIが計算されること"""
        data = _make_ohlcv(100, with_volume=False)
        data["tick_volume"] = np.random.randint(500, 2000, size=len(data)).astype(float)
        result = compute_indicators(data)

        assert result["mfi"] is not None
        assert result["current_mfi"] is not None

    def test_atr_ratio_is_positive(self) -> None:
        """ATR比率が正の値であること"""
        data = _make_ohlcv(100)
        result = compute_indicators(data)

        assert result["atr_ratio"] is not None
        assert result["atr_ratio"] > 0

    def test_none_data_returns_all_none(self) -> None:
        """data=Noneでは全てNoneが返ること"""
        result = compute_indicators(None)

        for key, value in result.items():
            assert value is None, f"{key} がNoneではありません: {value}"
