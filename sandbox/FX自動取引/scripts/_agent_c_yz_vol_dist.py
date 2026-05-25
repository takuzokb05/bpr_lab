"""Agent C 用一時スクリプト: GBP_JPY H1 YZ_vol 分布の期間別集計"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "mt5_GBP_JPY_H1_5y.csv", parse_dates=["datetime"]).set_index("datetime").sort_index()

o, h, l, c = df["open"], df["high"], df["low"], df["close"]
c_prev = c.shift(1)
log_oc_prev = np.log(o / c_prev)
log_co = np.log(c / o)
log_ho = np.log(h / o)
log_lo = np.log(l / o)
rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
w = 20
sigma_rs = rs.rolling(w).mean()
sigma_o = log_oc_prev.rolling(w).var()
sigma_c = log_co.rolling(w).var()
k = 0.34 / (1.34 + (w + 1) / (w - 1))
yz = sigma_o + k * sigma_c + (1 - k) * sigma_rs
yz_vol = np.sqrt(yz).dropna()

print("=== GBP_JPY H1 YZ_vol (w=20) 5年 ===")
print(f"全期間: {yz_vol.index.min()} -- {yz_vol.index.max()}")
print(f"行数: {len(yz_vol)}")
print(f"平均: {yz_vol.mean():.5f}, 中央値: {yz_vol.median():.5f}, std: {yz_vol.std():.5f}")
above = (yz_vol > 0.00175).sum()
print(f"閾値0.00175 上回り回数: {above} / {len(yz_vol)} = {above/len(yz_vol)*100:.2f}%")
print()

print("==== 期間別 (5年データの 1年ごと) ====")
for start, end, label in [
    ("2021-05-07", "2022-05-07", "Y1 2021-05〜2022-05"),
    ("2022-05-07", "2023-05-07", "Y2 2022-05〜2023-05"),
    ("2023-05-07", "2024-05-07", "Y3 2023-05〜2024-05"),
    ("2024-05-07", "2025-05-07", "Y4 2024-05〜2025-05"),
    ("2025-05-07", "2026-05-07", "Y5 2025-05〜2026-05"),
]:
    sub = yz_vol[(yz_vol.index >= start) & (yz_vol.index < end)]
    if len(sub) == 0:
        continue
    above = (sub > 0.00175).sum()
    rate = above / len(sub) * 100
    pct50 = np.percentile(sub.values, 50)
    pct90 = np.percentile(sub.values, 90)
    pct99 = np.percentile(sub.values, 99)
    print(f"{label}: n={len(sub)}, mean={sub.mean():.5f}, p50={pct50:.5f}, p90={pct90:.5f}, p99={pct99:.5f}, max={sub.max():.5f}, >0.00175={above} ({rate:.2f}%)")

print()
print("==== 直近 6ヶ月 (2025-11〜2026-05) ====")
last6m = yz_vol[yz_vol.index >= "2025-11-07"]
print(f"n={len(last6m)}, mean={last6m.mean():.5f}")
print(f"p50={np.percentile(last6m.values,50):.5f}, p75={np.percentile(last6m.values,75):.5f}, p90={np.percentile(last6m.values,90):.5f}, p99={np.percentile(last6m.values,99):.5f}, max={last6m.max():.5f}")
print(f">0.00175 = {(last6m>0.00175).sum()}回 ({(last6m>0.00175).mean()*100:.2f}%)")

print()
print("==== 直近 30日 (2026-04-07以降) ====")
recent = yz_vol[yz_vol.index >= "2026-04-07"]
print(f"n={len(recent)}, mean={recent.mean():.5f}, median={recent.median():.5f}, max={recent.max():.5f}, min={recent.min():.5f}")
print(f">0.00175 hit: {(recent>0.00175).sum()}回")
print(f"末尾10本: ")
for ts, v in recent.tail(10).items():
    print(f"  {ts}: {v:.5f}")

print()
print("==== 月別 hit率 (直近 12ヶ月) ====")
for month_start in pd.date_range("2025-05-01", "2026-05-01", freq="MS", tz="UTC"):
    me = month_start + pd.offsets.MonthEnd(0)
    sub = yz_vol[(yz_vol.index >= month_start) & (yz_vol.index <= me)]
    if len(sub) == 0:
        continue
    above = (sub > 0.00175).sum()
    rate = above / len(sub) * 100
    pct99 = np.percentile(sub.values, 99) if len(sub) > 0 else float('nan')
    print(f"{month_start.strftime('%Y-%m')}: n={len(sub):>4d}, mean={sub.mean():.5f}, max={sub.max():.5f}, p99={pct99:.5f}, >0.00175={above:>3d} ({rate:5.2f}%)")
