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
# 死活判定はハートビート (loop_health、約1時間ごと) 基準。
# 旧実装は「直近10分以内に LLM 判定があるか」基準だったが、判定はシグナル発生時
# しか記録されない (実測平均 17 分に 1 件) ため、稼働中でも WARN が頻発して
# オオカミ少年化し、2026-06-09 の本当の停止 (撤退発火) が 2 日間埋もれた。
HEARTBEAT_THRESHOLD_MIN = 75

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
        last_start_iso = row["event_at_utc"] if row else None
        if row:
            start_dt = parse_iso(row["event_at_utc"])
            status["uptime_hours"] = round(
                (now - start_dt).total_seconds() / 3600, 1,
            )
        else:
            status["uptime_hours"] = None

        # 停止検知: 最後の start より後に stop イベントがあれば「停止中」
        row = conn.execute(
            "SELECT event_at_utc, message FROM loop_health WHERE event_type='stop' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
        status["stopped"] = False
        if row and (last_start_iso is None or row["event_at_utc"] > last_start_iso):
            status["stopped"] = True
            status["stop_at"] = row["event_at_utc"]
            status["stop_age_hours"] = round(
                (now - parse_iso(row["event_at_utc"])).total_seconds() / 3600, 1,
            )
            # 停止理由 (retreat 等) も拾う
            reason_row = conn.execute(
                "SELECT event_type, message FROM loop_health "
                "WHERE event_type IN ('retreat', 'kill_switch', 'error') "
                "AND event_at_utc >= ? ORDER BY id DESC LIMIT 1",
                ((parse_iso(row["event_at_utc"]) - timedelta(minutes=5)).isoformat(timespec="seconds"),),
            ).fetchone()
            status["stop_reason"] = (
                f"{reason_row['event_type']}: {reason_row['message']}"
                if reason_row else row["message"]
            )

        # ハートビート鮮度 (start/heartbeat/stop いずれでも最新の loop_health)
        row = conn.execute(
            "SELECT event_at_utc FROM loop_health ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            status["heartbeat_age_min"] = round(
                (now - parse_iso(row["event_at_utc"])).total_seconds() / 60, 1,
            )
        else:
            status["heartbeat_age_min"] = None
    finally:
        conn.close()

    return status


def is_alive(status: dict) -> bool:
    """ハートビート (loop_health) が直近 HEARTBEAT_THRESHOLD_MIN 分以内なら稼働中。

    LLM 判定はシグナル発生時しか記録されず夜間は数時間空くため、
    判定鮮度を死活判定に使わない (旧実装のオオカミ少年化対策)。
    """
    if status.get("stopped"):
        return False
    age = status.get("heartbeat_age_min")
    if age is None:
        return False
    return age <= HEARTBEAT_THRESHOLD_MIN


def format_status_text(status: dict, alive: bool) -> str:
    if status.get("stopped"):
        header = ":rotating_light: *SPEC v3 ループ停止中* (STOPPED)"
    elif alive:
        header = "*SPEC v3 死活レポート* (ALIVE)"
    else:
        header = ":warning: *SPEC v3 死活レポート* (WARN: ハートビート途絶)"
    lines = [
        header,
        f"PID: {status.get('pid')}",
        f"now_utc: {status['now_utc']}",
    ]
    if status.get("stopped"):
        lines.append(
            f"停止時刻: {status.get('stop_at')} ({status.get('stop_age_hours')} 時間前)"
        )
        lines.append(f"停止理由: {status.get('stop_reason')}")
    if status.get("heartbeat_age_min") is not None:
        lines.append(f"最終ハートビート: {status['heartbeat_age_min']} 分前")
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
