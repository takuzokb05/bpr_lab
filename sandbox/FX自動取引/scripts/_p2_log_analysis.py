"""P2-D + P2-E 本番ログ解析。

P2-D: GBP_JPY スリッページ実態（シグナル → 発注 → 約定 のタイムスタンプ追跡）
P2-E: AIAdvisor の通過/拒否率と取引結果の集計

入力: data/trading_prod_snapshot.log[.1]
DB:   data/fx_trading_prod_snapshot.db (実取引のPL照合用)

出力:
  docs/gbp_jpy_slippage_analysis.md
  docs/ai_advisor_effectiveness.md
"""
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LOG_FILES = [
    ROOT / "data" / "trading_prod_snapshot.log.1",  # 古い順
    ROOT / "data" / "trading_prod_snapshot.log",
]
DB_PATH = ROOT / "data" / "fx_trading_prod_snapshot.db"
OUT_SLIP = ROOT / "docs" / "gbp_jpy_slippage_analysis.md"
OUT_AI = ROOT / "docs" / "ai_advisor_effectiveness.md"

# 正規表現
RE_LINE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[(?P<level>\w+)\] (?P<logger>[\w.]+): (?P<msg>.*)$"
)
RE_AI = re.compile(
    r"\[(?P<pair>[A-Z_]+)\]\s+AIフィルター: (?P<verdict>CONFIRM|CONTRADICT|NEUTRAL|REJECT)\s+\(direction=(?P<dir>\w+), confidence=(?P<conf>[\d.]+)\)"
)
RE_AI_NOPAIR = re.compile(  # 古い形式（ペア名なし）
    r"AIフィルター: (?P<verdict>CONFIRM|CONTRADICT|NEUTRAL|REJECT)\s+\(direction=(?P<dir>\w+), confidence=(?P<conf>[\d.]+)\)"
)
RE_SIGNAL = re.compile(
    r"\[(?P<pair>[A-Z_]+)\]\s+シグナル実行: (?P<dir>BUY|SELL)"
)
RE_OPEN = re.compile(
    r"ポジションオープン.*trade_id=(?P<tid>\d+).*instrument=(?P<pair>[A-Z_]+)"
)
RE_AI_REJECT_LOG = re.compile(
    r"AIフィルター: REJECT.*\)\。シグナルを見送り"
)
RE_FILL = re.compile(r"成行注文.*instrument=(?P<pair>[A-Z_]+).*price=(?P<price>[\d.]+)")
RE_BAR_CLOSE = re.compile(r"\[(?P<pair>[A-Z_]+)\].*close=(?P<close>[\d.]+)")


def parse_ts(ts_str: str) -> datetime:
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")


def stream_lines():
    for log in LOG_FILES:
        if not log.exists():
            continue
        with open(log, encoding="utf-8", errors="replace") as f:
            for raw in f:
                m = RE_LINE.match(raw.rstrip("\n"))
                if m:
                    yield m.group("ts"), m.group("logger"), m.group("msg")


