"""
FX自動取引システム — MetaTrader 5 ブローカークライアント

外為ファイネスト MT5 Python API を使用したBrokerClient実装。
シンボル変換（USD_JPY ↔ USDJPY-）、リトライロジック、
フィリングモード自動検出を含む。
"""

import logging
import math
import time
from typing import Optional

import MetaTrader5 as mt5
import pandas as pd

logger = logging.getLogger(__name__)

from src.broker_client import BrokerClient


# ================================================================
# 例外クラス
# ================================================================


class Mt5ClientError(Exception):
    """MT5クライアント固有のエラー"""
    pass


# ================================================================
# ヘルパー関数
# ================================================================

# ロットサイズ定数（1ロット = 100,000通貨単位）
LOT_SIZE = 100_000

# リトライ設定
MAX_RETRIES = 3  # リトライ回数（初回を含めず）
RETRY_DELAY = 1.0  # リトライ間隔（秒）

# リトライ可能なエラーコード
RETRYABLE_RETCODES = {
    10004,  # TRADE_RETCODE_REQUOTE
    10012,  # TRADE_RETCODE_TIMEOUT
    10014,  # TRADE_RETCODE_CONNECTION
}

# タイムフレーム変換マップ
_TIMEFRAME_MAP = {
    "M1": "TIMEFRAME_M1",
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D": "TIMEFRAME_D1",
    "D1": "TIMEFRAME_D1",
    "W": "TIMEFRAME_W1",
    "W1": "TIMEFRAME_W1",
    "MN1": "TIMEFRAME_MN1",
}


def to_mt5_symbol(instrument: str) -> str:
    """BrokerClient形式のシンボルをMT5形式に変換する。

    例: "USD_JPY" → "USDJPY-"
    """
    return instrument.replace("_", "") + "-"


def from_mt5_symbol(mt5_symbol: str) -> str:
    """MT5形式のシンボルをBrokerClient形式に変換する。

    例: "USDJPY-" → "USD_JPY"
    """
    # 末尾の "-" を除去
    base = mt5_symbol.rstrip("-")
    # 6文字の通貨ペアを3+3に分割してアンダースコアで結合
    return base[:3] + "_" + base[3:]


def to_mt5_timeframe(granularity: str) -> int:
    """文字列のタイムフレームをMT5定数に変換する。

    Args:
        granularity: タイムフレーム文字列（例: "H4", "D", "M15"）

    Returns:
        MT5タイムフレーム定数

    Raises:
        ValueError: 未対応のタイムフレームの場合
    """
    attr_name = _TIMEFRAME_MAP.get(granularity)
    if attr_name is None:
        raise ValueError(f"未対応のタイムフレーム: {granularity}")
    return getattr(mt5, attr_name)


# ================================================================
# Mt5Client
# ================================================================


