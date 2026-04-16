"""
FX自動取引システム — 通知グループモジュール

複数の通知先（Telegram, Slack等）を統合し、
一括で通知を送信するコンポジットパターン。
個別の通知先が失敗しても他の通知先への送信を継続する。
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class NotifierGroup:
    """複数の通知先をまとめて呼び出すコンポジット"""

    def __init__(self, notifiers: list) -> None:
        """
        Args:
            notifiers: TelegramNotifier / SlackNotifier等のリスト。
                      Noneは自動除外される。
        """
        self._notifiers = [n for n in notifiers if n is not None]

    def _dispatch(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """
        全通知先に対してメソッドを呼び出す。

        各通知先がメソッドを持っていない場合や、呼び出し失敗時は
        ログに記録して次の通知先に進む。

        Args:
            method_name: 呼び出すメソッド名
            *args: メソッドに渡す位置引数
            **kwargs: メソッドに渡すキーワード引数
        """
        for notifier in self._notifiers:
            if not hasattr(notifier, method_name):
                logger.debug(
                    "%s は %s メソッドを持っていません。スキップします。",
                    type(notifier).__name__,
                    method_name,
                )
                continue
            try:
                getattr(notifier, method_name)(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    "%s.%s() の呼び出しに失敗しました: %s",
                    type(notifier).__name__,
                    method_name,
                    e,
                )

    def notify_signal(self, instrument: str, signal: str, **kwargs: Any) -> None:
        """シグナル通知"""
        self._dispatch("notify_signal", instrument, signal, **kwargs)

    def notify_kill_switch(self, reason: str, is_active: bool) -> None:
        """キルスイッチ通知"""
        self._dispatch("notify_kill_switch", reason, is_active)

    def notify_error(self, error_msg: str, consecutive_count: int) -> None:
        """エラー通知"""
        self._dispatch("notify_error", error_msg, consecutive_count)

    def notify_bot_status(self, status: str, detail: str = "") -> None:
        """ボットステータス通知"""
        self._dispatch("notify_bot_status", status, detail)

    @property
    def notifier_count(self) -> int:
        """登録されている通知先の数"""
        return len(self._notifiers)
