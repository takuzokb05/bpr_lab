"""PR #26 デプロイ後（5/5 03:01〜）の取引・postmortem発生状況。"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fx_trading.db"

# PR #26 デプロイ (新Python PID 8044 起動)
PR26_DEPLOY = "2026-05-04T18:01:05+00:00"  # JST 5/5 03:01 = UTC 5/4 18:01


def main() -> None:
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    print(f"PR #26 deploy at: {PR26_DEPLOY} (UTC) / JST 5/5 03:01")
    print("=" * 60)

    # 新規取引
    cur.execute(
        "SELECT trade_id, instrument, units, opened_at, closed_at, pl, status "
        "FROM trades WHERE opened_at >= ? ORDER BY opened_at DESC",
        (PR26_DEPLOY,),
    )
    new_trades = cur.fetchall()
    print(f"PR#26後の新規取引: {len(new_trades)}")
    for t in new_trades[:10]:
        side = "BUY" if t[2] > 0 else "SELL"
        status = t[6] or "(none)"
        closed = t[4] or "OPEN"
        pl = t[5] if t[5] is not None else "-"
        print(f"  {t[0]:12} {t[1]:8} {side:4} opened={t[3]} closed={closed} pl={pl} status={status}")

    # 新規postmortem
    cur.execute(
        "SELECT trade_id, created_at, analysis_json "
        "FROM trade_postmortems WHERE created_at >= ? ORDER BY created_at DESC",
        (PR26_DEPLOY,),
    )
    new_pm = cur.fetchall()
    print()
    print(f"PR#26後の新規postmortem: {len(new_pm)}")
    for trade_id, created, _ in new_pm[:10]:
        print(f"  trade={trade_id} created={created}")

    # 直近の決済（PR#26後）
    cur.execute(
        "SELECT COUNT(*) FROM trades WHERE closed_at IS NOT NULL AND closed_at >= ?",
        (PR26_DEPLOY,),
    )
    closed_after = cur.fetchone()[0]
    print()
    print(f"PR#26後の決済済件数: {closed_after}")
    print(f"PR#26後のpostmortem率: "
          f"{len(new_pm)/closed_after*100:.1f}% ({len(new_pm)}/{closed_after})"
          if closed_after else "  (まだ決済なし)")

    con.close()


if __name__ == "__main__":
    main()
