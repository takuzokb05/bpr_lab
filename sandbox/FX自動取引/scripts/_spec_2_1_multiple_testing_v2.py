"""SPEC v2 - 2-1: Multiple Testing v2 — CHOP <25 を加えた 15-family 多重補正 (P1-A / Q3)

## v1 からの変更点
- ADOPTED_THRESHOLDS に CHOP <25 を 3 ペア追加 (合計 15 閾値)
- Romano-Wolf を 15-family に拡張 (旧 12-family)
- Bonferroni N=606 は不変 (CHOP <25 は P0-1 棚卸しの indicator_screening CHOP_GRID に含まれる)

## 検証する問い
P1-1b (Mode B WFA) で「真に頑健 (CV<0.1) なのは 2 件のみ: EUR_USD/GBP_JPY M15 CHOP <25」と判明。
v1 の Mode A 値は <30/35 だったので、P0-3 (v1) では <25 が補正対象に入っていなかった。

このスクリプトで CHOP <25 を多重補正下で評価し:
- Bonferroni N=606 通過 → AAA 級採用候補として復活、SPEC v2 § 2-1 に追記
- Bonferroni 棄却・Romano-Wolf 通過 → A クラスへ降格、保留
- 両方棄却 → CHOP は M15 補完層から外す方向

## 出力
- data/spec_2_1_multiple_testing_v2.json
- 標準出力: 15 閾値の補正後 p 値 + 判定

## 使用例
  python scripts/_spec_2_1_multiple_testing_v2.py --n_perm 20000
"""
from __future__ import annotations

import argparse
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
import pandas_ta as ta

ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("spec_2_1_multiple_testing_v2")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}
IS_RATIO = 0.75
N_TOTAL_TRIALS = 606  # P0-1 棚卸し結果 (CHOP <25 は indicator_screening CHOP_GRID に含まれる)

# 採用済み閾値 v2 (12 + CHOP <25 × 3 = 15)
ADOPTED_THRESHOLDS = [
    # M15 YZ_vol (window=14, percentile-based)
    ("USD_JPY", "M15", "YZ_vol", 14, "gt", 30, "pct", 2),
    ("EUR_USD", "M15", "YZ_vol", 14, "gt", 80, "pct", 2),
    ("GBP_JPY", "M15", "YZ_vol", 14, "gt", 30, "pct", 2),
    # M15 CHOP (length=14, absolute threshold) — Mode A 値 (旧)
    ("USD_JPY", "M15", "CHOP", 14, "lt", 35, "abs", 2),
    ("EUR_USD", "M15", "CHOP", 14, "lt", 30, "abs", 2),
    ("GBP_JPY", "M15", "CHOP", 14, "lt", 30, "abs", 2),
    # M15 CHOP <25 (length=14, absolute threshold) — Mode B v2 で頑健と判明 (新規追加)
    ("USD_JPY", "M15", "CHOP", 14, "lt", 25, "abs", 2),
    ("EUR_USD", "M15", "CHOP", 14, "lt", 25, "abs", 2),
    ("GBP_JPY", "M15", "CHOP", 14, "lt", 25, "abs", 2),
    # H1 YZ_vol (window=20, absolute threshold)
    ("USD_JPY", "H1", "YZ_vol", 20, "gt", 0.00174, "abs", 5),
    ("EUR_USD", "H1", "YZ_vol", 20, "gt", 0.00143, "abs", 5),
    ("GBP_JPY", "H1", "YZ_vol", 20, "gt", 0.00175, "abs", 5),
    # D1 YZ_vol (window=20, percentile-based)
    ("USD_JPY", "D1", "YZ_vol", 20, "gt", 50, "pct", 10),
    ("EUR_USD", "D1", "YZ_vol", 20, "gt", 75, "pct", 10),
    ("GBP_JPY", "D1", "YZ_vol", 20, "gt", 55, "pct", 10),
]


# ============================================================
# 指標計算 (v1 と同じ)
# ============================================================
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
    return out


def split_is_oos(df: pd.DataFrame, ratio: float = IS_RATIO):
    n = len(df)
    split_idx = int(n * ratio)
    return df.iloc[:split_idx], df.iloc[split_idx:]


