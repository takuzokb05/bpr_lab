"""SPEC v2 - 2-1 季節判定: 6指標スクリーニング (Walk-forward)

ADX 単独失敗を受けて、6つの代替指標を同じ TR/DPR/Spearman フレームで一括評価。
「IC > 0 で IS/OOS Spearman > 0.5」の指標を生き残らせる。

候補指標:
- S1: Choppiness Index (CHOP) — pandas-ta の chop()。<38.2 でトレンド判定
- S2: Hurst exponent (rolling R/S) — >0.55 でトレンド持続
- S3: Yang-Zhang realized volatility — 高ボラ判定
- S4: Range / ATR ratio — <1.0 で効率的トレンド
- S5: Variance Ratio Test — VR>1.0 でトレンド
- S6: MFI (Money Flow Index) — @onlybreakouts 流、>50/<50 で方向性

各指標の「トレンドフラグ」on のときの TR/DPR を測定。
IS で評価し OOS で再現するか確認、Spearman 順位相関で過剰最適化検出。
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
log = logging.getLogger("spec_2_1_screening")
log.setLevel(logging.INFO)


# ============================================================
# 設定
# ============================================================
import argparse
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--years", type=int, default=2, help="使用データの年数")
_parser.add_argument("--timeframe", choices=["M15", "H1", "D1"], default="M15")
_args, _ = _parser.parse_known_args()
_YEARS = _args.years
_TF = _args.timeframe

PAIRS = {
    "USD_JPY": f"mt5_USD_JPY_{_TF}_{_YEARS}y.csv",
    "EUR_USD": f"mt5_EUR_USD_{_TF}_{_YEARS}y.csv",
    "GBP_JPY": f"mt5_GBP_JPY_{_TF}_{_YEARS}y.csv",
}

LOOKAHEAD_BARS = {"M15": 24, "H1": 6, "D1": 5}[_TF]   # M15=6h / H1=6h / D1=1週間営業日
IS_RATIO = 0.75


# ============================================================
# 指標計算（自作）
# ============================================================
def calc_choppiness(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """Choppiness Index (pandas-ta)"""
    chop = ta.chop(df["high"], df["low"], df["close"], length=length)
    return chop


def calc_hurst_rolling(close: pd.Series, window: int = 100) -> pd.Series:
    """Hurst exponent via R/S 法 (rolling)"""

    def hurst_rs(arr):
        arr = np.asarray(arr)
        if len(arr) < 20 or np.std(arr) == 0:
            return np.nan
        # R/S 計算
        try:
            mean = np.mean(arr)
            dev = arr - mean
            cumdev = np.cumsum(dev)
            R = np.max(cumdev) - np.min(cumdev)
            S = np.std(arr, ddof=1)
            if S == 0 or R == 0:
                return np.nan
            # 簡易: log(R/S) / log(n)
            return np.log(R / S) / np.log(len(arr))
        except Exception:
            return np.nan

    log_returns = np.log(close).diff().fillna(0)
    return log_returns.rolling(window).apply(hurst_rs, raw=True)


def calc_yang_zhang(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Yang-Zhang realized volatility"""
    o = df["open"]
    h = df["high"]
    l = df["low"]
    c = df["close"]
    c_prev = c.shift(1)
    log_oc_prev = np.log(o / c_prev)
    log_co = np.log(c / o)
    log_ho = np.log(h / o)
    log_lo = np.log(l / o)

    # Rogers-Satchell
    rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
    sigma_rs = rs.rolling(window).mean()

    # Open variance
    sigma_o = log_oc_prev.rolling(window).var()
    # Close variance
    sigma_c = log_co.rolling(window).var()

    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    yz = sigma_o + k * sigma_c + (1 - k) * sigma_rs
    return np.sqrt(yz)


def calc_range_atr_ratio(df: pd.DataFrame, atr_period: int = 14, range_window: int = 14) -> pd.Series:
    """Range / ATR ratio"""
    atr = ta.atr(df["high"], df["low"], df["close"], length=atr_period)
    rng = (df["high"] - df["low"]).rolling(range_window).mean()
    return rng / atr


