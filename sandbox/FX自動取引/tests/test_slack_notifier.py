"""
SlackNotifier のユニットテスト

Slack Webhookへの送信をモックし、各通知メソッドの
ペイロード形式・色分け・エラーハンドリングを検証する。
"""

import pytest
from unittest.mock import patch, MagicMock

import requests

from src.slack_notifier import (
    SlackNotifier,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_BLUE,
)


DUMMY_WEBHOOK = "https://hooks.slack.com/services/T00/B00/xxxxx"


# ============================================================
# 初期化テスト
# ============================================================


class TestSlackNotifierInit:
    """初期化に関するテスト"""

    def test_empty_webhook_url_raises(self):
        """webhook_urlが空ならValueError"""
        with pytest.raises(ValueError, match="SLACK_WEBHOOK_URL"):
            SlackNotifier(webhook_url="")

    def test_none_webhook_url_raises(self):
        """webhook_urlがNone相当の空文字ならValueError"""
        with pytest.raises(ValueError):
            SlackNotifier(webhook_url="")

    def test_valid_init(self):
        """正常な初期化"""
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK, timeout=15)
        assert notifier._webhook_url == DUMMY_WEBHOOK
        assert notifier._timeout == 15

    def test_default_timeout(self):
        """デフォルトタイムアウトは10秒"""
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)
        assert notifier._timeout == 10


# ============================================================
# notify() テスト
# ============================================================


class TestNotify:
    """notify()メソッドのテスト"""

    @patch("src.slack_notifier.requests.post")
    def test_notify_success(self, mock_post):
        """正常送信でTrueを返す"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        result = notifier.notify("テストメッセージ")

        assert result is True
        mock_post.assert_called_once()
        # ペイロードの確認
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "attachments" in payload
        assert payload["attachments"][0]["color"] == COLOR_GREEN
        assert payload["attachments"][0]["text"] == "テストメッセージ"

    @patch("src.slack_notifier.requests.post")
    def test_notify_custom_color(self, mock_post):
        """カスタム色指定が反映される"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify("警告メッセージ", color=COLOR_RED)

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["attachments"][0]["color"] == COLOR_RED

    @patch("src.slack_notifier.requests.post")
    def test_notify_http_error_returns_false(self, mock_post):
        """HTTP 400等でFalseを返す（例外は投げない）"""
        mock_post.return_value = MagicMock(status_code=400, text="invalid_payload")
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        result = notifier.notify("テスト")

        assert result is False

    @patch("src.slack_notifier.requests.post")
    def test_notify_timeout_returns_false(self, mock_post):
        """タイムアウト時にFalseを返す（例外は投げない）"""
        mock_post.side_effect = requests.exceptions.Timeout("timeout")
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        result = notifier.notify("テスト")

        assert result is False

    @patch("src.slack_notifier.requests.post")
    def test_notify_connection_error_returns_false(self, mock_post):
        """接続エラー時にFalseを返す（例外は投げない）"""
        mock_post.side_effect = requests.exceptions.ConnectionError("refused")
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        result = notifier.notify("テスト")

        assert result is False


# ============================================================
# notify_signal() テスト
# ============================================================


class TestNotifySignal:
    """notify_signal()メソッドのテスト"""

    @patch("src.slack_notifier.requests.post")
    def test_signal_buy(self, mock_post):
        """BUYシグナルのフォーマット確認"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify_signal("USD_JPY", "BUY", conviction_score=7, regime="TRENDING")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        attachment = payload["attachments"][0]

        assert attachment["title"] == "シグナル検出"
        # fieldsに通貨ペア、方向、確信度、レジームが含まれる
        field_titles = [f["title"] for f in attachment["fields"]]
        assert "通貨ペア" in field_titles
        assert "方向" in field_titles
        assert "確信度" in field_titles
        assert "レジーム" in field_titles

        # 値の確認
        field_map = {f["title"]: f["value"] for f in attachment["fields"]}
        assert field_map["通貨ペア"] == "USD_JPY"
        assert "BUY" in field_map["方向"]
        assert field_map["確信度"] == "7/10"
        assert field_map["レジーム"] == "TRENDING"

    @patch("src.slack_notifier.requests.post")
    def test_signal_without_optional_fields(self, mock_post):
        """オプションフィールド無しのシグナル通知"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify_signal("EUR_USD", "SELL")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        fields = payload["attachments"][0]["fields"]
        field_titles = [f["title"] for f in fields]

        # 確信度・レジームは含まれない
        assert "確信度" not in field_titles
        assert "レジーム" not in field_titles


# ============================================================
# notify_trade() テスト
# ============================================================


