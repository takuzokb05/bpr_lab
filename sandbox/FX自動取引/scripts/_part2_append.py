"""Part2 バッチ append ツール — 判定行を CSV に追記。

LLM ロジックは含まない。各バッチで rows リストを Claude が手書きし、
このスクリプトは csv writer で安全に append するだけ。
"""
import csv
import sys
from pathlib import Path

OUT = Path("data/llm_filter_decisions_gbp_jpy_context_part2.csv")

def append_rows(rows):
    """rows: list of dict with keys matching header"""
    with OUT.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        for r in rows:
            w.writerow([
                r["signal_id"], r["pair"], r["timestamp_utc"], r["direction"],
                r["llm_decision"], r["llm_confidence"], r["llm_reasoning"],
                0, 0, 0.0, ""
            ])
    print(f"Appended {len(rows)} rows. Total now: {sum(1 for _ in OUT.open(encoding='utf-8')) - 1}")
