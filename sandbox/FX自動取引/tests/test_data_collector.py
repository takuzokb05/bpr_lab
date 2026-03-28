"""
F5: data_collector.py のユニットテスト

モックBrokerClientを使って価格データの取得・保存・読み込み・差分更新をテストする。
実APIへのアクセスは一切行わない。SQLiteは :memory: を使用してテスト後に自動クリーンアップ。
"""

from unittest.mock import MagicMock

import pytest
import pandas as pd

from src.broker_client import BrokerClient
from src.data_collector import DataCollector, DataCollectorError


# === テスト用のモック価格データ ===

def _make_mock_df(start: str = "2026-01-01", periods: int = 3) -> pd.DataFrame:
    """テスト用のOHLCV DataFrameを生成する"""
    dates = pd.date_range(start=start, periods=periods, freq="4h")
    data = {
        "open": [150.0 + i * 0.1 for i in range(periods)],
        "high": [150.5 + i * 0.1 for i in range(periods)],
        "low": [149.5 + i * 0.1 for i in range(periods)],
        "close": [150.3 + i * 0.1 for i in range(periods)],
        "volume": [1000 + i * 100 for i in range(periods)],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "time"
    return df


def _make_mock_client(return_df: pd.DataFrame | None = None) -> MagicMock:
    """モックBrokerClientを生成する"""
    mock = MagicMock(spec=BrokerClient)
    if return_df is not None:
        mock.get_prices.return_value = return_df
    return mock


# === テストクラス ===


class TestFetchAndStore:
    """fetch_and_store のテスト"""

    def test_data_is_stored_and_returned(self):
        """モックBrokerClientから返されたDataFrameがSQLiteに保存され、同じデータが返る"""
        mock_df = _make_mock_df()
        mock_client = _make_mock_client(mock_df)

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")
        result = collector.fetch_and_store("USD_JPY", 100, "H4")

        # APIから取得したデータと同じDataFrameが返る
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert list(result.columns) == ["open", "high", "low", "close", "volume"]

        # DBから読み込んでも同じデータが取得できる
        loaded = collector.load_from_db("USD_JPY", "H4")
        assert len(loaded) == 3
        assert loaded.iloc[0]["open"] == pytest.approx(150.0)
        assert loaded.iloc[0]["close"] == pytest.approx(150.3)
        assert loaded.iloc[0]["volume"] == 1000

    def test_empty_dataframe_returns_empty(self):
        """空のDataFrameが返された場合、空のDataFrameが返り、DBには保存されない"""
        empty_df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        mock_client = _make_mock_client(empty_df)

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")
        result = collector.fetch_and_store("USD_JPY", 100, "H4")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_broker_error_raises_data_collector_error(self):
        """BrokerClientがエラーを送出した場合、DataCollectorErrorにラップされる"""
        mock_client = _make_mock_client()
        mock_client.get_prices.side_effect = RuntimeError("API接続失敗")

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")

        with pytest.raises(DataCollectorError, match="価格データの取得に失敗"):
            collector.fetch_and_store("USD_JPY", 100, "H4")


class TestDuplicateElimination:
    """重複排除のテスト"""

    def test_duplicate_data_is_ignored(self):
        """同じデータを2回保存してもレコード数が増えない"""
        mock_df = _make_mock_df()
        mock_client = _make_mock_client(mock_df)

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")

        # 1回目の保存
        collector.fetch_and_store("USD_JPY", 100, "H4")
        loaded_1 = collector.load_from_db("USD_JPY", "H4")
        assert len(loaded_1) == 3

        # 2回目の保存（同じデータ）
        collector.fetch_and_store("USD_JPY", 100, "H4")
        loaded_2 = collector.load_from_db("USD_JPY", "H4")
        assert len(loaded_2) == 3  # レコード数は変わらない


class TestLoadFromDb:
    """load_from_db のテスト"""

    def test_load_returns_correct_dataframe(self):
        """保存済みデータをDataFrameとして正しく読み込める"""
        mock_df = _make_mock_df(periods=5)
        mock_client = _make_mock_client(mock_df)

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")
        collector.fetch_and_store("USD_JPY", 100, "H4")

        loaded = collector.load_from_db("USD_JPY", "H4")

        # カラムが正しい
        assert list(loaded.columns) == ["open", "high", "low", "close", "volume"]

        # インデックスがdatetimeである
        assert pd.api.types.is_datetime64_any_dtype(loaded.index)

        # time昇順でソートされている
        assert loaded.index.is_monotonic_increasing

        # レコード数が一致
        assert len(loaded) == 5

    def test_load_with_limit(self):
        """limitを指定した場合、指定数のレコードのみが返る"""
        mock_df = _make_mock_df(periods=10)
        mock_client = _make_mock_client(mock_df)

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")
        collector.fetch_and_store("USD_JPY", 100, "H4")

        loaded = collector.load_from_db("USD_JPY", "H4", limit=3)
        assert len(loaded) == 3

    def test_load_empty_returns_empty_dataframe(self):
        """データがない場合は空のDataFrameが返る"""
        mock_client = _make_mock_client()

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")
        loaded = collector.load_from_db("USD_JPY", "H4")

        assert isinstance(loaded, pd.DataFrame)
        assert len(loaded) == 0
        assert list(loaded.columns) == ["open", "high", "low", "close", "volume"]

    def test_load_different_instruments_are_separated(self):
        """異なる通貨ペアのデータが混在しない"""
        mock_df_usd = _make_mock_df(periods=3)
        mock_df_eur = _make_mock_df(start="2026-02-01", periods=2)

        mock_client = MagicMock(spec=BrokerClient)
        mock_client.get_prices.side_effect = [mock_df_usd, mock_df_eur]

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")
        collector.fetch_and_store("USD_JPY", 100, "H4")
        collector.fetch_and_store("EUR_USD", 100, "H4")

        loaded_usd = collector.load_from_db("USD_JPY", "H4")
        loaded_eur = collector.load_from_db("EUR_USD", "H4")

        assert len(loaded_usd) == 3
        assert len(loaded_eur) == 2


class TestUpdate:
    """update（差分更新）のテスト"""

    def test_initial_update_fetches_500_bars(self):
        """DBにデータがない場合は500本分を初期取得する"""
        mock_df = _make_mock_df(periods=5)
        mock_client = _make_mock_client(mock_df)

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")
        result = collector.update("USD_JPY", "H4")

        # get_pricesが500本で呼ばれたことを確認
        mock_client.get_prices.assert_called_once_with("USD_JPY", 500, "H4")
        assert len(result) == 5

    def test_incremental_update_fetches_only_new_data(self):
        """DB内の最新時刻以降のデータのみを取得する"""
        # 初期データ: 3本（00:00, 04:00, 08:00）
        initial_df = _make_mock_df(start="2026-01-01 00:00", periods=3)

        # 差分データ: 5本（00:00〜16:00）→ 08:00より後の 12:00, 16:00 の2本が新規
        full_df = _make_mock_df(start="2026-01-01 00:00", periods=5)

        mock_client = MagicMock(spec=BrokerClient)
        mock_client.get_prices.side_effect = [initial_df, full_df]

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")

        # 初期取得
        collector.fetch_and_store("USD_JPY", 100, "H4")
        assert len(collector.load_from_db("USD_JPY", "H4")) == 3

        # 差分更新
        new_data = collector.update("USD_JPY", "H4")

        # 差分は2本（12:00, 16:00）
        assert len(new_data) == 2

        # DB全体は5本
        all_data = collector.load_from_db("USD_JPY", "H4")
        assert len(all_data) == 5

    def test_update_with_no_new_data(self):
        """差分データがない場合は空のDataFrameが返る"""
        initial_df = _make_mock_df(start="2026-01-01", periods=3)

        mock_client = MagicMock(spec=BrokerClient)
        # 初期取得と差分取得で同じデータ
        mock_client.get_prices.side_effect = [initial_df, initial_df]

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")

        # 初期取得
        collector.fetch_and_store("USD_JPY", 100, "H4")

        # 差分更新（新しいデータなし）
        new_data = collector.update("USD_JPY", "H4")
        assert len(new_data) == 0

    def test_update_api_error_raises(self):
        """差分更新でAPI呼び出しが失敗した場合、DataCollectorErrorが送出される"""
        initial_df = _make_mock_df(periods=3)

        mock_client = MagicMock(spec=BrokerClient)
        mock_client.get_prices.side_effect = [initial_df, RuntimeError("API障害")]

        collector = DataCollector(broker_client=mock_client, db_path=":memory:")
        collector.fetch_and_store("USD_JPY", 100, "H4")

        with pytest.raises(DataCollectorError, match="差分更新の価格データ取得に失敗"):
            collector.update("USD_JPY", "H4")


class TestTableAutoCreation:
    """テーブル自動作成のテスト"""

    def test_creates_table_on_init(self):
        """DBファイルが存在しない状態から初期化できる"""
        mock_client = _make_mock_client()

        # :memory: は毎回新しいDBなのでテーブルが自動作成される
        collector = DataCollector(broker_client=mock_client, db_path=":memory:")

        # テーブルが存在することを確認（空の読み込みが成功する）
        loaded = collector.load_from_db("USD_JPY", "H4")
        assert isinstance(loaded, pd.DataFrame)
        assert len(loaded) == 0

    def test_creates_table_with_tmpfile(self, tmp_path):
        """tmpファイルで初期化してもテーブルが作成される"""
        db_file = tmp_path / "test_fx.db"
        mock_client = _make_mock_client()

        # ファイルがまだ存在しないことを確認
        assert not db_file.exists()

        collector = DataCollector(broker_client=mock_client, db_path=db_file)

        # ファイルが作成された
        assert db_file.exists()

        # データの読み書きが正常に動作する
        mock_df = _make_mock_df(periods=2)
        mock_client.get_prices.return_value = mock_df

        collector.fetch_and_store("USD_JPY", 10, "H4")
        loaded = collector.load_from_db("USD_JPY", "H4")
        assert len(loaded) == 2

    def test_existing_db_is_not_overwritten(self, tmp_path):
        """既存のDBファイルがあっても上書きされない"""
        db_file = tmp_path / "existing.db"
        mock_df = _make_mock_df(periods=3)

        # 1つ目のcollectorでデータを保存
        mock_client_1 = _make_mock_client(mock_df)
        collector_1 = DataCollector(broker_client=mock_client_1, db_path=db_file)
        collector_1.fetch_and_store("USD_JPY", 100, "H4")

        # 2つ目のcollectorで同じDBを開く
        mock_client_2 = _make_mock_client()
        collector_2 = DataCollector(broker_client=mock_client_2, db_path=db_file)

        # 1つ目で保存したデータが残っている
        loaded = collector_2.load_from_db("USD_JPY", "H4")
        assert len(loaded) == 3
