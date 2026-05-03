"""ベンチマーク用戦略: Linda Raschke "Holy Grail" Setup

本ファイルはベンチマーク専用。本番ロード対象外（_先頭プレフィックス）。

公開元（書籍/解説）:
- Linda Bradford Raschke & Laurence A. Connors,
  "Street Smarts: High Probability Short-Term Trading Strategies"
- 解説: https://www.tradingsetupsreview.com/holy-grail-trading-setup/

アルゴリズム要点:
- 強いトレンドの定義: ADX(14) > 30
- セットアップ: 価格が EMA(20) に押し戻される（タッチ or 接近）
- トリガー（買い）: 直近 high をブレイクアップした瞬間
- トリガー（売り）: 直近 low をブレイクダウンした瞬間
- 本来の Raschke 流は SL を直近スイングロー/ハイ、TP を直近スイング高値/安値に置くが、
  本ベンチでは他戦略と評価条件を揃えるため ATR ベース SL + RR=2.0 TP に統一する。

実装上の工夫:
- 「EMA(20) に最初の押し目接触」を厳密に検出するのは難しいため、
  以下のシンプルな代理ルールを使う:
  * BUY: ADX>30 かつ 上昇トレンド (close > EMA20) かつ
         直近 N=3 本以内に Low が EMA20 にタッチ（low <= EMA20 <= high のバー）
         かつ 当バーで前バー high をブレイクアップ
  * SELL: ADX>30 かつ 下降トレンド (close < EMA20) かつ
          直近 N=3 本以内に High が EMA20 にタッチ
          かつ 当バーで前バー low をブレイクダウン
- このため本実装は「Holy Grail インスピレーション版」であり、原典の挙動と
  100% 一致するものではない。比較目的としては十分代表性がある。
"""
import numpy as np
import pandas as pd
import pandas_ta as ta
from backtesting import Strategy


def _ema(close, length):
    return ta.ema(pd.Series(close), length=length)


def _atr(high, low, close, length=14):
    return ta.atr(
        pd.Series(high), pd.Series(low), pd.Series(close), length=length,
    )


def _adx(high, low, close, length=14):
    res = ta.adx(
        pd.Series(high), pd.Series(low), pd.Series(close), length=length,
    )
    if res is None:
        return pd.Series([np.nan] * len(close))
    col = f"ADX_{length}"
    if col in res.columns:
        return res[col]
    return pd.Series([np.nan] * len(close))


class HolyGrailBenchBT(Strategy):
    """Linda Raschke "Holy Grail" の Backtesting.py アダプタ（ベンチマーク専用）"""

    ema_period = 20
    adx_period = 14
    adx_threshold = 30      # 強いトレンドのみ
    pullback_lookback = 3   # 直近何本以内にEMAタッチを許容するか
    atr_period = 14
    atr_mult = 2.0
    rr = 2.0

    def init(self):
        self.ema = self.I(
            _ema, self.data.Close, self.ema_period, name="EMA",
        )
        self.adx = self.I(
            _adx, self.data.High, self.data.Low, self.data.Close,
            self.adx_period, name="ADX",
        )
        self.atr = self.I(
            _atr, self.data.High, self.data.Low, self.data.Close,
            self.atr_period, name="ATR",
        )

    def _ema_touched_recently_long(self) -> bool:
        """直近 N 本に EMA を Low が下抜けまたはタッチしたバーがあるか（ロング用）"""
        n = self.pullback_lookback
        # 当バー[-1]は判定対象外（ブレイクアップを待つので押し目はその前）
        for i in range(2, n + 2):
            if i > len(self.ema):
                break
            ema_v = self.ema[-i]
            low_v = self.data.Low[-i]
            high_v = self.data.High[-i]
            if np.isnan(ema_v):
                continue
            # その足が EMA をまたいでいる、または EMA より下に低値があった
            if low_v <= ema_v <= high_v or low_v <= ema_v:
                return True
        return False

    def _ema_touched_recently_short(self) -> bool:
        n = self.pullback_lookback
        for i in range(2, n + 2):
            if i > len(self.ema):
                break
            ema_v = self.ema[-i]
            low_v = self.data.Low[-i]
            high_v = self.data.High[-i]
            if np.isnan(ema_v):
                continue
            if low_v <= ema_v <= high_v or high_v >= ema_v:
                return True
        return False

    def next(self):
        # 必要バー数チェック
        if len(self.ema) < self.pullback_lookback + 2:
            return
        ema_v = self.ema[-1]
        adx_v = self.adx[-1]
        atr_v = self.atr[-1]
        if np.isnan(ema_v) or np.isnan(adx_v) or np.isnan(atr_v):
            return
        if atr_v == 0 or self.position:
            return
        if adx_v < self.adx_threshold:
            return  # 強いトレンドのみ

        price = self.data.Close[-1]
        prev_high = self.data.High[-2]
        prev_low = self.data.Low[-2]
        sl_dist = atr_v * self.atr_mult

        # 上昇トレンド: 価格 > EMA、押し目があり、前バー高値をブレイクアップ
        if price > ema_v and self._ema_touched_recently_long():
            if price > prev_high:
                self.buy(sl=price - sl_dist, tp=price + sl_dist * self.rr)
                return

        # 下降トレンド: 価格 < EMA、戻りがあり、前バー安値をブレイクダウン
        if price < ema_v and self._ema_touched_recently_short():
            if price < prev_low:
                self.sell(sl=price + sl_dist, tp=price - sl_dist * self.rr)
