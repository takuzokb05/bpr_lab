"""ベンチマーク用戦略: freqtrade HLHB (Huck Loves Her Bucks)

本ファイルはベンチマーク専用。本番ロード対象外（_先頭プレフィックス）。
本番戦略 (rsi_pullback.py 等) との PF/Sharpe/MaxDD 比較を目的に移植。

公開元:
- https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/hlhb.py
- 元アイデア: BabyPips "HLHB Trend-Catcher System"
  https://www.babypips.com/trading/forex-hlhb-system-explained-20180803

アルゴリズム要点（freqtrade 公開実装に準拠）:
- エントリー（買い）: EMA(5) が EMA(10) を上抜け（ゴールデンクロス） かつ
                     RSI(10) が 50 を上抜け かつ ADX(14) > 25
- エントリー（売り）: EMA(5) が EMA(10) を下抜け（デッドクロス） かつ
                     RSI(10) が 50 を下抜け かつ ADX(14) > 25
- 元実装は ROI/trailing_stop で利確・損切りを管理する Hyperopt 最適化前提だが、
  本ベンチでは他戦略と評価条件を揃えるため ATR ベース SL + RR=2.0 TP に統一する。

評価軸を揃えるための共通ルール:
- SL = ATR(14) * 2.0
- TP = SL距離 * 2.0  (RR=2.0)
- exclusive_orders=True（同時保有1ポジ）
"""
import numpy as np
import pandas as pd
import pandas_ta as ta
from backtesting import Strategy


def _ema(close, length):
    return ta.ema(pd.Series(close), length=length)


def _rsi(close, length):
    return ta.rsi(pd.Series(close), length=length)


def _atr(high, low, close, length=14):
    return ta.atr(
        pd.Series(high), pd.Series(low), pd.Series(close), length=length,
    )


def _adx(high, low, close, length=14):
    """ADX 列のみを返す（pandas_ta.adx は DataFrame を返すため）"""
    res = ta.adx(
        pd.Series(high), pd.Series(low), pd.Series(close), length=length,
    )
    if res is None:
        return pd.Series([np.nan] * len(close))
    col = f"ADX_{length}"
    if col in res.columns:
        return res[col]
    return pd.Series([np.nan] * len(close))


class HlhbBenchBT(Strategy):
    """freqtrade HLHB 戦略の Backtesting.py アダプタ（ベンチマーク専用）"""

    # HLHB 公開実装に準拠したパラメータ
    ema_fast = 5
    ema_slow = 10
    rsi_period = 10
    rsi_threshold = 50
    adx_period = 14
    adx_threshold = 25
    # 共通の SL/TP（他戦略と評価条件を揃えるため）
    atr_period = 14
    atr_mult = 2.0
    rr = 2.0

    def init(self):
        self.ema_f = self.I(
            _ema, self.data.Close, self.ema_fast, name="EMA_fast",
        )
        self.ema_s = self.I(
            _ema, self.data.Close, self.ema_slow, name="EMA_slow",
        )
        self.rsi = self.I(
            _rsi, self.data.Close, self.rsi_period, name="RSI",
        )
        self.adx = self.I(
            _adx, self.data.High, self.data.Low, self.data.Close,
            self.adx_period, name="ADX",
        )
        self.atr = self.I(
            _atr, self.data.High, self.data.Low, self.data.Close,
            self.atr_period, name="ATR",
        )

    def next(self):
        # 前バーが必要なクロス判定なので最低 2 本必要
        if len(self.ema_f) < 2:
            return
        # NaN ガード
        for v in (self.ema_f[-1], self.ema_s[-1], self.ema_f[-2],
                  self.ema_s[-2], self.rsi[-1], self.rsi[-2],
                  self.adx[-1], self.atr[-1]):
            if np.isnan(v):
                return
        if self.atr[-1] == 0 or self.position:
            return
        if self.adx[-1] < self.adx_threshold:
            return  # トレンドが弱い場面はエントリーしない

        price = self.data.Close[-1]
        sl_dist = self.atr[-1] * self.atr_mult

        # ゴールデンクロス + RSI 50 上抜け → BUY
        ema_cross_up = (
            self.ema_f[-2] <= self.ema_s[-2]
            and self.ema_f[-1] > self.ema_s[-1]
        )
        rsi_cross_up = (
            self.rsi[-2] <= self.rsi_threshold
            and self.rsi[-1] > self.rsi_threshold
        )
        if ema_cross_up and rsi_cross_up:
            self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)
            return

        # デッドクロス + RSI 50 下抜け → SELL
        ema_cross_dn = (
            self.ema_f[-2] >= self.ema_s[-2]
            and self.ema_f[-1] < self.ema_s[-1]
        )
        rsi_cross_dn = (
            self.rsi[-2] >= self.rsi_threshold
            and self.rsi[-1] < self.rsi_threshold
        )
        if ema_cross_dn and rsi_cross_dn:
            self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)
