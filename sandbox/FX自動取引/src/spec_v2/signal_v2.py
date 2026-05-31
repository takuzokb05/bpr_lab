"""SPEC v2 PoC シグナル雛形 (§ 3-1 確定までのプレースホルダ)

## 役割
SeasonalDetector が VOLATILE と判定した時のみ起動し、エントリー方向 (long / short)
と SL/TP を提案する。SPEC v2 § 3-1 は未確定のため、これは仮の最小ロジック。

## 仮ロジック (placeholder)
1. M15 直近 N=20 本の最高値 / 最安値を取得
2. 最新 close が:
   - 最高値ブレイク (close > 直近高値) → long
   - 最安値ブレイク (close < 直近安値) → short
   - どちらでもない → no_signal
3. SL: ATR(14) × 1.5、TP: ATR(14) × 3.0 (=リワードリスク 2.0)
4. ピップ単位で出力

## SPEC v2 § 3-1 確定後の差し替え点
- ブレイクアウト判定 → § 3-1 で SPEC 化された手法に置換
- ATR 倍率 → § 3-1 / § 3-2 確定値に置換
- RR 比 → § 3-1 / § 3-2 確定値に置換

PoC の目的は「SeasonalDetector が現実の相場で意味を持つか」の検証であり、
シグナル自体の最適性は本フェーズの問いではない。

## 注意
- この雛形は GBP_JPY 専用
- pips 計算は GBP_JPY (JPY クロス、1 pip = 0.01)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# GBP_JPY 専用設定 (JPY クロス)
PIP_SIZE = 0.01            # 1 pip = 0.01 JPY
BREAKOUT_LOOKBACK = 20      # M15 直近 20 本の最高値/最安値
ATR_PERIOD = 14
ATR_SL_MULT = 1.5
ATR_TP_MULT = 3.0


@dataclass
class TradeSignal:
    """エントリーシグナル"""
    direction: str             # 'long' / 'short' / 'no_signal'
    entry_price: float          # 想定エントリー価格 (M15 close を採用、実発注では現在 mid)
    sl_price: Optional[float]   # ストップロス価格
    tp_price: Optional[float]   # テイクプロフィット価格
    sl_pips: Optional[float]    # SL までの pips
    tp_pips: Optional[float]    # TP までの pips
    reason: str                 # 判定理由 (DB に保存)


def calc_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    """ATR (Average True Range) — 標準実装"""
    h, l, c = df["high"], df["low"], df["close"]
    prev_c = c.shift(1)
    tr = pd.concat([
        h - l,
        (h - prev_c).abs(),
        (l - prev_c).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def generate_signal(m15_df: pd.DataFrame) -> TradeSignal:
    """M15 DataFrame からシグナル生成 (placeholder)。

    Args:
        m15_df: M15 OHLCV DataFrame (最低 BREAKOUT_LOOKBACK + ATR_PERIOD 本)

    Returns:
        TradeSignal — direction が 'no_signal' の場合は entry_price のみ意味あり
    """
    if len(m15_df) < BREAKOUT_LOOKBACK + 1 or len(m15_df) < ATR_PERIOD + 1:
        return TradeSignal(
            direction="no_signal", entry_price=float(m15_df["close"].iloc[-1]),
            sl_price=None, tp_price=None, sl_pips=None, tp_pips=None,
            reason="insufficient_data",
        )

    close = float(m15_df["close"].iloc[-1])

    # 直近 BREAKOUT_LOOKBACK 本 (最新を除く) の最高値/最安値
    lookback_high = float(m15_df["high"].iloc[-BREAKOUT_LOOKBACK - 1:-1].max())
    lookback_low = float(m15_df["low"].iloc[-BREAKOUT_LOOKBACK - 1:-1].min())

    # ATR
    atr_series = calc_atr(m15_df, ATR_PERIOD)
    atr = float(atr_series.iloc[-1])
    if np.isnan(atr) or atr <= 0:
        return TradeSignal(
            direction="no_signal", entry_price=close,
            sl_price=None, tp_price=None, sl_pips=None, tp_pips=None,
            reason="atr_invalid",
        )

    sl_distance = atr * ATR_SL_MULT
    tp_distance = atr * ATR_TP_MULT

    # ブレイクアウト判定
    if close > lookback_high:
        return TradeSignal(
            direction="long",
            entry_price=close,
            sl_price=close - sl_distance,
            tp_price=close + tp_distance,
            sl_pips=sl_distance / PIP_SIZE,
            tp_pips=tp_distance / PIP_SIZE,
            reason=f"breakout_long(close={close:.3f} > high20={lookback_high:.3f}, atr={atr:.4f})",
        )
    elif close < lookback_low:
        return TradeSignal(
            direction="short",
            entry_price=close,
            sl_price=close + sl_distance,
            tp_price=close - tp_distance,
            sl_pips=sl_distance / PIP_SIZE,
            tp_pips=tp_distance / PIP_SIZE,
            reason=f"breakout_short(close={close:.3f} < low20={lookback_low:.3f}, atr={atr:.4f})",
        )
    else:
        return TradeSignal(
            direction="no_signal", entry_price=close,
            sl_price=None, tp_price=None, sl_pips=None, tp_pips=None,
            reason=f"no_breakout(close={close:.3f}, range=[{lookback_low:.3f}, {lookback_high:.3f}])",
        )