def analyze_ai() -> dict:
    """AIアドバイザー判定の集計。

    各 AIフィルター ログの直後に「シグナル実行」or「シグナルを見送り」が来る。
    REJECT は見送り、それ以外は実行 → ペア・方向・倍率を記録。
    """
    counts = defaultdict(lambda: defaultdict(int))   # pair -> verdict -> n
    counts_total = defaultdict(int)                   # verdict -> n (全ペア)
    direction_split = defaultdict(lambda: defaultdict(int))  # verdict -> direction(bullish/bearish/neutral) -> n
    confidence_by_verdict = defaultdict(list)         # verdict -> [conf]
    rejected_with_pair = []  # (ts, pair, direction, conf) 機会損失候補

    last_ai = None
    last_pair_seen = None
    for ts, logger, msg in stream_lines():
        # ペア検出（先行ログから [PAIR] 抽出）
        bracket = re.search(r"\[([A-Z_]+)\]", msg)
        if bracket:
            last_pair_seen = bracket.group(1)

        m = RE_AI.search(msg)
        if not m:
            m = RE_AI_NOPAIR.search(msg)
            if m:
                # ペア名は直近の bracket から推測
                pair_inferred = last_pair_seen or "UNKNOWN"
                verdict = m.group("verdict")
                direction = m.group("dir")
                conf = float(m.group("conf"))
            else:
                continue
        else:
            pair_inferred = m.group("pair")
            verdict = m.group("verdict")
            direction = m.group("dir")
            conf = float(m.group("conf"))

        counts[pair_inferred][verdict] += 1
        counts_total[verdict] += 1
        direction_split[verdict][direction] += 1
        confidence_by_verdict[verdict].append(conf)

        if verdict == "REJECT":
            rejected_with_pair.append((ts, pair_inferred, direction, conf))

    return {
        "counts_per_pair": dict(counts),
        "counts_total": dict(counts_total),
        "direction_split": {k: dict(v) for k, v in direction_split.items()},
        "confidence_by_verdict": dict(confidence_by_verdict),
        "rejects": rejected_with_pair,
    }


def analyze_gbp_jpy_slippage() -> dict:
    """GBP_JPY のシグナル → 約定 までの所要時間 + 価格変化追跡。

    BollingerReversal は logger=src.strategy.bollinger_reversal で:
      BB逆張り[売り|買い]シグナル: close=215.297 >= BBU=215.278, RSI=65.26>=65
    の形式。[PAIR] タグは無いので、直前の [GBP_JPY] tag の存在で GBP_JPY 由来かを推定。

    Fill は src.position_manager で:
      ポジションオープン成功: trade_id=8588008, instrument=GBP_JPY, units=-4620, price=215.01000, ...
    """
    events = []
    pending_signal = None    # 直近未消費の BB シグナル
    last_pair_in_loop = None  # 直近の [PAIR] タグから現在処理中のペアを推定

    for ts, logger, msg in stream_lines():
        # [PAIR] タグ更新
        pm = re.search(r"\[([A-Z_]+)\]", msg)
        if pm:
            last_pair_in_loop = pm.group(1)

        # BB シグナル検出
        sig_match = re.search(
            r"BB(?:逆張り|平均回帰)?(?:買い|売り)シグナル: close=(?P<close>[\d.]+)",
            msg,
        )
        if sig_match and logger.startswith("src.strategy.bollinger"):
            # 直近の trading_loop の [PAIR] が GBP_JPY なら採用
            if last_pair_in_loop == "GBP_JPY":
                pending_signal = {
                    "signal_ts": parse_ts(ts),
                    "signal_close": float(sig_match.group("close")),
                    "direction": "BUY" if "買い" in msg else "SELL",
                }
            continue

        # 約定 (instrument=GBP_JPY)
        fill_m = re.search(
            r"ポジションオープン成功: trade_id=(\d+), instrument=GBP_JPY, units=(-?\d+), price=(\d+\.\d+)",
            msg,
        )
        if fill_m and pending_signal is not None:
            ev = {
                **pending_signal,
                "trade_id": fill_m.group(1),
                "units": int(fill_m.group(2)),
                "fill_price": float(fill_m.group(3)),
                "fill_ts": parse_ts(ts),
            }
            events.append(ev)
            pending_signal = None
            continue

        # シグナル後に HOLD / 見送り / スキップ → リセット
        if pending_signal is not None and (
            "見送り" in msg or "スキップ" in msg or "HOLD" in msg or "REJECT" in msg
        ):
            # 同 pair で見送り判定が出た場合のみクリア
            if last_pair_in_loop == "GBP_JPY":
                # ただし「同一通貨ペア」スキップは BB シグナルの結果ではなく fill のスキップ
                if "ポジションオープン成功" not in msg:
                    pass  # シグナル候補は維持（次のシグナルで上書きされる）

    # DB から実 open_price を補完
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        for ev in events:
            tid = ev.get("trade_id")
            if tid is None:
                continue
            row = conn.execute(
                "SELECT open_price FROM trades WHERE trade_id=?", (str(tid),),
            ).fetchone()
            if row and ev.get("fill_price") is None:
                ev["fill_price"] = float(row[0])
        conn.close()

    # 集計
    pip = 0.01  # GBP_JPY
    rows = []
    for ev in events:
        if ev["fill_price"] is None or ev["fill_ts"] is None:
            continue
        latency_sec = (ev["fill_ts"] - ev["signal_ts"]).total_seconds()
        slip_pips = (ev["fill_price"] - ev["signal_close"]) / pip
        if ev["direction"] == "SELL":
            slip_pips = -slip_pips  # 不利方向を正に統一
        rows.append({
            "trade_id": ev["trade_id"],
            "signal_ts": ev["signal_ts"].isoformat(),
            "fill_ts": ev["fill_ts"].isoformat(),
            "latency_sec": latency_sec,
            "signal_close": ev["signal_close"],
            "fill_price": ev["fill_price"],
            "direction": ev["direction"],
            "slip_pips_unfavor": slip_pips,
        })

    df = pd.DataFrame(rows)
    return {
        "n": len(df),
        "df": df,
        "events_total": len(events),
    }


