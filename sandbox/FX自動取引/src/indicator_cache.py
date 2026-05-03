"""
FX自動取引システム — テクニカル指標キャッシュモジュール

1回のイテレーションで全モジュールが必要とする指標を一括計算し、
重複計算を排除する。

R1: IndicatorCache（共有指標計算）
"""

import logging
from typing import Optional

import pandas as pd
import pandas_ta as ta

from src.config import (
    ADX_PERIOD,
    ATR_PERIOD,
    MA_LONG_PERIOD,
    MA_SHORT_PERIOD,
    MA_TREND_PERIOD,
    MFI_PERIOD,
    REGIME_BBW_SQUEEZE_RATIO,
    RSI_PERIOD,
)

logger = logging.getLogger(__name__)


def compute_indicators(data: pd.DataFrame) -> dict:
    """全モジュールが必要とするテクニカル指標を一括計算する。

    Args:
        data: OHLCV形式のDataFrame（high, low, close, volume列）

    Returns:
        指標キャッシュdict。各モジュールはこのdictから値を読み取る。
        計算失敗した指標はNoneが設定される。
    """
    cache: dict = {
        # Series
        "rsi": None,
        "atr": None,
        "ma_short": None,
        "ma_long": None,
        "ma_trend": None,
        "mfi": None,
        # DataFrame
        "adx_df": None,
        "bbands": None,
        # Scalars
        "current_rsi": None,
        "current_adx": None,
        "current_atr": None,
        "current_mfi": None,
        "ma_short_current": None,
        "ma_long_current": None,
        "ma_short_prev": None,
        "ma_long_prev": None,
        "ma_trend_current": None,
        "atr_ratio": None,
        "bbw_ratio": None,
    }

    if data is None or data.empty:
        logger.warning("指標キャッシュ: データが空です。全てNoneで返却します。")
        return cache

    # --- RSI ---
    try:
        rsi = ta.rsi(data["close"], length=RSI_PERIOD)
        if rsi is not None:
            cache["rsi"] = rsi
            last_rsi = rsi.iloc[-1]
            if not pd.isna(last_rsi):
                cache["current_rsi"] = float(last_rsi)
    except Exception as e:
        logger.warning("指標キャッシュ: RSI計算失敗: %s", e)

    # --- ATR ---
    try:
        atr = ta.atr(data["high"], data["low"], data["close"], length=ATR_PERIOD)
        if atr is not None:
            cache["atr"] = atr
            last_atr = atr.iloc[-1]
            if not pd.isna(last_atr):
                cache["current_atr"] = float(last_atr)

            # ATR比率（現在ATR / 中央値ATR）
            valid_atr = atr.dropna()
            if len(valid_atr) >= 2:
                median_atr = valid_atr.median()
                if median_atr != 0:
                    cache["atr_ratio"] = float(valid_atr.iloc[-1] / median_atr)
    except Exception as e:
        logger.warning("指標キャッシュ: ATR計算失敗: %s", e)

    # --- MA短期・長期 ---
    try:
        ma_short = ta.sma(data["close"], length=MA_SHORT_PERIOD)
        if ma_short is not None:
            cache["ma_short"] = ma_short
            if len(ma_short) >= 2:
                last_val = ma_short.iloc[-1]
                prev_val = ma_short.iloc[-2]
                if not pd.isna(last_val):
                    cache["ma_short_current"] = float(last_val)
                if not pd.isna(prev_val):
                    cache["ma_short_prev"] = float(prev_val)
    except Exception as e:
        logger.warning("指標キャッシュ: MA短期計算失敗: %s", e)

    try:
        ma_long = ta.sma(data["close"], length=MA_LONG_PERIOD)
        if ma_long is not None:
            cache["ma_long"] = ma_long
            if len(ma_long) >= 2:
                last_val = ma_long.iloc[-1]
                prev_val = ma_long.iloc[-2]
                if not pd.isna(last_val):
                    cache["ma_long_current"] = float(last_val)
                if not pd.isna(prev_val):
                    cache["ma_long_prev"] = float(prev_val)
    except Exception as e:
        logger.warning("指標キャッシュ: MA長期計算失敗: %s", e)

    # --- MAトレンド（MA200）— RsiPullback等が参照 ---
    try:
        ma_trend = ta.sma(data["close"], length=MA_TREND_PERIOD)
        if ma_trend is not None:
            cache["ma_trend"] = ma_trend
            last_val = ma_trend.iloc[-1]
            if not pd.isna(last_val):
                cache["ma_trend_current"] = float(last_val)
    except Exception as e:
        logger.warning("指標キャッシュ: MAトレンド計算失敗: %s", e)

    # --- ADX ---
    try:
        adx_df = ta.adx(data["high"], data["low"], data["close"], length=ADX_PERIOD)
        if adx_df is not None:
            cache["adx_df"] = adx_df
            adx_col = f"ADX_{ADX_PERIOD}"
            if adx_col in adx_df.columns:
                last_adx = adx_df[adx_col].iloc[-1]
                if not pd.isna(last_adx):
                    cache["current_adx"] = float(last_adx)
    except Exception as e:
        logger.warning("指標キャッシュ: ADX計算失敗: %s", e)

    # --- MFI（volume列がある場合のみ） ---
    vol_col = None
    if "volume" in data.columns:
        vol_col = "volume"
    elif "tick_volume" in data.columns:
        vol_col = "tick_volume"

    if vol_col is not None:
        try:
            mfi = ta.mfi(
                data["high"], data["low"], data["close"], data[vol_col],
                length=MFI_PERIOD,
            )
            if mfi is not None:
                cache["mfi"] = mfi
                last_mfi = mfi.iloc[-1]
                if not pd.isna(last_mfi):
                    cache["current_mfi"] = float(last_mfi)
        except Exception as e:
            logger.warning("指標キャッシュ: MFI計算失敗: %s", e)

    # --- ボリンジャーバンド + BBW比率 ---
    try:
        bbands = ta.bbands(data["close"], length=20, std=2.0)
        if bbands is not None:
            cache["bbands"] = bbands

            # BBW列を探す
            bbw_col = "BBB_20_2.0"
            if bbw_col not in bbands.columns:
                bbw_candidates = [c for c in bbands.columns if c.startswith("BBB_")]
                if bbw_candidates:
                    bbw_col = bbw_candidates[0]
                else:
                    bbw_col = None

            if bbw_col is not None:
                bbw = bbands[bbw_col].dropna()
                if len(bbw) >= 2:
                    current_bbw = float(bbw.iloc[-1])
                    mean_bbw = float(bbw.mean())
                    if mean_bbw != 0:
                        cache["bbw_ratio"] = current_bbw / mean_bbw
    except Exception as e:
        logger.warning("指標キャッシュ: ボリンジャーバンド計算失敗: %s", e)

    return cache
