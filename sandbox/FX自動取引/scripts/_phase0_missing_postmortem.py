"""決済済みなのに postmortem がない trade_id を抽出する診断スクリプト。"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fx_trading.db"


def main() -> None:
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    # trades のスキーマ確認
    cur.execute("PRAGMA table_info(trades)")
    cols = [r[1] for r in cur.fetchall()]
    print("trades columns:", cols)
    print()

    # 決済済み (closed_at IS NOT NULL) trades
    cur.execute(
        "SELECT trade_id, instrument, opened_at, closed_at, pl "
        "FROM trades WHERE closed_at IS NOT NULL "
        "ORDER BY closed_at DESC"
    )
    closed = cur.fetchall()
    print(f"決済済みtrades: {len(closed)}")

    # postmortem ある trade_id
    cur.execute("SELECT trade_id FROM trade_postmortems")
    pm_ids = {r[0] for r in cur.fetchall()}
    print(f"postmortemあり: {len(pm_ids)}")

    print()
    print("=" * 60)
    print("決済済みなのに postmortem がない取引（直近20件）")
    print("=" * 60)
    missing = [t for t in closed if str(t[0]) not in pm_ids]
    print(f"missing total: {len(missing)}")
    for t in missing[:20]:
        print(f"  trade={t[0]:12s} {t[1]:8s} closed={t[3]} pl={t[4]}")

    print()
    print("=" * 60)
    print("postmortem ある取引の closed_at")
    print("=" * 60)
    for t in closed:
        if str(t[0]) in pm_ids:
            print(f"  trade={t[0]:12s} {t[1]:8s} closed={t[3]} pl={t[4]}")

    # snapshot あるか
    cur.execute("SELECT trade_id FROM trade_snapshots")
    snap_ids = {r[0] for r in cur.fetchall()}
    print()
    print(f"snapshotあり trade数: {len(snap_ids)}")
    missing_snap = [t for t in closed if str(t[0]) not in snap_ids]
    print(f"snapshotない決済済みtrade: {len(missing_snap)}")
    for t in missing_snap[:5]:
        print(f"  trade={t[0]} {t[1]} closed={t[3]}")

    con.close()


if __name__ == "__main__":
    main()
