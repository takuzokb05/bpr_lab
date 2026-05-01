"""
FX自動取引システム — ブローカー抽象化インターフェース

全ブローカー実装（OANDA, IB等）はこのインターフェースに準拠する。
doc 04 セクション3.1 BrokerClient最小メソッドセット準拠。
"""

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd


class BrokerClient(ABC):
    """
    ブローカーAPI抽象化基底クラス。

    Phase 1ではOANDA実装のみ。Phase 2でIBデモ接続テスト予定。
    OANDAはRESTful（ステートレス）、IBはTWS API（ステートフル・ソケットベース）であり、
    抽象化の実装コストが異なる点に注意。
    """

    @abstractmethod
    def get_prices(
        self,
        instrument: str,
        count: int,
        granularity: str,
    ) -> pd.DataFrame:
        """
        価格データを取得する。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            count: 取得するローソク足の本数
            granularity: 時間足（例: "H4", "D", "M15"）

        Returns:
            OHLCV形式のDataFrame。カラム: open, high, low, close, volume
            インデックス: datetime（UTC）
        """

    @abstractmethod
    def market_order(
        self,
        instrument: str,
        units: int,
        stop_loss: float,
        take_profit: float,
    ) -> dict:
        """
        成行注文を発注する。SL/TPは必須。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            units: 取引数量（正=買い、負=売り）
            stop_loss: 損切り価格（必須）
            take_profit: 利確価格（必須）

        Returns:
            注文結果を含むdict。最低限 "order_id" キーを含む。
        """

    @abstractmethod
    def limit_order(
        self,
        instrument: str,
        units: int,
        price: float,
        stop_loss: float,
        take_profit: float,
    ) -> dict:
        """
        指値注文を発注する。SL/TPは必須。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            units: 取引数量（正=買い、負=売り）
            price: 指値価格
            stop_loss: 損切り価格（必須）
            take_profit: 利確価格（必須）

        Returns:
            注文結果を含むdict。最低限 "order_id" キーを含む。
        """

    @abstractmethod
    def get_positions(self) -> list[dict]:
        """
        保有ポジション一覧を取得する。

        ローカル状態との整合性確認に使用する。

        Returns:
            ポジション情報のリスト。各dictは最低限以下を含む:
            - "trade_id": str
            - "instrument": str
            - "units": int（正=買い、負=売り）
            - "unrealized_pl": float
        """

    @abstractmethod
    def close_position(self, trade_id: str) -> dict:
        """
        指定したポジションを決済する。

        キルスイッチから呼び出される。

        Args:
            trade_id: 決済対象のトレードID

        Returns:
            決済結果を含むdict。最低限 "trade_id", "realized_pl" キーを含む。
        """

    @abstractmethod
    def get_account_summary(self) -> dict:
        """
        口座残高・証拠金情報を取得する。

        リスク計算（ポジションサイジング等）に使用する。

        Returns:
            口座情報のdict。最低限以下を含む:
            - "balance": float（口座残高）
            - "unrealized_pl": float（未実現損益）
            - "margin_used": float（使用証拠金）
            - "margin_available": float（利用可能証拠金）
        """

    def get_spread(self, instrument: str) -> Optional[float]:
        """
        現在のbid-askスプレッドを取得する。

        キルスイッチのスプレッド監視に使用する。
        デフォルト実装は None を返す（未対応ブローカー向け）。
        MT5Client等でオーバーライドして実装する。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）

        Returns:
            スプレッド値（価格差）。未対応の場合は None。
        """
        return None

    def get_closed_deal(self, trade_id: str) -> Optional[dict]:
        """
        ブローカー側で既に決済済みのポジションの決済情報を取得する。

        SL/TP発動でブローカーが自動決済した場合、close_position()を経由しないため
        ローカル側に close_price/realized_pl が残らない。ブローカーの取引履歴から
        事後的に復元するために使用する。

        デフォルト実装は None を返す（未対応ブローカー向け）。
        MT5Client等でオーバーライドして実装する。

        Args:
            trade_id: ポジションID

        Returns:
            決済情報のdict。最低限以下を含む:
                - "close_price": float（決済価格）
                - "realized_pl": float（実現損益）
            取得失敗または未対応の場合は None。
        """
        return None
