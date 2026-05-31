"""SPEC v3 — 記憶リーク診断 (recall probe)

LLM (Claude Sonnet 4.6) に文脈なしで過去の月次騰落を recall させ、的中率が
「トレンド多数派ベースライン」を超えるか = 単なるトレンド知識でなく『個別月の記憶』
があるかを測る。hold-out 期間 (2026) で的中率が baseline を大きく超えれば、
hold-out PF 1.304 は記憶リークで水増しされている疑い。

手法出典: docs/analysis/LLM_ADVISORY_EXTERNAL_RESEARCH.md finding 10
          (Economics Letters S0165176525004392 の recall プロキシ)
コスト方針: LLM 問い合わせは API 直叩きせず、メイン側が Agent tool (サブエージェント)
            経由で実施 (CLAUDE.md コスト管理ルール)。本スクリプトは正解生成と採点のみ。

使い方:
  python scripts/_spec_v3_leak_diagnostic.py gen     # 正解+質問を生成
  # → メイン側が data/_leak_diag_questions.json をサブエージェントに渡し、
  #    WebSearch 禁止・記憶のみで回答させ、data/_leak_diag_answers.json に保存
  python scripts/_spec_v3_leak_diagnostic.py score   # 的中率 vs baseline を集計
"""
import sys
import json
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import pandas as pd
import numpy as np

PAIRS = {
    "USD_JPY": "data/mt5_USD_JPY_D1_10y.csv",
    "GBP_JPY": "data/mt5_GBP_JPY_D1_10y.csv",
}
START = "2021-01"          # カットオフ前(記憶テスト) 〜 hold-out(2026) をカバー
TRUTH = "data/_leak_diag_truth.json"
QUESTIONS = "data/_leak_diag_questions.json"
ANSWERS = "data/_leak_diag_answers.json"
RECALL_FLAG_MARGIN = 0.10  # baseline + これ以上で「記憶疑い」フラグ


def monthly_dir(csv: str) -> dict:
    """D1 OHLCV から月初→月末の騰落 (up/down) を計算して {YYYY-MM: dir} を返す。"""
    df = pd.read_csv(csv)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df["ym"] = df["datetime"].dt.strftime("%Y-%m")
    g = df.sort_values("datetime").groupby("ym")["close"].agg(["first", "last"])
    g = g[g.index >= START]
    g["dir"] = np.where(g["last"] > g["first"], "up", "down")
    return g["dir"].to_dict()


def gen():
    truth, questions = {}, []
    for pair, csv in PAIRS.items():
        d = monthly_dir(csv)
        truth[pair] = d
        for ym in sorted(d):
            questions.append({"pair": pair, "month": ym})
    json.dump(truth, open(TRUTH, "w"), indent=2)
    json.dump(questions, open(QUESTIONS, "w"), ensure_ascii=False, indent=2)
    total = sum(len(v) for v in truth.values())
    print(f"生成: {total} 問 ({len(PAIRS)} ペア)")
    print(f"  truth     -> {TRUTH}")
    print(f"  questions -> {QUESTIONS}")
    for pair in PAIRS:
        s = pd.Series(truth[pair])
        s.index = pd.to_datetime(s.index)
        print(f"\n{pair} 月次騰落 (年別 up率 / トレンド baseline):")
        for y, grp in s.groupby(s.index.year):
            up = (grp == "up").mean()
            print(f"  {y}: n={len(grp):2d}  up率={up:.2f}  baseline(多数派)={max(up, 1 - up):.2f}")


def score():
    truth = json.load(open(TRUTH))
    ans = json.load(open(ANSWERS))  # [{pair, month, direction}, ...]
    amap = {(a["pair"], a["month"]): str(a.get("direction", "unknown")).lower() for a in ans}

    rows = []
    for pair in truth:
        for ym, t in truth[pair].items():
            a = amap.get((pair, ym), "missing")
            rows.append({
                "pair": pair, "year": int(ym[:4]), "truth": t, "answer": a,
                "correct": int(a == t), "answered": int(a in ("up", "down")),
            })
    df = pd.DataFrame(rows)

    print("=== 記憶リーク診断 結果 (recall probe) ===")
    for pair in truth:
        sub = df[df.pair == pair]
        print(f"\n{pair}:")
        print("  year  回答済/総数  的中率  baseline  unknown率  判定")
        for y, g in sub.groupby("year"):
            ans_g = g[g.answered == 1]
            acc = ans_g["correct"].mean() if len(ans_g) else float("nan")
            truths = g["truth"]
            base = max((truths == "up").mean(), (truths == "down").mean())
            unk = (g.answered == 0).mean()
            flag = ""
            if len(ans_g) and acc > base + RECALL_FLAG_MARGIN:
                flag = "<-- baseline超え(記憶疑い)"
            print(f"  {y}   {len(ans_g):2d}/{len(g):2d}        {acc:.2f}    {base:.2f}      {unk:.2f}     {flag}")

    print("\n[解釈]")
    print("  hold-out=2026年。2026の的中率が baseline を大きく超える → hold-out PF が記憶リークで水増しの疑い。")
    print("  2021-2024 で高く 2025-2026 で50%/baseline付近に落ちる → 正常なカットオフ境界(リーク無し)。")
    print("  全年とも baseline 付近 → そもそも recall できておらず、価格のみ構成のリーク懸念は小さい。")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "gen"
    {"gen": gen, "score": score}[mode]()
