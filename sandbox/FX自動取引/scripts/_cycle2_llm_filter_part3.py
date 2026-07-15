"""
USD_JPY LLM Direct Filter — 3並列の Part 3 専用ランナー (index 1292-1890, 599件)

既存 `_cycle2_llm_filter.py` の build_user_prompt / call_llm / SYSTEM_PROMPT /
LEAKAGE_COLUMNS を**そのまま再利用**し、GBP_JPY/USD_JPY Part 1-2 と完全に
同一のプロンプト・モデル設定で残り 599 件を判定する。

差分:
    - 出力は `data/llm_filter_decisions_usd_jpy_subagent_part3.csv` 固定
    - 既判定 (`llm_filter_decisions_usd_jpy.csv`) を除外した残り 1891 件のうち
      index 1292-1890 (599 件) のみを処理
    - ThreadPoolExecutor で並列 (デフォルト 16)
    - インクリメンタル保存 (50件ごとに CSV を flush)
    - 同一 part3 CSV があれば signal_id 単位でスキップ (再開対応)
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
logger = logging.getLogger("cycle2_part3")


PAIR = "USD_JPY"
SLICE_START = 1292
SLICE_END = 1891  # exclusive (1292..1890 inclusive = 599 件)
OUTPUT_CSV = _PROJECT_ROOT / "data" / "llm_filter_decisions_usd_jpy_subagent_part3.csv"
EXISTING_CSV = _PROJECT_ROOT / "data" / "llm_filter_decisions_usd_jpy.csv"


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
    """中間保存。失敗してもクラッシュさせない。"""
    try:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(list(results.values()))
        df.to_csv(output_csv, index=False)
    except Exception as e:  # noqa: BLE001
        logger.warning("中間保存失敗: %s", e)


def run_parallel(
    todo_df: pd.DataFrame,
    client: Anthropic,
    output_csv: Path,
    workers: int,
    flush_every: int,
) -> pd.DataFrame:
    """並列で全シグナルを処理し、インクリメンタル保存しながら結果 DF を返す。"""
    # 再開: 既存 part3 CSV があれば処理済 signal_id を控える
    processed: dict[str, dict] = {}
    if output_csv.exists():
        try:
            existing = pd.read_csv(output_csv)
            for _, row in existing.iterrows():
                err = str(row.get("llm_error", "")).strip()
                reasoning = str(row.get("llm_reasoning", ""))
                if err and ("api_error" in reasoning or "parse_error" in reasoning):
                    continue  # 再実行対象
                processed[str(row["signal_id"])] = row.to_dict()
            logger.info(
                "既存 part3 CSV から %d 件読み込み (再実行除外後 %d 件スキップ)",
                len(existing), len(processed),
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("既存 CSV 読込失敗 — 全件やり直し: %s", e)
            processed = {}

    todo = todo_df[~todo_df["signal_id"].astype(str).isin(processed.keys())]
    n_todo = len(todo)
    n_skip = len(todo_df) - n_todo
    logger.info(
        "判定対象 %d / 全 %d (スキップ %d、workers=%d)",
        n_todo, len(todo_df), n_skip, workers,
    )
    if n_todo == 0:
        return pd.DataFrame(list(processed.values()))

    results: dict[str, dict] = dict(processed)
    t0 = time.time()
    done = 0
    total_cost = sum(float(r.get("api_cost_usd", 0) or 0) for r in processed.values())

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_process_one, client, row): row["signal_id"]
            for _, row in todo.iterrows()
        }
        for fut in as_completed(futures):
            sid = futures[fut]
            try:
                rec = fut.result()
            except Exception as e:  # noqa: BLE001
                logger.exception("worker failure for %s: %s", sid, e)
                rec = {
                    "signal_id": sid,
                    "pair": "",
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

            if done % flush_every == 0:
                _flush(results, output_csv)

    _flush(results, output_csv)
    logger.info("並列判定完了: 全 %d 件 / 総コスト $%.4f", len(results), total_cost)
    return pd.DataFrame(list(results.values()))


def main() -> int:
    parser = argparse.ArgumentParser(description="USD_JPY LLM Filter — Part 3 (index 1292-1890)")
    parser.add_argument("--workers", type=int, default=16, help="並列スレッド数")
    parser.add_argument("--flush-every", type=int, default=50, help="N 件ごとに CSV を保存")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        logger.error("ANTHROPIC_API_KEY が見つかりません (.env または環境変数)")
        return 2

    # 入力ロード
    logger.info("入力 CSV 読込: %s", INPUT_CSV)
    df = pd.read_csv(INPUT_CSV)
    usd = df[df["pair"] == PAIR].reset_index(drop=True)
    logger.info("%s 全件: %d", PAIR, len(usd))

    # 既判定の signal_id を除外
    if not EXISTING_CSV.exists():
        logger.error("既判定 CSV が存在しない: %s", EXISTING_CSV)
        return 3
    existing = pd.read_csv(EXISTING_CSV)
    done_ids = set(existing["signal_id"].astype(str).tolist())
    remaining = usd[~usd["signal_id"].astype(str).isin(done_ids)].reset_index(drop=True)
    logger.info("既判定除外後の残り: %d", len(remaining))

    # 私の slice
    slice_df = remaining.iloc[SLICE_START:SLICE_END].copy()
    logger.info(
        "Part 3 slice [%d:%d) = %d 件 (先頭 %s ... 末尾 %s)",
        SLICE_START, SLICE_END, len(slice_df),
        slice_df.iloc[0]["signal_id"] if len(slice_df) > 0 else "-",
        slice_df.iloc[-1]["signal_id"] if len(slice_df) > 0 else "-",
    )

    # リーク列の混入チェック (build_user_prompt が触れない設計だが念のためログ)
    leakage_hit = LEAKAGE_COLUMNS & set(slice_df.columns)
    logger.info("リーク列の存在 (CSV 上): %d 列 — プロンプトには渡らない設計", len(leakage_hit))

    logger.info(
        "モデル=%s, T=%.1f, workers=%d, output=%s",
        MODEL_ID, TEMPERATURE, args.workers, OUTPUT_CSV,
    )

    client = Anthropic(api_key=api_key)
    decisions = run_parallel(
        slice_df, client, OUTPUT_CSV,
        workers=args.workers, flush_every=args.flush_every,
    )

    # 簡易サマリ
    print("\n========== Part 3 完了サマリ ==========")
    print(f"対象: {PAIR} slice [{SLICE_START}:{SLICE_END}) = {len(slice_df)} 件")
    print(f"判定済み件数: {len(decisions)}")
    if "llm_decision" in decisions:
        print(f"判定分布: {decisions['llm_decision'].value_counts().to_dict()}")
    if "api_cost_usd" in decisions:
        print(f"API 実コスト: ${decisions['api_cost_usd'].sum():.4f}")
    print(f"出力: {OUTPUT_CSV}")
    print("==========================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
