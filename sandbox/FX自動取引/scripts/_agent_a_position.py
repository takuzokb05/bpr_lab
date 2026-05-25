"""Agent A: PoC期間のH1 vol max=0.00131 が5年分布で何パーセンタイルか"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.spec_v2.seasonal_detection import calc_yang_zhang

csv = ROOT / 'data' / 'mt5_GBP_JPY_H1_5y.csv'
df = pd.read_csv(csv, parse_dates=['datetime']).set_index('datetime').sort_index()
yz = calc_yang_zhang(df, window=20).dropna()

# PoC期間で観測された値
poc_max = 0.001312
poc_p95 = 0.001298
poc_median = 0.000693
poc_min = 0.000501

print('## PoC期間で観測された値が、過去5年分布でどのパーセンタイルか')
print()
for label, val in [('PoC min',poc_min),('PoC median',poc_median),('PoC p95',poc_p95),('PoC max',poc_max)]:
    pct_5y = (yz < val).mean() * 100
    print(f'- {label} = {val:.6f} -> 5年分布の {pct_5y:.1f}%ile')

# 過去5年のうち「H1 max が PoC max 以下だった連続期間」を探す
# 14日窓ローリングで max を計算し、PoC期間 max=0.00131 以下になっていた窓を見つける
print()
print('## 過去5年で「rolling 14日 max <= 0.00131」だった期間 (PoC級の低ボラ期間)')
window_bars = 14 * 24  # H1 だと 14日 = 336バー
rmax = yz.rolling(window_bars).max()
low_periods = rmax[rmax <= 0.00131]
if len(low_periods) > 0:
    print(f'該当バー数 : {len(low_periods)} / {len(rmax.dropna())} = {len(low_periods)/len(rmax.dropna())*100:.2f}%')
    # 連続期間
    grouped = (low_periods.index.to_series().diff() > pd.Timedelta(hours=2)).cumsum()
    spans = low_periods.groupby(grouped).agg(['first', 'last', 'count'])
    print(f'連続スパン数 : {len(spans)}')
    print('### 連続期間のサンプル (count >= 100 のもの)')
    big_spans = spans[spans['count'] >= 100]
    for idx, row in big_spans.head(20).iterrows():
        # firstはvalueなのでindexで時刻を取り直す
        sub = low_periods[grouped == idx]
        t0 = sub.index[0]
        t1 = sub.index[-1]
        duration_h = (t1 - t0).total_seconds() / 3600
        print(f'  {t0} -> {t1} ({duration_h:.0f} h, {row["count"]} bars)')
else:
    print('該当なし: PoC期間より大きいmax値が常にあった')

# 別アプローチ: 各月のH1 max を計算
print()
print('## 過去5年の各月 H1 max (PoC max=0.00131 と比較)')
monthly = yz.resample('ME').max()
print('| 年月 | H1 max | / 0.00175 | PoC max=0.00131 以下か |')
print('|---|---|---|---|')
for ym, v in monthly.items():
    flag = 'YES (PoC級低ボラ)' if v <= 0.00131 else ''
    print(f'| {ym.strftime("%Y-%m")} | {v:.6f} | {v/0.00175*100:.1f}% | {flag} |')
