"""
FX自動取引システム — AI A/B 集計スクリプト (T5)

`trades` テーブルの closed 行を ai_decision / direction / confidence ビン別に集計し、
- CSV: data/ai_ab_summary.csv
- Markdown レポート: stdout または --output 指定先
- （オプション）Slack に Markdown レポートを通知

として出力する。

集計内容:
  1. ai_decision 別: count / win / loss / win_rate / total_pl / avg_pl / 95%CI
  2. ai_confidence ビン別 (0.0-0.5, 0.5-0.7, 0.7-0.9, 0.9-1.0): 同上
  3. ai_direction 別 (bullish / bearish / neutral): 同上
  4. AI=NEUTRALを除外した場合の勝率比較

使い方:
  python scripts/analyze_ai_ab.py
  python scripts/analyze_ai_ab.py --since 2026-04-01 --until 2026-05-01
  python scripts/analyze_ai_ab.py --csv data/ai_ab_summary.csv --output reports/ai_ab.md
  python scripts/analyze_ai_ab.py --slack
"""
from __future__ import annotations

import argparse
import csv
import logging
import math
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

# プロジェクトルートを sys.path に追加
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

# Windows cp932 環境向け
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_project_root / ".env")

from src.config import DB_PATH, SLACK_ALERTS_WEBHOOK_URL, SLACK_WEBHOOK_URL  # noqa: E402

logger = logging.getLogger(__name__)

# 信頼度ビン: (label, lower_inclusive, upper_exclusive_or_inclusive_top)
# 上限 1.0 だけ inclusive（confidence==1.0 のサンプルが落ちないように）
CONFIDENCE_BINS: list[tuple[str, float, float]] = [
    ("0.0-0.5", 0.0, 0.5),
    ("0.5-0.7", 0.5, 0.7),
    ("0.7-0.9", 0.7, 0.9),
    ("0.9-1.0", 0.9, 1.0001),
]


# ============================================================
# 集計データクラス
# ============================================================


@dataclass
class GroupStats:
    """1グループ（decision, bin, direction など）の統計値。"""

    label: str
    count: int = 0
    wins: int = 0
    losses: int = 0
    total_pl: float = 0.0
    pls: list[float] = field(default_factory=list)

    @property
    def decided(self) -> int:
        return self.wins + self.losses

    @property
    def win_rate(self) -> float:
        return (self.wins / self.decided * 100.0) if self.decided > 0 else 0.0

    @property
    def avg_pl(self) -> float:
        return (self.total_pl / self.count) if self.count > 0 else 0.0

    def win_rate_ci95(self) -> tuple[float, float]:
        """勝率の 95% Wilson 信頼区間（%）。

        通常の正規近似は小サンプルで両端が崩れるため、
        二項分布に対して安定な Wilson スコア区間を採用する。
        """
        n = self.decided
        if n == 0:
            return (0.0, 0.0)
        p = self.wins / n
        z = 1.96
        denom = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denom
        margin = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        low = max(0.0, center - margin) * 100.0
        high = min(1.0, center + margin) * 100.0
        return (low, high)

    def add(self, pl: float) -> None:
        self.count += 1
        self.total_pl += pl
        self.pls.append(pl)
        if pl > 0:
            self.wins += 1
        elif pl < 0:
            self.losses += 1
        # pl == 0 はカウントするが win/loss どちらにも入れない


# ============================================================
# DB 読み込み
# ============================================================


