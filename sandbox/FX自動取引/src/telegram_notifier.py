"""
FX自動取引システム — Telegram通知・コマンド受信モジュール

Telegram Bot APIを直接使用し、以下の機能を提供する:
- 取引イベントの通知（シグナル、ポジション開閉、キルスイッチ等）
- スマホからのコマンド受信（/status, /positions, /balance 等）

スレッド構成:
- 送信スレッド: Queueからメッセージを取り出してTelegram APIに送信
- ポーリングスレッド: getUpdatesでコマンドを受信しディスパッチ
"""

import logging
import queue
import threading
import time
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)

# Telegram Bot API ベースURL
_API_BASE = "https://api.telegram.org/bot{token}/{method}"

# 送信キューの上限（溢れた場合は古いメッセージを捨てる）
_MAX_QUEUE_SIZE = 100


class TelegramNotifier:
    """
    Telegram Bot API を使用した通知送信・コマンド受信ハンドラ。

    送信はバックグラウンドスレッドでQueue経由（メインループをブロックしない）。
    コマンド受信はロングポーリングで別スレッドが処理する。
    """

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        send_timeout: int = 10,
        poll_timeout: int = 30,
    ) -> None:
        """
        Args:
            bot_token: Telegram Bot API トークン
            chat_id: 通知先のチャットID
            send_timeout: sendMessage APIのタイムアウト（秒）
            poll_timeout: getUpdatesのロングポーリングタイムアウト（秒）
        """
        if not bot_token or not chat_id:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN と TELEGRAM_CHAT_ID の両方が必要です"
            )

        self._token = bot_token
        self._chat_id = str(chat_id)
        self._send_timeout = send_timeout
        self._poll_timeout = poll_timeout

        # 送信キュー
        self._send_queue: queue.Queue[Optional[str]] = queue.Queue(
            maxsize=_MAX_QUEUE_SIZE
        )

        # コマンドハンドラ登録 {コマンド名: ハンドラ関数}
        self._command_handlers: dict[str, Callable[[str], str]] = {}

        # コマンドハンドラ用キャッシュ（メインスレッドから更新、ポーラーから読取）
        self._cache_lock = threading.Lock()
        self._cached_account: Optional[dict] = None
        self._cached_positions: list[dict] = []
        self._cached_status: dict = {}

        # スレッド制御
        self._stop_event = threading.Event()
        self._sender_thread: Optional[threading.Thread] = None
        self._poller_thread: Optional[threading.Thread] = None
        self._started = False

        # ポーリング用: 最後に処理したupdate_id
        self._last_update_id: int = 0

    # ------------------------------------------------------------------
    # ライフサイクル
    # ------------------------------------------------------------------

    def start(self) -> None:
        """送信スレッドとポーリングスレッドを開始する。"""
        if self._started:
            logger.warning("TelegramNotifier は既に起動しています")
            return

        self._stop_event.clear()

        self._sender_thread = threading.Thread(
            target=self._sender_loop, name="telegram-sender", daemon=True
        )
        self._poller_thread = threading.Thread(
            target=self._poller_loop, name="telegram-poller", daemon=True
        )

        self._sender_thread.start()
        self._poller_thread.start()
        self._started = True
        logger.info("Telegram通知スレッドを開始しました")

    def stop(self) -> None:
        """両スレッドにシャットダウンを指示し、完了を待機する。"""
        if not self._started:
            return

        self._stop_event.set()

        # 送信スレッドのブロッキングを解除するためsentinel値を送る
        try:
            self._send_queue.put_nowait(None)
        except queue.Full:
            pass

        if self._sender_thread and self._sender_thread.is_alive():
            self._sender_thread.join(timeout=5)
        if self._poller_thread and self._poller_thread.is_alive():
            # ポーリングはpoll_timeout秒でタイムアウトするので待つ
            self._poller_thread.join(timeout=self._poll_timeout + 5)

        self._started = False
        logger.info("Telegram通知スレッドを停止しました")

    @property
    def is_running(self) -> bool:
        """通知システムが稼働中かどうか。"""
        return self._started and not self._stop_event.is_set()

    @property
    def pending_count(self) -> int:
        """送信キュー内の未送信メッセージ数。"""
        return self._send_queue.qsize()

    # ------------------------------------------------------------------
    # キャッシュ管理（メインスレッドから呼ぶ）
    # ------------------------------------------------------------------

    def update_cache(
        self,
        account: Optional[dict] = None,
        positions: Optional[list[dict]] = None,
        status: Optional[dict] = None,
    ) -> None:
        """メインスレッドからキャッシュを更新する。"""
        with self._cache_lock:
            if account is not None:
                self._cached_account = account
            if positions is not None:
                self._cached_positions = list(positions)
            if status is not None:
                self._cached_status = dict(status)

    def get_cached_account(self) -> Optional[dict]:
        """キャッシュされた口座情報を返す。"""
        with self._cache_lock:
            return self._cached_account

    def get_cached_positions(self) -> list[dict]:
        """キャッシュされたポジション一覧を返す。"""
        with self._cache_lock:
            return list(self._cached_positions)

    def get_cached_status(self) -> dict:
        """キャッシュされたボット状態を返す。"""
        with self._cache_lock:
            return dict(self._cached_status)

    # ------------------------------------------------------------------
    # 通知送信（メインスレッドから呼ぶ — 非ブロッキング）
    # ------------------------------------------------------------------

    def notify(self, message: str, parse_mode: str = "HTML") -> None:
        """メッセージを送信キューに追加する（非ブロッキング）。"""
        item = f"{parse_mode}:{message}"
        try:
            self._send_queue.put_nowait(item)
        except queue.Full:
            logger.warning("Telegram送信キューが満杯。メッセージを破棄: %s", message[:50])

    def notify_signal(self, instrument: str, signal: str) -> None:
        """シグナル検出の通知。"""
        emoji = "📈" if signal == "BUY" else "📉"
        self.notify(
            f"{emoji} <b>シグナル検出</b>\n"
            f"通貨ペア: {instrument}\n"
            f"方向: {signal}"
        )

    def notify_position_opened(
        self, instrument: str, units: int, price: float,
        sl: float, tp: float,
    ) -> None:
        """ポジションオープンの通知。"""
        direction = "BUY" if units > 0 else "SELL"
        self.notify(
            f"✅ <b>ポジションオープン</b>\n"
            f"通貨ペア: {instrument}\n"
            f"方向: {direction} | 数量: {abs(units):,}\n"
            f"価格: {price:.5f}\n"
            f"SL: {sl:.5f} | TP: {tp:.5f}"
        )

    def notify_position_closed(
        self, instrument: str, units: int, pl: float,
    ) -> None:
        """ポジション決済の通知。"""
        icon = "💰" if pl >= 0 else "💸"
        self.notify(
            f"{icon} <b>ポジション決済</b>\n"
            f"通貨ペア: {instrument}\n"
            f"数量: {abs(units):,}\n"
            f"損益: {pl:+,.0f}円"
        )

    def notify_kill_switch(self, reason: str, is_active: bool) -> None:
        """キルスイッチ発動/解除の通知。"""
        if is_active:
            self.notify(
                f"🚨 <b>キルスイッチ発動</b>\n"
                f"理由: {reason}\n"
                f"新規取引を停止しました"
            )
        else:
            self.notify(
                f"✅ <b>キルスイッチ解除</b>\n"
                f"取引を再開します"
            )

    def notify_error(self, error_msg: str, consecutive_count: int) -> None:
        """連続エラーの通知。"""
        self.notify(
            f"⚠️ <b>エラー検出</b>\n"
            f"連続エラー: {consecutive_count}回\n"
            f"内容: {error_msg}"
        )

    def notify_bot_status(self, status: str, detail: str = "") -> None:
        """ボット起動/停止の通知。"""
        detail_line = f"\n{detail}" if detail else ""
        self.notify(f"🤖 <b>ボット{status}</b>{detail_line}")

    # ------------------------------------------------------------------
    # コマンドハンドラ登録
    # ------------------------------------------------------------------

    def register_command_handler(
        self, command: str, handler: Callable[[str], str],
    ) -> None:
        """コマンドとハンドラのマッピングを登録する。"""
        self._command_handlers[command] = handler

    # ------------------------------------------------------------------
    # 内部: Telegram Bot API 呼び出し
    # ------------------------------------------------------------------

    def _send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Telegram Bot APIのsendMessageを呼び出す。成功でTrue。"""
        url = _API_BASE.format(token=self._token, method="sendMessage")
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        try:
            resp = requests.post(url, json=payload, timeout=self._send_timeout)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return True
                logger.warning(
                    "Telegram APIエラー: %s", data.get("description", "不明")
                )
                return False
            logger.warning(
                "Telegram送信失敗 (HTTP %d): %s",
                resp.status_code,
                resp.text[:200],
            )
            return False
        except requests.exceptions.Timeout:
            logger.warning("Telegram送信タイムアウト (%ds)", self._send_timeout)
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("Telegram接続エラー（ネットワーク不通の可能性）")
            return False
        except Exception as e:
            logger.warning("Telegram送信中に予期しないエラー: %s", e)
            return False

    def _get_updates(self) -> list[dict]:
        """Telegram Bot APIのgetUpdatesを呼び出す。"""
        url = _API_BASE.format(token=self._token, method="getUpdates")
        params = {
            "timeout": self._poll_timeout,
            "allowed_updates": '["message"]',
        }
        if self._last_update_id > 0:
            params["offset"] = self._last_update_id + 1

        try:
            resp = requests.get(
                url, params=params,
                timeout=self._poll_timeout + 10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return data.get("result", [])
            return []
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return []
        except Exception as e:
            logger.warning("Telegram getUpdates エラー: %s", e)
            return []

    # ------------------------------------------------------------------
    # 内部: スレッドメインループ
    # ------------------------------------------------------------------

    def _sender_loop(self) -> None:
        """送信スレッドのメインループ。"""
        while not self._stop_event.is_set():
            try:
                item = self._send_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            # sentinel値（None）で終了
            if item is None:
                break

            # "parse_mode:message" 形式をパース
            if ":" in item:
                parse_mode, message = item.split(":", 1)
            else:
                parse_mode, message = "HTML", item

            self._send_message(message, parse_mode)

            # レート制限対策（Telegram: 毎秒30メッセージまで）
            time.sleep(0.05)

    def _poller_loop(self) -> None:
        """ポーリングスレッドのメインループ。"""
        while not self._stop_event.is_set():
            updates = self._get_updates()

            for update in updates:
                update_id = update.get("update_id", 0)
                if update_id > self._last_update_id:
                    self._last_update_id = update_id

                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = str(message.get("chat", {}).get("id", ""))

                # チャットID検証（セキュリティ）
                if chat_id != self._chat_id:
                    logger.warning(
                        "不正なチャットIDからのメッセージを無視: %s", chat_id
                    )
                    continue

                # コマンドの処理
                if text.startswith("/"):
                    command = text.split()[0].lstrip("/").split("@")[0]
                    self._dispatch_command(command, chat_id)

            # ポーリング間隔（getUpdatesがロングポーリングなので追加スリープは最小限）
            if not updates and not self._stop_event.is_set():
                time.sleep(1)

    def _dispatch_command(self, command: str, chat_id: str) -> None:
        """コマンドに対応するハンドラを呼び出し、結果をキューに入れる。"""
        handler = self._command_handlers.get(command)
        if handler is None:
            self.notify(f"不明なコマンド: /{command}\n/help でコマンド一覧を確認")
            return

        try:
            result = handler(chat_id)
            if result:
                self.notify(result)
        except Exception as e:
            logger.error("コマンド /%s の実行中にエラー: %s", command, e)
            self.notify(f"⚠️ コマンド /{command} の実行に失敗しました")


class TelegramLogHandler(logging.Handler):
    """
    WARNING以上のログを自動的にTelegramに転送するlogging.Handler。

    キルスイッチ・ドローダウン等の既存ログメッセージが
    コード変更なしで自動的に通知される。
    """

    def __init__(
        self, notifier: TelegramNotifier, level: int = logging.WARNING,
    ) -> None:
        super().__init__(level)
        self._notifier = notifier
        # 重複通知防止: 直近のメッセージを記録
        self._recent_messages: list[tuple[float, str]] = []
        self._dedup_window_sec = 60  # 60秒以内の同一メッセージをスキップ

    def emit(self, record: logging.LogRecord) -> None:
        """ログレコードをTelegramに転送する。"""
        # Loggerから直接呼ばれた場合もレベルを尊重する
        if record.levelno < self.level:
            return
        try:
            msg = self.format(record)

            # 重複チェック
            now = time.time()
            # 古いエントリを削除
            self._recent_messages = [
                (t, m) for t, m in self._recent_messages
                if now - t < self._dedup_window_sec
            ]
            # 同一メッセージが直近にあればスキップ
            if any(m == msg for _, m in self._recent_messages):
                return
            self._recent_messages.append((now, msg))

            level_icon = {
                logging.WARNING: "⚠️",
                logging.ERROR: "❌",
                logging.CRITICAL: "🚨",
            }.get(record.levelno, "ℹ️")

            self._notifier.notify(
                f"{level_icon} [{record.levelname}] {msg}"
            )
        except Exception:
            self.handleError(record)
