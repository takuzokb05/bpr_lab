"""SPEC v2 PoC メインループ

GBP_JPY デモ口座で 60 秒間隔ループ:
1. M15 + H1 データ取得 (data_fetcher)
2. SeasonalDetector で季節判定
3. オープン中トレードの管理 (時間損切り / レジーム変化決済)
4. VOLATILE 時のみ新規エントリー判断 (signal_v2)
5. 1 ポジション制限、最小ロット 0.01 固定
6. DB に判定 + 発注 + 決済を記録
7. Slack 通知 (起動/エントリー/決済/エラー)

## 設計原則
- 既存 trading_loop.py は使わない (ゼロから書く、レビュワー全員一致)
- mt5_client は流用 (I/O 層、哲学中立)
- conviction_scorer / ai_advisor / bear_researcher は持ち込まない
- risk_manager の安全装置は最低限のみ参照、PoC は固定ロット
- DB は data/fx_spec_v2.db (亡き者と物理分離)

## 安全装置
- 最大保持時間: 4 時間 (= 16 本 M15) で時間損切り
- レジーム変化決済: VOLATILE → CALM/TRANSITIONAL で全決済
- 1 ポジション制限
- ロット固定 0.01 (= 1000 units)
- デモ口座限定 (起動時にチェック)
"""
from __future__ import annotations

import argparse
import io
import logging
import os
import signal
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.mt5_client import Mt5Client
from src.spec_v2.seasonal_detection import SeasonalDetector, SeasonRegime
from src.spec_v2.data_fetcher import fetch_m15_h1_for_seasonal, get_current_mid_price
from src.spec_v2.signal_v2 import generate_signal
from src.spec_v2 import db as poc_db


# ============================================================
# 設定
# ============================================================
POC_PAIR = "GBP_JPY"
POC_LOT_SIZE_UNITS = 1000           # 0.01 lot = 1,000 units (LOT_SIZE 100,000)
POC_LOOP_INTERVAL_SEC = 60
POC_MAX_HOLDING_MINUTES = 240       # 4 時間 (M15 16 本)
POC_DB_PATH = ROOT / "data" / "fx_spec_v2.db"
POC_LOG_PATH = ROOT / "data" / "spec_v2_poc.log"

PIP_SIZE = 0.01                     # GBP_JPY: 1 pip = 0.01


# ============================================================
# ログ設定
# ============================================================
def setup_logging():
    """ロガーをセットアップ。

    タスクスケジューラ経由起動でも確実に FileHandler が機能するよう以下を保証:
    - force=True: 既に basicConfig 済でも上書き (依存ライブラリの早期初期化対策)
    - delay=False: FileHandler を即時 open (lazy open による I/O 失敗の隠蔽防止)
    - 明示的に root に追加してハンドラ重複も防ぐ
    """
    POC_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(POC_LOG_PATH, encoding="utf-8", delay=False)
    stream_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[file_handler, stream_handler],
        force=True,  # 既存ハンドラを破棄して確実に File+Stream を再設定
    )


def _flush_logs() -> None:
    """全ハンドラを flush (タスクスケジューラ環境での buffer 滞留対策)"""
    for h in logging.getLogger().handlers:
        try:
            h.flush()
        except Exception:
            pass


logger = logging.getLogger("spec_v2_poc")


# ============================================================
# Slack 通知 (任意、SPEC_V2_SLACK_WEBHOOK_URL があれば使う)
# ============================================================
def slack_notify(message: str) -> None:
    """SPEC v2 PoC 専用 Slack 通知 (環境変数 SPEC_V2_SLACK_WEBHOOK_URL)"""
    webhook = os.environ.get("SPEC_V2_SLACK_WEBHOOK_URL")
    if not webhook:
        return
    try:
        import requests
        requests.post(webhook, json={"text": f"[SPEC v2 PoC] {message}"}, timeout=5)
    except Exception as e:
        logger.warning(f"Slack 通知失敗: {e}")


