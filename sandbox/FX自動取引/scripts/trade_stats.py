"""取引統計ダンプ（勝敗・合計P/L・ペア別）

--reconcile オプション: MT5 history_deals から実PLをDBに書き戻し。
broker_only取り込みで pl=0.0 になった trade を正確な値に修正する。
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--reconcile", action="store_true",
                    help="MT5 history_deals から実PLをDBに書き戻す")
parser.add_argument("--hours", type=int, default=72,
                    help="reconcile対象の過去時間（デフォルト72h）")
args = parser.parse_args()

DB = Path(__file__).resolve().parent.parent / "data" / "fx_trading.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()


def reconcile_from_mt5(hours: int) -> int:
    """MT5 deal history から実PL/close_priceをDBに反映。

    - status=open かつ broker側で決済済み → status=closed, 実PLで更新
    - pl=0.0 で closed になっているレコードも実PLで上書き
    - DBに存在しない position も新規INSERT

    Returns:
        更新件数
    """
    import MetaTrader5 as mt5
    if not mt5.initialize():
        print(f"MT5初期化失敗: {mt5.last_error()}")
        return 0

    to_date = datetime.now()
    from_date = to_date - timedelta(hours=hours)
    deals = mt5.history_deals_get(from_date, to_date) or []

    # position_id ごとに集約
    pos_data: dict[int, dict] = {}
    for d in deals:
        pid = d.position_id
        if pid not in pos_data:
            pos_data[pid] = {
                "symbol": d.symbol,
                "deals": [],
                "total_pl": 0.0,
            }
        pos_data[pid]["deals"].append(d)
        pos_data[pid]["total_pl"] += d.profit
    mt5.shutdown()

    updated = 0
    inserted = 0
    for pid, info in pos_data.items():
        deals_sorted = sorted(info["deals"], key=lambda x: x.time)
        entry_deal = next(
            (d for d in deals_sorted if d.entry == 0), deals_sorted[0]
        )
        exit_deals = [d for d in deals_sorted if d.entry == 1]
        # 完全にクローズしたもののみ対象
        if not exit_deals:
            continue
        last_exit = exit_deals[-1]

        close_price = last_exit.price
        closed_at = datetime.fromtimestamp(
            last_exit.time, tz=timezone.utc
        ).isoformat()
        pl = info["total_pl"]

        cur.execute(
            "SELECT id, status, pl FROM trades WHERE trade_id=?",
            (str(pid),),
        )
        row = cur.fetchone()
        if row is None:
            # DB未記録 → INSERT
            units = int(entry_deal.volume * 100_000)
            if entry_deal.type == 1:
                units = -units
            # シンボルから通貨ペア形式へ
            symbol = info["symbol"].rstrip("-")
            pair = symbol[:3] + "_" + symbol[3:]
            opened_at = datetime.fromtimestamp(
                entry_deal.time, tz=timezone.utc
            ).isoformat()
            cur.execute(
                """INSERT INTO trades
                   (trade_id, instrument, units, open_price, close_price,
                    pl, opened_at, closed_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'closed')""",
                (str(pid), pair, units, entry_deal.price, close_price,
                 pl, opened_at, closed_at),
            )
            inserted += 1
        else:
            db_id, db_status, db_pl = row
            # status open → closed へ、または pl=0 を実値に上書き
            if db_status != "closed" or (db_pl == 0.0 and pl != 0.0):
                cur.execute(
                    """UPDATE trades
                       SET close_price=?, pl=?, closed_at=?, status='closed'
                       WHERE id=?""",
                    (close_price, pl, closed_at, db_id),
                )
                updated += 1

    conn.commit()
    print(f"reconcile完了: 更新={updated}件 新規INSERT={inserted}件")
    return updated + inserted


if args.reconcile:
    reconcile_from_mt5(args.hours)
    print()

# テーブル一覧
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print(f"tables: {tables}")

if "trades" in tables:
    cur.execute("SELECT COUNT(*) FROM trades")
    print(f"total trades: {cur.fetchone()[0]}")

    # カラム一覧
    cur.execute("PRAGMA table_info(trades)")
    cols = [r[1] for r in cur.fetchall()]
    print(f"columns: {cols}")

    # ペア別サマリ（クローズ済みのみ）
    cur.execute(
        "SELECT instrument, COUNT(*), "
        "SUM(CASE WHEN pl > 0 THEN 1 ELSE 0 END), "
        "SUM(pl) "
        "FROM trades WHERE status = 'closed' "
        "GROUP BY instrument"
    )
    print("\n[closed trades by pair]")
    print(f"{'pair':12s} {'n':>3s} {'wins':>5s} {'sum_pl':>10s}")
    rows = cur.fetchall()
    total_n = total_w = 0
    total_pl = 0.0
    for r in rows:
        print(f"{r[0]:12s} {r[1]:>3d} {r[2]:>5d} {r[3]:>10.2f}")
        total_n += r[1]
        total_w += r[2]
        total_pl += r[3] or 0
    if total_n:
        print(f"{'TOTAL':12s} {total_n:>3d} {total_w:>5d} {total_pl:>10.2f}"
              f"  (win_rate={total_w/total_n*100:.1f}%)")

    # ステータス別
    cur.execute(
        "SELECT status, COUNT(*) FROM trades GROUP BY status"
    )
    print("\n[by status]")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")

    # 直近10件
    cur.execute(
        "SELECT instrument, units, open_price, close_price, "
        "pl, status, opened_at, closed_at "
        "FROM trades ORDER BY opened_at DESC LIMIT 10"
    )
    print("\n[recent 10]")
    for r in cur.fetchall():
        side = "BUY" if r[1] > 0 else "SELL"
        print(f"  {r[0]:8s} {side:4s} units={r[1]:+6d} "
              f"open={r[2]} close={r[3]} pl={r[4]} "
              f"status={r[5]} opened={r[6]}")
conn.close()
