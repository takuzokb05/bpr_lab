"""
第2サイクル LLM Direct Filter — USD_JPY サブエージェント part2 (index 646-1291)

`_cycle2_llm_filter.py` の build_user_prompt / call_llm を完全再利用し、
USD_JPY の未判定シグナル 1,891 件のうち、判定順 index 646-1291 の 646 件のみを処理する。

出力:
    data/llm_filter_decisions_usd_jpy_subagent_part2.csv

H9-1 と同じ判定基準・列構成・リーク防止を維持する。
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

# .env をロード (CLAUDE.md: ハードコード禁止)
from dotenv import load_dotenv  # noqa: E402

for env_path in [
    _PROJECT_ROOT / ".env",
    _PROJECT_ROOT.parent / "タスクマネージャー" / ".env",
    _PROJECT_ROOT.parent / "住宅比較" / ".env",
]:
    if env_path.exists():
        load_dotenv(env_path, override=False)

# 既存スクリプトから完全に同じ実装を import (再現性保証)
from _cycle2_llm_filter import (  # noqa: E402
    INPUT_CSV,
    MODEL_ID,
    TEMPERATURE,
    LEAKAGE_COLUMNS,
    build_user_prompt,
    call_llm,
)

from anthropic import Anthropic  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("cycle2_subagent_part2")

TARGET_PAIR = "USD_JPY"
SLICE_START = 646
SLICE_END = 1291  # inclusive
OUTPUT_CSV = _PROJECT_ROOT / "data" / "llm_filter_decisions_usd_jpy_subagent_part2.csv"
ALREADY_CSV = _PROJECT_ROOT / "data" / "llm_filter_decisions_usd_jpy.csv"


def _process_one(client: Anthropic, row: pd.Series) -> dict:
    """1 シグナルの判定 + 結果 dict を返す (スレッドから呼ばれる)。"""
    prompt = build_user_prompt(row)
    result = call_llm(client, prompt)
    return {
        "signal_id": row["signal_id"],
        "pair": row["pair"],
        "timestamp_utc": row["timestamp_utc"],
        "direction": row["direction"],
        "llm_decision": result.decision,
        "llm_confidence": result.confidence,
        "llm_reasoning": result.reasoning,
        "api_input_tokens": result.input_tokens,
        "api_output_tokens": result.output_tokens,
        "api_cost_usd": result.cost_usd,
        "llm_error": result.error or "",
    }


def _flush(results: dict, output_csv: Path) -> None:
    try:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(list(results.values()))
        df.to_csv(output_csv, index=False)
    except Exception as e:  # noqa: BLE001
        logger.warning("中間保存失敗: %s", e)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cycle 2 LLM Filter — subagent part2 (USD_JPY 646-1291)")
    parser.add_argument("--workers", type=int, default=12, help="並列スレッド数")
    parser.add_argument("--flush-every", type=int, default=25, help="N 件ごとに CSV を保存")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        logger.error("ANTHROPIC_API_KEY が見つかりません")
        return 2

    # シグナル抽出
    df = pd.read_csv(INPUT_CSV)
    usd = df[df["pair"] == TARGET_PAIR].copy().reset_index(drop=True)
    logger.info("%s 全件: %d", TARGET_PAIR, len(usd))

    # 既判定 (元の本判定 CSV) を除外
    if ALREADY_CSV.exists():
        done = pd.read_csv(ALREADY_CSV)
        done_ids = set(done["signal_id"].astype(str))
        logger.info("既判定 (%s): %d 件", ALREADY_CSV.name, len(done_ids))
    else:
        done_ids = set()
        logger.warning("既判定 CSV が見つからない: %s", ALREADY_CSV)

    remaining = usd[~usd["signal_id"].astype(str).isin(done_ids)].copy().reset_index(drop=True)
    logger.info("残り未判定: %d 件", len(remaining))

    # 担当スライス
    end = min(SLICE_END, len(remaining) - 1)
    target = remaining.iloc[SLICE_START : end + 1].copy().reset_index(drop=True)
    logger.info("担当 index %d-%d: %d 件 (first=%s, last=%s)",
                SLICE_START, end, len(target),
                target.iloc[0]["signal_id"], target.iloc[-1]["signal_id"])

    # リーク列除外確認
    leakage_hit = LEAKAGE_COLUMNS & set(target.columns)
    logger.info("リーク列除外確認: %d 列 (プロンプトには渡らない設計)", len(leakage_hit))

    # 既に subagent_part2 CSV があれば再開
    processed: dict[str, dict] = {}
    if OUTPUT_CSV.exists():
        try:
            existing = pd.read_csv(OUTPUT_CSV)
            for _, row in existing.iterrows():
                err = str(row.get("llm_error", "")).strip()
                reasoning = str(row.get("llm_reasoning", ""))
                if err and ("api_error" in reasoning or "parse_error" in reasoning):
                    continue
                processed[str(row["signal_id"])] = row.to_dict()
            logger.info("既存 part2 CSV から %d 件をスキップ", len(processed))
        except Exception as e:  # noqa: BLE001
            logger.warning("既存 part2 CSV 読込失敗 — 全件やり直し: %s", e)
            processed = {}

    todo = target[~target["signal_id"].astype(str).isin(processed.keys())]
    n_todo = len(todo)
    logger.info("判定対象 %d / 担当 %d (スキップ %d、workers=%d, model=%s, T=%.1f)",
                n_todo, len(target), len(target) - n_todo, args.workers, MODEL_ID, TEMPERATURE)

    if n_todo == 0:
        logger.info("全件処理済み")
        return 0

    client = Anthropic(api_key=api_key)
    results: dict[str, dict] = dict(processed)
    t0 = time.time()
    done = 0
    total_cost = sum(float(r.get("api_cost_usd", 0) or 0) for r in processed.values())

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_process_one, client, row): row["signal_id"]
                   for _, row in todo.iterrows()}
        for fut in as_completed(futures):
            sid = futures[fut]
            try:
                rec = fut.result()
            except Exception as e:  # noqa: BLE001
                logger.exception("worker failure for %s: %s", sid, e)
                rec = {
                    "signal_id": sid,
                    "pair": TARGET_PAIR,
                    "timestamp_utc": "",
                    "direction": "",
                    "llm_decision": "REJECT",
                    "llm_confidence": 0.0,
                    "llm_reasoning": f"[worker_exception] {type(e).__name__}: {e}",
                    "api_input_tokens": 0,
                    "api_output_tokens": 0,
                    "api_cost_usd": 0.0,
                    "llm_error": f"{type(e).__name__}: {e}",
                }
            results[str(rec["signal_id"])] = rec
            total_cost += float(rec.get("api_cost_usd", 0) or 0)
            done += 1

            if done % 25 == 0 or done == n_todo:
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed > 0 else 0
                eta = (n_todo - done) / rate if rate > 0 else 0
                logger.info(
                    "進捗 %d/%d (%.1f%%) | elapsed=%.0fs | rate=%.1f/s | ETA=%.0fs | cost=$%.3f",
                    done, n_todo, 100 * done / n_todo, elapsed, rate, eta, total_cost,
                )

            if done % args.flush_every == 0:
                _flush(results, OUTPUT_CSV)

    _flush(results, OUTPUT_CSV)
    logger.info("part2 判定完了: %d 件 / 総コスト $%.4f", len(results), total_cost)

    # 結果サマリ
    final = pd.DataFrame(list(results.values()))
    dist = final["llm_decision"].value_counts().to_dict()
    print("\n========== part2 集計 ==========")
    print(f"対象: {TARGET_PAIR} index {SLICE_START}-{end} (担当 {len(target)} 件 / 判定 {len(final)} 件)")
    print(f"判定分布: {dist}")
    print(f"API 実コスト: ${total_cost:.4f}")
    err_n = final["llm_error"].fillna("").astype(str).str.strip().str.len().gt(0).sum()
    print(f"API エラー件数: {err_n}")
    print("================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
