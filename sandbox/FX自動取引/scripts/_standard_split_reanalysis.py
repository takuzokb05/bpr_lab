"""Proposal 3 (CONFIRM only + ペア別 confidence 閾値) の標準分割再分析

背景:
  Karen 反論屋が J メタ分析の IS-OOS 主張を疑問視。J メタ分析は
  「IS:OOS = 件数で 1:1 に揃える」分割を使用したため、ペア別に
  異なる日付カットオフが発生し Combined PF が虚飾されている疑い。

このスクリプトは Proposal 3 を以下の標準分割で再評価する:
  1. 時間半々分割 (時間軸で前半 50% / 後半 50%, ペア共通カットオフ)
  2. 年単位分割 (2024 IS / 2025 OOS, 2026 を hold-out)
  3. 過去 1 年 OOS (直近 12 ヶ月を OOS, 残りを IS)
  4. 5-10 種の追加分割で OOS PF 分布を見る (選択バイアス検証)

入力データは _cycle2_meta_analysis.py の load_* 関数を再利用。
LLM API は呼ばない (再判定不要)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import numpy as np

BASE = Path(r"c:\Users\takuz\プロジェクト\bpr_lab\sandbox\FX自動取引")
DATA = BASE / "data"
sys.path.insert(0, str(BASE / "scripts"))

from _cycle2_meta_analysis import (
    load_signals_usd_jpy,
    load_signals_gbp_jpy,
    load_decisions_usd_jpy,
    load_decisions_gbp_jpy,
    merge_signal_decision,
    compute_pf,
)

# Proposal 3 構成: ペア別の confidence 閾値
PROPOSAL3 = {
    "USD_JPY": 0.65,
    "GBP_JPY": 0.60,
}


def prepare_pair_df(df: pd.DataFrame, pair: str) -> pd.DataFrame:
    """ペア df を準備し timestamp を datetime に揃える"""
    df = df.copy()
    df["ts"] = pd.to_datetime(df["timestamp_utc"], utc=True).dt.tz_localize(None)
    df = df.sort_values("ts").reset_index(drop=True)
    return df


def filter_confirm(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    return df[
        (df["llm_decision"] == "CONFIRM")
        & df["valid_decision"]
        & (df["llm_confidence"] >= threshold)
    ].copy()


def filter_all_signals(df: pd.DataFrame) -> pd.DataFrame:
    """base 用 (フィルタなし全シグナル)"""
    return df.copy()


def compute_proposal3_pf(
    df_usd: pd.DataFrame,
    df_gbp: pd.DataFrame,
    threshold_usd: float,
    threshold_gbp: float,
) -> tuple[dict, dict, dict]:
    """USD_JPY, GBP_JPY, Combined の Proposal 3 PF を返す"""
    usd_filt = filter_confirm(df_usd, threshold_usd)
    gbp_filt = filter_confirm(df_gbp, threshold_gbp)
    combined = pd.concat([usd_filt, gbp_filt], ignore_index=True)

    usd_stats = compute_pf(usd_filt["net_pnl"])
    gbp_stats = compute_pf(gbp_filt["net_pnl"])
    com_stats = compute_pf(combined["net_pnl"])
    return usd_stats.as_dict(), gbp_stats.as_dict(), com_stats.as_dict()


def compute_base_pf(
    df_usd: pd.DataFrame, df_gbp: pd.DataFrame
) -> tuple[dict, dict, dict]:
    """base = フィルタなし全シグナル"""
    usd_stats = compute_pf(df_usd["net_pnl"])
    gbp_stats = compute_pf(df_gbp["net_pnl"])
    combined = pd.concat([df_usd, df_gbp], ignore_index=True)
    com_stats = compute_pf(combined["net_pnl"])
    return usd_stats.as_dict(), gbp_stats.as_dict(), com_stats.as_dict()


# ============================================================
# 標準分割 1: 時間半々分割 (ペア共通カットオフ日)
# ============================================================
def time_half_split(df_usd: pd.DataFrame, df_gbp: pd.DataFrame) -> dict:
    """両ペアを連結 -> 時間軸で全体期間の中央日付でカット"""
    combined = pd.concat([df_usd, df_gbp], ignore_index=True)
    ts_min = combined["ts"].min()
    ts_max = combined["ts"].max()
    mid_ts = ts_min + (ts_max - ts_min) / 2

    is_usd = df_usd[df_usd["ts"] < mid_ts]
    oos_usd = df_usd[df_usd["ts"] >= mid_ts]
    is_gbp = df_gbp[df_gbp["ts"] < mid_ts]
    oos_gbp = df_gbp[df_gbp["ts"] >= mid_ts]

    # Proposal 3
    is_u, is_g, is_c = compute_proposal3_pf(
        is_usd, is_gbp, PROPOSAL3["USD_JPY"], PROPOSAL3["GBP_JPY"]
    )
    oos_u, oos_g, oos_c = compute_proposal3_pf(
        oos_usd, oos_gbp, PROPOSAL3["USD_JPY"], PROPOSAL3["GBP_JPY"]
    )
    # Base
    bu_is, bg_is, bc_is = compute_base_pf(is_usd, is_gbp)
    bu_oos, bg_oos, bc_oos = compute_base_pf(oos_usd, oos_gbp)

    return {
        "method": "time_half_split (ペア共通カットオフ日)",
        "cutoff": str(mid_ts),
        "is_period": f"{ts_min.date()} to {mid_ts.date()}",
        "oos_period": f"{mid_ts.date()} to {ts_max.date()}",
        "proposal3": {
            "USD_JPY": {"is": is_u, "oos": oos_u, "diff": round(oos_u["pf"] - is_u["pf"], 3)},
            "GBP_JPY": {"is": is_g, "oos": oos_g, "diff": round(oos_g["pf"] - is_g["pf"], 3)},
            "Combined": {"is": is_c, "oos": oos_c, "diff": round(oos_c["pf"] - is_c["pf"], 3)},
        },
        "base": {
            "USD_JPY": {"is": bu_is, "oos": bu_oos, "diff": round(bu_oos["pf"] - bu_is["pf"], 3)},
            "GBP_JPY": {"is": bg_is, "oos": bg_oos, "diff": round(bg_oos["pf"] - bg_is["pf"], 3)},
            "Combined": {"is": bc_is, "oos": bc_oos, "diff": round(bc_oos["pf"] - bc_is["pf"], 3)},
        },
    }


# ============================================================
# 標準分割 2: 年単位分割
# ============================================================
def year_split(df_usd: pd.DataFrame, df_gbp: pd.DataFrame) -> dict:
    """2024 (IS) / 2025 (OOS) / 2026 (Hold-out)"""

    def by_year(df, y_start, y_end):
        return df[(df["ts"] >= pd.Timestamp(y_start)) & (df["ts"] < pd.Timestamp(y_end))]

    is_usd = by_year(df_usd, "2024-01-01", "2025-01-01")
    oos_usd = by_year(df_usd, "2025-01-01", "2026-01-01")
    hold_usd = by_year(df_usd, "2026-01-01", "2027-01-01")

    is_gbp = by_year(df_gbp, "2024-01-01", "2025-01-01")
    oos_gbp = by_year(df_gbp, "2025-01-01", "2026-01-01")
    hold_gbp = by_year(df_gbp, "2026-01-01", "2027-01-01")

    is_u, is_g, is_c = compute_proposal3_pf(
        is_usd, is_gbp, PROPOSAL3["USD_JPY"], PROPOSAL3["GBP_JPY"]
    )
    oos_u, oos_g, oos_c = compute_proposal3_pf(
        oos_usd, oos_gbp, PROPOSAL3["USD_JPY"], PROPOSAL3["GBP_JPY"]
    )
    hold_u, hold_g, hold_c = compute_proposal3_pf(
        hold_usd, hold_gbp, PROPOSAL3["USD_JPY"], PROPOSAL3["GBP_JPY"]
    )
    bu_is, bg_is, bc_is = compute_base_pf(is_usd, is_gbp)
    bu_oos, bg_oos, bc_oos = compute_base_pf(oos_usd, oos_gbp)
    bu_h, bg_h, bc_h = compute_base_pf(hold_usd, hold_gbp)

    return {
        "method": "year_split (2024 IS / 2025 OOS / 2026 Hold-out)",
        "proposal3": {
            "USD_JPY": {
                "is_2024": is_u,
                "oos_2025": oos_u,
                "hold_2026": hold_u,
                "diff_oos_is": round(oos_u["pf"] - is_u["pf"], 3),
                "diff_hold_oos": round(hold_u["pf"] - oos_u["pf"], 3),
            },
            "GBP_JPY": {
                "is_2024": is_g,
                "oos_2025": oos_g,
                "hold_2026": hold_g,
                "diff_oos_is": round(oos_g["pf"] - is_g["pf"], 3),
                "diff_hold_oos": round(hold_g["pf"] - oos_g["pf"], 3),
            },
            "Combined": {
                "is_2024": is_c,
                "oos_2025": oos_c,
                "hold_2026": hold_c,
                "diff_oos_is": round(oos_c["pf"] - is_c["pf"], 3),
                "diff_hold_oos": round(hold_c["pf"] - oos_c["pf"], 3),
            },
        },
        "base": {
            "USD_JPY": {"is_2024": bu_is, "oos_2025": bu_oos, "hold_2026": bu_h},
            "GBP_JPY": {"is_2024": bg_is, "oos_2025": bg_oos, "hold_2026": bg_h},
            "Combined": {"is_2024": bc_is, "oos_2025": bc_oos, "hold_2026": bc_h},
        },
    }


# ============================================================
# 標準分割 3: 直近 12 ヶ月 OOS
# ============================================================
def trailing_12m_split(df_usd: pd.DataFrame, df_gbp: pd.DataFrame) -> dict:
    """全体の最終日から 12 ヶ月遡って OOS"""
    combined = pd.concat([df_usd, df_gbp], ignore_index=True)
    ts_max = combined["ts"].max()
    cutoff = ts_max - pd.Timedelta(days=365)

    is_usd = df_usd[df_usd["ts"] < cutoff]
    oos_usd = df_usd[df_usd["ts"] >= cutoff]
    is_gbp = df_gbp[df_gbp["ts"] < cutoff]
    oos_gbp = df_gbp[df_gbp["ts"] >= cutoff]

    is_u, is_g, is_c = compute_proposal3_pf(
        is_usd, is_gbp, PROPOSAL3["USD_JPY"], PROPOSAL3["GBP_JPY"]
    )
    oos_u, oos_g, oos_c = compute_proposal3_pf(
        oos_usd, oos_gbp, PROPOSAL3["USD_JPY"], PROPOSAL3["GBP_JPY"]
    )
    bu_is, bg_is, bc_is = compute_base_pf(is_usd, is_gbp)
    bu_oos, bg_oos, bc_oos = compute_base_pf(oos_usd, oos_gbp)

    return {
        "method": "trailing_12m_split (直近12ヶ月 = OOS)",
        "cutoff": str(cutoff),
        "proposal3": {
            "USD_JPY": {"is": is_u, "oos": oos_u, "diff": round(oos_u["pf"] - is_u["pf"], 3)},
            "GBP_JPY": {"is": is_g, "oos": oos_g, "diff": round(oos_g["pf"] - is_g["pf"], 3)},
            "Combined": {"is": is_c, "oos": oos_c, "diff": round(oos_c["pf"] - is_c["pf"], 3)},
        },
        "base": {
            "USD_JPY": {"is": bu_is, "oos": bu_oos, "diff": round(bu_oos["pf"] - bu_is["pf"], 3)},
            "GBP_JPY": {"is": bg_is, "oos": bg_oos, "diff": round(bg_oos["pf"] - bg_is["pf"], 3)},
            "Combined": {"is": bc_is, "oos": bc_oos, "diff": round(bc_oos["pf"] - bc_is["pf"], 3)},
        },
    }


# ============================================================
# 選択バイアス検証: 多種の分割で OOS PF 分布
# ============================================================
def split_distribution(df_usd: pd.DataFrame, df_gbp: pd.DataFrame) -> dict:
    """様々な分割方式で Proposal 3 の IS PF / OOS PF を計算
    "OOS PF > IS PF" になる分割が何 % か → 50% 未満なら J メタ分析は選択バイアス確定
    """
    results = []

    combined = pd.concat([df_usd, df_gbp], ignore_index=True)
    ts_min = combined["ts"].min()
    ts_max = combined["ts"].max()

    # ============ 候補分割集合 ============
    splits = []

    # (1) J メタ分析の特別分割 (件数で半々) - 参照用
    confirm_u = filter_confirm(df_usd, PROPOSAL3["USD_JPY"]).sort_values("ts")
    confirm_g = filter_confirm(df_gbp, PROPOSAL3["GBP_JPY"]).sort_values("ts")

    if len(confirm_u) > 0 and len(confirm_g) > 0:
        cutoff_u = confirm_u.iloc[len(confirm_u) // 2]["ts"]
        cutoff_g = confirm_g.iloc[len(confirm_g) // 2]["ts"]
        # J メタ流は USD と GBP で別カットオフ
        splits.append(
            (
                "J_meta_per_pair_count_half",
                ("per_pair_count_half", cutoff_u, cutoff_g),
            )
        )

    # (2) ペア共通日付カットオフ - 月単位で複数試す
    duration = ts_max - ts_min
    # 全期間の 30%, 40%, 50%, 60%, 70% 地点
    for pct in (30, 40, 50, 60, 70):
        cutoff = ts_min + duration * pct / 100.0
        splits.append((f"common_pct_{pct}", ("common", cutoff)))

    # (3) 暦年カットオフ
    for date_str in ("2025-01-01", "2025-04-01", "2025-07-01", "2025-10-01", "2026-01-01"):
        d = pd.Timestamp(date_str)
        if ts_min < d < ts_max:
            splits.append((f"calendar_{date_str}", ("common", d)))

    # (4) 直近 X ヶ月 OOS
    for months in (6, 9, 12, 15, 18):
        cutoff = ts_max - pd.Timedelta(days=months * 30)
        if cutoff > ts_min:
            splits.append((f"trailing_{months}m", ("common", cutoff)))

    # 評価
    for name, spec in splits:
        if spec[0] == "common":
            cutoff = spec[1]
            is_u_df = df_usd[df_usd["ts"] < cutoff]
            oos_u_df = df_usd[df_usd["ts"] >= cutoff]
            is_g_df = df_gbp[df_gbp["ts"] < cutoff]
            oos_g_df = df_gbp[df_gbp["ts"] >= cutoff]
            cutoff_info = str(cutoff.date())
        else:  # per_pair_count_half
            cu, cg = spec[1], spec[2]
            is_u_df = df_usd[df_usd["ts"] < cu]
            oos_u_df = df_usd[df_usd["ts"] >= cu]
            is_g_df = df_gbp[df_gbp["ts"] < cg]
            oos_g_df = df_gbp[df_gbp["ts"] >= cg]
            cutoff_info = f"USD={cu.date()},GBP={cg.date()}"

        # Proposal 3
        is_u, is_g, is_c = compute_proposal3_pf(
            is_u_df, is_g_df, PROPOSAL3["USD_JPY"], PROPOSAL3["GBP_JPY"]
        )
        oos_u, oos_g, oos_c = compute_proposal3_pf(
            oos_u_df, oos_g_df, PROPOSAL3["USD_JPY"], PROPOSAL3["GBP_JPY"]
        )
        # Base
        bu_is, bg_is, bc_is = compute_base_pf(is_u_df, is_g_df)
        bu_oos, bg_oos, bc_oos = compute_base_pf(oos_u_df, oos_g_df)

        results.append(
            {
                "split_name": name,
                "cutoff": cutoff_info,
                "is_pf_combined": is_c["pf"],
                "oos_pf_combined": oos_c["pf"],
                "is_n_combined": is_c["n"],
                "oos_n_combined": oos_c["n"],
                "diff_oos_is_combined": round(oos_c["pf"] - is_c["pf"], 3),
                "oos_improves_is": oos_c["pf"] > is_c["pf"],
                "is_pf_usd": is_u["pf"],
                "oos_pf_usd": oos_u["pf"],
                "is_pf_gbp": is_g["pf"],
                "oos_pf_gbp": oos_g["pf"],
                "base_is_pf_combined": bc_is["pf"],
                "base_oos_pf_combined": bc_oos["pf"],
                "lift_oos_combined": round(oos_c["pf"] - bc_oos["pf"], 3),
            }
        )

    n_total = len(results)
    n_improve = sum(1 for r in results if r["oos_improves_is"])
    pct_improve = round(100.0 * n_improve / n_total, 1) if n_total > 0 else 0.0

    return {
        "n_splits": n_total,
        "n_oos_improves_is": n_improve,
        "pct_oos_improves_is": pct_improve,
        "interpretation": (
            "選択バイアス疑い (J メタ分析 OK 分割は少数派)"
            if pct_improve < 50
            else "OOS 改善が多数派"
        ),
        "splits": results,
    }


# ============================================================
# ゲート判定
# ============================================================
def gate_evaluation(splits: list[dict]) -> dict:
    """3 つの標準分割すべてでゲート PASS/FAIL を判定

    G0-A: Combined OOS PF が base 比 +0.30 改善
    G0-B: Combined OOS PF >= 1.0 (構造的にプラス)
    IS-OOS consistency: OOS PF が IS から 10% 以上劣化していない (>= 0.9 * IS)
    """
    gate_results = []
    for split in splits:
        method = split["method"]
        prop3 = split["proposal3"]
        base = split["base"]

        if "Combined" in prop3:
            combined_p3 = prop3["Combined"]
            combined_base = base["Combined"]
            # year_split は是非 OOS = oos_2025 で判定
            if "oos" in combined_p3:
                oos_p3 = combined_p3["oos"]
                is_p3 = combined_p3["is"]
                oos_base = combined_base["oos"]
            elif "oos_2025" in combined_p3:
                oos_p3 = combined_p3["oos_2025"]
                is_p3 = combined_p3["is_2024"]
                oos_base = combined_base["oos_2025"]
            else:
                continue

            lift = oos_p3["pf"] - oos_base["pf"]
            g0a = lift >= 0.30
            g0b = oos_p3["pf"] >= 1.0
            # 一貫性
            if is_p3["pf"] > 0:
                consistency_pct = (oos_p3["pf"] / is_p3["pf"]) if is_p3["pf"] > 0 else 0
                is_consistent = consistency_pct >= 0.9
            else:
                consistency_pct = float("inf")
                is_consistent = True

            gate_results.append(
                {
                    "method": method,
                    "is_n": is_p3["n"],
                    "oos_n": oos_p3["n"],
                    "is_pf": is_p3["pf"],
                    "oos_pf": oos_p3["pf"],
                    "oos_base_pf": oos_base["pf"],
                    "lift_vs_base": round(lift, 3),
                    "G0_A_lift_ge_030": g0a,
                    "G0_B_oos_pf_ge_1.0": g0b,
                    "consistency_oos_over_is_pct": round(consistency_pct * 100, 1)
                    if isinstance(consistency_pct, float) and consistency_pct != float("inf")
                    else "N/A",
                    "is_consistent_within_10pct_degradation": is_consistent,
                    "all_pass": bool(g0a and g0b and is_consistent),
                }
            )

    n_pass = sum(1 for r in gate_results if r["all_pass"])
    n_total = len(gate_results)
    return {
        "n_splits_evaluated": n_total,
        "n_pass_all_gates": n_pass,
        "pass_rate_pct": round(100.0 * n_pass / n_total, 1) if n_total > 0 else 0.0,
        "verdict": (
            "PASS_ALL"
            if n_pass == n_total
            else ("PARTIAL" if n_pass > 0 else "FAIL_ALL")
        ),
        "details": gate_results,
    }


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 70)
    print("Standard Split Re-analysis: Proposal 3 (CONFIRM only + per-pair conf)")
    print("=" * 70)

    sig_usd = load_signals_usd_jpy()
    sig_gbp = load_signals_gbp_jpy()
    dec_usd = load_decisions_usd_jpy()
    dec_gbp = load_decisions_gbp_jpy()

    print(f"USD_JPY signals: {len(sig_usd)}, decisions: {len(dec_usd)}")
    print(f"GBP_JPY signals: {len(sig_gbp)}, decisions: {len(dec_gbp)}")

    df_usd_raw = merge_signal_decision(sig_usd, dec_usd)
    df_gbp_raw = merge_signal_decision(sig_gbp, dec_gbp)
    df_usd = prepare_pair_df(df_usd_raw, "USD_JPY")
    df_gbp = prepare_pair_df(df_gbp_raw, "GBP_JPY")

    print(f"USD_JPY merged: {len(df_usd)}, valid: {df_usd['valid_decision'].sum()}")
    print(f"GBP_JPY merged: {len(df_gbp)}, valid: {df_gbp['valid_decision'].sum()}")

    # 全期間 (参照用) - Proposal 3
    full_u, full_g, full_c = compute_proposal3_pf(
        df_usd, df_gbp, PROPOSAL3["USD_JPY"], PROPOSAL3["GBP_JPY"]
    )
    bu, bg, bc = compute_base_pf(df_usd, df_gbp)

    print("\n[All-period reference (no split)]")
    print(f"  USD_JPY base PF={bu['pf']} (n={bu['n']})  ->  Proposal3 PF={full_u['pf']} (n={full_u['n']})")
    print(f"  GBP_JPY base PF={bg['pf']} (n={bg['n']})  ->  Proposal3 PF={full_g['pf']} (n={full_g['n']})")
    print(f"  Combined base PF={bc['pf']} (n={bc['n']})  ->  Proposal3 PF={full_c['pf']} (n={full_c['n']})")

    # ============ 3 標準分割 ============
    s1 = time_half_split(df_usd, df_gbp)
    s2 = year_split(df_usd, df_gbp)
    s3 = trailing_12m_split(df_usd, df_gbp)

    # ============ 多種分割で OOS PF 分布 ============
    dist = split_distribution(df_usd, df_gbp)

    # ============ ゲート判定 ============
    gate = gate_evaluation([s1, s2, s3])

    output = {
        "all_period_reference": {
            "proposal3": {"USD_JPY": full_u, "GBP_JPY": full_g, "Combined": full_c},
            "base": {"USD_JPY": bu, "GBP_JPY": bg, "Combined": bc},
        },
        "standard_split_1_time_half": s1,
        "standard_split_2_year": s2,
        "standard_split_3_trailing_12m": s3,
        "selection_bias_check": dist,
        "gate_evaluation": gate,
        "proposal3_thresholds": PROPOSAL3,
    }

    out_path = DATA / "_standard_split_reanalysis.json"
    out_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    print(f"\nSaved: {out_path}")

    # Pretty print
    print("\n" + "=" * 70)
    print("STANDARD SPLIT 1: Time Half Split (Common Cutoff)")
    print("=" * 70)
    print(f"  Cutoff: {s1['cutoff']}")
    for pair in ("USD_JPY", "GBP_JPY", "Combined"):
        p = s1["proposal3"][pair]
        b = s1["base"][pair]
        print(f"\n  [{pair}]")
        print(f"    Proposal3: IS PF={p['is']['pf']} (n={p['is']['n']}) -> OOS PF={p['oos']['pf']} (n={p['oos']['n']}) diff={p['diff']:+.3f}")
        print(f"    Base     : IS PF={b['is']['pf']} (n={b['is']['n']}) -> OOS PF={b['oos']['pf']} (n={b['oos']['n']}) diff={b['diff']:+.3f}")
        print(f"    Lift (Proposal3 OOS - Base OOS): {p['oos']['pf'] - b['oos']['pf']:+.3f}")

    print("\n" + "=" * 70)
    print("STANDARD SPLIT 2: Year Split (2024 IS / 2025 OOS / 2026 Hold-out)")
    print("=" * 70)
    for pair in ("USD_JPY", "GBP_JPY", "Combined"):
        p = s2["proposal3"][pair]
        b = s2["base"][pair]
        print(f"\n  [{pair}]")
        print(f"    Proposal3 2024 IS: PF={p['is_2024']['pf']} (n={p['is_2024']['n']})")
        print(f"    Proposal3 2025 OOS: PF={p['oos_2025']['pf']} (n={p['oos_2025']['n']})")
        print(f"    Proposal3 2026 Hold: PF={p['hold_2026']['pf']} (n={p['hold_2026']['n']})")
        print(f"    diff OOS-IS={p['diff_oos_is']:+.3f}  diff Hold-OOS={p['diff_hold_oos']:+.3f}")
        print(f"    Base 2024 IS: PF={b['is_2024']['pf']} (n={b['is_2024']['n']})")
        print(f"    Base 2025 OOS: PF={b['oos_2025']['pf']} (n={b['oos_2025']['n']})")
        print(f"    Base 2026 Hold: PF={b['hold_2026']['pf']} (n={b['hold_2026']['n']})")
        print(f"    Lift OOS (P3-base): {p['oos_2025']['pf'] - b['oos_2025']['pf']:+.3f}")

    print("\n" + "=" * 70)
    print("STANDARD SPLIT 3: Trailing 12M OOS")
    print("=" * 70)
    print(f"  Cutoff: {s3['cutoff']}")
    for pair in ("USD_JPY", "GBP_JPY", "Combined"):
        p = s3["proposal3"][pair]
        b = s3["base"][pair]
        print(f"\n  [{pair}]")
        print(f"    Proposal3: IS PF={p['is']['pf']} (n={p['is']['n']}) -> OOS PF={p['oos']['pf']} (n={p['oos']['n']}) diff={p['diff']:+.3f}")
        print(f"    Base     : IS PF={b['is']['pf']} (n={b['is']['n']}) -> OOS PF={b['oos']['pf']} (n={b['oos']['n']}) diff={b['diff']:+.3f}")
        print(f"    Lift (Proposal3 OOS - Base OOS): {p['oos']['pf'] - b['oos']['pf']:+.3f}")

    print("\n" + "=" * 70)
    print(f"SELECTION BIAS CHECK ({dist['n_splits']} splits)")
    print("=" * 70)
    print(f"  OOS PF > IS PF: {dist['n_oos_improves_is']}/{dist['n_splits']} ({dist['pct_oos_improves_is']}%)")
    print(f"  Interpretation: {dist['interpretation']}")
    for r in dist["splits"]:
        flag = "★" if r["oos_improves_is"] else " "
        print(
            f"  {flag} {r['split_name']:25s} cutoff={r['cutoff']:25s}  "
            f"IS PF={r['is_pf_combined']:.3f} (n={r['is_n_combined']:4d}) -> "
            f"OOS PF={r['oos_pf_combined']:.3f} (n={r['oos_n_combined']:4d}) "
            f"diff={r['diff_oos_is_combined']:+.3f}  base_oos={r['base_oos_pf_combined']:.3f} "
            f"lift={r['lift_oos_combined']:+.3f}"
        )

    print("\n" + "=" * 70)
    print("GATE EVALUATION (3 standard splits)")
    print("=" * 70)
    print(f"  Verdict: {gate['verdict']}  ({gate['n_pass_all_gates']}/{gate['n_splits_evaluated']} pass)")
    for d in gate["details"]:
        print(f"\n  [{d['method']}]")
        print(f"    OOS PF={d['oos_pf']} vs base OOS PF={d['oos_base_pf']}  lift={d['lift_vs_base']:+.3f}")
        print(f"    G0-A (lift >= +0.30): {'PASS' if d['G0_A_lift_ge_030'] else 'FAIL'}")
        print(f"    G0-B (OOS PF >= 1.0): {'PASS' if d['G0_B_oos_pf_ge_1.0'] else 'FAIL'}")
        print(f"    Consistency (OOS within 90% of IS): {'PASS' if d['is_consistent_within_10pct_degradation'] else 'FAIL'} ({d['consistency_oos_over_is_pct']}%)")
        print(f"    ALL PASS: {d['all_pass']}")


if __name__ == "__main__":
    main()
