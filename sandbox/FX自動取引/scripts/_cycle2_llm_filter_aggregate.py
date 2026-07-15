"""
第2サイクル LLM Direct Filter — 3ペア統合集計レポート生成

入力:
    - data/llm_filter_decisions_gbp_jpy.csv
    - data/llm_filter_decisions_usd_jpy.csv
    - data/llm_filter_decisions_eur_usd.csv
    - data/signal_v2_historical_signals.csv

出力:
    docs/proposals/cycle2/LLM_FILTER_EXPANSION_REPORT.md

集計:
    - 各ペアの判定分布、各カテゴリPF、ゲート判定
    - 3ペア合算PF
    - CONFIRM only / CONFIRM+CONTRADICT (as-is) / NEUTRAL only / REJECT 等
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

SIGNALS_CSV = _PROJECT_ROOT / "data" / "signal_v2_historical_signals.csv"
DECISIONS = {
    "GBP_JPY": _PROJECT_ROOT / "data" / "llm_filter_decisions_gbp_jpy.csv",
    "USD_JPY": _PROJECT_ROOT / "data" / "llm_filter_decisions_usd_jpy.csv",
    "EUR_USD": _PROJECT_ROOT / "data" / "llm_filter_decisions_eur_usd.csv",
}
REPORT_MD = _PROJECT_ROOT / "docs" / "proposals" / "cycle2" / "LLM_FILTER_EXPANSION_REPORT.md"


def compute_pf(pnls: pd.Series) -> dict:
    """pips単位の PnL Series から PF / 勝率 等を返す。"""
    n = len(pnls)
    if n == 0:
        return {"n": 0, "win_rate": float("nan"), "avg_win": float("nan"),
                "avg_loss": float("nan"), "PF": float("nan"), "cum_pips": 0.0}
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    win_sum = wins.sum()
    loss_sum = -losses.sum()
    pf = (win_sum / loss_sum) if loss_sum > 0 else float("inf")
    return {
        "n": n,
        "win_rate": (pnls > 0).mean(),
        "avg_win": wins.mean() if len(wins) else float("nan"),
        "avg_loss": losses.mean() if len(losses) else float("nan"),
        "PF": pf,
        "cum_pips": pnls.sum(),
    }


def pf_str(d: dict) -> str:
    if d["n"] == 0:
        return "n=0"
    pf = d["PF"]
    return "inf" if pf == float("inf") else f"{pf:.3f}"


def aggregate_per_pair(pair: str, signals_all: pd.DataFrame) -> Optional[dict]:
    """1ペア分の集計を返す。判定 CSV がなければ None。"""
    dec_path = DECISIONS[pair]
    if not dec_path.exists():
        return None
    decisions = pd.read_csv(dec_path)
    signals = signals_all[signals_all["pair"] == pair].copy()
    merged = signals.merge(
        decisions[["signal_id", "llm_decision", "llm_error"]], on="signal_id", how="inner"
    )
    merged["net_pnl_pips"] = (
        merged["actual_pnl_pips_sl_tp_first_touch"] - merged["spread_assumed_pips"]
    )

    base = compute_pf(merged["net_pnl_pips"])

    confirm = merged[merged["llm_decision"] == "CONFIRM"]
    neutral = merged[merged["llm_decision"] == "NEUTRAL"]
    contradict = merged[merged["llm_decision"] == "CONTRADICT"]
    reject = merged[merged["llm_decision"] == "REJECT"]
    confirm_neutral = merged[merged["llm_decision"].isin(["CONFIRM", "NEUTRAL"])]

    # CONFIRM only + CONTRADICT そのまま (= signal_v2方向の取引を維持し、CONFIRM 群に追加)
    confirm_plus_contradict_asis = merged[merged["llm_decision"].isin(["CONFIRM", "CONTRADICT"])]

    distribution = merged["llm_decision"].value_counts().to_dict()
    total = sum(distribution.values())

    api_errors = (
        decisions["llm_error"].fillna("").astype(str).str.strip().str.len().gt(0).sum()
        if "llm_error" in decisions.columns else 0
    )
    cost_usd = (
        decisions["api_cost_usd"].sum() if "api_cost_usd" in decisions.columns else 0.0
    )

    return {
        "pair": pair,
        "n_signals": len(signals),
        "n_decisions": len(decisions),
        "merged": merged,
        "base": base,
        "confirm_only": compute_pf(confirm["net_pnl_pips"]),
        "neutral_only": compute_pf(neutral["net_pnl_pips"]),
        "confirm_neutral": compute_pf(confirm_neutral["net_pnl_pips"]),
        "contradict_asis": compute_pf(contradict["net_pnl_pips"]),
        "contradict_inverted": compute_pf(-contradict["net_pnl_pips"]),
        "reject_asis": compute_pf(reject["net_pnl_pips"]),
        "confirm_plus_contradict_asis": compute_pf(confirm_plus_contradict_asis["net_pnl_pips"]),
        "distribution": distribution,
        "total": total,
        "api_errors": int(api_errors),
        "cost_usd": float(cost_usd),
    }


def aggregate_combined(per_pair_results: list[dict]) -> dict:
    """3ペアの merged を縦結合して合算 PF を計算する。"""
    if not per_pair_results:
        return {}
    merged_all = pd.concat([r["merged"] for r in per_pair_results], ignore_index=True)

    confirm = merged_all[merged_all["llm_decision"] == "CONFIRM"]
    neutral = merged_all[merged_all["llm_decision"] == "NEUTRAL"]
    contradict = merged_all[merged_all["llm_decision"] == "CONTRADICT"]
    reject = merged_all[merged_all["llm_decision"] == "REJECT"]
    confirm_neutral = merged_all[merged_all["llm_decision"].isin(["CONFIRM", "NEUTRAL"])]
    confirm_plus_contradict_asis = merged_all[
        merged_all["llm_decision"].isin(["CONFIRM", "CONTRADICT"])
    ]

    return {
        "n_signals": len(merged_all),
        "distribution": merged_all["llm_decision"].value_counts().to_dict(),
        "base": compute_pf(merged_all["net_pnl_pips"]),
        "confirm_only": compute_pf(confirm["net_pnl_pips"]),
        "neutral_only": compute_pf(neutral["net_pnl_pips"]),
        "confirm_neutral": compute_pf(confirm_neutral["net_pnl_pips"]),
        "contradict_asis": compute_pf(contradict["net_pnl_pips"]),
        "contradict_inverted": compute_pf(-contradict["net_pnl_pips"]),
        "reject_asis": compute_pf(reject["net_pnl_pips"]),
        "confirm_plus_contradict_asis": compute_pf(confirm_plus_contradict_asis["net_pnl_pips"]),
    }


def gate_judge(base_pf: float, candidate_pf: float, n: int, gate_diff: float = 0.30) -> tuple[bool, str]:
    """ゲート判定 (+0.30 / n>=30) を行う。"""
    if n < 30:
        return False, f"FAIL (n={n}<30)"
    if base_pf == float("inf") or candidate_pf == float("inf"):
        return False, "FAIL (infinite PF)"
    diff = candidate_pf - base_pf
    ok = diff >= gate_diff
    return ok, ("PASS" if ok else "FAIL") + f" (diff={diff:+.3f})"


def fmt_pct(d: dict, key: str) -> str:
    n = sum(d.values())
    return f"{d.get(key, 0)} ({100.0 * d.get(key, 0) / n:.1f}%)" if n else "-"


def _row(label: str, d: dict) -> str:
    if d["n"] == 0:
        return f"| {label} | 0 | - | - | - | - | 0.0 |"
    pf = d["PF"]
    pf_s = "inf" if pf == float("inf") else f"{pf:.3f}"
    aw = f"{d['avg_win']:.2f}" if d["avg_win"] == d["avg_win"] else "-"
    al = f"{d['avg_loss']:.2f}" if d["avg_loss"] == d["avg_loss"] else "-"
    return f"| {label} | {d['n']} | {d['win_rate']:.1%} | {aw} | {al} | {pf_s} | {d['cum_pips']:.1f} |"


def build_report(per_pair: list[dict], combined: dict) -> str:
    lines: list[str] = []
    pairs = [r["pair"] for r in per_pair]
    total_cost = sum(r["cost_usd"] for r in per_pair)
    total_errors = sum(r["api_errors"] for r in per_pair)

    # TL;DR
    # 「最良戦略」を per_pair の各カテゴリ PF から決める (n>=30 の中で最大 PF)
    best = {"label": "-", "pair": "-", "pf": float("-inf"), "n": 0}
    candidates = [
        ("CONFIRM only", "confirm_only"),
        ("CONFIRM+NEUTRAL", "confirm_neutral"),
        ("CONTRADICT そのまま", "contradict_asis"),
        ("CONFIRM+CONTRADICT そのまま", "confirm_plus_contradict_asis"),
        ("REJECT (取らなかった群)", "reject_asis"),
    ]
    # 合算ベース
    base_combined_pf = combined["base"]["PF"]
    for label, key in candidates:
        d = combined[key]
        if d["n"] >= 30 and d["PF"] != float("inf") and d["PF"] > best["pf"]:
            best = {"label": label, "pair": "3ペア合算", "pf": d["PF"], "n": d["n"]}
    # 各ペアでも
    for r in per_pair:
        for label, key in candidates:
            d = r[key]
            if d["n"] >= 30 and d["PF"] != float("inf") and d["PF"] > best["pf"]:
                best = {"label": label, "pair": r["pair"], "pf": d["PF"], "n": d["n"]}

    gate_results = []
    for r in per_pair:
        base_pf = r["base"]["PF"]
        confirm_only_pf = r["confirm_only"]["PF"] if r["confirm_only"]["n"] >= 30 else None
        confirm_neutral_pf = r["confirm_neutral"]["PF"] if r["confirm_neutral"]["n"] >= 30 else None
        confirm_plus_pf = (
            r["confirm_plus_contradict_asis"]["PF"]
            if r["confirm_plus_contradict_asis"]["n"] >= 30 else None
        )
        gate_results.append({
            "pair": r["pair"],
            "base_pf": base_pf,
            "confirm_only_pf": confirm_only_pf,
            "confirm_neutral_pf": confirm_neutral_pf,
            "confirm_plus_pf": confirm_plus_pf,
            "confirm_only_pass": gate_judge(base_pf, confirm_only_pf, r["confirm_only"]["n"])[0]
                if confirm_only_pf is not None else False,
            "confirm_neutral_pass": gate_judge(base_pf, confirm_neutral_pf, r["confirm_neutral"]["n"])[0]
                if confirm_neutral_pf is not None else False,
            "confirm_plus_pass": gate_judge(base_pf, confirm_plus_pf, r["confirm_plus_contradict_asis"]["n"])[0]
                if confirm_plus_pf is not None else False,
        })

    lines += [
        "# LLM Filter 拡張検証 — 3ペア統合",
        "",
        "**実行日**: 2026-05-26",
        f"**対象**: signal_v2_historical_signals.csv の 3ペア (GBP_JPY / USD_JPY / EUR_USD)",
        f"**モデル**: claude-sonnet-4-6 (temperature=0.0, max_tokens=200)",
        f"**実コスト**: ${total_cost:.4f} USD (≒ ¥{total_cost * 150:.0f})",
        f"**API 失敗件数**: {total_errors} (リトライ後)",
        "",
        "---",
        "",
        "## TL;DR",
        "",
        f"- 3ペア合計 n={combined['n_signals']} (GBP_JPY={per_pair[0]['n_signals'] if per_pair else '-'} / "
        f"USD_JPY={next((r['n_signals'] for r in per_pair if r['pair']=='USD_JPY'), '-')} / "
        f"EUR_USD={next((r['n_signals'] for r in per_pair if r['pair']=='EUR_USD'), '-')})",
        f"- ベース PF (3ペア合算 signal_v2 単独): {pf_str(combined['base'])} (n={combined['base']['n']})",
        f"- 最良戦略: **{best['label']}** ({best['pair']}), PF={best['pf']:.3f}, n={best['n']}",
        "- ゲート (+0.30) 達成状況:",
    ]
    for gr in gate_results:
        co_str = f"CONFIRM only diff={gr['confirm_only_pf'] - gr['base_pf']:+.3f}" if gr['confirm_only_pf'] is not None else "CONFIRM only n<30"
        cn_str = f"CONFIRM+NEUTRAL diff={gr['confirm_neutral_pf'] - gr['base_pf']:+.3f}" if gr['confirm_neutral_pf'] is not None else "n<30"
        co_pass = "PASS" if gr['confirm_only_pass'] else "FAIL"
        cn_pass = "PASS" if gr['confirm_neutral_pass'] else "FAIL"
        lines.append(
            f"  - **{gr['pair']}**: CONFIRM only={co_pass} ({co_str}), CONFIRM+NEUTRAL={cn_pass} ({cn_str})"
        )

    # ペア別 判定分布
    lines += [
        "",
        "---",
        "",
        "## ペア別 判定分布",
        "",
        "| ペア | n | CONFIRM | NEUTRAL | CONTRADICT | REJECT | API失敗 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in per_pair:
        d = r["distribution"]
        n = r["total"]
        c = d.get("CONFIRM", 0); ne = d.get("NEUTRAL", 0); co = d.get("CONTRADICT", 0); rj = d.get("REJECT", 0)
        lines.append(
            f"| {r['pair']} | {n} | "
            f"{c} ({100*c/n:.1f}%) | "
            f"{ne} ({100*ne/n:.1f}%) | "
            f"{co} ({100*co/n:.1f}%) | "
            f"{rj} ({100*rj/n:.1f}%) | "
            f"{r['api_errors']} |"
        )
    # 合算行
    if combined:
        d = combined["distribution"]
        n = combined["n_signals"]
        c = d.get("CONFIRM", 0); ne = d.get("NEUTRAL", 0); co = d.get("CONTRADICT", 0); rj = d.get("REJECT", 0)
        lines.append(
            f"| **合算** | **{n}** | "
            f"**{c} ({100*c/n:.1f}%)** | "
            f"**{ne} ({100*ne/n:.1f}%)** | "
            f"**{co} ({100*co/n:.1f}%)** | "
            f"**{rj} ({100*rj/n:.1f}%)** | "
            f"**{total_errors}** |"
        )

    # ペア別 PF
    lines += [
        "",
        "---",
        "",
        "## ペア別 PF 比較",
        "",
        "PnL = `actual_pnl_pips_sl_tp_first_touch - spread_assumed_pips`",
        "",
        "| ペア | base | CONFIRM only | CONFIRM+NEUTRAL | CONTRADICT そのまま | CONFIRM+CONTRADICT そのまま* | NEUTRAL only | REJECT (取らなかった群) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in per_pair:
        lines.append(
            f"| {r['pair']} | "
            f"{pf_str(r['base'])} (n={r['base']['n']}) | "
            f"{pf_str(r['confirm_only'])} (n={r['confirm_only']['n']}) | "
            f"{pf_str(r['confirm_neutral'])} (n={r['confirm_neutral']['n']}) | "
            f"{pf_str(r['contradict_asis'])} (n={r['contradict_asis']['n']}) | "
            f"{pf_str(r['confirm_plus_contradict_asis'])} (n={r['confirm_plus_contradict_asis']['n']}) | "
            f"{pf_str(r['neutral_only'])} (n={r['neutral_only']['n']}) | "
            f"{pf_str(r['reject_asis'])} (n={r['reject_asis']['n']}) |"
        )
    if combined:
        lines.append(
            f"| **合算** | "
            f"**{pf_str(combined['base'])} (n={combined['base']['n']})** | "
            f"**{pf_str(combined['confirm_only'])} (n={combined['confirm_only']['n']})** | "
            f"**{pf_str(combined['confirm_neutral'])} (n={combined['confirm_neutral']['n']})** | "
            f"**{pf_str(combined['contradict_asis'])} (n={combined['contradict_asis']['n']})** | "
            f"**{pf_str(combined['confirm_plus_contradict_asis'])} (n={combined['confirm_plus_contradict_asis']['n']})** | "
            f"**{pf_str(combined['neutral_only'])} (n={combined['neutral_only']['n']})** | "
            f"**{pf_str(combined['reject_asis'])} (n={combined['reject_asis']['n']})** |"
        )
    lines += [
        "",
        "*CONFIRM+CONTRADICT そのまま = CONFIRM 群に「signal_v2 が指示した方向のまま CONTRADICT も取る」運用を加えた合算",
        "",
        "---",
        "",
        "## ペア別 詳細パフォーマンス (各カテゴリ)",
        "",
    ]
    for r in per_pair:
        lines += [
            f"### {r['pair']} (n={r['n_signals']})",
            "",
            "| カテゴリ | 件数 | 勝率 | 平均勝ち pips | 平均負け pips | PF | 累計 pips |",
            "|---|---|---|---|---|---|---|",
            _row("base (全件)", r["base"]),
            _row("CONFIRM only", r["confirm_only"]),
            _row("NEUTRAL only", r["neutral_only"]),
            _row("CONFIRM+NEUTRAL", r["confirm_neutral"]),
            _row("CONTRADICT そのまま", r["contradict_asis"]),
            _row("CONTRADICT 反転 (-1×)", r["contradict_inverted"]),
            _row("CONFIRM+CONTRADICT そのまま", r["confirm_plus_contradict_asis"]),
            _row("REJECT (取らなかった群)", r["reject_asis"]),
            "",
        ]

    # 合算詳細
    if combined:
        lines += [
            "### 3ペア合算",
            "",
            "| カテゴリ | 件数 | 勝率 | 平均勝ち pips | 平均負け pips | PF | 累計 pips |",
            "|---|---|---|---|---|---|---|",
            _row("base (全件)", combined["base"]),
            _row("CONFIRM only", combined["confirm_only"]),
            _row("NEUTRAL only", combined["neutral_only"]),
            _row("CONFIRM+NEUTRAL", combined["confirm_neutral"]),
            _row("CONTRADICT そのまま", combined["contradict_asis"]),
            _row("CONTRADICT 反転 (-1×)", combined["contradict_inverted"]),
            _row("CONFIRM+CONTRADICT そのまま", combined["confirm_plus_contradict_asis"]),
            _row("REJECT (取らなかった群)", combined["reject_asis"]),
            "",
        ]

    # ゲート判定
    lines += [
        "---",
        "",
        "## ゲート判定 (CYCLE2_PLAN.md +0.30 改善)",
        "",
        "ベース PF からの改善量 ≥ +0.30 かつ n ≥ 30 を達成すると PASS。",
        "",
        "| ペア | base PF | CONFIRM only PF (n) | diff | 判定 | CONFIRM+NEUTRAL PF (n) | diff | 判定 | CONFIRM+CONTRADICT そのまま PF (n) | diff | 判定 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in per_pair:
        base_pf = r["base"]["PF"]
        co_d = r["confirm_only"]
        cn_d = r["confirm_neutral"]
        cp_d = r["confirm_plus_contradict_asis"]
        co_pf = co_d["PF"]
        cn_pf = cn_d["PF"]
        cp_pf = cp_d["PF"]
        co_diff = co_pf - base_pf if co_d["n"] >= 30 and co_pf != float("inf") else None
        cn_diff = cn_pf - base_pf if cn_d["n"] >= 30 and cn_pf != float("inf") else None
        cp_diff = cp_pf - base_pf if cp_d["n"] >= 30 and cp_pf != float("inf") else None
        co_judge = ("PASS" if (co_diff is not None and co_diff >= 0.30) else "FAIL") if co_d["n"] >= 30 else "n<30"
        cn_judge = ("PASS" if (cn_diff is not None and cn_diff >= 0.30) else "FAIL") if cn_d["n"] >= 30 else "n<30"
        cp_judge = ("PASS" if (cp_diff is not None and cp_diff >= 0.30) else "FAIL") if cp_d["n"] >= 30 else "n<30"
        lines.append(
            f"| {r['pair']} | {base_pf:.3f} | "
            f"{pf_str(co_d)} (n={co_d['n']}) | "
            f"{(f'{co_diff:+.3f}' if co_diff is not None else '-')} | {co_judge} | "
            f"{pf_str(cn_d)} (n={cn_d['n']}) | "
            f"{(f'{cn_diff:+.3f}' if cn_diff is not None else '-')} | {cn_judge} | "
            f"{pf_str(cp_d)} (n={cp_d['n']}) | "
            f"{(f'{cp_diff:+.3f}' if cp_diff is not None else '-')} | {cp_judge} |"
        )
    if combined:
        base_pf = combined["base"]["PF"]
        co_d = combined["confirm_only"]; cn_d = combined["confirm_neutral"]; cp_d = combined["confirm_plus_contradict_asis"]
        co_diff = co_d["PF"] - base_pf if co_d["n"] >= 30 and co_d["PF"] != float("inf") else None
        cn_diff = cn_d["PF"] - base_pf if cn_d["n"] >= 30 and cn_d["PF"] != float("inf") else None
        cp_diff = cp_d["PF"] - base_pf if cp_d["n"] >= 30 and cp_d["PF"] != float("inf") else None
        co_judge = ("PASS" if (co_diff is not None and co_diff >= 0.30) else "FAIL") if co_d["n"] >= 30 else "n<30"
        cn_judge = ("PASS" if (cn_diff is not None and cn_diff >= 0.30) else "FAIL") if cn_d["n"] >= 30 else "n<30"
        cp_judge = ("PASS" if (cp_diff is not None and cp_diff >= 0.30) else "FAIL") if cp_d["n"] >= 30 else "n<30"
        lines.append(
            f"| **合算** | **{base_pf:.3f}** | "
            f"**{pf_str(co_d)} (n={co_d['n']})** | "
            f"**{(f'{co_diff:+.3f}' if co_diff is not None else '-')}** | **{co_judge}** | "
            f"**{pf_str(cn_d)} (n={cn_d['n']})** | "
            f"**{(f'{cn_diff:+.3f}' if cn_diff is not None else '-')}** | **{cn_judge}** | "
            f"**{pf_str(cp_d)} (n={cp_d['n']})** | "
            f"**{(f'{cp_diff:+.3f}' if cp_diff is not None else '-')}** | **{cp_judge}** |"
        )

    # コスト
    lines += [
        "",
        "---",
        "",
        "## コスト",
        "",
        "| ペア | n | 実コスト (USD) | 1件あたり (USD) | 円換算 (×150) |",
        "|---|---|---|---|---|",
    ]
    for r in per_pair:
        per_signal = r["cost_usd"] / r["n_decisions"] if r["n_decisions"] else 0
        lines.append(
            f"| {r['pair']} | {r['n_decisions']} | ${r['cost_usd']:.4f} | ${per_signal:.5f} | ¥{r['cost_usd'] * 150:.0f} |"
        )
    lines.append(
        f"| **合計** | **{sum(r['n_decisions'] for r in per_pair)}** | "
        f"**${total_cost:.4f}** | - | **¥{total_cost * 150:.0f}** |"
    )

    # 主要発見
    lines += [
        "",
        "---",
        "",
        "## ペア別 主要発見",
        "",
    ]
    for r in per_pair:
        base_pf = r["base"]["PF"]
        # 一番上がったカテゴリ
        cats = [
            ("CONFIRM only", r["confirm_only"]),
            ("CONFIRM+NEUTRAL", r["confirm_neutral"]),
            ("CONFIRM+CONTRADICT そのまま", r["confirm_plus_contradict_asis"]),
            ("CONTRADICT そのまま", r["contradict_asis"]),
        ]
        eligible = [(lbl, d) for lbl, d in cats if d["n"] >= 30 and d["PF"] != float("inf")]
        if eligible:
            best_local = max(eligible, key=lambda x: x[1]["PF"])
            lines.append(
                f"- **{r['pair']}**: base PF={base_pf:.3f}、最良カテゴリ={best_local[0]} "
                f"PF={best_local[1]['PF']:.3f} (n={best_local[1]['n']}, "
                f"diff={best_local[1]['PF'] - base_pf:+.3f})、"
                f"REJECT率={100 * r['distribution'].get('REJECT', 0) / r['total']:.1f}%"
            )
        else:
            # n<30 しかないケース (主に CONTRADICT)
            best_any = max(cats, key=lambda x: (x[1]["n"] >= 1, x[1]["PF"] if x[1]["PF"] != float("inf") else 0))
            lines.append(
                f"- **{r['pair']}**: base PF={base_pf:.3f}、有意 n≥30 カテゴリで最良候補なし。"
                f"参考: {best_any[0]} PF={pf_str(best_any[1])} (n={best_any[1]['n']})、"
                f"REJECT率={100 * r['distribution'].get('REJECT', 0) / r['total']:.1f}%"
            )

    # 結論
    any_pair_pass = any(
        gr['confirm_only_pass'] or gr['confirm_neutral_pass'] or gr['confirm_plus_pass']
        for gr in gate_results
    )

    # 合算ゲート
    base_pf_c = combined["base"]["PF"]
    combined_pass = False
    combined_passes_detail = []
    for lbl, key in [("CONFIRM only", "confirm_only"), ("CONFIRM+NEUTRAL", "confirm_neutral"),
                     ("CONFIRM+CONTRADICT そのまま", "confirm_plus_contradict_asis")]:
        d = combined[key]
        if d["n"] >= 30 and d["PF"] != float("inf"):
            diff = d["PF"] - base_pf_c
            if diff >= 0.30:
                combined_pass = True
                combined_passes_detail.append(f"{lbl}: diff={diff:+.3f}")

    lines += [
        "",
        "---",
        "",
        "## 結論",
        "",
    ]
    if combined_pass:
        lines += [
            f"- **3ペア合算でゲート PASS** ({'; '.join(combined_passes_detail)})",
            "- Phase 2' (新 SPEC v3 起草) 進出推奨",
            "- ペア依存性は要確認 (上記ペア別ゲート表を参照)",
        ]
    elif any_pair_pass:
        passed_pairs = [gr["pair"] for gr in gate_results
                       if gr['confirm_only_pass'] or gr['confirm_neutral_pass'] or gr['confirm_plus_pass']]
        lines += [
            f"- **個別ペアで PASS あり**: {', '.join(passed_pairs)}",
            "- 3ペア合算では FAIL → ペア依存性が強い可能性",
            "- 該当ペアに限定してプロンプト調整・追加検証検討",
        ]
    else:
        lines += [
            "- **全ペア・合算ともゲート FAIL**",
            f"- 最良の改善は{best['label']} ({best['pair']}) PF={best['pf']:.3f}",
            "- 第2サイクル LLM Direct Filter 撤退 or プロンプト大幅改修",
            "- CYCLE2_PLAN.md 撤退条件「Phase 0' 候補3本起草後 PF +0.3 未達」に該当",
        ]

    lines += [
        "",
        "---",
        "",
        "## ファイル",
        "",
        "- 入力: `data/signal_v2_historical_signals.csv` (3ペア合計 5,271 件)",
        "- 判定 CSV: `data/llm_filter_decisions_{gbp_jpy,usd_jpy,eur_usd}.csv`",
        "- 個別レポート: `docs/proposals/cycle2/LLM_FILTER_{GBP_JPY,USD_JPY,EUR_USD}_REPORT.md`",
        "- スクリプト: `scripts/_cycle2_llm_filter.py` (実行) / `scripts/_cycle2_llm_filter_aggregate.py` (本レポート生成)",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    if not SIGNALS_CSV.exists():
        print(f"signals CSV not found: {SIGNALS_CSV}", file=sys.stderr)
        return 2
    signals_all = pd.read_csv(SIGNALS_CSV)

    per_pair: list[dict] = []
    for pair in ["GBP_JPY", "USD_JPY", "EUR_USD"]:
        r = aggregate_per_pair(pair, signals_all)
        if r is None:
            print(f"WARN: {pair} の判定 CSV が見つかりません ({DECISIONS[pair]})", file=sys.stderr)
            continue
        per_pair.append(r)
        print(
            f"{pair}: n_signals={r['n_signals']}, n_decisions={r['n_decisions']}, "
            f"base_PF={pf_str(r['base'])}, confirm_only_PF={pf_str(r['confirm_only'])} (n={r['confirm_only']['n']}), "
            f"confirm_neutral_PF={pf_str(r['confirm_neutral'])} (n={r['confirm_neutral']['n']}), "
            f"contradict_asis_PF={pf_str(r['contradict_asis'])} (n={r['contradict_asis']['n']}), "
            f"reject_rate={100*r['distribution'].get('REJECT', 0)/r['total']:.1f}%, "
            f"cost=${r['cost_usd']:.4f}, errors={r['api_errors']}"
        )

    combined = aggregate_combined(per_pair) if per_pair else {}

    report = build_report(per_pair, combined)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(report, encoding="utf-8")
    print(f"\nレポート保存: {REPORT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