class TestNotifyTrade:
    """notify_trade()メソッドのテスト"""

    @patch("src.slack_notifier.requests.post")
    def test_trade_with_all_fields(self, mock_post):
        """全フィールド指定の取引通知"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify_trade(
            instrument="USD_JPY",
            direction="BUY",
            units=10000,
            price=150.123,
            sl=149.500,
            tp=151.500,
            conviction=8,
            ai_eval="AGREE",
            regime="TRENDING",
        )

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        attachment = payload["attachments"][0]

        assert attachment["title"] == "取引実行"
        field_map = {f["title"]: f["value"] for f in attachment["fields"]}
        assert field_map["通貨ペア"] == "USD_JPY"
        assert field_map["方向"] == "BUY"
        assert field_map["数量"] == "10,000"
        assert "150.12300" in field_map["価格"]
        assert field_map["確信度"] == "8/10"
        assert field_map["AI評価"] == "AGREE"
        assert field_map["レジーム"] == "TRENDING"

    @patch("src.slack_notifier.requests.post")
    def test_trade_contradict_color(self, mock_post):
        """AI評価CONTRADICTは黄色"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify_trade(
            instrument="EUR_USD", direction="SELL",
            units=5000, price=1.08000, sl=1.09000, tp=1.06000,
            ai_eval="CONTRADICT",
        )

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["attachments"][0]["color"] == COLOR_YELLOW

    @patch("src.slack_notifier.requests.post")
    def test_trade_reject_color(self, mock_post):
        """AI評価REJECTは赤色"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify_trade(
            instrument="GBP_JPY", direction="BUY",
            units=3000, price=190.000, sl=189.000, tp=192.000,
            ai_eval="REJECT",
        )

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["attachments"][0]["color"] == COLOR_RED


# ============================================================
# notify_kill_switch() テスト
# ============================================================


class TestNotifyKillSwitch:
    """notify_kill_switch()メソッドのテスト"""

    @patch("src.slack_notifier.requests.post")
    def test_kill_switch_activated(self, mock_post):
        """キルスイッチ発動通知"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify_kill_switch("ボラティリティ異常", is_active=True)

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        attachment = payload["attachments"][0]
        assert attachment["color"] == COLOR_RED
        assert "キルスイッチ発動" in attachment["title"]

    @patch("src.slack_notifier.requests.post")
    def test_kill_switch_deactivated(self, mock_post):
        """キルスイッチ解除通知"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify_kill_switch("", is_active=False)

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        attachment = payload["attachments"][0]
        assert attachment["color"] == COLOR_GREEN
        assert "キルスイッチ解除" in attachment["title"]


# ============================================================
# notify_error() テスト
# ============================================================


class TestNotifyError:
    """notify_error()メソッドのテスト"""

    @patch("src.slack_notifier.requests.post")
    def test_error_notification(self, mock_post):
        """エラー通知のフォーマット確認"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify_error("MT5接続タイムアウト", consecutive_count=3)

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        attachment = payload["attachments"][0]
        assert attachment["color"] == COLOR_RED
        field_map = {f["title"]: f["value"] for f in attachment["fields"]}
        assert field_map["連続エラー"] == "3回"
        assert field_map["内容"] == "MT5接続タイムアウト"


# ============================================================
# notify_bot_status() テスト
# ============================================================


class TestNotifyBotStatus:
    """notify_bot_status()メソッドのテスト"""

    @patch("src.slack_notifier.requests.post")
    def test_bot_status_with_detail(self, mock_post):
        """ボットステータス通知（詳細付き）"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify_bot_status("起動", detail="USD_JPY H4 60秒間隔")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        attachment = payload["attachments"][0]
        assert attachment["color"] == COLOR_BLUE
        assert "ボット起動" in attachment["title"]
        assert attachment["text"] == "USD_JPY H4 60秒間隔"

    @patch("src.slack_notifier.requests.post")
    def test_bot_status_without_detail(self, mock_post):
        """ボットステータス通知（詳細なし）"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify_bot_status("停止")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        attachment = payload["attachments"][0]
        assert "ボット停止" in attachment["title"]
        # textキーは存在しないこと
        assert "text" not in attachment


# ============================================================
# 予期しないエラーのハンドリングテスト
# ============================================================


class TestUnexpectedErrors:
    """予期しない例外のハンドリング"""

    @patch("src.slack_notifier.requests.post")
    def test_unexpected_exception_returns_false(self, mock_post):
        """予期しない例外でもFalseを返し、例外は投げない"""
        mock_post.side_effect = RuntimeError("unexpected")
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        result = notifier.notify("テスト")

        assert result is False

    @patch("src.slack_notifier.requests.post")
    def test_webhook_url_passed_correctly(self, mock_post):
        """Webhook URLが正しく送信先に使われる"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK)

        notifier.notify("テスト")

        call_args = mock_post.call_args
        assert call_args[0][0] == DUMMY_WEBHOOK

    @patch("src.slack_notifier.requests.post")
    def test_timeout_passed_correctly(self, mock_post):
        """カスタムタイムアウトが正しく設定される"""
        mock_post.return_value = MagicMock(status_code=200)
        notifier = SlackNotifier(webhook_url=DUMMY_WEBHOOK, timeout=5)

        notifier.notify("テスト")

        call_kwargs = mock_post.call_args
        timeout = call_kwargs.kwargs.get("timeout") or call_kwargs[1].get("timeout")
        assert timeout == 5
