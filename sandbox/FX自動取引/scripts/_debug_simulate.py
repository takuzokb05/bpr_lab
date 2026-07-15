"""シミュレーション内部の動作を1ステップずつ追跡"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

DATA_DIR = ROOT / "data"
INSTRUMENTS = ["EUR_USD", "GBP_USD", "AUD_USD", "NZD_USD", "USD_CHF", "USD_CAD", "USD_JPY"]


def load_data():
    data = {}
    for inst in INSTRUMENTS:
        path = DATA_DIR / f"mt5_{inst}_D1_5y.csv"
        df = pd.read_csv(path, parse_dates=["datetime"]).set_index("datetime").sort_index()
        df.index = df.index.tz_convert("UTC") if df.index.tz else df.index.tz_localize("UTC")
        data[inst] = df
    common_idx = None
    for inst, df in data.items():
        common_idx = df.index if common_idx is None else common_idx.intersection(df.index)
    for inst in INSTRUMENTS:
        data[inst] = data[inst].loc[common_idx]
    return data, common_idx


data, common_idx = load_data()
base_idx = common_idx

pair_a, pair_b = "NZD_USD", "USD_CAD"
print(f"Pair: {pair_a} / {pair_b}")

# 200日後 (180日窓を通過する最初の地点)
ts = base_idx[200]
print(f"ts (200番目): {ts}")
window_end = ts
window_start = ts - pd.Timedelta(days=180)
print(f"  window: {window_start} -> {window_end}")
print(f"  window_start < base_idx[0]? {window_start < base_idx[0]}")
print(f"  base_idx[0]: {base_idx[0]}")

sa = data[pair_a].loc[window_start:window_end, "close"]
sb = data[pair_b].loc[window_start:window_end, "close"]
print(f"  data len: sa={len(sa)}, sb={len(sb)}")

tstat, pval, _ = coint(sa.values, sb.values, trend="c")
print(f"  coint p={pval:.4f}")

# β
X = add_constant(sb.values)
model = OLS(sa.values, X).fit()
beta = float(model.params[1])
print(f"  beta={beta:.4f}")

# z-score 計算
lookback_start = ts - pd.Timedelta(days=70)
print(f"  lookback z: {lookback_start} -> {ts}")
sa2 = data[pair_a].loc[lookback_start:ts, "close"]
sb2 = data[pair_b].loc[lookback_start:ts, "close"]
print(f"  z lookback data len: sa={len(sa2)}, sb={len(sb2)}")
print(f"  ZSCORE_LOOKBACK=60, sa2>=60? {len(sa2) >= 60}")

spread = sa2 - beta * sb2
print(f"  spread head: {spread.head(3).values}")
z_series = (spread - spread.rolling(60).mean()) / spread.rolling(60).std(ddof=0)
print(f"  z final 5: {z_series.tail(5).values}")
