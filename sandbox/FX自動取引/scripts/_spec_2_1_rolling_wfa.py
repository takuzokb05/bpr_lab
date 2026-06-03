"""SPEC v2 - 2-1 季節判定: Rolling Walk-Forward Analysis (Step C P1-1)

採用済み 12 閾値を anchored expanding 5-fold WFA で評価し、fold 横断の安定性を検証。

## 背景
P0-3 で 12 閾値の多重補正後分類 (AAA 5 / AA 2 / A 3 / 🔴 2) を確定したが、これらは
すべて IS:OOS = 75:25 の **単一分割** で得られた値。Pardo (2008) や López de Prado (2018)
の標準は「k-fold WFA」で fold 横断の安定性を確認すること。単一分割の OOS が偶然良かった
だけの可能性があり、P1-1 で fold 横断の TR 再現性を確認する。

## 二段アプローチ

### Mode A: 閾値固定 (lock-step)
P0-3 で確定した閾値を fold 全体で固定し、各 fold OOS で TR を計測。
「現状の閾値値」が複数期間で robust かを評価。**本スクリプトはこちらを実装**。

### Mode B: 閾値再選定 (re-optimize) — 次段階
各 fold の IS で閾値を最良選定し、fold 間で「選ばれる閾値」のドリフトを測る。
ドリフトが大きい = 過学習の兆候 (Pardo 2008 plateau 原則)。

## fold 設計 (anchored expanding 5-fold)
データ全体を 6 等分し、各 fold で expanding IS + 次区間 OOS:
- fold 1: IS [0, 1/6], OOS [1/6, 2/6]
- fold 2: IS [0, 2/6], OOS [2/6, 3/6]
- fold 3: IS [0, 3/6], OOS [3/6, 4/6]
- fold 4: IS [0, 4/6], OOS [4/6, 5/6]
- fold 5: IS [0, 5/6], OOS [5/6, 6/6]

各 fold OOS = 全データの 1/6 ≈ 16.67%

## 評価指標
各閾値 × 各 fold OOS:
- TR (片側中央値比)
- n_high (閾値超過件数)

集計 (5 fold):
- TR_mean
- TR_std
- TR_min (最悪 fold)
- n_pass (TR > 1.0 を満たす fold 数 / 5)

## 判定
- 5/5 で TR > 1.0 → **強い安定性** (P0-3 クラスを維持)
- 4/5 → 中程度の安定性
- ≤3/5 → **不安定** (採用棄却検討、過学習疑い)

## 出力
- data/spec_2_1_rolling_wfa.json
- 標準出力: 各閾値の fold 別 TR + 集計判定
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
log = logging.getLogger("spec_2_1_rolling_wfa")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}
N_FOLDS = 5

# 採用済み閾値 (P0-3 と同じ)
# (pair, tf, indicator, length/window, comparison, threshold_or_pct, kind, years, p0_3_class)
ADOPTED_THRESHOLDS = [
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


def compute_tr_oos(oos_df: pd.DataFrame, threshold: float, comparison: str) -> dict:
    """OOS で TR を計算。oos_df は ind, future_return 列を含む。"""
    df = oos_df.dropna(subset=["ind", "future_return"])
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


# ============================================================
# Anchored Expanding 5-fold WFA
# ============================================================
def run_wfa_for_threshold(
    pair: str, tf: str, indicator_name: str, param: int,
    comparison: str, threshold_spec, threshold_kind: str, years: int,
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

    # 閾値の確定 (pct なら全データ分布で確定、abs ならそのまま)
    if threshold_kind == "pct":
        # 注: P0-2/P0-3 では OOS 区間で percentile を計算していた。
        # WFA では「閾値固定」のため、データ全体で percentile を計算する。
        threshold_value = float(np.percentile(aligned["ind"].values, threshold_spec))
    else:
        threshold_value = float(threshold_spec)

    fold_results = []
    for k in range(1, N_FOLDS + 1):
        is_end = k * fold_size
        oos_end = (k + 1) * fold_size if k < N_FOLDS else n
        oos_df = aligned.iloc[is_end:oos_end]
        if len(oos_df) == 0:
            fold_results.append({"fold": k, "n_oos": 0, "tr": None, "n_high": 0})
            continue
        result = compute_tr_oos(oos_df, threshold_value, comparison)
        fold_results.append({
            "fold": k,
            "n_oos": len(oos_df),
            "tr": result["tr"],
            "n_high": result["n_high"],
            "oos_period": [str(oos_df.index.min()), str(oos_df.index.max())],
        })

    # 集計
    valid_trs = [f["tr"] for f in fold_results if f["tr"] is not None]
    n_pass = sum(1 for tr in valid_trs if tr > 1.0)

    if valid_trs:
        tr_mean = float(np.mean(valid_trs))
        tr_std = float(np.std(valid_trs, ddof=1)) if len(valid_trs) > 1 else 0.0
        tr_min = float(min(valid_trs))
        tr_max = float(max(valid_trs))
    else:
        tr_mean = tr_std = tr_min = tr_max = None

    return {
        "pair": pair, "tf": tf, "indicator": indicator_name, "param": param,
        "comparison": comparison, "threshold_spec": threshold_spec,
        "threshold_kind": threshold_kind, "threshold_value": threshold_value,
        "fold_results": fold_results,
        "tr_mean": tr_mean,
        "tr_std": tr_std,
        "tr_min": tr_min,
        "tr_max": tr_max,
        "n_pass": n_pass,
        "n_total_folds": len(valid_trs),
    }


# ============================================================
# メイン
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 Rolling Walk-Forward Analysis (Step C P1-1, Mode A: 閾値固定)")
    print(f"  N_FOLDS = {N_FOLDS} (anchored expanding)")
    print(f"  対象: 採用済み {len(ADOPTED_THRESHOLDS)} 閾値")
    print(f"{'=' * 130}")

    results = []
    for spec in ADOPTED_THRESHOLDS:
        pair, tf, ind_name, param, comp, thr_spec, thr_kind, years, p0_3_class = spec
        print(f"\n--- {pair} / {tf} / {ind_name}({param}) {comp} {thr_spec}({thr_kind})  [{p0_3_class}] ---")
        r = run_wfa_for_threshold(pair, tf, ind_name, param, comp, thr_spec, thr_kind, years)
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        r["p0_3_class"] = p0_3_class
        results.append(r)

        print(f"  threshold_value = {r['threshold_value']:.6f}")
        print(f"  {'fold':<5} {'period':<28} {'n_oos':>7} {'n_high':>7} {'TR':>9}")
        for f in r["fold_results"]:
            tr_s = f"{f['tr']:.4f}" if f["tr"] is not None else "  -"
            mark = " ✓" if (f["tr"] is not None and f["tr"] > 1.0) else " ✗"
            period = f["oos_period"][0][:10] + " - " + f["oos_period"][1][:10] if "oos_period" in f else "-"
            print(f"  {f['fold']:<5} {period:<28} {f['n_oos']:>7} {f['n_high']:>7} {tr_s:>9}{mark}")

        if r["tr_mean"] is not None:
            print(f"  集計: mean={r['tr_mean']:.4f}, std={r['tr_std']:.4f}, "
                  f"min={r['tr_min']:.4f}, max={r['tr_max']:.4f}, "
                  f"n_pass={r['n_pass']}/{r['n_total_folds']}")

        # 安定性判定
        if r["n_pass"] == r["n_total_folds"] and r["n_total_folds"] >= 5:
            stability = "🟢 強い安定性 (5/5)"
        elif r["n_pass"] >= 4:
            stability = "🟡 中程度の安定性 (4/5)"
        else:
            stability = "🔴 不安定 (≤3/5)"
        print(f"  安定性: {stability}")
        r["stability"] = stability

    # ============================================================
    # サマリ
    # ============================================================
    print(f"\n{'=' * 130}")
    print(f"WFA サマリ (P0-3 クラス × WFA 安定性)")
    print(f"{'=' * 130}")
    print(f"{'Pair':<8} {'TF':<5} {'指標':<8} {'閾値':<14} {'P0-3':<6} "
          f"{'TR_mean':>8} {'TR_std':>7} {'TR_min':>8} {'n_pass':>8} {'安定性':<25}")
    print("-" * 130)
    for r in results:
        thr_disp = f"{r['threshold_spec']}{r['threshold_kind']}"
        tr_mean = f"{r['tr_mean']:.4f}" if r['tr_mean'] is not None else "  -"
        tr_std = f"{r['tr_std']:.4f}" if r['tr_std'] is not None else "  -"
        tr_min = f"{r['tr_min']:.4f}" if r['tr_min'] is not None else "  -"
        print(f"{r['pair']:<8} {r['tf']:<5} {r['indicator']:<8} {thr_disp:<14} "
              f"{r['p0_3_class']:<6} {tr_mean:>8} {tr_std:>7} {tr_min:>8} "
              f"{r['n_pass']}/{r['n_total_folds']:<6} {r['stability']:<25}")

    # P0-3 クラス × WFA 安定性のクロス集計
    print(f"\n{'=' * 130}")
    print(f"クロス集計: P0-3 クラス × WFA 安定性")
    print(f"{'=' * 130}")
    cross = {}
    for r in results:
        key = (r["p0_3_class"], r["stability"][:2])  # 🟢/🟡/🔴
        cross[key] = cross.get(key, 0) + 1
    print(f"{'P0-3 \\ WFA':<10} {'🟢 強':>8} {'🟡 中':>8} {'🔴 弱':>8}")
    for cls in ["AAA", "AA", "A", "🔴"]:
        green = cross.get((cls, "🟢"), 0)
        yellow = cross.get((cls, "🟡"), 0)
        red = cross.get((cls, "🔴"), 0)
        print(f"{cls:<10} {green:>8} {yellow:>8} {red:>8}")

    # JSON 保存
    out_json = ROOT / "data" / "spec_2_1_rolling_wfa.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
