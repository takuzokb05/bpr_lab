"""最終確認: 採用候補の改善案について再現性検証

改善案候補:
  1. Combined × CONFIRM × conf>=0.65
  2. Combined × CONFIRM × conf>=0.70
  3. USD_JPY × CONFIRM × conf>=0.65 + GBP_JPY × CONFIRM × conf>=0.60 (ペア別最適)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BASE = Path(r"c:\Users\takuz\プロジェクト\bpr_lab\sandbox\FX自動取引")

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


def main():
    sig_usd = load_signals_usd_jpy()
    sig_gbp = load_signals_gbp_jpy()
    dec_usd = load_decisions_usd_jpy()
    dec_gbp = load_decisions_gbp_jpy()

    df_usd = merge_signal_decision(sig_usd, dec_usd)
    df_gbp = merge_signal_decision(sig_gbp, dec_gbp)

    print("=" * 70)
    print("Proposal 3: Pair-specific optimal threshold")
    print("=" * 70)
    # USD_JPY: conf>=0.65 (最適 PF 1.565)
    # GBP_JPY: conf>=0.60 (最適 PF 1.294 n=469 で n>=30 を満たす最強)
    usd_sub = df_usd[(df_usd["llm_decision"] == "CONFIRM") & df_usd["valid_decision"] & (df_usd["llm_confidence"] >= 0.65)]
    gbp_sub = df_gbp[(df_gbp["llm_decision"] == "CONFIRM") & df_gbp["valid_decision"] & (df_gbp["llm_confidence"] >= 0.60)]
    combined_sub = pd.concat([usd_sub, gbp_sub], ignore_index=True)
    s = compute_pf(combined_sub["net_pnl"])
    print(f"  USD_JPY ≥0.65: PF={compute_pf(usd_sub['net_pnl']).pf} n={len(usd_sub)}")
    print(f"  GBP_JPY ≥0.60: PF={compute_pf(gbp_sub['net_pnl']).pf} n={len(gbp_sub)}")
    print(f"  Combined: PF={s.pf} n={s.n} cum_pips={s.cum_pips:.1f} win_rate={s.win_rate:.3f}")
    print(f"  Combined diff vs base PF (0.916): {s.pf - 0.916:+.3f}")

    print("\n" + "=" * 70)
    print("Proposal 4: USD_JPY conf>=0.70 + GBP_JPY conf>=0.60")
    print("=" * 70)
    usd_sub2 = df_usd[(df_usd["llm_decision"] == "CONFIRM") & df_usd["valid_decision"] & (df_usd["llm_confidence"] >= 0.70)]
    gbp_sub2 = df_gbp[(df_gbp["llm_decision"] == "CONFIRM") & df_gbp["valid_decision"] & (df_gbp["llm_confidence"] >= 0.60)]
    combined_sub2 = pd.concat([usd_sub2, gbp_sub2], ignore_index=True)
    s2 = compute_pf(combined_sub2["net_pnl"])
    print(f"  USD_JPY ≥0.70: PF={compute_pf(usd_sub2['net_pnl']).pf} n={len(usd_sub2)}")
    print(f"  GBP_JPY ≥0.60: PF={compute_pf(gbp_sub2['net_pnl']).pf} n={len(gbp_sub2)}")
    print(f"  Combined: PF={s2.pf} n={s2.n} cum_pips={s2.cum_pips:.1f}")
    print(f"  Combined diff vs base PF: {s2.pf - 0.916:+.3f}")

    # OOS for pair-specific
    print("\n" + "=" * 70)
    print("Proposal 3 IS/OOS (USD>=0.65, GBP>=0.60)")
    print("=" * 70)
    combined_sub_sorted = combined_sub.copy()
    combined_sub_sorted["ts"] = pd.to_datetime(combined_sub_sorted["timestamp_utc"], utc=True).dt.tz_localize(None)
    combined_sub_sorted = combined_sub_sorted.sort_values("ts").reset_index(drop=True)
    mid = len(combined_sub_sorted) // 2
    is_sub = combined_sub_sorted.iloc[:mid]
    oos_sub = combined_sub_sorted.iloc[mid:]
    is_stats = compute_pf(is_sub["net_pnl"])
    oos_stats = compute_pf(oos_sub["net_pnl"])
    print(f"  IS: PF={is_stats.pf} n={is_stats.n} ({is_sub['ts'].min().date()} - {is_sub['ts'].max().date()})")
    print(f"  OOS: PF={oos_stats.pf} n={oos_stats.n} ({oos_sub['ts'].min().date()} - {oos_sub['ts'].max().date()})")

    # 直近期間 (2025Q3+ = OOS-like)
    print("\n" + "=" * 70)
    print("Recent period 2025Q3+ check")
    print("=" * 70)
    for thr_lbl, df_sub in [("Combined>=0.65", pd.concat([
        df_usd[(df_usd["llm_decision"] == "CONFIRM") & df_usd["valid_decision"] & (df_usd["llm_confidence"] >= 0.65)],
        df_gbp[(df_gbp["llm_decision"] == "CONFIRM") & df_gbp["valid_decision"] & (df_gbp["llm_confidence"] >= 0.65)],
    ])), ("Combined>=0.70", pd.concat([
        df_usd[(df_usd["llm_decision"] == "CONFIRM") & df_usd["valid_decision"] & (df_usd["llm_confidence"] >= 0.70)],
        df_gbp[(df_gbp["llm_decision"] == "CONFIRM") & df_gbp["valid_decision"] & (df_gbp["llm_confidence"] >= 0.70)],
    ])), ("Proposal3", combined_sub)]:
        df_sub2 = df_sub.copy()
        df_sub2["ts"] = pd.to_datetime(df_sub2["timestamp_utc"], utc=True).dt.tz_localize(None)
        recent = df_sub2[df_sub2["ts"] >= "2025-07-01"]
        s = compute_pf(recent["net_pnl"])
        print(f"  {thr_lbl}: PF={s.pf} n={s.n} cum_pips={s.cum_pips:.1f} (since 2025-07-01)")


if __name__ == "__main__":
    main()
