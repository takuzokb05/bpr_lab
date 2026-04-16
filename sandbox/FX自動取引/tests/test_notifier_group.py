"""
R4: NotifierGroup のユニットテスト

複数通知先の統合ディスパッチ、None除外、
個別失敗時の継続動作を検証する。
"""

from unittest.mock import MagicMock, call

import pytest

from src.notifier_group import NotifierGroup


# ============================================================
# ヘルパー
# ============================================================


def _make_mock_notifier(name: str = "MockNotifier") -> MagicMock:
    """全メソッドを持つモック通知先を生成する。"""
    notifier = MagicMock()
    notifier.__class__.__name__ = name
    return notifier


# ============================================================
# 1. None除外テスト
# ============================================================


class TestNoneFiltering:
    """Noneの通知先が除外されることを検証"""

    def test_none_notifiers_are_filtered(self):
        """Noneが自動除外されること"""
        group = NotifierGroup([None, None, None])
        assert group.notifier_count == 0

    def test_mixed_none_and_valid(self):
        """Noneと有効な通知先が混在する場合"""
        mock1 = _make_mock_notifier()
        group = NotifierGroup([None, mock1, None])
        assert group.notifier_count == 1

    def test_empty_list(self):
        """空リストで初期化"""
        group = NotifierGroup([])
        assert group.notifier_count == 0
        # メソッド呼び出しがエラーにならないこと
        group.notify_signal("USD_JPY", "BUY")
        group.notify_kill_switch("test", True)
        group.notify_error("error", 3)
        group.notify_bot_status("起動")


# ============================================================
# 2. ディスパッチテスト
# ============================================================


class TestDispatch:
    """全通知先にメソッドが正しくディスパッチされることを検証"""

    def test_notify_signal_dispatched_to_all(self):
        """notify_signalが全通知先に呼ばれること"""
        mock1 = _make_mock_notifier("Telegram")
        mock2 = _make_mock_notifier("Slack")
        group = NotifierGroup([mock1, mock2])

        group.notify_signal("USD_JPY", "BUY", conviction_score=7, regime="TRENDING")

        mock1.notify_signal.assert_called_once_with(
            "USD_JPY", "BUY", conviction_score=7, regime="TRENDING",
        )
        mock2.notify_signal.assert_called_once_with(
            "USD_JPY", "BUY", conviction_score=7, regime="TRENDING",
        )

    def test_notify_kill_switch_dispatched(self):
        """notify_kill_switchが全通知先に呼ばれること"""
        mock1 = _make_mock_notifier()
        mock2 = _make_mock_notifier()
        group = NotifierGroup([mock1, mock2])

        group.notify_kill_switch("daily_loss", True)

        mock1.notify_kill_switch.assert_called_once_with("daily_loss", True)
        mock2.notify_kill_switch.assert_called_once_with("daily_loss", True)

    def test_notify_error_dispatched(self):
        """notify_errorが全通知先に呼ばれること"""
        mock1 = _make_mock_notifier()
        group = NotifierGroup([mock1])

        group.notify_error("接続エラー", 5)

        mock1.notify_error.assert_called_once_with("接続エラー", 5)

    def test_notify_bot_status_dispatched(self):
        """notify_bot_statusが全通知先に呼ばれること"""
        mock1 = _make_mock_notifier()
        mock2 = _make_mock_notifier()
        group = NotifierGroup([mock1, mock2])

        group.notify_bot_status("起動", "USD_JPY H4")

        mock1.notify_bot_status.assert_called_once_with("起動", "USD_JPY H4")
        mock2.notify_bot_status.assert_called_once_with("起動", "USD_JPY H4")


# ============================================================
# 3. 個別失敗時の継続テスト
# ============================================================


class TestFailureIsolation:
    """1つの通知先が失敗しても他の通知先に影響しないことを検証"""

    def test_first_notifier_fails_second_still_called(self):
        """最初の通知先が例外を投げても2番目は呼ばれること"""
        mock1 = _make_mock_notifier("Failing")
        mock1.notify_signal.side_effect = ConnectionError("タイムアウト")
        mock2 = _make_mock_notifier("Working")
        group = NotifierGroup([mock1, mock2])

        group.notify_signal("EUR_USD", "SELL")

        mock1.notify_signal.assert_called_once()
        mock2.notify_signal.assert_called_once_with("EUR_USD", "SELL")

    def test_notifier_without_method_is_skipped(self):
        """メソッドを持たない通知先はスキップされること"""
        # hasattr()チェック用: notify_signalを持たないオブジェクト
        class MinimalNotifier:
            pass

        minimal = MinimalNotifier()
        mock2 = _make_mock_notifier()
        group = NotifierGroup([minimal, mock2])

        group.notify_signal("GBP_JPY", "BUY")

        # MinimalNotifierはスキップされ、mock2だけ呼ばれる
        mock2.notify_signal.assert_called_once_with("GBP_JPY", "BUY")

    def test_all_notifiers_fail_no_exception(self):
        """全通知先が失敗してもNotifierGroup自体は例外を投げないこと"""
        mock1 = _make_mock_notifier()
        mock1.notify_error.side_effect = RuntimeError("fail1")
        mock2 = _make_mock_notifier()
        mock2.notify_error.side_effect = RuntimeError("fail2")
        group = NotifierGroup([mock1, mock2])

        # 例外は発生しない
        group.notify_error("test error", 3)

        mock1.notify_error.assert_called_once()
        mock2.notify_error.assert_called_once()
