"""SPEC v2 - 2-1: H1 YZ_vol 実用性検証 WFA (Karen レビュー対応)

## 背景
Q2 で「SPEC × 2.0 が新最良」と書いたが、Karen レビューで:
- EUR_USD ×2.0 で n_high=123 / 5 年 → 5 fold で 1 fold ≈ 24-25
- MIN_SAMPLE_IS=50 を確実に下回る fold が発生する
と指摘。Q2 ドキュメントは「採用候補」と書いたが、実用性は未検証。

## 検証内容
H1 YZ_vol を SPEC × {1.0, 1.5, 2.0, 2.5} で **固定** (Mode A 風) し、
anchored expanding 5-fold WFA を実行。

各 fold で:
- IS の n_high が MIN_SAMPLE_IS=50 を超えるか?
- IS_TR / OOS_TR は安定か?
- どの倍率が「実用上の最良」か (TR の高さ + fold 安定性のトレードオフ)

## 評価指標
- n_pass: OOS_TR > 1.0 を満たす fold 数
- usable_folds: IS_n_high >= MIN_SAMPLE_IS を満たす fold 数 (これが 5 未満なら実用不可)
- TR の fold 間 CV (時期分散)

## TR 評価式
Q2 / Mode B v2 と同じ low 群固定方式 (25-50%ile)。
threshold が 50%ile より十分高い ×1.0 以上では high と low は完全排他。

## 出力
- data/spec_2_1_h1_practical_wfa.json
- 標準出力: 各倍率の fold 別評価 + サマリ表

## 使用例
  python scripts/_spec_2_1_h1_practical_wfa.py
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

ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("spec_2_1_h1_practical_wfa")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD_H1 = 6
WINDOW_YZ = 20
N_FOLDS = 5
MIN_SAMPLE_IS = 50
MIN_SAMPLE_OOS = 30
LOW_PCT_RANGE = (25, 50)

H1_SPECS = [
    ("USD_JPY", 0.00174),
    ("EUR_USD", 0.00143),
    ("GBP_JPY", 0.00175),
]

MULTIPLIERS = [1.0, 1.5, 2.0, 2.5]


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


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def add_returns(df: pd.DataFrame, lookahead: int) -> pd.DataFrame:
    out = df.copy()
    out["future_return"] = (out["close"].shift(-lookahead) - out["close"]) / out["close"]
    return out


def compute_tr_fixed_low(
    df: pd.DataFrame, threshold: float, low_pct_range: tuple[float, float],
) -> dict:
    low_lo, low_hi = low_pct_range
    low_v_lo = float(np.percentile(df["ind"].values, low_lo))
    low_v_hi = float(np.percentile(df["ind"].values, low_hi))

    mask_high = df["ind"] > threshold
    mask_low = (df["ind"] >= low_v_lo) & (df["ind"] <= low_v_hi)

    n_high = int(mask_high.sum())
    n_low = int(mask_low.sum())
    if n_high == 0 or n_low == 0:
        return {"n_high": n_high, "n_low": n_low, "tr": None}

    median_high = float(np.median(df.loc[mask_high, "abs_return"].values))
    median_low = float(np.median(df.loc[mask_low, "abs_return"].values))
    if median_low <= 0:
        return {"n_high": n_high, "n_low": n_low, "tr": None}
    return {
        "n_high": n_high, "n_low": n_low,
        "median_high": median_high, "median_low": median_low,
        "tr": median_high / median_low,
    }


# ============================================================
# 固定閾値 WFA
# ============================================================
def run_fixed_threshold_wfa(
    pair: str, spec_value: float, multiplier: float,
) -> dict:
    csv_path = ROOT / "data" / f"mt5_{pair}_H1_5y.csv"
    if not csv_path.exists():
        return {"error": f"missing csv: {csv_path}"}

    df = load_csv(csv_path)
    indicator = calc_yang_zhang(df, window=WINDOW_YZ)
    df_ret = add_returns(df, LOOKAHEAD_H1)
    aligned = pd.concat([df_ret[["future_return"]], indicator.rename("ind")], axis=1).dropna()
    aligned = aligned.copy()
    aligned["abs_return"] = aligned["future_return"].abs()

    n = len(aligned)
    fold_size = n // (N_FOLDS + 1)
    threshold = spec_value * multiplier

    fold_results = []
    for k in range(1, N_FOLDS + 1):
        is_end = k * fold_size
        oos_end = (k + 1) * fold_size if k < N_FOLDS else n
        is_df = aligned.iloc[:is_end]
        oos_df = aligned.iloc[is_end:oos_end]

        is_eval = compute_tr_fixed_low(is_df, threshold, LOW_PCT_RANGE)
        oos_eval = compute_tr_fixed_low(oos_df, threshold, LOW_PCT_RANGE)

        usable = is_eval["n_high"] >= MIN_SAMPLE_IS

        fold_results.append({
            "fold": k,
            "is_period": [str(is_df.index.min()), str(is_df.index.max())],
            "oos_period": [str(oos_df.index.min()), str(oos_df.index.max())],
            "threshold": threshold,
            "is_n_high": is_eval["n_high"],
            "is_n_low": is_eval["n_low"],
            "is_tr": is_eval["tr"],
            "oos_n_high": oos_eval["n_high"],
            "oos_tr": oos_eval["tr"],
            "usable_is": usable,
        })

    # 集計
    is_trs = [f["is_tr"] for f in fold_results if f["is_tr"] is not None]
    oos_trs = [f["oos_tr"] for f in fold_results if f["oos_tr"] is not None]
    n_pass = sum(1 for tr in oos_trs if tr > 1.0)
    n_usable = sum(1 for f in fold_results if f["usable_is"])

    is_tr_cv = None
    if len(is_trs) > 1 and np.mean(is_trs) > 0:
        is_tr_cv = float(np.std(is_trs, ddof=1) / np.mean(is_trs))
    oos_tr_cv = None
    if len(oos_trs) > 1 and np.mean(oos_trs) > 0:
        oos_tr_cv = float(np.std(oos_trs, ddof=1) / np.mean(oos_trs))

    # 実用判定
    if n_usable < N_FOLDS:
        practical_judgment = f"🔴 IS サンプル不足 ({n_usable}/{N_FOLDS} fold のみ usable)"
    elif n_pass >= 4:
        practical_judgment = f"🟢 実用候補 ({n_pass}/{N_FOLDS} pass)"
    elif n_pass >= 3:
        practical_judgment = f"🟡 弱い実用性 ({n_pass}/{N_FOLDS} pass)"
    else:
        practical_judgment = f"🔴 不通過 ({n_pass}/{N_FOLDS} pass)"

    return {
        "pair": pair,
        "spec_value": spec_value,
        "multiplier": multiplier,
        "threshold": threshold,
        "n_total": n,
        "fold_results": fold_results,
        "is_tr_mean": float(np.mean(is_trs)) if is_trs else None,
        "is_tr_cv": is_tr_cv,
        "oos_tr_mean": float(np.mean(oos_trs)) if oos_trs else None,
        "oos_tr_cv": oos_tr_cv,
        "n_pass_oos": n_pass,
        "n_usable_is": n_usable,
        "practical_judgment": practical_judgment,
    }


# ============================================================
# メイン
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 H1 YZ_vol 実用性検証 (固定閾値 WFA)")
    print(f"  N_FOLDS={N_FOLDS}, MIN_SAMPLE_IS={MIN_SAMPLE_IS}, MIN_SAMPLE_OOS={MIN_SAMPLE_OOS}")
    print(f"  LOW_PCT_RANGE={LOW_PCT_RANGE}, MULTIPLIERS={MULTIPLIERS}")
    print(f"{'=' * 130}")

    all_results = []
    for pair, spec_value in H1_SPECS:
        for mult in MULTIPLIERS:
            print(f"\n--- {pair} × {mult:.1f} (threshold={spec_value*mult:.5f}) ---")
            r = run_fixed_threshold_wfa(pair, spec_value, mult)
            if "error" in r:
                print(f"  ERROR: {r['error']}")
                continue
            all_results.append(r)

            print(f"  {'fold':<5} {'IS_n_high':>10} {'IS_TR':>7} {'OOS_n_high':>11} {'OOS_TR':>7} {'usable':>7}")
            for f in r["fold_results"]:
                is_tr_s = f"{f['is_tr']:.3f}" if f['is_tr'] is not None else "  -"
                oos_tr_s = f"{f['oos_tr']:.3f}" if f['oos_tr'] is not None else "  -"
                usable_s = "✓" if f['usable_is'] else "✗"
                pass_mark = " ✓" if (f["oos_tr"] is not None and f["oos_tr"] > 1.0) else " ✗"
                print(f"  {f['fold']:<5} {f['is_n_high']:>10} {is_tr_s:>7} "
                      f"{f['oos_n_high']:>11} {oos_tr_s:>7}{pass_mark} {usable_s:>7}")

            is_cv_s = f"{r['is_tr_cv']:.3f}" if r['is_tr_cv'] is not None else "-"
            oos_cv_s = f"{r['oos_tr_cv']:.3f}" if r['oos_tr_cv'] is not None else "-"
            is_mean_s = f"{r['is_tr_mean']:.3f}" if r['is_tr_mean'] is not None else "-"
            oos_mean_s = f"{r['oos_tr_mean']:.3f}" if r['oos_tr_mean'] is not None else "-"
            print(f"  集計: IS_TR mean={is_mean_s} (CV={is_cv_s}), OOS_TR mean={oos_mean_s} (CV={oos_cv_s})")
            print(f"        n_pass={r['n_pass_oos']}/{N_FOLDS}, usable={r['n_usable_is']}/{N_FOLDS}")
            print(f"        判定: {r['practical_judgment']}")

    # サマリ
    print(f"\n{'=' * 140}")
    print(f"H1 YZ_vol 固定閾値 WFA サマリ")
    print(f"{'=' * 140}")
    print(f"{'Pair':<8} {'×':>4} {'閾値':>10} "
          f"{'IS_TR':>7} {'IS_CV':>6} {'OOS_TR':>7} {'OOS_CV':>6} "
          f"{'usable':>7} {'pass':>5}  判定")
    print("-" * 140)
    for r in all_results:
        is_cv = f"{r['is_tr_cv']:.3f}" if r['is_tr_cv'] is not None else "-"
        oos_cv = f"{r['oos_tr_cv']:.3f}" if r['oos_tr_cv'] is not None else "-"
        is_tr = f"{r['is_tr_mean']:.3f}" if r['is_tr_mean'] is not None else "-"
        oos_tr = f"{r['oos_tr_mean']:.3f}" if r['oos_tr_mean'] is not None else "-"
        print(f"{r['pair']:<8} {r['multiplier']:>4.1f} {r['threshold']:>10.5f} "
              f"{is_tr:>7} {is_cv:>6} {oos_tr:>7} {oos_cv:>6} "
              f"{r['n_usable_is']}/{N_FOLDS:<3} {r['n_pass_oos']}/{N_FOLDS:<3} "
              f"{r['practical_judgment']}")

    out_json = ROOT / "data" / "spec_2_1_h1_practical_wfa.json"
    out_json.write_text(json.dumps(all_results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