class Mt5Client(BrokerClient):
    """MetaTrader 5 ブローカークライアント。

    外為ファイネストのMT5デモ/本番口座に接続し、
    BrokerClientインターフェースを実装する。
    """

    def __init__(self):
        """MT5ターミナルに接続して初期化する。

        Raises:
            Mt5ClientError: MT5ターミナルへの接続に失敗した場合
        """
        if not mt5.initialize():
            error = mt5.last_error()
            raise Mt5ClientError(
                f"MT5ターミナルへの接続に失敗しました: {error}"
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        mt5.shutdown()
        return False

    # ================================================================
    # 価格データ取得
    # ================================================================

    def get_prices(
        self,
        instrument: str,
        count: int,
        granularity: str,
    ) -> pd.DataFrame:
        """価格データを取得する（リトライロジック付き）。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            count: 取得するローソク足の本数
            granularity: 時間足（例: "H4", "D", "M15"）

        Returns:
            OHLCV形式のDataFrame

        Raises:
            Mt5ClientError: 最大リトライ超過で取得失敗した場合
        """
        symbol = to_mt5_symbol(instrument)
        timeframe = to_mt5_timeframe(granularity)

        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is not None:
                break
            last_error = mt5.last_error()
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        else:
            raise Mt5ClientError(
                f"最大リトライ回数を超えました: {last_error}"
            )

        # numpy structured array → DataFrame
        df = pd.DataFrame(rates)
        if len(df) == 0:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        # tick_volume を volume にリネームし、必要なカラムのみ返す
        df = df.rename(columns={"tick_volume": "volume"})
        return df[["open", "high", "low", "close", "volume"]]

    # ================================================================
    # 注文発注
    # ================================================================

    def market_order(
        self,
        instrument: str,
        units: int,
        stop_loss: float,
        take_profit: float,
    ) -> dict:
        """成行注文を発注する。

        外為ファイネストではSL/TPを注文に含めると10013になるケースがあるため、
        約定後にTRADE_ACTION_SLTPで後から設定する2ステップ方式を採用。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            units: 取引数量（正=買い、負=売り）
            stop_loss: 損切り価格
            take_profit: 利確価格

        Returns:
            注文結果のdict

        Raises:
            Mt5ClientError: ティック取得失敗または注文エラーの場合
        """
        symbol = to_mt5_symbol(instrument)
        is_buy = units > 0
        volume = abs(units) / LOT_SIZE

        # ティック情報を取得
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise Mt5ClientError(f"ティック情報を取得できません: {symbol}")

        # volume をシンボルの volume_step に整列させる（retcode 10014 回避）
        volume = self._adjust_volume(symbol, volume)

        price = tick.ask if is_buy else tick.bid
        order_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL

        # Step 1: SL/TPなしで約定（外為ファイネスト互換）
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        # フィリングモード自動検出
        request = self._find_valid_filling(request)

        # リトライ付き注文送信
        result = self._send_order_with_retry(request)

        # Step 2: SL/TPを後から設定
        if stop_loss or take_profit:
            sltp_request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": result.order,
                "sl": stop_loss,
                "tp": take_profit,
            }
            sltp_result = mt5.order_send(sltp_request)
            if sltp_result.retcode != mt5.TRADE_RETCODE_DONE:
                # SL/TP設定失敗はログに残すが約定自体は成功しているので例外にしない
                logger.warning(
                    "SL/TP設定失敗（約定済み）: retcode=%d, comment=%s",
                    sltp_result.retcode, sltp_result.comment,
                )

        return {
            "status": "filled",
            "order_id": str(result.order),
            "units": units,
            "price": result.price,
            "comment": result.comment,
        }

    def limit_order(
        self,
        instrument: str,
        units: int,
        price: float,
        stop_loss: float,
        take_profit: float,
    ) -> dict:
        """指値注文を発注する。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            units: 取引数量（正=買い、負=売り）
            price: 指値価格
            stop_loss: 損切り価格
            take_profit: 利確価格

        Returns:
            注文結果のdict

        Raises:
            Mt5ClientError: 注文エラーの場合
        """
        symbol = to_mt5_symbol(instrument)
        is_buy = units > 0
        volume = abs(units) / LOT_SIZE

        # volume をシンボルの volume_step に整列させる（retcode 10014 回避）
        volume = self._adjust_volume(symbol, volume)

        order_type = mt5.ORDER_TYPE_BUY_LIMIT if is_buy else mt5.ORDER_TYPE_SELL_LIMIT

        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": stop_loss,
            "tp": take_profit,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        # フィリングモード自動検出
        request = self._find_valid_filling(request)

        # 注文送信（指値はリトライ不要）
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise Mt5ClientError(
                f"MT5注文エラー: retcode={result.retcode}, comment={result.comment}"
            )

        return {
            "status": "pending",
            "order_id": str(result.order),
            "units": units,
            "price": price,
            "comment": result.comment,
        }

    # ================================================================
    # ポジション管理
    # ================================================================

    def get_positions(self) -> list[dict]:
        """保有ポジション一覧を取得する。

        Returns:
            ポジション情報のリスト

        Raises:
            Mt5ClientError: ポジション情報取得に失敗した場合
        """
        positions = mt5.positions_get()
        if positions is None:
            error = mt5.last_error()
            raise Mt5ClientError(
                f"ポジション情報を取得できませんでした: {error}"
            )

        result = []
        for pos in positions:
            # 売りポジション（type=1）はunitsを負にする
            units = int(pos.volume * LOT_SIZE)
            if pos.type == 1:  # SELL
                units = -units

            result.append({
                "trade_id": str(pos.ticket),
                "instrument": from_mt5_symbol(pos.symbol),
                "units": units,
                "unrealized_pl": pos.profit,
                "price_open": pos.price_open,
            })

        return result

    def close_position(self, trade_id: str) -> dict:
        """指定したポジションを決済する。

        買いポジション → SELL注文、売りポジション → BUY注文で閉じる。

        Args:
            trade_id: 決済対象のトレードID

        Returns:
            決済結果のdict

        Raises:
            Mt5ClientError: ポジションが見つからない、またはエラーの場合
        """
        ticket = int(trade_id)

        # 対象ポジションを検索
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            raise Mt5ClientError(
                f"ポジションが見つかりません: trade_id={trade_id}"
            )

        pos = positions[0]
        symbol = pos.symbol

        # ティック情報を取得
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise Mt5ClientError(f"ティック情報を取得できません: {symbol}")

        # 買いポジション → SELL、売りポジション → BUY
        if pos.type == 0:  # BUY
            close_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:  # SELL
            close_type = mt5.ORDER_TYPE_BUY
            price = tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": close_type,
            "price": price,
            "position": ticket,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        # フィリングモード自動検出
        request = self._find_valid_filling(request)

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise Mt5ClientError(
                f"MT5決済エラー: retcode={result.retcode}, comment={result.comment}"
            )

        return {
            "trade_id": trade_id,
            "realized_pl": pos.profit,
            "close_price": result.price,
            "comment": result.comment,
        }

    def get_closed_deal(self, trade_id: str) -> Optional[dict]:
        """既に決済済みのポジションの決済情報をMT5の取引履歴から取得する。

        SL/TP発動による自動決済はclose_position()を経由しないため、
        reconcile処理で事後的に close_price/realized_pl を復元するために使用する。

        Args:
            trade_id: ポジションID（ticket番号）

        Returns:
            決済情報のdict（close_price, realized_pl, closed_at）。
            取得失敗時は None。
        """
        from datetime import datetime, timedelta, timezone

        try:
            ticket = int(trade_id)
        except (TypeError, ValueError):
            logger.warning("不正なtrade_id: %s", trade_id)
            return None

        # MT5の history_deals_get は時間範囲を要求する。
        # ポジションは数日以内に決済される想定で、過去14日を範囲にする。
        date_to = datetime.now(timezone.utc) + timedelta(days=1)
        date_from = date_to - timedelta(days=14)

        deals = mt5.history_deals_get(date_from, date_to, position=ticket)
        if deals is None or len(deals) == 0:
            error = mt5.last_error()
            logger.warning(
                "決済履歴を取得できませんでした: ticket=%s, mt5_error=%s",
                ticket, error,
            )
            return None

        # entry == DEAL_ENTRY_OUT (1) または DEAL_ENTRY_INOUT (2) が決済側
        close_deals = [
            d for d in deals
            if d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_INOUT)
        ]
        if not close_deals:
            logger.warning(
                "決済方向のdealが見つかりません: ticket=%s, deals=%d",
                ticket, len(deals),
            )
            return None

        # 複数の部分決済がある場合は合算（profitとswap/commissionを含めて実損益）
        realized_pl = sum(
            d.profit + getattr(d, "swap", 0.0) + getattr(d, "commission", 0.0)
            for d in close_deals
        )
        # 決済価格は最後の決済dealの価格（部分決済の最終約定）
        last_close = max(close_deals, key=lambda d: d.time)
        closed_at = datetime.fromtimestamp(last_close.time, tz=timezone.utc)

        return {
            "trade_id": trade_id,
            "close_price": float(last_close.price),
            "realized_pl": float(realized_pl),
            "closed_at": closed_at,
        }

    # ================================================================
    # 口座情報
    # ================================================================

    def get_account_summary(self) -> dict:
        """口座残高・証拠金情報を取得する。

        Returns:
            口座情報のdict

        Raises:
            Mt5ClientError: 口座情報取得に失敗した場合
        """
        account = mt5.account_info()
        if account is None:
            error = mt5.last_error()
            raise Mt5ClientError(
                f"口座情報を取得できませんでした: {error}"
            )

        positions = mt5.positions_get()
        open_count = len(positions) if positions else 0

        return {
            "balance": account.balance,
            "unrealized_pl": account.profit,
            "margin_used": account.margin,
            "margin_available": account.margin_free,
            "open_trade_count": open_count,
            "currency": account.currency,
        }

    # ================================================================
    # 内部ヘルパー
    # ================================================================

    def _adjust_volume(self, symbol: str, volume: float) -> float:
        """volumeをシンボルのvolume_stepに整列させ、min/maxにクランプする。

        MT5は volume が volume_step の倍数でないと retcode 10014
        (TRADE_RETCODE_INVALID_VOLUME) で注文を拒否する。
        さらに _find_valid_filling がその失敗を「Unsupported filling mode」
        として上書きしてしまうため、真因が見えなくなる（2026-04で発覚）。

        Args:
            symbol: MT5形式のシンボル（例: "USDJPY-"）
            volume: 希望するロット数（整列前）

        Returns:
            volume_stepに整列し、min/maxにクランプしたロット数

        Raises:
            Mt5ClientError: 丸めた結果が volume_min を下回り取引不可の場合
        """
        info = mt5.symbol_info(symbol)
        if info is None:
            return volume

        step = getattr(info, "volume_step", None)
        vmin = getattr(info, "volume_min", None)
        vmax = getattr(info, "volume_max", None)

        # MagicMock等の非数値属性では丸めをスキップ（既存テスト互換）
        if not isinstance(step, (int, float)) or step <= 0:
            return volume

        # 下方向に丸め（過剰ロットを避ける）
        adjusted = math.floor(volume / step) * step
        # 浮動小数の残差を抑えるため step の桁で丸め直す
        decimals = max(0, -int(math.floor(math.log10(step)))) if step < 1 else 0
        adjusted = round(adjusted, decimals)

        if isinstance(vmax, (int, float)) and vmax > 0 and adjusted > vmax:
            adjusted = vmax
        if isinstance(vmin, (int, float)) and vmin > 0 and adjusted < vmin:
            raise Mt5ClientError(
                f"ロット数が最小単位を下回ります: symbol={symbol}, "
                f"要求={volume}, 丸め後={adjusted}, volume_min={vmin}"
            )

        return adjusted

    def _find_valid_filling(self, request: dict) -> dict:
        """有効なフィリングモードを自動検出する。

        symbol_info().filling_modeのビットマスクから対応モードを判定し、
        フォールバックとしてorder_checkも試行する。

        Args:
            request: 注文リクエストdict

        Returns:
            フィリングモードが設定されたリクエストdict

        Raises:
            Mt5ClientError: 全フィリングタイプで失敗した場合
        """
        symbol = request.get("symbol", "")
        info = mt5.symbol_info(symbol)

        attempts: list[str] = []

        # symbol_info.filling_mode はビットマスク
        # SYMBOL_FILLING_FOK=1, SYMBOL_FILLING_IOC=2 に対応
        if info is not None:
            filling_mode = info.filling_mode
            # ビットマスクから対応フィリングを優先順に試行
            candidates = []
            if filling_mode & 1:  # SYMBOL_FILLING_FOK
                candidates.append(mt5.ORDER_FILLING_FOK)
            if filling_mode & 2:  # SYMBOL_FILLING_IOC
                candidates.append(mt5.ORDER_FILLING_IOC)
            # RETURN（ビット0x0、つまりExchange実行モード）は常にフォールバック候補
            candidates.append(mt5.ORDER_FILLING_RETURN)

            for filling in candidates:
                request["type_filling"] = filling
                check_result = mt5.order_check(request)
                if check_result is not None and check_result.retcode == 0:
                    return request
                if check_result is not None:
                    attempts.append(
                        f"filling={filling} retcode={check_result.retcode} "
                        f"comment={check_result.comment}"
                    )

        # symbol_infoが取れない場合、またはビットマスクで網羅できなかった場合の全パターン試行
        filling_types = [
            mt5.ORDER_FILLING_FOK,
            mt5.ORDER_FILLING_IOC,
            mt5.ORDER_FILLING_RETURN,
        ]

        for filling in filling_types:
            request["type_filling"] = filling
            check_result = mt5.order_check(request)
            if check_result is not None and check_result.retcode == 0:
                return request
            if check_result is not None:
                attempts.append(
                    f"filling={filling} retcode={check_result.retcode} "
                    f"comment={check_result.comment}"
                )

        # 最後の試行のcommentだけでなく各試行の詳細を残すことで真因を特定可能にする
        detail = "; ".join(attempts) if attempts else "order_check=None"
        raise Mt5ClientError(
            f"全フィリングタイプで失敗しました: {detail}"
        )

    def _send_order_with_retry(self, request: dict) -> object:
        """リトライ付きで注文を送信する。

        REQUOTE・TIMEOUT・CONNECTION エラー時にリトライする。

        Args:
            request: 注文リクエストdict

        Returns:
            MT5の注文結果オブジェクト

        Raises:
            Mt5ClientError: リトライ不可能なエラー、または最大リトライ超過の場合
        """
        for attempt in range(MAX_RETRIES + 1):
            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return result

            # リトライ可能なエラーかチェック
            if result.retcode not in RETRYABLE_RETCODES:
                raise Mt5ClientError(
                    f"MT5注文エラー: retcode={result.retcode}, "
                    f"comment={result.comment}"
                )

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

        raise Mt5ClientError(
            f"最大リトライ回数を超えました: retcode={result.retcode}, "
            f"comment={result.comment}"
        )
