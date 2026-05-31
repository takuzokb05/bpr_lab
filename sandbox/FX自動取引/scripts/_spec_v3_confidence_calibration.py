"""SPEC v3 — LLM confidence 判別力(discrimination)・校正(calibration)測定

Phase 0' の正式判定データと signal_v2 の実勝敗を signal_id で JOIN し、
LLM の自己申告 confidence が
  - 実勝率を「分離するか」(AUC / discrimination)
  - 絶対値が実勝率と「一致するか」(ECE / calibration)
を測る。

正式判定データ (docs/proposals/cycle2/IMPROVEMENT_META_ANALYSIS.md の「ファイル」節準拠):
  - USD_JPY: llm_filter_decisions_usd_jpy.csv (725) + _context_part{1,2,3} (1891) = 2616件
  - GBP_JPY: llm_filter_decisions_gbp_jpy_context_part{1,2,3} = 2443件
  - 勝敗: signal_v2_historical_signals.csv (USD) / _gbp_jpy_no_volatile.csv (GBP) の win_loss_sl_tp

背景: 旧 AIAdvisor は confidence 0.43-0.46 でラベル間分離なし (docs/ai_advisor_effectiveness.md)。
SPEC v3 が同じ運命か (AUC≈0.5) を定量化する。LLM コストゼロ (既存 CSV 集計のみ)。
外部調査の裏付け: docs/analysis/LLM_ADVISORY_EXTERNAL_RESEARCH.md finding 8 (ECE 0.49-0.57)。
"""
import sys
import argparse
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding='utf-8')  # Windows cp932 文字化け対策
except Exception:
    pass
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BINS = [0.0, 0.5, 0.6, 0.7, 0.8, 1.0001]


def load_official(pair: str):
    """正式判定データ × 実勝敗を JOIN して返す。"""
    if pair == "USD_JPY":
        base = pd.read_csv("data/llm_filter_decisions_usd_jpy.csv")
        ctx = pd.concat(
            [pd.read_csv(f"data/llm_filter_decisions_usd_jpy_context_part{i}.csv") for i in (1, 2, 3)],
            ignore_index=True,
        )
        dec = pd.concat([base, ctx], ignore_index=True)
        sig = pd.read_csv("data/signal_v2_historical_signals.csv")
        sig = sig[sig["pair"] == "USD_JPY"].copy()
        thr = 0.65
    elif pair == "GBP_JPY":
        dec = pd.concat(
            [pd.read_csv(f"data/llm_filter_decisions_gbp_jpy_context_part{i}.csv") for i in (1, 2, 3)],
            ignore_index=True,
        )
        sig = pd.read_csv("data/signal_v2_historical_signals_gbp_jpy_no_volatile.csv")
        thr = 0.60
    else:
        raise ValueError(pair)
    dec = dec.drop_duplicates("signal_id")
    m = dec.merge(sig[["signal_id", "win_loss_sl_tp"]], on="signal_id", how="inner")
    m["win"] = (m["win_loss_sl_tp"] == "WIN").astype(int)
    return m, thr


def auc_score(scores, labels) -> float:
    """ROC-AUC を rank ベース(Mann-Whitney U)で計算。sklearn/scipy 非依存。
    AUC = P(score(win) > score(loss))。0.5=判別力なし、1.0=完全分離。"""
    scores = np.asarray(scores, float)
    labels = np.asarray(labels, int)
    n_pos = int(labels.sum())
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = pd.Series(scores).rank().values  # tie は平均rank
    u = ranks[labels == 1].sum() - n_pos * (n_pos + 1) / 2.0
    return float(u / (n_pos * n_neg))


def calibration(conf, win, bins=BINS):
    """ECE と bin 別校正曲線 (mean_conf vs 実勝率) を返す。"""
    conf = np.asarray(conf, float)
    win = np.asarray(win, int)
    N = len(conf)
    ece = 0.0
    rows = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (conf >= lo) & (conf < hi)
        n = int(mask.sum())
        if n == 0:
            rows.append((f"[{lo:.2f},{hi:.2f})", 0, None, None))
            continue
        mc = float(conf[mask].mean())
        acc = float(win[mask].mean())
        ece += n / N * abs(mc - acc)
        rows.append((f"[{lo:.2f},{hi:.2f})", n, round(mc, 3), round(acc, 3)))
    return ece, rows


