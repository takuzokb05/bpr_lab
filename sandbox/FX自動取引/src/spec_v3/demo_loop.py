"""SPEC v3 — デモ運用メインループ

Proposal 3 (ペア別 confidence 閾値) を MT5 デモ口座で運用するループ。

## 構成
1. M15 ティック取得 (USD_JPY と GBP_JPY、両方を順次)
2. signal_v2.generate_signal でシグナル生成
3. LLMFilter.judge で CONFIRM/NEUTRAL/CONTRADICT/REJECT 判定
4. should_take_trade でペア別 confidence 閾値判定
5. MT5 デモ口座に発注 (lot 0.01)
6. SQLite (data/fx_spec_v3.db) に判定 + 発注 + 決済を全件記録
7. Slack 通知 (起動/シグナル/発注/決済/エラー/撤退)

## 各種制限 (SPEC_V3.md § 5)
- 1 ペア同時 1 ポジション
- 全体同時 2 ポジション
- 最大保持 24 時間
- 元本 1% を超える SL は発注拒否

## キルスイッチ
- LLM API 連続失敗 5 回 → 全ペア新規発注停止
- スプレッド 3 倍拡大 → 当該ペア新規発注ブロック (EMA baseline 比、SKIPPED 記録)
- 日次損失 -5% → 当日全停止 (DB 永続化、自動再起動でも継承)
- 月次損失 -10% → 月末まで停止 (DB 永続化)

## 撤退条件 (§ 4.5)
- 90 日 trades < 5
- 直近 100 trades の PF < 1.0
- 累計 -3,000 JPY
- LLM 月コスト > 5,000円
- 全ペアで上記成立 → SPEC v3 全停止

## 実行
```
python -m src.spec_v3.demo_loop --dry-run         # 接続テストのみ
python -m src.spec_v3.demo_loop --single-iter     # 1 イテレーションのみ
python -m src.spec_v3.demo_loop                   # 本番ループ (60 秒間隔)
```
"""
from __future__ import annotations

import argparse
import io
import logging
import os
import random
import signal as sig_module
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

# 文字化け対策 (タスクスケジューラ環境での stdout cp932 問題)
# テスト時は pytest の capture を壊さないよう、メインスクリプトとして実行された時のみ
def _wrap_stdout_utf8() -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", line_buffering=True,
        )
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", line_buffering=True,
        )

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# .env を読み込む
try:
    from dotenv import load_dotenv
    if (ROOT / ".env").exists():
        load_dotenv(ROOT / ".env")
except ImportError:
    pass

from src.spec_v2.signal_v2 import generate_signal  # noqa: E402  改変禁止モジュール
from src.spec_v3 import (  # noqa: E402
    ACCEPT_DECISIONS, CONFIDENCE_THRESHOLDS, ENABLED_PAIRS,
)
from src.spec_v3 import db as v3_db  # noqa: E402
from src.spec_v3.llm_filter import LLMFilter, should_take_trade  # noqa: E402
from src.spec_v3.risk_manager import (  # noqa: E402
    DEFAULT_PRINCIPAL_JPY, KillSwitchState, run_all_safety_checks,
)
from src.spec_v3.slack_notifier import SpecV3SlackNotifier  # noqa: E402


# ============================================================
# 設定
# ============================================================
DB_PATH = ROOT / "data" / "fx_spec_v3.db"
LOG_PATH = ROOT / "data" / "spec_v3_demo.log"

LOOP_INTERVAL_SEC = 60               # ループ間隔
MAX_HOLDING_MINUTES = 24 * 60        # 最大保持 24 時間
LOT_SIZE_UNITS_DEFAULT = 1_000       # 0.01 lot
MAX_TOTAL_POSITIONS = 2              # USD_JPY + GBP_JPY 同時 2 件まで

# シンボル別 pip サイズ (JPY クロス 0.01、それ以外 0.0001)
PIP_SIZES = {
    "USD_JPY": 0.01,
    "GBP_JPY": 0.01,
    "EUR_USD": 0.0001,
    "GBP_USD": 0.0001,
}

# データ取得本数 (M15 で 100 本 = 25 時間以上、ATR(14) + lookback(20) + 余裕)
M15_REQUIRED_BARS = 200


# ============================================================
# ログ
# ============================================================


def setup_logging() -> None:
    """ファイル + stdout の root logger を初期化"""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8", delay=False)
    stream_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[file_handler, stream_handler],
        force=True,
    )


def _flush_logs() -> None:
    for h in logging.getLogger().handlers:
        try:
            h.flush()
        except Exception:
            pass


logger = logging.getLogger("spec_v3_demo")


# ============================================================
# pipeline 1 行サマリログ (Ultra H-③ 是正、2026-05-28)
# SPEC v2 PR #26 で確立した "pipeline:" ログを SPEC v3 にも継承。
# `Select-String "pipeline:" data/spec_v3_demo.log` で各ステージの通過/却下が
# 時系列で grep 可能になる。memory `project_fx_pipeline_trace.md` 参照。
# ============================================================


def _emit_pipeline_log(
    pair: str,
    stage: str,
    *,
    reason: Optional[str] = None,
    signal_direction: Optional[str] = None,
    llm_label: Optional[str] = None,
    llm_confidence: Optional[float] = None,
    accepted: Optional[bool] = None,
    extra: Optional[dict] = None,
) -> None:
    """各ステージ通過 / 却下を 1 行 INFO ログとして出力する。

    出力例:
        pipeline: pair=USD_JPY stage=order_placed sig=long label=CONFIRM conf=0.72 accepted=True reason=accepted
    """
    parts: list[str] = [f"pair={pair}", f"stage={stage}"]
    if signal_direction is not None:
        parts.append(f"sig={signal_direction}")
    if llm_label is not None:
        parts.append(f"label={llm_label}")
    if llm_confidence is not None:
        try:
            parts.append(f"conf={float(llm_confidence):.2f}")
        except (TypeError, ValueError):
            parts.append(f"conf={llm_confidence}")
    if accepted is not None:
        parts.append(f"accepted={accepted}")
    if reason is not None:
        parts.append(f"reason={reason}")
    if extra:
        for k, v in extra.items():
            parts.append(f"{k}={v}")
    logger.info("pipeline: " + " ".join(parts))


