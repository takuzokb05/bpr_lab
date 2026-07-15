"""GBP_JPY part1 context judgment - batch appender.

各バッチで rows リストに辞書を入れて実行する。append-onlyでCSVに追記。
"""
import csv
import sys
from pathlib import Path

OUTPUT = Path(r"c:\Users\takuz\プロジェクト\bpr_lab\sandbox\FX自動取引\data\llm_filter_decisions_gbp_jpy_context_part1.csv")

def append_batch(rows: list[dict]) -> int:
    """rows を CSV に append。書き込み件数を返す。"""
    fieldnames = [
        "signal_id", "pair", "timestamp_utc", "direction",
        "llm_decision", "llm_confidence", "llm_reasoning",
        "api_input_tokens", "api_output_tokens", "api_cost_usd", "llm_error",
    ]
    with OUTPUT.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for r in rows:
            # 必須フィールド補完
            r.setdefault("pair", "GBP_JPY")
            r.setdefault("api_input_tokens", 0)
            r.setdefault("api_output_tokens", 0)
            r.setdefault("api_cost_usd", 0.0)
            r.setdefault("llm_error", "")
            writer.writerow(r)
    return len(rows)


if __name__ == "__main__":
    # バッチデータは別ファイルから import
    import importlib.util
    batch_file = sys.argv[1]
    spec = importlib.util.spec_from_file_location("batch", batch_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    n = append_batch(mod.ROWS)
    print(f"Appended {n} rows to {OUTPUT.name}")