def report(pair: str):
    m, thr = load_official(pair)
    print(f"\n{'='*64}\n{pair}  (JOIN後 n={len(m)}, 採用閾値={thr})")
    print(f"  全体勝率 (signal_v2 素): {m['win'].mean():.3f}")
    print(f"  判定分布: {m['llm_decision'].value_counts().to_dict()}")

    auc_all = auc_score(m["llm_confidence"], m["win"])
    print(f"  [全判定]      AUC(confidence→win) = {auc_all:.3f}")

    c = m[m["llm_decision"] == "CONFIRM"]
    auc_c = auc_score(c["llm_confidence"], c["win"])
    print(f"  [CONFIRM only n={len(c)}] AUC = {auc_c:.3f}  勝率 {c['win'].mean():.3f}")

    ece, rows = calibration(c["llm_confidence"], c["win"])
    print(f"  [CONFIRM] ECE = {ece:.3f}  (0=完全校正、大きいほど絶対値がズレ)")
    print("    bin            n    mean_conf  win_rate  (conf>win_rate=過信)")
    for b, n, mc, acc in rows:
        print(f"    {b:14s} {n:4d}     {str(mc):>6}    {str(acc):>6}")

    adopt = c[c["llm_confidence"] >= thr]
    wr = adopt["win"].mean() if len(adopt) else float("nan")
    print(f"  [採用群 CONFIRM&conf>={thr}] n={len(adopt)} 勝率 {wr:.3f}"
          f"  (RR2:1想定 PF≈{2*wr/(1-wr):.3f})" if len(adopt) else "")
    return m


def report_db(pair: str, thr: float):
    """デモDB (fx_spec_v3.db) の採用群から AUC/ECE/校正曲線を出す (Phase 2'B 判定用)。"""
    sys.path.insert(0, str(ROOT))
    from src.spec_v3 import db as v3_db
    db_path = ROOT / "data" / "fx_spec_v3.db"
    outcomes = v3_db.confirm_confidence_outcomes(db_path, pair)
    print(f"\n{'='*64}\n{pair} (デモDB 採用群, 閾値={thr})")
    if len(outcomes) < 1:
        print("  採用群データなし (デモ未起動 or 決済済トレード未発生)。n=0")
        return
    conf = [o[0] for o in outcomes]
    win = [o[1] for o in outcomes]
    auc = auc_score(conf, win)
    ece, rows = calibration(conf, win)
    wr = sum(win) / len(win)
    auc_s = "N/A" if auc is None else f"{auc:.3f}"
    print(f"  採用群 n={len(outcomes)}  勝率={wr:.3f}  AUC={auc_s}  ECE={ece:.3f}")
    print("    bin            n    mean_conf  win_rate")
    for b, n, mc, acc in rows:
        print(f"    {b:14s} {n:4d}     {str(mc):>6}    {str(acc):>6}")
    if auc is not None and len(outcomes) >= 20:
        verdict = "判別力あり (gate PASS)" if auc >= 0.55 else "判別力不足 (gate FAIL → 閾値見直し)"
        print(f"  → AUC gate (>=0.55): {verdict}")
    else:
        print("  → n<20 のため AUC 判定保留")


def _run_csv():
    ms = [report(p) for p in ("USD_JPY", "GBP_JPY")]
    comb = pd.concat(ms, ignore_index=True)
    c = comb[comb["llm_decision"] == "CONFIRM"]
    print(f"\n{'='*64}\nCOMBINED")
    print(f"  [全判定 n={len(comb)}] AUC = {auc_score(comb['llm_confidence'], comb['win']):.3f}")
    print(f"  [CONFIRM n={len(c)}] AUC = {auc_score(c['llm_confidence'], c['win']):.3f}  勝率 {c['win'].mean():.3f}")
    ece, rows = calibration(c["llm_confidence"], c["win"])
    print(f"  [CONFIRM] ECE = {ece:.3f}")
    print("    bin            n    mean_conf  win_rate")
    for b, n, mc, acc in rows:
        print(f"    {b:14s} {n:4d}     {str(mc):>6}    {str(acc):>6}")
    print("\n[解釈ガイド]")
    print("  AUC>0.55 = confidence に判別力あり(高conf=高勝率)。0.5付近 = 旧AIAdvisorと同じく信号にならない。")
    print("  ECE大 = 絶対値はズレている(conf 0.7でも勝率0.7ではない)。閾値運用には discrimination(AUC)が重要。")


def _run_db():
    sys.path.insert(0, str(ROOT))
    from src.spec_v3 import CONFIDENCE_THRESHOLDS
    for pair in ("USD_JPY", "GBP_JPY"):
        report_db(pair, CONFIDENCE_THRESHOLDS.get(pair, 0.65))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="SPEC v3 confidence 判別力/校正測定")
    ap.add_argument("--source", choices=["csv", "db"], default="csv",
                    help="csv=Phase 0' 判定CSV(確定済) / db=デモDB fx_spec_v3.db(Phase 2'B 用)")
    args = ap.parse_args()
    (_run_db if args.source == "db" else _run_csv)()
