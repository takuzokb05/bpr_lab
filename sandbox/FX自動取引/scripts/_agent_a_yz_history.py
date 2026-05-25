"""Agent A: 過去 GBP_JPY H1 YZ_vol 分布 (参考値)"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.spec_v2.seasonal_detection import calc_yang_zhang

csv = ROOT / 'data' / 'mt5_GBP_JPY_H1_5y.csv'
df = pd.read_csv(csv, parse_dates=['datetime']).set_index('datetime').sort_index()

print(f'## GBP_JPY H1 全期間概要')
print(f'- 期間: {df.index.min()} -> {df.index.max()}')
print(f'- バー数: {len(df)}')

yz = calc_yang_zhang(df, window=20).dropna()
print(f'- YZ_vol(window=20) 計算可能バー数: {len(yz)}')

# 全期間統計
vals_all = sorted(yz.values)


def stats(vals, label):
    n = len(vals)
    if n == 0:
        print(f'### {label}: データなし')
        return
    def pct(p):
        return vals[max(0, min(n - 1, int(round((p / 100.0) * (n - 1)))))]
    print(f'### {label} (n={n})')
    print(f'- min/max     : {vals[0]:.6f} / {vals[-1]:.6f}')
    print(f'- mean/median : {sum(vals)/n:.6f} / {pct(50):.6f}')
    print(f'- p25/p75     : {pct(25):.6f} / {pct(75):.6f}')
    print(f'- p90/p95/p99 : {pct(90):.6f} / {pct(95):.6f} / {pct(99):.6f}')
    print(f'- 0.00175 over : {sum(1 for v in vals if v > 0.00175)} ({sum(1 for v in vals if v > 0.00175)/n*100:.2f}%)')
    print()


stats(vals_all, '全期間 (約5年)')

# 直近1年
cutoff_1y = df.index.max() - pd.Timedelta(days=365)
yz_1y = yz[yz.index >= cutoff_1y]
stats(sorted(yz_1y.values), '直近 1 年')

# 直近6ヶ月
cutoff_6m = df.index.max() - pd.Timedelta(days=180)
yz_6m = yz[yz.index >= cutoff_6m]
stats(sorted(yz_6m.values), '直近 6 か月')

# 直近3ヶ月
cutoff_3m = df.index.max() - pd.Timedelta(days=90)
yz_3m = yz[yz.index >= cutoff_3m]
stats(sorted(yz_3m.values), '直近 3 か月')

# 直近1ヶ月 (PoC 期間相当)
cutoff_1m = df.index.max() - pd.Timedelta(days=30)
yz_1m = yz[yz.index >= cutoff_1m]
stats(sorted(yz_1m.values), '直近 1 か月 (PoC 相当)')

# 年別の中央値・p95
print('## 年別 YZ_vol(20) 中央値 / p95')
print('| 年 | n | median | p90 | p95 | max | over 0.00175 |')
print('|---|---|---|---|---|---|---|')
for yr, grp in yz.groupby(yz.index.year):
    v = sorted(grp.values)
    n = len(v)
    if n == 0:
        continue
    p50 = v[n // 2]
    p90 = v[int(0.90 * (n - 1))]
    p95 = v[int(0.95 * (n - 1))]
    mx = v[-1]
    over = sum(1 for x in v if x > 0.00175)
    print(f'| {yr} | {n} | {p50:.6f} | {p90:.6f} | {p95:.6f} | {mx:.6f} | {over} ({over/n*100:.1f}%) |')

# 月別 (直近12ヶ月)
print()
print('## 月別 YZ_vol(20) 中央値 / p95 (直近 12 か月)')
print('| 年月 | n | median | p95 | max | over 0.00175 |')
print('|---|---|---|---|---|---|')
yz_12m = yz[yz.index >= df.index.max() - pd.Timedelta(days=365)]
for ym, grp in yz_12m.groupby(yz_12m.index.to_period('M')):
    v = sorted(grp.values)
    n = len(v)
    if n == 0:
        continue
    p50 = v[n // 2]
    p95 = v[int(0.95 * (n - 1))]
    mx = v[-1]
    over = sum(1 for x in v if x > 0.00175)
    print(f'| {ym} | {n} | {p50:.6f} | {p95:.6f} | {mx:.6f} | {over} ({over/n*100:.1f}%) |')
