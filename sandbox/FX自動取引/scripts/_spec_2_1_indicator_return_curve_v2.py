"""SPEC v2 - 2-1: 指標–リターン曲線 v2 (Step C 新 P0 Q1 強化)

レビュー指摘 (Karen / analyst) を受けた v2:
- 20 → 50 分位 (粗グリッド問題)
- 二次係数 a の bootstrap 95%CI (U字判定の堅牢化)
- Hartigan dip test (単峰性の統計検定)
- Spearman ρ + permutation p (形状非依存の単調関係検定)

## 改良点

### 1. 解像度向上
20 分位 → 50 分位 (2% 刻み)。USD_JPY M15 YZ_vol で q5-14 がフラットだった疑惑を、
より細かい解像度で確認する。

### 2. 二次係数 a の bootstrap CI
v1 では二次係数 a の点推定の符号で「U字 / 逆U字」判定していたが、a≈0 のとき
信頼区間がゼロを跨ぐ可能性あり。bootstrap 95% CI を計算し、CI が:
- 完全に正 → U字方向 (二峰の可能性)
- 完全に負 → 逆U字方向 (中央単峰の可能性)
- ゼロを跨ぐ → 形状判別困難 (単峰確定とは言えない)

### 3. Hartigan dip test
50 分位の median |return| 系列を「サンプル」として dip test を適用。
dip 値が大きい (p < 0.05) なら多峰性の統計的支持がある。

### 4. Spearman ρ + permutation p
indicator vs |future_return| の単調関係を順位ベースで検定。
線形 / 二次回帰の前提なしに「単調か否か」を判定。

## 出力
- data/spec_2_1_return_curve_v2.json
- 標準出力: 各 (pair, tf, indicator) の v1 比較 + v2 統計検定結果

## 使用例
  python scripts/_spec_2_1_indicator_return_curve_v2.py --n_boot 1000
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
import diptest

ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("spec_2_1_indicator_return_curve_v2")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}
N_QUANTILES = 50  # 2% 刻み (v1 は 20)

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


# ============================================================
# 統計検定
# ============================================================
def bootstrap_quadratic_coef_ci(
    quantile_samples: list[np.ndarray],
    n_boot: int = 1000,
    seed: int = 42,
) -> dict:
    """各分位内の |return| サンプルから bootstrap で二次係数 a の 95%CI を出す。

    quantile_samples[q] は分位 q に属するサンプルの |return| 配列。
    元の分位定義は固定 (rank-based qcut)。
    """
    n_q = len(quantile_samples)
    rng = np.random.default_rng(seed)
    x = np.arange(n_q, dtype=float)

    boot_a = []
    boot_lin_slope = []
    boot_argmax = []
    boot_argmin = []
    skipped = 0

    for b in range(n_boot):
        medians = np.full(n_q, np.nan)
        for q in range(n_q):
            samples = quantile_samples[q]
            if len(samples) == 0:
                continue
            idx = rng.integers(0, len(samples), size=len(samples))
            medians[q] = np.median(samples[idx])

        if np.any(np.isnan(medians)):
            skipped += 1
            continue

        # 二次回帰
        coef_quad = np.polyfit(x, medians, 2)
        boot_a.append(float(coef_quad[0]))

        # 線形回帰の slope
        coef_lin = np.polyfit(x, medians, 1)
        boot_lin_slope.append(float(coef_lin[0]))

        boot_argmax.append(int(np.argmax(medians)))
        boot_argmin.append(int(np.argmin(medians)))

    boot_a = np.array(boot_a)
    boot_lin_slope = np.array(boot_lin_slope)
    boot_argmax = np.array(boot_argmax)
    boot_argmin = np.array(boot_argmin)

    if len(boot_a) == 0:
        return {"error": "no valid bootstrap samples"}

    return {
        "n_boot": len(boot_a),
        "skipped": skipped,
        "quadratic_coef": {
            "mean": float(boot_a.mean()),
            "std": float(boot_a.std(ddof=1)),
            "ci_low": float(np.percentile(boot_a, 2.5)),
            "ci_high": float(np.percentile(boot_a, 97.5)),
            "p_positive": float((boot_a > 0).mean()),  # U字方向の確率
            "p_negative": float((boot_a < 0).mean()),  # 逆U字方向の確率
        },
        "linear_slope": {
            "mean": float(boot_lin_slope.mean()),
            "std": float(boot_lin_slope.std(ddof=1)),
            "ci_low": float(np.percentile(boot_lin_slope, 2.5)),
            "ci_high": float(np.percentile(boot_lin_slope, 97.5)),
            "p_positive": float((boot_lin_slope > 0).mean()),
        },
        "argmax_distribution": {
            "mode": int(stats.mode(boot_argmax, keepdims=False).mode),
            "p_at_high_end": float((boot_argmax >= n_q - 2).mean()),
            "p_at_low_end": float((boot_argmax <= 1).mean()),
            "p_central": float(((boot_argmax >= n_q // 4) & (boot_argmax < 3 * n_q // 4)).mean()),
        },
        "argmin_distribution": {
            "mode": int(stats.mode(boot_argmin, keepdims=False).mode),
            "p_at_high_end": float((boot_argmin >= n_q - 2).mean()),
            "p_at_low_end": float((boot_argmin <= 1).mean()),
            "p_central": float(((boot_argmin >= n_q // 4) & (boot_argmin < 3 * n_q // 4)).mean()),
        },
    }


def hartigan_dip_test(medians: np.ndarray) -> dict:
    """50 分位の median 系列を「empirical distribution」として dip test を適用。

    厳密にはサンプル分布の単峰性検定だが、形状の凹凸検出には有効。
    p < 0.05 → 多峰性を統計的に支持。
    """
    if len(medians) < 4 or np.any(np.isnan(medians)):
        return {"error": "insufficient data"}
    dip, p_value = diptest.diptest(medians)
    return {
        "dip_statistic": float(dip),
        "p_value": float(p_value),
        "is_multimodal_at_05": bool(p_value < 0.05),
        "is_multimodal_at_10": bool(p_value < 0.10),
    }


def spearman_with_permutation(
    indicator_values: np.ndarray,
    abs_returns: np.ndarray,
    n_perm: int = 1000,
    seed: int = 42,
) -> dict:
    """Spearman ρ を permutation で検定。形状非依存の単調関係検定。"""
    if len(indicator_values) < 30:
        return {"error": "insufficient data"}
    rho, _ = stats.spearmanr(indicator_values, abs_returns)
    rng = np.random.default_rng(seed)

    # permutation null
    null_rhos = []
    for _ in range(n_perm):
        shuffled = rng.permutation(abs_returns)
        r, _ = stats.spearmanr(indicator_values, shuffled)
        null_rhos.append(r)
    null_rhos = np.array(null_rhos)

    p_two_sided = float((np.abs(null_rhos) >= abs(rho)).mean())
    return {
        "rho": float(rho),
        "p_value_perm": p_two_sided,
        "null_mean": float(null_rhos.mean()),
        "null_std": float(null_rhos.std(ddof=1)),
    }


# ============================================================
# 解釈
# ============================================================
def interpret(boot_result: dict, dip_result: dict, spearman_result: dict) -> str:
    """3 検定の結果から総合的な形状判定を出す。"""
    parts = []

    # 二次係数 CI
    qc = boot_result.get("quadratic_coef", {})
    ci_low = qc.get("ci_low")
    ci_high = qc.get("ci_high")
    if ci_low is not None and ci_high is not None:
        if ci_low > 0:
            parts.append("二次係数CI完全正(U字方向)")
        elif ci_high < 0:
            parts.append("二次係数CI完全負(逆U字方向)")
        else:
            parts.append("二次係数CIゼロ跨ぎ(形状判別困難)")

    # 線形 slope CI
    ls = boot_result.get("linear_slope", {})
    ls_low = ls.get("ci_low")
    ls_high = ls.get("ci_high")
    if ls_low is not None and ls_high is not None:
        if ls_low > 0:
            parts.append("線形slopeCI正(単調増加支持)")
        elif ls_high < 0:
            parts.append("線形slopeCI負(単調減少支持)")
        else:
            parts.append("線形slopeCIゼロ跨ぎ(単調性弱)")

    # dip test
    if "p_value" in dip_result:
        p_dip = dip_result["p_value"]
        if p_dip < 0.05:
            parts.append(f"dip:多峰性支持(p={p_dip:.3f})")
        elif p_dip < 0.10:
            parts.append(f"dip:多峰性弱支持(p={p_dip:.3f})")
        else:
            parts.append(f"dip:単峰否定なし(p={p_dip:.3f})")

    # Spearman
    if "rho" in spearman_result:
        rho = spearman_result["rho"]
        p_sp = spearman_result["p_value_perm"]
        if p_sp < 0.01:
            parts.append(f"Spearman ρ={rho:+.3f}有意(p<0.01)")
        elif p_sp < 0.05:
            parts.append(f"Spearman ρ={rho:+.3f}有意(p<0.05)")
        else:
            parts.append(f"Spearman ρ={rho:+.3f}有意性なし(p={p_sp:.3f})")

    return " | ".join(parts)


# ============================================================
# メイン処理
# ============================================================
def analyze_target(
    pair: str, tf: str, indicator_name: str, param: int, years: int,
    n_boot: int, n_perm: int,
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

    # D1 はサンプル少 (1407) なので分位を 25 にする
    n_q = N_QUANTILES if tf != "D1" else 25
    if len(aligned) < n_q * 20:
        return {"error": f"insufficient samples: n={len(aligned)} for {n_q} quantiles"}

    aligned = aligned.copy()
    aligned["abs_return"] = aligned["future_return"].abs()
    try:
        aligned["q"] = pd.qcut(aligned["ind"].rank(method="first"), n_q, labels=False)
    except ValueError as e:
        return {"error": f"qcut failed: {e}"}

    # 各分位の median (点推定) と各分位内の |return| サンプル
    quantile_samples = []
    quantile_stats = []
    for q in range(n_q):
        sub = aligned[aligned["q"] == q]
        if len(sub) == 0:
            quantile_samples.append(np.array([]))
            quantile_stats.append({"q": q, "n": 0})
            continue
        samples = sub["abs_return"].values
        quantile_samples.append(samples)
        quantile_stats.append({
            "q": q,
            "n": int(len(sub)),
            "ind_median": float(sub["ind"].median()),
            "abs_return_median": float(np.median(samples)),
            "abs_return_mean": float(samples.mean()),
        })

    medians = np.array([qs.get("abs_return_median", np.nan) for qs in quantile_stats])

    # ========== 統計検定 ==========
    print(f"  bootstrap (B={n_boot}, n_q={n_q}) ...", flush=True)
    boot_result = bootstrap_quadratic_coef_ci(quantile_samples, n_boot=n_boot)

    print(f"  Hartigan dip test ...", flush=True)
    dip_result = hartigan_dip_test(medians)

    print(f"  Spearman + permutation (n_perm={n_perm}) ...", flush=True)
    sp_result = spearman_with_permutation(
        aligned["ind"].values, aligned["abs_return"].values, n_perm=n_perm,
    )

    interpretation = interpret(boot_result, dip_result, sp_result)

    return {
        "pair": pair,
        "tf": tf,
        "indicator": indicator_name,
        "param": param,
        "years": years,
        "n_total": int(len(aligned)),
        "n_quantiles": n_q,
        "lookahead": LOOKAHEAD[tf],
        "quantile_stats": quantile_stats,
        "bootstrap": boot_result,
        "dip_test": dip_result,
        "spearman_perm": sp_result,
        "interpretation": interpretation,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_boot", type=int, default=1000)
    parser.add_argument("--n_perm", type=int, default=1000)
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 指標–リターン曲線 v2 (Step C 新 P0 Q1 強化)")
    print(f"  N_QUANTILES = {N_QUANTILES} (D1 は 25)")
    print(f"  n_boot      = {args.n_boot}")
    print(f"  n_perm      = {args.n_perm}")
    print(f"  対象        = {len(TARGETS)} (pair, tf, indicator)")
    print(f"{'=' * 130}")

    results = []
    for pair, tf, ind_name, param, years in TARGETS:
        print(f"\n--- {pair} / {tf} / {ind_name}({param}) ---")
        r = analyze_target(pair, tf, ind_name, param, years, args.n_boot, args.n_perm)
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        results.append(r)

        # 結果表示
        qc = r["bootstrap"]["quadratic_coef"]
        ls = r["bootstrap"]["linear_slope"]
        am = r["bootstrap"]["argmax_distribution"]
        ai = r["bootstrap"]["argmin_distribution"]
        dp = r["dip_test"]
        sp = r["spearman_perm"]
        n_q_actual = r["n_quantiles"]

        print(f"  n_total={r['n_total']}, n_quantiles={n_q_actual}")
        print(f"  [二次係数 a]   mean={qc['mean']:+.2e}, "
              f"95%CI=[{qc['ci_low']:+.2e}, {qc['ci_high']:+.2e}], "
              f"P(a>0)={qc['p_positive']:.3f}")
        print(f"  [線形 slope]   mean={ls['mean']:+.2e}, "
              f"95%CI=[{ls['ci_low']:+.2e}, {ls['ci_high']:+.2e}], "
              f"P(slope>0)={ls['p_positive']:.3f}")
        print(f"  [argmax分布]   mode=q{am['mode']}, P(端高q{n_q_actual-2}-{n_q_actual-1})={am['p_at_high_end']:.3f}, "
              f"P(中央)={am['p_central']:.3f}, P(端低q0-1)={am['p_at_low_end']:.3f}")
        print(f"  [argmin分布]   mode=q{ai['mode']}, P(中央)={ai['p_central']:.3f}, "
              f"P(端低q0-1)={ai['p_at_low_end']:.3f}, P(端高)={ai['p_at_high_end']:.3f}")
        print(f"  [Hartigan dip] dip={dp['dip_statistic']:.4f}, p={dp['p_value']:.3f}")
        print(f"  [Spearman]     ρ={sp['rho']:+.4f}, p_perm={sp['p_value_perm']:.3f}")
        print(f"  ★ {r['interpretation']}")

    # ============================================================
    # サマリ
    # ============================================================
    print(f"\n{'=' * 140}")
    print(f"形状判定サマリ v2 (Bootstrap CI + dip test + Spearman)")
    print(f"{'=' * 140}")
    print(f"{'Pair':<8} {'TF':<5} {'指標':<8} "
          f"{'a CI':<24} {'slope CI':<24} "
          f"{'dip p':>7} {'Sp ρ':>7} {'Sp p':>6}  解釈")
    print("-" * 140)
    for r in results:
        qc = r["bootstrap"]["quadratic_coef"]
        ls = r["bootstrap"]["linear_slope"]
        dp = r["dip_test"]
        sp = r["spearman_perm"]

        # CI 表示
        a_low = qc["ci_low"]
        a_high = qc["ci_high"]
        a_label = "正" if a_low > 0 else "負" if a_high < 0 else "跨"
        a_ci_s = f"[{a_low:+.1e},{a_high:+.1e}]{a_label}"

        s_low = ls["ci_low"]
        s_high = ls["ci_high"]
        s_label = "正" if s_low > 0 else "負" if s_high < 0 else "跨"
        s_ci_s = f"[{s_low:+.1e},{s_high:+.1e}]{s_label}"

        print(f"{r['pair']:<8} {r['tf']:<5} {r['indicator']:<8} "
              f"{a_ci_s:<24} {s_ci_s:<24} "
              f"{dp['p_value']:>7.3f} {sp['rho']:>+7.3f} {sp['p_value_perm']:>6.3f}")

    out_json = ROOT / "data" / "spec_2_1_return_curve_v2.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
