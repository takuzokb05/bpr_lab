"""
戦略基底モジュール

全ての取引戦略が継承すべき抽象基底クラスとシグナル型を定義する。
doc 04 セクション5.1 準拠。
"""

import enum
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class TpLevels:
    """段階的利確のレベル情報。

    Attributes:
        stop_loss: 損切り価格
        tp1: 第1利確価格（部分決済対象）
        tp2: 第2利確価格（残り全決済）
        atr: SL/TP算出に用いた ATR 値（事後検証用）
    """
    stop_loss: float
    tp1: float
    tp2: float
    atr: Optional[float] = None


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
    def generate_signal(self, data: pd.DataFrame, **kwargs) -> Signal:
        """
        価格データからシグナルを生成する。

        Args:
            data: OHLCV形式のDataFrame（少なくとも open, high, low, close 列を含む）
            **kwargs: 追加パラメータ（indicators等）

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

    def calculate_tp_levels(
        self,
        entry_price: float,
        direction: str,
        data: pd.DataFrame,
        pair_config: Optional[dict] = None,
    ) -> TpLevels:
        """
        SL / TP1 / TP2 を一括算出する（段階的部分利確のための拡張API）。

        既定実装は ATR ベース（USE_ATR_BASED_TP=True 時）または
        既存の calculate_stop_loss / calculate_take_profit を使ったフォールバック。
        個別戦略で必要なら override 可能。

        T4: pair_config が渡された場合、atr_sl_mult/atr_tp1_mult/atr_tp2_mult を
        ペア別オーバーライドとして使用する（pair_config.yaml 由来）。

        Args:
            entry_price: エントリー価格
            direction: "BUY" または "SELL"
            data: OHLCV DataFrame（ATR 算出に使用）
            pair_config: ペア別パラメータ dict（T4 pair_config.yaml 由来）

        Returns:
            TpLevels（SL, TP1, TP2, ATR）

        Raises:
            ValueError: ATR 算出不能、direction 不正、または SL とエントリーが一致した場合
        """
        from src.risk_manager import calculate_atr_based_levels  # 循環import回避
        from src.config import USE_ATR_BASED_TP

        if USE_ATR_BASED_TP:
            sl_mult = pair_config.get("atr_sl_mult") if pair_config else None
            tp1_mult = pair_config.get("atr_tp1_mult") if pair_config else None
            tp2_mult = pair_config.get("atr_tp2_mult") if pair_config else None
            return calculate_atr_based_levels(
                entry_price, direction, data,
                sl_mult=sl_mult, tp1_mult=tp1_mult, tp2_mult=tp2_mult,
            )

        # フォールバック: 旧来のSL/TPを TP1=TP2 として返す（部分利確しない動作）
        sl = self.calculate_stop_loss(entry_price, direction, data)
        tp = self.calculate_take_profit(entry_price, direction, sl)
        return TpLevels(stop_loss=sl, tp1=tp, tp2=tp, atr=None)
