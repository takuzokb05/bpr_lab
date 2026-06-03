"""SPEC v2 - 2-1 季節判定: Multiple Testing Correction (Step C P0-3)

採用済み 12 閾値に対し、N=606 試行全体および 12-family 内で multiple testing 補正を適用。

## 背景
P0-2 (`_spec_2_1_random_baseline.py`) で permutation 1000 回の raw p 値を測定。
12 閾値中 11/12 が p<0.05 を個別にクリア。ただし試行数 N=606 (P0-1 棚卸し結果) を
考慮すると、**Bonferroni 厳密境界は α/N = 0.05/606 ≈ 8.25×10⁻⁵**。

permutation 1000 回では分解能 0.001 までしか測れず、Bonferroni 境界より粗い。
このスクリプトは:
1. n_perm=20000 で各閾値の raw p を再測定 (分解能 5×10⁻⁵)
2. Bonferroni 補正 (N=606 全試行ファミリー)
3. Holm step-down (less conservative than Bonferroni)
4. Romano-Wolf 12-family step-down (max-T 統計量)

## 補正手法

### Bonferroni
p_bonf = min(1, p_raw × N), N=606
α=0.05 で生存条件: p_raw < 0.05/606 ≈ 8.25×10⁻⁵

### Holm step-down
1. p_(1) ≤ p_(2) ≤ ... ≤ p_(N) と昇順ソート
2. p_(k) を α/(N-k+1) と比較。最初に超えた所で止める
3. それ以前は棄却 (rejected)

### Romano-Wolf 12-family
1. 全 12 試行で同じ permutation を行い、各 perm で 12 試行のうち最大 TR を記録
2. null_max 分布を構築
3. p_rw = (null_max ≥ obs_TR).mean()
4. これは 12-family 内 FWER 補正。N=606 全体補正ではない（=relatively less conservative）

## 出力
- data/spec_2_1_multiple_testing.json
- 標準出力: 各閾値の raw_p / p_bonf_606 / p_holm_606 / p_rw_12 + 判定

## 注意
- 採用済み 12 閾値は P0-2 で「採用ステータス」が確定したもの
- N=606 試行全体の Bonferroni/Holm 適用は最も保守的 (false negative 大)
- Romano-Wolf 12-family は採用ペア間の相対比較として有用、ただし N=606 全体補正ではない
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
log = logging.getLogger("spec_2_1_multiple_testing")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}
IS_RATIO = 0.75
N_TOTAL_TRIALS = 606  # P0-1 試行数棚卸し結果

# 採用済み閾値 (P0-2 と同じ)
ADOPTED_THRESHOLDS = [
    ("USD_JPY", "M15", "YZ_vol", 14, "gt", 30, "pct", 2),
    ("EUR_USD", "M15", "YZ_vol", 14, "gt", 80, "pct", 2),
    ("GBP_JPY", "M15", "YZ_vol", 14, "gt", 30, "pct", 2),
    ("USD_JPY", "M15", "CHOP", 14, "lt", 35, "abs", 2),
    ("EUR_USD", "M15", "CHOP", 14, "lt", 30, "abs", 2),
    ("GBP_JPY", "M15", "CHOP", 14, "lt", 30, "abs", 2),
    ("USD_JPY", "H1", "YZ_vol", 20, "gt", 0.00174, "abs", 5),
    ("EUR_USD", "H1", "YZ_vol", 20, "gt", 0.00143, "abs", 5),
    ("GBP_JPY", "H1", "YZ_vol", 20, "gt", 0.00175, "abs", 5),
    ("USD_JPY", "D1", "YZ_vol", 20, "gt", 50, "pct", 10),
    ("EUR_USD", "D1", "YZ_vol", 20, "gt", 75, "pct", 10),
    ("GBP_JPY", "D1", "YZ_vol", 20, "gt", 55, "pct", 10),
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
    out["past_return"] = (out["close"] - out["close"].shift(lookahead)) / out["close"].shift(lookahead)
    return out


def split_is_oos(df: pd.DataFrame, ratio: float = IS_RATIO):
    n = len(df)
    split_idx = int(n * ratio)
    return df.iloc[:split_idx], df.iloc[split_idx:]


def compute_tr_fast(future_return: np.ndarray, indicator: np.ndarray,
                    threshold: float, comparison: str) -> float:
    """高速 TR 計算 (numpy ベクトル化)。NaN 行は事前除外済み前提。"""
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


# ============================================================
# Permutation Test (n_perm 強化版、null TR 全保存)
# ============================================================
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
        "null_trs": null_trs_clean,  # 後で Romano-Wolf に使う
        "n_null_valid": len(null_trs_clean),
    }


# ============================================================
# 多重補正
# ============================================================
def bonferroni_correction(p_raw: float, n_total: int) -> float:
    return min(1.0, p_raw * n_total)


def holm_step_down(p_values: list[float], n_total: int) -> list[float]:
    """Holm step-down 補正。
    p_values は試行ごとの raw p。n_total は全ファミリー試行数。
    返値: 各試行の補正後 p (元の順序で)。
    """
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    p_holm = [None] * n
    max_so_far = 0.0
    for rank, (orig_idx, p) in enumerate(indexed, start=1):
        # Holm: p × (n_total - rank + 1)
        # n_total: 全ファミリー、rank: 順位
        adj = p * (n_total - rank + 1)
        adj = min(1.0, max(adj, max_so_far))
        max_so_far = adj
        p_holm[orig_idx] = adj
    return p_holm


def romano_wolf_12family(obs_trs: np.ndarray, null_trs_matrix: np.ndarray) -> np.ndarray:
    """Romano-Wolf step-down 12-family.
    obs_trs: 観測 TR [12]
    null_trs_matrix: [12, n_perm] 各試行の null TR
    返値: 各試行の Romano-Wolf 補正後 p [12]
    """
    n_trials, n_perm = null_trs_matrix.shape
    # 各 perm で全 12 試行のうち最大 null_TR
    null_max_per_perm = null_trs_matrix.max(axis=0)  # [n_perm]

    # Step-down: obs_TR を降順にソートし、順次「残り試行の null max」と比較
    indexed = sorted(enumerate(obs_trs), key=lambda x: -x[1])
    p_rw = np.empty(n_trials)
    remaining_trials = list(range(n_trials))
    last_p = 0.0
    for orig_idx, obs in indexed:
        if not remaining_trials:
            p_rw[orig_idx] = last_p
            continue
        # 残り試行の null max
        sub_null_max = null_trs_matrix[remaining_trials, :].max(axis=0)
        p = float((sub_null_max >= obs).mean())
        # monotonic: p_rw は順序を保つ (Holm-like enforcement)
        p = max(p, last_p)
        p_rw[orig_idx] = p
        last_p = p
        remaining_trials.remove(orig_idx)
    return p_rw


# ============================================================
# メイン
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_perm", type=int, default=20000, help="permutation 回数")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 Multiple Testing Correction (Step C P0-3)")
    print(f"  n_perm = {args.n_perm}, seed = {args.seed}")
    print(f"  N_TOTAL_TRIALS = {N_TOTAL_TRIALS} (P0-1 棚卸し結果)")
    print(f"  Bonferroni 厳密境界: α=0.05/{N_TOTAL_TRIALS} = {0.05/N_TOTAL_TRIALS:.2e}")
    print(f"  対象: 採用済み {len(ADOPTED_THRESHOLDS)} 閾値")
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

        # raw p
        null_trs = r["null_trs"]
        obs_tr = r["obs_tr"]
        p_raw = float((null_trs >= obs_tr).mean()) if not np.isnan(obs_tr) else None

        # 出力 (null_trs はファイル保存時に大きいのでサマリだけ表示)
        if p_raw is not None:
            print(f"  OBS_TR = {obs_tr:.4f}")
            print(f"  null: mean={null_trs.mean():.4f}, std={null_trs.std():.4f}, "
                  f"p95={np.percentile(null_trs, 95):.4f}, p99={np.percentile(null_trs, 99):.4f}, "
                  f"max={null_trs.max():.4f}")
            print(f"  p_raw = {p_raw:.6f} (1/{args.n_perm} = {1/args.n_perm:.6f} が最小分解能)")

        raw_results.append({
            "spec": spec,
            "obs_tr": obs_tr,
            "p_raw": p_raw,
            "null_trs": null_trs,  # 後で Romano-Wolf に使う
        })

    # ============================================================
    # 多重補正
    # ============================================================
    print(f"\n{'=' * 130}")
    print(f"多重補正の適用")
    print(f"{'=' * 130}")

    # 全試行で共通の n_perm でないと Romano-Wolf の matrix 構築できない
    # (各試行で n_null_valid が違う可能性があるので、min で揃える)
    n_perm_min = min(len(r["null_trs"]) for r in raw_results)
    null_matrix = np.array([r["null_trs"][:n_perm_min] for r in raw_results])  # [n_trials, n_perm_min]
    obs_trs_arr = np.array([r["obs_tr"] for r in raw_results])

    p_raws = [r["p_raw"] for r in raw_results]
    p_bonf_606 = [bonferroni_correction(p, N_TOTAL_TRIALS) for p in p_raws]
    p_holm_606 = holm_step_down(p_raws, N_TOTAL_TRIALS)
    p_holm_12 = holm_step_down(p_raws, len(p_raws))
    p_rw_12 = romano_wolf_12family(obs_trs_arr, null_matrix)

    # サマリ表
    print(f"\n{'Pair':<8} {'TF':<5} {'Indicator':<8} {'閾値':<12} {'OBS_TR':>8} {'p_raw':>10} "
          f"{'p_bonf_606':>12} {'p_holm_606':>12} {'p_holm_12':>11} {'p_rw_12':>9} {'判定':>20}")
    print("-" * 145)

    final_results = []
    for i, r in enumerate(raw_results):
        spec = r["spec"]
        pair, tf, ind_name, _, _, thr_spec, thr_kind, _ = spec
        thr_disp = f"{thr_spec}{thr_kind}"

        # 判定 (最も保守的な Bonferroni N=606 ベース)
        p_b = p_bonf_606[i]
        p_rw = p_rw_12[i]
        if p_b < 0.05:
            v = "🟢 全補正で生存"
        elif p_rw < 0.05:
            v = "🟡 12-family のみ生存"
        else:
            v = "🔴 全補正で棄却"

        print(f"{pair:<8} {tf:<5} {ind_name:<8} {thr_disp:<12} "
              f"{r['obs_tr']:>8.4f} {r['p_raw']:>10.6f} "
              f"{p_b:>12.6f} {p_holm_606[i]:>12.6f} "
              f"{p_holm_12[i]:>11.6f} {p_rw:>9.6f} {v:>20}")

        final_results.append({
            "pair": pair, "tf": tf, "indicator": ind_name,
            "threshold_spec": thr_spec, "threshold_kind": thr_kind,
            "obs_tr": r["obs_tr"],
            "p_raw": r["p_raw"],
            "p_bonferroni_606": p_b,
            "p_holm_606": p_holm_606[i],
            "p_holm_12": p_holm_12[i],
            "p_rw_12": float(p_rw),
            "verdict": v,
        })

    # JSON 保存 (null_trs は除外、容量爆発のため)
    out_json = ROOT / "data" / "spec_2_1_multiple_testing.json"
    out_json.write_text(json.dumps({
        "config": {
            "n_perm": args.n_perm,
            "n_total_trials": N_TOTAL_TRIALS,
            "bonferroni_alpha": 0.05 / N_TOTAL_TRIALS,
        },
        "results": final_results,
    }, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
