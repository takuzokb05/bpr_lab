"""
戦略基底モジュール

全ての取引戦略が継承すべき抽象基底クラスとシグナル型を定義する。
doc 04 セクション5.1 準拠。
"""

import enum
import logging
from abc import ABC, abstractmethod

import pandas as pd

logger = logging.getLogger(__name__)


class Signal(enum.Enum):
    """取引シグナルの種別を表す列挙型"""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class StrategyBase(ABC):
    """
    取引戦略の抽象基底クラス

    全ての戦略はこのクラスを継承し、以下の3つのメソッドを実装する必要がある:
    - generate_signal: 価格データからシグナルを生成する
    - calculate_stop_loss: 損切り価格を算出する
    - calculate_take_profit: 利確価格を算出する
    """

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        価格データからシグナルを生成する。

        Args:
            data: OHLCV形式のDataFrame（少なくとも open, high, low, close 列を含む）

        Returns:
            Signal: BUY / SELL / HOLD のいずれか
        """

    @abstractmethod
    def calculate_stop_loss(
        self, entry_price: float, direction: str, data: pd.DataFrame
    ) -> float:
        """
        損切り価格を算出する。

        Args:
            entry_price: エントリー価格
            direction: エントリー方向（"BUY" または "SELL"）
            data: OHLCV形式のDataFrame（ATR等の計算に使用）

        Returns:
            損切り価格
        """

    @abstractmethod
    def calculate_take_profit(
        self, entry_price: float, direction: str, stop_loss: float
    ) -> float:
        """
        利確価格を算出する。

        Args:
            entry_price: エントリー価格
            direction: エントリー方向（"BUY" または "SELL"）
            stop_loss: 損切り価格

        Returns:
            利確価格
        """