def calc_variance_ratio(close: pd.Series, q: int = 4, window: int = 100) -> pd.Series:
    """Variance Ratio Test (Lo-MacKinlay 簡易版)"""
    log_returns = np.log(close).diff().fillna(0)

    def vr(arr):
        arr = np.asarray(arr)
        if len(arr) < q + 10:
            return np.nan
        try:
            var_1 = np.var(arr, ddof=1)
            if var_1 == 0:
                return np.nan
            # q 期リターン (オーバーラッピング)
            arr_q = pd.Series(arr).rolling(q).sum().dropna().values
            if len(arr_q) < 2:
                return np.nan
            var_q = np.var(arr_q, ddof=1)
            return var_q / (q * var_1)
        except Exception:
            return np.nan

    return log_returns.rolling(window).apply(vr, raw=True)


def calc_mfi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """Money Flow Index (pandas-ta)"""
    return ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=length)


# ============================================================
# 指標定義（評価用メタデータ）
# ============================================================
INDICATORS = {
    "S1_CHOP": {
        "calc": lambda df: calc_choppiness(df, length=14),
        "grid": [30, 35, 38.2, 42, 50, 60],   # CHOP < threshold でトレンド
        "comparison": "lt",
        "description": "Choppiness Index, lower = trending",
    },
    "S2_Hurst": {
        "calc": lambda df: calc_hurst_rolling(df["close"], window=100),
        "grid": [0.45, 0.50, 0.55, 0.60, 0.65],   # Hurst > threshold でトレンド持続
        "comparison": "gt",
        "description": "Hurst exponent (R/S, rolling 100), higher = trending",
    },
    "S3_YZ_vol": {
        "calc": lambda df: calc_yang_zhang(df, window=20),
        "grid": "percentile",   # 25th, 50th, 75th, 90th percentile を動的に
        "comparison": "gt",
        "description": "Yang-Zhang realized vol, higher = volatile/trending",
    },
    "S4_Range_ATR": {
        "calc": lambda df: calc_range_atr_ratio(df, atr_period=14, range_window=14),
        "grid": [0.7, 0.85, 1.0, 1.15, 1.3],   # ratio < threshold で効率的トレンド
        "comparison": "lt",
        "description": "Range/ATR ratio, lower = efficient trend",
    },
    "S5_VR": {
        "calc": lambda df: calc_variance_ratio(df["close"], q=4, window=100),
        "grid": [0.8, 0.9, 1.0, 1.1, 1.2, 1.3],   # VR > threshold でトレンド
        "comparison": "gt",
        "description": "Variance Ratio (q=4, rolling 100), >1 = trending",
    },
    "S6_MFI": {
        "calc": lambda df: calc_mfi(df, length=14),
        "grid": [50, 55, 60, 65, 70],   # MFI > threshold で上昇圧力強い
        "comparison": "gt",
        "description": "Money Flow Index, >50 = upward pressure",
    },
}


# ============================================================
# 評価関数
# ============================================================
def evaluate_indicator(
    df: pd.DataFrame,
    indicator: pd.Series,
    threshold: float,
    comparison: str,
) -> dict:
    """
    閾値判定で trigger された時刻について future_return の特性を測定。
    """
    df = df.copy()
    df["ind"] = indicator
    df = df.dropna(subset=["ind", "future_return", "past_return"])

    if comparison == "gt":
        high = df[df["ind"] > threshold]
        low = df[df["ind"] <= threshold]
    elif comparison == "lt":
        high = df[df["ind"] < threshold]
        low = df[df["ind"] >= threshold]
    else:
        raise ValueError(f"Unknown comparison: {comparison}")

    n_triggers = len(high)
    if n_triggers < 50:
        return {
            "n_triggers": n_triggers, "trendiness_ratio": None,
            "persistence_rate": None,
        }

    median_high = float(high["future_return"].abs().median())
    median_low = float(low["future_return"].abs().median()) if len(low) > 0 else 1e-9
    tr = median_high / median_low if median_low > 0 else None

    same_sign = (np.sign(high["past_return"]) == np.sign(high["future_return"])).sum()
    pr = float(same_sign / len(high))

    return {
        "n_triggers": n_triggers,
        "trendiness_ratio": tr,
        "persistence_rate": pr,
    }


