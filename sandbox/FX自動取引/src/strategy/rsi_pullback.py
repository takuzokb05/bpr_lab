"""RSI Pullback 戦略（単一タイムフレームの長期MA方向 × RSI極値）

バックテストで PF 2.05 (EUR/USD M15) / 1.97 (USD/JPY M15) を記録した本命戦略。

ロジック（単一タイムフレーム）:
- 同TF MA(200) の上なら「上昇トレンド」→ RSI < RSI_OVERSOLD で押し目買い
- 同TF MA(200) の下なら「下降トレンド」→ RSI > RSI_OVERBOUGHT で戻り売り
- SL = ATR * ATR_MULTIPLIER、TP = SL距離 * MIN_RISK_REWARD

注: 旧名 "MTFPullback" は誤称（マルチタイムフレームではない）。
本実装は与えられた単一の `data` DataFrame 内で MA200/RSI を計算する単TF戦略。
真のMTF（D1トレンド × M15エントリー等）は将来拡張で対応する。
"""
import logging
from typing import Optional

import pandas as pd
import pandas_ta as ta

from src.config import (
    ATR_MULTIPLIER,
    ATR_PERIOD,
    MA_TREND_PERIOD,
    MIN_RISK_REWARD,
    RSI_PERIOD,
)
from src.strategy.base import Signal, StrategyBase

logger = logging.getLogger(__name__)

# RsiPullback 固有パラメータ（バックテストで最適化済み）
RSI_PULLBACK_OVERSOLD = 35    # 押し目判定閾値（RSI < これで買い候補）
RSI_PULLBACK_OVERBOUGHT = 65  # 戻り判定閾値（RSI > これで売り候補）


class RsiPullback(StrategyBase):
    """
    長期MA方向に合わせて押し目/戻りを狙う単TF戦略。

    エントリー条件:
    - 買い: 現在価格 > MA(MA_TREND_PERIOD) かつ RSI < RSI_PULLBACK_OVERSOLD
    - 売り: 現在価格 < MA(MA_TREND_PERIOD) かつ RSI > RSI_PULLBACK_OVERBOUGHT
    - それ以外: HOLD

    損切り: ATRベース（ATR * ATR_MULTIPLIER）
    利確: リスクリワード比 MIN_RISK_REWARD 以上
    """

    def __init__(self) -> None:
        self._diagnostics: Optional[dict] = None

    @property
    def last_diagnostics(self) -> Optional[dict]:
        return self._diagnostics

    def generate_signal(self, data: pd.DataFrame, **kwargs) -> Signal:
        """長期トレンド方向への押し目/戻りを検出する。

        kwargs:
            indicators: 共有指標キャッシュ（ma_trend, rsi）
            pair_config: ペア別設定 dict（rsi_oversold/rsi_overbought をオーバーライド可能）
        """
        indicators = kwargs.get("indicators")
        pair_config = kwargs.get("pair_config") or {}

        # ペア別オーバーライド（pair_config.yaml）→ なければ戦略デフォルト
        rsi_oversold = pair_config.get("rsi_oversold", RSI_PULLBACK_OVERSOLD)
        rsi_overbought = pair_config.get("rsi_overbought", RSI_PULLBACK_OVERBOUGHT)

        if len(data) < MA_TREND_PERIOD + 5:
            logger.warning(
                "データ行数が不足しています（%d行 < %d行）。HOLD。",
                len(data), MA_TREND_PERIOD + 5,
            )
            return Signal.HOLD

        # MA(MA_TREND_PERIOD)（キャッシュ優先）
        ma_trend_series = None
        if indicators is not None:
            ma_trend_series = indicators.get("ma_trend")
        if ma_trend_series is None:
            ma_trend_series = ta.sma(data["close"], length=MA_TREND_PERIOD)

        # RSI（キャッシュ優先）
        rsi_series = None
        if indicators is not None:
            rsi_series = indicators.get("rsi")
        if rsi_series is None:
            rsi_series = ta.rsi(data["close"], length=RSI_PERIOD)

        if ma_trend_series is None or rsi_series is None:
            logger.warning("インジケータ計算失敗。HOLD。")
            return Signal.HOLD

        ma_trend = ma_trend_series.iloc[-1]
        rsi = rsi_series.iloc[-1]
        close = data["close"].iloc[-1]

        if pd.isna(ma_trend) or pd.isna(rsi):
            logger.warning("MA_TREND/RSIにNaN。HOLD。")
            return Signal.HOLD

        diag = {
            "close": float(close),
            "ma_trend": float(ma_trend),
            "trend": "up" if close > ma_trend else "down",
            "rsi": float(rsi),
            "rsi_oversold": rsi_oversold,
            "rsi_overbought": rsi_overbought,
        }

        # 上昇トレンド中の押し目買い
        if close > ma_trend and rsi < rsi_oversold:
            diag["hold_reason"] = None
            self._diagnostics = diag
            logger.info(
                "押し目買いシグナル: close=%.5f > MA%d=%.5f, RSI=%.2f<%d",
                close, MA_TREND_PERIOD, ma_trend, rsi, rsi_oversold,
            )
            return Signal.BUY

        # 下降トレンド中の戻り売り
        if close < ma_trend and rsi > rsi_overbought:
            diag["hold_reason"] = None
            self._diagnostics = diag
            logger.info(
                "戻り売りシグナル: close=%.5f < MA%d=%.5f, RSI=%.2f>%d",
                close, MA_TREND_PERIOD, ma_trend, rsi, rsi_overbought,
            )
            return Signal.SELL

        # エントリー条件外
        if close > ma_trend:
            diag["hold_reason"] = (
                f"上昇トレンドだがRSI={rsi:.1f}が押し目水準(<{rsi_oversold})未満"
            )
        else:
            diag["hold_reason"] = (
                f"下降トレンドだがRSI={rsi:.1f}が戻り水準(>{rsi_overbought})到達せず"
            )
        self._diagnostics = diag
        logger.debug("→ HOLD: %s", diag["hold_reason"])
        return Signal.HOLD

    def calculate_stop_loss(
        self, entry_price: float, direction: str, data: pd.DataFrame,
    ) -> float:
        """ATRベースの損切り価格。"""
        atr = ta.atr(data["high"], data["low"], data["close"], length=ATR_PERIOD)
        if atr is None or pd.isna(atr.iloc[-1]):
            raise ValueError(
                f"ATR計算不能: entry_price={entry_price}"
            )
        current_atr = atr.iloc[-1]
        if direction == "BUY":
            return entry_price - current_atr * ATR_MULTIPLIER
        if direction == "SELL":
            return entry_price + current_atr * ATR_MULTIPLIER
        raise ValueError(f"direction不正: {direction}")

    def calculate_take_profit(
        self, entry_price: float, direction: str, stop_loss: float,
    ) -> float:
        """リスクリワード比から利確価格を算出。"""
        risk = abs(entry_price - stop_loss)
        if risk == 0:
            raise ValueError(
                f"損切り幅ゼロ: entry={entry_price}, sl={stop_loss}"
            )
        if direction == "BUY":
            return entry_price + risk * MIN_RISK_REWARD
        if direction == "SELL":
            return entry_price - risk * MIN_RISK_REWARD
        raise ValueError(f"direction不正: {direction}")
