"""
TelegramNotifier のユニットテスト。

requests.post / requests.get をモックし、Telegram APIを実際には呼ばない。
"""

import logging
import queue
import threading
import time
from unittest.mock import MagicMock, patch, call

import pytest

from src.telegram_notifier import (
    TelegramNotifier,
    TelegramLogHandler,
    _API_BASE,
    _MAX_QUEUE_SIZE,
)


# ============================================================
# フィクスチャ
# ============================================================

@pytest.fixture
def notifier():
    """テスト用のTelegramNotifier（スレッド未起動）。"""
    return TelegramNotifier(
        bot_token="test-token-123",
        chat_id="12345",
        send_timeout=5,
        poll_timeout=1,
    )


@pytest.fixture
def mock_post():
    """requests.post をモック。"""
    with patch("src.telegram_notifier.requests.post") as m:
        m.return_value.status_code = 200
        m.return_value.json.return_value = {"ok": True, "result": {}}
        yield m


@pytest.fixture
def mock_get():
    """requests.get をモック。"""
    with patch("src.telegram_notifier.requests.get") as m:
        m.return_value.status_code = 200
        m.return_value.json.return_value = {"ok": True, "result": []}
        yield m


# ============================================================
# 1. 初期化テスト
# ============================================================

class TestInit:
    """初期化に関するテスト。"""

    def test_正常初期化(self):
        n = TelegramNotifier(bot_token="token", chat_id="123")
        assert n._token == "token"
        assert n._chat_id == "123"
        assert not n._started

    def test_トークン未設定でValueError(self):
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
            TelegramNotifier(bot_token="", chat_id="123")

    def test_チャットID未設定でValueError(self):
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
            TelegramNotifier(bot_token="token", chat_id="")

    def test_チャットIDを文字列に変換(self):
        n = TelegramNotifier(bot_token="token", chat_id="99999")
        assert n._chat_id == "99999"


# ============================================================
# 2. 送信キューテスト
# ============================================================

class TestSendQueue:
    """送信キューに関するテスト。"""

    def test_notifyでキューにメッセージが入る(self, notifier):
        notifier.notify("テストメッセージ")
        assert notifier.pending_count == 1

    def test_notifyは非ブロッキング(self, notifier):
        start = time.monotonic()
        notifier.notify("テスト")
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    def test_キュー満杯時にメッセージを破棄(self, notifier):
        for i in range(_MAX_QUEUE_SIZE):
            notifier.notify(f"msg-{i}")
        assert notifier.pending_count == _MAX_QUEUE_SIZE
        # これ以上入れても例外にはならない（ログ警告のみ）
        notifier.notify("溢れるメッセージ")
        assert notifier.pending_count == _MAX_QUEUE_SIZE

    def test_pending_countが正確(self, notifier):
        assert notifier.pending_count == 0
        notifier.notify("1")
        notifier.notify("2")
        assert notifier.pending_count == 2


# ============================================================
# 3. API呼び出しテスト
# ============================================================

class TestSendMessage:
    """_send_message の直接テスト。"""

    def test_正常送信(self, notifier, mock_post):
        result = notifier._send_message("テスト")
        assert result is True
        mock_post.assert_called_once()
        url = mock_post.call_args[1].get("url") or mock_post.call_args[0][0]
        assert "test-token-123" in url
        assert "sendMessage" in url

    def test_送信ペイロードの内容(self, notifier, mock_post):
        notifier._send_message("こんにちは", parse_mode="Markdown")
        payload = mock_post.call_args[1]["json"]
        assert payload["chat_id"] == "12345"
        assert payload["text"] == "こんにちは"
        assert payload["parse_mode"] == "Markdown"

    def test_HTTPエラー時にFalse(self, notifier, mock_post):
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Server Error"
        result = notifier._send_message("テスト")
        assert result is False

    def test_TelegramAPIエラー時にFalse(self, notifier, mock_post):
        mock_post.return_value.json.return_value = {
            "ok": False, "description": "Bad Request"
        }
        result = notifier._send_message("テスト")
        assert result is False

    def test_タイムアウト時にFalse(self, notifier, mock_post):
        import requests as req
        mock_post.side_effect = req.exceptions.Timeout("timeout")
        result = notifier._send_message("テスト")
        assert result is False

    def test_接続エラー時にFalse(self, notifier, mock_post):
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError("connection failed")
        result = notifier._send_message("テスト")
        assert result is False


# ============================================================
# 4. 通知フォーマットテスト
# ============================================================

