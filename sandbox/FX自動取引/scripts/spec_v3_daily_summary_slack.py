"""SPEC v3 日次サマリ Slack 通知 (JST 07:00 タスクスケジューラ起動)

直近 24 時間 (UTC) の集計を Slack に投稿:
- LLM 判定分布 (CONFIRM/NEUTRAL/CONTRADICT/REJECT/API_ERROR)
- ペア別 trades / win_rate / PF / PnL
- ローリング 30 日 PF
- LLM API 月コスト累計
- 撤退条件チェック結果

タスクスケジューラ登録:
- Trigger: Daily at JST 07:00
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

from src.spec_v3 import CONFIDENCE_THRESHOLDS, ENABLED_PAIRS  # noqa: E402
from src.spec_v3 import db as v3_db  # noqa: E402
from src.spec_v3.risk_manager import (  # noqa: E402
    DEFAULT_PRINCIPAL_JPY, KillSwitchState, run_all_safety_checks,
)

DB_PATH = ROOT / "data" / "fx_spec_v3.db"

logger = logging.getLogger("spec_v3_daily")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def _auc(outcomes: list) -> Optional[float]:
    """(score, label) リストから ROC-AUC を計算 (numpy 非依存、Mann-Whitney U)。

    label=1(win)/0(loss)。0.5=判別力なし、1.0=完全分離。
    pos/neg どちらか空なら None。採用群 n は小さいため O(n^2) で十分。
    confidence が勝敗を分離するかの計器 (feedback_confidence_auc_not_pf)。
    """
    pos = [s for s, l in outcomes if l == 1]
    neg = [s for s, l in outcomes if l == 0]
    if not pos or not neg:
        return None
    u = 0.0
    for ps in pos:
        for ns in neg:
            if ps > ns:
                u += 1.0
            elif ps == ns:
                u += 0.5
    return u / (len(pos) * len(neg))


def collect_summary(hours: int = 24) -> dict:
    """直近 hours 時間の集計"""
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)
    since_iso = since.isoformat(timespec="seconds")

    summary: dict = {
        "range_start_utc": since_iso,
        "range_end_utc": now.isoformat(timespec="seconds"),
        "date_jst": (now.astimezone(timezone(timedelta(hours=9)))).strftime("%Y-%m-%d"),
    }

    if not DB_PATH.exists():
        summary["error"] = f"DB が未生成: {DB_PATH}"
        return summary

    # 判定分布
    dist = v3_db.count_judgments_since(DB_PATH, since_iso)
    summary["llm_label_distribution"] = dist["by_label"]
    summary["llm_judgments_total"] = dist["total"]

    # ペア別 trade パフォーマンス
    per_pair: dict = {}
    with v3_db.get_conn(DB_PATH) as conn:
        for pair in ENABLED_PAIRS:
            cur = conn.execute(
                """
                SELECT c.pnl_pips, c.pnl_jpy
                FROM trade_closures c
                JOIN trades t ON t.id = c.trade_id
                WHERE t.pair = ? AND c.exit_at_utc >= ?
                """,
                (pair, since_iso),
            )
            rows = cur.fetchall()
            n = len(rows)
            wins = [r["pnl_pips"] for r in rows if r["pnl_pips"] is not None and r["pnl_pips"] > 0]
            losses = [r["pnl_pips"] for r in rows if r["pnl_pips"] is not None and r["pnl_pips"] < 0]
            pnl_jpy = sum((r["pnl_jpy"] or 0.0) for r in rows)
            win_sum = sum(wins)
            loss_sum = -sum(losses)
            if loss_sum > 0:
                pf = win_sum / loss_sum
            elif win_sum > 0:
                pf = float("inf")
            else:
                pf = 0.0
            per_pair[pair] = {
                "n_closed": n,
                "win_rate": (len(wins) / n) if n else 0.0,
                "pf": pf if pf != float("inf") else 99.99,
                "pnl_jpy": pnl_jpy,
            }
    summary["per_pair"] = per_pair

    # ローリング 30 日 PF
    rolling: dict = {}
    for pair in ENABLED_PAIRS:
        rolling[pair] = v3_db.recent_pf(DB_PATH, pair, n_trades=100)
    summary["rolling_30d_pf"] = rolling

    # LLM 月コスト
    cost = v3_db.llm_cost_in_month(DB_PATH)
    summary["llm_cost_usd"] = cost["cost_usd"]
    summary["llm_cost_n_calls"] = cost["n_calls"]
    summary["llm_cost_ym"] = cost["ym"]

    # 撤退条件チェック
    ks = KillSwitchState()
    safety = run_all_safety_checks(DB_PATH, ENABLED_PAIRS, ks, DEFAULT_PRINCIPAL_JPY)
    summary["retreat_action"] = safety["action"]
    summary["daily_pnl_jpy"] = safety["daily"]["pnl_jpy"]
    summary["monthly_pnl_jpy"] = safety["monthly"]["pnl_jpy"]

    # confidence 判別力 (採用群 CONFIRM の AUC、累計) — feedback_confidence_auc_not_pf
    # Phase 2'B 判定で AUC>=0.55 を gate にするための実測値。デモ初期は n 不足で N/A。
    conf_auc: dict = {}
    for pair in ENABLED_PAIRS:
        outcomes = v3_db.confirm_confidence_outcomes(DB_PATH, pair)
        conf_auc[pair] = {"auc": _auc(outcomes), "n": len(outcomes)}
    summary["confidence_auc"] = conf_auc

    return summary


def format_text(s: dict) -> str:
    lines = [f"*SPEC v3 Daily Summary — {s.get('date_jst', '')}*"]
    if "error" in s:
        lines.append(f":x: {s['error']}")
        return "\n".join(lines)

    # ペア別
    for pair, st in s.get("per_pair", {}).items():
        pf_s = f"{st['pf']:.2f}" if st['pf'] < 99 else "inf"
        lines.append(
            f"`{pair}` (conf>={CONFIDENCE_THRESHOLDS.get(pair, 0):.2f}): "
            f"trades={st['n_closed']} win_rate={st['win_rate']:.0%} "
            f"PF={pf_s} PnL={st['pnl_jpy']:+,.0f} JPY"
        )

    # LLM 判定分布
    dist = s.get("llm_label_distribution", {})
    if dist:
        lines.append("LLM 判定分布: " + " ".join(f"{k}={v}" for k, v in dist.items()))
        total = s.get("llm_judgments_total", 0)
        cr = dist.get("CONFIRM", 0) / total if total else 0.0
        flag = " :warning: 異常(90%+連続なら手動停止検討)" if cr >= 0.90 else ""
        lines.append(f"CONFIRM率: {cr:.0%}{flag}")
    lines.append(f"LLM 判定累計 (24h): {s.get('llm_judgments_total', 0)} 件")

    # ローリング PF
    rolling = s.get("rolling_30d_pf", {})
    if rolling:
        lines.append("Rolling 100-trades PF: " + " ".join(
            f"{p}={v:.2f}" if v is not None else f"{p}=N/A"
            for p, v in rolling.items()
        ))

    # confidence 判別力 AUC (採用群累計) — AUC≈0.5 は confidence が信号にならず (要 Phase 2'B 判定)
    ca = s.get("confidence_auc", {})
    if ca:
        parts = []
        for p, v in ca.items():
            if v["auc"] is not None and v["n"] >= 20:
                parts.append(f"{p}={v['auc']:.2f}(n={v['n']})")
            else:
                parts.append(f"{p}=N/A(n={v['n']})")
        lines.append("confidence判別力 AUC(採用群累計): " + " ".join(parts) + " ※0.5付近=判別力なし")

    # コスト
    cost_usd = s.get("llm_cost_usd")
    if cost_usd is not None:
        lines.append(
            f"LLM コスト ({s.get('llm_cost_ym')}): ${cost_usd:.3f} "
            f"(≒ ¥{cost_usd * 150:.0f}) calls={s.get('llm_cost_n_calls', 0)}"
        )

    # PnL
    lines.append(f"Daily PnL: {s.get('daily_pnl_jpy', 0):+,.0f} JPY")
    lines.append(f"Monthly PnL: {s.get('monthly_pnl_jpy', 0):+,.0f} JPY")

    # 撤退条件
    lines.append(f"Retreat status: `{s.get('retreat_action', 'ok')}`")

    return "\n".join(lines)


def post_slack(text: str) -> bool:
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
        logger.warning("Slack Webhook 未設定")
        print(text)
        return False

    payload = {
        "attachments": [{
            "color": "#2196F3",
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
    parser.add_argument("--hours", type=int, default=24, help="集計期間 (時間)")
    parser.add_argument("--print-only", action="store_true",
                        help="Slack 送信せず stdout 出力のみ")
    args = parser.parse_args()

    summary = collect_summary(hours=args.hours)
    text = format_text(summary)
    print(text)

    if not args.print_only:
        post_slack(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
