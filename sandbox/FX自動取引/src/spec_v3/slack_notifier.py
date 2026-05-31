"""SPEC v3 — Slack 通知ラッパ

既存 `src/slack_notifier.SlackNotifier` を利用しつつ、SPEC v3 専用の
通知メソッド (LLM 判定詳細、撤退条件アラート、死活レポート、日次サマリ) を提供する。

環境変数:
- SPEC_V3_SLACK_WEBHOOK_URL: 専用 Webhook (推奨、未設定なら SLACK_ALERTS_WEBHOOK_URL を fallback)
- SLACK_ALERTS_WEBHOOK_URL: 共通アラート Webhook (fallback 1)
- SLACK_WEBHOOK_URL: メイン Webhook (fallback 2)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from src.slack_notifier import (
    COLOR_BLUE, COLOR_GREEN, COLOR_RED, COLOR_YELLOW, SlackNotifier,
)

logger = logging.getLogger(__name__)


def _resolve_webhook_url() -> Optional[str]:
    """SPEC v3 用 Webhook URL を環境変数から解決"""
    for env_key in (
        "SPEC_V3_SLACK_WEBHOOK_URL",
        "SLACK_ALERTS_WEBHOOK_URL",
        "SLACK_WEBHOOK_URL",
    ):
        v = os.environ.get(env_key, "").strip()
        if v:
            return v
    return None


class SpecV3SlackNotifier:
    """SPEC v3 ループから呼び出す通知ラッパ。Webhook 未設定時は no-op。"""

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self._url = webhook_url or _resolve_webhook_url()
        if not self._url:
            logger.warning("SPEC_V3_SLACK_WEBHOOK_URL 未設定: Slack 通知は no-op")
            self._notifier: Optional[SlackNotifier] = None
        else:
            self._notifier = SlackNotifier(self._url)

    @property
    def enabled(self) -> bool:
        return self._notifier is not None

    # ============================================================
    # 起動 / 停止
    # ============================================================

    def bot_started(self, detail: str = "") -> None:
        if self._notifier:
            self._notifier.notify_bot_status("SPEC v3 起動", detail)

    def bot_stopped(self, detail: str = "") -> None:
        if self._notifier:
            self._notifier.notify_bot_status("SPEC v3 停止", detail)

    # ============================================================
    # シグナル & 取引イベント
    # ============================================================

    def signal_accepted(
        self, pair: str, direction: str, confidence: float,
        entry: float, sl: float, tp: float, reasoning: str,
    ) -> None:
        if not self._notifier:
            return
        text = (
            f":dart: *SPEC v3 採用シグナル* `{pair}` *{direction.upper()}*\n"
            f"entry={entry:.5f}  SL={sl:.5f}  TP={tp:.5f}\n"
            f"LLM confidence={confidence:.2f}\n"
            f"> {reasoning[:200]}"
        )
        self._notifier.notify(text, color=COLOR_GREEN)

    def signal_rejected(
        self, pair: str, direction: str, label: str, confidence: float,
        threshold: float, decision_reason: str,
    ) -> None:
        if not self._notifier:
            return
        color = COLOR_YELLOW
        if label == "REJECT":
            color = COLOR_RED
        elif label == "API_ERROR":
            color = COLOR_RED
        text = (
            f":no_entry_sign: SPEC v3 見送り `{pair}` {direction} "
            f"label={label} conf={confidence:.2f} (threshold {threshold:.2f}) "
            f"reason={decision_reason}"
        )
        self._notifier.notify(text, color=color)

    def trade_entered(
        self, pair: str, direction: str, ticket: int,
        entry: float, sl: float, tp: float, lots: float, confidence: float,
    ) -> None:
        if not self._notifier:
            return
        text = (
            f":rocket: *SPEC v3 ENTRY* `{pair}` *{direction.upper()}* "
            f"ticket={ticket} lots={lots} entry={entry:.5f} "
            f"SL={sl:.5f} TP={tp:.5f} conf={confidence:.2f}"
        )
        self._notifier.notify(text, color=COLOR_GREEN)

    def trade_closed(
        self, pair: str, direction: str, pnl_pips: float, pnl_jpy: float,
        reason: str, holding_minutes: int,
    ) -> None:
        if not self._notifier:
            return
        color = COLOR_GREEN if pnl_jpy >= 0 else COLOR_RED
        icon = ":white_check_mark:" if pnl_jpy >= 0 else ":small_red_triangle_down:"
        text = (
            f"{icon} *SPEC v3 CLOSE* `{pair}` {direction} "
            f"PnL={pnl_pips:+.1f}p ({pnl_jpy:+,.0f} JPY) "
            f"reason={reason} hold={holding_minutes}m"
        )
        self._notifier.notify(text, color=color)

    # ============================================================
    # キルスイッチ & 撤退
    # ============================================================

    def kill_switch(self, reason: str, is_active: bool) -> None:
        if self._notifier:
            self._notifier.notify_kill_switch(f"SPEC v3: {reason}", is_active)

    def retreat_triggered(self, code: str, message: str) -> None:
        if not self._notifier:
            return
        text = (
            f":octagonal_sign: *SPEC v3 撤退条件発火* code=`{code}`\n{message}"
        )
        self._notifier.notify(text, color=COLOR_RED)

    def daily_loss_warn(self, pct: float, level: str) -> None:
        if not self._notifier:
            return
        text = f":warning: 日次損失 {pct:.1%} ({level})"
        color = COLOR_YELLOW if level == "warn" else COLOR_RED
        self._notifier.notify(text, color=color)

    # ============================================================
    # 死活 / 日次サマリ
    # ============================================================

    def alive_report(self, payload: dict) -> None:
        """毎時死活レポート (JSON dict をフラットに整形)"""
        if not self._notifier:
            return
        lines = ["*SPEC v3 死活レポート*"]
        for k, v in payload.items():
            lines.append(f"- {k}: {v}")
        self._notifier.notify("\n".join(lines), color=COLOR_BLUE)

    def daily_summary(self, summary: dict) -> None:
        """日次サマリ"""
        if not self._notifier:
            return
        date_jst = summary.get("date_jst", "")
        lines = [f"*SPEC v3 Daily Summary — {date_jst}*"]
        for pair, stats in summary.get("per_pair", {}).items():
            lines.append(
                f"`{pair}`: trades={stats.get('n_closed', 0)} "
                f"win={stats.get('win_rate', 0):.0%} "
                f"PF={stats.get('pf', 0):.2f} "
                f"PnL={stats.get('pnl_jpy', 0):+,.0f} JPY"
            )
        dist = summary.get("llm_label_distribution", {})
        if dist:
            lines.append(f"LLM: " + " ".join(f"{k}={v}" for k, v in dist.items()))
        rolling = summary.get("rolling_30d_pf", {})
        if rolling:
            lines.append("Rolling 30d PF: " + " ".join(
                f"{p}={v:.2f}" if v is not None else f"{p}=N/A"
                for p, v in rolling.items()
            ))
        cost = summary.get("llm_cost_usd")
        if cost is not None:
            lines.append(f"LLM cost (month): ${cost:.3f} (≒ ¥{cost * 150:.0f})")
        retreat_code = summary.get("retreat_action", "ok")
        lines.append(f"Retreat status: {retreat_code}")
        self._notifier.notify("\n".join(lines), color=COLOR_BLUE)

    # ============================================================
    # 低レベル
    # ============================================================

    def raw(self, text: str, color: str = COLOR_BLUE) -> None:
        if self._notifier:
            self._notifier.notify(text, color=color)