def fetch_trades(
    db_path: Path,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    """closed_at が since〜until の範囲、AIフィルター適用済みの trades を取得する。

    ai_decision IS NOT NULL でフィルタするため、AI 適用前の旧データは自動的に除外される。
    """
    if not db_path.exists():
        logger.warning("DBファイルが存在しません: %s", db_path)
        return []

    sql = (
        "SELECT trade_id, instrument, units, open_price, close_price, pl, "
        "opened_at, closed_at, ai_decision, ai_confidence, ai_reasons, "
        "ai_direction, ai_regime "
        "FROM trades "
        "WHERE status = 'closed' AND ai_decision IS NOT NULL AND pl IS NOT NULL"
    )
    params: list[Any] = []
    if since is not None:
        sql += " AND closed_at >= ?"
        params.append(since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
    if until is not None:
        sql += " AND closed_at <  ?"
        params.append(until.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
    sql += " ORDER BY closed_at ASC"

    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


# ============================================================
# 集計ロジック
# ============================================================


def _confidence_bin_label(conf: Optional[float]) -> Optional[str]:
    if conf is None:
        return None
    for label, low, high in CONFIDENCE_BINS:
        if low <= conf < high:
            return label
    # 範囲外（負やNaN）は None を返してスキップ扱い
    return None


def aggregate(
    trades: Iterable[dict[str, Any]],
) -> dict[str, dict[str, GroupStats]]:
    """
    集計結果を返す。

    Returns:
        {
            "by_decision":   {"CONFIRM": GroupStats, ...},
            "by_confidence": {"0.0-0.5": GroupStats, ...},
            "by_direction":  {"bullish": GroupStats, ...},
            "compare":       {"all": GroupStats, "exclude_neutral": GroupStats},
        }
    """
    by_decision: dict[str, GroupStats] = {}
    by_confidence: dict[str, GroupStats] = {}
    by_direction: dict[str, GroupStats] = {}
    all_stats = GroupStats(label="all")
    excl_neutral = GroupStats(label="exclude_neutral")

    for t in trades:
        pl = t.get("pl")
        if pl is None:
            continue
        pl = float(pl)
        decision = (t.get("ai_decision") or "UNKNOWN").upper()
        direction = (t.get("ai_direction") or "unknown").lower()
        conf = t.get("ai_confidence")

        by_decision.setdefault(decision, GroupStats(label=decision)).add(pl)
        by_direction.setdefault(direction, GroupStats(label=direction)).add(pl)
        bin_label = _confidence_bin_label(
            float(conf) if conf is not None else None
        )
        if bin_label is not None:
            by_confidence.setdefault(
                bin_label, GroupStats(label=bin_label)
            ).add(pl)

        all_stats.add(pl)
        if decision != "NEUTRAL":
            excl_neutral.add(pl)

    return {
        "by_decision": by_decision,
        "by_confidence": by_confidence,
        "by_direction": by_direction,
        "compare": {"all": all_stats, "exclude_neutral": excl_neutral},
    }


# ============================================================
# 出力
# ============================================================


def _row(stats: GroupStats) -> dict[str, Any]:
    low, high = stats.win_rate_ci95()
    return {
        "label": stats.label,
        "count": stats.count,
        "wins": stats.wins,
        "losses": stats.losses,
        "win_rate_pct": round(stats.win_rate, 2),
        "win_rate_ci95_low": round(low, 2),
        "win_rate_ci95_high": round(high, 2),
        "total_pl": round(stats.total_pl, 2),
        "avg_pl": round(stats.avg_pl, 2),
    }


def write_csv(out: Path, agg: dict[str, dict[str, GroupStats]]) -> None:
    """全集計結果を1つのCSVにダンプする。"""
    out.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for axis_name, groups in agg.items():
        for label, stats in groups.items():
            row = _row(stats)
            row["axis"] = axis_name
            row["label"] = label
            rows.append(row)

    if not rows:
        logger.warning("集計対象データが0件のためCSVを書きませんでした")
        return

    fieldnames = [
        "axis", "label", "count", "wins", "losses",
        "win_rate_pct", "win_rate_ci95_low", "win_rate_ci95_high",
        "total_pl", "avg_pl",
    ]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("CSV書き出し: %s (%d行)", out, len(rows))


def _format_section(title: str, groups: dict[str, GroupStats]) -> str:
    if not groups:
        return f"### {title}\n\n(該当データなし)\n"
    lines = [f"### {title}", "", "| ラベル | 件数 | 勝 | 負 | 勝率 | 95%CI | 累計PL | 平均PL |", "|---|---:|---:|---:|---:|---|---:|---:|"]
    # ラベル昇順で安定順序にする
    for label in sorted(groups.keys()):
        s = groups[label]
        low, high = s.win_rate_ci95()
        lines.append(
            f"| {label} | {s.count} | {s.wins} | {s.losses} | "
            f"{s.win_rate:.1f}% | [{low:.1f}, {high:.1f}] | "
            f"{s.total_pl:+,.0f} | {s.avg_pl:+,.1f} |"
        )
    return "\n".join(lines) + "\n"


def build_report(
    agg: dict[str, dict[str, GroupStats]],
    period_label: str,
    total_trades: int,
) -> str:
    """Markdown レポートを生成する。"""
    cmp_all = agg["compare"]["all"]
    cmp_excl = agg["compare"]["exclude_neutral"]

    lines = [
        f"# AI A/B サマリ — {period_label}",
        "",
        f"対象: ai_decision IS NOT NULL の closed trades = {total_trades} 件",
        "",
    ]

    lines.append(_format_section("decision 別", agg["by_decision"]))
    lines.append(_format_section("ai_confidence ビン別", agg["by_confidence"]))
    lines.append(_format_section("ai_direction 別", agg["by_direction"]))

    lines.append("### 比較: NEUTRAL 除外時の勝率変化")
    lines.append("")
    if cmp_all.decided == 0:
        lines.append("(決着済み取引なし)")
    else:
        a_low, a_high = cmp_all.win_rate_ci95()
        e_low, e_high = cmp_excl.win_rate_ci95()
        diff = cmp_excl.win_rate - cmp_all.win_rate
        lines.append(
            f"- 全件: {cmp_all.decided}件、勝率 {cmp_all.win_rate:.1f}% "
            f"(95%CI [{a_low:.1f}, {a_high:.1f}])、累計PL {cmp_all.total_pl:+,.0f}"
        )
        lines.append(
            f"- NEUTRAL 除外: {cmp_excl.decided}件、勝率 {cmp_excl.win_rate:.1f}% "
            f"(95%CI [{e_low:.1f}, {e_high:.1f}])、累計PL {cmp_excl.total_pl:+,.0f}"
        )
        lines.append(f"- 差分: {diff:+.1f} ポイント")
    lines.append("")
    return "\n".join(lines)


# ============================================================
# Slack 通知
# ============================================================


def post_to_slack(webhook_url: str, markdown: str, timeout: int = 10) -> bool:
    """Markdown レポートを Slack に投稿する。"""
    import requests

    payload = {
        "text": ":bar_chart: *AI A/B サマリ*",
        "attachments": [
            {"color": "#3D7EAB", "text": markdown, "mrkdwn_in": ["text"]}
        ],
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=timeout)
        if resp.status_code == 200:
            return True
        logger.warning("Slack送信失敗 HTTP %d: %s", resp.status_code, resp.text[:200])
        return False
    except Exception as e:
        logger.warning("Slack送信エラー: %s", e)
        return False


def resolve_webhook_url() -> str:
    """T5 用に SLACK_AI_AB_WEBHOOK_URL を優先する。"""
    explicit = os.getenv("SLACK_AI_AB_WEBHOOK_URL", "").strip()
    if explicit:
        return explicit
    daily = os.getenv("SLACK_DAILY_WEBHOOK_URL", "").strip()
    if daily:
        return daily
    if SLACK_WEBHOOK_URL:
        return SLACK_WEBHOOK_URL
    if SLACK_ALERTS_WEBHOOK_URL:
        return SLACK_ALERTS_WEBHOOK_URL
    return ""


# ============================================================
# メイン
# ============================================================


def _parse_date(s: str) -> datetime:
    """YYYY-MM-DD 形式を JST 0:00 として解釈し UTC aware datetime に変換する。"""
    jst = timezone(timedelta(hours=9))
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=jst)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI A/B 集計（trades テーブルを ai_decision 別に集計）"
    )
    parser.add_argument(
        "--db", type=Path, default=DB_PATH, help=f"SQLite DBパス（デフォルト: {DB_PATH}）"
    )
    parser.add_argument("--since", type=str, default=None, help="開始日 (YYYY-MM-DD JST)")
    parser.add_argument("--until", type=str, default=None, help="終了日 (YYYY-MM-DD JST)")
    parser.add_argument(
        "--csv",
        type=Path,
        default=_project_root / "data" / "ai_ab_summary.csv",
        help="CSV 出力先",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Markdown レポート出力先（未指定時は stdout のみ）",
    )
    parser.add_argument(
        "--slack",
        action="store_true",
        help="Markdown レポートを Slack にも投稿する",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    since = _parse_date(args.since) if args.since else None
    until = _parse_date(args.until) if args.until else None

    period_label = "全期間"
    if since or until:
        period_label = (
            f"{since.strftime('%Y-%m-%d') if since else '...'} 〜 "
            f"{until.strftime('%Y-%m-%d') if until else '...'} JST"
        )

    logger.info("=== AI A/B 集計開始 ===")
    logger.info("DB: %s, 期間: %s", args.db, period_label)

    trades = fetch_trades(args.db, since=since, until=until)
    logger.info("対象trades: %d 件 (ai_decision 付与済みのみ)", len(trades))

    agg = aggregate(trades)
    write_csv(args.csv, agg)

    report = build_report(agg, period_label, len(trades))
    print(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        logger.info("Markdown 出力: %s", args.output)

    if args.slack:
        webhook = resolve_webhook_url()
        if not webhook:
            logger.warning(
                "Slack Webhook URLが未設定のため送信スキップ "
                "(SLACK_AI_AB_WEBHOOK_URL / SLACK_DAILY_WEBHOOK_URL / SLACK_WEBHOOK_URL / SLACK_ALERTS_WEBHOOK_URL)"
            )
        else:
            ok = post_to_slack(webhook, report)
            logger.info("Slack送信: %s", "OK" if ok else "FAIL")

    logger.info("=== AI A/B 集計完了 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