def compute_tr_fast(future_return: np.ndarray, indicator: np.ndarray,
                    threshold: float, comparison: str) -> float:
    if comparison == "gt":
        mask_high = indicator > threshold
    else:
        mask_high = indicator < threshold
    n_high = mask_high.sum()
    n_low = (~mask_high).sum()
    if n_high == 0 or n_low == 0:
        return np.nan
    median_high = np.median(np.abs(future_return[mask_high]))
    median_low = np.median(np.abs(future_return[~mask_high]))
    if median_low <= 0:
        return np.nan
    return median_high / median_low


def run_permutation_for_threshold(
    pair: str, tf: str, indicator_name: str, param: int,
    comparison: str, threshold_spec, threshold_kind: str,
    years: int, n_perm: int, seed: int,
) -> dict:
    csv_path = ROOT / "data" / f"mt5_{pair}_{tf}_{years}y.csv"
    if not csv_path.exists():
        return {"error": f"missing csv: {csv_path}"}

    df = load_csv(csv_path)
    if indicator_name == "YZ_vol":
        indicator = calc_yang_zhang(df, window=param)
    elif indicator_name == "CHOP":
        indicator = calc_chop(df, length=param)
    else:
        return {"error": f"unknown indicator: {indicator_name}"}

    df_ret = add_returns(df, LOOKAHEAD[tf])
    aligned = pd.concat([df_ret[["future_return"]], indicator.rename("ind")], axis=1).dropna()
    _is_df, oos_df = split_is_oos(aligned, IS_RATIO)

    fr_arr = oos_df["future_return"].values
    ind_arr = oos_df["ind"].values

    if threshold_kind == "pct":
        threshold_value = float(np.percentile(ind_arr, threshold_spec))
    else:
        threshold_value = float(threshold_spec)

    obs_tr = compute_tr_fast(fr_arr, ind_arr, threshold_value, comparison)

    rng = np.random.default_rng(seed)
    null_trs = np.empty(n_perm)
    for i in range(n_perm):
        shuffled = rng.permutation(ind_arr)
        null_trs[i] = compute_tr_fast(fr_arr, shuffled, threshold_value, comparison)

    null_trs_clean = null_trs[~np.isnan(null_trs)]

    return {
        "pair": pair, "tf": tf, "indicator": indicator_name, "param": param,
        "comparison": comparison, "threshold_spec": threshold_spec,
        "threshold_kind": threshold_kind, "threshold_value": threshold_value,
        "obs_tr": obs_tr,
        "null_trs": null_trs_clean,
        "n_null_valid": len(null_trs_clean),
    }


def bonferroni_correction(p_raw: float, n_total: int) -> float:
    return min(1.0, p_raw * n_total)


def holm_step_down(p_values: list[float], n_total: int) -> list[float]:
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    p_holm = [None] * n
    max_so_far = 0.0
    for rank, (orig_idx, p) in enumerate(indexed, start=1):
        adj = p * (n_total - rank + 1)
        adj = min(1.0, max(adj, max_so_far))
        max_so_far = adj
        p_holm[orig_idx] = adj
    return p_holm