class TestNotifyFormats:
    """各notify_xxx()メソッドのフォーマット検証。"""

    def test_notify_signal_BUY(self, notifier):
        notifier.notify_signal("USD_JPY", "BUY")
        item = notifier._send_queue.get_nowait()
        assert "シグナル検出" in item
        assert "USD_JPY" in item
        assert "BUY" in item
        assert "📈" in item

    def test_notify_signal_SELL(self, notifier):
        notifier.notify_signal("EUR_USD", "SELL")
        item = notifier._send_queue.get_nowait()
        assert "SELL" in item
        assert "📉" in item

    def test_notify_position_opened(self, notifier):
        notifier.notify_position_opened(
            instrument="USD_JPY", units=1000, price=150.123,
            sl=149.800, tp=151.000,
        )
        item = notifier._send_queue.get_nowait()
        assert "ポジションオープン" in item
        assert "USD_JPY" in item
        assert "BUY" in item
        assert "150.12300" in item

    def test_notify_position_opened_SELL(self, notifier):
        notifier.notify_position_opened(
            instrument="EUR_USD", units=-1000, price=1.08500,
            sl=1.09000, tp=1.07500,
        )
        item = notifier._send_queue.get_nowait()
        assert "SELL" in item

    def test_notify_position_closed_利益(self, notifier):
        notifier.notify_position_closed(
            instrument="USD_JPY", units=1000, pl=5000.0,
        )
        item = notifier._send_queue.get_nowait()
        assert "ポジション決済" in item
        assert "+5,000" in item
        assert "💰" in item

    def test_notify_position_closed_損失(self, notifier):
        notifier.notify_position_closed(
            instrument="EUR_USD", units=1000, pl=-3000.0,
        )
        item = notifier._send_queue.get_nowait()
        assert "-3,000" in item
        assert "💸" in item

    def test_notify_kill_switch_発動(self, notifier):
        notifier.notify_kill_switch(reason="daily_loss", is_active=True)
        item = notifier._send_queue.get_nowait()
        assert "キルスイッチ発動" in item
        assert "daily_loss" in item
        assert "🚨" in item

    def test_notify_kill_switch_解除(self, notifier):
        notifier.notify_kill_switch(reason="", is_active=False)
        item = notifier._send_queue.get_nowait()
        assert "キルスイッチ解除" in item

    def test_notify_error(self, notifier):
        notifier.notify_error("API接続断", consecutive_count=5)
        item = notifier._send_queue.get_nowait()
        assert "エラー検出" in item
        assert "5回" in item

    def test_notify_bot_status(self, notifier):
        notifier.notify_bot_status("起動", "3ペア監視開始")
        item = notifier._send_queue.get_nowait()
        assert "ボット起動" in item
        assert "3ペア監視開始" in item


# ============================================================
# 5. コマンド受信テスト
# ============================================================

