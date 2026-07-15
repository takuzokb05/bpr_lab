"""
第2サイクル LLM Direct Filter — 並列ランナー (USD_JPY / EUR_USD 拡張用)

既存 `_cycle2_llm_filter.py` の build_user_prompt / call_llm / SYSTEM_PROMPT を
**そのまま再利用** することで、GBP_JPY と完全に同一のプロンプト・モデル設定で
USD_JPY / EUR_USD を高速 (並列) に処理する。

差分:
    - ThreadPoolExecutor で並列度 N (デフォルト 16)
    - インクリメンタル保存 (50件ごとに CSV を flush)
    - 既存 CSV があれば signal_id 単位でスキップ (再開対応)
    - sleep 不要 (並列度で実効レート制御)

出力:
    data/llm_filter_decisions_{pair_lower}.csv
    docs/proposals/cycle2/LLM_FILTER_{PAIR}_REPORT.md  (build_report 経由で生成)
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
    build_paths,
    aggregate_pf,
    build_report,
)

from anthropic import Anthropic  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("cycle2_parallel")


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


def run_parallel(
    signals: pd.DataFrame,
    client: Anthropic,
    output_csv: Path,
    workers: int,
    flush_every: int,
) -> pd.DataFrame:
    """並列で全シグナルを処理し、インクリメンタル保存しながら結果 DF を返す。"""
    # 再開: 既存 CSV があれば処理済 signal_id を控える
    processed: dict[str, dict] = {}
    if output_csv.exists():
        try:
            existing = pd.read_csv(output_csv)
            for _, row in existing.iterrows():
                # エラー再試行: llm_error が空でない or decision=REJECT で reasoning が parse_error/api_error の場合は再実行
                err = str(row.get("llm_error", "")).strip()
                reasoning = str(row.get("llm_reasoning", ""))
                if err and ("api_error" in reasoning or "parse_error" in reasoning):
                    continue  # 再実行対象
                processed[str(row["signal_id"])] = row.to_dict()
            logger.info(
                "既存 CSV から %d 件読み込み (うち再実行除外後 %d 件をスキップ対象)",
                len(existing), len(processed),
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("既存 CSV 読込失敗 — 全件やり直し: %s", e)
            processed = {}

    todo = signals[~signals["signal_id"].astype(str).isin(processed.keys())]
    n_todo = len(todo)
    n_skip = len(signals) - n_todo
    logger.info(
        "判定対象 %d / 全 %d (スキップ %d、workers=%d)",
        n_todo, len(signals), n_skip, workers,
    )
    if n_todo == 0:
        # 全件処理済み
        return pd.DataFrame(list(processed.values()))

    results: dict[str, dict] = dict(processed)  # 上書き可
    t0 = time.time()
    done = 0
    total_cost = sum(float(r.get("api_cost_usd", 0) or 0) for r in processed.values())

    with ThreadPoolExecutor(max_workers=workers) as pool:
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


def _flush(results: dict, output_csv: Path) -> None:
    """中間保存。失敗してもクラッシュさせない。"""
    try:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(list(results.values()))
        df.to_csv(output_csv, index=False)
    except Exception as e:  # noqa: BLE001
        logger.warning("中間保存失敗: %s", e)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cycle 2 LLM Filter (parallel runner)")
    parser.add_argument("--pair", required=True, help="対象通貨ペア (例: USD_JPY)")
    parser.add_argument("--workers", type=int, default=16, help="並列スレッド数")
    parser.add_argument("--flush-every", type=int, default=50, help="N 件ごとに CSV を保存")
    parser.add_argument("--limit", type=int, default=None, help="検証件数の上限 (デバッグ用)")
    parser.add_argument("--skip-llm", action="store_true",
                        help="LLM 呼び出しをスキップしレポートだけ再生成")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key and not args.skip_llm:
        logger.error("ANTHROPIC_API_KEY が見つかりません")
        return 2

    output_csv, report_md = build_paths(args.pair)
    logger.info("対象ペア: %s", args.pair)
    logger.info("出力 CSV: %s", output_csv)
    logger.info("レポート MD: %s", report_md)

    df = pd.read_csv(INPUT_CSV)
    signals = df[df["pair"] == args.pair].copy()
    if args.limit:
        signals = signals.head(args.limit)
    logger.info("対象シグナル: %s = %d 件 (model=%s, T=%.1f, workers=%d)",
                args.pair, len(signals), MODEL_ID, TEMPERATURE, args.workers)

    # リーク列の混入チェック
    leakage_hit = LEAKAGE_COLUMNS & set(signals.columns)
    logger.info("リーク列除外確認: %d 列 (プロンプトには渡らない設計)", len(leakage_hit))

    if args.skip_llm:
        if not output_csv.exists():
            logger.error("--skip-llm 指定だが %s なし", output_csv)
            return 3
        decisions = pd.read_csv(output_csv)
    else:
        client = Anthropic(api_key=api_key)
        decisions = run_parallel(
            signals, client, output_csv,
            workers=args.workers, flush_every=args.flush_every,
        )

    # 集計
    agg = aggregate_pf(signals, decisions)
    total_cost = decisions["api_cost_usd"].sum() if "api_cost_usd" in decisions else 0.0

    print("\n========== 集計結果 ==========")
    print(f"対象: {args.pair} n_signals={len(signals)} / 判定済={len(decisions)}")
    print(f"判定分布: {agg['distribution']}")
    for key in ["base", "confirm_only", "neutral_only", "confirm_neutral",
                "contradict_as_is", "contradict_inverted", "reject_as_is"]:
        d = agg[key]
        if d["n"] == 0:
            print(f"{key:18s}: n=0")
        else:
            pf = "inf" if d["PF"] == float("inf") else f"{d['PF']:.3f}"
            print(f"{key:18s}: n={d['n']}, PF={pf}, cum={d['cum_pips']:.1f} pips, win_rate={d['win_rate']:.1%}")
    print(f"API 実コスト: ${total_cost:.4f}")
    print("=============================\n")

    # レポート出力 (個別ペア)
    report_text = build_report(agg, decisions, total_cost, len(signals), pair=args.pair)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text(report_text, encoding="utf-8")
    logger.info("レポート保存: %s", report_md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
