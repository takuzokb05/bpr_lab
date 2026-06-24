"""SPEC v2 - 2-1: 真因補強検証 (P1-B)

## 背景
Mode B v2 介入実験 (low 群固定方式) で M15 YZ_vol の二極化は劇的解消したが、
H1 YZ_vol abs グリッドと D1 YZ_vol pct グリッドでは閾値選定が変わらなかった。
「Mode B 二極化の真因 = TR 評価式 low 群感度」は M15 でのみ立証された状態。

## 検証する 3 候補
H1/D1 で介入が効かない理由を以下 3 候補で分離:

### 候補 b: グリッド設計依存 (最優先)
H1 YZ_vol abs グリッドは中心値 ± 50% (= ×0.5 〜 ×1.5)。
Q2 v1 で「真の最適は ×2.0 帯」と判明したので、**真の最適がグリッド外** =
「常にグリッド上限選定」の構造的アーティファクト。

検証: H1 YZ_vol を pct グリッド [80, 85, 90, 92.5, 95, 97.5, 99] で Mode B v2 再実行。
- pct グリッドなら「上限 99%ile」も「下限 80%ile」も両方ある = 構造的に上限選定が起きにくい
- それでも常に 99%ile が選ばれるなら真の最適がさらに外側 (Q2 v2 と整合)
- フラットに分布するなら abs グリッド設計が真因

### 候補 a: サンプル数依存 (検証)
M15 (50K) では二極化解消、H1 (30K) と D1 (1.4K) では解消せず。
サンプル数の差が真因かを検証。

検証: M15 YZ_vol をダウンサンプル (1/10 → 5K = H1 並み) して Mode B v2 再実行。
M15 でも二極化が再発するなら、サンプル数依存が真因。

### 候補 c: 自己相関構造 (確認のみ、本格検証は次回)
H1 / D1 はサンプル間自己相関が強く、permutation test の前提 (i.i.d.) が崩れる。
今回は時系列の autocorrelation を ACF(1), ACF(5) で計測し、M15 と比較するのみ。
本格的な block bootstrap は P1-C (新 Q4) で扱う。

## 出力
- data/spec_2_1_root_cause_analysis.json
- 標準出力: 候補 b/a/c の対照テーブル
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
log = logging.getLogger("spec_2_1_root_cause")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}
N_FOLDS = 5
MIN_SAMPLE_IS = 50
LOW_PCT_RANGE = (25, 50)

# H1 用 pct グリッド (右端寄り、Q2 v2 で発見した最適帯を含む)
H1_PCT_GRID = [80, 85, 90, 92.5, 95, 97.5, 99]


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
    df: pd.DataFrame, threshold: float, comparison: str,
    low_pct_range: tuple[float, float],
) -> dict:
    if comparison == "gt":
        mask_high = df["ind"] > threshold
    else:
        mask_high = df["ind"] < threshold

    low_lo, low_hi = low_pct_range
    low_v_lo = float(np.percentile(df["ind"].values, low_lo))
    low_v_hi = float(np.percentile(df["ind"].values, low_hi))
    mask_low = (df["ind"] >= low_v_lo) & (df["ind"] <= low_v_hi)

    n_high = int(mask_high.sum())
    n_low = int(mask_low.sum())
    if n_high == 0 or n_low == 0:
        return {"n_high": n_high, "n_low": n_low, "tr": None}

    median_high = float(np.median(df.loc[mask_high, "abs_return"].values))
    median_low = float(np.median(df.loc[mask_low, "abs_return"].values))
    if median_low <= 0:
        return {"n_high": n_high, "n_low": n_low, "tr": None}
    return {"n_high": n_high, "n_low": n_low, "tr": median_high / median_low}


# ============================================================
# 候補 b: H1 を pct グリッドで Mode B v2 再実行
# ============================================================
def run_modeB_v2_pct_grid(pair: str, years: int = 5) -> dict:
    """H1 YZ_vol を pct グリッドで Mode B v2 WFA"""
    csv_path = ROOT / "data" / f"mt5_{pair}_H1_{years}y.csv"
    if not csv_path.exists():
        return {"error": f"missing csv: {csv_path}"}

    df = load_csv(csv_path)
    indicator = calc_yang_zhang(df, window=20)
    df_ret = add_returns(df, LOOKAHEAD["H1"])
    aligned = pd.concat([df_ret[["future_return"]], indicator.rename("ind")], axis=1).dropna()
    aligned = aligned.copy()
    aligned["abs_return"] = aligned["future_return"].abs()

    n = len(aligned)
    fold_size = n // (N_FOLDS + 1)

    fold_results = []
    for k in range(1, N_FOLDS + 1):
        is_end = k * fold_size
        oos_end = (k + 1) * fold_size if k < N_FOLDS else n
        is_df = aligned.iloc[:is_end]
        oos_df = aligned.iloc[is_end:oos_end]

        best = None
        for pct in H1_PCT_GRID:
            threshold = float(np.percentile(is_df["ind"].values, pct))
            is_eval = compute_tr_fixed_low(is_df, threshold, "gt", LOW_PCT_RANGE)
            if is_eval["tr"] is None or is_eval["n_high"] < MIN_SAMPLE_IS:
                continue
            if best is None or is_eval["tr"] > best["is_tr"]:
                best = {
                    "pct": pct, "threshold": threshold,
                    "is_n_high": is_eval["n_high"], "is_tr": is_eval["tr"],
                }

        if best is None:
            fold_results.append({"fold": k, "error": "no candidate"})
            continue

        oos_eval = compute_tr_fixed_low(oos_df, best["threshold"], "gt", LOW_PCT_RANGE)
        fold_results.append({
            "fold": k, "best_pct": best["pct"], "threshold": best["threshold"],
            "is_n_high": best["is_n_high"], "is_tr": best["is_tr"],
            "oos_n_high": oos_eval["n_high"], "oos_tr": oos_eval["tr"],
        })

    valid = [f for f in fold_results if "error" not in f]
    if not valid:
        return {"error": "no valid folds"}

    best_pcts = [f["best_pct"] for f in valid]
    pct_cv = float(np.std(best_pcts, ddof=1) / np.mean(best_pcts)) if len(best_pcts) > 1 else 0.0
    bipolar = float(np.mean([abs(p - 50) for p in best_pcts]))
    oos_trs = [f["oos_tr"] for f in valid if f["oos_tr"] is not None]

    return {
        "pair": pair, "method": "Mode B v2 + pct grid",
        "fold_results": fold_results,
        "best_pcts": best_pcts,
        "pct_cv": pct_cv,
        "bipolarization_score": bipolar,
        "oos_tr_mean": float(np.mean(oos_trs)) if oos_trs else None,
        "n_pass_oos": sum(1 for tr in oos_trs if tr > 1.0),
        "n_total_folds": len(valid),
    }


# ============================================================
# 候補 a: M15 ダウンサンプリングで二極化が再発するか
# ============================================================
def run_modeB_v2_m15_downsampled(pair: str, target_n: int = 5000, years: int = 2) -> dict:
    """M15 YZ_vol を target_n サンプルにダウンサンプリングして Mode B v2 再実行"""
    csv_path = ROOT / "data" / f"mt5_{pair}_M15_{years}y.csv"
    if not csv_path.exists():
        return {"error": f"missing csv: {csv_path}"}

    df = load_csv(csv_path)
    indicator = calc_yang_zhang(df, window=14)
    df_ret = add_returns(df, LOOKAHEAD["M15"])
    aligned = pd.concat([df_ret[["future_return"]], indicator.rename("ind")], axis=1).dropna()
    aligned = aligned.copy()
    aligned["abs_return"] = aligned["future_return"].abs()

    # ダウンサンプリング (時系列構造を保つため等間隔抽出)
    n_full = len(aligned)
    if n_full <= target_n:
        return {"error": f"data smaller than target_n: {n_full} <= {target_n}"}
    step = n_full // target_n
    aligned = aligned.iloc[::step].head(target_n).copy()

    n = len(aligned)
    fold_size = n // (N_FOLDS + 1)

    YZ_PCT_GRID = [10, 20, 30, 40, 50, 60, 70, 80, 90]

    fold_results = []
    for k in range(1, N_FOLDS + 1):
        is_end = k * fold_size
        oos_end = (k + 1) * fold_size if k < N_FOLDS else n
        is_df = aligned.iloc[:is_end]
        oos_df = aligned.iloc[is_end:oos_end]

        best = None
        for pct in YZ_PCT_GRID:
            threshold = float(np.percentile(is_df["ind"].values, pct))
            is_eval = compute_tr_fixed_low(is_df, threshold, "gt", LOW_PCT_RANGE)
            if is_eval["tr"] is None or is_eval["n_high"] < MIN_SAMPLE_IS:
                continue
            if best is None or is_eval["tr"] > best["is_tr"]:
                best = {
                    "pct": pct, "threshold": threshold,
                    "is_n_high": is_eval["n_high"], "is_tr": is_eval["tr"],
                }

        if best is None:
            fold_results.append({"fold": k, "error": "no candidate"})
            continue

        oos_eval = compute_tr_fixed_low(oos_df, best["threshold"], "gt", LOW_PCT_RANGE)
        fold_results.append({
            "fold": k, "best_pct": best["pct"], "threshold": best["threshold"],
            "is_n_high": best["is_n_high"], "is_tr": best["is_tr"],
            "oos_n_high": oos_eval["n_high"], "oos_tr": oos_eval["tr"],
        })

    valid = [f for f in fold_results if "error" not in f]
    if not valid:
        return {"error": "no valid folds"}

    best_pcts = [f["best_pct"] for f in valid]
    pct_cv = float(np.std(best_pcts, ddof=1) / np.mean(best_pcts)) if len(best_pcts) > 1 else 0.0
    bipolar = float(np.mean([abs(p - 50) for p in best_pcts]))

    return {
        "pair": pair, "method": f"M15 downsampled to n={target_n}",
        "n_total": n,
        "fold_results": fold_results,
        "best_pcts": best_pcts,
        "pct_cv": pct_cv,
        "bipolarization_score": bipolar,
    }


# ============================================================
# 候補 c: 自己相関 ACF
# ============================================================
def compute_acf(pair: str, tf: str, years: int) -> dict:
    csv_path = ROOT / "data" / f"mt5_{pair}_{tf}_{years}y.csv"
    if not csv_path.exists():
        return {"error": f"missing csv: {csv_path}"}

    df = load_csv(csv_path)
    indicator = calc_yang_zhang(df, window=20 if tf != "M15" else 14)
    indicator = indicator.dropna()

    # ACF lag 1, 5, 10, 24
    acfs = {}
    for lag in [1, 5, 10, 24]:
        if len(indicator) > lag:
            shifted = indicator.shift(lag)
            valid = ~(indicator.isna() | shifted.isna())
            if valid.sum() > 30:
                acf = float(np.corrcoef(indicator[valid], shifted[valid])[0, 1])
                acfs[f"lag_{lag}"] = acf
            else:
                acfs[f"lag_{lag}"] = None
        else:
            acfs[f"lag_{lag}"] = None

    return {"pair": pair, "tf": tf, "n": len(indicator), "acf": acfs}


# ============================================================
# メイン
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    pairs = ["USD_JPY", "EUR_USD", "GBP_JPY"]

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 真因補強検証 (P1-B): 候補 b/a/c")
    print(f"{'=' * 130}")

    # ====================
    # 候補 b: H1 pct グリッド
    # ====================
    print(f"\n--- 候補 b: H1 YZ_vol を pct グリッド {H1_PCT_GRID} で Mode B v2 ---")
    print(f"対照: 旧 abs グリッド (Mode B v2 = SPEC × {{0.5,...,1.5}}) では best_pct ≈ {{82, 95, 95, 95, 95}} 等で CV 0.16")
    print()
    print(f"{'Pair':<10} {'best_pcts (5 fold)':<35} {'pct CV':>7} {'二極化':>7} {'OOS_TR':>7} {'pass':>5}")
    print("-" * 90)

    candidate_b_results = []
    for pair in pairs:
        r = run_modeB_v2_pct_grid(pair)
        if "error" in r:
            print(f"{pair:<10} ERROR: {r['error']}")
            continue
        candidate_b_results.append(r)
        bp_s = str(r["best_pcts"])[:35]
        oos_s = f"{r['oos_tr_mean']:.3f}" if r['oos_tr_mean'] is not None else "-"
        print(f"{pair:<10} {bp_s:<35} {r['pct_cv']:>7.3f} "
              f"{r['bipolarization_score']:>7.1f} {oos_s:>7} {r['n_pass_oos']}/{r['n_total_folds']}")

    # ====================
    # 候補 a: M15 ダウンサンプリング
    # ====================
    print(f"\n--- 候補 a: M15 YZ_vol を n=5000 (H1 並み) にダウンサンプリングして Mode B v2 ---")
    print(f"対照: M15 full (50K) では best_pct CV 0.06-0.26、二極化解消")
    print()
    print(f"{'Pair':<10} {'n':>6} {'best_pcts (5 fold)':<35} {'pct CV':>7} {'二極化':>7}")
    print("-" * 80)

    candidate_a_results = []
    for pair in pairs:
        r = run_modeB_v2_m15_downsampled(pair, target_n=5000)
        if "error" in r:
            print(f"{pair:<10} ERROR: {r['error']}")
            continue
        candidate_a_results.append(r)
        bp_s = str(r["best_pcts"])[:35]
        print(f"{pair:<10} {r['n_total']:>6} {bp_s:<35} {r['pct_cv']:>7.3f} "
              f"{r['bipolarization_score']:>7.1f}")

    # ====================
    # 候補 c: 自己相関
    # ====================
    print(f"\n--- 候補 c: YZ_vol 自己相関 (ACF lag 1/5/10/24) ---")
    print()
    print(f"{'Pair':<10} {'TF':<5} {'n':>7} {'ACF(1)':>8} {'ACF(5)':>8} {'ACF(10)':>9} {'ACF(24)':>9}")
    print("-" * 70)

    candidate_c_results = []
    for pair in pairs:
        for tf, years in [("M15", 2), ("H1", 5), ("D1", 10)]:
            r = compute_acf(pair, tf, years)
            if "error" in r:
                continue
            candidate_c_results.append(r)
            acf = r["acf"]
            acf_strs = []
            for lag in [1, 5, 10, 24]:
                v = acf.get(f"lag_{lag}")
                acf_strs.append(f"{v:>+8.3f}" if v is not None else "        -")
            print(f"{pair:<10} {tf:<5} {r['n']:>7} {acf_strs[0]:>8} {acf_strs[1]:>8} "
                  f"{acf_strs[2]:>9} {acf_strs[3]:>9}")

    # ====================
    # 結論
    # ====================
    print(f"\n{'=' * 130}")
    print(f"結論")
    print(f"{'=' * 130}")

    if candidate_b_results:
        b_cvs = [r["pct_cv"] for r in candidate_b_results]
        b_avg_cv = np.mean(b_cvs)
        if b_avg_cv < 0.1:
            print(f"候補 b: 🟢 H1 pct グリッドで CV {b_avg_cv:.3f} < 0.1 → abs グリッド設計が真因の一つ")
        elif b_avg_cv < 0.3:
            print(f"候補 b: 🟡 H1 pct グリッドで CV {b_avg_cv:.3f} → 部分的に改善、グリッド設計は寄与あり")
        else:
            print(f"候補 b: 🔴 H1 pct グリッドでも CV {b_avg_cv:.3f} → グリッド設計は真因ではない")

    if candidate_a_results:
        a_cvs = [r["pct_cv"] for r in candidate_a_results]
        a_avg_cv = np.mean(a_cvs)
        if a_avg_cv > 0.3:
            print(f"候補 a: 🟢 M15 ダウンサンプル後 CV {a_avg_cv:.3f} > 0.3 → サンプル数が真因 (n が減ると二極化再発)")
        elif a_avg_cv > 0.1:
            print(f"候補 a: 🟡 M15 ダウンサンプル後 CV {a_avg_cv:.3f} → 部分的に二極化再発、サンプル数は寄与あり")
        else:
            print(f"候補 a: 🔴 M15 ダウンサンプル後でも CV {a_avg_cv:.3f} → サンプル数は真因ではない")

    if candidate_c_results:
        # ACF lag 1 の TF 別比較
        acf1_by_tf = {}
        for r in candidate_c_results:
            tf = r["tf"]
            v = r["acf"].get("lag_1")
            if v is not None:
                acf1_by_tf.setdefault(tf, []).append(v)
        for tf in ["M15", "H1", "D1"]:
            if tf in acf1_by_tf:
                avg = np.mean(acf1_by_tf[tf])
                print(f"候補 c 参考: {tf} ACF(1) 平均 = {avg:+.3f} (M15 vs H1 vs D1 で自己相関構造の違い)")

    out_json = ROOT / "data" / "spec_2_1_root_cause_analysis.json"
    out_json.write_text(json.dumps({
        "candidate_b_h1_pct_grid": candidate_b_results,
        "candidate_a_m15_downsampled": candidate_a_results,
        "candidate_c_acf": candidate_c_results,
    }, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
