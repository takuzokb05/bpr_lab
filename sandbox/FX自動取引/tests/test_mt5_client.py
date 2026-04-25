"""
MT5Client のユニットテスト

MetaTrader5モジュール全体をモックしてテストする（MT5ターミナル不要）。
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.broker_client import BrokerClient


# ================================================================
# MT5モジュールのモック
# ================================================================


def _make_mt5_mock() -> MagicMock:
    """全定数・関数を持つMT5モジュールモックを生成する。"""
    mock = MagicMock()

    # タイムフレーム定数
    mock.TIMEFRAME_M1 = 1
    mock.TIMEFRAME_M5 = 5
    mock.TIMEFRAME_M15 = 15
    mock.TIMEFRAME_M30 = 30
    mock.TIMEFRAME_H1 = 16385
    mock.TIMEFRAME_H4 = 16388
    mock.TIMEFRAME_D1 = 16408
    mock.TIMEFRAME_W1 = 32769
    mock.TIMEFRAME_MN1 = 49153

    # 注文タイプ定数
    mock.ORDER_TYPE_BUY = 0
    mock.ORDER_TYPE_SELL = 1
    mock.ORDER_TYPE_BUY_LIMIT = 2
    mock.ORDER_TYPE_SELL_LIMIT = 3

    # 取引アクション定数
    mock.TRADE_ACTION_DEAL = 1
    mock.TRADE_ACTION_PENDING = 5

    # 注文時間・フィリング定数
    mock.ORDER_TIME_GTC = 0
    mock.ORDER_FILLING_FOK = 0
    mock.ORDER_FILLING_IOC = 1
    mock.ORDER_FILLING_RETURN = 2

    # 戻りコード定数
    mock.TRADE_RETCODE_DONE = 10009
    mock.TRADE_RETCODE_REQUOTE = 10004
    mock.TRADE_RETCODE_TIMEOUT = 10012
    mock.TRADE_RETCODE_CONNECTION = 10014

    return mock


@pytest.fixture
def mt5_mock():
    """MT5モジュールをモックしてMt5Clientをインポート可能にする。"""
    mock = _make_mt5_mock()

    # initialize() 成功、account_info() で口座情報を返す
    mock.initialize.return_value = True
    mock_account = MagicMock()
    mock_account.login = 22005467
    mock_account.server = "GaitameFinest-Demo"
    mock_account.balance = 1000000.0
    mock_account.currency = "JPY"
    mock.account_info.return_value = mock_account

    # symbol_info: フィリングモード（IOC対応）
    mock_symbol_info = MagicMock()
    mock_symbol_info.filling_mode = 2  # IOC
    mock.symbol_info.return_value = mock_symbol_info

    # order_check: デフォルトで成功（retcode=0）
    mock_check_result = MagicMock()
    mock_check_result.retcode = 0
    mock.order_check.return_value = mock_check_result

    with patch.dict("sys.modules", {"MetaTrader5": mock}):
        with patch("src.mt5_client.mt5", mock):
            yield mock


@pytest.fixture
def client(mt5_mock):
    """モックされたMT5で初期化済みのMt5Clientを返す。"""
    from src.mt5_client import Mt5Client

    return Mt5Client()


# ================================================================
# シンボル変換のテスト
# ================================================================


class TestSymbolConversion:
    """シンボル名変換のテスト"""

    def test_to_mt5_symbol(self, mt5_mock):
        from src.mt5_client import to_mt5_symbol

        assert to_mt5_symbol("USD_JPY") == "USDJPY-"
        assert to_mt5_symbol("EUR_USD") == "EURUSD-"
        assert to_mt5_symbol("GBP_JPY") == "GBPJPY-"

    def test_from_mt5_symbol(self, mt5_mock):
        from src.mt5_client import from_mt5_symbol

        assert from_mt5_symbol("USDJPY-") == "USD_JPY"
        assert from_mt5_symbol("EURUSD-") == "EUR_USD"
        assert from_mt5_symbol("GBPJPY-") == "GBP_JPY"

    def test_roundtrip_conversion(self, mt5_mock):
        """BrokerClient形式 → MT5形式 → BrokerClient形式のラウンドトリップ"""
        from src.mt5_client import from_mt5_symbol, to_mt5_symbol

        instruments = ["USD_JPY", "EUR_USD", "GBP_JPY", "AUD_USD", "EUR_JPY"]
        for inst in instruments:
            assert from_mt5_symbol(to_mt5_symbol(inst)) == inst


# ================================================================
# タイムフレーム変換のテスト
# ================================================================


class TestTimeframeConversion:
    """タイムフレーム変換のテスト"""

    def test_known_timeframes(self, mt5_mock):
        from src.mt5_client import to_mt5_timeframe

        assert to_mt5_timeframe("H4") == mt5_mock.TIMEFRAME_H4
        assert to_mt5_timeframe("D") == mt5_mock.TIMEFRAME_D1
        assert to_mt5_timeframe("M15") == mt5_mock.TIMEFRAME_M15
        assert to_mt5_timeframe("H1") == mt5_mock.TIMEFRAME_H1

    def test_unknown_timeframe_raises(self, mt5_mock):
        from src.mt5_client import to_mt5_timeframe

        with pytest.raises(ValueError, match="未対応のタイムフレーム"):
            to_mt5_timeframe("X1")


# ================================================================
# 初期化のテスト
# ================================================================


class TestMt5ClientInit:
    """Mt5Client初期化のテスト"""

    def test_is_broker_client(self, client):
        """BrokerClientのサブクラスである"""
        assert isinstance(client, BrokerClient)

    def test_init_success(self, mt5_mock):
        """正常に初期化できる"""
        from src.mt5_client import Mt5Client

        client = Mt5Client()
        mt5_mock.initialize.assert_called_once()

    def test_init_failure_raises(self, mt5_mock):
        """MT5ターミナル接続失敗でMt5ClientErrorが送出される"""
        from src.mt5_client import Mt5Client, Mt5ClientError

        mt5_mock.initialize.return_value = False
        mt5_mock.last_error.return_value = (-1, "Terminal not found")

        with pytest.raises(Mt5ClientError, match="接続に失敗"):
            Mt5Client()


# ================================================================
# get_prices のテスト
# ================================================================


class TestGetPrices:
    """get_pricesのテスト"""

    def test_returns_dataframe_with_correct_columns(self, client, mt5_mock):
        """正しいカラムを持つDataFrameが返る"""
        # numpy structured arrayを生成（MT5のcopy_rates_from_posの戻り値）
        rates = np.array(
            [
                (1704067200, 150.1, 150.5, 149.8, 150.3, 1234, 31, 0),
                (1704081600, 150.3, 150.7, 150.0, 150.5, 5678, 28, 0),
            ],
            dtype=[
                ("time", "i8"),
                ("open", "f8"),
                ("high", "f8"),
                ("low", "f8"),
                ("close", "f8"),
                ("tick_volume", "i8"),
                ("spread", "i4"),
                ("real_volume", "i8"),
            ],
        )
        mt5_mock.copy_rates_from_pos.return_value = rates

        df = client.get_prices("USD_JPY", 100, "H4")

        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert len(df) == 2

    def test_correct_ohlcv_values(self, client, mt5_mock):
        """OHLCV値が正しく変換される"""
        rates = np.array(
            [(1704067200, 150.1, 150.5, 149.8, 150.3, 1234, 31, 0)],
            dtype=[
                ("time", "i8"),
                ("open", "f8"),
                ("high", "f8"),
                ("low", "f8"),
                ("close", "f8"),
                ("tick_volume", "i8"),
                ("spread", "i4"),
                ("real_volume", "i8"),
            ],
        )
        mt5_mock.copy_rates_from_pos.return_value = rates

        df = client.get_prices("USD_JPY", 100, "H4")

        assert df.iloc[0]["open"] == pytest.approx(150.1)
        assert df.iloc[0]["high"] == pytest.approx(150.5)
        assert df.iloc[0]["low"] == pytest.approx(149.8)
        assert df.iloc[0]["close"] == pytest.approx(150.3)
        assert df.iloc[0]["volume"] == 1234

    def test_empty_data_returns_empty_dataframe(self, client, mt5_mock):
        """空のデータで空DataFrameが返る"""
        mt5_mock.copy_rates_from_pos.return_value = np.array(
            [],
            dtype=[
                ("time", "i8"),
                ("open", "f8"),
                ("high", "f8"),
                ("low", "f8"),
                ("close", "f8"),
                ("tick_volume", "i8"),
                ("spread", "i4"),
                ("real_volume", "i8"),
            ],
        )

        df = client.get_prices("USD_JPY", 100, "H4")

        assert len(df) == 0

    def test_symbol_conversion_in_request(self, client, mt5_mock):
        """get_pricesがMT5形式のシンボルでAPIを呼ぶ"""
        rates = np.array(
            [(1704067200, 150.1, 150.5, 149.8, 150.3, 1234, 31, 0)],
            dtype=[
                ("time", "i8"),
                ("open", "f8"),
                ("high", "f8"),
                ("low", "f8"),
                ("close", "f8"),
                ("tick_volume", "i8"),
                ("spread", "i4"),
                ("real_volume", "i8"),
            ],
        )
        mt5_mock.copy_rates_from_pos.return_value = rates

        client.get_prices("USD_JPY", 100, "H4")

        # "USDJPY-" で呼ばれている
        call_args = mt5_mock.copy_rates_from_pos.call_args
        assert call_args[0][0] == "USDJPY-"


# ================================================================
# market_order のテスト
# ================================================================


class TestMarketOrder:
    """market_orderのテスト"""

    def _setup_order_mock(self, mt5_mock, bid=152.700, ask=152.730):
        """注文用のモックを準備する。"""
        mock_tick = MagicMock()
        mock_tick.bid = bid
        mock_tick.ask = ask
        mt5_mock.symbol_info_tick.return_value = mock_tick

        mock_result = MagicMock()
        mock_result.retcode = mt5_mock.TRADE_RETCODE_DONE
        mock_result.order = 12345
        mock_result.price = ask
        mock_result.comment = "Request executed"
        mt5_mock.order_send.return_value = mock_result

        return mock_result

    def test_buy_order(self, client, mt5_mock):
        """買い注文が正しく発注される"""
        self._setup_order_mock(mt5_mock)

        result = client.market_order("USD_JPY", 10000, 152.0, 154.0)

        assert result["status"] == "filled"
        assert result["order_id"] == "12345"
        assert result["units"] == 10000

        # market_order は1回目=約定、2回目=SL/TP設定 で order_send を2回呼ぶ
        # 約定リクエストを検証
        deal_request = mt5_mock.order_send.call_args_list[0][0][0]
        assert deal_request["symbol"] == "USDJPY-"
        assert deal_request["type"] == mt5_mock.ORDER_TYPE_BUY
        assert deal_request["volume"] == 0.1  # 10000 / 100000
        assert deal_request["action"] == mt5_mock.TRADE_ACTION_DEAL

        # SL/TPリクエストを検証
        sltp_request = mt5_mock.order_send.call_args_list[1][0][0]
        assert sltp_request["action"] == mt5_mock.TRADE_ACTION_SLTP
        assert sltp_request["sl"] == 152.0
        assert sltp_request["tp"] == 154.0

    def test_sell_order(self, client, mt5_mock):
        """売り注文が正しく発注される（unitsが負）"""
        mock_result = self._setup_order_mock(mt5_mock)
        mock_result.price = 152.700  # bid

        result = client.market_order("USD_JPY", -10000, 154.0, 152.0)

        assert result["status"] == "filled"
        assert result["units"] == -10000

        deal_request = mt5_mock.order_send.call_args_list[0][0][0]
        assert deal_request["type"] == mt5_mock.ORDER_TYPE_SELL

    def test_tick_unavailable_raises(self, client, mt5_mock):
        """ティック取得失敗でMt5ClientErrorが送出される"""
        from src.mt5_client import Mt5ClientError

        mt5_mock.symbol_info_tick.return_value = None

        with pytest.raises(Mt5ClientError, match="ティック情報"):
            client.market_order("USD_JPY", 10000, 152.0, 154.0)


# ================================================================
# limit_order のテスト
# ================================================================


class TestLimitOrder:
    """limit_orderのテスト"""

    def test_buy_limit(self, client, mt5_mock):
        """買い指値注文が正しく発注される"""
        mock_result = MagicMock()
        mock_result.retcode = mt5_mock.TRADE_RETCODE_DONE
        mock_result.order = 23456
        mock_result.comment = "Request executed"
        mt5_mock.order_send.return_value = mock_result

        result = client.limit_order("USD_JPY", 10000, 151.0, 150.0, 153.0)

        assert result["order_id"] == "23456"
        assert result["status"] == "pending"
        assert result["price"] == 151.0

        call_args = mt5_mock.order_send.call_args[0][0]
        assert call_args["type"] == mt5_mock.ORDER_TYPE_BUY_LIMIT
        assert call_args["action"] == mt5_mock.TRADE_ACTION_PENDING

    def test_sell_limit(self, client, mt5_mock):
        """売り指値注文が正しく発注される"""
        mock_result = MagicMock()
        mock_result.retcode = mt5_mock.TRADE_RETCODE_DONE
        mock_result.order = 34567
        mock_result.comment = "Request executed"
        mt5_mock.order_send.return_value = mock_result

        result = client.limit_order("EUR_USD", -10000, 1.1000, 1.1100, 1.0900)

        call_args = mt5_mock.order_send.call_args[0][0]
        assert call_args["type"] == mt5_mock.ORDER_TYPE_SELL_LIMIT
        assert call_args["symbol"] == "EURUSD-"


# ================================================================
# get_positions のテスト
# ================================================================


class TestGetPositions:
    """get_positionsのテスト"""

    def _make_position(
        self,
        ticket=101,
        symbol="USDJPY-",
        pos_type=0,
        volume=0.1,
        profit=500.0,
        price_open=152.0,
    ):
        """テスト用ポジションオブジェクトを生成。"""
        pos = MagicMock()
        pos.ticket = ticket
        pos.symbol = symbol
        pos.type = pos_type
        pos.volume = volume
        pos.profit = profit
        pos.price_open = price_open
        return pos

    def test_returns_position_list(self, client, mt5_mock):
        """ポジション一覧が正しく返る"""
        mt5_mock.positions_get.return_value = (
            self._make_position(ticket=101, symbol="USDJPY-", pos_type=0),
            self._make_position(ticket=102, symbol="EURUSD-", pos_type=1),
        )

        positions = client.get_positions()

        assert len(positions) == 2
        assert positions[0]["trade_id"] == "101"
        assert positions[0]["instrument"] == "USD_JPY"
        assert positions[0]["units"] == 10000  # 0.1 * 100000
        assert positions[0]["unrealized_pl"] == 500.0

    def test_sell_position_units_negative(self, client, mt5_mock):
        """売りポジションのunitsが負の値"""
        mt5_mock.positions_get.return_value = (
            self._make_position(pos_type=1, volume=0.05),
        )

        positions = client.get_positions()

        assert positions[0]["units"] == -5000  # -0.05 * 100000

    def test_empty_positions(self, client, mt5_mock):
        """ポジションなしで空リストが返る"""
        mt5_mock.positions_get.return_value = ()

        positions = client.get_positions()

        assert positions == []

    def test_positions_none_raises_error(self, client, mt5_mock):
        """positions_getがNone（エラー）でMt5ClientErrorを送出する"""
        from src.mt5_client import Mt5ClientError

        mt5_mock.positions_get.return_value = None
        mt5_mock.last_error.return_value = (-1, "Error")

        with pytest.raises(Mt5ClientError, match="ポジション情報を取得できませんでした"):
            client.get_positions()


# ================================================================
# close_position のテスト
# ================================================================


class TestClosePosition:
    """close_positionのテスト"""

    def test_close_buy_position(self, client, mt5_mock):
        """買いポジションの決済（SELL注文で閉じる）"""
        # ポジション情報
        pos = MagicMock()
        pos.ticket = 101
        pos.symbol = "USDJPY-"
        pos.type = 0  # BUY
        pos.volume = 0.1
        pos.profit = 300.0
        mt5_mock.positions_get.return_value = (pos,)

        # ティック情報
        tick = MagicMock()
        tick.bid = 152.5
        tick.ask = 152.53
        mt5_mock.symbol_info_tick.return_value = tick

        # 決済結果
        close_result = MagicMock()
        close_result.retcode = mt5_mock.TRADE_RETCODE_DONE
        close_result.price = 152.5
        close_result.comment = "Request executed"
        mt5_mock.order_send.return_value = close_result

        result = client.close_position("101")

        assert result["trade_id"] == "101"
        assert result["realized_pl"] == 300.0
        assert result["close_price"] == 152.5

        # SELL注文で決済
        call_args = mt5_mock.order_send.call_args[0][0]
        assert call_args["type"] == mt5_mock.ORDER_TYPE_SELL
        assert call_args["position"] == 101

    def test_close_sell_position(self, client, mt5_mock):
        """売りポジションの決済（BUY注文で閉じる）"""
        pos = MagicMock()
        pos.ticket = 102
        pos.symbol = "EURUSD-"
        pos.type = 1  # SELL
        pos.volume = 0.05
        pos.profit = -100.0
        mt5_mock.positions_get.return_value = (pos,)

        tick = MagicMock()
        tick.bid = 1.1050
        tick.ask = 1.1053
        mt5_mock.symbol_info_tick.return_value = tick

        close_result = MagicMock()
        close_result.retcode = mt5_mock.TRADE_RETCODE_DONE
        close_result.price = 1.1053
        close_result.comment = "Request executed"
        mt5_mock.order_send.return_value = close_result

        result = client.close_position("102")

        call_args = mt5_mock.order_send.call_args[0][0]
        assert call_args["type"] == mt5_mock.ORDER_TYPE_BUY

    def test_position_not_found_raises(self, client, mt5_mock):
        """存在しないポジションでMt5ClientErrorが送出される"""
        from src.mt5_client import Mt5ClientError

        mt5_mock.positions_get.return_value = ()

        with pytest.raises(Mt5ClientError, match="ポジションが見つかりません"):
            client.close_position("999")


# ================================================================
# get_closed_deal のテスト
# ================================================================


class TestGetClosedDeal:
    """get_closed_dealのテスト（SL/TP自動決済時のPL復元）"""

    def _make_deal(self, *, entry, profit, price, time_ts, swap=0.0, commission=0.0):
        d = MagicMock()
        d.entry = entry
        d.profit = profit
        d.price = price
        d.time = time_ts
        d.swap = swap
        d.commission = commission
        return d

    def test_returns_close_info_for_sl_tp_triggered_position(self, client, mt5_mock):
        """SL/TPで自動決済されたポジションのclose_price/realized_plが復元される"""
        mt5_mock.DEAL_ENTRY_OUT = 1
        mt5_mock.DEAL_ENTRY_INOUT = 2
        # 開始deal（IN=0）と決済deal（OUT=1）
        deal_in = self._make_deal(entry=0, profit=0.0, price=150.0, time_ts=1000)
        deal_out = self._make_deal(
            entry=1, profit=423.5, price=150.85, time_ts=2000,
            swap=-1.0, commission=-2.5,
        )
        mt5_mock.history_deals_get.return_value = (deal_in, deal_out)

        result = client.get_closed_deal("8646754")

        assert result is not None
        assert result["trade_id"] == "8646754"
        assert result["close_price"] == 150.85
        # profit + swap + commission = 423.5 - 1.0 - 2.5
        assert result["realized_pl"] == pytest.approx(420.0)
        assert result["closed_at"].timestamp() == 2000

    def test_returns_none_when_history_empty(self, client, mt5_mock):
        """履歴が空ならNoneを返す"""
        mt5_mock.DEAL_ENTRY_OUT = 1
        mt5_mock.DEAL_ENTRY_INOUT = 2
        mt5_mock.history_deals_get.return_value = ()
        mt5_mock.last_error.return_value = (0, "Success")

        assert client.get_closed_deal("9999") is None

    def test_returns_none_when_no_close_deal(self, client, mt5_mock):
        """エントリーdealのみで決済dealが無い場合はNone"""
        mt5_mock.DEAL_ENTRY_OUT = 1
        mt5_mock.DEAL_ENTRY_INOUT = 2
        deal_in = self._make_deal(entry=0, profit=0.0, price=150.0, time_ts=1000)
        mt5_mock.history_deals_get.return_value = (deal_in,)

        assert client.get_closed_deal("8646754") is None

    def test_aggregates_partial_closes(self, client, mt5_mock):
        """複数の部分決済dealがあるとPLを合算し、最後の価格を採用"""
        mt5_mock.DEAL_ENTRY_OUT = 1
        mt5_mock.DEAL_ENTRY_INOUT = 2
        deal_in = self._make_deal(entry=0, profit=0.0, price=150.0, time_ts=1000)
        deal_out1 = self._make_deal(entry=1, profit=100.0, price=150.5, time_ts=2000)
        deal_out2 = self._make_deal(entry=1, profit=200.0, price=150.9, time_ts=3000)
        mt5_mock.history_deals_get.return_value = (deal_in, deal_out1, deal_out2)

        result = client.get_closed_deal("8646754")

        assert result["realized_pl"] == pytest.approx(300.0)
        assert result["close_price"] == 150.9  # 最後の決済価格
        assert result["closed_at"].timestamp() == 3000

    def test_invalid_trade_id_returns_none(self, client, mt5_mock):
        """数値変換できないtrade_idはNone"""
        assert client.get_closed_deal("not-a-number") is None


# ================================================================
# get_account_summary のテスト
# ================================================================


class TestGetAccountSummary:
    """get_account_summaryのテスト"""

    def test_returns_account_info(self, client, mt5_mock):
        """口座情報が正しく返る"""
        account = MagicMock()
        account.balance = 1000000.0
        account.profit = 5000.0
        account.margin = 52500.0
        account.margin_free = 947500.0
        account.currency = "JPY"
        mt5_mock.account_info.return_value = account
        mt5_mock.positions_get.return_value = (MagicMock(), MagicMock())

        summary = client.get_account_summary()

        assert summary["balance"] == 1000000.0
        assert summary["unrealized_pl"] == 5000.0
        assert summary["margin_used"] == 52500.0
        assert summary["margin_available"] == 947500.0
        assert summary["open_trade_count"] == 2
        assert summary["currency"] == "JPY"

    def test_account_info_failure_raises(self, client, mt5_mock):
        """口座情報取得失敗でMt5ClientErrorが送出される"""
        from src.mt5_client import Mt5ClientError

        mt5_mock.account_info.return_value = None
        mt5_mock.last_error.return_value = (-1, "Not connected")

        with pytest.raises(Mt5ClientError, match="口座情報を取得できませんでした"):
            client.get_account_summary()


# ================================================================
# リトライロジックのテスト
# ================================================================


class TestRetryLogic:
    """リトライロジックのテスト"""

    def test_retries_on_none_result(self, client, mt5_mock):
        """結果がNoneの場合にリトライする"""
        rates = np.array(
            [(1704067200, 150.1, 150.5, 149.8, 150.3, 1234, 31, 0)],
            dtype=[
                ("time", "i8"),
                ("open", "f8"),
                ("high", "f8"),
                ("low", "f8"),
                ("close", "f8"),
                ("tick_volume", "i8"),
                ("spread", "i4"),
                ("real_volume", "i8"),
            ],
        )
        mt5_mock.copy_rates_from_pos.side_effect = [None, rates]
        mt5_mock.last_error.return_value = (-1, "Temporary error")

        with patch("src.mt5_client.time.sleep"):
            df = client.get_prices("USD_JPY", 100, "H4")

        assert len(df) == 1
        assert mt5_mock.copy_rates_from_pos.call_count == 2

    def test_raises_after_max_retries(self, client, mt5_mock):
        """最大リトライ超過でMt5ClientErrorを送出"""
        from src.mt5_client import Mt5ClientError

        mt5_mock.copy_rates_from_pos.return_value = None
        mt5_mock.last_error.return_value = (-1, "Persistent error")

        with patch("src.mt5_client.time.sleep"), \
             pytest.raises(Mt5ClientError, match="最大リトライ"):
            client.get_prices("USD_JPY", 100, "H4")

        # 初回 + 3回リトライ = 4回
        assert mt5_mock.copy_rates_from_pos.call_count == 4

    def test_retries_on_requote(self, client, mt5_mock):
        """REQUOTE時にリトライする"""
        # ティック設定
        tick = MagicMock()
        tick.bid = 152.7
        tick.ask = 152.73
        mt5_mock.symbol_info_tick.return_value = tick

        # 1回目: REQUOTE、2回目: 成功
        requote_result = MagicMock()
        requote_result.retcode = mt5_mock.TRADE_RETCODE_REQUOTE
        requote_result.comment = "Requote"

        success_result = MagicMock()
        success_result.retcode = mt5_mock.TRADE_RETCODE_DONE
        success_result.order = 99999
        success_result.price = 152.73
        success_result.comment = "Done"

        # market_order は SL/TP設定で追加の order_send 呼び出しがある
        sltp_result = MagicMock()
        sltp_result.retcode = mt5_mock.TRADE_RETCODE_DONE
        sltp_result.comment = "SL/TP set"
        mt5_mock.order_send.side_effect = [requote_result, success_result, sltp_result]

        with patch("src.mt5_client.time.sleep"):
            result = client.market_order("USD_JPY", 10000, 152.0, 154.0)

        assert result["status"] == "filled"
        # 約定リトライ2回 + SL/TP設定1回 = 3回
        assert mt5_mock.order_send.call_count == 3

    def test_no_retry_on_invalid_request(self, client, mt5_mock):
        """リトライ不可能なエラーではリトライしない"""
        from src.mt5_client import Mt5ClientError

        tick = MagicMock()
        tick.bid = 152.7
        tick.ask = 152.73
        mt5_mock.symbol_info_tick.return_value = tick

        error_result = MagicMock()
        error_result.retcode = 10013  # Invalid request
        error_result.comment = "Invalid request"
        mt5_mock.order_send.return_value = error_result

        with pytest.raises(Mt5ClientError, match="MT5注文エラー"):
            client.market_order("USD_JPY", 10000, 152.0, 154.0)

        # リトライなし = 1回のみ
        assert mt5_mock.order_send.call_count == 1


# ================================================================
# フィリングモードのテスト
# ================================================================


class TestFindValidFilling:
    """_find_valid_fillingのテスト"""

    def test_fok_passes_check(self, client, mt5_mock):
        """FOKでorder_checkが通ればFOKが設定される"""
        # symbol_infoでFOK対応を返す
        sym_info = MagicMock()
        sym_info.filling_mode = 1  # SYMBOL_FILLING_FOK
        mt5_mock.symbol_info.return_value = sym_info

        check_ok = MagicMock()
        check_ok.retcode = 0
        mt5_mock.order_check.return_value = check_ok

        request = {"symbol": "USDJPY-", "type_filling": 999, "action": 1}
        result = client._find_valid_filling(request)
        assert result["type_filling"] == mt5_mock.ORDER_FILLING_FOK

    def test_fallback_to_ioc(self, client, mt5_mock):
        """FOK失敗→IOCで通る場合、IOCが設定される"""
        # symbol_infoでFOK+IOC対応を返す
        sym_info = MagicMock()
        sym_info.filling_mode = 3  # FOK(1) + IOC(2)
        mt5_mock.symbol_info.return_value = sym_info

        check_fail = MagicMock()
        check_fail.retcode = 10013
        check_fail.comment = "Invalid request"
        check_ok = MagicMock()
        check_ok.retcode = 0
        mt5_mock.order_check.side_effect = [check_fail, check_ok]

        request = {"symbol": "USDJPY-", "type_filling": 999, "action": 1}
        result = client._find_valid_filling(request)
        assert result["type_filling"] == mt5_mock.ORDER_FILLING_IOC

    def test_fallback_to_return(self, client, mt5_mock):
        """FOK/IOC両方失敗→RETURNで通る場合"""
        # symbol_infoでFOK+IOC対応だがorder_checkで両方失敗
        sym_info = MagicMock()
        sym_info.filling_mode = 3
        mt5_mock.symbol_info.return_value = sym_info

        check_fail = MagicMock()
        check_fail.retcode = 10013
        check_fail.comment = "Invalid request"
        check_ok = MagicMock()
        check_ok.retcode = 0
        # FOK失敗 → IOC失敗 → RETURN成功
        mt5_mock.order_check.side_effect = [check_fail, check_fail, check_ok]

        request = {"symbol": "USDJPY-", "type_filling": 999, "action": 1}
        result = client._find_valid_filling(request)
        assert result["type_filling"] == mt5_mock.ORDER_FILLING_RETURN

    def test_symbol_info_none_fallback(self, client, mt5_mock):
        """symbol_infoがNoneの場合は従来の全パターン試行にフォールバック"""
        mt5_mock.symbol_info.return_value = None

        check_fail = MagicMock()
        check_fail.retcode = 10013
        check_fail.comment = "Invalid request"
        check_ok = MagicMock()
        check_ok.retcode = 0
        mt5_mock.order_check.side_effect = [check_fail, check_ok]

        request = {"symbol": "USDJPY-", "type_filling": 999, "action": 1}
        result = client._find_valid_filling(request)
        assert result["type_filling"] == mt5_mock.ORDER_FILLING_IOC

    def test_filling_mode_return_only(self, client, mt5_mock):
        """filling_mode=0（FOK/IOCどちらも非対応）の場合、RETURNのみ試行"""
        sym_info = MagicMock()
        sym_info.filling_mode = 0  # FOK/IOCどちらも非対応
        mt5_mock.symbol_info.return_value = sym_info

        check_ok = MagicMock()
        check_ok.retcode = 0
        mt5_mock.order_check.return_value = check_ok

        request = {"symbol": "USDJPY-", "type_filling": 999, "action": 1}
        result = client._find_valid_filling(request)
        # RETURNのみが候補なので最初にRETURNが試行される
        assert result["type_filling"] == mt5_mock.ORDER_FILLING_RETURN

    def test_all_fail_raises(self, client, mt5_mock):
        """全フィリングタイプ失敗時はMt5ClientErrorを投げる"""
        from src.mt5_client import Mt5ClientError

        sym_info = MagicMock()
        sym_info.filling_mode = 3
        mt5_mock.symbol_info.return_value = sym_info

        check_fail = MagicMock()
        check_fail.retcode = 10013
        check_fail.comment = "Invalid request"
        mt5_mock.order_check.return_value = check_fail

        request = {"symbol": "USDJPY-", "type_filling": 999, "action": 1}
        with pytest.raises(Mt5ClientError, match="全フィリングタイプで失敗"):
            client._find_valid_filling(request)


# ================================================================
# _adjust_volume のテスト
# ================================================================


class TestAdjustVolume:
    """_adjust_volume のテスト（2026-04 retcode 10014 バグ回避）"""

    def _make_symbol_info(self, step=0.01, vmin=0.01, vmax=100.0):
        info = MagicMock()
        info.volume_step = step
        info.volume_min = vmin
        info.volume_max = vmax
        return info

    def test_rounds_down_to_step(self, client, mt5_mock):
        """端数付きvolumeがstepに整列される（0.39037 -> 0.39）"""
        mt5_mock.symbol_info.return_value = self._make_symbol_info(step=0.01)
        assert client._adjust_volume("AUDUSD-", 0.39037) == pytest.approx(0.39)

    def test_clamps_to_max(self, client, mt5_mock):
        """volume_maxを超える場合はvmaxにクランプ"""
        mt5_mock.symbol_info.return_value = self._make_symbol_info(
            step=0.01, vmax=50.0
        )
        assert client._adjust_volume("USDJPY-", 100.5) == 50.0

    def test_raises_when_below_min(self, client, mt5_mock):
        """丸め後にvolume_minを下回ればMt5ClientError"""
        from src.mt5_client import Mt5ClientError

        mt5_mock.symbol_info.return_value = self._make_symbol_info(
            step=0.1, vmin=0.1
        )
        with pytest.raises(Mt5ClientError, match="最小単位"):
            client._adjust_volume("USDJPY-", 0.05)

    def test_symbol_info_none_passes_through(self, client, mt5_mock):
        """symbol_infoがNoneなら丸めずそのまま返す"""
        mt5_mock.symbol_info.return_value = None
        assert client._adjust_volume("USDJPY-", 0.39037) == 0.39037

    def test_magic_mock_step_passes_through(self, client, mt5_mock):
        """volume_stepが数値でない（MagicMock等）ならスキップ（既存テスト互換）"""
        info = MagicMock()
        info.filling_mode = 2
        # volume_step を設定しない → MagicMock属性（非数値）
        mt5_mock.symbol_info.return_value = info
        assert client._adjust_volume("USDJPY-", 0.1) == 0.1


# ================================================================
# Context Manager のテスト
# ================================================================


class TestContextManager:
    """context managerのテスト"""

    def test_context_manager_calls_shutdown(self, mt5_mock):
        """withブロック終了時にshutdownが呼ばれる"""
        from src.mt5_client import Mt5Client

        with Mt5Client() as client:
            pass

        mt5_mock.shutdown.assert_called_once()
