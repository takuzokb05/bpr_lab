"""戦略バリエーション — Backtesting.py 用アダプタ

- DonchianBreakoutBT   : N本高値/安値ブレイクで順張り
- BollingerReversalBT  : 2σタッチ + RSI過熱で逆張り
- MTFPullbackBT        : 長期MA方向 × 短期RSI過売/過熱で押し目/戻り
- ATRChannelBreakoutBT : ATR幅を抜けたら順張り（Donchianのボラ版）

全て ATRベースSL + RR2.0 TP を共通化。
"""
import numpy as np
import pandas as pd
import pandas_ta as ta
from backtesting import Strategy


def _atr_only(high, low, close, length=14):
    return ta.atr(pd.Series(high), pd.Series(low), pd.Series(close),
                  length=length)


def _rsi_only(close, length=14):
    return ta.rsi(pd.Series(close), length=length)


def _sma_only(close, length=50):
    return ta.sma(pd.Series(close), length=length)


def _bb_upper(close, length=20, std=2.0):
    bb = ta.bbands(pd.Series(close), length=length, std=std)
    if bb is None:
        return pd.Series([np.nan] * len(close))
    col = [c for c in bb.columns if c.startswith("BBU_")]
    return bb[col[0]] if col else pd.Series([np.nan] * len(close))


def _bb_lower(close, length=20, std=2.0):
    bb = ta.bbands(pd.Series(close), length=length, std=std)
    if bb is None:
        return pd.Series([np.nan] * len(close))
    col = [c for c in bb.columns if c.startswith("BBL_")]
    return bb[col[0]] if col else pd.Series([np.nan] * len(close))


# ------------------------------------------------------------
# A1. Donchian Breakout（N本高値/安値ブレイクで順張り）
# ------------------------------------------------------------
class DonchianBreakoutBT(Strategy):
    donchian_len = 20
    atr_period = 14
    atr_mult = 2.0
    rr = 2.0

    def init(self):
        self.high_n = self.I(
            lambda h: pd.Series(h).rolling(self.donchian_len).max().shift(1),
            self.data.High, name="HighN",
        )
        self.low_n = self.I(
            lambda l: pd.Series(l).rolling(self.donchian_len).min().shift(1),
            self.data.Low, name="LowN",
        )
        self.atr = self.I(
            _atr_only, self.data.High, self.data.Low, self.data.Close,
            self.atr_period, name="ATR",
        )

    def next(self):
        if np.isnan(self.high_n[-1]) or np.isnan(self.low_n[-1]):
            return
        if np.isnan(self.atr[-1]) or self.atr[-1] == 0:
            return
        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.atr_mult

        # 上方ブレイク → BUY
        if price > self.high_n[-1] and not self.position:
            sl = price - sl_dist
            tp = price + sl_dist * self.rr
            self.buy(sl=sl, tp=tp)
        # 下方ブレイク → SELL
        elif price < self.low_n[-1] and not self.position:
            sl = price + sl_dist
            tp = price - sl_dist * self.rr
            self.sell(sl=sl, tp=tp)


# ------------------------------------------------------------
# A2. ATR Channel Breakout（ATR幅を超えたら順張り）
# ------------------------------------------------------------
class ATRChannelBreakoutBT(Strategy):
    ma_period = 20
    atr_period = 14
    atr_mult = 1.5  # チャネル幅
    sl_atr_mult = 2.0  # SL幅
    rr = 2.0

    def init(self):
        self.ma = self.I(_sma_only, self.data.Close, self.ma_period, name="MA")
        self.atr = self.I(
            _atr_only, self.data.High, self.data.Low, self.data.Close,
            self.atr_period, name="ATR",
        )

    def next(self):
        if np.isnan(self.ma[-1]) or np.isnan(self.atr[-1]):
            return
        if self.atr[-1] == 0 or self.position:
            return
        upper = self.ma[-1] + self.atr[-1] * self.atr_mult
        lower = self.ma[-1] - self.atr[-1] * self.atr_mult
        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.sl_atr_mult

        if price > upper:
            self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)
        elif price < lower:
            self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)


# ------------------------------------------------------------
# B1. MTF Pullback（長期MA方向の押し目買い/戻り売り）
# ------------------------------------------------------------
class MTFPullbackBT(Strategy):
    trend_ma = 200   # 長期トレンド判定
    rsi_period = 14
    rsi_oversold = 35
    rsi_overbought = 65
    atr_period = 14
    atr_mult = 2.0
    rr = 2.0

    def init(self):
        self.ma200 = self.I(_sma_only, self.data.Close, self.trend_ma, name="MA200")
        self.rsi = self.I(_rsi_only, self.data.Close, self.rsi_period, name="RSI")
        self.atr = self.I(
            _atr_only, self.data.High, self.data.Low, self.data.Close,
            self.atr_period, name="ATR",
        )

    def next(self):
        if (np.isnan(self.ma200[-1]) or np.isnan(self.rsi[-1])
                or np.isnan(self.atr[-1])):
            return
        if self.atr[-1] == 0 or self.position:
            return
        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.atr_mult

        # 長期上昇トレンド + RSI oversold → 押し目買い
        if price > self.ma200[-1] and self.rsi[-1] < self.rsi_oversold:
            self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)
        # 長期下降トレンド + RSI overbought → 戻り売り
        elif price < self.ma200[-1] and self.rsi[-1] > self.rsi_overbought:
            self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)


# ------------------------------------------------------------
# C1. Bollinger Mean Reversion（2σタッチ+RSI過熱で逆張り）
# ------------------------------------------------------------
class BollingerReversalBT(Strategy):
    bb_length = 20
    bb_std = 2.0
    rsi_period = 14
    rsi_overbought = 70
    rsi_oversold = 30
    atr_period = 14
    atr_mult = 1.5  # Meanreversionは短めSL
    rr = 1.5        # 平均回帰は大きなTP狙わない

    def init(self):
        self.bb_u = self.I(
            _bb_upper, self.data.Close, self.bb_length, self.bb_std,
            name="BBU",
        )
        self.bb_l = self.I(
            _bb_lower, self.data.Close, self.bb_length, self.bb_std,
            name="BBL",
        )
        self.rsi = self.I(_rsi_only, self.data.Close, self.rsi_period, name="RSI")
        self.atr = self.I(
            _atr_only, self.data.High, self.data.Low, self.data.Close,
            self.atr_period, name="ATR",
        )

    def next(self):
        if (np.isnan(self.bb_u[-1]) or np.isnan(self.bb_l[-1])
                or np.isnan(self.rsi[-1]) or np.isnan(self.atr[-1])):
            return
        if self.atr[-1] == 0 or self.position:
            return
        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.atr_mult

        # 上バンド + RSI overbought → 逆張り売り
        if price >= self.bb_u[-1] and self.rsi[-1] >= self.rsi_overbought:
            self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)
        # 下バンド + RSI oversold → 逆張り買い
        elif price <= self.bb_l[-1] and self.rsi[-1] <= self.rsi_oversold:
            self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)


STRATEGIES = {
    "Donchian": DonchianBreakoutBT,
    "ATRChannel": ATRChannelBreakoutBT,
    "MTFPullback": MTFPullbackBT,
    "BollingerReversal": BollingerReversalBT,
}
