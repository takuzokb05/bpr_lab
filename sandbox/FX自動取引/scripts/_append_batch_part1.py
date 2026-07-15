# -*- coding: utf-8 -*-
"""バッチJSONを読んで context_part1.csv に追記する汎用スクリプト"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / 'data' / 'llm_filter_decisions_usd_jpy_context_part1.csv'

def append(batch_path: Path) -> int:
    """JSONバッチから rows を読んで CSV に追記する。"""
    with open(batch_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    rows = data['rows']
    with open(OUT_CSV, 'a', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow([
                r['signal_id'], r['pair'], r['timestamp_utc'], r['direction'],
                r['llm_decision'], r['llm_confidence'], r['llm_reasoning'],
                0, 0, 0.0, '',
            ])
    return len(rows)

if __name__ == '__main__':
    p = Path(sys.argv[1])
    n = append(p)
    print(f'Appended {n} rows from {p.name}')
