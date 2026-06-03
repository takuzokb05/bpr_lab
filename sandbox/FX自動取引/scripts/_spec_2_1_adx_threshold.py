"""SPEC v2 - 2-1 季節判定: ADX trending 閾値（M15 短期）の Walk-forward 検証 v2

researcher 知見を反映した評価関数:

1. **Trendiness Ratio (TR)**: ADX>閾値時の |future_return| の中央値 / 全期間中央値
   - >1.0 なら「ADX>閾値が大きな値動きを当てている」
   - 戦略フリー、相対的、飽和しにくい

2. **Directional Persistence Rate (DPR)**: ADX>閾値時、直近のリターン符号が次N本でも同じ符号で持続する割合
   - 戦略フリー、トレンド継続性を直接測定

3. **Sample Size n_triggers**: 閾値を上げるとサンプル数が減る → 統計的有意性

過剰最適化検出:
- IS で各閾値の TR / DPR を測定 → IS 最良閾値を選定
- OOS で同じ閾値の TR / DPR を測定 → 乖離率
- IS/OOS の閾値間 Spearman 順位相関（researcher 推奨）
- 隣接閾値の安定性（±2 範囲で同等帯か）

入力: data/mt5_*_M15_2y.csv（USD_JPY / EUR_USD / GBP_JPY）
出力: data/spec_2_1_adx_summary.json + 標準出力テーブル
"""
from __future__ import annotations

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
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("spec_2_1")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
PAIRS = {
    "USD_JPY": "mt5_USD_JPY_M15_2y.csv",
    "EUR_USD": "mt5_EUR_USD_M15_2y.csv",
    "GBP_JPY": "mt5_GBP_JPY_M15_2y.csv",
}

ADX_GRID = [18, 20, 22, 25, 28, 30, 35]  # researcher 推奨で 35 追加
ADX_PERIOD = 14
ATR_PERIOD = 14
LOOKAHEAD_BARS = 24   # M15 × 24 = 6時間（24時間は飽和したため短縮）
IS_RATIO = 0.75       # researcher 推奨 75/25


# ============================================================
# データ読込・前処理
# ============================================================
def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    adx_df = ta.adx(out["high"], out["low"], out["close"], length=ADX_PERIOD)
    out["adx"] = adx_df[f"ADX_{ADX_PERIOD}"]
    out["atr"] = ta.atr(out["high"], out["low"], out["close"], length=ATR_PERIOD)
    # future_return: N本後のリターン（pip 換算ではなく% で扱い、ペア間比較可）
    out["future_return"] = (
        out["close"].shift(-LOOKAHEAD_BARS) - out["close"]
    ) / out["close"]
    # past_return: 直近N本のリターン（持続性測定用）
    out["past_return"] = (
        out["close"] - out["close"].shift(LOOKAHEAD_BARS)
    ) / out["close"].shift(LOOKAHEAD_BARS)
    return out.dropna()


# ============================================================
# 評価関数
# ============================================================
def evaluate_threshold(df: pd.DataFrame, adx_thr: float) -> dict:
    """
    ADX > 閾値 のサブセットと、それ以外で future_return の特性を比較。

    Returns:
        n_triggers: ADX 超過サンプル数
        median_abs_return_high: ADX > 閾値時の |future_return| の中央値
        median_abs_return_low:  ADX <= 閾値時の |future_return| の中央値
        trendiness_ratio: high / low（>1 なら ADX>閾値が大きい値動きを捉えている）
        persistence_rate: ADX>閾値時、past_return と future_return の符号が一致する割合
    """
    high = df[df["adx"] > adx_thr]
    low = df[df["adx"] <= adx_thr]

    n_triggers = len(high)
    if n_triggers < 50:
        return {
            "n_triggers": n_triggers,
            "median_abs_return_high": None,
            "median_abs_return_low": None,
            "trendiness_ratio": None,
            "persistence_rate": None,
        }

    median_high = float(high["future_return"].abs().median())
    median_low = float(low["future_return"].abs().median()) if len(low) > 0 else 1e-9
    tr = median_high / median_low if median_low > 0 else None

    # Persistence: ADX>閾値時、past_return と future_return の符号が一致する割合
    valid = high.dropna(subset=["past_return", "future_return"])
    if len(valid) > 0:
        same_sign = (np.sign(valid["past_return"]) == np.sign(valid["future_return"])).sum()
        pr = float(same_sign / len(valid))
    else:
        pr = None

    return {
        "n_triggers": n_triggers,
        "median_abs_return_high": median_high,
        "median_abs_return_low": median_low,
        "trendiness_ratio": tr,
        "persistence_rate": pr,
    }


