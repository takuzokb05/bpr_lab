"""SPEC v2 - 2-1 YZ_vol 追加検証 (細グリッド + サンプル考慮型最良閾値)

D1/H1/M15 のいずれかで、YZ_vol の細パーセンタイルグリッド (9点) を walk-forward 評価。
「OOS サンプル≥MIN_SAMPLE」を満たす範囲で最高 IS 閾値を採用（サンプル考慮型）。

使用例:
  python scripts/_spec_2_1_d1_yz_vol_revalidation.py --timeframe D1 --years 10
  python scripts/_spec_2_1_d1_yz_vol_revalidation.py --timeframe M15 --years 2
  python scripts/_spec_2_1_d1_yz_vol_revalidation.py --timeframe H1 --years 5
"""
from __future__ import annotations

import io
import json
import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("d1_yz_revalidation")
log.setLevel(logging.INFO)


import argparse
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--timeframe", choices=["M15", "H1", "D1"], default="D1")
_parser.add_argument("--years", type=int, default=10)
_args, _ = _parser.parse_known_args()
_TF = _args.timeframe
_YEARS = _args.years

PAIRS = {
    "USD_JPY": f"mt5_USD_JPY_{_TF}_{_YEARS}y.csv",
    "EUR_USD": f"mt5_EUR_USD_{_TF}_{_YEARS}y.csv",
    "GBP_JPY": f"mt5_GBP_JPY_{_TF}_{_YEARS}y.csv",
}

# 時間軸別 lookahead: M15=24bars(6h) / H1=6bars(6h) / D1=5bars(1週間営業日)
LOOKAHEAD_BARS = {"M15": 24, "H1": 6, "D1": 5}[_TF]
IS_RATIO = 0.75
PERCENTILES = [30, 40, 50, 55, 60, 65, 70, 75, 80]
MIN_SAMPLE = 50         # IS/OOS とも sample >= 50 を採用条件


def calc_yang_zhang(df: pd.DataFrame, window: int = 20) -> pd.Series:
    o = df["open"]
    h = df["high"]
    l = df["low"]
    c = df["close"]
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


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["future_return"] = (out["close"].shift(-LOOKAHEAD_BARS) - out["close"]) / out["close"]
    out["past_return"] = (out["close"] - out["close"].shift(LOOKAHEAD_BARS)) / out["close"].shift(LOOKAHEAD_BARS)
    return out


def split_is_oos(df: pd.DataFrame, ratio: float = IS_RATIO):
    n = len(df)
    split_idx = int(n * ratio)
    return df.iloc[:split_idx], df.iloc[split_idx:]


def evaluate_at_threshold(df_with_ret: pd.DataFrame, indicator: pd.Series, threshold: float) -> dict:
    """gt 比較で trigger された行の TR/DPR を測定（最低サンプル制約なし）"""
    df = df_with_ret.copy()
    df["ind"] = indicator.reindex(df.index)
    df = df.dropna(subset=["ind", "future_return", "past_return"])

    high = df[df["ind"] > threshold]
    low = df[df["ind"] <= threshold]

    n_triggers = len(high)
    if n_triggers == 0:
        return {"n_triggers": 0, "trendiness_ratio": None, "persistence_rate": None}

    median_high = float(high["future_return"].abs().median())
    median_low = float(low["future_return"].abs().median()) if len(low) > 0 else 1e-9
    tr = median_high / median_low if median_low > 0 else None

    same_sign = (np.sign(high["past_return"]) == np.sign(high["future_return"])).sum()
    pr = float(same_sign / len(high))

    return {"n_triggers": n_triggers, "trendiness_ratio": tr, "persistence_rate": pr}


