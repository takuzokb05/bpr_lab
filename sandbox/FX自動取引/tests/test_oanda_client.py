"""
F3: oanda_client.py のユニットテスト

モックを使ってOANDA APIとの通信をテストする（デモ口座への実接続は不要）。
"""

from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

from src.oanda_client import OandaClient, OandaClientError
from src.broker_client import BrokerClient


# === テスト用のモックレスポンス ===

MOCK_CANDLES_RESPONSE = {
    "instrument": "USD_JPY",
    "granularity": "H4",
    "candles": [
        {
            "complete": True,
            "mid": {"o": "150.100", "h": "150.500", "l": "149.800", "c": "150.300"},
            "time": "2026-01-01T00:00:00.000000000Z",
            "volume": 1234,
        },
        {
            "complete": True,
            "mid": {"o": "150.300", "h": "150.700", "l": "150.000", "c": "150.500"},
            "time": "2026-01-01T04:00:00.000000000Z",
            "volume": 5678,
        },
        {
            "complete": False,  # 未完成 → スキップされる
            "mid": {"o": "150.500", "h": "150.600", "l": "150.400", "c": "150.550"},
            "time": "2026-01-01T08:00:00.000000000Z",
            "volume": 100,
        },
    ],
}

MOCK_MARKET_ORDER_RESPONSE = {
    "orderFillTransaction": {
        "id": "100",
        "type": "ORDER_FILL",
        "instrument": "USD_JPY",
        "units": "1000",
        "price": "150.200",
        "tradeOpened": {"tradeID": "101"},
    }
}

MOCK_LIMIT_ORDER_RESPONSE = {
    "orderCreateTransaction": {
        "id": "200",
        "type": "LIMIT_ORDER",
        "instrument": "USD_JPY",
        "units": "1000",
        "price": "149.500",
    }
}

MOCK_TRADES_RESPONSE = {
    "trades": [
        {
            "id": "101",
            "instrument": "USD_JPY",
            "currentUnits": "1000",
            "unrealizedPL": "500.0",
            "price": "150.200",
        },
        {
            "id": "102",
            "instrument": "EUR_USD",
            "currentUnits": "-2000",
            "unrealizedPL": "-200.0",
            "price": "1.05000",
        },
    ]
}

MOCK_CLOSE_RESPONSE = {
    "orderFillTransaction": {
        "id": "300",
        "price": "150.500",
        "pl": "300.0",
    }
}

MOCK_ACCOUNT_RESPONSE = {
    "account": {
        "balance": "1000000",
        "unrealizedPL": "5000",
        "marginUsed": "52500",
        "marginAvailable": "947500",
        "openTradeCount": 2,
        "currency": "JPY",
    }
}


@pytest.fixture
def mock_client():
    """モックされたOANDA APIを持つOandaClientを生成"""
    with patch("src.oanda_client.API") as MockAPI:
        mock_api_instance = MagicMock()
        MockAPI.return_value = mock_api_instance
        client = OandaClient(
            api_key="test-key",
            account_id="test-account-123",
            environment="practice",
        )
        client._api = mock_api_instance
        yield client, mock_api_instance


class TestOandaClientInit:
    """初期化のテスト"""

    def test_init_with_valid_credentials(self):
        """正常な認証情報で初期化できる"""
        with patch("src.oanda_client.API"):
            client = OandaClient(
                api_key="test-key",
                account_id="test-account",
                environment="practice",
            )
            assert isinstance(client, BrokerClient)

    def test_init_without_api_key_raises(self):
        """APIキーなしでOandaClientErrorが送出される"""
        with patch("src.oanda_client.OANDA_API_KEY", ""), \
             pytest.raises(OandaClientError, match="APIキー"):
            OandaClient(api_key="", account_id="test-account")

    def test_init_without_account_id_raises(self):
        """口座IDなしでOandaClientErrorが送出される"""
        with patch("src.oanda_client.OANDA_ACCOUNT_ID", ""), \
             pytest.raises(OandaClientError, match="口座ID"):
            OandaClient(api_key="test-key", account_id="")


