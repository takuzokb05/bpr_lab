"""PR #25 (max_tokens fix) 反映後の postmortem 出力率を計測する。

PR #25 を含む新プロセスは 2026-05-04 09:52:53 起動。
それ以降の決済 vs postmortem 比率を見て、修正の効果を確認する。
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fx_trading.db"

# PR #25 が稼働開始した時刻（VPS 5/4 09:52:53 起動）
FIX_DEPLOY_AT = datetime(2026, 5, 4, 0, 52, 53, tzinfo=timezone.utc).isoformat()
# (JST 9:52 = UTC 0:52)


def main() -> None:
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    # 1. 修正前後の決済数
    print("=" * 60)
    print(f"PR #25 deploy at: {FIX_DEPLOY_AT}")
    print("=" * 60)

    cur.execute(
        "SELECT COUNT(*) FROM trades WHERE closed_at IS NOT NULL "
        "AND closed_at < ?",
        (FIX_DEPLOY_AT,),
    )
    closed_before = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM trades WHERE closed_at IS NOT NULL "
        "AND closed_at >= ?",
        (FIX_DEPLOY_AT,),
    )
    closed_after = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM trade_postmortems WHERE created_at < ?",
        (FIX_DEPLOY_AT,),
    )
    pm_before = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM trade_postmortems WHERE created_at >= ?",
        (FIX_DEPLOY_AT,),
    )
    pm_after = cur.fetchone()[0]

    print()
    print(f"BEFORE fix:")
    print(f"  closed trades : {closed_before}")
    print(f"  postmortems   : {pm_before}")
    if closed_before:
        print(f"  rate          : {pm_before/closed_before*100:.1f}%")

    print()
    print(f"AFTER fix:")
    print(f"  closed trades : {closed_after}")
    print(f"  postmortems   : {pm_after}")
    if closed_after:
        print(f"  rate          : {pm_after/closed_after*100:.1f}%")
    else:
        print("  (no closed trades after fix yet)")

    # 2. 修正後の決済 trade_id 一覧 + postmortem の有無
    print()
    print("=" * 60)
    print("修正後の決済（trade_id ごと postmortem 有無）")
    print("=" * 60)
    cur.execute(
        "SELECT trade_id, instrument, closed_at, pl FROM trades "
        "WHERE closed_at IS NOT NULL AND closed_at >= ? "
        "ORDER BY closed_at DESC",
        (FIX_DEPLOY_AT,),
    )
    rows = cur.fetchall()
    cur.execute("SELECT trade_id FROM trade_postmortems")
    pm_ids = {r[0] for r in cur.fetchall()}

    for trade_id, inst, closed, pl in rows:
        flag = "OK" if str(trade_id) in pm_ids else "MISS"
        print(f"  {flag} {trade_id:12} {inst:8} {closed} pl={pl}")

    # 3. AFTER fix で postmortem 失敗（決済はあるが pm がない）
    missing_after = [r for r in rows if str(r[0]) not in pm_ids]
    print()
    print(f"AFTER fix で postmortem missing: {len(missing_after)}/{len(rows)}")

    con.close()


if __name__ == "__main__":
    main()