# ============================================================
# トレード管理
# ============================================================
def manage_open_trades(
    client: Mt5Client, current_regime: SeasonRegime,
) -> None:
    """オープン中トレードの時間損切り / レジーム変化決済を実行"""
    open_trades = poc_db.get_open_trades(POC_DB_PATH)
    if not open_trades:
        return

    mt5_positions = client.get_positions()
    mt5_ticket_map = {int(p["trade_id"]): p for p in mt5_positions if p["instrument"] == POC_PAIR}

    now_utc = datetime.now(timezone.utc)

    for trade in open_trades:
        ticket = trade["mt5_ticket"]
        if ticket is None:
            continue

        # MT5 側で既に決済されている (TP/SL ヒット)
        if ticket not in mt5_ticket_map:
            logger.info(f"trade {trade['id']} (ticket {ticket}) 既に MT5 で決済済み、DB 同期")
            _record_closure_from_mt5_history(client, trade, reason="tp_or_sl")
            continue

        # 時間損切り判定
        entry_time = datetime.fromisoformat(trade["entry_at_utc"].replace("Z", "+00:00"))
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=timezone.utc)
        holding_minutes = int((now_utc - entry_time).total_seconds() / 60)

        if holding_minutes >= POC_MAX_HOLDING_MINUTES:
            logger.info(f"trade {trade['id']} 時間損切り (保持 {holding_minutes} 分)")
            _close_and_record(client, trade, reason="time_limit", holding_minutes=holding_minutes)
            slack_notify(f"⏰ 時間損切り {trade['direction']} {holding_minutes}分")
            continue

        # レジーム変化決済 (VOLATILE 以外になったら閉じる)
        if current_regime != SeasonRegime.VOLATILE:
            logger.info(f"trade {trade['id']} レジーム変化決済 ({current_regime.value})")
            _close_and_record(client, trade, reason="regime_change", holding_minutes=holding_minutes)
            slack_notify(f"📉 レジーム変化決済 {trade['direction']} ({current_regime.value})")
            continue


def _close_and_record(
    client: Mt5Client, trade, reason: str, holding_minutes: int,
) -> None:
    """ポジションを MT5 で決済し、DB に記録"""
    ticket = trade["mt5_ticket"]
    try:
        result = client.close_position(str(ticket))
        exit_price = float(result.get("price", 0)) or get_current_mid_price(client, POC_PAIR) or trade["entry_price"]
    except Exception as e:
        logger.error(f"close_position 失敗: ticket={ticket} {e}")
        exit_price = get_current_mid_price(client, POC_PAIR) or trade["entry_price"]

    pnl_pips, pnl_jpy = _calc_pnl(trade, exit_price)
    poc_db.insert_trade_closure(
        POC_DB_PATH, trade_id=trade["id"],
        exit_at_utc=poc_db.utc_now_iso(),
        exit_price=exit_price, exit_reason=reason,
        pnl_pips=pnl_pips, pnl_jpy=pnl_jpy,
        holding_minutes=holding_minutes,
    )
    logger.info(
        f"trade {trade['id']} closed: reason={reason} exit={exit_price:.3f} "
        f"PnL={pnl_pips:+.1f} pips ({pnl_jpy:+.0f} JPY)"
    )


def _record_closure_from_mt5_history(client: Mt5Client, trade, reason: str) -> None:
    """MT5 で TP/SL ヒット済みの場合、現在価格で近似的に PnL 記録"""
    exit_price = get_current_mid_price(client, POC_PAIR) or trade["entry_price"]
    entry_time = datetime.fromisoformat(trade["entry_at_utc"].replace("Z", "+00:00"))
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=timezone.utc)
    holding_minutes = int((datetime.now(timezone.utc) - entry_time).total_seconds() / 60)

    pnl_pips, pnl_jpy = _calc_pnl(trade, exit_price)
    poc_db.insert_trade_closure(
        POC_DB_PATH, trade_id=trade["id"],
        exit_at_utc=poc_db.utc_now_iso(),
        exit_price=exit_price, exit_reason=reason,
        pnl_pips=pnl_pips, pnl_jpy=pnl_jpy,
        holding_minutes=holding_minutes,
    )


