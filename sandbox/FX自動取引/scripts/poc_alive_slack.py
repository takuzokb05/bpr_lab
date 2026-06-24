"""SPEC v2 PoC 死活監視 Slack 通知

DB の seasonal_judgments / loop_health / trades をチェックし、
- 最終判定が 10 分以内 → 生存通知 (毎時 :00 トリガー想定)
- 10 分超 → 警告通知

環境変数:
- SPEC_V2_SLACK_WEBHOOK_URL: Slack Incoming Webhook URL
  未設定なら stdout に出力するだけ (ローカルでのテスト用)

タスクスケジューラ登録: SPECv2_AliveCheck
- Trigger: AtStartup + Once(now) with RepetitionInterval=PT1H, Duration=indefinite
- ExecutionTimeLimit=PT0S
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

# 文字化け対策 (タスクスケジューラ環境での stdout cp932 問題)
import io
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

ROOT = Path(__file__).resolve().parents[1]
POC_DB_PATH = ROOT / "data" / "fx_spec_v2.db"

# 最終判定からこの分数以内なら生存扱い、超えたら警告
ALIVE_THRESHOLD_MINUTES = 10

logger = logging.getLogger("poc_alive_slack")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def parse_iso_utc(s: str) -> datetime:
    """ISO8601 文字列を UTC tz-aware datetime に変換"""
    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def gather_poc_status(db_path: Path) -> dict:
    """DB から PoC 状態をかき集める"""
    status: dict = {
        "db_path": str(db_path),
        "db_exists": db_path.exists(),
        "now_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if not db_path.exists():
        status["error"] = f"DB が存在しない: {db_path}"
        return status

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        # 最新 seasonal_judgments
        row = conn.execute("""
            SELECT id, judged_at_utc, regime, m15_above, h1_above
            FROM seasonal_judgments
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        if row:
            status["latest_judgment"] = {
                "id": row["id"],
                "judged_at_utc": row["judged_at_utc"],
                "regime": row["regime"],
                "m15_above": bool(row["m15_above"]) if row["m15_above"] is not None else None,
                "h1_above": bool(row["h1_above"]) if row["h1_above"] is not None else None,
            }
            latest_dt = parse_iso_utc(row["judged_at_utc"])
            delta_min = (datetime.now(timezone.utc) - latest_dt).total_seconds() / 60
            status["latest_judgment"]["age_minutes"] = round(delta_min, 1)
        else:
            status["latest_judgment"] = None

        # 累計判定件数
        n = conn.execute("SELECT COUNT(*) FROM seasonal_judgments").fetchone()[0]
        status["total_judgments"] = int(n)

        # 最新 loop_health
        row = conn.execute("""
            SELECT event_at_utc, event_type, message
            FROM loop_health ORDER BY id DESC LIMIT 1
        """).fetchone()
        if row:
            status["latest_health"] = {
                "event_at_utc": row["event_at_utc"],
                "event_type": row["event_type"],
                "message": row["message"],
            }
        else:
            status["latest_health"] = None

        # オープン中ポジション件数
        n = conn.execute("SELECT COUNT(*) FROM trades WHERE status='open'").fetchone()[0]
        status["n_open_trades"] = int(n)

        # 直近24h ENTRY/CLOSE 件数
        since = (datetime.now(timezone.utc).timestamp() - 24 * 3600)
        # SQLite では ISO 文字列比較で OK (UTC で揃えてあるので)
        # 24h 前の ISO 文字列を作る
        from datetime import timedelta
        since_iso = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(timespec="seconds")
        n_entries = conn.execute(
            "SELECT COUNT(*) FROM trades WHERE entry_at_utc >= ?", (since_iso,),
        ).fetchone()[0]
        n_closes = conn.execute(
            "SELECT COUNT(*) FROM trade_closures WHERE exit_at_utc >= ?", (since_iso,),
        ).fetchone()[0]
        status["entries_24h"] = int(n_entries)
        status["closes_24h"] = int(n_closes)
    finally:
        conn.close()

    return status


def build_message(status: dict, alive: bool) -> str:
    """Slack 用テキストを組み立てる (絵文字+簡潔フォーマット)"""
    icon = "🟢" if alive else "🚨"
    head = "PoC 死活: 正常" if alive else "PoC 死活: ⚠️ 停止疑い"

    lines = [f"{icon} *[SPEC v2 PoC] {head}*"]
    if status.get("error"):
        lines.append(f"エラー: `{status['error']}`")
        lines.append(f"now (UTC): `{status['now_utc']}`")
        return "\n".join(lines)

    lj = status.get("latest_judgment")
    if lj:
        lines.append(
            f"最終判定: `{lj['judged_at_utc']}` ({lj['age_minutes']:.1f}分前) "
            f"regime=`{lj['regime']}` M15above={lj['m15_above']} H1above={lj['h1_above']}"
        )
    else:
        lines.append("最終判定: (なし)")

    lines.append(f"累計判定: {status.get('total_judgments', 0)} 件")

    lh = status.get("latest_health")
    if lh:
        lines.append(
            f"loop_health 最新: `{lh['event_at_utc']}` {lh['event_type']} "
            f"`{lh.get('message') or ''}`"
        )

    lines.append(
        f"open positions: {status.get('n_open_trades', 0)} | "
        f"直近24h: ENTRY {status.get('entries_24h', 0)} / CLOSE {status.get('closes_24h', 0)}"
    )
    return "\n".join(lines)


def post_slack(webhook: str, text: str) -> bool:
    """Slack Webhook に POST。失敗時 False。"""
    try:
        resp = requests.post(webhook, json={"text": text}, timeout=10)
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
    parser.add_argument("--threshold", type=float, default=ALIVE_THRESHOLD_MINUTES,
                       help=f"生存とみなす最終判定からの分数 (default: {ALIVE_THRESHOLD_MINUTES})")
    parser.add_argument("--force-alive", action="store_true",
                       help="alive 通知を強制送信 (テスト用)")
    parser.add_argument("--quiet-when-alive", action="store_true",
                       help="alive 時は通知せず、警告時のみ通知する (常時実行向け)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Slack に送らず stdout に出力するだけ")
    args = parser.parse_args()

    status = gather_poc_status(args.db)

    # alive 判定
    if status.get("error"):
        alive = False
    elif status.get("latest_judgment") is None:
        alive = False
    else:
        alive = status["latest_judgment"]["age_minutes"] <= args.threshold

    if args.force_alive:
        alive = True

    msg = build_message(status, alive)
    logger.info(f"alive={alive} status_summary={json.dumps({k: v for k, v in status.items() if k != 'now_utc'}, default=str, ensure_ascii=False)[:300]}")
    print(msg)

    webhook = os.environ.get("SPEC_V2_SLACK_WEBHOOK_URL")
    if args.dry_run or not webhook:
        if not webhook:
            logger.warning("SPEC_V2_SLACK_WEBHOOK_URL 未設定。Slack には送信しない (stdout のみ)")
        return 0 if alive else 2

    # quiet-when-alive: alive のときは送らない (毎時実行で alive 連投を避ける用途)
    if args.quiet_when_alive and alive:
        logger.info("quiet-when-alive: alive のため Slack 送信スキップ")
        return 0

    ok = post_slack(webhook, msg)
    if not ok:
        return 3
    return 0 if alive else 2


if __name__ == "__main__":
    sys.exit(main())
