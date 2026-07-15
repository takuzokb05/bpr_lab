"""本番DB調査用 (VPSにscpして実行)"""
import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\bpr_lab\sandbox\FX自動取引\data\fx_trading.db'
c = sqlite3.connect(db_path)
cur = c.cursor()

print('=== schema ===')
cur.execute("SELECT name,sql FROM sqlite_master WHERE type='table'")
for r in cur.fetchall():
    print(r[0])
    print(r[1][:300])
    print()

print('=== last 30 trades ===')
cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 30")
cols = [d[0] for d in cur.description]
print('cols:', cols)
for r in cur.fetchall():
    print(r)

print('=== since 2026-04-30 by instrument (post PR#4) ===')
cur.execute("""
    SELECT instrument,
           COUNT(*) AS n,
           SUM(CASE WHEN pl>0 THEN 1 ELSE 0 END) AS wins,
           ROUND(SUM(pl),0) AS sum_pl,
           ROUND(AVG(pl),1) AS avg_pl,
           COUNT(DISTINCT pl) AS distinct_pl,
           COUNT(DISTINCT close_price) AS distinct_close
    FROM trades
    WHERE status='closed' AND closed_at >= '2026-04-30'
    GROUP BY instrument
""")
for r in cur.fetchall():
    print(r)

print('=== all closed trades ===')
cur.execute("""
    SELECT instrument,
           COUNT(*) AS n,
           SUM(CASE WHEN pl>0 THEN 1 ELSE 0 END) AS wins,
           ROUND(SUM(pl),0) AS sum_pl,
           ROUND(AVG(pl),1) AS avg_pl
    FROM trades WHERE status='closed' GROUP BY instrument
""")
for r in cur.fetchall():
    print(r)

print('=== open positions ===')
cur.execute("SELECT * FROM trades WHERE status='open'")
for r in cur.fetchall():
    print(r)

print('=== last 7 closed (post PR#4) ===')
cur.execute("""
    SELECT id, trade_id, instrument, units, open_price, close_price, stop_loss, take_profit, pl,
           opened_at, closed_at
    FROM trades
    WHERE status='closed' AND closed_at >= '2026-04-30T11:00:00'
    ORDER BY id ASC
""")
for r in cur.fetchall():
    print(r)
