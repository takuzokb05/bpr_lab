"""
FX自動取引システム — Slack Webhook通知モジュール

Slack Incoming Webhookを使用して取引イベントを通知する。
Block Kit形式で構造化メッセージを送信。
送信失敗はログに記録するが、メインのトレーディングループをブロックしない。
"""

import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

# 色定義
COLOR_GREEN = "#36a64f"   # 通常情報、ポジションオープン
COLOR_YELLOW = "#ffc107"  # 警告、CONTRADICT
COLOR_RED = "#dc3545"     # エラー、キルスイッチ、REJECT
COLOR_BLUE = "#2196F3"    # ステータス変更


class SlackNotifier:
    """
    Slack Incoming Webhook を使用した通知送信ハンドラ。

    TelegramNotifierと異なり、ポーリング/コマンド受信機能は持たない。
    送信失敗時は例外を投げず、logger.warningで記録してFalseを返す。
    """

    def __init__(self, webhook_url: str, timeout: int = 10) -> None:
        """
        Args:
            webhook_url: Slack Incoming WebhookのURL
            timeout: HTTP POSTのタイムアウト（秒）

        Raises:
            ValueError: webhook_urlが空の場合
        """
        if not webhook_url:
            raise ValueError(
                "SLACK_WEBHOOK_URL が設定されていません。"
                ".envファイルにSLACK_WEBHOOK_URLを設定してください。"
            )

        self._webhook_url = webhook_url
        self._timeout = timeout

    def notify(self, text: str, color: str = COLOR_GREEN) -> bool:
        """
        attachments形式でメッセージを送信する。

        Args:
            text: 送信するメッセージ本文
            color: サイドバーの色（hex）

        Returns:
            送信成功ならTrue、失敗ならFalse
        """
        payload: dict[str, Any] = {
            "attachments": [
                {
                    "color": color,
                    "text": text,
                    "mrkdwn_in": ["text"],
                }
            ]
        }
        return self._post(payload)

    def notify_signal(
        self,
        instrument: str,
        signal: str,
        conviction_score: int = 0,
        regime: str = "",
    ) -> None:
        """
        シグナル検出の通知。

        Args:
            instrument: 通貨ペア名
            signal: シグナル方向（BUY/SELL）
            conviction_score: 確信度スコア（0-10）
            regime: 市場レジーム
        """
        direction_icon = ":chart_with_upwards_trend:" if signal == "BUY" else ":chart_with_downwards_trend:"

        fields = [
            {"title": "通貨ペア", "value": instrument, "short": True},
            {"title": "方向", "value": f"{direction_icon} {signal}", "short": True},
        ]

        if conviction_score > 0:
            fields.append(
                {"title": "確信度", "value": f"{conviction_score}/10", "short": True}
            )

        if regime:
            fields.append(
                {"title": "レジーム", "value": regime, "short": True}
            )

        payload: dict[str, Any] = {
            "attachments": [
                {
                    "color": COLOR_GREEN,
                    "fallback": f"シグナル検出: {instrument} {signal}",
                    "title": "シグナル検出",
                    "fields": fields,
                    "mrkdwn_in": ["text", "fields"],
                }
            ]
        }
        self._post(payload)

    def notify_trade(
        self,
        instrument: str,
        direction: str,
        units: int,
        price: float,
        sl: float,
        tp: float,
        conviction: int = 0,
        ai_eval: str = "",
        regime: str = "",
    ) -> None:
        """
        取引実行の通知。Block Kit形式でconviction/AI eval/regime一覧表示。

        Args:
            instrument: 通貨ペア名
            direction: 取引方向（BUY/SELL）
            units: 取引数量
            price: 約定価格
            sl: ストップロス価格
            tp: テイクプロフィット価格
            conviction: 確信度スコア
            ai_eval: AI評価結果（AGREE/CONTRADICT/REJECT等）
            regime: 市場レジーム
        """
        fields = [
            {"title": "通貨ペア", "value": instrument, "short": True},
            {"title": "方向", "value": direction, "short": True},
            {"title": "数量", "value": f"{abs(units):,}", "short": True},
            {"title": "価格", "value": f"{price:.5f}", "short": True},
            {"title": "SL", "value": f"{sl:.5f}", "short": True},
            {"title": "TP", "value": f"{tp:.5f}", "short": True},
        ]

        if conviction > 0:
            fields.append(
                {"title": "確信度", "value": f"{conviction}/10", "short": True}
            )

        # AI評価の色分け
        color = COLOR_GREEN
        if ai_eval:
            fields.append(
                {"title": "AI評価", "value": ai_eval, "short": True}
            )
            if ai_eval == "CONTRADICT":
                color = COLOR_YELLOW
            elif ai_eval == "REJECT":
                color = COLOR_RED

        if regime:
            fields.append(
                {"title": "レジーム", "value": regime, "short": True}
            )

        payload: dict[str, Any] = {
            "attachments": [
                {
                    "color": color,
                    "fallback": f"取引実行: {instrument} {direction} {abs(units):,}",
                    "title": "取引実行",
                    "fields": fields,
                    "mrkdwn_in": ["text", "fields"],
                }
            ]
        }
        self._post(payload)

    def notify_position_closed(
        self,
        instrument: str,
        direction: str,
        close_price: float,
        pl: float,
        hold_minutes: Optional[int] = None,
        reason: str = "",
        pl_unknown: bool = False,
    ) -> None:
        """
        ポジション決済の通知。

        Args:
            instrument: 通貨ペア名
            direction: 方向（BUY/SELL）
            close_price: 決済価格
            pl: 実現損益（JPY）
            hold_minutes: 保有時間（分）
            reason: 決済理由（"TP/SL", "EMERGENCY", "手動", "ブローカー側決済" 等）
            pl_unknown: 損益が不明な場合 True（ブローカー履歴から取得できなかった場合）
        """
        # 損益の色分け: 利益=緑、損失=赤、不明=青
        if pl_unknown:
            color = COLOR_BLUE
            pl_display = "不明（要MT5履歴確認）"
            title_icon = ":grey_question:"
        elif pl > 0:
            color = COLOR_GREEN
            pl_display = f"+{pl:,.0f} JPY"
            title_icon = ":white_check_mark:"
        elif pl < 0:
            color = COLOR_RED
            pl_display = f"{pl:,.0f} JPY"
            title_icon = ":small_red_triangle_down:"
        else:
            color = COLOR_BLUE
            pl_display = "±0 JPY"
            title_icon = ":black_square_for_stop:"

        fields = [
            {"title": "通貨ペア", "value": instrument, "short": True},
            {"title": "方向", "value": direction, "short": True},
            {"title": "決済価格", "value": f"{close_price:.5f}", "short": True},
            {"title": "損益", "value": pl_display, "short": True},
        ]

        if hold_minutes is not None:
            if hold_minutes >= 60:
                hold_str = f"{hold_minutes // 60}時間{hold_minutes % 60}分"
            else:
                hold_str = f"{hold_minutes}分"
            fields.append({"title": "保有時間", "value": hold_str, "short": True})

        if reason:
            fields.append({"title": "決済理由", "value": reason, "short": True})

        payload: dict[str, Any] = {
            "attachments": [
                {
                    "color": color,
                    "fallback": f"ポジション決済: {instrument} {direction} {pl_display}",
                    "title": f"{title_icon} ポジション決済",
                    "fields": fields,
                    "mrkdwn_in": ["text", "fields"],
                }
            ]
        }
        self._post(payload)

    def notify_kill_switch(self, reason: str, is_active: bool) -> None:
        """
        キルスイッチ発動/解除の通知。

        Args:
            reason: キルスイッチの理由
            is_active: True=発動、False=解除
        """
        if is_active:
            payload: dict[str, Any] = {
                "attachments": [
                    {
                        "color": COLOR_RED,
                        "fallback": f"キルスイッチ発動: {reason}",
                        "title": ":rotating_light: キルスイッチ発動",
                        "fields": [
                            {"title": "理由", "value": reason, "short": False},
                            {"title": "状態", "value": "新規取引を停止しました", "short": False},
                        ],
                        "mrkdwn_in": ["text", "fields"],
                    }
                ]
            }
        else:
            payload = {
                "attachments": [
                    {
                        "color": COLOR_GREEN,
                        "fallback": "キルスイッチ解除",
                        "title": ":white_check_mark: キルスイッチ解除",
                        "text": "取引を再開します",
                        "mrkdwn_in": ["text"],
                    }
                ]
            }
        self._post(payload)

    def notify_error(self, error_msg: str, consecutive_count: int) -> None:
        """
        連続エラーの通知。

        Args:
            error_msg: エラーメッセージ
            consecutive_count: 連続エラー回数
        """
        payload: dict[str, Any] = {
            "attachments": [
                {
                    "color": COLOR_RED,
                    "fallback": f"エラー検出: {error_msg}",
                    "title": ":warning: エラー検出",
                    "fields": [
                        {"title": "連続エラー", "value": f"{consecutive_count}回", "short": True},
                        {"title": "内容", "value": error_msg, "short": False},
                    ],
                    "mrkdwn_in": ["text", "fields"],
                }
            ]
        }
        self._post(payload)

    def notify_bot_status(self, status: str, detail: str = "") -> None:
        """
        ボット起動/停止の通知。

        Args:
            status: ステータス文字列（例: "起動", "停止"）
            detail: 追加の詳細情報
        """
        text = f"ボット{status}"
        if detail:
            text += f"\n{detail}"

        payload: dict[str, Any] = {
            "attachments": [
                {
                    "color": COLOR_BLUE,
                    "fallback": text,
                    "title": f":robot_face: ボット{status}",
                    "text": detail if detail else None,
                    "mrkdwn_in": ["text"],
                }
            ]
        }

        # textがNoneの場合は除去
        attachment = payload["attachments"][0]
        if attachment.get("text") is None:
            del attachment["text"]

        self._post(payload)

    # ------------------------------------------------------------------
    # 内部: Webhook送信
    # ------------------------------------------------------------------

    def _post(self, payload: dict[str, Any]) -> bool:
        """
        Slack Webhookにペイロードを送信する。

        Args:
            payload: 送信するJSONペイロード

        Returns:
            送信成功ならTrue、失敗ならFalse
        """
        try:
            resp = requests.post(
                self._webhook_url,
                json=payload,
                timeout=self._timeout,
            )
            if resp.status_code == 200:
                return True

            logger.warning(
                "Slack送信失敗 (HTTP %d): %s",
                resp.status_code,
                resp.text[:200],
            )
            return False

        except requests.exceptions.Timeout:
            logger.warning("Slack送信タイムアウト (%ds)", self._timeout)
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("Slack接続エラー（ネットワーク不通の可能性）")
            return False
        except Exception as e:
            logger.warning("Slack送信中に予期しないエラー: %s", e)
            return False
