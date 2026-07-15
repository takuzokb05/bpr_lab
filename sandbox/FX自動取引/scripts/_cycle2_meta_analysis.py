"""LLM Direct Filter 改善余地メタ分析スクリプト

USD_JPY 2616件 + GBP_JPY 2443件 = 5059件の判定結果を多角的に分析し、
CONFIRM only 戦略の PF を +0.15 以上改善する切り口を探索する。

分析:
  A. Confidence 別 PF
  B. セッション別 PF
  C. レジーム (USD/JPY 24h vol) 別 PF
  D. ペア別最適 confidence 閾値
  E. 時系列安定性 (四半期別)
  F. CONFIRM reasoning 質分析
  G. REJECT 群誤判定率

すべての PF 計算で net_pnl = actual_pnl_pips_sl_tp_first_touch - spread_assumed_pips
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import numpy as np

BASE = Path(r"c:\Users\takuz\プロジェクト\bpr_lab\sandbox\FX自動取引")
DATA = BASE / "data"


def load_signals_usd_jpy() -> pd.DataFrame:
    """USD_JPY 全シグナル"""
    df = pd.read_csv(DATA / "signal_v2_historical_signals.csv")
    df = df[df["pair"] == "USD_JPY"].copy()
    return df


def load_signals_gbp_jpy() -> pd.DataFrame:
    """GBP_JPY no_volatile版 全シグナル"""
    df = pd.read_csv(DATA / "signal_v2_historical_signals_gbp_jpy_no_volatile.csv")
    return df


def load_decisions_usd_jpy() -> pd.DataFrame:
    """USD_JPY 全 LLM 判定 (リトライ版優先)"""
    parts = []
    # 基本判定 (最初のクレジット切れ前 725件)
    base = pd.read_csv(DATA / "llm_filter_decisions_usd_jpy.csv")
    parts.append(base)
    # context_part1〜3 (リトライ版、context追加版)
    for i in (1, 2, 3):
        p = pd.read_csv(DATA / f"llm_filter_decisions_usd_jpy_context_part{i}.csv")
        parts.append(p)
    df = pd.concat(parts, ignore_index=True)
    # 重複は signal_id で最新の有効判定 (llm_error が空) を優先
    df["_valid"] = df["llm_error"].isna() | (df["llm_error"].astype(str).str.strip() == "")
    df = df.sort_values(["signal_id", "_valid"], ascending=[True, False])
    df = df.drop_duplicates(subset=["signal_id"], keep="first").reset_index(drop=True)
    df = df.drop(columns=["_valid"])
    return df


def load_decisions_gbp_jpy() -> pd.DataFrame:
    """GBP_JPY 全 LLM 判定"""
    parts = []
    base = pd.read_csv(DATA / "llm_filter_decisions_gbp_jpy.csv")
    parts.append(base)
    for i in (1, 2, 3):
        p = pd.read_csv(DATA / f"llm_filter_decisions_gbp_jpy_context_part{i}.csv")
        parts.append(p)
    df = pd.concat(parts, ignore_index=True)
    df["_valid"] = df["llm_error"].isna() | (df["llm_error"].astype(str).str.strip() == "")
    df = df.sort_values(["signal_id", "_valid"], ascending=[True, False])
    df = df.drop_duplicates(subset=["signal_id"], keep="first").reset_index(drop=True)
    df = df.drop(columns=["_valid"])
    return df


def merge_signal_decision(signals: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    """シグナル+判定を merge して net_pnl を計算"""
    df = signals.merge(
        decisions[["signal_id", "llm_decision", "llm_confidence", "llm_reasoning", "llm_error"]],
        on="signal_id",
        how="left",
    )
    df["net_pnl"] = df["actual_pnl_pips_sl_tp_first_touch"] - df["spread_assumed_pips"]
    # 有効判定フラグ
    df["valid_decision"] = df["llm_decision"].notna() & (
        df["llm_error"].isna() | (df["llm_error"].astype(str).str.strip() == "")
    )
    return df


@dataclass
class PFStats:
    n: int
    win_rate: float
    avg_win: float
    avg_loss: float
    pf: float
    cum_pips: float
    sharpe: float

    def as_dict(self) -> dict:
        return {
            "n": self.n,
            "win_rate": round(self.win_rate, 3),
            "avg_win": round(self.avg_win, 2),
            "avg_loss": round(self.avg_loss, 2),
            "pf": round(self.pf, 3),
            "cum_pips": round(self.cum_pips, 1),
            "sharpe": round(self.sharpe, 3),
        }


def compute_pf(net_pnl: pd.Series) -> PFStats:
    """PF と関連統計を計算 (net_pnl pips ベース)"""
    s = net_pnl.dropna()
    n = len(s)
    if n == 0:
        return PFStats(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    wins = s[s > 0]
    losses = s[s <= 0]
    gross_win = wins.sum()
    gross_loss = abs(losses.sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    win_rate = len(wins) / n if n > 0 else 0.0
    avg_win = wins.mean() if len(wins) > 0 else 0.0
    avg_loss = losses.mean() if len(losses) > 0 else 0.0
    sharpe = (s.mean() / s.std()) if s.std() > 0 else 0.0
    return PFStats(n, win_rate, avg_win, avg_loss, pf, s.sum(), sharpe)


# ============================================================
# A. Confidence 別 PF
# ============================================================
def analyze_confidence_bins(df: pd.DataFrame, label: str) -> dict:
    """CONFIRM only 内で confidence ビンごとに PF を集計"""
    confirm = df[(df["llm_decision"] == "CONFIRM") & df["valid_decision"]].copy()
    bins = [0.4, 0.5, 0.6, 0.7, 0.8, 1.01]
    bin_labels = ["[0.4,0.5)", "[0.5,0.6)", "[0.6,0.7)", "[0.7,0.8)", "[0.8,1.0]"]
    confirm["conf_bin"] = pd.cut(confirm["llm_confidence"], bins=bins, labels=bin_labels, right=False)
    result = {}
    for bl in bin_labels:
        sub = confirm[confirm["conf_bin"] == bl]
        stats = compute_pf(sub["net_pnl"])
        result[bl] = stats.as_dict()

    # 累積閾値 (confidence >= X)
    thresholds = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]
    threshold_result = {}
    for t in thresholds:
        sub = confirm[confirm["llm_confidence"] >= t]
        stats = compute_pf(sub["net_pnl"])
        threshold_result[f">={t:.2f}"] = stats.as_dict()

    return {"label": label, "by_bin": result, "by_threshold": threshold_result}


# ============================================================
# B. セッション別 PF (CONFIRM only)
# ============================================================
def analyze_sessions(df: pd.DataFrame, label: str) -> dict:
    confirm = df[(df["llm_decision"] == "CONFIRM") & df["valid_decision"]].copy()
    result = {}

    # 単独セッション
    only_tokyo = (confirm["is_tokyo_session"] == 1) & (confirm["is_london_session"] == 0) & (confirm["is_ny_session"] == 0)
    only_london = (confirm["is_tokyo_session"] == 0) & (confirm["is_london_session"] == 1) & (confirm["is_ny_session"] == 0)
    only_ny = (confirm["is_tokyo_session"] == 0) & (confirm["is_london_session"] == 0) & (confirm["is_ny_session"] == 1)
    london_ny = (confirm["is_london_session"] == 1) & (confirm["is_ny_session"] == 1)
    tokyo_london = (confirm["is_tokyo_session"] == 1) & (confirm["is_london_session"] == 1)
    no_session = (confirm["is_tokyo_session"] == 0) & (confirm["is_london_session"] == 0) & (confirm["is_ny_session"] == 0)
    tokyo_any = confirm["is_tokyo_session"] == 1
    london_any = confirm["is_london_session"] == 1
    ny_any = confirm["is_ny_session"] == 1

    masks = {
        "Tokyo only (excl London/NY)": only_tokyo,
        "London only (excl Tokyo/NY)": only_london,
        "NY only (excl Tokyo/London)": only_ny,
        "London+NY overlap": london_ny,
        "Tokyo+London overlap": tokyo_london,
        "Off-session (none)": no_session,
        "Any Tokyo": tokyo_any,
        "Any London": london_any,
        "Any NY": ny_any,
    }
    for name, mask in masks.items():
        sub = confirm[mask]
        stats = compute_pf(sub["net_pnl"])
        result[name] = stats.as_dict()

    return {"label": label, "by_session": result}


# ============================================================
# C. レジーム別 PF
# ============================================================
def analyze_regime(df: pd.DataFrame, label: str) -> dict:
    confirm = df[(df["llm_decision"] == "CONFIRM") & df["valid_decision"]].copy()
    confirm["usd_jpy_24h_abs"] = confirm["related_usd_jpy_24h_change_pct"].abs()

    masks = {
        "Low vol (<0.5%)": confirm["usd_jpy_24h_abs"] < 0.5,
        "Mid vol (0.5-1.5%)": (confirm["usd_jpy_24h_abs"] >= 0.5) & (confirm["usd_jpy_24h_abs"] < 1.5),
        "High vol (>=1.5%)": confirm["usd_jpy_24h_abs"] >= 1.5,
        "Exclude high vol (<1.5%)": confirm["usd_jpy_24h_abs"] < 1.5,
        "Exclude low vol (>=0.5%)": confirm["usd_jpy_24h_abs"] >= 0.5,
    }
    result = {}
    for name, mask in masks.items():
        sub = confirm[mask]
        stats = compute_pf(sub["net_pnl"])
        result[name] = stats.as_dict()
    return {"label": label, "by_regime": result}


# ============================================================
# D. ペア別最適 confidence 閾値
# ============================================================
def analyze_optimal_confidence(df: pd.DataFrame, label: str) -> dict:
    confirm = df[(df["llm_decision"] == "CONFIRM") & df["valid_decision"]].copy()
    thresholds = np.arange(0.40, 0.95, 0.05)
    rows = []
    for t in thresholds:
        sub = confirm[confirm["llm_confidence"] >= t]
        stats = compute_pf(sub["net_pnl"])
        rows.append({"threshold": round(float(t), 2), **stats.as_dict()})
    return {"label": label, "thresholds": rows}


# ============================================================
# E. 時系列安定性
# ============================================================
def analyze_temporal_stability(df: pd.DataFrame, label: str) -> dict:
    confirm = df[(df["llm_decision"] == "CONFIRM") & df["valid_decision"]].copy()
    confirm["ts"] = pd.to_datetime(confirm["timestamp_utc"])
    confirm["quarter"] = confirm["ts"].dt.to_period("Q")
    result = {}
    for q, sub in confirm.groupby("quarter"):
        stats = compute_pf(sub["net_pnl"])
        result[str(q)] = stats.as_dict()
    return {"label": label, "by_quarter": result}


# ============================================================
# F. CONFIRM 質分析 (reasoning キーワード)
# ============================================================
def analyze_reasoning_quality(df: pd.DataFrame, label: str) -> dict:
    confirm = df[(df["llm_decision"] == "CONFIRM") & df["valid_decision"]].copy()
    confirm["reasoning"] = confirm["llm_reasoning"].fillna("").astype(str)

    patterns = {
        "directional_match": r"(整合|一致|方向)",
        "high_liquidity": r"(ロンドン|NY|重複|流動性)",
        "volatility_regime": r"(介入|ボラ|急騰|急落)",
        "risk_reward_fit": r"(ATR|SL|RR|リスクリワード)",
    }
    result = {}
    for name, pat in patterns.items():
        mask = confirm["reasoning"].str.contains(pat, regex=True)
        sub = confirm[mask]
        stats = compute_pf(sub["net_pnl"])
        result[name] = {"matched": int(mask.sum()), **stats.as_dict()}
    # 全体 (基準)
    result["_all_confirm"] = compute_pf(confirm["net_pnl"]).as_dict()
    return {"label": label, "by_pattern": result}


# ============================================================
# G. REJECT 群誤判定率
# ============================================================
def analyze_reject_quality(df: pd.DataFrame, label: str) -> dict:
    reject = df[(df["llm_decision"] == "REJECT") & df["valid_decision"]].copy()
    n = len(reject)
    if n == 0:
        return {"label": label, "n": 0}
    correct_avoid = reject[reject["net_pnl"] < 0]  # 取らなくて正解
    wrong_skip = reject[reject["net_pnl"] >= 0]  # 取ってれば勝てた

    # REJECT 群を仮に取った場合のPF
    if_taken_stats = compute_pf(reject["net_pnl"])

    result = {
        "label": label,
        "n_reject": n,
        "correct_avoid_n": int(len(correct_avoid)),
        "wrong_skip_n": int(len(wrong_skip)),
        "wrong_skip_rate": round(len(wrong_skip) / n, 3) if n > 0 else 0.0,
        "correct_avoid_loss_avg": round(correct_avoid["net_pnl"].mean(), 2) if len(correct_avoid) > 0 else 0.0,
        "wrong_skip_gain_avg": round(wrong_skip["net_pnl"].mean(), 2) if len(wrong_skip) > 0 else 0.0,
        "if_taken_pf": if_taken_stats.as_dict(),
    }
    return result


# ============================================================
# 追加: 組合せ最適化 (オーバーフィット明示用)
# ============================================================
def analyze_combos(df: pd.DataFrame, label: str) -> dict:
    """confidence 閾値 × セッション の組み合わせ"""
    confirm = df[(df["llm_decision"] == "CONFIRM") & df["valid_decision"]].copy()

    sessions = {
        "all": pd.Series(True, index=confirm.index),
        "London+NY": (confirm["is_london_session"] == 1) & (confirm["is_ny_session"] == 1),
        "Any London or NY": (confirm["is_london_session"] == 1) | (confirm["is_ny_session"] == 1),
        "Exclude Tokyo-only": ~((confirm["is_tokyo_session"] == 1) & (confirm["is_london_session"] == 0) & (confirm["is_ny_session"] == 0)),
        "Any NY": confirm["is_ny_session"] == 1,
    }
    thresholds = [0.50, 0.60, 0.65, 0.70, 0.75]

    rows = []
    for sname, smask in sessions.items():
        for t in thresholds:
            sub = confirm[smask & (confirm["llm_confidence"] >= t)]
            stats = compute_pf(sub["net_pnl"])
            rows.append({
                "session": sname,
                "confidence_threshold": t,
                **stats.as_dict(),
            })
    return {"label": label, "combos": rows}


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 70)
    print("Loading data...")
    print("=" * 70)
    sig_usd = load_signals_usd_jpy()
    sig_gbp = load_signals_gbp_jpy()
    dec_usd = load_decisions_usd_jpy()
    dec_gbp = load_decisions_gbp_jpy()
    print(f"USD_JPY signals: {len(sig_usd)}, decisions: {len(dec_usd)}")
    print(f"GBP_JPY signals: {len(sig_gbp)}, decisions: {len(dec_gbp)}")

    df_usd = merge_signal_decision(sig_usd, dec_usd)
    df_gbp = merge_signal_decision(sig_gbp, dec_gbp)
    df_combined = pd.concat([df_usd, df_gbp], ignore_index=True)

    print(f"USD_JPY merged: {len(df_usd)}, valid decisions: {df_usd['valid_decision'].sum()}")
    print(f"GBP_JPY merged: {len(df_gbp)}, valid decisions: {df_gbp['valid_decision'].sum()}")
    print(f"Combined: {len(df_combined)}, valid: {df_combined['valid_decision'].sum()}")

    # Base PF
    base_usd = compute_pf(df_usd["net_pnl"])
    base_gbp = compute_pf(df_gbp["net_pnl"])
    base_combined = compute_pf(df_combined["net_pnl"])

    # CONFIRM only PF
    confirm_usd = compute_pf(df_usd[(df_usd["llm_decision"] == "CONFIRM") & df_usd["valid_decision"]]["net_pnl"])
    confirm_gbp = compute_pf(df_gbp[(df_gbp["llm_decision"] == "CONFIRM") & df_gbp["valid_decision"]]["net_pnl"])
    confirm_combined = compute_pf(df_combined[(df_combined["llm_decision"] == "CONFIRM") & df_combined["valid_decision"]]["net_pnl"])

    decision_counts = {
        "USD_JPY": df_usd[df_usd["valid_decision"]]["llm_decision"].value_counts().to_dict(),
        "GBP_JPY": df_gbp[df_gbp["valid_decision"]]["llm_decision"].value_counts().to_dict(),
        "Combined": df_combined[df_combined["valid_decision"]]["llm_decision"].value_counts().to_dict(),
    }

    output = {
        "summary": {
            "USD_JPY": {
                "n_total": len(df_usd),
                "n_valid_decisions": int(df_usd["valid_decision"].sum()),
                "base_pf": base_usd.as_dict(),
                "confirm_only_pf": confirm_usd.as_dict(),
                "diff": round(confirm_usd.pf - base_usd.pf, 3),
                "decision_counts": decision_counts["USD_JPY"],
            },
            "GBP_JPY": {
                "n_total": len(df_gbp),
                "n_valid_decisions": int(df_gbp["valid_decision"].sum()),
                "base_pf": base_gbp.as_dict(),
                "confirm_only_pf": confirm_gbp.as_dict(),
                "diff": round(confirm_gbp.pf - base_gbp.pf, 3),
                "decision_counts": decision_counts["GBP_JPY"],
            },
            "Combined": {
                "n_total": len(df_combined),
                "n_valid_decisions": int(df_combined["valid_decision"].sum()),
                "base_pf": base_combined.as_dict(),
                "confirm_only_pf": confirm_combined.as_dict(),
                "diff": round(confirm_combined.pf - base_combined.pf, 3),
                "decision_counts": decision_counts["Combined"],
            },
        },
        "A_confidence_bins": {
            "USD_JPY": analyze_confidence_bins(df_usd, "USD_JPY"),
            "GBP_JPY": analyze_confidence_bins(df_gbp, "GBP_JPY"),
            "Combined": analyze_confidence_bins(df_combined, "Combined"),
        },
        "B_sessions": {
            "USD_JPY": analyze_sessions(df_usd, "USD_JPY"),
            "GBP_JPY": analyze_sessions(df_gbp, "GBP_JPY"),
            "Combined": analyze_sessions(df_combined, "Combined"),
        },
        "C_regime": {
            "USD_JPY": analyze_regime(df_usd, "USD_JPY"),
            "GBP_JPY": analyze_regime(df_gbp, "GBP_JPY"),
            "Combined": analyze_regime(df_combined, "Combined"),
        },
        "D_optimal_confidence": {
            "USD_JPY": analyze_optimal_confidence(df_usd, "USD_JPY"),
            "GBP_JPY": analyze_optimal_confidence(df_gbp, "GBP_JPY"),
            "Combined": analyze_optimal_confidence(df_combined, "Combined"),
        },
        "E_temporal": {
            "USD_JPY": analyze_temporal_stability(df_usd, "USD_JPY"),
            "GBP_JPY": analyze_temporal_stability(df_gbp, "GBP_JPY"),
            "Combined": analyze_temporal_stability(df_combined, "Combined"),
        },
        "F_reasoning_quality": {
            "USD_JPY": analyze_reasoning_quality(df_usd, "USD_JPY"),
            "GBP_JPY": analyze_reasoning_quality(df_gbp, "GBP_JPY"),
            "Combined": analyze_reasoning_quality(df_combined, "Combined"),
        },
        "G_reject_quality": {
            "USD_JPY": analyze_reject_quality(df_usd, "USD_JPY"),
            "GBP_JPY": analyze_reject_quality(df_gbp, "GBP_JPY"),
            "Combined": analyze_reject_quality(df_combined, "Combined"),
        },
        "H_combos": {
            "USD_JPY": analyze_combos(df_usd, "USD_JPY"),
            "GBP_JPY": analyze_combos(df_gbp, "GBP_JPY"),
            "Combined": analyze_combos(df_combined, "Combined"),
        },
    }

    out_path = BASE / "data" / "_cycle2_meta_analysis_result.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nResult saved to: {out_path}")

    # Pretty print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for pair, s in output["summary"].items():
        print(f"\n[{pair}]")
        print(f"  total: {s['n_total']}, valid: {s['n_valid_decisions']}")
        print(f"  base PF: {s['base_pf']['pf']} (n={s['base_pf']['n']})")
        print(f"  CONFIRM PF: {s['confirm_only_pf']['pf']} (n={s['confirm_only_pf']['n']})")
        print(f"  diff: {s['diff']:+.3f}")
        print(f"  decisions: {s['decision_counts']}")


if __name__ == "__main__":
    main()
