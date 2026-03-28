"""
F2: broker_client.py のユニットテスト

ABCインターフェースが正しく定義されているかを検証する。
"""

import pytest
import pandas as pd

from src.broker_client import BrokerClient


class DummyClient(BrokerClient):
    """テスト用のBrokerClient具象実装"""

    def get_prices(self, instrument: str, count: int, granularity: str) -> pd.DataFrame:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    def market_order(self, instrument: str, units: int, stop_loss: float, take_profit: float) -> dict:
        return {"order_id": "dummy"}

    def limit_order(self, instrument: str, units: int, price: float, stop_loss: float, take_profit: float) -> dict:
        return {"order_id": "dummy"}

    def get_positions(self) -> list[dict]:
        return []

    def close_position(self, trade_id: str) -> dict:
        return {"trade_id": trade_id, "realized_pl": 0.0}

    def get_account_summary(self) -> dict:
        return {"balance": 0.0, "unrealized_pl": 0.0, "margin_used": 0.0, "margin_available": 0.0}


class IncompleteClient(BrokerClient):
    """一部メソッドが未実装のクライアント（インスタンス化不可のはず）"""
    pass


class TestBrokerClientInterface:
    """BrokerClientインターフェースのテスト"""

    def test_cannot_instantiate_abc(self):
        """ABCは直接インスタンス化できない"""
        with pytest.raises(TypeError):
            BrokerClient()

    def test_cannot_instantiate_incomplete(self):
        """抽象メソッドが未実装の場合インスタンス化できない"""
        with pytest.raises(TypeError):
            IncompleteClient()

    def test_can_instantiate_complete(self):
        """全メソッド実装済みならインスタンス化できる"""
        client = DummyClient()
        assert isinstance(client, BrokerClient)

    def test_has_six_abstract_methods(self):
        """6つの抽象メソッドが定義されている"""
        abstract_methods = BrokerClient.__abstractmethods__
        assert len(abstract_methods) == 6
        expected = {"get_prices", "market_order", "limit_order", "get_positions", "close_position", "get_account_summary"}
        assert abstract_methods == expected

    def test_get_prices_returns_dataframe(self):
        """get_pricesはDataFrameを返す"""
        client = DummyClient()
        result = client.get_prices("USD_JPY", 100, "H4")
        assert isinstance(result, pd.DataFrame)

    def test_market_order_returns_dict(self):
        """market_orderはdictを返す"""
        client = DummyClient()
        result = client.market_order("USD_JPY", 1000, 149.0, 152.0)
        assert isinstance(result, dict)
        assert "order_id" in result

    def test_limit_order_returns_dict(self):
        """limit_orderはdictを返す"""
        client = DummyClient()
        result = client.limit_order("USD_JPY", 1000, 150.0, 149.0, 152.0)
        assert isinstance(result, dict)
        assert "order_id" in result

    def test_get_positions_returns_list(self):
        """get_positionsはlistを返す"""
        client = DummyClient()
        result = client.get_positions()
        assert isinstance(result, list)

    def test_close_position_returns_dict(self):
        """close_positionはdictを返す"""
        client = DummyClient()
        result = client.close_position("12345")
        assert isinstance(result, dict)
        assert "trade_id" in result

    def test_get_account_summary_returns_dict(self):
        """get_account_summaryはdictを返す"""
        client = DummyClient()
        result = client.get_account_summary()
        assert isinstance(result, dict)
        assert "balance" in result
