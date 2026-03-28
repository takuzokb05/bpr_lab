"""
FX自動取引システム — OANDA REST API v20 実装

BrokerClientインターフェースのOANDA実装。
doc 04 セクション3.1 準拠。
"""

import logging
import time
from datetime import datetime, timezone

import pandas as pd
from oandapyV20 import API
from oandapyV20.exceptions import V20Error
from oandapyV20.endpoints.instruments import InstrumentsCandles
from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.endpoints.trades import TradeClose, TradesList
from oandapyV20.endpoints.accounts import AccountSummary
from oandapyV20.contrib.requests import MarketOrderRequest, LimitOrderRequest

from src.broker_client import BrokerClient
from src.config import (
    OANDA_API_KEY,
    OANDA_ACCOUNT_ID,
    OANDA_ENVIRONMENT,
    API_TIMEOUT,
    API_MAX_RETRIES,
)

logger = logging.getLogger(__name__)


class OandaClientError(Exception):
    """OANDA API固有のエラー"""


class OandaClient(BrokerClient):
    """
    OANDA REST API v20 の BrokerClient 実装。

    全API呼び出しにタイムアウトとリトライを適用する。
    """

    def __init__(
        self,
        api_key: str | None = None,
        account_id: str | None = None,
        environment: str | None = None,
    ) -> None:
        """
        OANDAクライアントを初期化する。

        Args:
            api_key: OANDAのAPIキー。省略時はconfig.pyの値を使用。
            account_id: OANDA口座ID。省略時はconfig.pyの値を使用。
            environment: "practice" or "live"。省略時はconfig.pyの値を使用。
        """
        self._api_key = api_key or OANDA_API_KEY
        self._account_id = account_id or OANDA_ACCOUNT_ID
        self._environment = environment or OANDA_ENVIRONMENT

        if not self._api_key:
            raise OandaClientError(
                "OANDAのAPIキーが設定されていません。.envファイルを確認してください。"
            )
        if not self._account_id:
            raise OandaClientError(
                "OANDAの口座IDが設定されていません。.envファイルを確認してください。"
            )

        self._api = API(
            access_token=self._api_key,
            environment=self._environment,
            request_params={"timeout": API_TIMEOUT},
        )
        logger.info(
            "OANDAクライアントを初期化しました（環境: %s、口座: %s）",
            self._environment,
            self._account_id[:8] + "...",
        )

    def _request_with_retry(self, endpoint) -> dict:
        """
        指数バックオフ付きリトライでAPIリクエストを実行する。

        CLAUDE.md リトライ・タイムアウト規約準拠:
        - 5xx/Timeout: 指数バックオフでリトライ（最大3回）
        - 429: Retry-Afterヘッダに従う

        Args:
            endpoint: oandapyV20のエンドポイントオブジェクト

        Returns:
            APIレスポンスのdict

        Raises:
            OandaClientError: 最大リトライ回数超過後もエラーが解消しない場合
        """
        last_error = None

        for attempt in range(API_MAX_RETRIES + 1):
            try:
                response = self._api.request(endpoint)
                return response

            except V20Error as e:
                last_error = e
                status_code = getattr(e, "code", None)

                # 429: レート制限 → Retry-Afterに従う
                if status_code == 429:
                    retry_after = 1
                    logger.warning(
                        "レート制限に到達しました。%d秒後にリトライします（試行 %d/%d）",
                        retry_after,
                        attempt + 1,
                        API_MAX_RETRIES + 1,
                    )
                    time.sleep(retry_after)
                    continue

                # 5xx: サーバーエラー → 指数バックオフ
                if status_code and 500 <= status_code < 600:
                    if attempt < API_MAX_RETRIES:
                        wait = 2 ** attempt
                        logger.warning(
                            "サーバーエラー(%d)。%d秒後にリトライします（試行 %d/%d）",
                            status_code,
                            wait,
                            attempt + 1,
                            API_MAX_RETRIES + 1,
                        )
                        time.sleep(wait)
                        continue

                # 4xx（429以外）: クライアントエラー → リトライしない
                logger.error("OANDA APIエラー: %s", e)
                raise OandaClientError(f"OANDA APIエラー: {e}") from e

            except (ConnectionError, TimeoutError, OSError) as e:
                last_error = e
                if attempt < API_MAX_RETRIES:
                    wait = 2 ** attempt
                    logger.warning(
                        "接続エラー。%d秒後にリトライします（試行 %d/%d）: %s",
                        wait,
                        attempt + 1,
                        API_MAX_RETRIES + 1,
                        e,
                    )
                    time.sleep(wait)
                    continue

        raise OandaClientError(
            f"最大リトライ回数({API_MAX_RETRIES})を超過しました。最後のエラー: {last_error}"
        )

    def get_prices(
        self,
        instrument: str,
        count: int,
        granularity: str,
    ) -> pd.DataFrame:
        """
        OHLCV価格データを取得する。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            count: 取得するローソク足の本数（最大5000）
            granularity: 時間足（例: "H4", "D", "M15"）

        Returns:
            OHLCV形式のDataFrame。カラム: open, high, low, close, volume
            インデックス: datetime（UTC）
        """
        params = {
            "count": count,
            "granularity": granularity,
            "price": "M",  # mid価格を使用
        }
        endpoint = InstrumentsCandles(instrument=instrument, params=params)
        response = self._request_with_retry(endpoint)

        candles = response.get("candles", [])
        if not candles:
            logger.warning(
                "価格データが空です: instrument=%s, granularity=%s",
                instrument,
                granularity,
            )
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        rows = []
        for candle in candles:
            if not candle.get("complete", False):
                continue  # 未完成のローソク足はスキップ
            mid = candle["mid"]
            rows.append({
                "time": pd.to_datetime(candle["time"]),
                "open": float(mid["o"]),
                "high": float(mid["h"]),
                "low": float(mid["l"]),
                "close": float(mid["c"]),
                "volume": int(candle["volume"]),
            })

        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame(rows)
        df.set_index("time", inplace=True)
        df.index = df.index.tz_localize(None)  # タイムゾーン情報を除去（UTC前提）
        return df

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
            stop_loss: 損切り価格
            take_profit: 利確価格

        Returns:
            {"order_id": str, "price": float, "units": int} を含むdict
        """
        order_data = MarketOrderRequest(
            instrument=instrument,
            units=units,
            stopLossOnFill={"price": str(stop_loss)},
            takeProfitOnFill={"price": str(take_profit)},
        )
        endpoint = OrderCreate(
            accountID=self._account_id,
            data=order_data.data,
        )
        response = self._request_with_retry(endpoint)

        # 約定結果を抽出
        fill = response.get("orderFillTransaction", {})
        if not fill:
            # 注文は作成されたが即時約定しなかった場合
            create = response.get("orderCreateTransaction", {})
            logger.warning("成行注文が即時約定しませんでした: %s", create)
            return {
                "order_id": create.get("id", ""),
                "price": 0.0,
                "units": units,
                "status": "pending",
            }

        trade_opened = fill.get("tradeOpened", {})
        return {
            "order_id": fill.get("id", ""),
            "trade_id": trade_opened.get("tradeID", ""),
            "price": float(fill.get("price", 0)),
            "units": int(fill.get("units", 0)),
            "status": "filled",
        }

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
            stop_loss: 損切り価格
            take_profit: 利確価格

        Returns:
            {"order_id": str, "status": str} を含むdict
        """
        order_data = LimitOrderRequest(
            instrument=instrument,
            units=units,
            price=str(price),
            stopLossOnFill={"price": str(stop_loss)},
            takeProfitOnFill={"price": str(take_profit)},
        )
        endpoint = OrderCreate(
            accountID=self._account_id,
            data=order_data.data,
        )
        response = self._request_with_retry(endpoint)

        create = response.get("orderCreateTransaction", {})
        return {
            "order_id": create.get("id", ""),
            "price": price,
            "units": units,
            "status": "pending",
        }

    def get_positions(self) -> list[dict]:
        """
        保有ポジション一覧を取得する（オープントレードベース）。

        Returns:
            ポジション情報のリスト。各dictは以下を含む:
            - "trade_id": str
            - "instrument": str
            - "units": int
            - "unrealized_pl": float
        """
        endpoint = TradesList(
            accountID=self._account_id,
            params={"state": "OPEN"},
        )
        response = self._request_with_retry(endpoint)

        positions = []
        for trade in response.get("trades", []):
            positions.append({
                "trade_id": trade["id"],
                "instrument": trade["instrument"],
                "units": int(trade["currentUnits"]),
                "unrealized_pl": float(trade.get("unrealizedPL", 0)),
                "open_price": float(trade.get("price", 0)),
            })

        return positions

    def close_position(self, trade_id: str) -> dict:
        """
        指定したポジションを決済する。

        Args:
            trade_id: 決済対象のトレードID

        Returns:
            {"trade_id": str, "realized_pl": float} を含むdict
        """
        endpoint = TradeClose(
            accountID=self._account_id,
            tradeID=trade_id,
            data={"units": "ALL"},
        )
        response = self._request_with_retry(endpoint)

        fill = response.get("orderFillTransaction", {})
        return {
            "trade_id": trade_id,
            "realized_pl": float(fill.get("pl", 0)),
            "close_price": float(fill.get("price", 0)),
        }

    def get_account_summary(self) -> dict:
        """
        口座残高・証拠金情報を取得する。

        Returns:
            口座情報のdict:
            - "balance": float
            - "unrealized_pl": float
            - "margin_used": float
            - "margin_available": float
        """
        endpoint = AccountSummary(accountID=self._account_id)
        response = self._request_with_retry(endpoint)

        account = response.get("account", {})
        return {
            "balance": float(account.get("balance", 0)),
            "unrealized_pl": float(account.get("unrealizedPL", 0)),
            "margin_used": float(account.get("marginUsed", 0)),
            "margin_available": float(account.get("marginAvailable", 0)),
            "open_trade_count": int(account.get("openTradeCount", 0)),
            "currency": account.get("currency", "JPY"),
        }
