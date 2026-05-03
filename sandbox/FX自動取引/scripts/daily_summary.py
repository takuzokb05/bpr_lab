"""
FX自動取引システム — 日次取引サマリスクリプト

前日（JST 00:00〜23:59）に決済された取引をSQLite `trades` テーブルから集計し、
MT5の口座情報と合わせてSlack #ai-daily に Block Kit形式で通知する。

土曜朝は過去7日分の週次サマリを追加で送信する。

実行例:
  python scripts/daily_summary.py                # 本番（前日集計＋Slack送信）
  python scripts/daily_summary.py --dry-run      # stdoutに集計結果のみ出力
  python scripts/daily_summary.py --force-weekly # 強制的に週次サマリを付与

タスクスケジューラ登録（VPS・JST 06:25 毎日）:
  schtasks /Create /TN "FX_DailySummary" ^
    /TR "cmd.exe /c cd /d C:\\bpr_lab\\fx_trading && C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python313\\python.exe scripts\\daily_summary.py >> data\\daily_summary_log.txt 2>&1" ^
    /SC DAILY /ST 06:25 /RU Administrator /RL HIGHEST /F
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows cp932環境でも Unicode 文字（•, 絵文字等）を stdout に出力できるようにする
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from typing import Any

# プロジェクトルートをsys.pathに追加
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

from dotenv import load_dotenv

# .env読み込み（FXプロジェクト用）
load_dotenv(_project_root / ".env")

from src.config import DB_PATH, SLACK_ALERTS_WEBHOOK_URL, SLACK_WEBHOOK_URL  # noqa: E402
from src.slack_notifier import (  # noqa: E402
    COLOR_BLUE,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_YELLOW,
)

logger = logging.getLogger(__name__)

# JSTタイムゾーン
JST = timezone(timedelta(hours=9))


# ============================================================
# データクラス
# ============================================================


@dataclass
class TradeStats:
    """取引統計サマリ"""

    period_label: str  # "前日" / "過去7日"
    period_start_jst: datetime
    period_end_jst: datetime
    trade_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    total_pl: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0
    by_instrument: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def win_rate(self) -> float:
        """勝率（%）。決着した取引がゼロなら0.0。"""
        decided = self.win_count + self.loss_count
        if decided == 0:
            return 0.0
        return self.win_count / decided * 100.0


# ============================================================
# 集計ロジック
# ============================================================


def fetch_ai_ab_trades(
    db_path: Path, start_jst: datetime, end_jst: datetime
) -> list[dict[str, Any]]:
    """指定期間内に決済された AI 判定付き trades を取得する（T5: A/B 用）。

    ai_decision IS NOT NULL でフィルタするため、AI フィルター適用前のデータは除外される。
    """
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        start_utc = start_jst.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        end_utc = end_jst.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        # 旧スキーマのDBでは ai_decision カラムが無いため、無ければ空配列を返す
        try:
            cur = conn.execute(
                """SELECT trade_id, instrument, pl, ai_decision, ai_confidence,
                          ai_direction, ai_regime, closed_at
                   FROM trades
                   WHERE status = 'closed' AND closed_at IS NOT NULL
                     AND closed_at >= ? AND closed_at < ?
                     AND ai_decision IS NOT NULL AND pl IS NOT NULL
                   ORDER BY closed_at ASC""",
                (start_utc, end_utc),
            )
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.OperationalError as e:
            logger.info("AI A/B 取得スキップ（カラム未追加の可能性）: %s", e)
            return []
    finally:
        conn.close()


def build_ai_ab_text(
    trades: list[dict[str, Any]], period_label: str
) -> str | None:
    """AI A/B 簡易サマリ（フィルター利用ありの取引について decision 別勝率）を返す。

    None を返した場合はセクション自体を非表示にする。
    """
    if not trades:
        return None

    by_decision: dict[str, dict[str, float]] = {}
    total_count = 0
    total_pl = 0.0
    total_wins = 0
    total_losses = 0

    for t in trades:
        pl = t.get("pl")
        if pl is None:
            continue
        pl = float(pl)
        decision = (t.get("ai_decision") or "UNKNOWN").upper()
        bucket = by_decision.setdefault(
            decision, {"count": 0, "wins": 0, "losses": 0, "pl": 0.0}
        )
        bucket["count"] += 1
        bucket["pl"] += pl
        if pl > 0:
            bucket["wins"] += 1
            total_wins += 1
        elif pl < 0:
            bucket["losses"] += 1
            total_losses += 1
        total_count += 1
        total_pl += pl

    if total_count == 0:
        return None

    decided = total_wins + total_losses
    overall_wr = (total_wins / decided * 100.0) if decided > 0 else 0.0
    sign = "+" if total_pl >= 0 else ""
    lines = [
        f"*AI A/B サマリ*（{period_label} / AI判定付き取引のみ）",
        f"• 全体: {total_count}回 (勝{total_wins}/負{total_losses}) "
        f"勝率 {overall_wr:.1f}% / 累計 {sign}{total_pl:,.0f} JPY",
    ]

    # NEUTRAL 除外比較
    excl_wins = sum(
        b["wins"] for d, b in by_decision.items() if d != "NEUTRAL"
    )
    excl_losses = sum(
        b["losses"] for d, b in by_decision.items() if d != "NEUTRAL"
    )
    excl_decided = excl_wins + excl_losses
    if excl_decided > 0 and excl_decided != decided:
        excl_wr = excl_wins / excl_decided * 100.0
        diff = excl_wr - overall_wr
        lines.append(
            f"• NEUTRAL除外: {excl_decided}回 勝率 {excl_wr:.1f}% "
            f"({diff:+.1f}pt)"
        )

    # decision 別
    lines.append("• decision 別:")
    for decision in sorted(by_decision.keys()):
        b = by_decision[decision]
        d_decided = b["wins"] + b["losses"]
        wr = (b["wins"] / d_decided * 100.0) if d_decided > 0 else 0.0
        s = "+" if b["pl"] >= 0 else ""
        lines.append(
            f"    - {decision}: {int(b['count'])}回 "
            f"(勝{int(b['wins'])}/負{int(b['losses'])}) "
            f"勝率 {wr:.1f}% / {s}{b['pl']:,.0f} JPY"
        )

    return "\n".join(lines)


def fetch_closed_trades(
    db_path: Path, start_jst: datetime, end_jst: datetime
) -> list[dict[str, Any]]:
    """指定期間内に決済された取引を取得する。

    opened_at / closed_at はISO形式文字列。MT5の注文コメント等で
    タイムゾーン指定がないケース（naive datetime）にも対応する。

    Args:
        db_path: SQLiteファイルのパス
        start_jst: 期間開始（JST aware）
        end_jst: 期間終了（JST aware、この時刻は含まない）

    Returns:
        取引行のリスト（カラム: trade_id, instrument, units, pl, opened_at, closed_at）
    """
    if not db_path.exists():
        logger.warning("DBファイルが存在しません: %s", db_path)
        return []

    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # closed_at を文字列比較するためISOフォーマット（秒まで）で渡す。
        # SQLite のISO8601は辞書順=時系列順になる特性を利用。
        # JST→UTCに揃えた上で naive ISO 文字列で比較する。
        start_utc_iso = start_jst.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        end_utc_iso = end_jst.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        cur.execute(
            """
            SELECT trade_id, instrument, units, open_price, close_price,
                   pl, opened_at, closed_at, status
            FROM trades
            WHERE status = 'closed'
              AND closed_at IS NOT NULL
              AND closed_at >= ?
              AND closed_at <  ?
            ORDER BY closed_at ASC
            """,
            (start_utc_iso, end_utc_iso),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def count_open_trades(db_path: Path) -> int:
    """現在オープン中のポジション数をDBから取得する。"""
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM trades WHERE status = 'open'")
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def aggregate_trades(
    trades: list[dict[str, Any]],
    period_label: str,
    start_jst: datetime,
    end_jst: datetime,
) -> TradeStats:
    """取引リストをTradeStatsに集計する。

    pl が None の行はスキップ（決済済みだが損益未記録のケース）。
    """
    stats = TradeStats(
        period_label=period_label,
        period_start_jst=start_jst,
        period_end_jst=end_jst,
    )

    for t in trades:
        pl = t.get("pl")
        if pl is None:
            # 損益が未記録の行はカウントせずログに残す
            logger.debug("pl未記録のためスキップ: trade_id=%s", t.get("trade_id"))
            continue

        pl = float(pl)
        stats.trade_count += 1
        stats.total_pl += pl

        if pl > 0:
            stats.win_count += 1
            if pl > stats.max_win:
                stats.max_win = pl
        elif pl < 0:
            stats.loss_count += 1
            if pl < stats.max_loss:
                stats.max_loss = pl
        # pl == 0 は勝ち負けどちらにも入れない

        # 通貨ペア別内訳
        inst = t.get("instrument") or "UNKNOWN"
        bucket = stats.by_instrument.setdefault(
            inst,
            {"count": 0, "wins": 0, "losses": 0, "pl": 0.0},
        )
        bucket["count"] += 1
        bucket["pl"] += pl
        if pl > 0:
            bucket["wins"] += 1
        elif pl < 0:
            bucket["losses"] += 1

    return stats


# ============================================================
# MT5 口座情報取得
# ============================================================


def fetch_account_info() -> dict[str, Any] | None:
    """MT5から現在の口座情報を取得する。

    失敗時は None を返し、Slack送信は口座情報なしで続行する。
    """
    try:
        from src.mt5_client import Mt5Client
    except Exception as e:
        logger.warning("Mt5Client import失敗: %s", e)
        return None

    try:
        with Mt5Client() as client:
            summary = client.get_account_summary()
            # 現在オープン中ポジションの含み損益
            try:
                positions = client.get_positions()
                summary["open_positions_detail"] = positions
            except Exception as e:
                logger.warning("MT5ポジション取得失敗: %s", e)
                summary["open_positions_detail"] = []
            return summary
    except Exception as e:
        logger.warning("MT5接続/情報取得失敗: %s", e)
        return None


# ============================================================
# Slack通知（Block Kit形式）
# ============================================================


def build_stats_text(stats: TradeStats) -> str:
    """TradeStatsを人間可読なMarkdownテキストに整形する。"""
    if stats.trade_count == 0:
        return (
            f"*{stats.period_label}*（"
            f"{stats.period_start_jst.strftime('%m/%d %H:%M')}〜"
            f"{stats.period_end_jst.strftime('%m/%d %H:%M')} JST）\n"
            f"> 決済された取引はありませんでした。"
        )

    pl_sign = "+" if stats.total_pl >= 0 else ""
    lines = [
        f"*{stats.period_label}サマリ*（"
        f"{stats.period_start_jst.strftime('%m/%d')}〜"
        f"{(stats.period_end_jst - timedelta(seconds=1)).strftime('%m/%d')} JST）",
        f"• 取引回数: *{stats.trade_count}回* "
        f"（勝 {stats.win_count} / 負 {stats.loss_count} / 勝率 {stats.win_rate:.1f}%）",
        f"• 累積損益: *{pl_sign}{stats.total_pl:,.0f} JPY*",
        f"• 最大勝ち: +{stats.max_win:,.0f} JPY / 最大負け: {stats.max_loss:,.0f} JPY",
    ]

    # 通貨ペア別内訳（2ペア以上あれば表示）
    if len(stats.by_instrument) >= 1:
        lines.append("• 通貨ペア別:")
        # 損益が大きい順
        sorted_items = sorted(
            stats.by_instrument.items(), key=lambda kv: kv[1]["pl"], reverse=True
        )
        for inst, b in sorted_items:
            sign = "+" if b["pl"] >= 0 else ""
            lines.append(
                f"    - {inst}: {b['count']}回 "
                f"(勝{b['wins']}/負{b['losses']}) {sign}{b['pl']:,.0f} JPY"
            )

    return "\n".join(lines)


def build_account_text(
    account: dict[str, Any] | None,
    prev_balance: float | None,
    open_count_db: int,
) -> str:
    """口座情報セクションを整形する。"""
    if account is None:
        return (
            "*口座状況*\n"
            "> MT5から口座情報を取得できませんでした（接続失敗）。"
        )

    balance = account.get("balance", 0.0)
    unrealized = account.get("unrealized_pl", 0.0)
    currency = account.get("currency", "JPY")
    open_count_mt5 = account.get("open_trade_count", 0)

    lines = [
        "*口座状況*",
        f"• 現在残高: *{balance:,.0f} {currency}*",
    ]

    if prev_balance is not None:
        diff = balance - prev_balance
        sign = "+" if diff >= 0 else ""
        pct = (diff / prev_balance * 100.0) if prev_balance != 0 else 0.0
        lines.append(f"• 前日比: {sign}{diff:,.0f} {currency} ({sign}{pct:.2f}%)")

    u_sign = "+" if unrealized >= 0 else ""
    lines.append(
        f"• オープンポジション: {open_count_mt5}件（DB: {open_count_db}件） "
        f"含み損益 {u_sign}{unrealized:,.0f} {currency}"
    )

    # ポジション詳細（最大5件）
    details = account.get("open_positions_detail", [])
    if details:
        for pos in details[:5]:
            direction = "BUY" if pos.get("units", 0) > 0 else "SELL"
            u_pl = pos.get("unrealized_pl", 0.0)
            sign = "+" if u_pl >= 0 else ""
            lines.append(
                f"    - {pos.get('instrument')} {direction} "
                f"{abs(pos.get('units', 0)):,} @ {pos.get('price_open', 0):.5f} "
                f"({sign}{u_pl:,.0f})"
            )

    return "\n".join(lines)


def pick_color(stats: TradeStats) -> str:
    """損益状況に応じた色を選択する。"""
    if stats.trade_count == 0:
        return COLOR_BLUE
    if stats.total_pl > 0:
        return COLOR_GREEN
    if stats.total_pl < 0:
        return COLOR_RED
    return COLOR_YELLOW


def post_to_slack(
    webhook_url: str,
    daily_stats: TradeStats,
    weekly_stats: TradeStats | None,
    account: dict[str, Any] | None,
    prev_balance: float | None,
    open_count_db: int,
    ai_ab_text: str | None = None,
    timeout: int = 10,
) -> bool:
    """集計結果をSlackに送信する。

    SlackNotifier.notify() をそのまま使うと色が一色しか指定できないため、
    attachments を複数束ねて直接POSTする。
    """
    import requests

    attachments: list[dict[str, Any]] = []

    # 日次サマリ
    attachments.append(
        {
            "color": pick_color(daily_stats),
            "text": build_stats_text(daily_stats),
            "mrkdwn_in": ["text"],
        }
    )

    # 週次サマリ（土曜のみ）
    if weekly_stats is not None:
        attachments.append(
            {
                "color": pick_color(weekly_stats),
                "text": build_stats_text(weekly_stats),
                "mrkdwn_in": ["text"],
            }
        )

    # AI A/B サマリ（直近30日）
    if ai_ab_text:
        attachments.append(
            {
                "color": COLOR_BLUE,
                "text": ai_ab_text,
                "mrkdwn_in": ["text"],
            }
        )

    # 口座情報
    attachments.append(
        {
            "color": COLOR_BLUE,
            "text": build_account_text(account, prev_balance, open_count_db),
            "mrkdwn_in": ["text"],
        }
    )

    payload = {
        "text": ":bar_chart: *FX自動取引 日次レポート*",
        "attachments": attachments,
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=timeout)
        if resp.status_code == 200:
            logger.info("Slack送信成功")
            return True
        logger.warning(
            "Slack送信失敗 (HTTP %d): %s", resp.status_code, resp.text[:200]
        )
        return False
    except requests.exceptions.Timeout:
        logger.warning("Slack送信タイムアウト (%ds)", timeout)
        return False
    except Exception as e:
        logger.warning("Slack送信中にエラー: %s", e)
        return False


# ============================================================
# Webhook選択
# ============================================================


def resolve_webhook_url() -> str:
    """Slack Webhook URLを優先順位で解決する。

    優先順: SLACK_DAILY_WEBHOOK_URL > SLACK_WEBHOOK_URL > SLACK_ALERTS_WEBHOOK_URL
    """
    daily = os.getenv("SLACK_DAILY_WEBHOOK_URL", "").strip()
    if daily:
        return daily
    if SLACK_WEBHOOK_URL:
        return SLACK_WEBHOOK_URL
    if SLACK_ALERTS_WEBHOOK_URL:
        return SLACK_ALERTS_WEBHOOK_URL
    return ""


# ============================================================
# 期間計算
# ============================================================


def compute_yesterday_range(now_jst: datetime) -> tuple[datetime, datetime]:
    """JSTの前日 00:00〜当日 00:00 の範囲を返す。"""
    today_0 = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_0 = today_0 - timedelta(days=1)
    return yesterday_0, today_0


def compute_week_range(now_jst: datetime) -> tuple[datetime, datetime]:
    """JSTの過去7日（前日を含む）の範囲を返す。"""
    today_0 = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    start = today_0 - timedelta(days=7)
    return start, today_0


def compute_month_range(now_jst: datetime) -> tuple[datetime, datetime]:
    """JSTの過去30日（前日を含む）の範囲を返す（T5: AI A/B 用）。"""
    today_0 = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    start = today_0 - timedelta(days=30)
    return start, today_0


# ============================================================
# メイン
# ============================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="FX日次取引サマリ（SQLite trades + MT5口座情報 → Slack）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Slack送信せず、集計結果をstdoutに出力するのみ",
    )
    parser.add_argument(
        "--force-weekly",
        action="store_true",
        help="曜日に関係なく週次サマリを追加する",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help=f"SQLite DBパス（デフォルト: {DB_PATH}）",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.info("=== 日次取引サマリ 開始 ===")
    logger.info("DB: %s", args.db)

    now_jst = datetime.now(JST)
    y_start, y_end = compute_yesterday_range(now_jst)
    logger.info(
        "集計期間（前日）: %s 〜 %s JST",
        y_start.strftime("%Y-%m-%d %H:%M"),
        y_end.strftime("%Y-%m-%d %H:%M"),
    )

    # 前日集計
    daily_trades = fetch_closed_trades(args.db, y_start, y_end)
    daily_stats = aggregate_trades(daily_trades, "前日", y_start, y_end)
    logger.info(
        "前日取引: count=%d, pl=%.0f, win=%d, loss=%d",
        daily_stats.trade_count,
        daily_stats.total_pl,
        daily_stats.win_count,
        daily_stats.loss_count,
    )

    # 週次集計（土曜 = weekday=5、または --force-weekly）
    weekly_stats: TradeStats | None = None
    is_saturday = now_jst.weekday() == 5
    if is_saturday or args.force_weekly:
        w_start, w_end = compute_week_range(now_jst)
        logger.info(
            "集計期間（週次）: %s 〜 %s JST",
            w_start.strftime("%Y-%m-%d"),
            w_end.strftime("%Y-%m-%d"),
        )
        weekly_trades = fetch_closed_trades(args.db, w_start, w_end)
        weekly_stats = aggregate_trades(weekly_trades, "過去7日", w_start, w_end)
        logger.info(
            "週次取引: count=%d, pl=%.0f",
            weekly_stats.trade_count,
            weekly_stats.total_pl,
        )

    # AI A/B サマリ（直近30日）
    m_start, m_end = compute_month_range(now_jst)
    ai_ab_trades = fetch_ai_ab_trades(args.db, m_start, m_end)
    ai_ab_text = build_ai_ab_text(ai_ab_trades, "直近30日")
    if ai_ab_text:
        logger.info("AI A/B 集計対象: %d 件", len(ai_ab_trades))
    else:
        logger.info("AI A/B: 対象データなし（カラム未追加 or 0件）")

    # 口座情報取得
    account = fetch_account_info()
    open_count_db = count_open_trades(args.db)

    # 前日残高推定: 現在残高 - 前日決済損益（概算）
    prev_balance: float | None = None
    if account is not None:
        prev_balance = account.get("balance", 0.0) - daily_stats.total_pl

    # stdoutに整形結果を出力（dry-run でも本番でも）
    logger.info("---- 日次サマリ ----")
    for line in build_stats_text(daily_stats).splitlines():
        logger.info(line)
    if weekly_stats is not None:
        logger.info("---- 週次サマリ ----")
        for line in build_stats_text(weekly_stats).splitlines():
            logger.info(line)
    if ai_ab_text:
        logger.info("---- AI A/B サマリ（直近30日）----")
        for line in ai_ab_text.splitlines():
            logger.info(line)
    logger.info("---- 口座状況 ----")
    for line in build_account_text(account, prev_balance, open_count_db).splitlines():
        logger.info(line)

    if args.dry_run:
        logger.info("--dry-run指定のためSlack送信はスキップします")
        logger.info("=== 日次取引サマリ 完了（dry-run） ===")
        return 0

    # Slack送信
    webhook_url = resolve_webhook_url()
    if not webhook_url:
        logger.warning(
            "Slack Webhook URLが未設定のため送信をスキップします "
            "(SLACK_DAILY_WEBHOOK_URL / SLACK_WEBHOOK_URL / SLACK_ALERTS_WEBHOOK_URL)"
        )
        return 0

    ok = post_to_slack(
        webhook_url=webhook_url,
        daily_stats=daily_stats,
        weekly_stats=weekly_stats,
        account=account,
        prev_balance=prev_balance,
        open_count_db=open_count_db,
        ai_ab_text=ai_ab_text,
    )

    logger.info("=== 日次取引サマリ 完了 ===")
    return 0 if ok else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logging.exception("致命的エラー: %s", e)
        sys.exit(1)