def evaluate_pair(pair: str, df: pd.DataFrame) -> dict:
    indicator = calc_yang_zhang(df, window=20)
    valid = indicator.dropna()
    grid = [float(np.percentile(valid, p)) for p in PERCENTILES]

    df_with_ret = add_returns(df).dropna()
    is_df, oos_df = split_is_oos(df_with_ret, IS_RATIO)

    rows = []
    for pct, thr in zip(PERCENTILES, grid):
        is_r = evaluate_at_threshold(is_df, indicator, thr)
        oos_r = evaluate_at_threshold(oos_df, indicator, thr)
        rows.append({
            "percentile": pct,
            "threshold": thr,
            "is_n": is_r["n_triggers"],
            "is_tr": is_r["trendiness_ratio"],
            "is_dpr": is_r["persistence_rate"],
            "oos_n": oos_r["n_triggers"],
            "oos_tr": oos_r["trendiness_ratio"],
            "oos_dpr": oos_r["persistence_rate"],
        })

    # Spearman: IS/OOS とも非null TRランク
    is_trs = [r["is_tr"] for r in rows if r["is_tr"] is not None and r["oos_tr"] is not None]
    oos_trs = [r["oos_tr"] for r in rows if r["is_tr"] is not None and r["oos_tr"] is not None]
    rho_tr, _ = spearmanr(is_trs, oos_trs) if len(is_trs) >= 3 else (np.nan, np.nan)
    is_dprs = [r["is_dpr"] for r in rows if r["is_dpr"] is not None and r["oos_dpr"] is not None]
    oos_dprs = [r["oos_dpr"] for r in rows if r["is_dpr"] is not None and r["oos_dpr"] is not None]
    rho_dpr, _ = spearmanr(is_dprs, oos_dprs) if len(is_dprs) >= 3 else (np.nan, np.nan)

    # サンプル考慮型最良閾値:
    # IS_n>=MIN_SAMPLE AND OOS_n>=MIN_SAMPLE の中で IS_TR 最大
    eligible = [r for r in rows
                if r["is_n"] >= MIN_SAMPLE and r["oos_n"] >= MIN_SAMPLE
                and r["is_tr"] is not None]
    if eligible:
        best = max(eligible, key=lambda r: r["is_tr"])
    else:
        best = None

    return {
        "pair": pair,
        "rows": rows,
        "spearman_tr": float(rho_tr) if not np.isnan(rho_tr) else None,
        "spearman_dpr": float(rho_dpr) if not np.isnan(rho_dpr) else None,
        "best_eligible": best,
    }


def is_survivor(result: dict) -> bool:
    """採用条件: best_eligible が存在 AND IS_TR>1.05 AND OOS_TR>1.0
       AND max(Spearman_TR, Spearman_DPR) > 0.5"""
    best = result.get("best_eligible")
    if not best:
        return False
    if best["is_tr"] is None or best["is_tr"] < 1.05:
        return False
    if best["oos_tr"] is None or best["oos_tr"] < 1.0:
        return False
    rho = max(result["spearman_tr"] or -1, result["spearman_dpr"] or -1)
    if rho < 0.5:
        return False
    return True