# ============================================================
# IS/OOS 分割
# ============================================================
def split_is_oos(df: pd.DataFrame, ratio: float = IS_RATIO) -> tuple:
    n = len(df)
    split_idx = int(n * ratio)
    return df.iloc[:split_idx], df.iloc[split_idx:]


def evaluate_pair(pair: str, csv_path: Path) -> dict:
    df = load_csv(csv_path)
    df = add_indicators(df)
    is_df, oos_df = split_is_oos(df, IS_RATIO)

    print(f"\n{'='*120}")
    print(
        f"{pair}: total {len(df)} bars, "
        f"IS {len(is_df)} ({is_df.index.min().date()} - {is_df.index.max().date()}), "
        f"OOS {len(oos_df)} ({oos_df.index.min().date()} - {oos_df.index.max().date()})"
    )
    print(f"{'='*120}")

    is_results = {}
    oos_results = {}
    for adx_thr in ADX_GRID:
        is_results[adx_thr] = evaluate_threshold(is_df, adx_thr)
        oos_results[adx_thr] = evaluate_threshold(oos_df, adx_thr)

    # 表示
    print(f"{'ADX>閾値':<8} | {'IS_TR':>6} {'IS_DPR':>7} {'IS_N':>5} | "
          f"{'OOS_TR':>7} {'OOS_DPR':>8} {'OOS_N':>6} | {'ΔTR':>7} {'ΔDPR':>7}")
    print("-" * 90)

    for adx_thr in ADX_GRID:
        ir = is_results[adx_thr]
        or_ = oos_results[adx_thr]

        def fmt(v, decimals=3):
            return f"{v:.{decimals}f}" if v is not None else "  -"

        delta_tr = (or_["trendiness_ratio"] or 0) - (ir["trendiness_ratio"] or 0) if ir["trendiness_ratio"] and or_["trendiness_ratio"] else 0
        delta_dpr = (or_["persistence_rate"] or 0) - (ir["persistence_rate"] or 0) if ir["persistence_rate"] and or_["persistence_rate"] else 0

        print(
            f"{adx_thr:<8} | {fmt(ir['trendiness_ratio']):>6} {fmt(ir['persistence_rate']):>7} {ir['n_triggers']:>5} | "
            f"{fmt(or_['trendiness_ratio']):>7} {fmt(or_['persistence_rate']):>8} {or_['n_triggers']:>6} | "
            f"{delta_tr:>+7.3f} {delta_dpr:>+7.3f}"
        )

    # IS で最良 trendiness_ratio の閾値（DPR との合成スコアも）
    valid_is = {k: v for k, v in is_results.items() if v["trendiness_ratio"] is not None}
    if valid_is:
        best_tr = max(valid_is.items(), key=lambda kv: kv[1]["trendiness_ratio"])
        best_dpr = max(valid_is.items(), key=lambda kv: kv[1]["persistence_rate"] or 0)
        print(f"\n  IS 最良 (TR): ADX>{best_tr[0]}, TR={best_tr[1]['trendiness_ratio']:.3f}, "
              f"DPR={best_tr[1]['persistence_rate']:.3f}, N={best_tr[1]['n_triggers']}")
        print(f"  IS 最良 (DPR): ADX>{best_dpr[0]}, DPR={best_dpr[1]['persistence_rate']:.3f}, "
              f"TR={best_dpr[1]['trendiness_ratio']:.3f}, N={best_dpr[1]['n_triggers']}")
        oos_at_best_tr = oos_results[best_tr[0]]
        if oos_at_best_tr["trendiness_ratio"] is not None:
            tr_delta = oos_at_best_tr["trendiness_ratio"] - best_tr[1]["trendiness_ratio"]
            print(f"  → OOS at ADX>{best_tr[0]}: TR={oos_at_best_tr['trendiness_ratio']:.3f} (Δ={tr_delta:+.3f}), "
                  f"DPR={oos_at_best_tr['persistence_rate']:.3f}")

    # IS/OOS の閾値ランキングの Spearman 順位相関
    is_tr_ranks = [is_results[t]["trendiness_ratio"] or 0 for t in ADX_GRID]
    oos_tr_ranks = [oos_results[t]["trendiness_ratio"] or 0 for t in ADX_GRID]
    rho_tr, p_tr = spearmanr(is_tr_ranks, oos_tr_ranks)
    is_dpr_ranks = [is_results[t]["persistence_rate"] or 0 for t in ADX_GRID]
    oos_dpr_ranks = [oos_results[t]["persistence_rate"] or 0 for t in ADX_GRID]
    rho_dpr, p_dpr = spearmanr(is_dpr_ranks, oos_dpr_ranks)
    print(f"\n  IS↔OOS Spearman: TR rho={rho_tr:.3f} (p={p_tr:.3f}), "
          f"DPR rho={rho_dpr:.3f} (p={p_dpr:.3f})")
    print(f"  ※ rho>0.5 で IS の閾値ランキングが OOS で再現していると判定（researcher 推奨）")

    return {
        "pair": pair,
        "n_bars_total": len(df),
        "is_period": [str(is_df.index.min()), str(is_df.index.max())],
        "oos_period": [str(oos_df.index.min()), str(oos_df.index.max())],
        "is_results": is_results,
        "oos_results": oos_results,
        "spearman_tr": float(rho_tr),
        "spearman_dpr": float(rho_dpr),
        "best_is_threshold_tr": best_tr[0] if valid_is else None,
        "best_is_threshold_dpr": best_dpr[0] if valid_is else None,
    }


