"""
FX自動取引システム — 価格データ取得・管理モジュール

ブローカーAPIから価格データを取得し、SQLiteに保存・読み込みする。
SPEC.md F5 準拠。
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

from src.broker_client import BrokerClient
from src.config import DB_PATH

logger = logging.getLogger(__name__)


class DataCollectorError(Exception):
    """DataCollector固有のエラー"""


class DataCollector:
    """
    価格データの取得・保存・読み込みを管理するクラス。

    BrokerClientを通じてOHLCVデータを取得し、SQLiteに永続化する。
    差分更新により、必要最小限のAPI呼び出しでデータを最新に保つ。
    """

    def __init__(
        self,
        broker_client: BrokerClient,
        db_path: Path | None = None,
    ) -> None:
        """
        DataCollectorを初期化する。

        Args:
            broker_client: 価格データ取得に使うBrokerClient実装
            db_path: SQLiteデータベースのパス。省略時はconfig.DB_PATHを使用。
                     ":memory:" を指定するとインメモリDBを使用する（テスト用）。
        """
        self._client = broker_client
        self._db_path = db_path if db_path is not None else DB_PATH
        self._is_memory = str(self._db_path) == ":memory:"

        # データディレクトリが存在しなければ作成（:memory:の場合はスキップ）
        if not self._is_memory:
            self._db_path = Path(self._db_path)
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        # :memory: DBでは同一コネクションを使い回す（別コネクション=別DB）
        self._persistent_conn: sqlite3.Connection | None = None
        if self._is_memory:
            self._persistent_conn = sqlite3.connect(":memory:")

        self._init_db()
        logger.info("DataCollectorを初期化しました（DB: %s）", self._db_path)

    def close(self) -> None:
        """
        永続コネクションを閉じる。

        :memory: モードの場合のみコネクションを閉じる。
        ファイルモードでは都度接続のため何もしない。
        close()後のDB操作は未定義動作となる。
        """
        if self._persistent_conn is not None:
            self._persistent_conn.close()
            self._persistent_conn = None
            logger.info("DataCollectorの永続コネクションを閉じました")

    def __enter__(self) -> "DataCollector":
        """コンテキストマネージャのエントリ。"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャのイグジット。close()を呼ぶ。"""
        self.close()

    def _get_connection(self) -> sqlite3.Connection:
        """
        SQLiteコネクションを取得する。

        :memory: モードでは永続的な単一コネクションを返す。
        ファイルモードでは都度新規コネクションを作成する。

        Returns:
            sqlite3.Connection
        """
        if self._persistent_conn is not None:
            return self._persistent_conn
        return sqlite3.connect(str(self._db_path))

    def _close_connection(self, conn: sqlite3.Connection) -> None:
        """
        コネクションを閉じる。永続コネクション（:memory:）は閉じない。

        Args:
            conn: 閉じる対象のコネクション
        """
        if conn is not self._persistent_conn:
            conn.close()

    def _init_db(self) -> None:
        """
        SQLiteテーブルを作成する（存在しない場合のみ）。

        pricesテーブル:
        - instrument, granularity, time の複合主キーで重複を防止
        - timeはISO8601形式の文字列
        """
        create_sql = """
        CREATE TABLE IF NOT EXISTS prices (
            instrument TEXT NOT NULL,
            granularity TEXT NOT NULL,
            time TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            PRIMARY KEY (instrument, granularity, time)
        );
        """
        conn = self._get_connection()
        try:
            conn.execute(create_sql)
            conn.commit()
        except sqlite3.Error as e:
            raise DataCollectorError(
                f"データベースの初期化に失敗しました: {e}"
            ) from e
        finally:
            self._close_connection(conn)

    def fetch_and_store(
        self,
        instrument: str,
        count: int,
        granularity: str,
    ) -> pd.DataFrame:
        """
        ブローカーAPIから価格データを取得し、SQLiteに保存する。

        重複データはINSERT OR IGNOREにより自動的にスキップされる。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            count: 取得するローソク足の本数
            granularity: 時間足（例: "H4", "D", "M15"）

        Returns:
            取得したOHLCVデータのDataFrame

        Raises:
            DataCollectorError: データの取得または保存に失敗した場合
        """
        try:
            df = self._client.get_prices(instrument, count, granularity)
        except Exception as e:
            raise DataCollectorError(
                f"価格データの取得に失敗しました（{instrument}, {granularity}）: {e}"
            ) from e

        if df.empty:
            logger.warning(
                "取得した価格データが空です: instrument=%s, granularity=%s",
                instrument,
                granularity,
            )
            return df

        self._store_dataframe(df, instrument, granularity)
        logger.info(
            "価格データを取得・保存しました: instrument=%s, granularity=%s, %d本",
            instrument,
            granularity,
            len(df),
        )
        return df

    def _store_dataframe(
        self,
        df: pd.DataFrame,
        instrument: str,
        granularity: str,
    ) -> None:
        """
        DataFrameの内容をSQLiteに保存する。

        Args:
            df: OHLCV形式のDataFrame（インデックス: datetime）
            instrument: 通貨ペア
            granularity: 時間足
        """
        insert_sql = """
        INSERT OR IGNORE INTO prices
            (instrument, granularity, time, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        conn = self._get_connection()
        try:
            rows = []
            for timestamp, row in df.iterrows():
                time_str = pd.Timestamp(timestamp).isoformat()
                rows.append((
                    instrument,
                    granularity,
                    time_str,
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    int(row["volume"]),
                ))
            conn.executemany(insert_sql, rows)
            conn.commit()
        except sqlite3.Error as e:
            raise DataCollectorError(
                f"データベースへの保存に失敗しました: {e}"
            ) from e
        finally:
            self._close_connection(conn)

    def update(
        self,
        instrument: str,
        granularity: str,
    ) -> pd.DataFrame:
        """
        差分更新を実行する。

        DB内の最新タイムスタンプ以降のデータのみをAPIから取得し、DBに追記する。
        DBにデータがない場合は500本分を初期取得する。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            granularity: 時間足（例: "H4", "D", "M15"）

        Returns:
            今回取得したデータのDataFrame（差分のみ）

        Raises:
            DataCollectorError: データの取得または保存に失敗した場合
        """
        latest_time = self._get_latest_time(instrument, granularity)

        if latest_time is None:
            # DBにデータがない → 初期取得（500本）
            logger.info(
                "DBにデータがありません。初期取得を実行します: instrument=%s, granularity=%s, 500本",
                instrument,
                granularity,
            )
            return self.fetch_and_store(instrument, 500, granularity)

        # 差分取得: 最新時刻以降のデータを取得
        # APIは直近N本を返すので、十分な本数を指定して最新時刻以降を抽出
        logger.info(
            "差分更新を実行します: instrument=%s, granularity=%s, 最新=%s",
            instrument,
            granularity,
            latest_time,
        )

        try:
            df = self._client.get_prices(instrument, 500, granularity)
        except Exception as e:
            raise DataCollectorError(
                f"差分更新の価格データ取得に失敗しました（{instrument}, {granularity}）: {e}"
            ) from e

        if df.empty:
            logger.info("差分更新: 新しいデータはありません")
            return df

        # DB内の最新時刻より後のデータのみ抽出
        latest_ts = pd.Timestamp(latest_time)
        new_data = df[df.index > latest_ts]

        if new_data.empty:
            logger.info("差分更新: 新しいデータはありません")
            return new_data

        self._store_dataframe(new_data, instrument, granularity)
        logger.info(
            "差分更新完了: %d本の新しいデータを保存しました",
            len(new_data),
        )
        return new_data

    def _get_latest_time(
        self,
        instrument: str,
        granularity: str,
    ) -> str | None:
        """
        DB内の指定通貨ペア・時間足の最新タイムスタンプを取得する。

        Args:
            instrument: 通貨ペア
            granularity: 時間足

        Returns:
            最新のタイムスタンプ（ISO8601文字列）。データがなければNone。
        """
        query_sql = """
        SELECT MAX(time) FROM prices
        WHERE instrument = ? AND granularity = ?
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(query_sql, (instrument, granularity))
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
        except sqlite3.Error as e:
            raise DataCollectorError(
                f"最新タイムスタンプの取得に失敗しました: {e}"
            ) from e
        finally:
            self._close_connection(conn)

    def load_from_db(
        self,
        instrument: str,
        granularity: str,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        SQLiteから価格データをDataFrameとして読み込む。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            granularity: 時間足（例: "H4", "D", "M15"）
            limit: 取得するレコード数の上限。Noneで全件取得。

        Returns:
            OHLCV形式のDataFrame。カラム: open, high, low, close, volume
            インデックス: datetime（time昇順ソート済み）
        """
        query_sql = """
        SELECT time, open, high, low, close, volume
        FROM prices
        WHERE instrument = ? AND granularity = ?
        ORDER BY time ASC
        """
        params: list = [instrument, granularity]

        if limit is not None:
            query_sql += " LIMIT ?"
            params.append(limit)

        conn = self._get_connection()
        try:
            df = pd.read_sql_query(query_sql, conn, params=params)
        except (sqlite3.Error, pd.errors.DatabaseError) as e:
            raise DataCollectorError(
                f"データベースからの読み込みに失敗しました: {e}"
            ) from e
        finally:
            self._close_connection(conn)

        if df.empty:
            logger.info(
                "DBにデータがありません: instrument=%s, granularity=%s",
                instrument,
                granularity,
            )
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        # timeカラムをdatetimeインデックスに変換
        df["time"] = pd.to_datetime(df["time"])
        df.set_index("time", inplace=True)

        return df
