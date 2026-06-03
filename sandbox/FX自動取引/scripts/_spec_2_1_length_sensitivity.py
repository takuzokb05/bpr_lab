"""SPEC v2 - 2-1 length 感度分析

YZ_vol window と CHOP length の暫定値（20, 14）が安定範囲か確認。
- YZ_vol window: [10, 14, 20, 30] × D1(5.5y) × 3pair
- CHOP length: [7, 10, 14, 21] × M15(2y) × 3pair

各 length で「OOS_TR>1.0 が成立する閾値が存在するか」の生存性と、
最良 OOS_TR 値の安定性（length 間で大きくぶれないか）を確認。

使用例:
  python scripts/_spec_2_1_length_sensitivity.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

import numpy as np
import pandas as pd
import pandas_ta as ta

ROOT = Path(__file__).resolve().parent.parent

PAIRS = ["USD_JPY", "EUR_USD", "GBP_JPY"]
IS_RATIO = 0.75
MIN_SAMPLE = 50

LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}

YZ_PERCENTILES = [30, 50, 60, 70, 80]   # 5点でいい（粒度十分）
CHOP_GRID = [30, 35, 38.2, 42, 50, 60]


def calc_yang_zhang(df: pd.DataFrame, window: int) -> pd.Series:
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    c_prev = c.shift(1)
    log_oc_prev = np.log(o / c_prev)
    log_co = np.log(c / o)
    log_ho = np.log(h / o)
    log_lo = np.log(l / o)
    rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
    sigma_rs = rs.rolling(window).mean()
    sigma_o = log_oc_prev.rolling(window).var()
    sigma_c = log_co.rolling(window).var()
    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    yz = sigma_o + k * sigma_c + (1 - k) * sigma_rs
    return np.sqrt(yz)


def calc_chop(df: pd.DataFrame, length: int) -> pd.Series:
    return ta.chop(df["high"], df["low"], df["close"], length=length)


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def add_returns(df: pd.DataFrame, lookahead: int) -> pd.DataFrame:
    out = df.copy()
    out["future_return"] = (out["close"].shift(-lookahead) - out["close"]) / out["close"]
    out["past_return"] = (out["close"] - out["close"].shift(lookahead)) / out["close"].shift(lookahead)
    return out


def split_is_oos(df: pd.DataFrame, ratio: float = IS_RATIO):
    n = len(df)
    split_idx = int(n * ratio)
    return df.iloc[:split_idx], df.iloc[split_idx:]


def evaluate_at_threshold(df_with_ret: pd.DataFrame, indicator: pd.Series,
                          threshold: float, comparison: str) -> dict:
    df = df_with_ret.copy()
    df["ind"] = indicator.reindex(df.index)
    df = df.dropna(subset=["ind", "future_return", "past_return"])

    if comparison == "gt":
        high = df[df["ind"] > threshold]
        low = df[df["ind"] <= threshold]
    else:
        high = df[df["ind"] < threshold]
        low = df[df["ind"] >= threshold]

    n_triggers = len(high)
    if n_triggers == 0:
        return {"n": 0, "tr": None, "dpr": None}

    median_high = float(high["future_return"].abs().median())
    median_low = float(low["future_return"].abs().median()) if len(low) > 0 else 1e-9
    tr = median_high / median_low if median_low > 0 else None
    same_sign = (np.sign(high["past_return"]) == np.sign(high["future_return"])).sum()
    pr = float(same_sign / len(high))
    return {"n": n_triggers, "tr": tr, "dpr": pr}


def best_eligible_threshold(rows: list[dict]) -> dict | None:
    """rows = [{"thr":, "is_n":, "is_tr":, "oos_n":, "oos_tr":, ...}]"""
    eligible = [r for r in rows
                if r["is_n"] >= MIN_SAMPLE and r["oos_n"] >= MIN_SAMPLE
                and r["is_tr"] is not None and r["oos_tr"] is not None]
    if not eligible:
        return None
    return max(eligible, key=lambda r: r["is_tr"])


def evaluate_yz(pair: str, timeframe: str, years: int, window: int) -> dict:
    csv_path = ROOT / "data" / f"mt5_{pair}_{timeframe}_{years}y.csv"
    if not csv_path.exists():
        return {"pair": pair, "tf": timeframe, "window": window, "error": "no csv"}
    df = load_csv(csv_path)
    indicator = calc_yang_zhang(df, window=window)
    valid = indicator.dropna()
    grid = [float(np.percentile(valid, p)) for p in YZ_PERCENTILES]

    df_ret = add_returns(df, LOOKAHEAD[timeframe]).dropna()
    is_df, oos_df = split_is_oos(df_ret, IS_RATIO)

    rows = []
    for pct, thr in zip(YZ_PERCENTILES, grid):
        is_r = evaluate_at_threshold(is_df, indicator, thr, "gt")
        oos_r = evaluate_at_threshold(oos_df, indicator, thr, "gt")
        rows.append({"pct": pct, "thr": thr,
                     "is_n": is_r["n"], "is_tr": is_r["tr"], "is_dpr": is_r["dpr"],
                     "oos_n": oos_r["n"], "oos_tr": oos_r["tr"], "oos_dpr": oos_r["dpr"]})

    best = best_eligible_threshold(rows)
    return {"pair": pair, "tf": timeframe, "indicator": "YZ_vol",
            "param_name": "window", "param_value": window,
            "rows": rows, "best": best}


def evaluate_chop(pair: str, timeframe: str, years: int, length: int) -> dict:
    csv_path = ROOT / "data" / f"mt5_{pair}_{timeframe}_{years}y.csv"
    if not csv_path.exists():
        return {"pair": pair, "tf": timeframe, "length": length, "error": "no csv"}
    df = load_csv(csv_path)
    indicator = calc_chop(df, length=length)

    df_ret = add_returns(df, LOOKAHEAD[timeframe]).dropna()
    is_df, oos_df = split_is_oos(df_ret, IS_RATIO)

    rows = []
    for thr in CHOP_GRID:
        is_r = evaluate_at_threshold(is_df, indicator, thr, "lt")
        oos_r = evaluate_at_threshold(oos_df, indicator, thr, "lt")
        rows.append({"thr": thr,
                     "is_n": is_r["n"], "is_tr": is_r["tr"], "is_dpr": is_r["dpr"],
                     "oos_n": oos_r["n"], "oos_tr": oos_r["tr"], "oos_dpr": oos_r["dpr"]})

    best = best_eligible_threshold(rows)
    return {"pair": pair, "tf": timeframe, "indicator": "CHOP",
            "param_name": "length", "param_value": length,
            "rows": rows, "best": best}


def main():
    print(f"\n{'='*120}")
    print(f"SPEC v2 - 2-1 length 感度分析")
    print(f"{'='*120}")

    results = []

    # ---- YZ_vol window 感度: D1 5.5y × 3pair × window ----
    print(f"\n--- YZ_vol window 感度（D1 10y）---")
    print(f"  {'pair':<8} {'window':>7} {'best_pct':>9} {'best_thr':>10} {'IS_TR':>7} {'OOS_TR':>7} {'OOS_n':>6} {'判定':>10}")
    for window in [10, 14, 20, 30]:
        for pair in PAIRS:
            r = evaluate_yz(pair, "D1", 10, window)
            results.append(r)
            best = r.get("best")
            if best:
                surv = "✓" if (best["oos_tr"] and best["oos_tr"] > 1.0 and best["is_tr"] > 1.05) else "✗"
                print(f"  {pair:<8} {window:>7} {best['pct']:>9} {best['thr']:>10.5f} "
                      f"{best['is_tr']:>7.3f} {best['oos_tr']:>7.3f} {best['oos_n']:>6} {surv:>10}")
            else:
                print(f"  {pair:<8} {window:>7} {'-':>9} {'-':>10} {'-':>7} {'-':>7} {'-':>6} {'✗':>10}")

    # ---- YZ_vol window 感度: H1 5y × 3pair × window ----
    print(f"\n--- YZ_vol window 感度（H1 5y）---")
    print(f"  {'pair':<8} {'window':>7} {'best_pct':>9} {'best_thr':>10} {'IS_TR':>7} {'OOS_TR':>7} {'OOS_n':>6} {'判定':>10}")
    for window in [10, 14, 20, 30]:
        for pair in PAIRS:
            r = evaluate_yz(pair, "H1", 5, window)
            results.append(r)
            best = r.get("best")
            if best:
                surv = "✓" if (best["oos_tr"] and best["oos_tr"] > 1.0 and best["is_tr"] > 1.05) else "✗"
                print(f"  {pair:<8} {window:>7} {best['pct']:>9} {best['thr']:>10.5f} "
                      f"{best['is_tr']:>7.3f} {best['oos_tr']:>7.3f} {best['oos_n']:>6} {surv:>10}")
            else:
                print(f"  {pair:<8} {window:>7} {'-':>9} {'-':>10} {'-':>7} {'-':>7} {'-':>6} {'✗':>10}")

    # ---- YZ_vol window 感度: M15 2y × 3pair × window ----
    print(f"\n--- YZ_vol window 感度（M15 2y）---")
    print(f"  {'pair':<8} {'window':>7} {'best_pct':>9} {'best_thr':>10} {'IS_TR':>7} {'OOS_TR':>7} {'OOS_n':>6} {'判定':>10}")
    for window in [10, 14, 20, 30]:
        for pair in PAIRS:
            r = evaluate_yz(pair, "M15", 2, window)
            results.append(r)
            best = r.get("best")
            if best:
                surv = "✓" if (best["oos_tr"] and best["oos_tr"] > 1.0 and best["is_tr"] > 1.05) else "✗"
                print(f"  {pair:<8} {window:>7} {best['pct']:>9} {best['thr']:>10.5f} "
                      f"{best['is_tr']:>7.3f} {best['oos_tr']:>7.3f} {best['oos_n']:>6} {surv:>10}")
            else:
                print(f"  {pair:<8} {window:>7} {'-':>9} {'-':>10} {'-':>7} {'-':>7} {'-':>6} {'✗':>10}")

    # ---- CHOP length 感度: M15 2y × 3pair × length ----
    print(f"\n--- CHOP length 感度（M15 2y）---")
    print(f"  {'pair':<8} {'length':>7} {'best_thr':>10} {'IS_TR':>7} {'OOS_TR':>7} {'OOS_n':>6} {'判定':>10}")
    for length in [7, 10, 14, 21]:
        for pair in PAIRS:
            r = evaluate_chop(pair, "M15", 2, length)
            results.append(r)
            best = r.get("best")
            if best:
                surv = "✓" if (best["oos_tr"] and best["oos_tr"] > 1.0 and best["is_tr"] > 1.05) else "✗"
                print(f"  {pair:<8} {length:>7} {best['thr']:>10} "
                      f"{best['is_tr']:>7.3f} {best['oos_tr']:>7.3f} {best['oos_n']:>6} {surv:>10}")
            else:
                print(f"  {pair:<8} {length:>7} {'-':>10} {'-':>7} {'-':>7} {'-':>6} {'✗':>10}")

    out_json = ROOT / "data" / "spec_2_1_length_sensitivity.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
