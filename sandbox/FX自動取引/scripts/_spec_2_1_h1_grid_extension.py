"""SPEC v2 - 2-1: H1 YZ_vol グリッド拡張 (Step C 新 P0 Q2)

P1-1b で H1 YZ_vol 3 ペアの Mode B 最良閾値が **グリッド上限 (SPEC × 1.5)** を全 fold で選定。
Q1 で指標–リターン関係が単峰 (単調増加) と確定したので、これは
「真の最適閾値がグリッド外、もっと高い帯」を意味する可能性が高い。

## 検証する具体的な問い
- H1 YZ_vol の真の最適閾値は SPEC × どこにあるか?
- SPEC × 1.5 → 2.0 → 3.0 → 5.0 と上げたとき、TR は伸び続けるか頭打ちか?
- ペアごとに頭打ち位置が違うか、それとも共通か?

## 検証方法
1. 各 H1 ペア (USD/EUR/GBP) × 全期間 (5 年)
2. グリッド: SPEC × {1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0} (8 点)
3. ついでに percentile グリッド: {80, 85, 90, 92.5, 95, 97.5, 99, 99.5} (8 点)
4. 各閾値で:
   - n_high / n_low (low: 5%ile 〜 50%ile 帯を fixed low として使用)
   - median |future_return|_high / median |future_return|_low
   - TR = median_high / median_low
5. グリッド上を TR が伸び続けるか、ピーク位置を持つかを判定

## 期待される結論パターン
- (a) SPEC × 2.0-3.0 で頭打ち → 新 SPEC 値はそこ、Mode B 結果と整合
- (b) SPEC × 5.0 でも上限選定継続 → グリッド設計が大きく外れている (再々設計必要)
- (c) ペアごとに頭打ちが違う → ペア別グリッドが必要

## 出力
- data/spec_2_1_h1_grid_extension.json
- 標準出力: 各ペアのグリッド評価テーブル + 頭打ち位置判定

## 使用例
  python scripts/_spec_2_1_h1_grid_extension.py
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
log = logging.getLogger("spec_2_1_h1_grid_extension")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD_H1 = 6
WINDOW_YZ = 20
MIN_SAMPLE = 30  # 各帯の最低サンプル数

# H1 YZ_vol 採用 SPEC 値 (Mode A 値 = P0-2 で permutation 通過済の閾値)
H1_SPECS = [
    ("USD_JPY", 0.00174),
    ("EUR_USD", 0.00143),
    ("GBP_JPY", 0.00175),
]

# abs グリッド (SPEC 倍率)
ABS_MULTIPLIERS = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
# percentile グリッド (右端に集中)
PCT_GRID = [80, 85, 90, 92.5, 95, 97.5, 99, 99.5]

# Low 群の固定範囲 (TR 評価のベースライン)
# Q1 検証で TR = median(high)/median(low) の low 群サイズ依存性が問題と判明
# → low を 25-50%ile 帯に固定することで low 群の安定性を確保
LOW_PCT_RANGE = (25, 50)


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
# 評価関数
# ============================================================
def eval_threshold_with_fixed_low(
    df: pd.DataFrame,  # ind, abs_return 列を含む
    threshold: float,
    low_pct_range: tuple[float, float],
) -> dict:
    """high: ind > threshold / low: ind が low_pct_range の percentile 帯
    TR = median(|return|_high) / median(|return|_low)
    """
    low_pct_lo, low_pct_hi = low_pct_range
    low_lo = float(np.percentile(df["ind"].values, low_pct_lo))
    low_hi = float(np.percentile(df["ind"].values, low_pct_hi))

    mask_high = df["ind"] > threshold
    mask_low = (df["ind"] >= low_lo) & (df["ind"] <= low_hi)

    n_high = int(mask_high.sum())
    n_low = int(mask_low.sum())

    if n_high < MIN_SAMPLE or n_low < MIN_SAMPLE:
        return {
            "threshold": threshold,
            "n_high": n_high, "n_low": n_low,
            "median_high": None, "median_low": None,
            "tr": None,
            "low_range": [low_lo, low_hi],
        }

    median_high = float(np.median(df.loc[mask_high, "abs_return"].values))
    median_low = float(np.median(df.loc[mask_low, "abs_return"].values))

    if median_low <= 0:
        tr = None
    else:
        tr = median_high / median_low

    return {
        "threshold": threshold,
        "n_high": n_high, "n_low": n_low,
        "median_high": median_high, "median_low": median_low,
        "tr": tr,
        "low_range": [low_lo, low_hi],
    }


def analyze_pair(pair: str, spec_value: float) -> dict:
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

    # abs グリッド評価
    abs_results = []
    for mult in ABS_MULTIPLIERS:
        threshold = spec_value * mult
        r = eval_threshold_with_fixed_low(aligned, threshold, LOW_PCT_RANGE)
        r["multiplier"] = mult
        # threshold が分布のどの percentile に対応するか
        pct_in_dist = float((aligned["ind"] <= threshold).mean() * 100)
        r["pct_in_dist"] = pct_in_dist
        abs_results.append(r)

    # percentile グリッド評価
    pct_results = []
    for pct in PCT_GRID:
        threshold = float(np.percentile(aligned["ind"].values, pct))
        r = eval_threshold_with_fixed_low(aligned, threshold, LOW_PCT_RANGE)
        r["pct"] = pct
        r["spec_multiplier"] = threshold / spec_value
        pct_results.append(r)

    # 頭打ち判定 (abs グリッドの TR 列を見る)
    tr_seq = [r["tr"] for r in abs_results]
    valid_tr = [(i, t) for i, t in enumerate(tr_seq) if t is not None]

    plateau_judgment = "計算不能"
    if len(valid_tr) >= 3:
        # ピーク位置と前後の差分
        peak_idx, peak_tr = max(valid_tr, key=lambda x: x[1])
        last_idx, last_tr = valid_tr[-1]
        # ピークが最後 → 頭打ち見えず
        # ピークが中盤 → 頭打ち位置 = ピーク
        # 末端で n_high < MIN_SAMPLE になって TR が None → サンプル制約による頭打ち
        if peak_idx == last_idx and len(valid_tr) == len(abs_results):
            plateau_judgment = f"🔴 末端ピーク (×{ABS_MULTIPLIERS[peak_idx]}) — グリッド外に最適あり"
        elif peak_idx == last_idx:
            plateau_judgment = f"🟡 末端ピーク (×{ABS_MULTIPLIERS[peak_idx]}) — それ以降サンプル不足"
        elif peak_idx == 0:
            plateau_judgment = f"🟢 SPEC値が最良 (×{ABS_MULTIPLIERS[peak_idx]})"
        else:
            mid_mult = ABS_MULTIPLIERS[peak_idx]
            plateau_judgment = f"🟢 中段でピーク (×{mid_mult})"

    return {
        "pair": pair,
        "spec_value": spec_value,
        "n_total": n_total,
        "abs_grid": abs_results,
        "pct_grid": pct_results,
        "plateau_judgment": plateau_judgment,
    }


# ============================================================
# メイン
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 H1 YZ_vol グリッド拡張 (Step C 新 P0 Q2)")
    print(f"  ABS_MULTIPLIERS = {ABS_MULTIPLIERS}")
    print(f"  PCT_GRID        = {PCT_GRID}")
    print(f"  LOW_PCT_RANGE   = {LOW_PCT_RANGE}")
    print(f"  MIN_SAMPLE      = {MIN_SAMPLE}")
    print(f"{'=' * 130}")

    results = []
    for pair, spec_value in H1_SPECS:
        print(f"\n--- {pair} (SPEC = {spec_value}) ---")
        r = analyze_pair(pair, spec_value)
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        results.append(r)

        print(f"  n_total = {r['n_total']}")

        # abs グリッド表示
        print(f"\n  [abs グリッド]")
        print(f"  {'×':>4} {'閾値':>10} {'%ile':>6} "
              f"{'n_high':>7} {'n_low':>6} {'med_h':>10} {'med_l':>10} {'TR':>7}")
        for ag in r["abs_grid"]:
            mh = f"{ag['median_high']:.5f}" if ag['median_high'] else "-"
            ml = f"{ag['median_low']:.5f}" if ag['median_low'] else "-"
            tr = f"{ag['tr']:.3f}" if ag['tr'] else "-"
            print(f"  {ag['multiplier']:>4.1f} {ag['threshold']:>10.5f} "
                  f"{ag['pct_in_dist']:>6.1f} "
                  f"{ag['n_high']:>7} {ag['n_low']:>6} {mh:>10} {ml:>10} {tr:>7}")

        # percentile グリッド表示
        print(f"\n  [percentile グリッド]")
        print(f"  {'%ile':>6} {'閾値':>10} {'×SPEC':>8} "
              f"{'n_high':>7} {'n_low':>6} {'med_h':>10} {'med_l':>10} {'TR':>7}")
        for pg in r["pct_grid"]:
            mh = f"{pg['median_high']:.5f}" if pg['median_high'] else "-"
            ml = f"{pg['median_low']:.5f}" if pg['median_low'] else "-"
            tr = f"{pg['tr']:.3f}" if pg['tr'] else "-"
            print(f"  {pg['pct']:>6.1f} {pg['threshold']:>10.5f} "
                  f"{pg['spec_multiplier']:>8.2f} "
                  f"{pg['n_high']:>7} {pg['n_low']:>6} {mh:>10} {ml:>10} {tr:>7}")

        print(f"\n  頭打ち判定: {r['plateau_judgment']}")

    # サマリ
    print(f"\n{'=' * 130}")
    print(f"H1 YZ_vol グリッド拡張サマリ")
    print(f"{'=' * 130}")
    print(f"{'Pair':<8} {'SPEC':<10} {'×1.0 TR':>10} {'×1.5 TR':>10} {'×2.0 TR':>10} "
          f"{'×3.0 TR':>10} {'×5.0 TR':>10} {'頭打ち判定':<40}")
    print("-" * 130)
    for r in results:
        tr_at = {ag['multiplier']: ag['tr'] for ag in r["abs_grid"]}
        tr_str = lambda m: f"{tr_at[m]:.3f}" if tr_at.get(m) else "-"
        print(f"{r['pair']:<8} {r['spec_value']:<10.5f} "
              f"{tr_str(1.0):>10} {tr_str(1.5):>10} {tr_str(2.0):>10} "
              f"{tr_str(3.0):>10} {tr_str(5.0):>10} {r['plateau_judgment']:<40}")

    out_json = ROOT / "data" / "spec_2_1_h1_grid_extension.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