def _calc_pnl(trade, exit_price: float) -> tuple[float, float]:
    """PnL を pips / JPY で計算"""
    direction = trade["direction"]
    entry = trade["entry_price"]
    lots = trade["lots"]
    if direction == "long":
        pips = (exit_price - entry) / PIP_SIZE
    else:
        pips = (entry - exit_price) / PIP_SIZE
    # GBP_JPY は JPY 建てなので、1 pip × lots × 1000 = JPY 損益 (0.01 × 100000 × lots × pips)
    # 0.01 × 100000 = 1000 JPY/pip per 1 lot
    # 0.01 lot なら 10 JPY/pip
    pnl_jpy = pips * lots * 1000
    return pips, pnl_jpy


# ============================================================
# 新規エントリー判断
# ============================================================
def maybe_enter(
    client: Mt5Client, m15_df, h1_df, judgment, judgment_id: int,
) -> None:
    """VOLATILE 時に signal_v2 を呼び、エントリー条件成立なら発注"""
    if judgment.regime != SeasonRegime.VOLATILE:
        return

    # 既存ポジションあり → スキップ (1 ポジション制限)
    open_trades = poc_db.get_open_trades(POC_DB_PATH)
    if open_trades:
        logger.debug(f"既存オープン {len(open_trades)} 件あり、新規エントリー見送り")
        return

    signal_obj = generate_signal(m15_df)
    if signal_obj.direction == "no_signal":
        logger.debug(f"signal=no_signal: {signal_obj.reason}")
        return

    units = POC_LOT_SIZE_UNITS if signal_obj.direction == "long" else -POC_LOT_SIZE_UNITS

    try:
        result = client.market_order(
            instrument=POC_PAIR, units=units,
            stop_loss=signal_obj.sl_price or 0.0,
            take_profit=signal_obj.tp_price or 0.0,
        )
    except Exception as e:
        logger.error(f"market_order 失敗: {e}")
        slack_notify(f"❌ 発注失敗: {e}")
        return

    ticket = int(result.get("order_id", 0)) if result.get("order_id") else None
    fill_price = float(result.get("price", signal_obj.entry_price))

    trade_id = poc_db.insert_trade(
        POC_DB_PATH,
        mt5_ticket=ticket,
        entry_at_utc=poc_db.utc_now_iso(),
        direction=signal_obj.direction,
        lots=POC_LOT_SIZE_UNITS / 100_000,
        entry_price=fill_price,
        sl_price=signal_obj.sl_price, tp_price=signal_obj.tp_price,
        sl_pips=signal_obj.sl_pips, tp_pips=signal_obj.tp_pips,
        judgment_id=judgment_id,
        signal_reason=signal_obj.reason,
    )
    logger.info(
        f"📈 ENTRY {signal_obj.direction} ticket={ticket} entry={fill_price:.3f} "
        f"SL={signal_obj.sl_price:.3f} ({signal_obj.sl_pips:.1f}pips) "
        f"TP={signal_obj.tp_price:.3f} ({signal_obj.tp_pips:.1f}pips) "
        f"trade_id={trade_id}"
    )
    slack_notify(
        f"📈 新規 {signal_obj.direction} @ {fill_price:.3f} "
        f"SL {signal_obj.sl_pips:.0f}p / TP {signal_obj.tp_pips:.0f}p "
        f"({signal_obj.reason})"
    )


# ============================================================
# メインループ
# ============================================================
_stop_requested = False


def _signal_handler(sig, frame):
    global _stop_requested
    logger.info(f"signal {sig} 受信、ループ停止予定")
    _stop_requested = True


