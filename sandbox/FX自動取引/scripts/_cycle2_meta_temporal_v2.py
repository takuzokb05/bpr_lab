"""confidence 閾値ごとの四半期安定性 + 時系列分割テスト

直近期間 (2025H2 + 2026H1) で PF が維持されているかを確認
本番投入時の期待値検証
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BASE = Path(r"c:\Users\takuz\プロジェクト\bpr_lab\sandbox\FX自動取引")
DATA = BASE / "data"

import sys
sys.path.insert(0, str(BASE / "scripts"))
from _cycle2_meta_analysis import (
    load_signals_usd_jpy,
    load_signals_gbp_jpy,
    load_decisions_usd_jpy,
    load_decisions_gbp_jpy,
    merge_signal_decision,
    compute_pf,
)


def temporal_pf_by_threshold(df: pd.DataFrame, thresholds: list[float], label: str) -> dict:
    """CONFIRM only かつ confidence ≥ t の四半期別 PF"""
    confirm = df[(df["llm_decision"] == "CONFIRM") & df["valid_decision"]].copy()
    confirm["ts"] = pd.to_datetime(confirm["timestamp_utc"], utc=True)
    confirm["quarter"] = confirm["ts"].dt.tz_localize(None).dt.to_period("Q")

    result = {}
    for t in thresholds:
        sub = confirm[confirm["llm_confidence"] >= t]
        q_result = {}
        for q, qsub in sub.groupby("quarter"):
            stats = compute_pf(qsub["net_pnl"])
            q_result[str(q)] = stats.as_dict()
        result[f">={t:.2f}"] = q_result
    return {"label": label, "by_threshold_quarter": result}


def in_sample_out_sample_split(df: pd.DataFrame, thresholds: list[float], label: str) -> dict:
    """IS (前半) / OOS (後半) 分割 PF"""
    confirm = df[(df["llm_decision"] == "CONFIRM") & df["valid_decision"]].copy()
    confirm["ts"] = pd.to_datetime(confirm["timestamp_utc"], utc=True).dt.tz_localize(None)
    confirm = confirm.sort_values("ts").reset_index(drop=True)
    n = len(confirm)
    mid = n // 2

    is_df = confirm.iloc[:mid]
    oos_df = confirm.iloc[mid:]

    is_start = is_df["ts"].min()
    is_end = is_df["ts"].max()
    oos_start = oos_df["ts"].min()
    oos_end = oos_df["ts"].max()

    result = {
        "is_period": f"{is_start.date()} to {is_end.date()}",
        "oos_period": f"{oos_start.date()} to {oos_end.date()}",
        "by_threshold": {},
    }

    for t in thresholds:
        is_sub = is_df[is_df["llm_confidence"] >= t]
        oos_sub = oos_df[oos_df["llm_confidence"] >= t]
        is_stats = compute_pf(is_sub["net_pnl"])
        oos_stats = compute_pf(oos_sub["net_pnl"])
        result["by_threshold"][f">={t:.2f}"] = {
            "is": is_stats.as_dict(),
            "oos": oos_stats.as_dict(),
            "pf_diff_oos_minus_is": round(oos_stats.pf - is_stats.pf, 3),
        }
    return {"label": label, **result}


def main():
    sig_usd = load_signals_usd_jpy()
    sig_gbp = load_signals_gbp_jpy()
    dec_usd = load_decisions_usd_jpy()
    dec_gbp = load_decisions_gbp_jpy()

    df_usd = merge_signal_decision(sig_usd, dec_usd)
    df_gbp = merge_signal_decision(sig_gbp, dec_gbp)
    df_combined = pd.concat([df_usd, df_gbp], ignore_index=True)

    thresholds = [0.50, 0.60, 0.65, 0.70]

    output = {
        "E2_temporal_by_threshold": {
            "USD_JPY": temporal_pf_by_threshold(df_usd, thresholds, "USD_JPY"),
            "GBP_JPY": temporal_pf_by_threshold(df_gbp, thresholds, "GBP_JPY"),
            "Combined": temporal_pf_by_threshold(df_combined, thresholds, "Combined"),
        },
        "I_is_oos_split": {
            "USD_JPY": in_sample_out_sample_split(df_usd, thresholds, "USD_JPY"),
            "GBP_JPY": in_sample_out_sample_split(df_gbp, thresholds, "GBP_JPY"),
            "Combined": in_sample_out_sample_split(df_combined, thresholds, "Combined"),
        },
    }

    out_path = BASE / "data" / "_cycle2_meta_analysis_temporal_v2.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Saved: {out_path}")

    # Pretty print
    print("\n" + "=" * 70)
    print("In-Sample / Out-of-Sample Split")
    print("=" * 70)
    for pair in ("USD_JPY", "GBP_JPY", "Combined"):
        print(f"\n[{pair}]")
        r = output["I_is_oos_split"][pair]
        print(f"  IS: {r['is_period']}")
        print(f"  OOS: {r['oos_period']}")
        for thr, stats in r["by_threshold"].items():
            print(f"  {thr}: IS PF={stats['is']['pf']} (n={stats['is']['n']}) -> OOS PF={stats['oos']['pf']} (n={stats['oos']['n']}) diff={stats['pf_diff_oos_minus_is']:+.3f}")

    print("\n" + "=" * 70)
    print("Temporal PF by Threshold (Combined)")
    print("=" * 70)
    for thr, q_data in output["E2_temporal_by_threshold"]["Combined"]["by_threshold_quarter"].items():
        print(f"\n  {thr}:")
        for q, stats in q_data.items():
            print(f"    {q}: PF={stats['pf']} (n={stats['n']}) cum={stats['cum_pips']:+.1f}")


if __name__ == "__main__":
    main()
