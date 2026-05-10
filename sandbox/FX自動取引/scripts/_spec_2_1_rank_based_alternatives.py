"""SPEC v2 - 2-1: 順位ベース代替指標 (P1-C / 新 Q4)

## 背景
Q1 v2 + 介入実験で「TR 評価式は low 群感度を持つ」と判明。
TR の代替として順位ベースの指標 (Spearman ρ / Kendall τ) を評価。

## 検証する問い
1. Spearman ρ / Kendall τ は TR と相関するか? (代替として使えるか)
2. block bootstrap で自己相関を考慮した CI はどう変わるか? (P1-B 候補 c の本格対処)
3. TR が low 群感度で揺れる場面で、Spearman/Kendall は安定か?

## 検証方法
各 (pair, tf, indicator) で:
- TR (low 群固定 25-50%ile)
- Spearman ρ + block bootstrap 95%CI (block_size = lookahead × 4)
- Kendall τ + block bootstrap 95%CI
- 順位ベース指標と TR の相関 (Pearson)

## block bootstrap
時系列の自己相関を考慮するため、連続する block_size 個のサンプルを 1 ブロックとして扱い、
B=500 回ブロックを再サンプリング。

## 出力
- data/spec_2_1_rank_based.json
- 標準出力: 各組の TR vs ρ vs τ の比較表
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
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("spec_2_1_rank_based")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}
LOW_PCT_RANGE = (25, 50)

# block_size = lookahead × 4 (自己相関が 0.5 を切るあたりの目安)
BLOCK_SIZE_BY_TF = {"M15": 96, "H1": 24, "D1": 20}

TARGETS = [
    ("USD_JPY", "M15", "YZ_vol", 14, 2),
    ("EUR_USD", "M15", "YZ_vol", 14, 2),
    ("GBP_JPY", "M15", "YZ_vol", 14, 2),
    ("USD_JPY", "M15", "CHOP", 14, 2),
    ("EUR_USD", "M15", "CHOP", 14, 2),
    ("GBP_JPY", "M15", "CHOP", 14, 2),
    ("USD_JPY", "H1", "YZ_vol", 20, 5),
    ("EUR_USD", "H1", "YZ_vol", 20, 5),
    ("GBP_JPY", "H1", "YZ_vol", 20, 5),
    ("USD_JPY", "D1", "YZ_vol", 20, 10),
    ("EUR_USD", "D1", "YZ_vol", 20, 10),
    ("GBP_JPY", "D1", "YZ_vol", 20, 10),
]


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


def compute_tr_fixed_low(ind: np.ndarray, abs_ret: np.ndarray, threshold: float) -> float:
    """TR for low 群固定方式 (25-50%ile)"""
    low_lo = float(np.percentile(ind, LOW_PCT_RANGE[0]))
    low_hi = float(np.percentile(ind, LOW_PCT_RANGE[1]))
    mask_high = ind > threshold
    mask_low = (ind >= low_lo) & (ind <= low_hi)
    if mask_high.sum() < 30 or mask_low.sum() < 30:
        return None
    med_h = np.median(abs_ret[mask_high])
    med_l = np.median(abs_ret[mask_low])
    if med_l <= 0:
        return None
    return float(med_h / med_l)


def block_bootstrap_correlation(
    x: np.ndarray, y: np.ndarray, block_size: int,
    method: str, n_boot: int = 500, seed: int = 42,
) -> dict:
    """連続 block_size のブロックを再サンプリングして相関係数の CI を出す"""
    n = len(x)
    n_blocks = (n + block_size - 1) // block_size
    rng = np.random.default_rng(seed)

    boot_corrs = []
    for _ in range(n_boot):
        # ブロック開始位置をランダムに選択
        starts = rng.integers(0, n - block_size + 1, size=n_blocks)
        idx_list = []
        for s in starts:
            idx_list.append(np.arange(s, s + block_size))
        idx = np.concatenate(idx_list)[:n]
        x_b = x[idx]
        y_b = y[idx]
        if method == "spearman":
            r, _ = stats.spearmanr(x_b, y_b)
        elif method == "kendall":
            r, _ = stats.kendalltau(x_b, y_b)
        if not np.isnan(r):
            boot_corrs.append(r)

    boot_corrs = np.array(boot_corrs)
    if len(boot_corrs) == 0:
        return {"error": "no valid bootstrap"}

    return {
        "mean": float(boot_corrs.mean()),
        "std": float(boot_corrs.std(ddof=1)),
        "ci_low": float(np.percentile(boot_corrs, 2.5)),
        "ci_high": float(np.percentile(boot_corrs, 97.5)),
    }


def analyze_target(
    pair: str, tf: str, indicator_name: str, param: int, years: int,
    n_boot: int,
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
        return {"error": f"unknown indicator"}

    df_ret = add_returns(df, LOOKAHEAD[tf])
    aligned = pd.concat([df_ret[["future_return"]], indicator.rename("ind")], axis=1).dropna()
    aligned = aligned.copy()
    aligned["abs_return"] = aligned["future_return"].abs()

    ind_arr = aligned["ind"].values
    abs_ret_arr = aligned["abs_return"].values

    block_size = BLOCK_SIZE_BY_TF[tf]

    # Spearman ρ + block bootstrap
    print(f"  Spearman block bootstrap (B={n_boot}, block={block_size})...")
    rho, p_naive = stats.spearmanr(ind_arr, abs_ret_arr)
    rho_block = block_bootstrap_correlation(ind_arr, abs_ret_arr, block_size, "spearman", n_boot=n_boot)

    # Kendall τ + block bootstrap (Kendall は遅いので n_boot を抑える)
    n_boot_kt = min(n_boot, 200)
    print(f"  Kendall block bootstrap (B={n_boot_kt})...")
    tau, p_kt_naive = stats.kendalltau(ind_arr, abs_ret_arr)
    tau_block = block_bootstrap_correlation(ind_arr, abs_ret_arr, block_size, "kendall", n_boot=n_boot_kt)

    # TR (low 群固定方式) — 中央 50%ile を threshold として
    threshold = float(np.median(ind_arr))
    tr_median = compute_tr_fixed_low(ind_arr, abs_ret_arr, threshold)

    # 90%ile threshold での TR (より厳しい高ボラ判定)
    threshold_90 = float(np.percentile(ind_arr, 90))
    tr_90 = compute_tr_fixed_low(ind_arr, abs_ret_arr, threshold_90)

    return {
        "pair": pair, "tf": tf, "indicator": indicator_name,
        "n_total": len(aligned),
        "block_size": block_size,
        "spearman": {
            "rho": float(rho),
            "p_naive": float(p_naive),
            "block_bootstrap_ci": rho_block,
        },
        "kendall": {
            "tau": float(tau),
            "p_naive": float(p_kt_naive),
            "block_bootstrap_ci": tau_block,
        },
        "tr_median_threshold": tr_median,
        "tr_90pct_threshold": tr_90,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_boot", type=int, default=500)
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 順位ベース代替指標 (P1-C / 新 Q4)")
    print(f"  block_size = {BLOCK_SIZE_BY_TF}")
    print(f"  n_boot = {args.n_boot}")
    print(f"{'=' * 130}")

    results = []
    for pair, tf, ind_name, param, years in TARGETS:
        print(f"\n--- {pair} / {tf} / {ind_name}({param}) ---")
        r = analyze_target(pair, tf, ind_name, param, years, args.n_boot)
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        results.append(r)

        sp = r["spearman"]
        kt = r["kendall"]
        sp_ci = sp["block_bootstrap_ci"]
        kt_ci = kt["block_bootstrap_ci"]

        sp_ci_s = f"[{sp_ci['ci_low']:+.3f}, {sp_ci['ci_high']:+.3f}]" if "error" not in sp_ci else "ERROR"
        kt_ci_s = f"[{kt_ci['ci_low']:+.3f}, {kt_ci['ci_high']:+.3f}]" if "error" not in kt_ci else "ERROR"

        tr_m_s = f"{r['tr_median_threshold']:.3f}" if r['tr_median_threshold'] is not None else "-"
        tr_90_s = f"{r['tr_90pct_threshold']:.3f}" if r['tr_90pct_threshold'] is not None else "-"

        print(f"  Spearman ρ = {sp['rho']:+.4f}, block bootstrap 95%CI = {sp_ci_s}")
        print(f"  Kendall  τ = {kt['tau']:+.4f}, block bootstrap 95%CI = {kt_ci_s}")
        print(f"  TR (50%ile thr) = {tr_m_s}, TR (90%ile thr) = {tr_90_s}")

    # ============================================================
    # サマリ: TR vs Spearman vs Kendall
    # ============================================================
    print(f"\n{'=' * 140}")
    print(f"順位ベース vs TR の対照表")
    print(f"{'=' * 140}")
    print(f"{'Pair':<8} {'TF':<5} {'Ind':<8} "
          f"{'Spearman ρ':>11} {'CI 幅':>8} "
          f"{'Kendall τ':>10} {'CI 幅':>8} "
          f"{'TR(50%)':>8} {'TR(90%)':>8}")
    print("-" * 140)

    spearman_sig = 0
    kendall_sig = 0
    tr_significant = 0  # TR > 1.2 で「強信号」と仮定
    for r in results:
        sp = r["spearman"]
        kt = r["kendall"]
        sp_ci = sp["block_bootstrap_ci"]
        kt_ci = kt["block_bootstrap_ci"]

        sp_ci_w = (sp_ci["ci_high"] - sp_ci["ci_low"]) if "error" not in sp_ci else None
        kt_ci_w = (kt_ci["ci_high"] - kt_ci["ci_low"]) if "error" not in kt_ci else None

        # 0 を跨がないなら有意
        if "error" not in sp_ci:
            if not (sp_ci["ci_low"] < 0 < sp_ci["ci_high"]):
                spearman_sig += 1
        if "error" not in kt_ci:
            if not (kt_ci["ci_low"] < 0 < kt_ci["ci_high"]):
                kendall_sig += 1
        if r['tr_90pct_threshold'] is not None and r['tr_90pct_threshold'] > 1.2:
            tr_significant += 1

        sp_w_s = f"{sp_ci_w:.3f}" if sp_ci_w is not None else "-"
        kt_w_s = f"{kt_ci_w:.3f}" if kt_ci_w is not None else "-"
        tr_m_s = f"{r['tr_median_threshold']:.3f}" if r['tr_median_threshold'] is not None else "-"
        tr_90_s = f"{r['tr_90pct_threshold']:.3f}" if r['tr_90pct_threshold'] is not None else "-"

        print(f"{r['pair']:<8} {r['tf']:<5} {r['indicator']:<8} "
              f"{sp['rho']:>+11.4f} {sp_w_s:>8} "
              f"{kt['tau']:>+10.4f} {kt_w_s:>8} "
              f"{tr_m_s:>8} {tr_90_s:>8}")

    print(f"\nblock bootstrap CI が 0 を跨がない (有意) 件数:")
    print(f"  Spearman: {spearman_sig}/{len(results)}")
    print(f"  Kendall : {kendall_sig}/{len(results)}")
    print(f"  TR(90%) > 1.2 件数: {tr_significant}/{len(results)}")

    out_json = ROOT / "data" / "spec_2_1_rank_based.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