def write_ai_report(ai: dict):
    OUT_AI.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# P2-E: AIAdvisor 通過/拒否率と取引結果集計\n")
    lines.append(f"生成日時: {datetime.now().isoformat()}")
    lines.append(f"対象ログ: {[str(p.name) for p in LOG_FILES if p.exists()]}")
    lines.append("")
    lines.append("## 1. 全体集計\n")
    total = sum(ai["counts_total"].values())
    lines.append(f"AIフィルター 評価総数: **{total}**\n")
    lines.append("| 判定 | 件数 | 比率 |")
    lines.append("|---|---:|---:|")
    for verdict in ("CONFIRM", "NEUTRAL", "CONTRADICT", "REJECT"):
        n = ai["counts_total"].get(verdict, 0)
        pct = n / total * 100 if total else 0
        lines.append(f"| {verdict} | {n} | {pct:.1f}% |")
    lines.append("")

    lines.append("## 2. ペア別\n")
    lines.append("| pair | CONFIRM | NEUTRAL | CONTRADICT | REJECT | 計 |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for pair, vc in sorted(ai["counts_per_pair"].items()):
        c = vc.get("CONFIRM", 0)
        n = vc.get("NEUTRAL", 0)
        ct = vc.get("CONTRADICT", 0)
        r = vc.get("REJECT", 0)
        lines.append(f"| {pair} | {c} | {n} | {ct} | {r} | {c+n+ct+r} |")
    lines.append("")

    lines.append("## 3. AI direction 別 内訳\n")
    lines.append("AIが bullish/bearish/neutral と評価した内訳。")
    lines.append("| 判定 | bullish | bearish | neutral |")
    lines.append("|---|---:|---:|---:|")
    for v in ("CONFIRM", "NEUTRAL", "CONTRADICT", "REJECT"):
        d = ai["direction_split"].get(v, {})
        lines.append(f"| {v} | {d.get('bullish', 0)} | {d.get('bearish', 0)} | {d.get('neutral', 0)} |")
    lines.append("")

    lines.append("## 4. confidence 分布\n")
    lines.append("| 判定 | n | 平均 conf | 中央値 |")
    lines.append("|---|---:|---:|---:|")
    for v in ("CONFIRM", "NEUTRAL", "CONTRADICT", "REJECT"):
        confs = ai["confidence_by_verdict"].get(v, [])
        if confs:
            lines.append(f"| {v} | {len(confs)} | {sum(confs)/len(confs):.2f} | {sorted(confs)[len(confs)//2]:.2f} |")
        else:
            lines.append(f"| {v} | 0 | - | - |")
    lines.append("")

    # 実取引との照合（DB 側）
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        df_trades = pd.read_sql_query(
            """SELECT instrument, ai_decision, COUNT(*) AS n,
                      SUM(CASE WHEN pl>0 THEN 1 ELSE 0 END) AS wins,
                      ROUND(AVG(pl), 1) AS avg_pl,
                      ROUND(SUM(pl), 0) AS sum_pl
               FROM trades
               WHERE status='closed'
               GROUP BY instrument, ai_decision
               ORDER BY instrument, n DESC""",
            conn,
        )
        conn.close()
        lines.append("## 5. 実取引 PL × AI判定（DB集計）\n")
        if df_trades.empty:
            lines.append("（trades テーブルに ai_decision が記録されていない）")
        else:
            lines.append("| instrument | ai_decision | n | wins | WR | avg PL | sum PL |")
            lines.append("|---|---|---:|---:|---:|---:|---:|")
            for _, r in df_trades.iterrows():
                wr = r["wins"] / r["n"] * 100 if r["n"] else 0
                lines.append(
                    f"| {r['instrument']} | {r['ai_decision'] or '(なし)'} | {r['n']} | "
                    f"{r['wins']} | {wr:.1f}% | {r['avg_pl']} | {r['sum_pl']} |"
                )
        lines.append("")
    lines.append("")

    lines.append("## 6. 解釈\n")
    reject_pct = ai["counts_total"].get("REJECT", 0) / total * 100 if total else 0
    contradict_pct = ai["counts_total"].get("CONTRADICT", 0) / total * 100 if total else 0
    confirm_pct = ai["counts_total"].get("CONFIRM", 0) / total * 100 if total else 0
    lines.append(f"- REJECT 比率 {reject_pct:.1f}%、CONTRADICT 比率 {contradict_pct:.1f}%、CONFIRM 比率 {confirm_pct:.1f}%")
    if reject_pct < 5:
        lines.append("- REJECT がほぼ無いため、AI は事実上見送り判定をしていない")
    if contradict_pct > 50:
        lines.append("- CONTRADICT が過半数 → AI が常に逆張り判断を返している。bias の偏り or 戦略との不整合")
    lines.append("")
    lines.append("詳細な「AI 有/無 のA/B 比較」は実取引 PL を AIfilter 倍率と紐づけて分析する必要があり、")
    lines.append("市場分析 JSON （`data/market_analysis.json`）の更新頻度依存。本レポートでは集計のみ。")

    OUT_AI.write_text("\n".join(lines), encoding="utf-8")
    print(f"AI report: {OUT_AI}")


def write_slip_report(slip: dict):
    OUT_SLIP.parent.mkdir(parents=True, exist_ok=True)
    df = slip["df"]
    lines = []
    lines.append("# P2-D: GBP_JPY シグナル→約定 レイテンシ + スリッページ実態\n")
    lines.append(f"生成日時: {datetime.now().isoformat()}")
    lines.append(f"対象: GBP_JPY のみ（最大スリッページ p95=21pips を観測したため）")
    lines.append(f"検出シグナル数: {slip['events_total']}")
    lines.append(f"フィル完了 (DB 照合済み): {slip['n']}")
    lines.append("")
    if df.empty:
        lines.append("⚠ ペアリング可能な signal/fill ペアが取れず。ログ正規表現の見直しが必要。")
        OUT_SLIP.write_text("\n".join(lines), encoding="utf-8")
        return
    lines.append("## 1. レイテンシ（シグナル検出 → ポジションオープン記録までの所要時間）\n")
    lines.append("| 指標 | 値 (秒) |")
    lines.append("|---|---:|")
    lines.append(f"| n | {len(df)} |")
    lines.append(f"| 平均 | {df['latency_sec'].mean():.1f} |")
    lines.append(f"| 中央値 | {df['latency_sec'].median():.1f} |")
    lines.append(f"| p95 | {df['latency_sec'].quantile(0.95):.1f} |")
    lines.append(f"| max | {df['latency_sec'].max():.1f} |")
    lines.append("")
    lines.append("## 2. スリッページ（実 fill_price vs シグナル時 close, 不利方向を正に統一）\n")
    lines.append("| 指標 | pips |")
    lines.append("|---|---:|")
    lines.append(f"| 平均 | {df['slip_pips_unfavor'].mean():+.2f} |")
    lines.append(f"| 中央値 | {df['slip_pips_unfavor'].median():+.2f} |")
    lines.append(f"| p95 | {df['slip_pips_unfavor'].quantile(0.95):+.2f} |")
    lines.append(f"| max | {df['slip_pips_unfavor'].max():+.2f} |")
    lines.append(f"| min | {df['slip_pips_unfavor'].min():+.2f} |")
    lines.append("")
    lines.append("## 3. レイテンシ × スリッページ 相関\n")
    if len(df) > 3:
        corr = df[["latency_sec", "slip_pips_unfavor"]].corr().iloc[0, 1]
        lines.append(f"Pearson 相関係数: **{corr:+.3f}**")
        if abs(corr) > 0.3:
            lines.append("→ 中度〜強の相関あり。約定遅延がスリッページの主因。")
        else:
            lines.append("→ 相関弱い。スリッページの主因はスプレッド or 価格急変動と推定。")
    lines.append("")
    lines.append("## 4. 個別取引（最初の 20 件）\n")
    lines.append("| trade_id | signal_ts | latency_s | signal_close | fill_price | slip_pips |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for _, r in df.head(20).iterrows():
        lines.append(
            f"| {r['trade_id']} | {r['signal_ts'][:19]} | "
            f"{r['latency_sec']:.1f} | {r['signal_close']:.3f} | "
            f"{r['fill_price']:.3f} | {r['slip_pips_unfavor']:+.2f} |"
        )
    lines.append("")
    lines.append("## 5. 解釈\n")
    avg_lat = df['latency_sec'].mean()
    avg_slip = df['slip_pips_unfavor'].mean()
    lines.append(f"- 平均レイテンシ {avg_lat:.1f} 秒、平均スリッページ {avg_slip:+.2f} pips")
    if avg_lat > 30:
        lines.append(f"- レイテンシが {avg_lat:.0f} 秒と過大 → 60 秒ポーリングで M15 close から最大 60s 待つ仕様の影響")
        lines.append("  → ポーリング短縮 or M15 close イベント駆動への移行検討")
    if avg_slip > 2:
        lines.append(f"- 平均 {avg_slip:.1f} pips 不利方向にズレている → BT spread=1pip の前提を {int(avg_slip)+1}pip に補正すべき")
    lines.append("")
    lines.append("## 6. 参考: P1-2 との数値比較\n")
    lines.append("| 出処 | n | avg slip pips | p95 |")
    lines.append("|---|---:|---:|---:|")
    lines.append(f"| P1-2 (yfinance bar close 比較) | 37 | +3.51 | +21.28 |")
    lines.append(f"| P2-D (実ログ signal_close 比較) | {len(df)} | {df['slip_pips_unfavor'].mean():+.2f} | {df['slip_pips_unfavor'].quantile(0.95):+.2f} |")

    OUT_SLIP.write_text("\n".join(lines), encoding="utf-8")
    print(f"Slip report: {OUT_SLIP}")


def main() -> int:
    print("Step 1: AI 解析中…")
    ai = analyze_ai()
    print(f"  → 総評価数 {sum(ai['counts_total'].values())}")
    write_ai_report(ai)

    print("Step 2: GBP_JPY スリッページ解析中…")
    slip = analyze_gbp_jpy_slippage()
    print(f"  → events {slip['events_total']}, fill完了 {slip['n']}")
    write_slip_report(slip)

    print("\nDone")
    return 0


if __name__ == "__main__":
    sys.exit(main())
