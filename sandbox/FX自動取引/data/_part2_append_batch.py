"""Batch CSV appender for LLM filter decisions part2.
各バッチで rows リストを書き換えて実行する。"""
import csv
import sys

OUT_PATH = r"C:\Users\takuz\プロジェクト\bpr_lab\sandbox\FX自動取引\data\llm_filter_decisions_usd_jpy_context_part2.csv"

# 引数: バッチ番号
batch = sys.argv[1] if len(sys.argv) > 1 else "0"
print(f"Appending batch {batch}")

# rows は外部から差し込む (このスクリプトは下のロジックを書き換えて使う代わりに、
# 別途生成された rows.json を読み込む形にする)
import json
with open(rf"C:\Users\takuz\プロジェクト\bpr_lab\sandbox\FX自動取引\data\_part2_batch_{batch}.json", encoding="utf-8") as f:
    rows = json.load(f)

with open(OUT_PATH, "a", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    for r in rows:
        writer.writerow([
            r["signal_id"], r["pair"], r["timestamp_utc"], r["direction"],
            r["llm_decision"], r["llm_confidence"], r["llm_reasoning"],
            0, 0, 0.0, ""
        ])

print(f"Wrote {len(rows)} rows. New total:")
with open(OUT_PATH, encoding="utf-8") as f:
    total = sum(1 for _ in f) - 1
print(f"  decisions in CSV: {total}")