def romano_wolf_family(obs_trs: np.ndarray, null_trs_matrix: np.ndarray) -> np.ndarray:
    """Romano-Wolf step-down family補正 (15-family or arbitrary size)"""
    n_trials, n_perm = null_trs_matrix.shape
    indexed = sorted(enumerate(obs_trs), key=lambda x: -x[1])
    p_rw = np.empty(n_trials)
    remaining_trials = list(range(n_trials))
    last_p = 0.0
    for orig_idx, obs in indexed:
        if not remaining_trials:
            p_rw[orig_idx] = last_p
            continue
        sub_null_max = null_trs_matrix[remaining_trials, :].max(axis=0)
        p = float((sub_null_max >= obs).mean())
        p = max(p, last_p)
        p_rw[orig_idx] = p
        last_p = p
        remaining_trials.remove(orig_idx)
    return p_rw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_perm", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    n_family = len(ADOPTED_THRESHOLDS)
    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 Multiple Testing v2 ({n_family}-family / CHOP <25 追加)")
    print(f"  n_perm = {args.n_perm}, seed = {args.seed}")
    print(f"  N_TOTAL_TRIALS = {N_TOTAL_TRIALS}")
    print(f"  Bonferroni 厳密境界: α=0.05/{N_TOTAL_TRIALS} = {0.05/N_TOTAL_TRIALS:.2e}")
    print(f"  対象: {n_family} 閾値 (旧 12 + CHOP <25 × 3)")
    print(f"{'=' * 130}")

    raw_results = []
    for spec in ADOPTED_THRESHOLDS:
        pair, tf, ind_name, param, comp, thr_spec, thr_kind, years = spec
        print(f"\n--- {pair} / {tf} / {ind_name}({param}) {comp} {thr_spec}({thr_kind}) ---")
        r = run_permutation_for_threshold(
            pair, tf, ind_name, param, comp, thr_spec, thr_kind, years,
            args.n_perm, args.seed,
        )
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue

        null_trs = r["null_trs"]
        obs_tr = r["obs_tr"]
        p_raw = float((null_trs >= obs_tr).mean()) if not np.isnan(obs_tr) else None

        if p_raw is not None:
            print(f"  OBS_TR = {obs_tr:.4f}")
            print(f"  null: mean={null_trs.mean():.4f}, std={null_trs.std():.4f}, "
                  f"p99={np.percentile(null_trs, 99):.4f}, max={null_trs.max():.4f}")
            print(f"  p_raw = {p_raw:.6f}")

        raw_results.append({
            "spec": spec,
            "obs_tr": obs_tr,
            "p_raw": p_raw,
            "null_trs": null_trs,
        })

    print(f"\n{'=' * 130}")
    print(f"多重補正の適用 ({n_family}-family)")
    print(f"{'=' * 130}")

    n_perm_min = min(len(r["null_trs"]) for r in raw_results)
    null_matrix = np.array([r["null_trs"][:n_perm_min] for r in raw_results])
    obs_trs_arr = np.array([r["obs_tr"] for r in raw_results])

    p_raws = [r["p_raw"] for r in raw_results]
    p_bonf_606 = [bonferroni_correction(p, N_TOTAL_TRIALS) for p in p_raws]
    p_holm_606 = holm_step_down(p_raws, N_TOTAL_TRIALS)
    p_holm_15 = holm_step_down(p_raws, len(p_raws))
    p_rw_15 = romano_wolf_family(obs_trs_arr, null_matrix)

    print(f"\n{'Pair':<8} {'TF':<5} {'Ind':<8} {'閾値':<10} {'OBS_TR':>8} {'p_raw':>10} "
          f"{'p_bonf_606':>11} {'p_holm_606':>11} {'p_holm_15':>10} {'p_rw_15':>9} {'判定':>20}")
    print("-" * 145)

    final_results = []
    for i, r in enumerate(raw_results):
        spec = r["spec"]
        pair, tf, ind_name, _, _, thr_spec, thr_kind, _ = spec
        thr_disp = f"{thr_spec}{thr_kind}"

        p_b = p_bonf_606[i]
        p_rw = p_rw_15[i]
        if p_b < 0.05:
            v = "🟢 全補正で生存"
        elif p_rw < 0.05:
            v = f"🟡 {n_family}-family のみ生存"
        else:
            v = "🔴 全補正で棄却"

        print(f"{pair:<8} {tf:<5} {ind_name:<8} {thr_disp:<10} "
              f"{r['obs_tr']:>8.4f} {r['p_raw']:>10.6f} "
              f"{p_b:>11.6f} {p_holm_606[i]:>11.6f} "
              f"{p_holm_15[i]:>10.6f} {p_rw:>9.6f} {v:>20}")

        final_results.append({
            "pair": pair, "tf": tf, "indicator": ind_name,
            "threshold_spec": thr_spec, "threshold_kind": thr_kind,
            "obs_tr": r["obs_tr"],
            "p_raw": r["p_raw"],
            "p_bonferroni_606": p_b,
            "p_holm_606": p_holm_606[i],
            "p_holm_family": p_holm_15[i],
            "p_rw_family": float(p_rw),
            "verdict": v,
        })

    out_json = ROOT / "data" / "spec_2_1_multiple_testing_v2.json"
    out_json.write_text(json.dumps({
        "config": {
            "n_perm": args.n_perm,
            "n_total_trials": N_TOTAL_TRIALS,
            "n_family": n_family,
            "bonferroni_alpha": 0.05 / N_TOTAL_TRIALS,
        },
        "results": final_results,
    }, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