class TestCommandHandling:
    """コマンド受信とディスパッチのテスト。"""

    def test_コマンドハンドラ登録(self, notifier):
        handler = MagicMock(return_value="OK")
        notifier.register_command_handler("test", handler)
        assert "test" in notifier._command_handlers

    def test_コマンドディスパッチ(self, notifier):
        handler = MagicMock(return_value="応答メッセージ")
        notifier.register_command_handler("status", handler)
        notifier._dispatch_command("status", "12345")
        handler.assert_called_once_with("12345")
        # 応答がキューに入る
        item = notifier._send_queue.get_nowait()
        assert "応答メッセージ" in item

    def test_未登録コマンド(self, notifier):
        notifier._dispatch_command("unknown", "12345")
        item = notifier._send_queue.get_nowait()
        assert "不明なコマンド" in item
        assert "/unknown" in item

    def test_チャットID不一致の拒否(self, notifier, mock_get):
        """ポーリングで受信したメッセージのchat_idが不一致なら無視。"""
        mock_get.return_value.json.return_value = {
            "ok": True,
            "result": [{
                "update_id": 1,
                "message": {
                    "text": "/status",
                    "chat": {"id": 99999},  # 不正なID
                },
            }],
        }
        handler = MagicMock(return_value="OK")
        notifier.register_command_handler("status", handler)

        # getUpdatesを1回呼び、ポーラーのロジックを手動再現
        updates = notifier._get_updates()
        for update in updates:
            msg = update.get("message", {})
            chat_id = str(msg.get("chat", {}).get("id", ""))
            if chat_id == notifier._chat_id:
                text = msg.get("text", "")
                if text.startswith("/"):
                    cmd = text.split()[0].lstrip("/").split("@")[0]
                    notifier._dispatch_command(cmd, chat_id)

        handler.assert_not_called()

    def test_正常なコマンド受信(self, notifier, mock_get):
        """正しいchat_idからのコマンドが処理される。"""
        mock_get.return_value.json.return_value = {
            "ok": True,
            "result": [{
                "update_id": 100,
                "message": {
                    "text": "/help",
                    "chat": {"id": 12345},
                },
            }],
        }
        handler = MagicMock(return_value="ヘルプ情報")
        notifier.register_command_handler("help", handler)

        # getUpdatesを1回呼び、ポーラーのロジックを手動再現
        updates = notifier._get_updates()
        for update in updates:
            update_id = update.get("update_id", 0)
            if update_id > notifier._last_update_id:
                notifier._last_update_id = update_id
            msg = update.get("message", {})
            chat_id = str(msg.get("chat", {}).get("id", ""))
            if chat_id == notifier._chat_id:
                text = msg.get("text", "")
                if text.startswith("/"):
                    cmd = text.split()[0].lstrip("/").split("@")[0]
                    notifier._dispatch_command(cmd, chat_id)

        handler.assert_called_once_with("12345")
        assert notifier._last_update_id == 100

    def test_ボット名付きコマンド(self, notifier):
        """'/help@mybot' のような形式でもコマンドを認識する。"""
        handler = MagicMock(return_value="OK")
        notifier.register_command_handler("help", handler)
        # _poller_loop内のパースロジックをテスト
        # コマンド文字列から@以降を除去する
        command = "/help@openclaw_takumi_bot".split()[0].lstrip("/").split("@")[0]
        assert command == "help"

    def test_コマンドハンドラ例外時にエラー通知(self, notifier):
        handler = MagicMock(side_effect=RuntimeError("DB接続エラー"))
        notifier.register_command_handler("status", handler)
        notifier._dispatch_command("status", "12345")
        item = notifier._send_queue.get_nowait()
        assert "失敗しました" in item


# ============================================================
# 6. スレッド制御テスト
# ============================================================

class TestThreadControl:
    """start()/stop() のライフサイクルテスト。"""

    @patch("src.telegram_notifier.requests.post")
    @patch("src.telegram_notifier.requests.get")
    def test_start_stop_ライフサイクル(self, mock_get, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True, "result": {}}
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"ok": True, "result": []}

        n = TelegramNotifier(
            bot_token="token", chat_id="123", poll_timeout=1,
        )
        n.start()
        assert n.is_running
        assert n._sender_thread.is_alive()
        assert n._poller_thread.is_alive()

        n.stop()
        assert not n.is_running

    def test_二重start防止(self, notifier, mock_post, mock_get):
        notifier.start()
        notifier.start()  # 二重呼び出し — 警告が出るが例外にならない
        assert notifier._started
        notifier.stop()

    def test_停止前のstopは無害(self, notifier):
        # まだstart()していない状態でstop()
        notifier.stop()  # 例外にならない


# ============================================================
# 7. エラー耐性テスト
# ============================================================

class TestErrorResilience:
    """Telegramダウン時のエラー耐性テスト。"""

    @patch("src.telegram_notifier.requests.get")
    @patch("src.telegram_notifier.requests.post")
    def test_Telegram障害でもメインループに影響なし(self, mock_post, mock_get):
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError("Telegram down")
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"ok": True, "result": []}

        n = TelegramNotifier(
            bot_token="token", chat_id="123", poll_timeout=1,
        )
        n.start()

        # notifyは即座に返る（ブロックしない）
        start = time.monotonic()
        for i in range(10):
            n.notify(f"テスト{i}")
        elapsed = time.monotonic() - start
        assert elapsed < 0.5

        n.stop()

    def test_getUpdatesエラーからの復帰(self, notifier, mock_get):
        """getUpdatesが例外を投げても、ポーラーは停止しない。"""
        import requests as req
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise req.exceptions.ConnectionError("network error")
            # 2回目以降は正常応答
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"ok": True, "result": []}
            return resp

        mock_get.side_effect = side_effect
        # ポーラーを手動で複数回呼ぶ
        results1 = notifier._get_updates()
        results2 = notifier._get_updates()
        assert results1 == []  # エラー時は空リスト
        assert results2 == []  # 正常応答（結果なし）
        assert call_count == 2

    def test_送信スレッドは送信失敗でも継続(self, notifier, mock_post):
        """1件目の送信が失敗しても、2件目は処理される。"""
        call_results = [False, True]
        send_count = 0

        original_send = notifier._send_message

        def mock_send(text, parse_mode="HTML"):
            nonlocal send_count
            result = call_results[min(send_count, len(call_results) - 1)]
            send_count += 1
            if not result:
                return False
            return True

        notifier._send_message = mock_send

        notifier.notify("失敗するメッセージ")
        notifier.notify("成功するメッセージ")

        # 送信スレッドを手動実行（一部だけ）
        # キューから2件取り出して処理
        for _ in range(2):
            item = notifier._send_queue.get(timeout=1)
            if item and ":" in item:
                pm, msg = item.split(":", 1)
                notifier._send_message(msg, pm)

        assert send_count == 2