def main():
    data_dir = ROOT / "data"
    print(f"\n{'='*120}")
    print(f"SPEC v2 - 2-1 ADX trending 閾値の Walk-forward 検証 v2")
    print(f"  ADX_GRID = {ADX_GRID}")
    print(f"  ADX_PERIOD = {ADX_PERIOD}, ATR_PERIOD = {ATR_PERIOD}")
    print(f"  LOOKAHEAD_BARS = {LOOKAHEAD_BARS} ({LOOKAHEAD_BARS // 4}h on M15)")
    print(f"  IS_RATIO = {IS_RATIO}")
    print(f"  評価関数: Trendiness Ratio (TR) + Directional Persistence Rate (DPR)")
    print(f"{'='*120}")

    summary = {}
    for pair, csv_name in PAIRS.items():
        csv_path = data_dir / csv_name
        if not csv_path.exists():
            print(f"⚠ {pair}: {csv_name} 未存在、スキップ")
            continue
        summary[pair] = evaluate_pair(pair, csv_path)

    # 統合: 全ペアの IS 最良閾値の分布
    print(f"\n{'='*120}")
    print(f"統合判定: 全ペアでの IS 最良閾値分布 + 安定性チェック")
    print(f"{'='*120}")
    print(f"{'Pair':<10} {'best_TR':>7} {'best_DPR':>8} {'Spearman_TR':>11} {'Spearman_DPR':>12}")
    print("-" * 60)
    best_tr_thrs = []
    best_dpr_thrs = []
    for pair, r in summary.items():
        print(
            f"{pair:<10} {r['best_is_threshold_tr']:>7} {r['best_is_threshold_dpr']:>8} "
            f"{r['spearman_tr']:>+11.3f} {r['spearman_dpr']:>+12.3f}"
        )
        if r["best_is_threshold_tr"]:
            best_tr_thrs.append(r["best_is_threshold_tr"])
        if r["best_is_threshold_dpr"]:
            best_dpr_thrs.append(r["best_is_threshold_dpr"])

    if best_tr_thrs:
        print(f"\n  全ペア IS 最良閾値 (TR) の中央値: {int(np.median(best_tr_thrs))}, 分布: {sorted(best_tr_thrs)}")
    if best_dpr_thrs:
        print(f"  全ペア IS 最良閾値 (DPR) の中央値: {int(np.median(best_dpr_thrs))}, 分布: {sorted(best_dpr_thrs)}")

    # 同等帯チェック: TR が IS で最良±10% 以内の閾値 = 同等帯
    print(f"\n{'='*120}")
    print(f"同等帯チェック: 各ペアで IS TR が最良値の 90% 以上の閾値帯")
    print(f"{'='*120}")
    for pair, r in summary.items():
        is_results = r["is_results"]
        valid = {k: v for k, v in is_results.items() if v["trendiness_ratio"] is not None}
        if not valid:
            continue
        max_tr = max(v["trendiness_ratio"] for v in valid.values())
        equivalent_band = [k for k, v in valid.items() if v["trendiness_ratio"] >= max_tr * 0.9]
        median_band = int(np.median(equivalent_band)) if equivalent_band else None
        print(f"  {pair}: 同等帯 = {sorted(equivalent_band)}, 中央値 = {median_band}")

    out_json = data_dir / "spec_2_1_adx_summary.json"
    out_json.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