# ============================================================
# Mt5 関連の薄いラッパ
# ============================================================


def _instantiate_mt5_client():
    """テストで mock しやすいよう関数化"""
    from src.mt5_client import Mt5Client
    return Mt5Client()


def fetch_m15(client, pair: str, bars: int = M15_REQUIRED_BARS) -> pd.DataFrame:
    """M15 OHLCV を取得 (シンプルな mt5_client ラッパ)"""
    return client.get_prices(pair, count=bars, granularity=pair_to_pricecount(bars))


def pair_to_pricecount(bars: int) -> str:
    # mt5_client は granularity 文字列を受け取るので別名のままだとちぐはぐ
    # 互換のため M15 固定で返す
    return "M15"


def _get_related_24h_changes(client, pair: str) -> dict:
    """関連通貨の 24h 変化率 (%) を取得。
    エラー時は空 dict を返し、コンテキストは null になる。
    """
    related = ["USD_JPY", "EUR_USD", "GBP_USD"]
    out: dict[str, float] = {}
    for sym in related:
        if sym == pair:
            # 自ペアは既に取得済みなので skip (LLM プロンプトでは「対象外」を含めない)
            continue
        try:
            # M15 96 本 = 24 時間
            df = client.get_prices(sym, count=97, granularity="M15")
            if len(df) >= 97:
                old = float(df["close"].iloc[0])
                new = float(df["close"].iloc[-1])
                if old > 0:
                    out[sym] = (new - old) / old * 100.0
        except Exception as e:  # noqa: BLE001
            logger.debug("related fetch fail %s: %s", sym, e)
    return out


# ============================================================
# トレード管理
# ============================================================


def _calc_pnl(pair: str, direction: str, entry: float, exit_price: float,
              lots: float) -> tuple[float, float]:
    """PnL を (pips, JPY) で返す。JPY クロスは 1 pip = 1000 JPY / lot, それ以外は省略"""
    pip = PIP_SIZES.get(pair, 0.0001)
    if direction == "long":
        diff = exit_price - entry
    else:
        diff = entry - exit_price
    pips = diff / pip
    # JPY クロスのみ簡易計算 (USD/EUR ペアは別途換算が必要だが SPEC v3 対象外)
    if pair.endswith("_JPY"):
        # 0.01 (1 pip) × 100,000 (1 lot) = 1000 JPY/pip
        pnl_jpy = pips * lots * 1000.0
    else:
        # USD ペアは厳密でないが概算
        pnl_jpy = pips * lots * 10.0
    return pips, pnl_jpy


def manage_open_trades(client, kill_switch: KillSwitchState) -> None:
    """オープン中ポジションの管理 (時間損切り / MT5 側 TP/SL ヒットの同期)"""
    open_trades = v3_db.get_open_trades(DB_PATH)
    if not open_trades:
        return

    try:
        mt5_positions = client.get_positions()
    except Exception as e:  # noqa: BLE001
        logger.error("MT5 positions 取得失敗: %s", e)
        return

    mt5_ticket_map = {int(p["trade_id"]): p for p in mt5_positions}
    now_utc = datetime.now(timezone.utc)

    for trade in open_trades:
        ticket = trade["mt5_ticket"]
        pair = trade["pair"]
        if ticket is None:
            continue

        # 既に MT5 側で決済された (TP / SL ヒット)
        if int(ticket) not in mt5_ticket_map:
            logger.info("ticket %s は既に MT5 で決済済み、DB を同期", ticket)
            _record_closure_from_history(client, trade, reason="tp_or_sl")
            continue

        # 時間損切り
        entry_dt = _parse_iso_utc(trade["entry_at_utc"])
        holding_min = int((now_utc - entry_dt).total_seconds() / 60)
        if holding_min >= MAX_HOLDING_MINUTES:
            logger.info("trade %d 時間損切り (保持 %d 分)", trade["id"], holding_min)
            _close_and_record(client, trade, reason="time_limit",
                              holding_minutes=holding_min)
            continue