def main():
    data_dir = ROOT / "data"
    print(f"\n{'='*120}")
    print(f"YZ_vol 追加検証 (細グリッド + サンプル考慮型最良閾値) [{_TF} {_YEARS}y]")
    print(f"  PERCENTILES = {PERCENTILES}")
    print(f"  MIN_SAMPLE = {MIN_SAMPLE}")
    print(f"  LOOKAHEAD_BARS = {LOOKAHEAD_BARS}")
    print(f"  IS_RATIO = {IS_RATIO}")
    print(f"{'='*120}")

    all_results = []
    for pair, csv_name in PAIRS.items():
        path = data_dir / csv_name
        if not path.exists():
            print(f"  {pair}: NOT FOUND ({path})")
            continue
        df = load_csv(path)
        r = evaluate_pair(pair, df)
        all_results.append(r)

        print(f"\n--- {pair} ---")
        print(f"  {'pct':>5} {'thr':>10} {'is_n':>6} {'is_TR':>8} {'is_DPR':>8} {'oos_n':>6} {'oos_TR':>8} {'oos_DPR':>8}")
        for row in r["rows"]:
            thr_s = f"{row['threshold']:.5f}"
            is_tr_s = f"{row['is_tr']:.3f}" if row['is_tr'] else "  -"
            is_dpr_s = f"{row['is_dpr']:.3f}" if row['is_dpr'] else "  -"
            oos_tr_s = f"{row['oos_tr']:.3f}" if row['oos_tr'] else "  -"
            oos_dpr_s = f"{row['oos_dpr']:.3f}" if row['oos_dpr'] else "  -"
            mark = ""
            if row['is_n'] >= MIN_SAMPLE and row['oos_n'] >= MIN_SAMPLE:
                mark = " ✓"
            print(f"  {row['percentile']:>5} {thr_s:>10} {row['is_n']:>6} {is_tr_s:>8} {is_dpr_s:>8} {row['oos_n']:>6} {oos_tr_s:>8} {oos_dpr_s:>8}{mark}")

        rho_tr = f"{r['spearman_tr']:+.3f}" if r['spearman_tr'] is not None else "  -"
        rho_dpr = f"{r['spearman_dpr']:+.3f}" if r['spearman_dpr'] is not None else "  -"
        print(f"  Spearman: TR={rho_tr}, DPR={rho_dpr}")

        best = r["best_eligible"]
        survivor = "✓ 採用可" if is_survivor(r) else "✗ 採用不可"
        if best:
            print(f"  最良閾値 (IS_n>={MIN_SAMPLE} AND OOS_n>={MIN_SAMPLE}):")
            print(f"    pct={best['percentile']}  thr={best['threshold']:.5f}")
            print(f"    IS:  n={best['is_n']:>4}  TR={best['is_tr']:.3f}  DPR={best['is_dpr']:.3f}")
            print(f"    OOS: n={best['oos_n']:>4}  TR={best['oos_tr']:.3f}  DPR={best['oos_dpr']:.3f}")
        else:
            print(f"  ✗ サンプル≥{MIN_SAMPLE} を満たす閾値なし")
        print(f"  判定: {survivor}")

    # サマリ
    print(f"\n{'='*120}")
    print(f"統合判定サマリ")
    print(f"{'='*120}")
    print(f"{'Pair':<10} {'best_pct':>10} {'best_thr':>12} {'IS_TR':>8} {'OOS_TR':>8} {'rho_TR':>8} {'判定':>10}")
    print("-" * 80)
    for r in all_results:
        best = r["best_eligible"]
        if best:
            pair = r["pair"]
            pct = best["percentile"]
            thr = f"{best['threshold']:.5f}"
            is_tr = f"{best['is_tr']:.3f}"
            oos_tr = f"{best['oos_tr']:.3f}" if best['oos_tr'] else "  -"
            rho = f"{r['spearman_tr']:+.3f}" if r['spearman_tr'] is not None else "  -"
            mark = "✓ 採用可" if is_survivor(r) else "✗ 採用不可"
            print(f"{pair:<10} {pct:>10} {thr:>12} {is_tr:>8} {oos_tr:>8} {rho:>8} {mark:>10}")
        else:
            print(f"{r['pair']:<10} {'-':>10} {'-':>12} {'-':>8} {'-':>8} {'-':>8} ✗ 採用不可")

    # JSON 保存
    out_payload = {
        "config": {
            "percentiles": PERCENTILES,
            "min_sample": MIN_SAMPLE,
            "lookahead_bars": LOOKAHEAD_BARS,
            "is_ratio": IS_RATIO,
        },
        "results": [
            {
                "pair": r["pair"],
                "rows": r["rows"],
                "spearman_tr": r["spearman_tr"],
                "spearman_dpr": r["spearman_dpr"],
                "best_eligible": r["best_eligible"],
                "survivor": is_survivor(r),
            }
            for r in all_results
        ],
    }
    out_json = data_dir / f"spec_2_1_yz_vol_revalidation_{_TF}_{_YEARS}y.json"
    out_json.write_text(json.dumps(out_payload, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
