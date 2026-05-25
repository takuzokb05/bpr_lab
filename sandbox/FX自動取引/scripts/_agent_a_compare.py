"""Agent A: MT5 CSV(H1) と PoC DB の YZ_vol 比較 — 同一時刻の値を突き合わせ"""
import sqlite3
import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.spec_v2.seasonal_detection import calc_yang_zhang

csv = ROOT / 'data' / 'mt5_GBP_JPY_H1_5y.csv'
df = pd.read_csv(csv, parse_dates=['datetime']).set_index('datetime').sort_index()
yz_csv = calc_yang_zhang(df, window=20).dropna()

# 直近 (PoC 期間に近い分)
recent = yz_csv[yz_csv.index >= pd.Timestamp('2026-04-25', tz='UTC')]
print(f'## MT5 CSV H1 直近 (2026-04-25 以降) YZ_vol(20)')
print(f'バー数: {len(recent)}')
print(f'min/max: {recent.min():.6f} / {recent.max():.6f}')
print(f'median : {recent.median():.6f}')
print(f'p95    : {recent.quantile(0.95):.6f}')
print(f'> 0.00175 件数 : {(recent > 0.00175).sum()}')
print()
print('### 直近 H1 各時刻の YZ_vol (last 30 bars)')
print(recent.tail(30).to_string())

# CSV 期間 vs PoC 期間
print()
print(f'CSV 最終時刻 : {df.index.max()}')
print(f'CSV 期間 : {df.index.min()} -> {df.index.max()}')
