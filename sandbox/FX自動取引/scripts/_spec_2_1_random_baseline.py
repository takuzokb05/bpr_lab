"""SPEC v2 - 2-1 季節判定: Random Indicator Baseline (Permutation Test)

Step C P0-2: 採用閾値の OOS_TR 値が「ノイズと区別可能か」を直接検証する。

## 背景
仮説 H7 (三層生存=採用根拠) は Step B 文献調査で文献的に壊滅
(Bailey-López de Prado 2014 / Sullivan-Timmermann-White 1999 / Harvey-Liu-Zhu 2016)。
試行数 N≈606 (P0-1 棚卸し結果) で、Bailey 2014 False Strategy Theorem の境界を遥かに超える。
σ_TR=0.15 仮定の deflation 試算では、現状採用 TR の半数以上が「ノイズと区別不可」の危険度。
仮定値を実測値に置換しないと判断できない。

## 検証方法 (Permutation Test)
1. 価格系列 (close, future_return) は固定
2. 指標系列 (YZ_vol or CHOP) を時系列方向にランダムシャッフル
   - 自己相関が破壊され、純粋に「分布だけ同じノイズ」になる
   - 分位点 (percentile) は不変なので、同じ閾値で評価できる
3. 同じ percentile-based threshold 評価で TR を計算
4. 1000 permutation で TR の null 分布を構築
5. 現状採用閾値の OOS_TR が null 分布の何 percentile か判定

## Null 分布の解釈
- 採用 OOS_TR > 99%ile of null  → 強い採用根拠 (p < 0.01)
- 採用 OOS_TR > 95%ile of null  → 弱い採用根拠 (p < 0.05)
- 採用 OOS_TR < 95%ile of null  → **ノイズと区別不可、採用棄却**

## 対象 (SPEC_v2.md § 2-1 採用済 12閾値)
| Pair | Timeframe | Indicator | 採用閾値 (percentile) | 採用OOS_TR |
| USD_JPY | M15 | YZ_vol w=14 | > 0.00038 (30%ile) | 1.138 |
| EUR_USD | M15 | YZ_vol w=14 | > 0.00054 (80%ile) | 1.737 |
| GBP_JPY | M15 | YZ_vol w=14 | > 0.00039 (30%ile) | 1.229 |
| USD_JPY | M15 | CHOP   l=14 | < 35 | ~1.20 |
| EUR_USD | M15 | CHOP   l=14 | < 30 | ~1.21 |
| GBP_JPY | M15 | CHOP   l=14 | < 30 | ~1.26 |
| USD_JPY | H1  | YZ_vol w=20 | > 0.00174 | 1.916 |
| EUR_USD | H1  | YZ_vol w=20 | > 0.00143 | 1.922 |
| GBP_JPY | H1  | YZ_vol w=20 | > 0.00175 | 2.031 |
| USD_JPY | D1  | YZ_vol w=20 | > 0.00549 (50%ile) | 1.596 |
| EUR_USD | D1  | YZ_vol w=20 | > 0.00537 (75%ile) | 1.209 |
| GBP_JPY | D1  | YZ_vol w=20 | > 0.00570 (55%ile) | 1.724 |

## 出力
- data/spec_2_1_random_baseline.json
- 標準出力: 各閾値の TR vs null 分布 + p値

## 使用例
  python scripts/_spec_2_1_random_baseline.py --n_perm 1000
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
log = logging.getLogger("spec_2_1_random_baseline")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}
IS_RATIO = 0.75

# 採用済み閾値 (SPEC_v2.md § 2-1 から)
# (pair, tf, indicator, length/window, comparison, threshold_or_pct, kind)
# kind: "abs" = 絶対閾値, "pct" = percentile (number 0-100)
ADOPTED_THRESHOLDS = [
    # M15 YZ_vol (window=14, percentile-based)
    ("USD_JPY", "M15", "YZ_vol", 14, "gt", 30, "pct", 2),
    ("EUR_USD", "M15", "YZ_vol", 14, "gt", 80, "pct", 2),
    ("GBP_JPY", "M15", "YZ_vol", 14, "gt", 30, "pct", 2),
    # M15 CHOP (length=14, absolute threshold)
    ("USD_JPY", "M15", "CHOP", 14, "lt", 35, "abs", 2),
    ("EUR_USD", "M15", "CHOP", 14, "lt", 30, "abs", 2),
    ("GBP_JPY", "M15", "CHOP", 14, "lt", 30, "abs", 2),
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


# ============================================================
# データ準備
# ============================================================
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


# ============================================================
# TR 計算
# ============================================================
def compute_tr(df_with_ret: pd.DataFrame, indicator_values: np.ndarray,
               threshold: float, comparison: str) -> dict:
    """事前に計算済みの indicator (np.ndarray) を使って TR を測る。
    df_with_ret と indicator_values は同じインデックス順 / 同じ長さ前提。"""
    fr = df_with_ret["future_return"].values
    ind = indicator_values

    if comparison == "gt":
        mask_high = ind > threshold
    else:
        mask_high = ind < threshold

    mask_valid = ~np.isnan(ind) & ~np.isnan(fr)
    mask_high = mask_high & mask_valid
    mask_low = ~mask_high & mask_valid

    n_high = int(mask_high.sum())
    n_low = int(mask_low.sum())

    if n_high == 0 or n_low == 0:
        return {"n_high": n_high, "tr": None}

    median_high = float(np.median(np.abs(fr[mask_high])))
    median_low = float(np.median(np.abs(fr[mask_low])))

    if median_low <= 0:
        return {"n_high": n_high, "tr": None}

    tr = median_high / median_low
    return {"n_high": n_high, "tr": tr}


# ============================================================
# Permutation Test
# ============================================================
def permutation_test(
    pair: str,
    tf: str,
    indicator_name: str,
    param: int,
    comparison: str,
    threshold_spec: float,
    threshold_kind: str,
    years: int,
    n_perm: int,
    seed: int = 42,
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
    # データを揃える: 指標と return が両方有効な行のみ
    aligned = pd.concat([df_ret[["future_return", "past_return"]], indicator.rename("ind")], axis=1)
    aligned = aligned.dropna()

    is_df, oos_df = split_is_oos(aligned, IS_RATIO)

    # OOS の閾値を確定
    # threshold_kind == "pct": OOS 全体での percentile
    # threshold_kind == "abs": そのまま絶対値
    if threshold_kind == "pct":
        threshold_value = float(np.percentile(oos_df["ind"].values, threshold_spec))
    else:
        threshold_value = float(threshold_spec)

    # 観測 TR (元の指標)
    obs_result = compute_tr(oos_df, oos_df["ind"].values, threshold_value, comparison)
    obs_tr = obs_result["tr"]
    obs_n = obs_result["n_high"]

    # Null 分布: 指標シャッフル × n_perm 回
    rng = np.random.default_rng(seed)
    null_trs = []
    ind_array = oos_df["ind"].values.copy()

    for _ in range(n_perm):
        shuffled = rng.permutation(ind_array)
        # 閾値もシャッフル後の分布で再計算 (kind=pct の場合)
        # 分布は不変なので同じ percentile = 同じ threshold_value、abs も同じ
        # → 閾値は固定でOK
        result = compute_tr(oos_df, shuffled, threshold_value, comparison)
        if result["tr"] is not None:
            null_trs.append(result["tr"])

    null_arr = np.array(null_trs)
    if len(null_arr) == 0:
        return {"error": "no valid null TRs"}

    # p値: 観測値以上が null 分布で何割か
    p_value = float((null_arr >= obs_tr).mean()) if obs_tr is not None else None

    return {
        "pair": pair,
        "tf": tf,
        "indicator": indicator_name,
        "param": param,
        "comparison": comparison,
        "threshold_spec": threshold_spec,
        "threshold_kind": threshold_kind,
        "threshold_value": threshold_value,
        "obs_tr": obs_tr,
        "obs_n_high": obs_n,
        "null_n": len(null_arr),
        "null_mean": float(null_arr.mean()),
        "null_std": float(null_arr.std()),
        "null_p50": float(np.percentile(null_arr, 50)),
        "null_p90": float(np.percentile(null_arr, 90)),
        "null_p95": float(np.percentile(null_arr, 95)),
        "null_p99": float(np.percentile(null_arr, 99)),
        "null_max": float(null_arr.max()),
        "p_value": p_value,
    }


# ============================================================
# メイン
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_perm", type=int, default=1000, help="permutation 回数")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 Random Indicator Baseline (Permutation Test)")
    print(f"  n_perm = {args.n_perm}, seed = {args.seed}")
    print(f"  IS_RATIO = {IS_RATIO}, OOS で評価")
    print(f"  対象: SPEC_v2.md § 2-1 採用済 {len(ADOPTED_THRESHOLDS)} 閾値")
    print(f"{'=' * 130}")

    results = []
    for spec in ADOPTED_THRESHOLDS:
        pair, tf, ind_name, param, comp, thr_spec, thr_kind, years = spec
        print(f"\n--- {pair} / {tf} / {ind_name}({param}) {comp} {thr_spec}({thr_kind}) ---")
        r = permutation_test(
            pair, tf, ind_name, param, comp, thr_spec, thr_kind, years,
            args.n_perm, args.seed,
        )
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        results.append(r)

        # 判定
        obs_tr = r["obs_tr"]
        if obs_tr is None:
            verdict = "計算不能"
        elif obs_tr > r["null_p99"]:
            verdict = "🟢 強い採用根拠 (p < 0.01)"
        elif obs_tr > r["null_p95"]:
            verdict = "🟡 弱い採用根拠 (p < 0.05)"
        else:
            verdict = "🔴 ノイズと区別不可 (採用棄却推奨)"

        print(f"  threshold_value = {r['threshold_value']:.6f}")
        print(f"  OBS  : TR = {r['obs_tr']:.4f} (n_high = {r['obs_n_high']})")
        print(f"  NULL : mean={r['null_mean']:.4f}, std={r['null_std']:.4f}")
        print(f"         p50={r['null_p50']:.4f}, p90={r['null_p90']:.4f}, p95={r['null_p95']:.4f}, p99={r['null_p99']:.4f}, max={r['null_max']:.4f}")
        print(f"  p-value = {r['p_value']:.4f}")
        print(f"  判定: {verdict}")

    # サマリ
    print(f"\n{'=' * 130}")
    print(f"サマリ")
    print(f"{'=' * 130}")
    print(f"{'Pair':<8} {'TF':<5} {'指標':<8} {'閾値':<12} {'OBS_TR':>8} {'p95':>8} {'p99':>8} {'p-val':>8} {'判定':>30}")
    print("-" * 130)
    for r in results:
        if r["obs_tr"] is None:
            continue
        if r["obs_tr"] > r["null_p99"]:
            v = "🟢 強い (p<0.01)"
        elif r["obs_tr"] > r["null_p95"]:
            v = "🟡 弱い (p<0.05)"
        else:
            v = "🔴 区別不可 (棄却推奨)"
        thr_disp = f"{r['threshold_spec']}{r['threshold_kind']}"
        print(f"{r['pair']:<8} {r['tf']:<5} {r['indicator']:<8} {thr_disp:<12} "
              f"{r['obs_tr']:>8.4f} {r['null_p95']:>8.4f} {r['null_p99']:>8.4f} "
              f"{r['p_value']:>8.4f} {v:>30}")

    out_json = ROOT / "data" / "spec_2_1_random_baseline.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
