"""SPEC v3 死活監視 Slack 通知 (1 時間ごとタスクスケジューラ起動)

DB から最新の判定・ループヘルス・open trade をかき集めて Slack に投稿。

環境変数 (どれか 1 つあれば動く):
- SPEC_V3_SLACK_WEBHOOK_URL
- SLACK_ALERTS_WEBHOOK_URL
- SLACK_WEBHOOK_URL

タスクスケジューラ登録:
- AtStartup + Once(now+5m) RepetitionInterval=PT1H
- ExecutionTimeLimit=PT0S
"""
from __future__ import annotations

import argparse
import io
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    if (ROOT / ".env").exists():
        load_dotenv(ROOT / ".env")
except ImportError:
    pass

DB_PATH = ROOT / "data" / "fx_spec_v3.db"
ALIVE_THRESHOLD_MIN = 10

logger = logging.getLogger("spec_v3_alive")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def parse_iso(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def gather_status() -> dict:
    """DB の現状をかき集める"""
    now = datetime.now(timezone.utc)
    status: dict = {
        "db_path": str(DB_PATH),
        "db_exists": DB_PATH.exists(),
        "now_utc": now.isoformat(timespec="seconds"),
        "pid": os.getpid(),
    }
    if not DB_PATH.exists():
        status["error"] = "DB が未生成 (ループが一度も起動していない可能性)"
        return status

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        # 最新判定
        row = conn.execute(
            "SELECT id, judged_at_utc, pair, llm_label, llm_confidence, accepted "
            "FROM llm_judgments ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            age = (now - parse_iso(row["judged_at_utc"])).total_seconds() / 60
            status["latest_judgment"] = {
                "id": row["id"],
                "judged_at": row["judged_at_utc"],
                "pair": row["pair"],
                "label": row["llm_label"],
                "confidence": row["llm_confidence"],
                "accepted": bool(row["accepted"]),
                "age_min": round(age, 1),
            }
        else:
            status["latest_judgment"] = None

        # 累計
        n_judgments = conn.execute(
            "SELECT COUNT(*) FROM llm_judgments"
        ).fetchone()[0]
        status["total_judgments"] = int(n_judgments)

        # 1h / 24h 件数
        since_1h = (now - timedelta(hours=1)).isoformat(timespec="seconds")
        since_24h = (now - timedelta(hours=24)).isoformat(timespec="seconds")
        n_1h = conn.execute(
            "SELECT COUNT(*) FROM llm_judgments WHERE judged_at_utc >= ?", (since_1h,),
        ).fetchone()[0]
        n_24h = conn.execute(
            "SELECT COUNT(*) FROM llm_judgments WHERE judged_at_utc >= ?", (since_24h,),
        ).fetchone()[0]
        status["judgments_1h"] = int(n_1h)
        status["judgments_24h"] = int(n_24h)

        # オープンポジション
        rows = conn.execute(
            "SELECT pair, direction, entry_price, llm_confidence, mt5_ticket "
            "FROM trades WHERE status='open' ORDER BY id"
        ).fetchall()
        status["open_positions"] = [
            {
                "pair": r["pair"], "direction": r["direction"],
                "entry": r["entry_price"], "confidence": r["llm_confidence"],
                "ticket": r["mt5_ticket"],
            }
            for r in rows
        ]

        # 最新ループヘルス
        row = conn.execute(
            "SELECT event_at_utc, event_type, message FROM loop_health "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            status["latest_health"] = {
                "event_at": row["event_at_utc"],
                "type": row["event_type"],
                "message": row["message"],
            }
        else:
            status["latest_health"] = None

        # 稼働時間: 最後の "start" イベントからの経過
        row = conn.execute(
            "SELECT event_at_utc FROM loop_health WHERE event_type='start' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            start_dt = parse_iso(row["event_at_utc"])
            status["uptime_hours"] = round(
                (now - start_dt).total_seconds() / 3600, 1,
            )
        else:
            status["uptime_hours"] = None
    finally:
        conn.close()

    return status


def is_alive(status: dict) -> bool:
    """判定が直近 ALIVE_THRESHOLD_MIN 分以内ならアライブ扱い"""
    j = status.get("latest_judgment")
    if not j:
        # 判定が一度もないと「未起動」扱い (撤退条件抵触ではない)
        return False
    age = j.get("age_min")
    if age is None:
        return False
    return age <= ALIVE_THRESHOLD_MIN


def format_status_text(status: dict, alive: bool) -> str:
    lines = [
        f"*SPEC v3 死活レポート* ({'ALIVE' if alive else 'WARN'})",
        f"PID: {status.get('pid')}",
        f"now_utc: {status['now_utc']}",
    ]
    j = status.get("latest_judgment")
    if j:
        lines.append(
            f"最新判定: pair={j['pair']} label={j['label']} "
            f"conf={j['confidence']} age={j['age_min']}m"
        )
    else:
        lines.append("最新判定: なし")
    lines.append(f"累計判定: {status.get('total_judgments', 0)} 件")
    lines.append(f"直近1h: {status.get('judgments_1h', 0)} / 24h: {status.get('judgments_24h', 0)}")
    if status.get("open_positions"):
        for op in status["open_positions"]:
            lines.append(
                f"open: {op['pair']} {op['direction']} @ {op['entry']:.5f} "
                f"ticket={op['ticket']} conf={op['confidence']}"
            )
    else:
        lines.append("open: 0 件")
    if status.get("uptime_hours") is not None:
        lines.append(f"稼働時間: {status['uptime_hours']} 時間")
    if "error" in status:
        lines.append(f":x: {status['error']}")
    return "\n".join(lines)


def post_slack(text: str, color: str) -> bool:
    import requests
    for env in (
        "SPEC_V3_SLACK_WEBHOOK_URL",
        "SLACK_ALERTS_WEBHOOK_URL",
        "SLACK_WEBHOOK_URL",
    ):
        url = os.environ.get(env, "").strip()
        if url:
            break
    else:
        logger.warning("Slack Webhook 未設定: stdout のみ")
        print(text)
        return False

    payload = {
        "attachments": [{
            "color": color,
            "text": text,
            "mrkdwn_in": ["text"],
        }],
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            return True
        logger.warning("Slack 送信失敗 HTTP %d: %s", resp.status_code, resp.text[:200])
    except Exception as e:  # noqa: BLE001
        logger.warning("Slack 送信エラー: %s", e)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet-when-alive", action="store_true",
                        help="ALIVE 時は Slack 通知しない (警告のみ)")
    args = parser.parse_args()

    status = gather_status()
    alive = is_alive(status)
    text = format_status_text(status, alive)
    print(text)

    if alive and args.quiet_when_alive:
        return 0

    color = "#2196F3" if alive else "#dc3545"
    post_slack(text, color)
    return 0


if __name__ == "__main__":
    sys.exit(main())
