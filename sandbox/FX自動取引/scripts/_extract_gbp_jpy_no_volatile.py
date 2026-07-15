"""GBP_JPY signal_v2 シグナル抽出 (VOLATILE フィルタなし)

USD_JPY と公平比較するため、GBP_JPY も signal_v2 単独 (VOLATILE フィルタなし) で抽出。
既存 `_cycle2_extract_signals.py` のロジックを流用し、PAIR_CONFIG の
`use_volatile_filter` を False に強制する。

出力:
  data/signal_v2_historical_signals_gbp_jpy_no_volatile.csv

確認内容:
  - 既存 216件 (VOLATILE あり) の signal_id がすべて新 CSV に含まれているか
  - 抽出件数の増加
  - base PF (signal_v2 単独) と既存 PF の差
"""
from __future__ import annotations

import sys
from pathlib import Path
import csv

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# 既存抽出スクリプトを importlib 経由でモジュール化して再利用 (scripts/ は非パッケージ)
import importlib.util
_spec_path = ROOT / "scripts" / "_cycle2_extract_signals.py"
_spec = importlib.util.spec_from_file_location("_cycle2_extract_signals", _spec_path)
_cycle2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cycle2)

PAIR_CONFIG = _cycle2.PAIR_CONFIG
load_related_close_h1 = _cycle2.load_related_close_h1
extract_signals_for_pair = _cycle2.extract_signals_for_pair
summarize = _cycle2.summarize


def main() -> None:
    print("===== GBP_JPY signal_v2 抽出 (VOLATILE フィルタなし) =====\n")

    # 元の設定を壊さないようコピーして上書き
    pair = "GBP_JPY"
    original_use_volatile = PAIR_CONFIG[pair]["use_volatile_filter"]
    PAIR_CONFIG[pair]["use_volatile_filter"] = False
    print(f"PAIR_CONFIG[{pair}].use_volatile_filter: "
          f"{original_use_volatile} -> {PAIR_CONFIG[pair]['use_volatile_filter']}")

    print("\n関連通貨 H1 close 読み込み中...")
    related_closes = load_related_close_h1()
    for k, v in related_closes.items():
        print(f"  {k}: {len(v)} rows ({v.index[0]} -> {v.index[-1]})")

    # 抽出実行 (既存ロジックを呼ぶだけ)
    rows = extract_signals_for_pair(pair, related_closes)

    # 設定を元に戻す
    PAIR_CONFIG[pair]["use_volatile_filter"] = original_use_volatile

    # CSV 出力
    out_csv = ROOT / "data" / "signal_v2_historical_signals_gbp_jpy_no_volatile.csv"
    if rows:
        keys = list(rows[0].keys())
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nCSV 出力: {out_csv} ({len(rows)} rows)")
    else:
        print("\nERROR: シグナルなし")
        return

    # サマリ
    print("\n========== サマリ (signal_v2 単独, VOLATILE なし) ==========")
    s = summarize(rows, f"{pair} (no VOLATILE)")
    for k, v in s.items():
        if k != "label":
            print(f"  {k}: {v}")

    # ============================================================
    # Sanity check: 既存 216 件 (VOLATILE あり) が新 CSV に含まれているか
    # ============================================================
    print("\n========== Sanity check ==========")
    existing_csv = ROOT / "data" / "signal_v2_historical_signals.csv"
    existing_df = pd.read_csv(existing_csv)
    existing_gbp = existing_df[existing_df["pair"] == pair].copy()
    print(f"既存 (VOLATILE あり) GBP_JPY: {len(existing_gbp)} 件")

    new_df = pd.DataFrame(rows)
    print(f"新 (VOLATILE なし) GBP_JPY: {len(new_df)} 件")

    # signal_id は idx 順に振られているため新旧で一致しない可能性がある。
    # timestamp_utc + direction の組で照合する
    existing_keys = set(zip(existing_gbp["timestamp_utc"], existing_gbp["direction"]))
    new_keys = set(zip(new_df["timestamp_utc"], new_df["direction"]))

    missing = existing_keys - new_keys
    print(f"既存 -> 新 で消えたシグナル: {len(missing)} 件")
    if missing:
        print("  最初の5件:")
        for m in list(missing)[:5]:
            print(f"    {m}")

    contained = existing_keys & new_keys
    print(f"既存 -> 新 で残ったシグナル: {len(contained)} / {len(existing_keys)}")
    inclusion_rate = len(contained) / len(existing_keys) * 100 if existing_keys else 0
    print(f"既存包含率: {inclusion_rate:.2f}%")

    # ============================================================
    # 既存 216 件の PF と新 CSV の PF を比較
    # ============================================================
    print("\n========== PF 比較 ==========")
    existing_summary = summarize(existing_gbp.to_dict("records"), f"{pair} (VOLATILE あり)")
    print("\n[既存 GBP_JPY: VOLATILE フィルタあり, 216件]")
    for k, v in existing_summary.items():
        if k != "label":
            print(f"  {k}: {v}")

    print(f"\n[新 GBP_JPY: signal_v2 単独, VOLATILE なし, {len(rows)}件]")
    for k, v in s.items():
        if k != "label":
            print(f"  {k}: {v}")

    # 差異まとめ
    print("\n========== 差異 ==========")
    n_diff = len(rows) - len(existing_gbp)
    pf_existing = existing_summary.get("PF", 0)
    pf_new = s.get("PF", 0)
    print(f"  件数差: +{n_diff} ({len(existing_gbp)} -> {len(rows)})")
    print(f"  PF 差: {pf_existing} -> {pf_new}  (delta={round(pf_new - pf_existing, 3) if pf_existing != float('inf') else 'N/A'})")
    print(f"  既存 win_rate: {existing_summary.get('win_rate_pct', 0)}%  /  新 win_rate: {s.get('win_rate_pct', 0)}%")


if __name__ == "__main__":
    main()
