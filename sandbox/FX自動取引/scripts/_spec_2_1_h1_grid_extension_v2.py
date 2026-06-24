"""SPEC v2 - 2-1: H1 YZ_vol グリッド拡張 v2 (Karen / analyst レビュー対応)

## v1 からの強化点
1. **TR の bootstrap 95% CI** (B=1000) — TR の標本誤差を定量化
2. **low 群定義の感度分析** — LOW_PCT_RANGE を 5 通り変えて TR ランキングの安定性確認
3. **TR の隣接倍率 CI 重なり** — 「ピーク」が統計的に有意か判定

## 検証する論理
- v1 で「USD_JPY ×2.0 がピーク (TR=2.84)、×3.0 で TR=2.12 と減少」と書いた
- これが本当に統計的に有意なピークか? → TR の 95%CI を出して隣接倍率と重なるか確認
- low 群定義による TR ランキングの揺らぎ → low 群を変えても×2.0 がベストか?

## 出力
- data/spec_2_1_h1_grid_extension_v2.json
- 標準出力: 各 (pair, mult, low_setting) の TR + CI、サマリ表

## 使用例
  python scripts/_spec_2_1_h1_grid_extension_v2.py --n_boot 1000
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
log = logging.getLogger("spec_2_1_h1_grid_extension_v2")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD_H1 = 6
WINDOW_YZ = 20
MIN_SAMPLE = 30

H1_SPECS = [
    ("USD_JPY", 0.00174),
    ("EUR_USD", 0.00143),
    ("GBP_JPY", 0.00175),
]

ABS_MULTIPLIERS = [1.0, 1.5, 2.0, 2.5, 3.0]
LOW_SETTINGS = [
    (0, 25),    # 最低 1/4
    (10, 30),   # 低中
    (25, 50),   # 下半分後半 (Q2 v1 採用)
    (40, 60),   # 中央
    (50, 75),   # 上半分前半
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


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def add_returns(df: pd.DataFrame, lookahead: int) -> pd.DataFrame:
    out = df.copy()
    out["future_return"] = (out["close"].shift(-lookahead) - out["close"]) / out["close"]
    return out


# ============================================================
# bootstrap TR
# ============================================================
def bootstrap_tr(
    high_returns: np.ndarray, low_returns: np.ndarray,
    n_boot: int = 1000, seed: int = 42,
) -> dict:
    """TR = median(|ret|_high) / median(|ret|_low) の bootstrap CI"""
    if len(high_returns) < MIN_SAMPLE or len(low_returns) < MIN_SAMPLE:
        return {"error": "insufficient samples"}

    rng = np.random.default_rng(seed)
    boot_trs = []
    for _ in range(n_boot):
        h_idx = rng.integers(0, len(high_returns), size=len(high_returns))
        l_idx = rng.integers(0, len(low_returns), size=len(low_returns))
        h_med = np.median(high_returns[h_idx])
        l_med = np.median(low_returns[l_idx])
        if l_med > 0:
            boot_trs.append(h_med / l_med)

    boot_trs = np.array(boot_trs)
    if len(boot_trs) == 0:
        return {"error": "no valid bootstrap"}

    return {
        "tr_point": float(np.median(high_returns) / np.median(low_returns)),
        "tr_mean": float(boot_trs.mean()),
        "tr_std": float(boot_trs.std(ddof=1)),
        "tr_ci_low": float(np.percentile(boot_trs, 2.5)),
        "tr_ci_high": float(np.percentile(boot_trs, 97.5)),
        "n_high": len(high_returns),
        "n_low": len(low_returns),
    }


def eval_threshold_with_low(
    aligned: pd.DataFrame, threshold: float, low_pct_range: tuple[float, float],
    n_boot: int,
) -> dict:
    low_lo, low_hi = low_pct_range
    low_v_lo = float(np.percentile(aligned["ind"].values, low_lo))
    low_v_hi = float(np.percentile(aligned["ind"].values, low_hi))

    mask_high = aligned["ind"] > threshold
    mask_low = (aligned["ind"] >= low_v_lo) & (aligned["ind"] <= low_v_hi)

    high_returns = aligned.loc[mask_high, "abs_return"].values
    low_returns = aligned.loc[mask_low, "abs_return"].values

    boot = bootstrap_tr(high_returns, low_returns, n_boot=n_boot)
    boot["threshold"] = threshold
    boot["low_pct_range"] = list(low_pct_range)
    boot["low_value_range"] = [low_v_lo, low_v_hi]
    return boot


def analyze_pair(pair: str, spec_value: float, n_boot: int) -> dict:
    csv_path = ROOT / "data" / f"mt5_{pair}_H1_5y.csv"
    if not csv_path.exists():
        return {"error": f"missing csv: {csv_path}"}

    df = load_csv(csv_path)
    indicator = calc_yang_zhang(df, window=WINDOW_YZ)
    df_ret = add_returns(df, LOOKAHEAD_H1)
    aligned = pd.concat([df_ret[["future_return"]], indicator.rename("ind")], axis=1).dropna()
    aligned = aligned.copy()
    aligned["abs_return"] = aligned["future_return"].abs()

    n_total = len(aligned)
    print(f"  n_total={n_total}, bootstrap B={n_boot} ...")

    # 各 (multiplier, low_setting) で評価
    grid_results = []
    for mult in ABS_MULTIPLIERS:
        threshold = spec_value * mult
        for low_setting in LOW_SETTINGS:
            r = eval_threshold_with_low(aligned, threshold, low_setting, n_boot)
            r["multiplier"] = mult
            grid_results.append(r)

    return {
        "pair": pair,
        "spec_value": spec_value,
        "n_total": n_total,
        "grid_results": grid_results,
    }


def find_best_multiplier(pair_result: dict, low_setting: tuple[float, float]) -> dict:
    """指定 low setting で各倍率の TR を比較し、ピーク位置と隣接 CI 重なりを判定"""
    rows = [r for r in pair_result["grid_results"]
            if tuple(r["low_pct_range"]) == low_setting and "error" not in r]
    rows.sort(key=lambda r: r["multiplier"])

    if not rows:
        return {"error": "no valid rows"}

    # ピーク位置
    trs = [r["tr_point"] for r in rows]
    peak_idx = int(np.argmax(trs))
    peak = rows[peak_idx]

    # 隣接 CI 重なり判定
    overlap_with_neighbors = []
    for i, r in enumerate(rows):
        if i == peak_idx:
            continue
        # 重なり: r の CI が peak の CI と重なるか
        overlap = not (r["tr_ci_high"] < peak["tr_ci_low"] or r["tr_ci_low"] > peak["tr_ci_high"])
        overlap_with_neighbors.append({
            "multiplier": r["multiplier"],
            "tr_point": r["tr_point"],
            "ci": [r["tr_ci_low"], r["tr_ci_high"]],
            "overlaps_peak": overlap,
        })

    return {
        "low_setting": list(low_setting),
        "peak_multiplier": peak["multiplier"],
        "peak_tr": peak["tr_point"],
        "peak_ci": [peak["tr_ci_low"], peak["tr_ci_high"]],
        "overlap_with_neighbors": overlap_with_neighbors,
        "all_trs": [{"multiplier": r["multiplier"], "tr": r["tr_point"],
                     "ci": [r["tr_ci_low"], r["tr_ci_high"]],
                     "n_high": r["n_high"]} for r in rows],
    }


# ============================================================
# メイン
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_boot", type=int, default=1000)
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 H1 YZ_vol グリッド拡張 v2 (bootstrap CI + low 群感度)")
    print(f"  ABS_MULTIPLIERS = {ABS_MULTIPLIERS}")
    print(f"  LOW_SETTINGS    = {LOW_SETTINGS}")
    print(f"  n_boot          = {args.n_boot}")
    print(f"{'=' * 130}")

    results = []
    for pair, spec_value in H1_SPECS:
        print(f"\n--- {pair} (SPEC = {spec_value}) ---")
        r = analyze_pair(pair, spec_value, args.n_boot)
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        results.append(r)

        # low 設定 (25,50) (=Q2 v1 採用) のグリッド表示
        target_low = (25, 50)
        rows = [g for g in r["grid_results"]
                if tuple(g["low_pct_range"]) == target_low and "error" not in g]
        rows.sort(key=lambda x: x["multiplier"])

        print(f"  [low={target_low} (Q2 v1 採用)]")
        print(f"  {'×':>4} {'閾値':>10} {'n_high':>7} "
              f"{'TR点推定':>10} {'95%CI下':>10} {'95%CI上':>10} {'CI幅':>8}")
        for g in rows:
            ci_w = g["tr_ci_high"] - g["tr_ci_low"]
            print(f"  {g['multiplier']:>4.1f} {g['threshold']:>10.5f} "
                  f"{g['n_high']:>7} "
                  f"{g['tr_point']:>10.3f} {g['tr_ci_low']:>10.3f} "
                  f"{g['tr_ci_high']:>10.3f} {ci_w:>8.3f}")

        # 隣接 CI 重なり
        peak_info = find_best_multiplier(r, target_low)
        if "error" not in peak_info:
            print(f"  ピーク位置: ×{peak_info['peak_multiplier']} (TR={peak_info['peak_tr']:.3f}, "
                  f"CI=[{peak_info['peak_ci'][0]:.3f}, {peak_info['peak_ci'][1]:.3f}])")
            print(f"  隣接との CI 重なり:")
            for n in peak_info["overlap_with_neighbors"]:
                mark = " 重なり あり" if n["overlaps_peak"] else " 分離"
                print(f"    ×{n['multiplier']}: TR={n['tr_point']:.3f}, "
                      f"CI=[{n['ci'][0]:.3f}, {n['ci'][1]:.3f}]{mark}")

    # ============================================================
    # サマリ: low 群感度分析
    # ============================================================
    print(f"\n{'=' * 140}")
    print(f"low 群定義の感度分析 (各 low 設定で各倍率の TR ピーク位置がどう変わるか)")
    print(f"{'=' * 140}")
    print(f"{'Pair':<8} {'low':<10} "
          f"{'ピーク×':>8} {'ピーク TR':>10} {'95%CI':<22} "
          f"{'重なり数':>8}")
    print("-" * 140)
    for r in results:
        for low_setting in LOW_SETTINGS:
            peak_info = find_best_multiplier(r, low_setting)
            if "error" in peak_info:
                continue
            n_overlap = sum(1 for n in peak_info["overlap_with_neighbors"]
                           if n["overlaps_peak"])
            ci_s = f"[{peak_info['peak_ci'][0]:.2f}, {peak_info['peak_ci'][1]:.2f}]"
            print(f"{r['pair']:<8} {str(low_setting):<10} "
                  f"{peak_info['peak_multiplier']:>8.1f} "
                  f"{peak_info['peak_tr']:>10.3f} "
                  f"{ci_s:<22} "
                  f"{n_overlap:>4}/4")

    out_json = ROOT / "data" / "spec_2_1_h1_grid_extension_v2.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
