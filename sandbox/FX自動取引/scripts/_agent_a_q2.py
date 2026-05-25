"""Agent A Q2: time series + alternative threshold simulation + conjunction"""
import sqlite3
import json
import datetime as dt
from collections import defaultdict

DB = r'C:\bpr_lab_spec_v2\sandbox\FX自動取引\data\fx_spec_v2.db'
con = sqlite3.connect(DB)
cur = con.cursor()

# 日別 H1 YZ_vol
cur.execute('''SELECT substr(judged_at_utc,1,10) AS d, h1_yz_vol
               FROM seasonal_judgments WHERE h1_yz_vol IS NOT NULL''')
by_day = defaultdict(list)
for d, v in cur.fetchall():
    by_day[d].append(v)

print('## 日別 H1 YZ_vol 推移 (UTC)')
print('| date | n | median | p90 | p95 | max | p95/0.00175 |')
print('|---|---|---|---|---|---|---|')
for d in sorted(by_day.keys()):
    vs = sorted(by_day[d])
    n = len(vs)
    med = vs[n // 2]
    p90 = vs[max(0, int(0.90 * (n - 1)))]
    p95 = vs[max(0, int(0.95 * (n - 1)))]
    mx = vs[-1]
    ratio = p95 / 0.00175 * 100
    print(f'| {d} | {n} | {med:.6f} | {p90:.6f} | {p95:.6f} | {mx:.6f} | {ratio:.1f}% |')

print()
print('## 代替閾値シミュレーション (期間全体)')
cur.execute('SELECT h1_yz_vol FROM seasonal_judgments WHERE h1_yz_vol IS NOT NULL')
all_h1 = sorted([r[0] for r in cur.fetchall()])
n = len(all_h1)


def pctile(p):
    return all_h1[max(0, min(n - 1, int(round((p / 100.0) * (n - 1)))))]


candidates = {
    'p70': pctile(70),
    'p75': pctile(75),
    'p80': pctile(80),
    'p85': pctile(85),
    'p90': pctile(90),
    'p95': pctile(95),
    'p99': pctile(99),
}
print('| 閾値候補 | 閾値値 | over件数 | over率 |')
print('|---|---|---|---|')
for name, th in candidates.items():
    over = sum(1 for v in all_h1 if v > th)
    print(f'| {name} | {th:.6f} | {over} | {over/n*100:.1f}% |')
print(f'| 現行 | 0.001750 | 0 | 0.0% |')

# rolling 14日 p95
print()
print('## rolling 14日 p95 シミュレーション')
cur.execute('SELECT judged_at_utc, h1_yz_vol FROM seasonal_judgments WHERE h1_yz_vol IS NOT NULL ORDER BY judged_at_utc')
rows = cur.fetchall()
times = []
vals = []
for ts, v in rows:
    # ストリップして naive 化
    s = ts.replace('Z', '').split('+')[0]
    t = dt.datetime.fromisoformat(s)
    times.append(t)
    vals.append(v)
day_keys = sorted(set(t.date() for t in times))
print('| date_end | n_window | p95(14d) | / 0.00175 |')
print('|---|---|---|---|')
for dk in day_keys:
    cutoff = dt.datetime.combine(dk, dt.time(23, 59, 59))
    start = cutoff - dt.timedelta(days=14)
    window = sorted([v for t, v in zip(times, vals) if start <= t <= cutoff])
    if len(window) < 50:
        continue
    p95 = window[int(0.95 * (len(window) - 1))]
    print(f'| {dk} | {len(window)} | {p95:.6f} | {p95/0.00175*100:.1f}% |')

# M15 above=True のとき H1
print()
print('## M15 above=True のとき H1 YZ_vol 分布')
cur.execute('SELECT h1_yz_vol FROM seasonal_judgments WHERE m15_above=1 AND h1_yz_vol IS NOT NULL')
h1_when_m15_up = sorted([r[0] for r in cur.fetchall()])
nn = len(h1_when_m15_up)
if nn > 0:
    p50 = h1_when_m15_up[nn // 2]
    p90 = h1_when_m15_up[int(0.9 * (nn - 1))]
    p95 = h1_when_m15_up[int(0.95 * (nn - 1))]
    mx = h1_when_m15_up[-1]
    print(f'- n = {nn}')
    print(f'- median = {p50:.6f} (閾値の {p50/0.00175*100:.1f}%)')
    print(f'- p90    = {p90:.6f} (閾値の {p90/0.00175*100:.1f}%)')
    print(f'- p95    = {p95:.6f} (閾値の {p95/0.00175*100:.1f}%)')
    print(f'- max    = {mx:.6f} (閾値の {mx/0.00175*100:.1f}%)')

print()
print('## M15 上抜け時の H1 vol/閾値 比率分布')
thresholds_pct = [50, 60, 70, 80, 90, 95, 100]
print('| H1/threshold >= | 件数 | % of m15_above |')
print('|---|---|---|')
for pct in thresholds_pct:
    cnt = sum(1 for v in h1_when_m15_up if v >= 0.00175 * pct / 100)
    print(f'| {pct}% ({0.00175*pct/100:.5f}) | {cnt} | {cnt/nn*100:.1f}% |')

con.close()
