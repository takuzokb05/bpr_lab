"""
FX自動取引システム — ポジション管理モジュール

ポジションのライフサイクル管理（オープン・クローズ・同期）を担当する。
ローカル状態とブローカー状態の照合を行い、不整合を検知する。
SPEC_phase2.md F12 準拠。
"""

import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from src.broker_client import BrokerClient
from src.config import CORRELATION_GROUPS, MAX_CORRELATION_EXPOSURE, MAX_OPEN_POSITIONS
from src.risk_manager import RiskManager
from src.strategy.base import Signal, StrategyBase
from src.trade_postmortem import TradePostMortem

logger = logging.getLogger(__name__)


class PositionManagerError(Exception):
    """ポジション管理固有のエラー"""


class PositionManager:
    """
    ポジションのライフサイクルを管理するクラス。

    シグナルに基づくポジションオープン、決済、ブローカーとの同期を行う。
    リスク管理チェックを全て通過した場合のみポジションを開く。
    """

    def __init__(
        self,
        broker_client: BrokerClient,
        risk_manager: RiskManager,
        max_positions: int = MAX_OPEN_POSITIONS,
        db_path: Optional[Path] = None,
    ) -> None:
        """
        Args:
            broker_client: ブローカークライアント（注文発注・ポジション取得）
            risk_manager: リスク管理（キルスイッチ・損失上限・ポジションサイジング）
            max_positions: 最大同時ポジション数
            db_path: SQLiteデータベースパス（tradesテーブル用。
                     未設定時はDB永続化を行わない）

        Raises:
            ValueError: max_positions が1未満の場合
        """
        if max_positions < 1:
            raise ValueError(
                f"最大ポジション数は1以上である必要があります: {max_positions}"
            )
        self._broker_client = broker_client
        self._risk_manager = risk_manager
        self._max_positions = max_positions
        self._open_positions: list[dict] = []
        self._trade_history: list[dict] = []
        self._lock = threading.Lock()  # マルチスレッド対応: ポジション操作の排他制御
        self._db_path = db_path
        self._postmortem = TradePostMortem(db_path=db_path)
        if db_path is not None:
            self._init_trades_db()

    # ------------------------------------------------------------------
    # SQLite 永続化
    # ------------------------------------------------------------------

    def _init_trades_db(self) -> None:
        """trades テーブルを作成する。

        T5: 既存DBに対しても AI 関連カラムを冪等に追加する（マイグレーション相当）。
        本番DBは scripts/migrate_add_ai_columns.py を別途流すが、
        新規環境やテストで CREATE TABLE 後に呼ばれた場合もカラムが揃うようにする。
        """
        if self._db_path is None:
            return
        if str(self._db_path) != ":memory:":
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT NOT NULL UNIQUE,
                    instrument TEXT NOT NULL,
                    units INTEGER NOT NULL,
                    open_price REAL NOT NULL,
                    close_price REAL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    pl REAL,
                    opened_at TEXT NOT NULL,
                    closed_at TEXT,
                    status TEXT NOT NULL DEFAULT 'open',
                    ai_decision TEXT,
                    ai_confidence REAL,
                    ai_reasons TEXT,
                    ai_direction TEXT,
                    ai_regime TEXT
                )
                """
            )
            # 既に古いスキーマで作成されたDBにも AI カラムを追加する（冪等）
            cur = conn.execute("PRAGMA table_info(trades)")
            existing = {row[1] for row in cur.fetchall()}
            for col, col_type in (
                ("ai_decision", "TEXT"),
                ("ai_confidence", "REAL"),
                ("ai_reasons", "TEXT"),
                ("ai_direction", "TEXT"),
                ("ai_regime", "TEXT"),
            ):
                if col not in existing:
                    conn.execute(f"ALTER TABLE trades ADD COLUMN {col} {col_type}")

    def _db_save_open_trade(self, position: dict) -> None:
        """オープンしたポジションをDBに保存する。

        T5: AIバイアス情報（ai_decision/ai_confidence/ai_reasons/ai_direction/ai_regime）
        が position dict に含まれていれば一緒に保存する。AIフィルター未適用時は NULL のまま。
        """
        if self._db_path is None:
            return
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO trades
                       (trade_id, instrument, units, open_price,
                        stop_loss, take_profit, opened_at, status,
                        ai_decision, ai_confidence, ai_reasons,
                        ai_direction, ai_regime)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?)""",
                    (
                        position["trade_id"],
                        position["instrument"],
                        position["units"],
                        position["open_price"],
                        position["stop_loss"],
                        position["take_profit"],
                        position["opened_at"].isoformat(),
                        position.get("ai_decision"),
                        position.get("ai_confidence"),
                        position.get("ai_reasons"),
                        position.get("ai_direction"),
                        position.get("ai_regime"),
                    ),
                )
        except sqlite3.Error as e:
            logger.warning("ポジションオープンのDB記録に失敗: %s", e)

    def _db_save_closed_trade(
        self,
        trade_id: str,
        close_price: float,
        pl: float,
        closed_at: datetime,
    ) -> None:
        """決済済みトレードをDBに反映する。"""
        if self._db_path is None:
            return
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                conn.execute(
                    """UPDATE trades
                       SET close_price=?, pl=?, closed_at=?, status='closed'
                       WHERE trade_id=?""",
                    (close_price, pl, closed_at.isoformat(), trade_id),
                )
        except sqlite3.Error as e:
            logger.warning("ポジション決済のDB記録に失敗: %s", e)

    # ------------------------------------------------------------------
    # 相関チェック
    # ------------------------------------------------------------------

    def _check_correlation_exposure(
        self, instrument: str
    ) -> tuple[bool, str]:
        """
        相関グループ内のポジション数をチェックする。

        同一グループ内の保有ポジション数が MAX_CORRELATION_EXPOSURE を
        超過する場合、新規ポジションをブロックする。
        ロック内から呼ぶこと。

        Args:
            instrument: 新規オープン対象の通貨ペア

        Returns:
            (許可フラグ, 理由文字列)。許可時は (True, "")。
        """
        for group_name, group_instruments in CORRELATION_GROUPS.items():
            if instrument not in group_instruments:
                continue

            # このグループに属する保有ポジション数をカウント
            count = sum(
                1 for pos in self._open_positions
                if pos["instrument"] in group_instruments
            )

            if count >= MAX_CORRELATION_EXPOSURE:
                reason = (
                    f"相関グループ '{group_name}' の保有数が上限に到達 "
                    f"({count}/{MAX_CORRELATION_EXPOSURE})"
                )
                return False, reason

        return True, ""

    # ------------------------------------------------------------------
    # ポジションオープン
    # ------------------------------------------------------------------

    def open_position(
        self,
        instrument: str,
        signal: Signal,
        data: pd.DataFrame,
        strategy: StrategyBase,
        indicators: Optional[dict] = None,
        ai_record: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        シグナルに基づいてポジションを開く。

        全てのリスクチェックを順に通過した場合のみ注文を発注する。
        安全側に倒す方針のため、判断に迷う場合はポジションを開かない。

        Args:
            instrument: 通貨ペア（例: "USD_JPY"）
            signal: 取引シグナル（BUY / SELL / HOLD）
            data: OHLCV形式のDataFrame（SL/TP計算に使用）
            strategy: 戦略インスタンス（SL/TP算出用）

        Returns:
            注文結果dict。取引不可時はNone。

        Raises:
            PositionManagerError: ブローカーAPI呼び出しで予期しないエラーが発生した場合
        """
        # 1. シグナルチェック: BUY or SELL でなければ取引しない
        if signal not in (Signal.BUY, Signal.SELL):
            logger.debug("シグナルがBUY/SELLではないため取引スキップ: %s", signal)
            return None

        direction = signal.value  # "BUY" or "SELL"

        with self._lock:
            # 2. キルスイッチチェック
            if not self._risk_manager.kill_switch.is_trading_allowed():
                logger.warning(
                    "キルスイッチ発動中のため取引不可: reason=%s",
                    self._risk_manager.kill_switch.reason,
                )
                return None

            # 3. 同一通貨ペアの重複チェック（ローカルキャッシュ）
            for pos in self._open_positions:
                if pos["instrument"] == instrument:
                    logger.info(
                        "同一通貨ペア %s のポジションが既に存在するため取引スキップ: "
                        "trade_id=%s",
                        instrument,
                        pos["trade_id"],
                    )
                    return None

            # 3a. 同一通貨ペアの重複チェック（ブローカー直接照会）
            # 起動直後の sync 未実施・MT5 への伝搬遅延・複数プロセス起動など、
            # ローカルキャッシュ単独では取りこぼすケースに対するアトミックな安全網。
            # P1-2 分析で 04/21〜05/01 に GBP_JPY で 21/37 件の重複が観測されたため追加。
            try:
                broker_positions = self._broker_client.get_positions()
            except Exception as e:
                # 取得失敗時は既存ローカルチェックを信頼してフォールスルー
                logger.warning(
                    "ブローカーポジション取得失敗（ローカル判定で続行）: %s", e,
                )
                broker_positions = []
            for bpos in broker_positions:
                if bpos.get("instrument") == instrument:
                    logger.info(
                        "同一通貨ペア %s のブローカーポジションが既に存在するため取引スキップ: "
                        "trade_id=%s",
                        instrument,
                        bpos.get("trade_id"),
                    )
                    return None

            # 3b. 相関グループ内のエクスポージャーチェック
            corr_allowed, corr_reason = self._check_correlation_exposure(instrument)
            if not corr_allowed:
                logger.info(
                    "相関エクスポージャー上限のため取引スキップ: %s", corr_reason
                )
                return None

            # 4. 最大ポジション数チェック
            if len(self._open_positions) >= self._max_positions:
                logger.info(
                    "最大ポジション数(%d)に達しているため取引スキップ: 現在=%d",
                    self._max_positions,
                    len(self._open_positions),
                )
                return None

            # 5. 損失上限チェック
            is_allowed, reason = self._risk_manager.check_loss_limits(
                self._trade_history
            )
            if not is_allowed:
                logger.warning("損失上限に到達のため取引不可: %s", reason)
                return None

            # 6. 連続負けチェック
            _, is_stopped = self._risk_manager.check_consecutive_losses(
                self._trade_history
            )
            if is_stopped:
                logger.warning("連続負け上限に到達のため取引不可")
                return None

            # エントリー価格を最新の終値から取得
            entry_price = float(data["close"].iloc[-1])

            # 7. SL算出（ポジションサイズ計算に必要）
            stop_loss = strategy.calculate_stop_loss(entry_price, direction, data)

            # stop_loss_pips の算出: JPYクロスと非JPYペアで除数が異なる
            is_jpy_cross = "JPY" in instrument.upper()
            pip_unit = 0.01 if is_jpy_cross else 0.0001
            stop_loss_pips = round(abs(entry_price - stop_loss) / pip_unit, 1)

            # stop_loss_pips が0の場合は安全のため取引しない
            if stop_loss_pips <= 0:
                logger.warning(
                    "stop_loss_pipsが0以下のため取引不可: instrument=%s, "
                    "entry=%.5f, sl=%.5f",
                    instrument,
                    entry_price,
                    stop_loss,
                )
                return None

            # ポジションサイズ算出
            balance = self._risk_manager.account_balance
            lot_size = self._risk_manager.calculate_position_size(
                balance, stop_loss_pips, instrument
            )

            # 8. ポジションサイズが0なら取引不可
            if lot_size <= 0:
                logger.info(
                    "ポジションサイズが0のため取引スキップ: instrument=%s", instrument
                )
                return None

            # 9. TP算出
            take_profit = strategy.calculate_take_profit(
                entry_price, direction, stop_loss
            )

            # units計算: lot_size * 1000 の整数変換
            # BUY → 正, SELL → 負
            units = int(lot_size * 1000)
            if units == 0:
                logger.info(
                    "units が0のため取引スキップ: lot_size=%.6f, instrument=%s",
                    lot_size,
                    instrument,
                )
                return None

            if signal == Signal.SELL:
                units = -units

            # 10. 成行注文発注
            try:
                order_result = self._broker_client.market_order(
                    instrument=instrument,
                    units=units,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )
            except Exception as e:
                raise PositionManagerError(
                    f"成行注文の発注に失敗しました: instrument={instrument}, "
                    f"units={units}, error={e}"
                ) from e

            # 11. ローカル状態を更新
            trade_id = order_result.get("trade_id", order_result.get("order_id", ""))
            open_price = order_result.get("price", entry_price)

            position = {
                "trade_id": str(trade_id),
                "instrument": instrument,
                "units": units,
                "open_price": float(open_price),
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "opened_at": datetime.now(timezone.utc),
                "unrealized_pl": 0.0,
            }
            # T5: AI A/B 検証用に AIBias 記録を埋め込む（オプショナル）
            if ai_record:
                for key in (
                    "ai_decision",
                    "ai_confidence",
                    "ai_reasons",
                    "ai_direction",
                    "ai_regime",
                ):
                    if key in ai_record:
                        position[key] = ai_record[key]
            self._open_positions.append(position)
            self._db_save_open_trade(position)

            # エントリー時の指標スナップショットを保存（事後分析用）
            if indicators is not None:
                self._postmortem.save_entry_snapshot(str(trade_id), indicators)

        logger.info(
            "ポジションオープン成功: trade_id=%s, instrument=%s, units=%d, "
            "price=%.5f, sl=%.5f, tp=%.5f",
            trade_id,
            instrument,
            units,
            open_price,
            stop_loss,
            take_profit,
        )

        return order_result

    # ------------------------------------------------------------------
    # ポジションクローズ
    # ------------------------------------------------------------------

    def close_position(self, trade_id: str) -> Optional[dict]:
        """
        指定ポジションを決済し、trade_historyに移動する。

        Args:
            trade_id: 決済対象のトレードID

        Returns:
            決済結果dict。該当ポジションが見つからない場合はNone。

        Raises:
            PositionManagerError: ブローカーAPI呼び出しで予期しないエラーが発生した場合
        """
        with self._lock:
            # ローカル状態から該当ポジションを検索
            target_pos = None
            for pos in self._open_positions:
                if pos["trade_id"] == trade_id:
                    target_pos = pos
                    break

            if target_pos is None:
                logger.warning(
                    "決済対象のポジションが見つかりません: trade_id=%s", trade_id
                )
                return None

            # ブローカーに決済リクエスト
            try:
                close_result = self._broker_client.close_position(trade_id)
            except Exception as e:
                raise PositionManagerError(
                    f"ポジション決済に失敗しました: trade_id={trade_id}, error={e}"
                ) from e

            # ローカル状態から削除
            self._open_positions = [
                p for p in self._open_positions if p["trade_id"] != trade_id
            ]

            # 取引履歴に追加（H-2: 決済結果の欠損値を検知・警告）
            close_price = close_result.get("close_price")
            realized_pl = close_result.get("realized_pl")
            pl_unknown = close_price is None or realized_pl is None

            if pl_unknown:
                logger.warning(
                    "ブローカーから決済価格または損益が返却されませんでした: "
                    "trade_id=%s, close_result=%s",
                    trade_id, close_result,
                )

            history_entry = {
                "trade_id": trade_id,
                "instrument": target_pos["instrument"],
                "units": target_pos["units"],
                "open_price": target_pos["open_price"],
                "close_price": close_price if close_price is not None else 0.0,
                "pl": realized_pl if realized_pl is not None else 0.0,
                "pl_unknown": pl_unknown,
                "opened_at": target_pos["opened_at"],
                "close_time": datetime.now(timezone.utc),
            }
            self._trade_history.append(history_entry)
            self._db_save_closed_trade(
                trade_id,
                history_entry["close_price"],
                history_entry["pl"],
                history_entry["close_time"],
            )

        logger.info(
            "ポジション決済完了: trade_id=%s, instrument=%s, pl=%.2f",
            trade_id,
            target_pos["instrument"],
            history_entry["pl"],
        )

        # 事後分析をバックグラウンドでトリガー
        self._postmortem.trigger_analysis(
            trade_id=trade_id,
            instrument=target_pos["instrument"],
            units=target_pos["units"],
            open_price=target_pos["open_price"],
            close_price=history_entry["close_price"],
            pl=history_entry["pl"],
            opened_at=target_pos["opened_at"],
            closed_at=history_entry["close_time"],
        )

        return close_result

    # ------------------------------------------------------------------
    # 一括決済（キルスイッチ用）
    # ------------------------------------------------------------------

    def close_all_positions(self, reason: str = "") -> dict:
        """
        全ポジションを一括決済する。EMERGENCYキルスイッチ用。

        個別の決済エラーが発生しても残りのポジション決済を継続する。

        Args:
            reason: 一括決済の理由（ログ出力用）

        Returns:
            {
                "closed": list[dict],     # 決済成功した結果リスト
                "failed": list[str],      # 決済失敗したtrade_idリスト
                "total": int,             # 決済対象の総数
            }
        """
        if reason:
            logger.warning("全ポジション一括決済を開始: reason=%s", reason)
        else:
            logger.warning("全ポジション一括決済を開始")

        closed: list[dict] = []
        failed: list[str] = []

        # リストのコピーを使って反復（close_positionがリストを変更するため）
        positions_to_close = list(self._open_positions)

        for pos in positions_to_close:
            trade_id = pos["trade_id"]
            try:
                result = self.close_position(trade_id)
                if result is not None:
                    closed.append(result)
                else:
                    logger.error(
                        "一括決済中にポジションが見つかりませんでした: "
                        "trade_id=%s",
                        trade_id,
                    )
                    failed.append(trade_id)
            except PositionManagerError as e:
                # 一括決済では個別エラーでも継続する（安全性のため全て試みる）
                logger.error(
                    "一括決済中にエラー発生（続行）: trade_id=%s, error=%s",
                    trade_id,
                    e,
                )
                failed.append(trade_id)

        logger.info(
            "全ポジション一括決済完了: 成功=%d, 失敗=%d, 合計=%d",
            len(closed),
            len(failed),
            len(positions_to_close),
        )

        return {
            "closed": closed,
            "failed": failed,
            "total": len(positions_to_close),
        }

    # ------------------------------------------------------------------
    # ブローカー同期
    # ------------------------------------------------------------------

    def sync_with_broker(self) -> dict:
        """
        ブローカーの実ポジションとローカル状態を照合する。

        不整合を検知し、ローカル状態を修正する。

        Returns:
            {
                "synced": int,        # 一致したポジション数
                "local_only": list,   # ローカルのみに存在するtrade_idリスト
                "broker_only": list,  # ブローカーのみに存在するtrade_idリスト
            }

        Raises:
            PositionManagerError: ブローカーAPI呼び出しで予期しないエラーが発生した場合
        """
        try:
            broker_positions = self._broker_client.get_positions()
        except Exception as e:
            raise PositionManagerError(
                f"ブローカーからのポジション取得に失敗しました: {e}"
            ) from e

        with self._lock:
            # ブローカー側のtrade_idセット
            broker_ids = {str(p["trade_id"]) for p in broker_positions}

            # ローカル側のtrade_idセット
            local_ids = {p["trade_id"] for p in self._open_positions}

            # 一致: 両方に存在
            synced_ids = local_ids & broker_ids

            # ローカルのみ: ブローカーでは既に決済済みの可能性
            local_only = sorted(local_ids - broker_ids)

            # ブローカーのみ: ローカルが把握していないポジション
            broker_only = sorted(broker_ids - local_ids)

            # 一致したポジションの未実現損益を更新
            broker_pos_map = {str(p["trade_id"]): p for p in broker_positions}
            for pos in self._open_positions:
                if pos["trade_id"] in synced_ids:
                    broker_pos = broker_pos_map[pos["trade_id"]]
                    pos["unrealized_pl"] = broker_pos.get("unrealized_pl", 0.0)

            # H-3: ローカルのみのポジションを自動除去（ブローカーで決済済み）
            if local_only:
                for orphan_id in local_only:
                    target = next(
                        (p for p in self._open_positions if p["trade_id"] == orphan_id),
                        None,
                    )
                    if target:
                        self._open_positions.remove(target)

                        # ブローカーの取引履歴から決済情報を復元（SL/TP自動決済対応）
                        deal = None
                        try:
                            deal = self._broker_client.get_closed_deal(orphan_id)
                        except Exception as e:
                            logger.warning(
                                "決済履歴の取得に失敗: trade_id=%s, error=%s",
                                orphan_id, e,
                            )

                        if deal is not None:
                            close_price = float(deal.get("close_price", 0.0))
                            realized_pl = float(deal.get("realized_pl", 0.0))
                            close_time = deal.get("closed_at") or datetime.now(timezone.utc)
                            pl_unknown = False
                        else:
                            # 履歴から取得できなかった場合のみフォールバック
                            close_price = 0.0
                            realized_pl = 0.0
                            close_time = datetime.now(timezone.utc)
                            pl_unknown = True

                        self._trade_history.append({
                            "trade_id": orphan_id,
                            "instrument": target["instrument"],
                            "units": target["units"],
                            "open_price": target["open_price"],
                            "close_price": close_price,
                            "pl": realized_pl,
                            "pl_unknown": pl_unknown,
                            "opened_at": target["opened_at"],
                            "close_time": close_time,
                        })
                        self._db_save_closed_trade(
                            orphan_id, close_price, realized_pl, close_time
                        )
                        logger.warning(
                            "ブローカー側で決済済みのポジションをローカルから除去: "
                            "trade_id=%s, instrument=%s, close_price=%.5f, pl=%.2f, pl_unknown=%s",
                            orphan_id, target["instrument"],
                            close_price, realized_pl, pl_unknown,
                        )

                        # 事後分析をバックグラウンドでトリガー
                        try:
                            self._postmortem.trigger_analysis(
                                trade_id=orphan_id,
                                instrument=target["instrument"],
                                units=target["units"],
                                open_price=target["open_price"],
                                close_price=close_price,
                                pl=realized_pl,
                                opened_at=target["opened_at"],
                                closed_at=close_time,
                            )
                        except Exception as e:
                            logger.warning(
                                "事後分析トリガー失敗: trade_id=%s, error=%s",
                                orphan_id, e,
                            )

            # broker_only: ブローカーにあるがローカル未把握
            # bot再起動時のポジション復元、または手動取引で開いたもの。
            # 取り込まないと MAX_OPEN_POSITIONS や重複チェックが機能しない。
            if broker_only:
                for orphan_id in broker_only:
                    broker_pos = broker_pos_map[orphan_id]
                    position = {
                        "trade_id": orphan_id,
                        "instrument": broker_pos["instrument"],
                        "units": broker_pos["units"],
                        "open_price": float(broker_pos.get("price_open", 0.0)),
                        # SL/TPはブローカー側で設定済み前提、未知なら 0.0
                        "stop_loss": float(broker_pos.get("stop_loss", 0.0) or 0.0),
                        "take_profit": float(
                            broker_pos.get("take_profit", 0.0) or 0.0
                        ),
                        "opened_at": datetime.now(timezone.utc),
                        "unrealized_pl": float(broker_pos.get("unrealized_pl", 0.0)),
                    }
                    self._open_positions.append(position)
                    # DBにも記録（既存があれば REPLACE、なければ新規 INSERT）
                    self._db_save_open_trade(position)
                    logger.info(
                        "ブローカーポジションをローカルに取り込み: "
                        "trade_id=%s, instrument=%s, units=%d",
                        orphan_id, position["instrument"], position["units"],
                    )

            # 古い取引履歴をメモリから除去（DBには残る）
            self._trim_trade_history()

        result = {
            "synced": len(synced_ids),
            "local_only": local_only,
            "broker_only": broker_only,
        }

        logger.debug(
            "ブローカー同期完了: synced=%d, local_only=%d, broker_only=%d",
            result["synced"],
            len(local_only),
            len(broker_only),
        )

        return result

    # ------------------------------------------------------------------
    # プロパティ・ゲッター
    # ------------------------------------------------------------------

    def get_open_positions(self) -> list[dict]:
        """
        ローカルの保有ポジション一覧を返す。

        Returns:
            ポジション情報dictのリスト（コピー）
        """
        with self._lock:
            return list(self._open_positions)

    @property
    def position_count(self) -> int:
        """現在の保有ポジション数"""
        with self._lock:
            return len(self._open_positions)

    @property
    def trade_history(self) -> list[dict]:
        """決済済みの取引履歴（損失上限チェック用）"""
        with self._lock:
            return list(self._trade_history)

    def _trim_trade_history(self) -> None:
        """30日以上前の取引履歴をメモリから除去する（DBには残る）。

        ロック内から呼ぶこと。
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        self._trade_history = [
            t for t in self._trade_history
            if t.get("close_time", t.get("opened_at")) > cutoff
        ]