# ============================================================
# データ準備
# ============================================================
def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["future_return"] = (
        out["close"].shift(-LOOKAHEAD_BARS) - out["close"]
    ) / out["close"]
    out["past_return"] = (
        out["close"] - out["close"].shift(LOOKAHEAD_BARS)
    ) / out["close"].shift(LOOKAHEAD_BARS)
    return out


def split_is_oos(df: pd.DataFrame, ratio: float = IS_RATIO) -> tuple:
    n = len(df)
    split_idx = int(n * ratio)
    return df.iloc[:split_idx], df.iloc[split_idx:]


# ============================================================
# 指標ごとの IS/OOS 評価
# ============================================================
def evaluate_pair_indicator(
    pair: str,
    indicator_name: str,
    df: pd.DataFrame,
) -> dict:
    spec = INDICATORS[indicator_name]
    indicator = spec["calc"](df)

    # percentile グリッドの場合、指標分布から閾値を動的決定
    if spec["grid"] == "percentile":
        valid = indicator.dropna()
        grid = [
            float(np.percentile(valid, p)) for p in [25, 50, 75, 90]
        ]
    else:
        grid = spec["grid"]

    df_with_ret = add_returns(df).dropna()
    is_df, oos_df = split_is_oos(df_with_ret, IS_RATIO)
    indicator_is = indicator.reindex(is_df.index)
    indicator_oos = indicator.reindex(oos_df.index)

    is_results = {}
    oos_results = {}
    for thr in grid:
        is_results[thr] = evaluate_indicator(
            is_df, indicator_is, thr, spec["comparison"]
        )
        oos_results[thr] = evaluate_indicator(
            oos_df, indicator_oos, thr, spec["comparison"]
        )

    # Spearman
    is_tr_ranks = [is_results[t]["trendiness_ratio"] or 0 for t in grid]
    oos_tr_ranks = [oos_results[t]["trendiness_ratio"] or 0 for t in grid]
    rho_tr, p_tr = spearmanr(is_tr_ranks, oos_tr_ranks)
    is_dpr_ranks = [is_results[t]["persistence_rate"] or 0 for t in grid]
    oos_dpr_ranks = [oos_results[t]["persistence_rate"] or 0 for t in grid]
    rho_dpr, p_dpr = spearmanr(is_dpr_ranks, oos_dpr_ranks)

    # IS 最良閾値（TR）
    valid_is = {k: v for k, v in is_results.items() if v["trendiness_ratio"] is not None}
    if valid_is:
        best_thr = max(valid_is.items(), key=lambda kv: kv[1]["trendiness_ratio"])
        best_thr_val = best_thr[0]
        best_tr_is = best_thr[1]["trendiness_ratio"]
        best_dpr_is = best_thr[1]["persistence_rate"]
        best_tr_oos = oos_results[best_thr_val]["trendiness_ratio"]
        best_dpr_oos = oos_results[best_thr_val]["persistence_rate"]
    else:
        best_thr_val = None
        best_tr_is = best_dpr_is = best_tr_oos = best_dpr_oos = None

    return {
        "indicator": indicator_name,
        "pair": pair,
        "grid": grid,
        "is_results": is_results,
        "oos_results": oos_results,
        "spearman_tr": float(rho_tr) if not np.isnan(rho_tr) else None,
        "spearman_dpr": float(rho_dpr) if not np.isnan(rho_dpr) else None,
        "best_is_threshold": best_thr_val,
        "best_tr_is": best_tr_is,
        "best_dpr_is": best_dpr_is,
        "best_tr_oos": best_tr_oos,
        "best_dpr_oos": best_dpr_oos,
    }


