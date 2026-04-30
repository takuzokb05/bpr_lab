"""MTF Pullback 戦略（長期トレンド方向への押し目買い/戻り売り）

バックテストで PF 2.05 (EUR/USD M15) / 1.97 (USD/JPY M15) を記録した本命戦略。

ロジック:
- 長期MA(200)の上なら「上昇トレンド」→ RSI oversold(<35) で押し目買い
- 長期MA(200)の下なら「下降トレンド」→ RSI overbought(>65) で戻り売り
- SL = ATR * atr_multiplier、TP = SL距離 * MIN_RISK_REWARD

現在のMA Crossoverとは異なり、**トレンド中の押し目/戻りを狙う**ため
強トレンド相場で「遅参」にならない特性を持つ。
"""
import logging
from typing import Optional

import pandas as pd
import pandas_ta as ta

from src.config import (
    ATR_MULTIPLIER,
    ATR_PERIOD,
    MIN_RISK_REWARD,
    RSI_PERIOD,
)
from src.strategy.base import Signal, StrategyBase

logger = logging.getLogger(__name__)

# MTFPullback 固有パラメータ（バックテストで最適化済み）
MTF_TREND_MA = 200           # 長期トレンド判定MA
MTF_RSI_OVERSOLD = 35        # 押し目判定閾値（RSI < これで買い候補）
MTF_RSI_OVERBOUGHT = 65      # 戻り判定閾値（RSI > これで売り候補）


class MTFPullback(StrategyBase):
    """
    長期MA方向に合わせて押し目/戻りを狙う戦略。

    エントリー条件:
    - 買い: 現在価格 > MA200 かつ RSI < MTF_RSI_OVERSOLD
    - 売り: 現在価格 < MA200 かつ RSI > MTF_RSI_OVERBOUGHT
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
        """長期トレンド方向への押し目/戻りを検出する。"""
        indicators = kwargs.get("indicators")

        if len(data) < MTF_TREND_MA + 5:
            logger.warning(
                "データ行数が不足しています（%d行 < %d行）。HOLD。",
                len(data), MTF_TREND_MA + 5,
            )
            return Signal.HOLD

        # MA200（キャッシュ優先）
        ma200_series = None
        if indicators is not None:
            ma200_series = indicators.get("ma_trend")
        if ma200_series is None:
            ma200_series = ta.sma(data["close"], length=MTF_TREND_MA)

        # RSI（キャッシュ優先）
        rsi_series = None
        if indicators is not None:
            rsi_series = indicators.get("rsi")
        if rsi_series is None:
            rsi_series = ta.rsi(data["close"], length=RSI_PERIOD)

        if ma200_series is None or rsi_series is None:
            logger.warning("インジケータ計算失敗。HOLD。")
            return Signal.HOLD

        ma200 = ma200_series.iloc[-1]
        rsi = rsi_series.iloc[-1]
        close = data["close"].iloc[-1]

        if pd.isna(ma200) or pd.isna(rsi):
            logger.warning("MA200/RSIにNaN。HOLD。")
            return Signal.HOLD

        diag = {
            "close": float(close),
            "ma200": float(ma200),
            "trend": "up" if close > ma200 else "down",
            "rsi": float(rsi),
            "rsi_oversold": MTF_RSI_OVERSOLD,
            "rsi_overbought": MTF_RSI_OVERBOUGHT,
        }

        # 上昇トレンド中の押し目買い
        if close > ma200 and rsi < MTF_RSI_OVERSOLD:
            diag["hold_reason"] = None
            self._diagnostics = diag
            logger.info(
                "押し目買いシグナル: close=%.5f > MA200=%.5f, RSI=%.2f<%d",
                close, ma200, rsi, MTF_RSI_OVERSOLD,
            )
            return Signal.BUY

        # 下降トレンド中の戻り売り
        if close < ma200 and rsi > MTF_RSI_OVERBOUGHT:
            diag["hold_reason"] = None
            self._diagnostics = diag
            logger.info(
                "戻り売りシグナル: close=%.5f < MA200=%.5f, RSI=%.2f>%d",
                close, ma200, rsi, MTF_RSI_OVERBOUGHT,
            )
            return Signal.SELL

        # エントリー条件外
        if close > ma200:
            diag["hold_reason"] = f"上昇トレンドだがRSI={rsi:.1f}が押し目水準(<{MTF_RSI_OVERSOLD})未満"
        else:
            diag["hold_reason"] = f"下降トレンドだがRSI={rsi:.1f}が戻り水準(>{MTF_RSI_OVERBOUGHT})到達せず"
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