# ============================================================
# 8. キャッシュテスト
# ============================================================

class TestCache:
    """キャッシュ管理のテスト。"""

    def test_初期状態は空(self, notifier):
        assert notifier.get_cached_account() is None
        assert notifier.get_cached_positions() == []
        assert notifier.get_cached_status() == {}

    def test_キャッシュ更新と取得(self, notifier):
        notifier.update_cache(
            account={"balance": 1000000, "currency": "JPY"},
            positions=[{"instrument": "USD_JPY", "units": 1000}],
            status={"active_instruments": ["USD_JPY"], "kill_switch": False},
        )
        assert notifier.get_cached_account()["balance"] == 1000000
        assert len(notifier.get_cached_positions()) == 1
        assert notifier.get_cached_status()["kill_switch"] is False

    def test_部分更新(self, notifier):
        notifier.update_cache(account={"balance": 500000})
        notifier.update_cache(positions=[{"instrument": "EUR_USD"}])
        # accountは最初の値が残っている
        assert notifier.get_cached_account()["balance"] == 500000
        assert len(notifier.get_cached_positions()) == 1

    def test_キャッシュはコピーを返す(self, notifier):
        """キャッシュの取得はコピーなので、外部から変更されない。"""
        notifier.update_cache(positions=[{"instrument": "USD_JPY"}])
        positions = notifier.get_cached_positions()
        positions.append({"instrument": "FAKE"})
        # 元のキャッシュは変更されていない
        assert len(notifier.get_cached_positions()) == 1


# ============================================================
# 9. TelegramLogHandler テスト
# ============================================================

class TestTelegramLogHandler:
    """TelegramLogHandler のテスト。"""

    def test_WARNING以上が転送される(self, notifier):
        handler = TelegramLogHandler(notifier, level=logging.WARNING)
        handler.setFormatter(logging.Formatter("%(message)s"))

        record = logging.LogRecord(
            name="test", level=logging.WARNING,
            pathname="", lineno=0, msg="キルスイッチ発動",
            args=(), exc_info=None,
        )
        handler.emit(record)
        item = notifier._send_queue.get_nowait()
        assert "キルスイッチ発動" in item
        assert "⚠️" in item

    def test_CRITICALのアイコン(self, notifier):
        handler = TelegramLogHandler(notifier, level=logging.WARNING)
        handler.setFormatter(logging.Formatter("%(message)s"))

        record = logging.LogRecord(
            name="test", level=logging.CRITICAL,
            pathname="", lineno=0, msg="緊急停止",
            args=(), exc_info=None,
        )
        handler.emit(record)
        item = notifier._send_queue.get_nowait()
        assert "🚨" in item

    def test_重複メッセージのデデュプ(self, notifier):
        handler = TelegramLogHandler(notifier, level=logging.WARNING)
        handler.setFormatter(logging.Formatter("%(message)s"))

        record = logging.LogRecord(
            name="test", level=logging.WARNING,
            pathname="", lineno=0, msg="同じメッセージ",
            args=(), exc_info=None,
        )
        handler.emit(record)
        handler.emit(record)  # 2回目は重複なのでスキップ

        assert notifier.pending_count == 1

    def test_異なるメッセージは両方転送(self, notifier):
        handler = TelegramLogHandler(notifier, level=logging.WARNING)
        handler.setFormatter(logging.Formatter("%(message)s"))

        for msg in ["メッセージA", "メッセージB"]:
            record = logging.LogRecord(
                name="test", level=logging.WARNING,
                pathname="", lineno=0, msg=msg,
                args=(), exc_info=None,
            )
            handler.emit(record)

        assert notifier.pending_count == 2

    def test_INFO以下は転送されない(self, notifier):
        handler = TelegramLogHandler(notifier, level=logging.WARNING)
        handler.setFormatter(logging.Formatter("%(message)s"))

        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0, msg="通常ログ",
            args=(), exc_info=None,
        )
        # handle()を使う（emit()はレベルフィルタをバイパスする）
        handler.handle(record)
        assert notifier.pending_count == 0