# ============================================================
# 生存判定
# ============================================================
def is_survivor(result: dict) -> bool:
    """
    IC > 0 (best_tr_is > 1.05) かつ
    IS/OOS Spearman > 0.5 (TR or DPR どちらか) かつ
    OOS 最良閾値の TR > 1.0
    """
    if result["best_tr_is"] is None:
        return False
    if result["best_tr_is"] < 1.05:
        return False
    if result["best_tr_oos"] is None or result["best_tr_oos"] < 1.0:
        return False
    rho = max(
        result["spearman_tr"] or -1,
        result["spearman_dpr"] or -1,
    )
    if rho < 0.5:
        return False
    return True


# ============================================================
# メイン
# ============================================================
def main():
    data_dir = ROOT / "data"
    print(f"\n{'='*120}")
    print(f"SPEC v2 - 2-1 指標スクリーニング (6指標 × 3ペア)")
    print(f"  LOOKAHEAD_BARS = {LOOKAHEAD_BARS} ({LOOKAHEAD_BARS // 4}h on M15)")
    print(f"  IS_RATIO = {IS_RATIO}")
    print(f"  生存条件: IS_TR > 1.05 AND OOS_TR > 1.0 AND max(Spearman_TR/DPR) > 0.5")
    print(f"{'='*120}")

    all_results = []
    for indicator_name in INDICATORS.keys():
        print(f"\n--- {indicator_name}: {INDICATORS[indicator_name]['description']} ---")
        for pair, csv_name in PAIRS.items():
            csv_path = data_dir / csv_name
            if not csv_path.exists():
                continue
            df = load_csv(csv_path)
            try:
                r = evaluate_pair_indicator(pair, indicator_name, df)
                all_results.append(r)
                survivor = "✓ 生存" if is_survivor(r) else "✗ 脱落"
                ti = f"{r['best_tr_is']:.3f}" if r['best_tr_is'] else "  -"
                to = f"{r['best_tr_oos']:.3f}" if r['best_tr_oos'] else "  -"
                di = f"{r['best_dpr_is']:.3f}" if r['best_dpr_is'] else "  -"
                do = f"{r['best_dpr_oos']:.3f}" if r['best_dpr_oos'] else "  -"
                rt = f"{r['spearman_tr']:+.3f}" if r['spearman_tr'] is not None else "  -"
                rd = f"{r['spearman_dpr']:+.3f}" if r['spearman_dpr'] is not None else "  -"
                bt = f"{r['best_is_threshold']}" if r['best_is_threshold'] is not None else "-"
                print(f"  {pair}: best_thr={bt:>6} | IS_TR={ti} OOS_TR={to} | "
                      f"IS_DPR={di} OOS_DPR={do} | rho_TR={rt} rho_DPR={rd} | {survivor}")
            except Exception as e:
                log.error("eval failed: %s/%s: %s", pair, indicator_name, e)
                print(f"  {pair}: ERROR - {e}")

    # 生存指標サマリ
    print(f"\n{'='*120}")
    print(f"統合判定: 生存指標サマリ")
    print(f"{'='*120}")
    print(f"{'Indicator':<12} {'USD_JPY':>10} {'EUR_USD':>10} {'GBP_JPY':>10} {'生存率':>8}")
    print("-" * 60)
    for indicator_name in INDICATORS.keys():
        per_pair = {r["pair"]: is_survivor(r) for r in all_results
                    if r["indicator"] == indicator_name}
        survivors = sum(1 for v in per_pair.values() if v)
        total = len(per_pair)
        usd = "✓" if per_pair.get("USD_JPY") else "✗"
        eur = "✓" if per_pair.get("EUR_USD") else "✗"
        gbp = "✓" if per_pair.get("GBP_JPY") else "✗"
        rate = f"{survivors}/{total}"
        print(f"{indicator_name:<12} {usd:>10} {eur:>10} {gbp:>10} {rate:>8}")

    # JSON 保存
    out = {
        "config": {
            "indicators": list(INDICATORS.keys()),
            "pairs": list(PAIRS.keys()),
            "lookahead_bars": LOOKAHEAD_BARS,
            "is_ratio": IS_RATIO,
        },
        "results": all_results,
    }
    out_json = data_dir / f"spec_2_1_indicator_screening_{_TF}_{_YEARS}y.json"
    out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
