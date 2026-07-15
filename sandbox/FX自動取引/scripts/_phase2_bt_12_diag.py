"""診断: ローリング cointegration の動態を確認

- 180 日 / 120 日 / 90 日 ローリングで p<0.05 を満たすペア組合せの時系列頻度
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint

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


def rolling_coint_analysis(data, common_idx, window_days, step_days=14):
    """各 window で 全ペア組合せの p<0.05 比率を時系列で集計"""
    pair_pairs = []
    for i, a in enumerate(INSTRUMENTS):
        for j, b in enumerate(INSTRUMENTS):
            if i < j:
                pair_pairs.append((a, b))

    rows = []
    cur = common_idx[0] + pd.Timedelta(days=window_days)
    while cur <= common_idx[-1]:
        w_start = cur - pd.Timedelta(days=window_days)
        w_end = cur
        for a, b in pair_pairs:
            sa = data[a].loc[w_start:w_end, "close"]
            sb = data[b].loc[w_start:w_end, "close"]
            if len(sa) < 30:
                continue
            try:
                _, pval, _ = coint(sa.values, sb.values, trend="c")
            except Exception:
                pval = np.nan
            rows.append({"end": cur, "pair": f"{a}_{b}", "pvalue": pval,
                         "is_coint": (not np.isnan(pval)) and pval < 0.05})
        cur += pd.Timedelta(days=step_days)
    return pd.DataFrame(rows)


def main():
    data, common_idx = load_data()
    print(f"期間: {common_idx[0]} -> {common_idx[-1]} ({len(common_idx)} 日)")

    for w in [90, 120, 180, 240]:
        df = rolling_coint_analysis(data, common_idx, w)
        n_total = len(df)
        n_coint = df["is_coint"].sum()
        pct = n_coint / n_total * 100 if n_total > 0 else 0
        # ペアごとの coint 維持率
        by_pair = df.groupby("pair")["is_coint"].mean().sort_values(ascending=False)
        print(f"\n=== window={w}日 ===")
        print(f"  total snapshots: {n_total}, coint比率: {pct:.1f}% ({n_coint}/{n_total})")
        print(f"  ペア別 coint 維持率 (上位 10):")
        print(by_pair.head(10).to_string())

    # 最良ペアの p値時系列
    print("\n=== 180日 window 最良ペアの p値時系列 (EUR_USD_GBP_USD) ===")
    df_180 = rolling_coint_analysis(data, common_idx, 180)
    eg = df_180[df_180["pair"] == "EUR_USD_GBP_USD"]
    print(eg.head(20).to_string())
    print(f"  最低 p値: {eg['pvalue'].min():.4f}  最高: {eg['pvalue'].max():.4f}")


if __name__ == "__main__":
    main()