class TestGetPrices:
    """get_prices のテスト"""

    def test_returns_dataframe_with_correct_columns(self, mock_client):
        """正しいカラムを持つDataFrameが返る"""
        client, mock_api = mock_client
        mock_api.request.return_value = MOCK_CANDLES_RESPONSE

        df = client.get_prices("USD_JPY", 100, "H4")

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]

    def test_skips_incomplete_candles(self, mock_client):
        """未完成のローソク足はスキップされる"""
        client, mock_api = mock_client
        mock_api.request.return_value = MOCK_CANDLES_RESPONSE

        df = client.get_prices("USD_JPY", 100, "H4")

        # 3本中1本が未完成なので2本
        assert len(df) == 2

    def test_correct_ohlcv_values(self, mock_client):
        """OHLCV値が正しく変換される"""
        client, mock_api = mock_client
        mock_api.request.return_value = MOCK_CANDLES_RESPONSE

        df = client.get_prices("USD_JPY", 100, "H4")

        assert df.iloc[0]["open"] == 150.100
        assert df.iloc[0]["high"] == 150.500
        assert df.iloc[0]["low"] == 149.800
        assert df.iloc[0]["close"] == 150.300
        assert df.iloc[0]["volume"] == 1234

    def test_empty_candles_returns_empty_dataframe(self, mock_client):
        """空のレスポンスで空DataFrameが返る"""
        client, mock_api = mock_client
        mock_api.request.return_value = {"candles": []}

        df = client.get_prices("USD_JPY", 100, "H4")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestMarketOrder:
    """market_order のテスト"""

    def test_returns_order_info(self, mock_client):
        """注文情報が正しく返る"""
        client, mock_api = mock_client
        mock_api.request.return_value = MOCK_MARKET_ORDER_RESPONSE

        result = client.market_order("USD_JPY", 1000, 149.0, 152.0)

        assert result["order_id"] == "100"
        assert result["trade_id"] == "101"
        assert result["price"] == 150.200
        assert result["status"] == "filled"

    def test_pending_order(self, mock_client):
        """即時約定しなかった場合のハンドリング"""
        client, mock_api = mock_client
        mock_api.request.return_value = {
            "orderCreateTransaction": {"id": "999"}
        }

        result = client.market_order("USD_JPY", 1000, 149.0, 152.0)

        assert result["status"] == "pending"
        assert result["order_id"] == "999"


class TestLimitOrder:
    """limit_order のテスト"""

    def test_returns_order_info(self, mock_client):
        """指値注文の情報が正しく返る"""
        client, mock_api = mock_client
        mock_api.request.return_value = MOCK_LIMIT_ORDER_RESPONSE

        result = client.limit_order("USD_JPY", 1000, 149.5, 148.5, 151.0)

        assert result["order_id"] == "200"
        assert result["price"] == 149.5
        assert result["status"] == "pending"


class TestGetPositions:
    """get_positions のテスト"""

    def test_returns_position_list(self, mock_client):
        """ポジション一覧が正しく返る"""
        client, mock_api = mock_client
        mock_api.request.return_value = MOCK_TRADES_RESPONSE

        positions = client.get_positions()

        assert len(positions) == 2
        assert positions[0]["trade_id"] == "101"
        assert positions[0]["instrument"] == "USD_JPY"
        assert positions[0]["units"] == 1000
        assert positions[0]["unrealized_pl"] == 500.0

    def test_short_position_units(self, mock_client):
        """売りポジションのunitsが負の値"""
        client, mock_api = mock_client
        mock_api.request.return_value = MOCK_TRADES_RESPONSE

        positions = client.get_positions()

        assert positions[1]["units"] == -2000

    def test_empty_positions(self, mock_client):
        """ポジションなしで空リストが返る"""
        client, mock_api = mock_client
        mock_api.request.return_value = {"trades": []}

        positions = client.get_positions()

        assert positions == []


class TestClosePosition:
    """close_position のテスト"""

    def test_returns_close_result(self, mock_client):
        """決済結果が正しく返る"""
        client, mock_api = mock_client
        mock_api.request.return_value = MOCK_CLOSE_RESPONSE

        result = client.close_position("101")

        assert result["trade_id"] == "101"
        assert result["realized_pl"] == 300.0
        assert result["close_price"] == 150.5


class TestGetAccountSummary:
    """get_account_summary のテスト"""

    def test_returns_account_info(self, mock_client):
        """口座情報が正しく返る"""
        client, mock_api = mock_client
        mock_api.request.return_value = MOCK_ACCOUNT_RESPONSE

        summary = client.get_account_summary()

        assert summary["balance"] == 1000000.0
        assert summary["unrealized_pl"] == 5000.0
        assert summary["margin_used"] == 52500.0
        assert summary["margin_available"] == 947500.0
        assert summary["open_trade_count"] == 2
        assert summary["currency"] == "JPY"


class TestRetryLogic:
    """リトライロジックのテスト"""

    def test_retries_on_connection_error(self, mock_client):
        """接続エラー時にリトライする"""
        client, mock_api = mock_client
        mock_api.request.side_effect = [
            ConnectionError("接続失敗"),
            MOCK_ACCOUNT_RESPONSE,
        ]

        with patch("src.oanda_client.time.sleep"):
            summary = client.get_account_summary()

        assert summary["balance"] == 1000000.0
        assert mock_api.request.call_count == 2

    def test_raises_after_max_retries(self, mock_client):
        """最大リトライ超過でOandaClientErrorを送出"""
        client, mock_api = mock_client
        mock_api.request.side_effect = ConnectionError("接続失敗")

        with patch("src.oanda_client.time.sleep"), \
             pytest.raises(OandaClientError, match="最大リトライ"):
            client.get_account_summary()

        # 初回 + 3回リトライ = 4回
        assert mock_api.request.call_count == 4

    def test_no_retry_on_client_error(self, mock_client):
        """4xxクライアントエラーではリトライしない"""
        from oandapyV20.exceptions import V20Error

        client, mock_api = mock_client
        error = V20Error(code=400, msg="Bad Request")
        mock_api.request.side_effect = error

        with pytest.raises(OandaClientError):
            client.get_account_summary()

        # リトライなし = 1回のみ
        assert mock_api.request.call_count == 1
