"""SPEC v2 - 2-1: Mode B 閾値再選定 WFA v2 — Q1↔Q2 論理断絶を塞ぐ介入実験

## 背景
P1-1b (Mode B v1) で 12 中 11 の閾値が Mode A 値と不一致 → 物語破棄条項発火。
Q1 v1 で「TR 評価式 (旧式) の low 群サイズ感度が真因」と仮説立てたが、
これは介入実験で検証していなかった (analyst レビューが指摘した論理断絶)。

## 介入の内容
旧 TR (Mode B v1):
    high = (ind > threshold), low = (ind <= threshold)
    TR_old = median(|ret|_high) / median(|ret|_low)
    → threshold で low 群サイズと内容が変動 → サンプル感度問題が発生

新 TR (Mode B v2 = Q2 で採用した方式):
    high = (ind > threshold)
    low  = 全分布の 25-50%ile 帯 (threshold によらず固定)
    TR_new = median(|ret|_high) / median(|ret|_low_fixed)

注意: threshold が 25%ile 以下になると high ⊃ low となり TR が 1 に近づく
(これは threshold を低く取ることへの自然なペナルティ — 二極化抑制効果)。

## 検定する論理
- Mode B v1 で観察した「閾値が 10%ile / 90%ile に二極化」現象が
  Mode B v2 (low 群固定) で **解消** するか?
  - 解消する → TR 評価式の low 群感度が真因確定 (Q1 仮説支持)
  - 解消しない → 別の真因がある (例: Q1 v2 で示唆された U字成分による低ボラ側の真信号)
- Mode A 値との一致率が改善するか?
- 閾値 CV (時期間ドリフト) が小さくなるか?

## 出力
- data/spec_2_1_rolling_wfa_modeB_v2.json
- 標準出力: v1 vs v2 の対照表

## 使用例
  python scripts/_spec_2_1_rolling_wfa_modeB_v2.py
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
log = logging.getLogger("spec_2_1_rolling_wfa_modeB_v2")
log.setLevel(logging.INFO)


# ============================================================
# 設定 (Mode B v1 と同じ)
# ============================================================
LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}
N_FOLDS = 5
MIN_SAMPLE_IS = 50
MIN_SAMPLE_OOS = 30

YZ_PCT_GRID = [10, 20, 30, 40, 50, 60, 70, 80, 90]
CHOP_ABS_GRID = [25, 28, 30, 33, 35, 38, 40, 45, 50]

LOW_PCT_RANGE = (25, 50)  # 介入: low 群を固定

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
# 指標計算
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


def make_abs_grid(center: float, n_points: int = 9, span_factor: float = 0.5) -> list[float]:
    log_center = np.log(center)
    half_span = np.log(1 + span_factor)
    log_grid = np.linspace(log_center - half_span, log_center + half_span, n_points)
    return [float(np.exp(x)) for x in log_grid]


# ============================================================
# 介入: TR 評価式を low 群固定方式に変更
# ============================================================
def compute_tr_fixed_low(
    df: pd.DataFrame,  # ind, abs_return 列を含む (NaN 除外済み前提)
    threshold: float,
    comparison: str,
    low_pct_range: tuple[float, float],
) -> dict:
    """high: comparison & threshold の関係 / low: 固定 percentile 帯 (25-50%ile)"""
    if comparison == "gt":
        mask_high = df["ind"] > threshold
    else:  # lt
        mask_high = df["ind"] < threshold

    low_lo, low_hi = low_pct_range
    low_v_lo = float(np.percentile(df["ind"].values, low_lo))
    low_v_hi = float(np.percentile(df["ind"].values, low_hi))
    mask_low = (df["ind"] >= low_v_lo) & (df["ind"] <= low_v_hi)

    n_high = int(mask_high.sum())
    n_low = int(mask_low.sum())
    if n_high == 0 or n_low == 0:
        return {"n_high": n_high, "n_low": n_low, "tr": None,
                "low_range": [low_v_lo, low_v_hi]}

    median_high = float(np.median(np.abs(df.loc[mask_high, "abs_return"].values)))
    median_low = float(np.median(np.abs(df.loc[mask_low, "abs_return"].values)))
    if median_low <= 0:
        return {"n_high": n_high, "n_low": n_low, "tr": None,
                "low_range": [low_v_lo, low_v_hi]}
    return {
        "n_high": n_high, "n_low": n_low,
        "median_high": median_high, "median_low": median_low,
        "tr": median_high / median_low,
        "low_range": [low_v_lo, low_v_hi],
    }


# ============================================================
# Mode B v2 WFA
# ============================================================
def run_modeB_v2_wfa(
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
    aligned = aligned.copy()
    aligned["abs_return"] = aligned["future_return"].abs()

    n = len(aligned)
    fold_size = n // (N_FOLDS + 1)

    if indicator_name == "YZ_vol":
        if threshold_kind == "pct":
            grid_specs = [(p, "pct") for p in YZ_PCT_GRID]
        else:
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

        best = None
        all_eval = []
        for grid_val, grid_kind in grid_specs:
            if grid_kind == "pct":
                threshold = float(np.percentile(is_df["ind"].values, grid_val))
            else:
                threshold = float(grid_val)

            is_eval = compute_tr_fixed_low(is_df, threshold, comparison, LOW_PCT_RANGE)
            all_eval.append({
                "grid_value": grid_val, "grid_kind": grid_kind,
                "threshold": threshold,
                "is_n_high": is_eval["n_high"], "is_n_low": is_eval["n_low"],
                "is_tr": is_eval["tr"],
            })

            if is_eval["tr"] is None or is_eval["n_high"] < MIN_SAMPLE_IS:
                continue
            if best is None or is_eval["tr"] > best["is_tr"]:
                best = {
                    "grid_value": grid_val, "grid_kind": grid_kind,
                    "threshold": threshold,
                    "is_n_high": is_eval["n_high"], "is_n_low": is_eval["n_low"],
                    "is_tr": is_eval["tr"],
                }

        if best is None:
            fold_results.append({"fold": k, "error": "no IS candidate meets criteria"})
            continue

        oos_eval = compute_tr_fixed_low(oos_df, best["threshold"], comparison, LOW_PCT_RANGE)
        fold_results.append({
            "fold": k,
            "is_period": [str(is_df.index.min()), str(is_df.index.max())],
            "oos_period": [str(oos_df.index.min()), str(oos_df.index.max())],
            "best_grid_value": best["grid_value"],
            "best_grid_kind": best["grid_kind"],
            "best_threshold": best["threshold"],
            "is_n_high": best["is_n_high"],
            "is_n_low": best["is_n_low"],
            "is_tr": best["is_tr"],
            "oos_n_high": oos_eval["n_high"],
            "oos_n_low": oos_eval["n_low"],
            "oos_tr": oos_eval["tr"],
            "all_eval": all_eval,
        })

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

    if threshold_cv is not None:
        if threshold_cv < 0.1:
            drift_judgment = "🟢 強い頑健性 (CV<0.1)"
        elif threshold_cv < 0.3:
            drift_judgment = "🟡 中程度ドリフト (0.1≤CV<0.3)"
        else:
            drift_judgment = "🔴 カーブフィット疑い (CV≥0.3)"
    else:
        drift_judgment = "計算不能"

    def _approx_match(gv: float, ref: float) -> bool:
        if ref == 0:
            return gv == 0
        return abs(gv - ref) / abs(ref) < 1e-6

    mode_a_in_modeB = sum(1 for gv in grid_values if _approx_match(gv, mode_a_threshold))
    mode_a_match_rate = mode_a_in_modeB / len(valid_folds)

    # 二極化指標: 選択された percentile (or abs を percentile 換算) の標準偏差 / 中央性
    if threshold_kind == "pct":
        # percentile グリッドなので grid_values が直接 percentile
        pcts = grid_values
    else:
        # abs グリッドの場合、それぞれの threshold が分布上の何 percentile か算出
        pcts = []
        for f in valid_folds:
            pct_in_dist = float((aligned["ind"] <= f["best_threshold"]).mean() * 100)
            pcts.append(pct_in_dist)

    bipolarization_score = 0.0
    if len(pcts) > 0:
        # 二極化: |選択 - 50| の平均 (端寄りなら高い)
        bipolarization_score = float(np.mean([abs(p - 50) for p in pcts]))

    return {
        "pair": pair, "tf": tf, "indicator": indicator_name,
        "param": param, "comparison": comparison,
        "mode_a_threshold": mode_a_threshold,
        "mode_a_threshold_kind": threshold_kind,
        "fold_results": fold_results,
        "best_grid_values_per_fold": grid_values,
        "thresholds_per_fold": thresholds,
        "selected_percentiles": pcts,
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
        "bipolarization_score": bipolarization_score,
    }


# ============================================================
# メイン
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 Mode B v2 介入実験 (low 群固定方式 25-50%ile)")
    print(f"  N_FOLDS = {N_FOLDS}, MIN_SAMPLE_IS = {MIN_SAMPLE_IS}")
    print(f"  LOW_PCT_RANGE = {LOW_PCT_RANGE} (旧 v1 は threshold 連動)")
    print(f"  対象: 採用済み {len(ADOPTED_SPECS)} 閾値")
    print(f"{'=' * 130}")

    # v1 結果読み込み (比較用)
    v1_path = ROOT / "data" / "spec_2_1_rolling_wfa_modeB.json"
    v1_data = {}
    if v1_path.exists():
        v1_results = json.loads(v1_path.read_text(encoding="utf-8"))
        for r in v1_results:
            key = (r["pair"], r["tf"], r["indicator"])
            v1_data[key] = r

    results = []
    for spec in ADOPTED_SPECS:
        pair, tf, ind_name, param, comp, mode_a_thr, thr_kind, years, p0_3_class = spec
        print(f"\n--- {pair} / {tf} / {ind_name}({param}) {comp} (Mode A: {mode_a_thr}{thr_kind}) ---")
        r = run_modeB_v2_wfa(pair, tf, ind_name, param, comp, mode_a_thr, thr_kind, years)
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        r["p0_3_class"] = p0_3_class
        results.append(r)

        # v1 との比較表示
        v1 = v1_data.get((pair, tf, ind_name), {})

        print(f"  v2 best_grid_values: {r['best_grid_values_per_fold']}")
        if v1:
            print(f"  v1 best_grid_values: {v1.get('best_grid_values_per_fold', [])}")

        cv_s = f"{r['threshold_cv']:.3f}" if r['threshold_cv'] is not None else "-"
        v1_cv = v1.get('threshold_cv')
        v1_cv_s = f"{v1_cv:.3f}" if v1_cv is not None else "-"

        oos_mean_s = f"{r['oos_tr_mean']:.3f}" if r['oos_tr_mean'] is not None else "-"
        v1_oos = v1.get('oos_tr_mean')
        v1_oos_s = f"{v1_oos:.3f}" if v1_oos is not None else "-"

        print(f"  CV (v2/v1):           {cv_s} / {v1_cv_s}")
        print(f"  OOS_TR mean (v2/v1):  {oos_mean_s} / {v1_oos_s}")
        print(f"  n_pass (v2/v1):       {r['n_pass_oos']}/{r['n_total_folds']} / "
              f"{v1.get('n_pass_oos', '?')}/{v1.get('n_total_folds', '?')}")
        print(f"  Mode A 一致率 (v2/v1): {r['mode_a_match_rate']*100:.0f}% / "
              f"{v1.get('mode_a_match_rate', 0)*100:.0f}%")
        print(f"  二極化指標 (v2):     {r['bipolarization_score']:.1f} (0=完全中央 / 50=完全端)")
        print(f"  ドリフト判定 (v2):   {r['drift_judgment']}")

    # サマリ: v1 vs v2 対照
    print(f"\n{'=' * 140}")
    print(f"Mode B v1 vs v2 対照 (介入実験)")
    print(f"{'=' * 140}")
    print(f"{'Pair':<8} {'TF':<5} {'指標':<8} "
          f"{'v1 CV':>7} {'v2 CV':>7} "
          f"{'v1 一致':>7} {'v2 一致':>7} "
          f"{'v1 npass':>9} {'v2 npass':>9} "
          f"{'v2 二極化':>9}")
    print("-" * 140)
    for r in results:
        v1 = v1_data.get((r["pair"], r["tf"], r["indicator"]), {})
        v1_cv = v1.get('threshold_cv')
        v1_cv_s = f"{v1_cv:.3f}" if v1_cv is not None else "-"
        v2_cv_s = f"{r['threshold_cv']:.3f}" if r['threshold_cv'] is not None else "-"
        v1_match = f"{v1.get('mode_a_match_rate', 0)*100:.0f}%"
        v2_match = f"{r['mode_a_match_rate']*100:.0f}%"
        v1_npass = f"{v1.get('n_pass_oos', '?')}/{v1.get('n_total_folds', '?')}"
        v2_npass = f"{r['n_pass_oos']}/{r['n_total_folds']}"
        bipolar = f"{r['bipolarization_score']:.1f}"

        print(f"{r['pair']:<8} {r['tf']:<5} {r['indicator']:<8} "
              f"{v1_cv_s:>7} {v2_cv_s:>7} "
              f"{v1_match:>7} {v2_match:>7} "
              f"{v1_npass:>9} {v2_npass:>9} "
              f"{bipolar:>9}")

    out_json = ROOT / "data" / "spec_2_1_rolling_wfa_modeB_v2.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