def _parse_iso_utc(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _close_and_record(client, trade, reason: str, holding_minutes: int,
                      notifier: Optional[SpecV3SlackNotifier] = None) -> None:
    ticket = int(trade["mt5_ticket"])
    pair = trade["pair"]
    direction = trade["direction"]
    entry = float(trade["entry_price"])
    lots = float(trade["lots"])
    try:
        result = client.close_position(str(ticket))
        # Mt5Client.close_position は "close_price" を返す (market_order は "price")。
        # Ultra H-① 是正 (2026-05-28): キー誤読で exit_price=entry → PnL=0 になり
        # 24h 時間損切りの Phase 2'A PF 計測が歪む致命バグだった。
        # `close_price` を最優先、後方互換として "price" もフォールバック、最終的に entry。
        raw_price = result.get("close_price")
        if raw_price is None:
            raw_price = result.get("price")
        try:
            exit_price = float(raw_price) if raw_price is not None else 0.0
        except (TypeError, ValueError):
            exit_price = 0.0
        if exit_price <= 0:
            exit_price = entry
    except Exception as e:  # noqa: BLE001
        logger.error("close_position 失敗 ticket=%d: %s", ticket, e)
        exit_price = entry

    pips, pnl_jpy = _calc_pnl(pair, direction, entry, exit_price, lots)
    v3_db.insert_trade_closure(
        DB_PATH, trade_id=trade["id"],
        exit_at_utc=v3_db.utc_now_iso(),
        exit_price=exit_price, exit_reason=reason,
        pnl_pips=pips, pnl_jpy=pnl_jpy,
        holding_minutes=holding_minutes,
    )
    logger.info(
        "CLOSE pair=%s dir=%s reason=%s entry=%.5f exit=%.5f PnL=%+.1fp (%+.0f JPY) hold=%dm",
        pair, direction, reason, entry, exit_price, pips, pnl_jpy, holding_minutes,
    )
    if notifier:
        notifier.trade_closed(pair, direction, pips, pnl_jpy, reason, holding_minutes)


def _sync_closed_positions_to_db(close_result: dict, reason: str) -> None:
    """close_all_positions の結果を DB の trades.status に反映する。

    Ultra H-⑤ 是正 (2026-05-28): SPEC v3 撤退条件 #5 発火時に
    `client.close_all_positions()` を呼ぶが、それだけでは DB の
    `trades.status='open'` 行が残置されたままになり、次回起動時の
    集計や `manage_open_trades` が `_record_closure_from_history`
    経由で現在価格を使った近似 PnL を計算してしまう。

    本関数は close_result["closed"] (= Mt5Client.close_position の戻り値リスト) を
    iterate し、各 ticket に対応する DB trade を確定 (trade_closures 行を INSERT
    かつ trades.status='closed' に UPDATE) する。
    close_result["failed"] (= 決済失敗した trade_id リスト) は status='close_failed'
    として記録するため、運用後の集計で「閉じられなかったポジション」を識別できる。

    Args:
        close_result: Mt5Client.close_all_positions() の戻り値
            ({"closed": [{"trade_id", "realized_pl", "close_price", ...}, ...],
              "failed": [trade_id_str, ...], "total": int})
        reason: 決済理由 (例: "retreat_close_retreat_5_all_pairs")
    """
    closed_list = close_result.get("closed") or []
    failed_list = close_result.get("failed") or []

    # 成功した決済: trade_closures に INSERT + trades.status='closed' へ
    for cd in closed_list:
        try:
            ticket = int(cd.get("trade_id") or 0)
        except (TypeError, ValueError):
            continue
        if ticket <= 0:
            continue
        try:
            trade_row = _find_db_trade_by_ticket(ticket)
            if trade_row is None:
                logger.warning(
                    "sync_closed: ticket=%d に対応する DB trade が見つからない", ticket,
                )
                continue
            # 既に closed なら skip
            if trade_row["status"] == "closed":
                continue
            entry = float(trade_row["entry_price"])
            lots = float(trade_row["lots"])
            direction = trade_row["direction"]
            pair = trade_row["pair"]
            # close_price を最優先、フォールバックで realized_pl から逆算は省略
            raw_price = cd.get("close_price")
            if raw_price is None:
                raw_price = cd.get("price")
            try:
                exit_price = float(raw_price) if raw_price is not None else 0.0
            except (TypeError, ValueError):
                exit_price = 0.0
            if exit_price <= 0:
                exit_price = entry
            pips, pnl_jpy = _calc_pnl(pair, direction, entry, exit_price, lots)
            entry_dt = _parse_iso_utc(trade_row["entry_at_utc"])
            holding_min = int(
                (datetime.now(timezone.utc) - entry_dt).total_seconds() / 60
            )
            v3_db.insert_trade_closure(
                DB_PATH, trade_id=int(trade_row["id"]),
                exit_at_utc=v3_db.utc_now_iso(),
                exit_price=exit_price, exit_reason=reason,
                pnl_pips=pips, pnl_jpy=pnl_jpy,
                holding_minutes=holding_min,
            )
            logger.info(
                "sync_closed: trade_id=%d ticket=%d pair=%s exit=%.5f pnl=%+.0f",
                int(trade_row["id"]), ticket, pair, exit_price, pnl_jpy,
            )
        except Exception as e:  # noqa: BLE001
            logger.error("sync_closed 個別エラー ticket=%d: %s", ticket, e)

    # 失敗した決済: trades.status='close_failed' に更新するだけ (近似 PnL 入れない)
    for fid in failed_list:
        try:
            ticket = int(fid)
        except (TypeError, ValueError):
            continue
        if ticket <= 0:
            continue
        try:
            _mark_trade_status_failed(ticket, reason)
        except Exception as e:  # noqa: BLE001
            logger.error("close_failed status 更新エラー ticket=%d: %s", ticket, e)


def _find_db_trade_by_ticket(ticket: int):
    """trades テーブルから mt5_ticket でマッチする行を返す (1 行 or None)。"""
    if not DB_PATH.exists():
        return None
    with v3_db.get_conn(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT * FROM trades WHERE mt5_ticket=? ORDER BY id DESC LIMIT 1",
            (ticket,),
        )
        return cur.fetchone()


def _mark_trade_status_failed(ticket: int, reason: str) -> None:
    """trades.status='close_failed' に更新 (PnL 記録なし)。"""
    if not DB_PATH.exists():
        return
    with v3_db.get_conn(DB_PATH) as conn:
        conn.execute(
            "UPDATE trades SET status='close_failed' "
            "WHERE mt5_ticket=? AND status='open'",
            (ticket,),
        )
    logger.warning("close_failed status マーク: ticket=%d reason=%s", ticket, reason)


def _record_closure_from_history(client, trade, reason: str) -> None:
    """MT5 側で TP/SL がヒット済みのケースを DB に同期 (現在価格で近似)"""
    pair = trade["pair"]
    direction = trade["direction"]
    entry = float(trade["entry_price"])
    lots = float(trade["lots"])
    try:
        df = client.get_prices(pair, count=1, granularity="M1")
        exit_price = float(df["close"].iloc[-1]) if len(df) else entry
    except Exception:
        exit_price = entry
    pips, pnl_jpy = _calc_pnl(pair, direction, entry, exit_price, lots)
    entry_dt = _parse_iso_utc(trade["entry_at_utc"])
    holding_min = int((datetime.now(timezone.utc) - entry_dt).total_seconds() / 60)
    v3_db.insert_trade_closure(
        DB_PATH, trade_id=trade["id"],
        exit_at_utc=v3_db.utc_now_iso(),
        exit_price=exit_price, exit_reason=reason,
        pnl_pips=pips, pnl_jpy=pnl_jpy,
        holding_minutes=holding_min,
    )


# ============================================================
# シグナル評価 + 発注 (1 ペア分)
# ============================================================


def process_pair(
    client,
    pair: str,
    *,
    filter_obj: Optional[LLMFilter],
    notifier: SpecV3SlackNotifier,
    kill_switch: KillSwitchState,
    dry_run: bool,
    lot_units: int,
) -> dict:
    """ペア 1 件分のシグナル生成 → LLM 判定 → 発注判断。
    戻り値は記録用 dict (テスト/ログ向け)。
    """
    summary: dict = {"pair": pair, "stage": "start"}

    # 1. データ取得
    try:
        m15_df = fetch_m15(client, pair)
    except Exception as e:  # noqa: BLE001
        logger.error("M15 取得失敗 %s: %s", pair, e)
        summary["stage"] = "fetch_fail"
        summary["error"] = str(e)
        _emit_pipeline_log(pair, "fetch_fail", reason=str(e))
        return summary
    if len(m15_df) < 50:
        logger.warning("M15 データ不足 %s n=%d", pair, len(m15_df))
        summary["stage"] = "insufficient_data"
        _emit_pipeline_log(pair, "insufficient_data",
                           reason=f"n={len(m15_df)}")
        return summary

    # 2. signal_v2 シグナル生成
    sig = generate_signal(m15_df)
    summary["signal_direction"] = sig.direction
    if sig.direction == "no_signal":
        summary["stage"] = "no_signal"
        _emit_pipeline_log(pair, "no_signal", signal_direction=sig.direction)
        return summary

    # 3a. スプレッド異常キルスイッチ (Ultra/Karen バグ② 是正、2026-05-27)
    # SPEC v3 § 5.2 キルスイッチ #3 を実装層に配線。
    # baseline を EMA で追従しつつ、3 倍超で発注ブロック (LLM 呼び出し前)。
    current_spread = client.get_spread(pair) if hasattr(client, "get_spread") else None
    if current_spread is not None:
        kill_switch.update_spread(pair, current_spread)
        if kill_switch.check_spread_anomaly(pair, current_spread):
            baseline = kill_switch.spread_baseline.get(pair)
            reason_msg = (
                f"spread_anomaly:current={current_spread:.2f}pips,"
                f"baseline={baseline:.2f}pips,multiplier>=3.0"
            )
            logger.warning(
                "pair=%s スプレッド異常検知 (current=%.2f, baseline=%.2f) → "
                "発注ブロック、SKIPPED 記録のみ",
                pair, current_spread, baseline or 0.0,
            )
            v3_db.insert_llm_judgment(
                DB_PATH,
                judged_at_utc=v3_db.utc_now_iso(), pair=pair,
                signal_direction=sig.direction, entry_price=sig.entry_price,
                sl_price=sig.sl_price, tp_price=sig.tp_price,
                sl_pips=sig.sl_pips, tp_pips=sig.tp_pips,
                atr=None, signal_reason=sig.reason,
                llm_label="SKIPPED", llm_confidence=None,
                llm_reasoning=reason_msg,
                accepted=False, decision_reason="spread_anomaly",
                api_input_tokens=None, api_output_tokens=None,
                api_cost_usd=None, api_error=None, context=None,
            )
            v3_db.insert_loop_health(DB_PATH, "kill_switch", reason_msg, pair=pair)
            try:
                notifier.kill_switch(
                    f"[{pair}] スプレッド異常 {current_spread:.2f}pips "
                    f"(baseline {baseline or 0:.2f}pips×3 超)",
                    False,
                )
            except Exception:  # noqa: BLE001
                pass
            summary["stage"] = "spread_anomaly_blocked"
            summary["spread_pips"] = current_spread
            _emit_pipeline_log(
                pair, "spread_anomaly_blocked",
                signal_direction=sig.direction,
                reason=f"spread={current_spread:.2f}>=baseline*3",
                extra={"baseline": f"{baseline or 0:.2f}"},
            )
            return summary

    # 3. キルスイッチチェック (LLM 呼び出し前)
    blocked, reason = kill_switch.is_blocked(pair)
    if blocked:
        logger.info("pair=%s blocked: %s, シグナルは記録のみ", pair, reason)
        v3_db.insert_llm_judgment(
            DB_PATH,
            judged_at_utc=v3_db.utc_now_iso(), pair=pair,
            signal_direction=sig.direction, entry_price=sig.entry_price,
            sl_price=sig.sl_price, tp_price=sig.tp_price,
            sl_pips=sig.sl_pips, tp_pips=sig.tp_pips,
            atr=None, signal_reason=sig.reason,
            llm_label="SKIPPED", llm_confidence=None,
            llm_reasoning=f"killswitch:{reason}",
            accepted=False, decision_reason="killswitch_blocked",
            api_input_tokens=None, api_output_tokens=None,
            api_cost_usd=None, api_error=None, context=None,
        )
        summary["stage"] = "killswitch_blocked"
        summary["reason"] = reason
        _emit_pipeline_log(pair, "killswitch_blocked",
                           signal_direction=sig.direction, reason=reason)
        return summary

    # 4. 既存ポジション (1 ペア 1 件、全体 2 件)
    open_pair = v3_db.get_open_trades(DB_PATH, pair=pair)
    if open_pair:
        logger.debug("pair=%s 既存 open あり、新規スキップ", pair)
        summary["stage"] = "position_already_open"
        _emit_pipeline_log(pair, "position_already_open",
                           signal_direction=sig.direction,
                           reason="pair has open")
        return summary
    open_total = v3_db.get_open_trades(DB_PATH)
    if len(open_total) >= MAX_TOTAL_POSITIONS:
        logger.debug("全体 open=%d 件、新規スキップ", len(open_total))
        summary["stage"] = "max_total_positions"
        _emit_pipeline_log(pair, "max_total_positions",
                           signal_direction=sig.direction,
                           reason=f"open_total={len(open_total)}>={MAX_TOTAL_POSITIONS}")
        return summary

    # 5. LLM 判定
    if filter_obj is None:
        # dry-run: LLM をスキップ、結果は記録だけ
        v3_db.insert_llm_judgment(
            DB_PATH,
            judged_at_utc=v3_db.utc_now_iso(), pair=pair,
            signal_direction=sig.direction, entry_price=sig.entry_price,
            sl_price=sig.sl_price, tp_price=sig.tp_price,
            sl_pips=sig.sl_pips, tp_pips=sig.tp_pips,
            atr=None, signal_reason=sig.reason,
            llm_label="DRY_RUN", llm_confidence=None,
            llm_reasoning="dry_run_skip",
            accepted=False, decision_reason="dry_run",
            api_input_tokens=None, api_output_tokens=None,
            api_cost_usd=None, api_error=None, context=None,
        )
        summary["stage"] = "dry_run"
        _emit_pipeline_log(pair, "dry_run", signal_direction=sig.direction,
                           reason="filter_obj=None")
        return summary

    from src.spec_v3.llm_filter import build_context, calc_atr
    related = _get_related_24h_changes(client, pair)
    # ATR 計算 (Ultra/Karen バグ⑥ 是正、2026-05-27)
    # signal_v2 は改変禁止のため、llm_filter.calc_atr を別途複製して呼ぶ。
    # Phase 0' BT の `_cycle2_extract_signals.py` で LLM プロンプトに渡していた
    # ATR 値を Phase 2'A でも同等に渡し、confidence 校正の前提を揃える。
    atr_value = calc_atr(m15_df)
    context = build_context(
        pair=pair,
        signal={
            "direction": sig.direction,
            "entry_price": sig.entry_price,
            "sl_price": sig.sl_price,
            "tp_price": sig.tp_price,
            "sl_pips": sig.sl_pips,
            "tp_pips": sig.tp_pips,
            "atr": atr_value,
        },
        m15_df=m15_df,
        related_24h_changes=related,
        timestamp_utc=v3_db.utc_now_iso(),
    )
    decision = filter_obj.judge(context)

    # LLM 結果 → キルスイッチ更新
    if decision.is_error:
        if kill_switch.on_llm_failure():
            notifier.kill_switch(
                f"LLM API 連続失敗 {kill_switch.llm_consecutive_failures} 回", True,
            )
    else:
        kill_switch.on_llm_success()

    # 6. 採用判定
    accepted, decision_reason = should_take_trade(
        pair=pair,
        decision=decision,
        confidence_thresholds=CONFIDENCE_THRESHOLDS,
        accept_labels=ACCEPT_DECISIONS,
    )

    # 7. DB 記録 (採用/見送り問わず全件)
    judgment_id = v3_db.insert_llm_judgment(
        DB_PATH,
        judged_at_utc=v3_db.utc_now_iso(), pair=pair,
        signal_direction=sig.direction, entry_price=sig.entry_price,
        sl_price=sig.sl_price, tp_price=sig.tp_price,
        sl_pips=sig.sl_pips, tp_pips=sig.tp_pips,
        atr=atr_value, signal_reason=sig.reason,
        llm_label=decision.label, llm_confidence=decision.confidence,
        llm_reasoning=decision.reasoning,
        accepted=accepted, decision_reason=decision_reason,
        api_input_tokens=decision.input_tokens,
        api_output_tokens=decision.output_tokens,
        api_cost_usd=decision.cost_usd,
        api_error=decision.error,
        context=context,
    )
    summary["judgment_id"] = judgment_id
    summary["llm_label"] = decision.label
    summary["llm_confidence"] = decision.confidence
    summary["accepted"] = accepted
    summary["decision_reason"] = decision_reason

    threshold = CONFIDENCE_THRESHOLDS.get(pair, 1.0)
    if not accepted:
        logger.info(
            "見送り pair=%s dir=%s label=%s conf=%.2f reason=%s",
            pair, sig.direction, decision.label, decision.confidence, decision_reason,
        )
        notifier.signal_rejected(
            pair, sig.direction, decision.label, decision.confidence,
            threshold, decision_reason,
        )
        summary["stage"] = "rejected"
        _emit_pipeline_log(
            pair, "rejected",
            signal_direction=sig.direction,
            llm_label=decision.label,
            llm_confidence=decision.confidence,
            accepted=False,
            reason=decision_reason,
        )
        return summary

    # 8. 発注 (dry_run なら skip)
    if dry_run:
        logger.info("dry_run なので発注スキップ pair=%s", pair)
        summary["stage"] = "accepted_dry_run"
        _emit_pipeline_log(
            pair, "accepted_dry_run",
            signal_direction=sig.direction,
            llm_label=decision.label,
            llm_confidence=decision.confidence,
            accepted=True,
            reason="dry_run",
        )
        return summary

    units = lot_units if sig.direction == "long" else -lot_units
    try:
        result = client.market_order(
            instrument=pair, units=units,
            stop_loss=sig.sl_price or 0.0,
            take_profit=sig.tp_price or 0.0,
        )
    except Exception as e:  # noqa: BLE001
        logger.error("market_order 失敗 pair=%s: %s", pair, e)
        notifier.raw(f":x: 発注失敗 {pair}: {e}")
        summary["stage"] = "order_failed"
        summary["error"] = str(e)
        _emit_pipeline_log(
            pair, "order_failed",
            signal_direction=sig.direction,
            llm_label=decision.label,
            llm_confidence=decision.confidence,
            accepted=True,
            reason=f"market_order_exc:{e}",
        )
        return summary

    ticket = int(result.get("order_id") or 0) or None
    fill_price = float(result.get("price", sig.entry_price))
    trade_id = v3_db.insert_trade(
        DB_PATH,
        mt5_ticket=ticket,
        entry_at_utc=v3_db.utc_now_iso(),
        pair=pair, direction=sig.direction,
        lots=lot_units / 100_000,
        entry_price=fill_price,
        sl_price=sig.sl_price, tp_price=sig.tp_price,
        sl_pips=sig.sl_pips, tp_pips=sig.tp_pips,
        judgment_id=judgment_id,
        signal_reason=sig.reason,
        llm_label=decision.label,
        llm_confidence=decision.confidence,
        is_demo=True,
    )
    logger.info(
        "ENTRY pair=%s dir=%s ticket=%s entry=%.5f SL=%.5f TP=%.5f conf=%.2f trade_id=%d",
        pair, sig.direction, ticket, fill_price, sig.sl_price or 0,
        sig.tp_price or 0, decision.confidence, trade_id,
    )
    notifier.trade_entered(
        pair, sig.direction, ticket or 0, fill_price,
        sig.sl_price or 0.0, sig.tp_price or 0.0,
        lot_units / 100_000, decision.confidence,
    )
    summary["stage"] = "entered"
    summary["trade_id"] = trade_id
    summary["ticket"] = ticket
    _emit_pipeline_log(
        pair, "order_placed",
        signal_direction=sig.direction,
        llm_label=decision.label,
        llm_confidence=decision.confidence,
        accepted=True,
        reason=decision_reason,
        extra={"ticket": ticket or 0, "trade_id": trade_id,
               "entry": f"{fill_price:.5f}"},
    )
    return summary


# ============================================================
# キルスイッチ状態の永続化 (Ultra/Karen バグ⑤ 是正)
# ============================================================


def _persist_killswitch_state(kill_switch: KillSwitchState) -> None:
    """KillSwitchState の永続化フィールドを DB に保存。失敗は致命でないので debug ログのみ。"""
    try:
        v3_db.save_killswitch_state(
            DB_PATH,
            daily_block_until=kill_switch.daily_block_until,
            monthly_block_until=kill_switch.monthly_block_until,
            blocked_pairs=kill_switch.blocked_pairs,
            global_block_reason=kill_switch.global_block_reason,
            spread_baseline=kill_switch.spread_baseline,
        )
    except Exception as e:  # noqa: BLE001
        logger.debug("kill_switch state 保存失敗 (許容): %s", e)


def _restore_killswitch_state(kill_switch: KillSwitchState) -> None:
    """DB から KillSwitchState を復元 (起動時に呼ぶ)。"""
    try:
        state = v3_db.load_killswitch_state(DB_PATH)
    except Exception as e:  # noqa: BLE001
        logger.warning("kill_switch state 復元失敗 (許容、初期状態で起動): %s", e)
        return

    # 日次停止: 当日のものだけ復元 (古い日付ならクリア)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily = state.get("daily_block_until")
    if daily is not None and daily >= today:
        kill_switch.daily_block_until = daily
        logger.warning(
            "[復元] 日次停止状態 daily_block_until=%s (今日 %s) を継承", daily, today,
        )

    # 月次停止: 当月のものだけ復元
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")
    monthly = state.get("monthly_block_until")
    if monthly is not None and monthly >= this_month:
        kill_switch.monthly_block_until = monthly
        logger.warning(
            "[復元] 月次停止状態 monthly_block_until=%s (当月 %s) を継承",
            monthly, this_month,
        )

    blocked = state.get("blocked_pairs") or set()
    if blocked:
        kill_switch.blocked_pairs.update(blocked)
        logger.info("[復元] ペア別ブロック復元: %s", sorted(blocked))

    gbr = state.get("global_block_reason")
    if gbr:
        kill_switch.global_block_reason = gbr
        logger.warning("[復元] グローバルブロック復元: %s", gbr)

    baseline = state.get("spread_baseline") or {}
    if baseline:
        kill_switch.spread_baseline.update(baseline)
        logger.info("[復元] スプレッドベースライン復元: %s", baseline)


# ============================================================
# 安全チェック (毎ループ実行)
# ============================================================


def evaluate_safety(
    kill_switch: KillSwitchState,
    notifier: SpecV3SlackNotifier,
    principal_jpy: float,
) -> str:
    """損失上限 + 撤退条件をチェック。返り値は action 文字列。"""
    safety = run_all_safety_checks(
        DB_PATH, ENABLED_PAIRS, kill_switch, principal_jpy=principal_jpy,
    )
    action = safety["action"]

    if action == "warn":
        notifier.daily_loss_warn(safety["daily"]["pct_of_principal"], "warn")
    elif action == "half_size":
        notifier.daily_loss_warn(safety["daily"]["pct_of_principal"], "half")
    elif action == "daily_stop":
        notifier.kill_switch("日次損失 -5% 超過、当日全停止", True)
        v3_db.insert_loop_health(DB_PATH, "kill_switch", "daily_loss_stop")
        # 日次停止状態を DB に永続化 (Ultra/Karen バグ⑤ 是正、2026-05-27)
        # 自動再起動 (RestartCount=5) でも日次停止が解けないように
        _persist_killswitch_state(kill_switch)
    elif action == "monthly_stop":
        notifier.kill_switch("月次損失 -10% 超過、月末まで停止", True)
        v3_db.insert_loop_health(DB_PATH, "kill_switch", "monthly_loss_stop")
        # 月次停止状態を DB に永続化
        today_ym = datetime.now(timezone.utc).strftime("%Y-%m")
        kill_switch.monthly_block_until = today_ym
        _persist_killswitch_state(kill_switch)
    elif action.startswith("retreat_"):
        # 撤退条件発火 → DB 記録 + Slack 通知
        # どれが発火したか抽出
        msgs = []
        for st in safety["per_pair_retreat"].values():
            if st.triggered:
                msgs.append(f"[{st.pair}] {st.message}")
        if safety["llm_cost_retreat"].triggered:
            msgs.append(safety["llm_cost_retreat"].message)
        if safety["system_retreat"].triggered:
            msgs.append(safety["system_retreat"].message)
        notifier.retreat_triggered(action, "; ".join(msgs))
        v3_db.insert_loop_health(DB_PATH, "retreat", "; ".join(msgs))

    return action


# ============================================================
# メインループ
# ============================================================
_stop_requested = False


def _signal_handler(sig, frame):
    global _stop_requested
    logger.info("signal %s 受信、ループ停止予定", sig)
    _stop_requested = True


def _ordered_pairs_for_iteration(
    enabled_pairs: tuple[str, ...],
    iter_count: int,
    shuffle_pairs: bool,
) -> list[str]:
    """ペア評価順を返す (Ultra H-④ 是正、2026-05-28)。

    - shuffle_pairs=True (本番デフォルト): イテレーションごとにランダムシャッフル
      固定順 (USD_JPY → GBP_JPY) で max_total_positions=2 を埋めて
      GBP_JPY が枯渇するリスクを抑える
    - shuffle_pairs=False: 元の順序を維持 (テスト・再現性確保用)

    iter_count を seed に使う Random インスタンス経由でシャッフルし、
    iteration ごとに決定論的に異なる順序を出す。
    """
    pairs = list(enabled_pairs)
    if not shuffle_pairs or len(pairs) <= 1:
        return pairs
    # 毎ループで異なる順序にするが、iter_count を seed にして決定論性を保つ
    rng = random.Random(iter_count)
    rng.shuffle(pairs)
    return pairs


def run_loop(
    *,
    dry_run: bool = False,
    single_iter: bool = False,
    enabled_pairs: tuple[str, ...] = ENABLED_PAIRS,
    lot_units: int = LOT_SIZE_UNITS_DEFAULT,
    principal_jpy: float = DEFAULT_PRINCIPAL_JPY,
    interval_sec: int = LOOP_INTERVAL_SEC,
    mt5_client=None,
    llm_filter=None,
    notifier=None,
    shuffle_pairs: bool = True,
) -> None:
    """メインループ。`mt5_client` / `llm_filter` / `notifier` をテストで mock 可。"""
    setup_logging()
    v3_db.init_db(DB_PATH)
    v3_db.insert_loop_health(DB_PATH, "start", f"dry_run={dry_run}")

    logger.info("=" * 80)
    logger.info("SPEC v3 デモループ開始")
    logger.info("  pairs=%s lot=%d dry_run=%s single_iter=%s",
                enabled_pairs, lot_units, dry_run, single_iter)
    logger.info("  DB: %s", DB_PATH)
    logger.info("  confidence_thresholds=%s", CONFIDENCE_THRESHOLDS)
    logger.info("  accept_decisions=%s", ACCEPT_DECISIONS)
    logger.info("=" * 80)

    # シグナルハンドラ (Ctrl+C / SIGTERM で gracefully 停止)
    try:
        sig_module.signal(sig_module.SIGINT, _signal_handler)
        sig_module.signal(sig_module.SIGTERM, _signal_handler)
    except (ValueError, AttributeError):
        # Windows のメインスレッドでない場合は無視
        pass

    notifier = notifier or SpecV3SlackNotifier()
    notifier.bot_started(
        f"pairs={list(enabled_pairs)} lot={lot_units} dry_run={dry_run}"
    )

    # MT5 接続
    if mt5_client is None:
        try:
            mt5_client = _instantiate_mt5_client()
        except Exception as e:  # noqa: BLE001
            logger.error("MT5 接続失敗: %s", e)
            notifier.raw(f":x: MT5 接続失敗: {e}")
            v3_db.insert_loop_health(DB_PATH, "error", f"mt5_init: {e}")
            return

    # LLM Filter
    if llm_filter is None and not dry_run:
        try:
            llm_filter = LLMFilter()
        except Exception as e:  # noqa: BLE001
            logger.error("LLMFilter 初期化失敗: %s", e)
            notifier.raw(f":x: LLM Filter 初期化失敗: {e}")
            v3_db.insert_loop_health(DB_PATH, "error", f"llm_init: {e}")
            return

    kill_switch = KillSwitchState()
    # キルスイッチ状態を DB から復元 (Ultra/Karen バグ⑤ 是正、2026-05-27)
    # VPS タスクスケジューラ自動再起動で日次停止が解けないように
    _restore_killswitch_state(kill_switch)
    iter_count = 0

    try:
        while not _stop_requested:
            iter_count += 1
            try:
                # 安全チェック (撤退/損失上限)
                action = evaluate_safety(kill_switch, notifier, principal_jpy)
                if action.startswith("retreat_") or action in ("daily_stop", "monthly_stop"):
                    logger.error("ループ停止要件発火: %s", action)
                    _stop = True
                    if action == "daily_stop":
                        # 当日のみ停止 → 翌日まで sleep して継続
                        _stop = False
                    if _stop:
                        # 撤退/月次停止時は MT5 のオープンポジションを全クローズ
                        # (Ultra/Karen バグ③ 是正、2026-05-27)
                        # SPEC v3 撤退条件 #5 発火後にポジションが放置される問題への対処。
                        # daily_stop は当日のみ停止 (継続) なのでクローズしない。
                        if action.startswith("retreat_") or action == "monthly_stop":
                            try:
                                close_result = mt5_client.close_all_positions(
                                    reason=f"spec_v3_{action}",
                                )
                                logger.warning(
                                    "[撤退時クローズ] reason=%s closed=%d failed=%d total=%d",
                                    action, len(close_result.get("closed", [])),
                                    len(close_result.get("failed", [])),
                                    close_result.get("total", 0),
                                )
                                # DB status を MT5 実態と同期 (Ultra H-⑤ 是正、2026-05-28)
                                # close_all_positions だけでは trades.status='open' が残り、
                                # 次回起動時に manage_open_trades が現在価格で
                                # 近似 PnL を計算してしまう
                                try:
                                    _sync_closed_positions_to_db(
                                        close_result, reason=f"retreat_close_{action}",
                                    )
                                except Exception as sync_err:  # noqa: BLE001
                                    logger.error(
                                        "撤退クローズ後の DB 同期失敗: %s", sync_err,
                                    )
                                v3_db.insert_loop_health(
                                    DB_PATH, "retreat_close",
                                    f"action={action} closed={len(close_result.get('closed', []))} "
                                    f"failed={len(close_result.get('failed', []))} "
                                    f"total={close_result.get('total', 0)}",
                                )
                                # 撤退時クローズの通知
                                try:
                                    notifier.raw(
                                        f":octagonal_sign: 撤退に伴う一括決済 "
                                        f"action={action} "
                                        f"closed={len(close_result.get('closed', []))}/"
                                        f"{close_result.get('total', 0)} "
                                        f"failed={len(close_result.get('failed', []))}"
                                    )
                                except Exception:  # noqa: BLE001
                                    pass
                            except Exception as e:  # noqa: BLE001
                                logger.error(
                                    "撤退時 close_all_positions 失敗: %s "
                                    "(MT5 にポジションが残置されている可能性あり)", e,
                                )
                                v3_db.insert_loop_health(
                                    DB_PATH, "error",
                                    f"retreat_close_failed: {e}",
                                )
                        v3_db.insert_loop_health(DB_PATH, "stop", action)
                        break

                # オープン中ポジション管理
                try:
                    manage_open_trades(mt5_client, kill_switch)
                except Exception as e:  # noqa: BLE001
                    logger.error("manage_open_trades 失敗: %s", e)

                # 各ペアごとに評価 (Ultra H-④ 是正: ペア評価順をランダム化)
                iter_pairs = _ordered_pairs_for_iteration(
                    enabled_pairs, iter_count, shuffle_pairs,
                )
                for pair in iter_pairs:
                    try:
                        process_pair(
                            mt5_client, pair,
                            filter_obj=llm_filter if not dry_run else None,
                            notifier=notifier,
                            kill_switch=kill_switch,
                            dry_run=dry_run,
                            lot_units=lot_units,
                        )
                    except Exception as e:  # noqa: BLE001
                        tb = traceback.format_exc()
                        logger.error("process_pair 失敗 %s: %s\n%s", pair, e, tb)
                        v3_db.insert_loop_health(DB_PATH, "error",
                                                 f"process_pair {pair}: {e}",
                                                 pair=pair)

                # heartbeat 1 時間に 1 回 (60 iter × 60s = 1h)
                if iter_count % 60 == 0:
                    v3_db.insert_loop_health(
                        DB_PATH, "heartbeat", f"iter={iter_count}",
                    )

            except Exception as e:  # noqa: BLE001
                tb = traceback.format_exc()
                logger.error("ループ予期せぬエラー: %s\n%s", e, tb)
                v3_db.insert_loop_health(DB_PATH, "error", str(e))
                notifier.raw(f":x: ループエラー: {e}")

            _flush_logs()

            if single_iter:
                break

            for _ in range(interval_sec):
                if _stop_requested:
                    break
                time.sleep(1)
    finally:
        v3_db.insert_loop_health(DB_PATH, "stop", f"iter_count={iter_count}")
        notifier.bot_stopped(f"iter_count={iter_count}")
        logger.info("ループ停止 (iter_count=%d)", iter_count)


# ============================================================
# CLI
# ============================================================


def main() -> int:
    parser = argparse.ArgumentParser(description="SPEC v3 デモループ")
    parser.add_argument("--dry-run", action="store_true",
                        help="LLM 呼び出しと発注をスキップ、シグナル/接続テストのみ")
    parser.add_argument("--single-iter", action="store_true",
                        help="1 イテレーションだけ実行して終了 (テスト用)")
    parser.add_argument("--lot-units", type=int, default=LOT_SIZE_UNITS_DEFAULT,
                        help="取引数量 (units, 1000=0.01 lot)")
    parser.add_argument("--interval", type=int, default=LOOP_INTERVAL_SEC,
                        help="ループ間隔 (秒)")
    parser.add_argument("--principal-jpy", type=float, default=DEFAULT_PRINCIPAL_JPY,
                        help="元本 (JPY) - 損失上限の計算に使う")
    parser.add_argument("--no-shuffle-pairs", action="store_true",
                        help="ペア評価順をシャッフルせず ENABLED_PAIRS 順固定 "
                             "(テスト/再現性確認用)")
    args = parser.parse_args()

    # CLI として実行された時のみ stdout を UTF-8 にラップ (pytest 環境を壊さない)
    _wrap_stdout_utf8()

    run_loop(
        dry_run=args.dry_run,
        single_iter=args.single_iter,
        lot_units=args.lot_units,
        principal_jpy=args.principal_jpy,
        interval_sec=args.interval,
        shuffle_pairs=not args.no_shuffle_pairs,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
