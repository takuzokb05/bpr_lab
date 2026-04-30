"""Bollinger Reversal 戦略（2σタッチ+RSI過熱で逆張り）

バックテスト実績:
- EUR/USD M15: PF 1.24, 勝率46.3%, DD-21%, SR 1.11, 134トレード
- GBP/JPY M15: PF 1.08, 勝率41.7%, DD-26%, SR 0.43, 120トレード

ロジック:
- 上バンド到達 + RSI >= 70 → 逆張りSELL（平均回帰期待）
- 下バンド到達 + RSI <= 30 → 逆張りBUY
- SL/TPは短め（ATR*1.5 / RR=1.5）— 平均回帰は大きなTP狙わない
"""
import logging
from typing import Optional

import pandas as pd
import pandas_ta as ta

from src.config import (
    ATR_PERIOD,
    RSI_PERIOD,
)
from src.strategy.base import Signal, StrategyBase

logger = logging.getLogger(__name__)

# BollingerReversal固有パラメータ（BB_RSI_OVERBOUGHT/OVERSOLDは共通70/30から独立化）
# 70/30は過熱過ぎて発火頻度が低すぎるため、65/35に緩和
BB_LENGTH = 20
BB_STD = 2.0
BB_RSI_OVERBOUGHT = 65    # 共通70→65に緩和
BB_RSI_OVERSOLD = 35      # 共通30→35に緩和
BB_ATR_MULTIPLIER = 1.5   # 平均回帰は短めSL
BB_MIN_RISK_REWARD = 1.5  # 平均回帰は大きなTP狙わない


class BollingerReversal(StrategyBase):
    """2σタッチ+RSI過熱で逆張りする平均回帰戦略。"""

    def __init__(self) -> None:
        self._diagnostics: Optional[dict] = None

    @property
    def last_diagnostics(self) -> Optional[dict]:
        return self._diagnostics

    def generate_signal(self, data: pd.DataFrame, **kwargs) -> Signal:
        if len(data) < BB_LENGTH + 5:
            logger.warning(
                "データ不足（%d行 < %d行）。HOLD。",
                len(data), BB_LENGTH + 5,
            )
            return Signal.HOLD

        bbands = ta.bbands(data["close"], length=BB_LENGTH, std=BB_STD)
        if bbands is None:
            logger.warning("BBands計算失敗。HOLD。")
            return Signal.HOLD

        upper_col = [c for c in bbands.columns if c.startswith("BBU_")]
        lower_col = [c for c in bbands.columns if c.startswith("BBL_")]
        if not upper_col or not lower_col:
            logger.warning("BB上下バンド列が見つからない。HOLD。")
            return Signal.HOLD

        bb_u = bbands[upper_col[0]].iloc[-1]
        bb_l = bbands[lower_col[0]].iloc[-1]
        rsi_series = ta.rsi(data["close"], length=RSI_PERIOD)
        if rsi_series is None:
            logger.warning("RSI計算失敗。HOLD。")
            return Signal.HOLD
        rsi = rsi_series.iloc[-1]
        close = data["close"].iloc[-1]

        if pd.isna(bb_u) or pd.isna(bb_l) or pd.isna(rsi):
            return Signal.HOLD

        diag = {
            "close": float(close),
            "bb_upper": float(bb_u),
            "bb_lower": float(bb_l),
            "rsi": float(rsi),
        }

        # 上バンドタッチ + RSI過熱 → 逆張りSELL
        if close >= bb_u and rsi >= BB_RSI_OVERBOUGHT:
            diag["hold_reason"] = None
            self._diagnostics = diag
            logger.info(
                "BB逆張り売りシグナル: close=%.5f >= BBU=%.5f, RSI=%.2f>=%d",
                close, bb_u, rsi, BB_RSI_OVERBOUGHT,
            )
            return Signal.SELL

        # 下バンドタッチ + RSI過売 → 逆張りBUY
        if close <= bb_l and rsi <= BB_RSI_OVERSOLD:
            diag["hold_reason"] = None
            self._diagnostics = diag
            logger.info(
                "BB逆張り買いシグナル: close=%.5f <= BBL=%.5f, RSI=%.2f<=%d",
                close, bb_l, rsi, BB_RSI_OVERSOLD,
            )
            return Signal.BUY

        diag["hold_reason"] = f"BB/RSI条件未達 (close={close:.5f}, RSI={rsi:.1f})"
        self._diagnostics = diag
        return Signal.HOLD

    def calculate_stop_loss(
        self, entry_price: float, direction: str, data: pd.DataFrame,
    ) -> float:
        atr = ta.atr(data["high"], data["low"], data["close"], length=ATR_PERIOD)
        if atr is None or pd.isna(atr.iloc[-1]):
            raise ValueError(f"ATR計算不能: entry={entry_price}")
        current_atr = atr.iloc[-1]
        if direction == "BUY":
            return entry_price - current_atr * BB_ATR_MULTIPLIER
        if direction == "SELL":
            return entry_price + current_atr * BB_ATR_MULTIPLIER
        raise ValueError(f"direction不正: {direction}")

    def calculate_take_profit(
        self, entry_price: float, direction: str, stop_loss: float,
    ) -> float:
        risk = abs(entry_price - stop_loss)
        if risk == 0:
            raise ValueError(f"損切り幅ゼロ")
        if direction == "BUY":
            return entry_price + risk * BB_MIN_RISK_REWARD
        if direction == "SELL":
            return entry_price - risk * BB_MIN_RISK_REWARD
        raise ValueError(f"direction不正: {direction}")
