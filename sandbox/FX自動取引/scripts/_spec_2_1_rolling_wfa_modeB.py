"""SPEC v2 - 2-1: Mode B 閾値再選定 WFA (Step C P1-1b)

各 fold IS で最良閾値を再選定し、fold 間ドリフトを測定。
P1-1 Mode A (閾値固定) で生じた複数のねじれの本質に接近する。

## 検証する具体的な問い
- A クラス 3閾値 (Bonferroni 棄却 / WFA 5/5) — fold 間で同じ閾値が選ばれるか?
- EUR_USD M15 CHOP (P0-3🔴 / WFA 5/5) — 最良閾値が <30 で安定すれば「偶然連続説」を一部排除
- EUR_USD H1 fold 3 クラッシュ — fold 3 IS で別の最良閾値が出るか? = 閾値不適合説の検証
- D1 USD/GBP (Bonferroni 棄却 / WFA 5/5) — fold 間ドリフトの大小

## fold 設計
P1-1 Mode A と同じ anchored expanding 5-fold:
- fold k: IS [0, k/6], OOS [k/6, (k+1)/6], k=1..5

## 各 fold での閾値再選定
1. IS 区間で指標 (YZ_vol または CHOP) を計算
2. 候補グリッド全体で IS_TR を計測
3. n_high >= MIN_SAMPLE_IS の制約下で **IS_TR 最大の閾値**を「fold k の最良閾値」とする
4. その最良閾値を OOS 区間で評価 → OOS_TR

## 候補グリッド
- YZ_vol (percentile-based): {10, 20, 30, 40, 50, 60, 70, 80, 90}
- YZ_vol (abs-based, H1): SPEC値 を中心に対数等間隔の 9点 (例: 0.0010 ~ 0.0030)
- CHOP (abs-based): {25, 28, 30, 33, 35, 38, 40, 45, 50}

## 集計指標
各閾値スペックについて:
- 各 fold の最良閾値 (絶対値 or percentile)
- 各 fold の IS_TR / OOS_TR / n_high
- 閾値 CV = std / mean — **fold 間ドリフトの指標**
- 全 fold で同じ閾値が選ばれた率
- Mode A 固定値からの乖離 (再選定閾値 vs 固定閾値)

## ドリフト判定
- 閾値 CV < 0.1 → **強い頑健性** (Mode A と Mode B でほぼ一致、ねじれは別要因)
- 0.1 ≤ CV < 0.3 → 中程度ドリフト
- CV >= 0.3 → **カーブフィット疑い** (時期依存で「最良」が変動)

## 出力
- data/spec_2_1_rolling_wfa_modeB.json
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
log = logging.getLogger("spec_2_1_rolling_wfa_modeB")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}
N_FOLDS = 5
MIN_SAMPLE_IS = 50
MIN_SAMPLE_OOS = 30  # OOS は IS より緩く

# 候補グリッド
YZ_PCT_GRID = [10, 20, 30, 40, 50, 60, 70, 80, 90]
CHOP_ABS_GRID = [25, 28, 30, 33, 35, 38, 40, 45, 50]
# H1 YZ_vol abs グリッドは SPEC 値ごとに対数等間隔で再構築 (run 内で生成)


# 採用済み閾値スペック (P0-3 と同じ + Mode A 採用値)
# (pair, tf, indicator, length/window, comparison, mode_a_threshold_value, threshold_kind, years, p0_3_class)
ADOPTED_SPECS = [
    ("USD_JPY", "M15", "YZ_vol", 14, "gt", 30, "pct", 2, "AA"),
    ("EUR_USD", "M15", "YZ_vol", 14, "gt", 80, "pct", 2, "AAA"),
    ("GBP_JPY", "M15", "YZ_vol", 14, "gt", 30, "pct", 2, "AAA"),
    ("USD_JPY", "M15", "CHOP", 14, "lt", 35, "abs", 2, "AA"),
    ("EUR_USD", "M15", "CHOP", 14, "lt", 30, "abs", 2, "🔴"),
    ("GBP_JPY", "M15", "CHOP", 14, "lt", 30, "abs", 2, "A"),
    ("USD_JPY", "H1", "YZ_vol", 20, "gt", 0.00174, "abs", 5, "AAA"),
    ("EUR_USD", "H1", "YZ_vol", 20, "gt", 0.00143, "abs", 5, "AAA"),
    ("GBP_JPY", "H1", "YZ_vol", 20, "gt", 0.00175, "abs", 5, "AAA"),
    ("USD_JPY", "D1", "YZ_vol", 20, "gt", 50, "pct", 10, "A"),
    ("EUR_USD", "D1", "YZ_vol", 20, "gt", 75, "pct", 10, "🔴"),
    ("GBP_JPY", "D1", "YZ_vol", 20, "gt", 55, "pct", 10, "A"),
]


# ============================================================
# 指標計算 (P1-1 と同じ)
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


def compute_tr(df: pd.DataFrame, threshold: float, comparison: str) -> dict:
    """df は ind, future_return 列を含む (NaN 除外済み前提)"""
    if comparison == "gt":
        mask_high = df["ind"] > threshold
    else:
        mask_high = df["ind"] < threshold

    n_high = int(mask_high.sum())
    n_low = int((~mask_high).sum())
    if n_high == 0 or n_low == 0:
        return {"n_high": n_high, "tr": None}

    median_high = float(np.median(np.abs(df.loc[mask_high, "future_return"].values)))
    median_low = float(np.median(np.abs(df.loc[~mask_high, "future_return"].values)))
    if median_low <= 0:
        return {"n_high": n_high, "tr": None}
    return {"n_high": n_high, "tr": median_high / median_low}


def make_abs_grid(center: float, n_points: int = 9, span_factor: float = 0.5) -> list[float]:
    """中心値の周りに対数等間隔のグリッドを生成。
    span_factor=0.5 なら center * 0.5 〜 center * 1.5 の範囲 (実質的には対数で均等)。
    n_points は奇数推奨 (中心値が含まれる)。
    """
    log_center = np.log(center)
    half_span = np.log(1 + span_factor)
    log_grid = np.linspace(log_center - half_span, log_center + half_span, n_points)
    return [float(np.exp(x)) for x in log_grid]


# ============================================================
# Mode B WFA
# ============================================================
def run_modeB_wfa(
    pair: str, tf: str, indicator_name: str, param: int,
    comparison: str, mode_a_threshold: float, threshold_kind: str, years: int,
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

    n = len(aligned)
    fold_size = n // (N_FOLDS + 1)

    # 候補グリッド準備
    if indicator_name == "YZ_vol":
        if threshold_kind == "pct":
            grid_specs = [(p, "pct") for p in YZ_PCT_GRID]
        else:  # abs (H1)
            grid_specs = [(v, "abs") for v in make_abs_grid(mode_a_threshold, 9, 0.5)]
    elif indicator_name == "CHOP":
        grid_specs = [(v, "abs") for v in CHOP_ABS_GRID]

    fold_results = []
    for k in range(1, N_FOLDS + 1):
        is_end = k * fold_size
        oos_end = (k + 1) * fold_size if k < N_FOLDS else n
        is_df = aligned.iloc[:is_end]
        oos_df = aligned.iloc[is_end:oos_end]

        if len(is_df) == 0 or len(oos_df) == 0:
            fold_results.append({"fold": k, "error": "empty"})
            continue

        # 各候補で IS_TR を計測 → 最良閾値を選定
        best = None
        all_eval = []
        for grid_val, grid_kind in grid_specs:
            if grid_kind == "pct":
                threshold = float(np.percentile(is_df["ind"].values, grid_val))
            else:
                threshold = float(grid_val)

            is_eval = compute_tr(is_df, threshold, comparison)
            all_eval.append({
                "grid_value": grid_val, "grid_kind": grid_kind,
                "threshold": threshold,
                "is_n_high": is_eval["n_high"], "is_tr": is_eval["tr"],
            })

            if is_eval["tr"] is None or is_eval["n_high"] < MIN_SAMPLE_IS:
                continue
            if best is None or is_eval["tr"] > best["is_tr"]:
                best = {
                    "grid_value": grid_val, "grid_kind": grid_kind,
                    "threshold": threshold,
                    "is_n_high": is_eval["n_high"], "is_tr": is_eval["tr"],
                }

        if best is None:
            fold_results.append({"fold": k, "error": "no IS candidate meets criteria"})
            continue

        # 最良閾値で OOS を評価
        oos_eval = compute_tr(oos_df, best["threshold"], comparison)
        fold_results.append({
            "fold": k,
            "is_period": [str(is_df.index.min()), str(is_df.index.max())],
            "oos_period": [str(oos_df.index.min()), str(oos_df.index.max())],
            "best_grid_value": best["grid_value"],
            "best_grid_kind": best["grid_kind"],
            "best_threshold": best["threshold"],
            "is_n_high": best["is_n_high"],
            "is_tr": best["is_tr"],
            "oos_n_high": oos_eval["n_high"],
            "oos_tr": oos_eval["tr"],
            "all_eval": all_eval,
        })

    # 集計: fold 間ドリフト
    valid_folds = [f for f in fold_results if "error" not in f]
    if not valid_folds:
        return {"error": "no valid folds"}

    grid_values = [f["best_grid_value"] for f in valid_folds]
    thresholds = [f["best_threshold"] for f in valid_folds]
    is_trs = [f["is_tr"] for f in valid_folds]
    oos_trs = [f["oos_tr"] for f in valid_folds if f["oos_tr"] is not None]

    threshold_mean = float(np.mean(thresholds))
    threshold_std = float(np.std(thresholds, ddof=1)) if len(thresholds) > 1 else 0.0
    threshold_cv = threshold_std / threshold_mean if threshold_mean != 0 else None

    n_pass_oos = sum(1 for tr in oos_trs if tr > 1.0)

    # ドリフト判定
    if threshold_cv is not None:
        if threshold_cv < 0.1:
            drift_judgment = "🟢 強い頑健性 (CV<0.1)"
        elif threshold_cv < 0.3:
            drift_judgment = "🟡 中程度ドリフト (0.1≤CV<0.3)"
        else:
            drift_judgment = "🔴 カーブフィット疑い (CV≥0.3)"
    else:
        drift_judgment = "計算不能"

    # Mode A 固定値との乖離
    mode_a_in_modeB = sum(1 for gv in grid_values if gv == mode_a_threshold)
    mode_a_match_rate = mode_a_in_modeB / len(valid_folds)

    return {
        "pair": pair, "tf": tf, "indicator": indicator_name,
        "param": param, "comparison": comparison,
        "mode_a_threshold": mode_a_threshold,
        "mode_a_threshold_kind": threshold_kind,
        "fold_results": fold_results,
        "best_grid_values_per_fold": grid_values,
        "thresholds_per_fold": thresholds,
        "threshold_mean": threshold_mean,
        "threshold_std": threshold_std,
        "threshold_cv": threshold_cv,
        "is_tr_mean": float(np.mean(is_trs)),
        "oos_tr_mean": float(np.mean(oos_trs)) if oos_trs else None,
        "oos_tr_min": float(min(oos_trs)) if oos_trs else None,
        "oos_tr_max": float(max(oos_trs)) if oos_trs else None,
        "n_pass_oos": n_pass_oos,
        "n_total_folds": len(valid_folds),
        "drift_judgment": drift_judgment,
        "mode_a_match_rate": mode_a_match_rate,
    }


# ============================================================
# メイン
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 Mode B 閾値再選定 WFA (Step C P1-1b)")
    print(f"  N_FOLDS = {N_FOLDS} (anchored expanding)")
    print(f"  MIN_SAMPLE_IS = {MIN_SAMPLE_IS}")
    print(f"  YZ_PCT_GRID = {YZ_PCT_GRID}")
    print(f"  CHOP_ABS_GRID = {CHOP_ABS_GRID}")
    print(f"  H1 YZ_vol abs グリッド: SPEC値の対数等間隔 9点 (±50%)")
    print(f"  対象: 採用済み {len(ADOPTED_SPECS)} 閾値")
    print(f"{'=' * 130}")

    results = []
    for spec in ADOPTED_SPECS:
        pair, tf, ind_name, param, comp, mode_a_thr, thr_kind, years, p0_3_class = spec
        print(f"\n--- {pair} / {tf} / {ind_name}({param}) {comp} (Mode A: {mode_a_thr}{thr_kind}, P0-3 {p0_3_class}) ---")
        r = run_modeB_wfa(pair, tf, ind_name, param, comp, mode_a_thr, thr_kind, years)
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        r["p0_3_class"] = p0_3_class
        results.append(r)

        # fold ごとの最良閾値を表示
        print(f"  {'fold':<5} {'best_grid':>10} {'threshold':>12} {'IS_n':>6} {'IS_TR':>7} {'OOS_n':>7} {'OOS_TR':>7}")
        for f in r["fold_results"]:
            if "error" in f:
                print(f"  {f['fold']:<5}  ERROR: {f['error']}")
                continue
            grid_disp = f"{f['best_grid_value']}{f['best_grid_kind']}"
            thr_s = f"{f['best_threshold']:.5f}"
            is_tr_s = f"{f['is_tr']:.3f}" if f["is_tr"] is not None else "  -"
            oos_tr_s = f"{f['oos_tr']:.3f}" if f["oos_tr"] is not None else "  -"
            mark = " ✓" if (f["oos_tr"] is not None and f["oos_tr"] > 1.0) else " ✗"
            print(f"  {f['fold']:<5} {grid_disp:>10} {thr_s:>12} {f['is_n_high']:>6} "
                  f"{is_tr_s:>7} {f['oos_n_high']:>7} {oos_tr_s:>7}{mark}")

        # 集計
        cv_s = f"{r['threshold_cv']:.3f}" if r['threshold_cv'] is not None else "-"
        oos_mean_s = f"{r['oos_tr_mean']:.3f}" if r['oos_tr_mean'] is not None else "-"
        print(f"  集計: 閾値 mean={r['threshold_mean']:.5f}, std={r['threshold_std']:.5f}, CV={cv_s}")
        print(f"        OOS_TR mean={oos_mean_s}, n_pass={r['n_pass_oos']}/{r['n_total_folds']}")
        print(f"        Mode A 値との一致率: {r['mode_a_match_rate']*100:.0f}% ({sum(1 for gv in r['best_grid_values_per_fold'] if gv == r['mode_a_threshold'])}/{r['n_total_folds']})")
        print(f"        ドリフト判定: {r['drift_judgment']}")

    # ============================================================
    # サマリ
    # ============================================================
    print(f"\n{'=' * 130}")
    print(f"Mode B WFA サマリ (P0-3 クラス × 閾値ドリフト × OOS 通過率)")
    print(f"{'=' * 130}")
    print(f"{'Pair':<8} {'TF':<5} {'指標':<8} {'Mode A':<10} {'P0-3':<6} "
          f"{'閾値CV':>7} {'IS_TR平均':>9} {'OOS_TR平均':>11} {'n_pass':>8} {'Mode一致':>9} {'ドリフト':<25}")
    print("-" * 130)
    for r in results:
        mode_a_disp = f"{r['mode_a_threshold']}{r['mode_a_threshold_kind']}"
        cv_s = f"{r['threshold_cv']:.3f}" if r['threshold_cv'] is not None else "-"
        is_tr_s = f"{r['is_tr_mean']:.3f}"
        oos_tr_s = f"{r['oos_tr_mean']:.3f}" if r['oos_tr_mean'] is not None else "-"
        match_s = f"{r['mode_a_match_rate']*100:.0f}%"
        print(f"{r['pair']:<8} {r['tf']:<5} {r['indicator']:<8} {mode_a_disp:<10} {r['p0_3_class']:<6} "
              f"{cv_s:>7} {is_tr_s:>9} {oos_tr_s:>11} {r['n_pass_oos']}/{r['n_total_folds']:<6} "
              f"{match_s:>9} {r['drift_judgment']:<25}")

    out_json = ROOT / "data" / "spec_2_1_rolling_wfa_modeB.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
