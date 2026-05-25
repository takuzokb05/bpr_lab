"""Phase 0 analyst probe - 亡き者DBから戦略/ペア別に集計"""
import sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

for db_name in ["fx_trading_prod_snapshot.db", "fx_trading.db"]:
    db_path = ROOT / "data" / db_name
    if not db_path.exists():
        continue
    print(f"\n===== {db_name} =====")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        print("tables:", [r[0] for r in cur.fetchall()])
        cur.execute("PRAGMA table_info(trades)")
        cols = [r[1] for r in cur.fetchall()]
        print("trades cols:", cols)

        # ペア別集計 (pl 列)
        cur.execute("SELECT instrument, status, COUNT(*), ROUND(SUM(pl),0) FROM trades GROUP BY instrument, status")
        print("\n[instrument x status]")
        for row in cur.fetchall():
            print(row)

        # AI direction 別 (ai_decision)
        print("\n[ai_decision x instrument (closed)]")
        cur.execute("""
            SELECT ai_decision, instrument, COUNT(*),
                   SUM(CASE WHEN pl>0 THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN pl<=0 THEN 1 ELSE 0 END) as losses,
                   ROUND(SUM(pl),0) as total_pnl,
                   ROUND(SUM(CASE WHEN pl>0 THEN pl ELSE 0 END),0) as gross_win,
                   ROUND(-SUM(CASE WHEN pl<0 THEN pl ELSE 0 END),0) as gross_loss
            FROM trades
            WHERE status='closed'
            GROUP BY ai_decision, instrument
            ORDER BY instrument, ai_decision
        """)
        for row in cur.fetchall():
            print(row)

        # ai_regime 別
        print("\n[ai_regime x instrument (closed)]")
        cur.execute("""
            SELECT ai_regime, instrument, COUNT(*),
                   SUM(CASE WHEN pl>0 THEN 1 ELSE 0 END) as wins,
                   ROUND(SUM(pl),0) as total_pnl
            FROM trades
            WHERE status='closed'
            GROUP BY ai_regime, instrument
            ORDER BY instrument, ai_regime
        """)
        for row in cur.fetchall():
            print(row)

        # 保有時間統計
        print("\n[Holding time stats (closed)]")
        try:
            cur.execute("""
                SELECT instrument,
                       COUNT(*),
                       ROUND(AVG((julianday(closed_at)-julianday(opened_at))*1440), 1) as avg_min
                FROM trades
                WHERE status='closed' AND closed_at IS NOT NULL AND opened_at IS NOT NULL
                GROUP BY instrument
            """)
            for row in cur.fetchall():
                print(row)
        except Exception as e:
            print("  holding time err:", e)

        # 月別累計
        print("\n[Monthly PnL (closed)]")
        try:
            cur.execute("""
                SELECT substr(closed_at, 1, 7) as mo, instrument, COUNT(*), ROUND(SUM(pl), 0)
                FROM trades
                WHERE status='closed' AND closed_at IS NOT NULL
                GROUP BY mo, instrument
                ORDER BY mo, instrument
                LIMIT 80
            """)
            for row in cur.fetchall():
                print(row)
        except Exception as e:
            print("  monthly err:", e)
    finally:
        con.close()
