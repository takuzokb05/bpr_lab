"""Karen の数字を完全再現するための追加検証

Karen が示した数字 (Proposal 3 合算 IS=1.367 / OOS=1.329) を、
J メタ分析の「ペア別件数半々」分割で再現できるか確認する。
"""
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

BASE = Path(r"c:\Users\takuz\プロジェクト\bpr_lab\sandbox\FX自動取引")
sys.path.insert(0, str(BASE / "scripts"))

from _cycle2_meta_analysis import (
    load_signals_usd_jpy,
    load_signals_gbp_jpy,
    load_decisions_usd_jpy,
    load_decisions_gbp_jpy,
    merge_signal_decision,
    compute_pf,
)

PROPOSAL3 = {"USD_JPY": 0.65, "GBP_JPY": 0.60}


def filter_confirm(df, threshold):
    return df[
        (df["llm_decision"] == "CONFIRM")
        & df["valid_decision"]
        & (df["llm_confidence"] >= threshold)
    ].copy()


def main():
    sig_usd = load_signals_usd_jpy()
    sig_gbp = load_signals_gbp_jpy()
    dec_usd = load_decisions_usd_jpy()
    dec_gbp = load_decisions_gbp_jpy()

    df_usd = merge_signal_decision(sig_usd, dec_usd)
    df_gbp = merge_signal_decision(sig_gbp, dec_gbp)

    df_usd["ts"] = pd.to_datetime(df_usd["timestamp_utc"], utc=True).dt.tz_localize(None)
    df_gbp["ts"] = pd.to_datetime(df_gbp["timestamp_utc"], utc=True).dt.tz_localize(None)
    df_usd = df_usd.sort_values("ts").reset_index(drop=True)
    df_gbp = df_gbp.sort_values("ts").reset_index(drop=True)

    # ============================================================
    # 検証 A: J メタ分析の Per-pair-count-half 分割で
    # USD_JPY 0.65 と GBP_JPY 0.60 を統合 (Karen の数字を再現)
    # ============================================================
    print("=" * 70)
    print("検証 A: J メタ分析の per-pair-count-half 分割で Proposal 3 統合")
    print("=" * 70)

    # USD_JPY 0.65 CONFIRM を半々
    confirm_u = filter_confirm(df_usd, PROPOSAL3["USD_JPY"])
    confirm_u = confirm_u.sort_values("ts").reset_index(drop=True)
    n_u = len(confirm_u)
    mid_u = n_u // 2
    is_u = confirm_u.iloc[:mid_u]
    oos_u = confirm_u.iloc[mid_u:]
    print(f"\n  USD_JPY 0.65 CONFIRM n={n_u}")
    print(f"    IS  ({mid_u} 件): {is_u['ts'].min().date()} to {is_u['ts'].max().date()}")
    print(f"    OOS ({n_u - mid_u} 件): {oos_u['ts'].min().date()} to {oos_u['ts'].max().date()}")
    us = compute_pf(is_u["net_pnl"])
    uo = compute_pf(oos_u["net_pnl"])
    print(f"    IS PF={us.pf:.3f}  OOS PF={uo.pf:.3f}  diff={uo.pf - us.pf:+.3f}")

    # GBP_JPY 0.60 CONFIRM を半々
    confirm_g = filter_confirm(df_gbp, PROPOSAL3["GBP_JPY"])
    confirm_g = confirm_g.sort_values("ts").reset_index(drop=True)
    n_g = len(confirm_g)
    mid_g = n_g // 2
    is_g = confirm_g.iloc[:mid_g]
    oos_g = confirm_g.iloc[mid_g:]
    print(f"\n  GBP_JPY 0.60 CONFIRM n={n_g}")
    print(f"    IS  ({mid_g} 件): {is_g['ts'].min().date()} to {is_g['ts'].max().date()}")
    print(f"    OOS ({n_g - mid_g} 件): {oos_g['ts'].min().date()} to {oos_g['ts'].max().date()}")
    gs = compute_pf(is_g["net_pnl"])
    go = compute_pf(oos_g["net_pnl"])
    print(f"    IS PF={gs.pf:.3f}  OOS PF={go.pf:.3f}  diff={go.pf - gs.pf:+.3f}")

    # Combined (Proposal 3 合算)
    is_combined = pd.concat([is_u, is_g], ignore_index=True)
    oos_combined = pd.concat([oos_u, oos_g], ignore_index=True)
    cs = compute_pf(is_combined["net_pnl"])
    co = compute_pf(oos_combined["net_pnl"])
    print(f"\n  Proposal 3 合算 n_is={len(is_combined)}, n_oos={len(oos_combined)}")
    print(f"    IS PF={cs.pf:.3f}  OOS PF={co.pf:.3f}  diff={co.pf - cs.pf:+.3f}")
    print(f"    Karen 主張: IS=1.367 / OOS=1.329 / diff=-0.038")
    print(f"    再現確認: {'一致' if abs(cs.pf - 1.367) < 0.01 and abs(co.pf - 1.329) < 0.01 else '不一致'}")

    # ============================================================
    # 検証 B: ペア共通カットオフ日で再計算
    # ============================================================
    print("\n" + "=" * 70)
    print("検証 B: ペア共通カットオフ日 (全データ時間軸で半々) で Proposal 3")
    print("=" * 70)
    all_combined = pd.concat([df_usd, df_gbp], ignore_index=True)
    ts_min = all_combined["ts"].min()
    ts_max = all_combined["ts"].max()
    mid_ts = ts_min + (ts_max - ts_min) / 2
    print(f"\n  共通カットオフ: {mid_ts}")

    is_usd_b = filter_confirm(df_usd[df_usd["ts"] < mid_ts], PROPOSAL3["USD_JPY"])
    oos_usd_b = filter_confirm(df_usd[df_usd["ts"] >= mid_ts], PROPOSAL3["USD_JPY"])
    is_gbp_b = filter_confirm(df_gbp[df_gbp["ts"] < mid_ts], PROPOSAL3["GBP_JPY"])
    oos_gbp_b = filter_confirm(df_gbp[df_gbp["ts"] >= mid_ts], PROPOSAL3["GBP_JPY"])

    print(f"\n  USD_JPY 0.65: IS n={len(is_usd_b)}, OOS n={len(oos_usd_b)}")
    print(f"  GBP_JPY 0.60: IS n={len(is_gbp_b)}, OOS n={len(oos_gbp_b)}")

    is_b = pd.concat([is_usd_b, is_gbp_b], ignore_index=True)
    oos_b = pd.concat([oos_usd_b, oos_gbp_b], ignore_index=True)
    csb = compute_pf(is_b["net_pnl"])
    cob = compute_pf(oos_b["net_pnl"])
    print(f"\n  共通カットオフでの Proposal 3 合算")
    print(f"    IS PF={csb.pf:.3f} (n={csb.n})  OOS PF={cob.pf:.3f} (n={cob.n})  diff={cob.pf - csb.pf:+.3f}")


if __name__ == "__main__":
    main()
