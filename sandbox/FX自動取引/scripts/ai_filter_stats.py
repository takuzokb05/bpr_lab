"""AIフィルタ判定の統計と実トレードとの突合

入力:
- data/trading.log (UTF-8) からAIフィルタ判定とシグナル/発注を抽出
- MT5 history_deals で実PLを照合

出力:
- 判定別（CONFIRM/CONTRADICT/NEUTRAL/REJECT）の頻度
- 発注ログと判定の紐付け
- 実PLとの相関
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "trading.log"

# 正規表現パターン
RE_SIGNAL = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ "
    r".*?(押し目買いシグナル|戻り売りシグナル|BB逆張り売りシグナル|BB逆張り買いシグナル)"
)
RE_CONVICTION = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ .*?"
    r"\[(\w+)\] conviction score: (\d+)/10"
)
RE_AI_FILTER = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ .*?"
    r"AIフィルター: (CONFIRM|CONTRADICT|NEUTRAL|REJECT) "
    r"\(direction=(\w+), confidence=([\d\.]+)\)(?: → 倍率([\d\.]+))?"
)
RE_OPEN = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ .*?"
    r"ポジションオープン成功: trade_id=(\d+), instrument=(\w+), units=(-?\d+)"
)
RE_BEAR = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ .*?"
    r"Bear Researcher警告: severity=([\d\.]+)"
)


def parse_log():
    if not LOG_PATH.exists():
        print(f"ログファイル未発見: {LOG_PATH}")
        return

    ai_counts = defaultdict(int)
    bear_count = 0
    open_events: list[dict] = []
    recent_ai: dict | None = None  # 直近AI判定（ペア別に保持すべきだが現状簡易）
    recent_ai_by_pair: dict[str, dict] = {}
    recent_conv_by_pair: dict[str, dict] = {}

    with LOG_PATH.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = RE_CONVICTION.search(line)
            if m:
                ts, pair, score = m.group(1), m.group(2), int(m.group(3))
                recent_conv_by_pair[pair] = {"ts": ts, "score": score}
                continue

            m = RE_AI_FILTER.search(line)
            if m:
                ts, verdict, direction, conf = m.group(1), m.group(2), m.group(3), float(m.group(4))
                mult = float(m.group(5)) if m.group(5) else None
                ai_counts[verdict] += 1
                # 直近のconvictionとペアで紐付けたいが、判定ログにpair名がないので
                # 「直前のconvictionログのペア」を仮定（現状のログ仕様）
                last_conv = None
                for p, conv in recent_conv_by_pair.items():
                    if last_conv is None or conv["ts"] > last_conv["ts"]:
                        last_conv = conv
                        last_pair = p
                recent_ai_by_pair[last_pair if last_conv else "?"] = {
                    "ts": ts, "verdict": verdict,
                    "direction": direction, "confidence": conf,
                    "multiplier": mult,
                }
                continue

            m = RE_BEAR.search(line)
            if m:
                bear_count += 1
                continue

            m = RE_OPEN.search(line)
            if m:
                ts, trade_id, pair, units = m.group(1), m.group(2), m.group(3), int(m.group(4))
                side = "BUY" if units > 0 else "SELL"
                # 直近のAI判定（同pair）と紐付け
                ai = recent_ai_by_pair.get(pair)
                conv = recent_conv_by_pair.get(pair)
                open_events.append({
                    "ts": ts, "trade_id": trade_id, "pair": pair,
                    "side": side, "units": units,
                    "ai_verdict": ai["verdict"] if ai else "N/A",
                    "ai_direction": ai["direction"] if ai else "",
                    "ai_multiplier": ai["multiplier"] if ai else None,
                    "conviction": conv["score"] if conv else None,
                })

    print("=== AIフィルタ判定統計 ===")
    total = sum(ai_counts.values())
    for v in ["CONFIRM", "CONTRADICT", "NEUTRAL", "REJECT"]:
        c = ai_counts.get(v, 0)
        pct = (c / total * 100) if total else 0
        print(f"  {v:10s}: {c:4d}件 ({pct:5.1f}%)")
    print(f"  TOTAL     : {total:4d}件")
    print(f"\nBear Researcher警告: {bear_count}件")

    print(f"\n=== 発注イベント {len(open_events)}件 ===")
    print(f"{'timestamp':20s} {'trade_id':10s} {'pair':8s} {'side':5s} "
          f"{'conv':>4s} {'AI verdict':12s} {'AI dir':10s} {'mult':>5s}")
    for e in open_events:
        mult_s = f"{e['ai_multiplier']:.2f}" if e["ai_multiplier"] else "-"
        conv_s = str(e["conviction"]) if e["conviction"] is not None else "-"
        print(f"{e['ts']:20s} {e['trade_id']:10s} {e['pair']:8s} {e['side']:5s} "
              f"{conv_s:>4s} {e['ai_verdict']:12s} {e['ai_direction']:10s} {mult_s:>5s}")

    # MT5実PLと突合
    try:
        import MetaTrader5 as mt5
        mt5.initialize()
        to_date = datetime.now()
        from_date = to_date - timedelta(hours=48)
        deals = mt5.history_deals_get(from_date, to_date) or []
        pos_pl = {}
        for d in deals:
            pos_pl.setdefault(d.position_id, 0.0)
            pos_pl[d.position_id] += d.profit
        mt5.shutdown()

        print(f"\n=== AI判定別の実損益 ===")
        verdict_pl = defaultdict(lambda: {"n": 0, "wins": 0, "pl": 0.0})
        for e in open_events:
            tid = int(e["trade_id"])
            if tid in pos_pl:
                v = e["ai_verdict"]
                pl = pos_pl[tid]
                verdict_pl[v]["n"] += 1
                verdict_pl[v]["pl"] += pl
                if pl > 0:
                    verdict_pl[v]["wins"] += 1
        for v, s in verdict_pl.items():
            wr = (s["wins"] / s["n"] * 100) if s["n"] else 0
            print(f"  {v:12s}: {s['n']:3d}件 勝{s['wins']:3d} "
                  f"勝率{wr:5.1f}% 合計PL={s['pl']:+9.2f}")
    except Exception as e:
        print(f"\nMT5突合スキップ: {e}")


if __name__ == "__main__":
    parse_log()
