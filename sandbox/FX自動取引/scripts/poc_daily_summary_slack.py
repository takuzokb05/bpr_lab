"""SPEC v2 PoC 日次サマリ Slack 通知

直近24時間 (現在時刻 -24h 〜 現在時刻) の集計を Slack に Block Kit 形式で投稿:
- 判定件数 / regime 分布 (calm / transitional / volatile)
- M15 above=True 件数と割合
- H1 YZ_vol の min/median/max
- ENTRY / CLOSE 件数、現在 open 件数
- PnL 合計 (pips, JPY)

環境変数:
- SPEC_V2_SLACK_WEBHOOK_URL: Slack Incoming Webhook URL

タスクスケジューラ登録: SPECv2_DailySummary
- Trigger: Daily at JST 07:00
- ExecutionTimeLimit=PT0S
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import os
import sqlite3
import statistics
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import requests

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

ROOT = Path(__file__).resolve().parents[1]
POC_DB_PATH = ROOT / "data" / "fx_spec_v2.db"

logger = logging.getLogger("poc_daily_summary")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def collect_summary(db_path: Path, hours: int = 24) -> dict:
    """直近 hours 時間の集計を返す"""
    now_utc = datetime.now(timezone.utc)
    since = now_utc - timedelta(hours=hours)
    since_iso = since.isoformat(timespec="seconds")

    summary: dict = {
        "range_start_utc": since_iso,
        "range_end_utc": now_utc.isoformat(timespec="seconds"),
        "hours": hours,
    }

    if not db_path.exists():
        summary["error"] = f"DB が存在しない: {db_path}"
        return summary

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        # 判定件数 + regime 分布
        total = conn.execute(
            "SELECT COUNT(*) FROM seasonal_judgments WHERE judged_at_utc >= ?",
            (since_iso,),
        ).fetchone()[0]
        summary["n_judgments"] = int(total)

        rows = conn.execute("""
            SELECT regime, COUNT(*) AS cnt
            FROM seasonal_judgments
            WHERE judged_at_utc >= ?
            GROUP BY regime
        """, (since_iso,)).fetchall()
        regime_dist = {r["regime"]: int(r["cnt"]) for r in rows}
        # 0 件のキーも埋める
        for k in ("calm", "transitional", "volatile"):
            regime_dist.setdefault(k, 0)
        summary["regime_distribution"] = regime_dist

        # M15 above=True 件数
        m15_above_n = conn.execute("""
            SELECT COUNT(*) FROM seasonal_judgments
            WHERE judged_at_utc >= ? AND m15_above = 1
        """, (since_iso,)).fetchone()[0]
        summary["m15_above_count"] = int(m15_above_n)
        summary["m15_above_ratio"] = (m15_above_n / total) if total > 0 else 0.0

        # H1 YZ_vol の min/median/max
        h1_rows = conn.execute("""
            SELECT h1_yz_vol FROM seasonal_judgments
            WHERE judged_at_utc >= ? AND h1_yz_vol IS NOT NULL
        """, (since_iso,)).fetchall()
        h1_vals = [r["h1_yz_vol"] for r in h1_rows]
        if h1_vals:
            summary["h1_yz_vol_min"] = float(min(h1_vals))
            summary["h1_yz_vol_median"] = float(statistics.median(h1_vals))
            summary["h1_yz_vol_max"] = float(max(h1_vals))
        else:
            summary["h1_yz_vol_min"] = None
            summary["h1_yz_vol_median"] = None
            summary["h1_yz_vol_max"] = None

        # ENTRY 件数 (期間内に entry_at_utc を持つ trades)
        n_entries = conn.execute(
            "SELECT COUNT(*) FROM trades WHERE entry_at_utc >= ?",
            (since_iso,),
        ).fetchone()[0]
        summary["entries"] = int(n_entries)

        # CLOSE 件数 (期間内に exit_at_utc を持つ closures)
        n_closes = conn.execute(
            "SELECT COUNT(*) FROM trade_closures WHERE exit_at_utc >= ?",
            (since_iso,),
        ).fetchone()[0]
        summary["closes"] = int(n_closes)

        # 現在 open
        n_open = conn.execute(
            "SELECT COUNT(*) FROM trades WHERE status='open'"
        ).fetchone()[0]
        summary["n_open_now"] = int(n_open)

        # PnL 合計 (closures only)
        row = conn.execute("""
            SELECT
                COALESCE(SUM(pnl_pips), 0) AS total_pips,
                COALESCE(SUM(pnl_jpy), 0) AS total_jpy
            FROM trade_closures
            WHERE exit_at_utc >= ?
        """, (since_iso,)).fetchone()
        summary["pnl_pips_total"] = float(row["total_pips"])
        summary["pnl_jpy_total"] = float(row["total_jpy"])

        # exit_reason 内訳
        reason_rows = conn.execute("""
            SELECT exit_reason, COUNT(*) AS cnt
            FROM trade_closures
            WHERE exit_at_utc >= ?
            GROUP BY exit_reason
        """, (since_iso,)).fetchall()
        summary["exit_reasons"] = {r["exit_reason"]: int(r["cnt"]) for r in reason_rows}
    finally:
        conn.close()

    return summary


def fmt_or_dash(v: Optional[float], fmt: str = "{:.5f}") -> str:
    return fmt.format(v) if v is not None else "N/A"


def build_blocks(summary: dict) -> dict:
    """Slack Block Kit ペイロードを構築"""
    if summary.get("error"):
        return {
            "text": f"[SPEC v2 PoC] 日次サマリ エラー: {summary['error']}",
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn",
                    "text": f":x: *[SPEC v2 PoC] 日次サマリ エラー*\n`{summary['error']}`"}},
            ],
        }

    rd = summary["regime_distribution"]
    total = summary["n_judgments"]
    def pct(n: int) -> str:
        return f"{(n / total * 100):.1f}%" if total > 0 else "-"

    # 期間表示 (JST 換算)
    start_jst = datetime.fromisoformat(summary["range_start_utc"]).astimezone(
        timezone(timedelta(hours=9))
    ).strftime("%m-%d %H:%M")
    end_jst = datetime.fromisoformat(summary["range_end_utc"]).astimezone(
        timezone(timedelta(hours=9))
    ).strftime("%m-%d %H:%M JST")
    range_label = f"{start_jst} 〜 {end_jst}"

    pnl_pips = summary["pnl_pips_total"]
    pnl_jpy = summary["pnl_jpy_total"]
    pnl_icon = "📈" if pnl_pips > 0 else ("📉" if pnl_pips < 0 else "➖")

    reasons = summary.get("exit_reasons", {})
    reasons_text = (
        ", ".join(f"{k}={v}" for k, v in reasons.items())
        if reasons else "(なし)"
    )

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "SPEC v2 PoC 日次サマリ"},
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f":clock1: {range_label} (直近 {summary['hours']}h)"}
            ],
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*判定数*\n{total}"},
                {"type": "mrkdwn",
                 "text": f"*regime 分布*\ncalm: {rd['calm']} ({pct(rd['calm'])})\n"
                         f"transitional: {rd['transitional']} ({pct(rd['transitional'])})\n"
                         f"volatile: {rd['volatile']} ({pct(rd['volatile'])})"},
            ],
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn",
                 "text": f"*M15 above*\n{summary['m15_above_count']} 件 "
                         f"({summary['m15_above_ratio']*100:.1f}%)"},
                {"type": "mrkdwn",
                 "text": f"*H1 YZ_vol*\nmin: `{fmt_or_dash(summary['h1_yz_vol_min'])}`\n"
                         f"median: `{fmt_or_dash(summary['h1_yz_vol_median'])}`\n"
                         f"max: `{fmt_or_dash(summary['h1_yz_vol_max'])}`"},
            ],
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn",
                 "text": f"*取引*\nENTRY: {summary['entries']}\n"
                         f"CLOSE: {summary['closes']}\n"
                         f"open now: {summary['n_open_now']}"},
                {"type": "mrkdwn",
                 "text": f"*PnL (24h)*\n{pnl_icon} {pnl_pips:+.1f} pips\n"
                         f"{pnl_jpy:+.0f} JPY"},
            ],
        },
    ]
    if reasons:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn",
                          "text": f"*決済理由内訳*: {reasons_text}"}],
        })

    # fallback テキスト (通知センター表示用)
    fallback = (
        f"[SPEC v2 PoC] {range_label} | "
        f"判定 {total} | volatile {rd['volatile']} | "
        f"ENTRY {summary['entries']} / CLOSE {summary['closes']} | "
        f"PnL {pnl_pips:+.1f} pips"
    )

    return {"text": fallback, "blocks": blocks}


def post_slack(webhook: str, payload: dict) -> bool:
    try:
        resp = requests.post(webhook, json=payload, timeout=10)
        if resp.status_code >= 300:
            logger.warning(f"Slack POST 失敗: status={resp.status_code} body={resp.text[:200]}")
            return False
        return True
    except Exception as e:
        logger.warning(f"Slack POST 例外: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=POC_DB_PATH,
                       help="PoC DB パス (default: data/fx_spec_v2.db)")
    parser.add_argument("--hours", type=int, default=24,
                       help="集計対象の時間 (default: 24)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Slack に送らず stdout に payload を出力")
    args = parser.parse_args()

    summary = collect_summary(args.db, hours=args.hours)
    logger.info(
        "summary: " +
        json.dumps(summary, ensure_ascii=False, default=str)[:600]
    )
    payload = build_blocks(summary)

    webhook = os.environ.get("SPEC_V2_SLACK_WEBHOOK_URL")
    if args.dry_run or not webhook:
        if not webhook:
            logger.warning("SPEC_V2_SLACK_WEBHOOK_URL 未設定。Slack には送信しない (stdout のみ)")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    ok = post_slack(webhook, payload)
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
