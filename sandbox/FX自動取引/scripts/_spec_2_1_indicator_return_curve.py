"""SPEC v2 - 2-1: 指標–リターン曲線 (Step C 新 P0 Q1)

P1-1b で M15 YZ_vol 3ペアの Mode B 最良閾値が 10%ile / 90%ile に二極化した。
これは指標–リターン関係が単峰でない可能性を示唆する。

## 検証する具体的な問い
- 各ペア × 各時間軸で、YZ_vol / CHOP の値域と |future_return| の関係は単峰か二峰か?
- 単峰なら → グリッド設計を見直すだけで済む (SPEC v2 § 2-1 数値の方向性は維持)
- 二峰なら → 指標選定そのものを再考、OPERATING_MODEL § 2-1 の概念設計まで波及

## 検証方法
1. 各 (pair, tf, indicator) で 20 分位 (5% 刻み) に区切る
2. 各分位ごとに |future_return| の median / mean / std / n を計算
3. 形状判定:
   - 線形回帰 (y = a*x + b): R²_linear / slope
   - 二次回帰 (y = a*x^2 + b*x + c): R²_quad / 二次係数 a
   - argmax / argmin の位置 (両端 vs 中央)
4. 形状分類:
   - **単調増加** : 線形 R²>0.7 かつ slope>0
   - **単調減少** : 線形 R²>0.7 かつ slope<0
   - **逆U字 (単峰、中央高)** : 二次 R²>0.7 かつ a<0 かつ argmax が中央 4-15
   - **U字 (二峰、両端高)** : 二次 R²>0.7 かつ a>0 かつ argmin が中央 4-15
   - **端立ち (右肩)** : argmax が q=18-19、線形 R² も中程度
   - **端立ち (左肩)** : argmax が q=0-1、線形 R² も中程度
   - **不明瞭** : どれにも当てはまらない

## 期待される結論パターン
- (a) 単峰 (逆U字 / 単調) → グリッド設計を見直す、SPEC v2 § 2-1 数値の方向性は維持
- (b) 二峰 (U字) → 指標選定そのものを再考、OPERATING_MODEL § 2-1 まで波及
- (c) ペア依存 → H4 (ペア別閾値) の根拠が深まるが複雑化

## 出力
- data/spec_2_1_return_curve.json
- 標準出力: 各 (pair, tf, indicator) の分位テーブル + 形状判定

## 使用例
  python scripts/_spec_2_1_indicator_return_curve.py
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
log = logging.getLogger("spec_2_1_indicator_return_curve")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
LOOKAHEAD = {"M15": 24, "H1": 6, "D1": 5}
N_QUANTILES = 20  # 5% 刻み

# 検証対象 (pair, tf, indicator, length/window, years)
TARGETS = [
    # M15: YZ_vol w=14, CHOP l=14, 2 年
    ("USD_JPY", "M15", "YZ_vol", 14, 2),
    ("EUR_USD", "M15", "YZ_vol", 14, 2),
    ("GBP_JPY", "M15", "YZ_vol", 14, 2),
    ("USD_JPY", "M15", "CHOP", 14, 2),
    ("EUR_USD", "M15", "CHOP", 14, 2),
    ("GBP_JPY", "M15", "CHOP", 14, 2),
    # H1: YZ_vol w=20, 5 年
    ("USD_JPY", "H1", "YZ_vol", 20, 5),
    ("EUR_USD", "H1", "YZ_vol", 20, 5),
    ("GBP_JPY", "H1", "YZ_vol", 20, 5),
    # D1: YZ_vol w=20, 10 年
    ("USD_JPY", "D1", "YZ_vol", 20, 10),
    ("EUR_USD", "D1", "YZ_vol", 20, 10),
    ("GBP_JPY", "D1", "YZ_vol", 20, 10),
]


# ============================================================
# 指標計算 (P1-1 / P1-1b と同じ)
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
# 形状判定
# ============================================================
def fit_polynomial(x: np.ndarray, y: np.ndarray, degree: int) -> tuple[float, np.ndarray]:
    """次数 degree の多項式フィット。R² と係数 (高次→定数) を返す。"""
    if len(x) <= degree:
        return 0.0, np.zeros(degree + 1)
    coef = np.polyfit(x, y, degree)
    y_pred = np.polyval(coef, x)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return r2, coef


def classify_shape(quantile_medians: np.ndarray) -> dict:
    """20 分位の median |return| 系列から形状を判定する。

    判定優先順:
    1. 線形 R²>0.7 → 単調 (slope sign)
    2. 二次 R²>0.7 かつ 線形比 +0.15 改善 → U字 / 逆U字 (a sign + argmax/min 位置)
    3. argmax/argmin が端 → 端立ち
    4. それ以外 → 不明瞭
    """
    n = len(quantile_medians)
    x = np.arange(n, dtype=float)
    y = quantile_medians

    r2_linear, coef_lin = fit_polynomial(x, y, 1)
    r2_quad, coef_quad = fit_polynomial(x, y, 2)

    slope = float(coef_lin[0])
    a_quad = float(coef_quad[0])
    argmax = int(np.argmax(y))
    argmin = int(np.argmin(y))

    # 中央領域 (5-14, つまり 25%-70%ile 帯)
    central = lambda i: 5 <= i <= 14
    edge_low = lambda i: i <= 1
    edge_high = lambda i: i >= n - 2

    if r2_linear > 0.7:
        if slope > 0:
            shape = "単調増加"
        else:
            shape = "単調減少"
    elif r2_quad > 0.7 and (r2_quad - r2_linear) > 0.15:
        if a_quad < 0 and central(argmax):
            shape = "逆U字 (単峰)"
        elif a_quad > 0 and central(argmin):
            shape = "U字 (二峰)"
        elif a_quad < 0:
            shape = f"逆U字様 (峰=q{argmax})"
        else:
            shape = f"U字様 (谷=q{argmin})"
    elif edge_high(argmax) and not edge_high(argmin):
        shape = f"右肩 (max=q{argmax})"
    elif edge_low(argmax) and not edge_low(argmin):
        shape = f"左肩 (max=q{argmax})"
    else:
        shape = f"不明瞭 (max=q{argmax}, min=q{argmin})"

    # ピーク・谷の絶対比 (max/min) — 形状の強さ
    peak_trough_ratio = float(y[argmax] / y[argmin]) if y[argmin] > 0 else None

    return {
        "shape": shape,
        "r2_linear": r2_linear,
        "r2_quadratic": r2_quad,
        "slope": slope,
        "quadratic_coef": a_quad,
        "argmax": argmax,
        "argmin": argmin,
        "peak_value": float(y[argmax]),
        "trough_value": float(y[argmin]),
        "peak_trough_ratio": peak_trough_ratio,
    }


# ============================================================
# メイン処理
# ============================================================
def analyze_target(pair: str, tf: str, indicator_name: str, param: int, years: int) -> dict:
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

    if len(aligned) < N_QUANTILES * 30:  # 各分位最低 30 サンプル
        return {"error": f"insufficient samples: n={len(aligned)}"}

    # 20 分位に区切る (rank-based qcut で同値による偏りを防ぐ)
    aligned = aligned.copy()
    aligned["abs_return"] = aligned["future_return"].abs()
    try:
        aligned["q"] = pd.qcut(aligned["ind"].rank(method="first"), N_QUANTILES, labels=False)
    except ValueError as e:
        return {"error": f"qcut failed: {e}"}

    # 各分位の統計
    quantile_stats = []
    for q in range(N_QUANTILES):
        sub = aligned[aligned["q"] == q]
        if len(sub) == 0:
            quantile_stats.append({"q": q, "n": 0})
            continue
        quantile_stats.append({
            "q": q,
            "n": int(len(sub)),
            "ind_min": float(sub["ind"].min()),
            "ind_max": float(sub["ind"].max()),
            "ind_median": float(sub["ind"].median()),
            "abs_return_median": float(sub["abs_return"].median()),
            "abs_return_mean": float(sub["abs_return"].mean()),
            "abs_return_std": float(sub["abs_return"].std()),
        })

    # 形状判定
    medians = np.array([qs.get("abs_return_median", np.nan) for qs in quantile_stats])
    if np.any(np.isnan(medians)):
        return {"error": "missing quantiles"}
    shape_info = classify_shape(medians)

    return {
        "pair": pair,
        "tf": tf,
        "indicator": indicator_name,
        "param": param,
        "years": years,
        "n_total": int(len(aligned)),
        "lookahead": LOOKAHEAD[tf],
        "quantile_stats": quantile_stats,
        "shape": shape_info,
    }


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    print(f"\n{'=' * 130}")
    print(f"SPEC v2 - 2-1 指標–リターン曲線 (Step C 新 P0 Q1: 単峰性検証)")
    print(f"  N_QUANTILES = {N_QUANTILES}")
    print(f"  LOOKAHEAD   = {LOOKAHEAD}")
    print(f"  対象        = {len(TARGETS)} (pair, tf, indicator)")
    print(f"{'=' * 130}")

    results = []
    for pair, tf, ind_name, param, years in TARGETS:
        print(f"\n--- {pair} / {tf} / {ind_name}({param}) ---")
        r = analyze_target(pair, tf, ind_name, param, years)
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        results.append(r)

        # 分位テーブル (簡略表示: 5 分位ごと)
        print(f"  n_total = {r['n_total']}")
        print(f"  {'q':>3} {'ind_med':>10} {'|ret|_med':>12} {'|ret|_mean':>12} {'n':>6}")
        for qs in r["quantile_stats"]:
            if qs["n"] == 0:
                continue
            if qs["q"] % 2 != 0 and qs["q"] not in (19,):  # 偶数 + 最後だけ表示
                continue
            ind_med_s = f"{qs['ind_median']:.5f}" if qs.get('ind_median') else "-"
            ret_med_s = f"{qs['abs_return_median']:.6f}"
            ret_mean_s = f"{qs['abs_return_mean']:.6f}"
            print(f"  {qs['q']:>3} {ind_med_s:>10} {ret_med_s:>12} {ret_mean_s:>12} {qs['n']:>6}")

        # 形状判定
        s = r["shape"]
        print(f"  形状判定: {s['shape']}")
        print(f"    R²_linear={s['r2_linear']:.3f} (slope={s['slope']:.2e})")
        print(f"    R²_quad  ={s['r2_quadratic']:.3f} (quad_coef={s['quadratic_coef']:.2e})")
        ptr = s['peak_trough_ratio']
        ptr_s = f", peak/trough={ptr:.2f}" if ptr else ""
        print(f"    argmax=q{s['argmax']} (med={s['peak_value']:.6f}) / "
              f"argmin=q{s['argmin']} (med={s['trough_value']:.6f}){ptr_s}")

    # ============================================================
    # サマリ
    # ============================================================
    print(f"\n{'=' * 130}")
    print(f"形状判定サマリ")
    print(f"{'=' * 130}")
    print(f"{'Pair':<8} {'TF':<5} {'指標':<8} {'形状':<25} "
          f"{'R²_lin':>7} {'R²_quad':>8} {'argmax':>7} {'argmin':>7} {'P/T比':>7}")
    print("-" * 130)
    for r in results:
        s = r["shape"]
        ptr_s = f"{s['peak_trough_ratio']:.2f}" if s['peak_trough_ratio'] else "-"
        print(f"{r['pair']:<8} {r['tf']:<5} {r['indicator']:<8} {s['shape']:<25} "
              f"{s['r2_linear']:>7.3f} {s['r2_quadratic']:>8.3f} "
              f"{s['argmax']:>7} {s['argmin']:>7} {ptr_s:>7}")

    # 集計: 形状の分布
    print(f"\n--- 形状カテゴリ別集計 ---")
    shape_groups: dict[str, list[str]] = {}
    for r in results:
        cat = r["shape"]["shape"].split(" ")[0]  # 主カテゴリ
        key = cat
        shape_groups.setdefault(key, []).append(f"{r['pair']}/{r['tf']}/{r['indicator']}")
    for k, v in sorted(shape_groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  [{k}] {len(v)} 件: {', '.join(v)}")

    out_json = ROOT / "data" / "spec_2_1_return_curve.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