def run_loop(dry_run: bool = False, single_iter: bool = False):
    setup_logging()
    poc_db.init_db(POC_DB_PATH)
    poc_db.insert_loop_health(POC_DB_PATH, "start", f"dry_run={dry_run}")

    logger.info("=" * 80)
    logger.info(f"SPEC v2 PoC ループ開始 (pair={POC_PAIR}, lot={POC_LOT_SIZE_UNITS / 100_000})")
    logger.info(f"  DB: {POC_DB_PATH}")
    logger.info(f"  LOG: {POC_LOG_PATH}")
    logger.info(f"  間隔: {POC_LOOP_INTERVAL_SEC} 秒")
    logger.info(f"  最大保持: {POC_MAX_HOLDING_MINUTES} 分")
    logger.info(f"  dry_run: {dry_run}, single_iter: {single_iter}")
    logger.info("=" * 80)
    slack_notify(f"🟢 PoC 起動 (dry_run={dry_run})")

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        client = Mt5Client()
    except Exception as e:
        logger.error(f"MT5 接続失敗 (Mt5Client init): {e}")
        slack_notify(f"❌ MT5 接続失敗: {e}")
        poc_db.insert_loop_health(POC_DB_PATH, "error", f"MT5 init 失敗: {e}")
        return

    detector = SeasonalDetector(pair=POC_PAIR)
    iter_count = 0

    while not _stop_requested:
        iter_count += 1
        try:
            # 1. データ取得
            data = fetch_m15_h1_for_seasonal(client, pair=POC_PAIR)

            # 2. 季節判定
            judgment = detector.judge(data["m15"], data["h1"], use_chop_optional=True)
            jid = poc_db.insert_seasonal_judgment(
                POC_DB_PATH, judged_at_utc=poc_db.utc_now_iso(),
                regime=judgment.regime.value,
                m15_yz_vol=judgment.m15_yz_vol, m15_threshold=judgment.m15_threshold,
                m15_above=judgment.m15_above,
                h1_yz_vol=judgment.h1_yz_vol, h1_threshold=judgment.h1_threshold,
                h1_above=judgment.h1_above,
                chop_optional=judgment.chop_optional, chop_below_25=judgment.chop_below_25,
                notes=f"iter={iter_count}",
            )
            m15_yz_s = f"{judgment.m15_yz_vol:.5f}" if judgment.m15_yz_vol else "N/A"
            m15_thr_s = f"{judgment.m15_threshold:.5f}" if judgment.m15_threshold else "N/A"
            h1_yz_s = f"{judgment.h1_yz_vol:.5f}" if judgment.h1_yz_vol else "N/A"
            h1_thr_s = f"{judgment.h1_threshold:.5f}"
            logger.info(
                f"[iter {iter_count}] regime={judgment.regime.value} | "
                f"M15 YZ={m15_yz_s} thr={m15_thr_s} above={judgment.m15_above} | "
                f"H1 YZ={h1_yz_s} thr={h1_thr_s} above={judgment.h1_above}"
            )

            if not dry_run:
                # 3. オープン中トレードの管理
                manage_open_trades(client, judgment.regime)

                # 4. 新規エントリー判断
                maybe_enter(client, data["m15"], data["h1"], judgment, jid)

            # heartbeat 1 時間に 1 回
            if iter_count % 60 == 0:
                poc_db.insert_loop_health(POC_DB_PATH, "heartbeat", f"iter={iter_count}")

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"ループエラー: {e}\n{tb}")
            poc_db.insert_loop_health(POC_DB_PATH, "error", str(e))
            slack_notify(f"❌ ループエラー: {e}")

        # 各イテレーション末尾でログを必ず flush
        # (タスクスケジューラ環境で buffer が滞留して `tail -f` でリアルタイム性が落ちる対策)
        _flush_logs()

        if single_iter:
            break

        # 次のループまで sleep (停止リクエスト中は短く)
        for _ in range(POC_LOOP_INTERVAL_SEC):
            if _stop_requested:
                break
            time.sleep(1)

    poc_db.insert_loop_health(POC_DB_PATH, "stop", f"iter_count={iter_count}")
    slack_notify(f"🔴 PoC 停止 (iter={iter_count})")
    logger.info(f"ループ停止 (iter_count={iter_count})")
    # Mt5Client は明示的 disconnect 不要 (Python プロセス終了時に自動解放)
    # MT5 ライブラリの mt5.shutdown() を呼びたい場合はここに追加


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                       help="判定のみ、発注/決済をしない (起動初日の動作確認用)")
    parser.add_argument("--single-iter", action="store_true",
                       help="1 イテレーションだけ実行して終了 (テスト用)")
    args = parser.parse_args()

    run_loop(dry_run=args.dry_run, single_iter=args.single_iter)


if __name__ == "__main__":
    main()
