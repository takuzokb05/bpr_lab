"""
FX自動取引システム -- リスク管理コアモジュール

ポジションサイジング、ドローダウン制御、損失上限チェック、
連続負けカウンター、レバレッジチェック、キルスイッチを提供する。
doc 04 セクション4.1-4.2 / SPEC.md F4 準拠。
"""

import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from src.broker_client import BrokerClient
from src.config import (
    DRAWDOWN_LEVELS,
    KILL_API_DISCONNECT_SEC,
    KILL_ATR_MULTIPLIER,
    KILL_COOLDOWN_MINUTES,
    KILL_SPREAD_MULTIPLIER,
    MAX_CONSECUTIVE_LOSSES,
    MAX_DAILY_LOSS,
    MAX_LEVERAGE,
    MAX_MONTHLY_LOSS,
    MAX_RISK_PER_TRADE,
    MAX_WEEKLY_LOSS,
)

logger = logging.getLogger(__name__)


class KillSwitch:
    """
    キルスイッチ -- 6種類の発動条件を管理する緊急停止機構。

    発動条件:
      1. 日次損失キル
      2. 連続負けキル
      3. ボラティリティキル（ATR通常の KILL_ATR_MULTIPLIER 倍）
      4. スプレッドキル（通常の KILL_SPREAD_MULTIPLIER 倍）
      5. API切断キル（KILL_API_DISCONNECT_SEC 秒以上の切断）
      6. 手動キル
    """

    # 有効なキルスイッチ理由の一覧
    VALID_REASONS: set[str] = {
        "daily_loss",
        "consecutive_losses",
        "volatility",
        "spread",
        "api_disconnect",
        "manual",
    }

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._is_active: bool = False
        self._reason: Optional[str] = None
        self._activated_at: Optional[datetime] = None
        self._db_path = db_path
        self._db_log_id: Optional[int] = None
        if db_path is not None:
            self._init_kill_switch_db()

    # --- プロパティ ---

    @property
    def is_active(self) -> bool:
        """キルスイッチが発動中かどうか"""
        return self._is_active

    @property
    def reason(self) -> Optional[str]:
        """発動理由。未発動時は None"""
        return self._reason

    @property
    def activated_at(self) -> Optional[datetime]:
        """発動時刻。未発動時は None"""
        return self._activated_at

    def activate(self, reason: str) -> None:
        """
        キルスイッチを発動する。

        Args:
            reason: 発動理由（VALID_REASONS のいずれか）

        Raises:
            ValueError: 不正な発動理由が指定された場合
        """
        if reason not in self.VALID_REASONS:
            raise ValueError(
                f"不正なキルスイッチ理由: '{reason}'。"
                f"有効な値: {sorted(self.VALID_REASONS)}"
            )
        self._is_active = True
        self._reason = reason
        self._activated_at = datetime.now(timezone.utc)
        logger.warning(
            "キルスイッチ発動: reason=%s, activated_at=%s",
            reason,
            self._activated_at.isoformat(),
        )
        self._db_log_activation()

    def deactivate(self) -> None:
        """キルスイッチを解除する。"""
        if self._is_active:
            logger.info(
                "キルスイッチ解除: reason=%s, was_active_since=%s",
                self._reason,
                self._activated_at.isoformat() if self._activated_at else "N/A",
            )
            self._db_log_deactivation()
        self._is_active = False
        self._reason = None
        self._activated_at = None

    # --- SQLite 永続化 ---

    def _init_kill_switch_db(self) -> None:
        """kill_switch_log テーブルを作成する。"""
        if self._db_path is None:
            return
        if str(self._db_path) != ":memory:":
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kill_switch_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reason TEXT NOT NULL,
                    activated_at TEXT NOT NULL,
                    deactivated_at TEXT,
                    balance_at_activation REAL,
                    drawdown_rate REAL
                )
                """
            )

    def _db_log_activation(self) -> None:
        """キルスイッチ発動をDBに記録する。"""
        if self._db_path is None or self._activated_at is None:
            return
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                cursor = conn.execute(
                    "INSERT INTO kill_switch_log (reason, activated_at) VALUES (?, ?)",
                    (self._reason, self._activated_at.isoformat()),
                )
                self._db_log_id = cursor.lastrowid
        except sqlite3.Error as e:
            logger.warning("キルスイッチ発動のDB記録に失敗: %s", e)

    def _db_log_deactivation(self) -> None:
        """キルスイッチ解除をDBに記録する。"""
        if self._db_path is None or self._db_log_id is None:
            return
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                conn.execute(
                    "UPDATE kill_switch_log SET deactivated_at=? WHERE id=?",
                    (datetime.now(timezone.utc).isoformat(), self._db_log_id),
                )
            self._db_log_id = None
        except sqlite3.Error as e:
            logger.warning("キルスイッチ解除のDB記録に失敗: %s", e)

    def is_trading_allowed(self) -> bool:
        """取引が許可されているかどうかを返す（キルスイッチ未発動なら True）。"""
        return not self._is_active

    def should_auto_deactivate(self, current_time: Optional[datetime] = None) -> bool:
        """
        自動解除すべきかどうかを判定する。

        解除条件:
        - daily_loss: 翌日0:00 UTC以降 → True
        - consecutive_losses: 24時間経過後 → True
        - volatility / spread: 常に True（呼び出し元で条件判定済みの前提）
        - api_disconnect: 常に True（再接続後に呼ばれる前提）
        - manual: 常に False（手動解除のみ）

        Args:
            current_time: 判定基準時刻（テスト用。未指定時は現在時刻UTC）

        Returns:
            True なら自動解除可能。
        """
        if not self._is_active:
            return False

        if current_time is None:
            current_time = datetime.now(timezone.utc)

        reason = self._reason

        if reason == "daily_loss":
            # 翌日0:00 UTC以降で解除
            if self._activated_at is None:
                return False
            activated_date = self._activated_at.date()
            next_day_start = datetime(
                activated_date.year,
                activated_date.month,
                activated_date.day,
                tzinfo=timezone.utc,
            ) + timedelta(days=1)
            return current_time >= next_day_start

        if reason == "consecutive_losses":
            # 24時間経過後で解除
            if self._activated_at is None:
                return False
            return current_time >= self._activated_at + timedelta(hours=24)

        if reason in ("volatility", "spread"):
            # クールダウン期間経過後に解除可能（即時解除を防止）
            if self._activated_at is None:
                return False
            cooldown = timedelta(minutes=KILL_COOLDOWN_MINUTES)
            return current_time >= self._activated_at + cooldown

        if reason == "api_disconnect":
            # 常に True（再接続後に呼ばれる前提）
            return True

        if reason == "manual":
            # 手動キルは手動解除のみ
            return False

        # 未知の理由 → 安全側で解除しない
        return False


class RiskManager:
    """
    リスク管理コアクラス。

    ポジションサイジング、ドローダウン制御、損失上限チェック、
    連続負けカウンター、レバレッジチェックを統合的に提供する。
    """

    def __init__(
        self,
        account_balance: float,
        broker_client: Optional[BrokerClient] = None,
        db_path: Optional[Path] = None,
    ) -> None:
        """
        Args:
            account_balance: 初期口座残高（円）
            broker_client: ブローカークライアント（pip_value動的計算に使用。
                           未設定時はPhase 1固定値にフォールバック）
            db_path: SQLiteデータベースパス（kill_switch_logテーブル用。
                     未設定時はDB永続化を行わない）

        Raises:
            ValueError: 口座残高が0以下の場合
        """
        if account_balance <= 0:
            raise ValueError(
                f"口座残高は正の値である必要があります: {account_balance}"
            )
        self._account_balance = account_balance
        self._peak_balance = account_balance
        self._broker_client = broker_client
        self.kill_switch = KillSwitch(db_path=db_path)
        # 直近成功した quote_currency → JPY レートのキャッシュ。
        # broker 一時失敗時のフォールバック優先順位:
        #   1. このキャッシュ（最新成功値）  2. 静的 _FALLBACK_QUOTE_TO_JPY
        # インスタンス属性にしてプロセス間で共有しない（テスト独立性のため）。
        self._live_jpy_rate_cache: dict[str, float] = {}

    @property
    def account_balance(self) -> float:
        """現在の口座残高"""
        return self._account_balance

    @property
    def peak_balance(self) -> float:
        """最高残高（ドローダウン計算基準）"""
        return self._peak_balance

    def update_balance(self, new_balance: float) -> None:
        """
        口座残高を更新し、ピーク残高も必要に応じて更新する。

        ブローカーAPIから残高を取得するたびに呼び出すこと。
        ドローダウン制御・損失上限チェックの正確性に必要。

        Args:
            new_balance: 最新の口座残高

        Raises:
            ValueError: new_balance が負の値の場合
        """
        if new_balance < 0:
            raise ValueError(f"口座残高が負の値です: {new_balance}")
        self._account_balance = new_balance
        if new_balance > self._peak_balance:
            self._peak_balance = new_balance
            logger.info("ピーク残高を更新: %.0f", new_balance)

    # ------------------------------------------------------------------
    # 0. キルスイッチ総合評価（F14）
    # ------------------------------------------------------------------

    def evaluate_kill_switch(
        self,
        current_balance: float,
        trade_history: list[dict],
        current_atr: Optional[float] = None,
        normal_atr: Optional[float] = None,
        current_spread: Optional[float] = None,
        normal_spread: Optional[float] = None,
    ) -> Optional[str]:
        """
        全キルスイッチ条件を評価し、発動すべき理由を返す。

        チェック順序（優先度順）:
        1. ドローダウン STOP/EMERGENCY → "daily_loss"
        2. 日次損失上限 → "daily_loss"
        3. 連続負け → "consecutive_losses"
        4. ボラティリティ（ATR） → "volatility"
        5. スプレッド → "spread"

        全条件クリアなら None。
        例外発生時は安全側に "daily_loss" を返す（取引停止）。

        Args:
            current_balance: 現在の口座残高
            trade_history: 取引履歴リスト
            current_atr: 現在のATR値（None可）
            normal_atr: 通常時のATR値（None可）
            current_spread: 現在のスプレッド（None可）
            normal_spread: 通常時のスプレッド（None可）

        Returns:
            発動すべきキルスイッチの理由文字列。全条件クリアなら None。
        """
        try:
            # 1. ドローダウンチェック
            _, level_name, _ = self.check_drawdown(
                current_balance, self._peak_balance
            )
            if level_name in ("STOP", "EMERGENCY"):
                logger.warning(
                    "キルスイッチ評価: ドローダウン %s 検出 → daily_loss",
                    level_name,
                )
                return "daily_loss"

            # 2. 日次損失上限チェック
            is_allowed, reason = self.check_loss_limits(trade_history)
            if not is_allowed:
                logger.warning(
                    "キルスイッチ評価: 損失上限到達 → daily_loss (%s)", reason
                )
                return "daily_loss"

            # 3. 連続負けチェック
            _, is_stopped = self.check_consecutive_losses(trade_history)
            if is_stopped:
                logger.warning(
                    "キルスイッチ評価: 連続負け上限到達 → consecutive_losses"
                )
                return "consecutive_losses"

            # 4. ボラティリティチェック（ATR）
            if (
                current_atr is not None
                and normal_atr is not None
                and normal_atr > 0
                and current_atr >= normal_atr * KILL_ATR_MULTIPLIER
            ):
                logger.warning(
                    "キルスイッチ評価: ATR異常 (current=%.5f, normal=%.5f, "
                    "multiplier=%.1f) → volatility",
                    current_atr,
                    normal_atr,
                    KILL_ATR_MULTIPLIER,
                )
                return "volatility"

            # 5. スプレッドチェック
            if (
                current_spread is not None
                and normal_spread is not None
                and normal_spread > 0
                and current_spread >= normal_spread * KILL_SPREAD_MULTIPLIER
            ):
                logger.warning(
                    "キルスイッチ評価: スプレッド異常 (current=%.5f, normal=%.5f, "
                    "multiplier=%.1f) → spread",
                    current_spread,
                    normal_spread,
                    KILL_SPREAD_MULTIPLIER,
                )
                return "spread"

            # 全条件クリア
            return None

        except Exception as e:
            # 例外発生時は安全側に倒す（手動解除強制で安全を確保）
            logger.error(
                "キルスイッチ評価中に例外が発生しました。安全のため取引を停止します "
                "（手動解除が必要です）: %s",
                e,
                exc_info=True,
            )
            return "manual"

    # ------------------------------------------------------------------
    # 1. ポジションサイジング
    # ------------------------------------------------------------------

    def calculate_position_size(
        self,
        balance: float,
        stop_loss_pips: float,
        instrument: str,
    ) -> float:
        """
        1-2%ルールに基づくポジションサイズ（ロット数）を計算する。

        計算式: balance * MAX_RISK_PER_TRADE / stop_loss_pips
        ドローダウンレベルに応じた制限を適用する。

        Args:
            balance: 口座残高（円）
            stop_loss_pips: 損切り幅（pips）
            instrument: 通貨ペア（例: "USD_JPY"）

        Returns:
            ロット数（0以上）。取引不可時は 0.0。

        Raises:
            ValueError: balance または stop_loss_pips が不正な場合
        """
        if balance <= 0:
            raise ValueError(f"口座残高は正の値である必要があります: {balance}")
        if stop_loss_pips <= 0:
            raise ValueError(
                f"損切り幅(pips)は正の値である必要があります: {stop_loss_pips}"
            )

        # 現在のドローダウンレベルを確認
        drawdown_rate, level_name, _ = self.check_drawdown(
            balance, self._peak_balance
        )

        # STOP / EMERGENCY レベルでは取引不可
        if level_name in ("STOP", "EMERGENCY"):
            logger.warning(
                "ドローダウンレベル %s のため取引停止中: instrument=%s",
                level_name,
                instrument,
            )
            return 0.0

        # 基本ロット計算: リスク金額 / (SL pips * 1pipあたりの金額)
        pip_value = self._get_pip_value(instrument)
        risk_amount = balance * MAX_RISK_PER_TRADE
        lot_size = risk_amount / (stop_loss_pips * pip_value)

        # ドローダウンレベルに応じた制限
        if level_name == "REDUCE":
            # 10%ドローダウン: ポジションサイズを半減
            lot_size *= 0.5
            logger.info(
                "ドローダウン REDUCE レベル: ポジションサイズを半減 -> %.2f",
                lot_size,
            )
        elif level_name == "MINIMUM":
            # 15%ドローダウン: 最小ロット（0.01ロット = 1,000通貨相当）
            minimum_lot = 0.01
            lot_size = minimum_lot
            logger.info(
                "ドローダウン MINIMUM レベル: 最小ロット %.2f に制限",
                minimum_lot,
            )

        # 負の値にはならないが念のため
        lot_size = max(lot_size, 0.0)

        logger.info(
            "ポジションサイズ計算完了: instrument=%s, balance=%.0f, "
            "sl_pips=%.1f, lot_size=%.4f, drawdown_level=%s",
            instrument,
            balance,
            stop_loss_pips,
            lot_size,
            level_name or "NORMAL",
        )
        return lot_size

    # ------------------------------------------------------------------
    # 2. ドローダウン制御
    # ------------------------------------------------------------------

    def check_drawdown(
        self,
        current_balance: float,
        peak_balance: float,
    ) -> tuple[float, Optional[str], Optional[str]]:
        """
        ドローダウン率と該当レベルを判定する。

        ドローダウン率 = (peak - current) / peak
        5段階の閾値を上位から判定し、最も厳しいレベルを返す。

        Args:
            current_balance: 現在の口座残高
            peak_balance: 最高残高

        Returns:
            (drawdown_rate, level_name, action) のタプル。
            該当レベルがなければ level_name と action は None。

        Raises:
            ValueError: peak_balance が0以下の場合
        """
        if peak_balance <= 0:
            raise ValueError(
                f"最高残高は正の値である必要があります: {peak_balance}"
            )

        # ドローダウン率の計算
        if current_balance >= peak_balance:
            return (0.0, None, None)

        drawdown_rate = (peak_balance - current_balance) / peak_balance

        # アクション定義（レベル名 -> アクション説明）
        action_map: dict[str, str] = {
            "WARNING": "警告通知を送信",
            "REDUCE": "ポジションサイズを半減",
            "MINIMUM": "最小ロットのみ許可",
            "STOP": "新規取引を全停止",
            "EMERGENCY": "全ポジションを強制決済",
        }

        # 閾値を降順（厳しい順）にチェック
        matched_level: Optional[str] = None
        for threshold in sorted(DRAWDOWN_LEVELS.keys(), reverse=True):
            if drawdown_rate >= threshold:
                matched_level = DRAWDOWN_LEVELS[threshold]
                break

        if matched_level is not None:
            action = action_map.get(matched_level, "不明なアクション")
            logger.warning(
                "ドローダウン検出: rate=%.2f%%, level=%s, action=%s",
                drawdown_rate * 100,
                matched_level,
                action,
            )
            return (drawdown_rate, matched_level, action)

        return (drawdown_rate, None, None)

    # ------------------------------------------------------------------
    # 3. 損失上限チェック
    # ------------------------------------------------------------------

    def check_loss_limits(
        self,
        trade_history: list[dict],
    ) -> tuple[bool, Optional[str]]:
        """
        日次・週次・月次の損失上限をチェックする。

        trade_history の各要素は {"pl": float, "close_time": datetime} を含む。
        損失合計を口座残高比で計算し、上限超過時は取引停止を返す。

        Args:
            trade_history: 取引履歴リスト

        Returns:
            (is_allowed, reason) のタプル。
            is_allowed=True なら取引許可、False なら停止。
            reason は停止理由（許可時は None）。
        """
        # 安全チェックでの例外は取引停止に倒す（C2: 安全側フォールバック）
        try:
            return self._check_loss_limits_inner(trade_history)
        except (KeyError, TypeError) as e:
            logger.error(
                "損失上限チェック中にデータ不正を検出。安全のため取引を停止します: %s", e
            )
            return (False, f"損失上限チェック中のデータ不正: {e}")

    def _check_loss_limits_inner(
        self,
        trade_history: list[dict],
    ) -> tuple[bool, Optional[str]]:
        """check_loss_limits の内部実装。"""
        now = datetime.now(timezone.utc)

        # 監査B8: 日次は KillSwitch.should_auto_deactivate と同じカレンダーUTC日境界を使う
        # （ローリング24h だと境界が曖昧で「日次キル発動 → 翌0:00で解除 → check_loss_limits は
        # まだ23時間枠で再ブロック」という不整合が起きるため）
        day_start = datetime(
            now.year, now.month, now.day, tzinfo=timezone.utc,
        )
        # 週次・月次は性質的にローリング（運用要件として直近の累積損失を見る）
        week_start = now - timedelta(weeks=1)
        month_start = now - timedelta(days=30)

        # 各期間の損失を集計（plが負の取引のみ）
        daily_loss = 0.0
        weekly_loss = 0.0
        monthly_loss = 0.0

        for trade in trade_history:
            pl = trade["pl"]
            close_time = trade["close_time"]

            # H3: naive datetime はUTCと仮定して変換
            if close_time.tzinfo is None:
                close_time = close_time.replace(tzinfo=timezone.utc)

            # 負のPL（損失）のみ集計
            if pl < 0:
                if close_time >= day_start:
                    daily_loss += abs(pl)
                if close_time >= week_start:
                    weekly_loss += abs(pl)
                if close_time >= month_start:
                    monthly_loss += abs(pl)

        # H5: 口座残高が0以下の場合は即座に取引停止
        balance = self._account_balance
        if balance <= 0:
            reason = f"口座残高が不正です（{balance}円）。取引を停止します。"
            logger.error(reason)
            return (False, reason)

        daily_loss_rate = daily_loss / balance
        weekly_loss_rate = weekly_loss / balance
        monthly_loss_rate = monthly_loss / balance

        # 上限チェック（厳しい順にチェック）
        if monthly_loss_rate >= MAX_MONTHLY_LOSS:
            reason = (
                f"月次損失上限に到達: {monthly_loss_rate:.2%} "
                f"(上限: {MAX_MONTHLY_LOSS:.2%})"
            )
            logger.warning("取引停止: %s", reason)
            return (False, reason)

        if weekly_loss_rate >= MAX_WEEKLY_LOSS:
            reason = (
                f"週次損失上限に到達: {weekly_loss_rate:.2%} "
                f"(上限: {MAX_WEEKLY_LOSS:.2%})"
            )
            logger.warning("取引停止: %s", reason)
            return (False, reason)

        if daily_loss_rate >= MAX_DAILY_LOSS:
            reason = (
                f"日次損失上限に到達: {daily_loss_rate:.2%} "
                f"(上限: {MAX_DAILY_LOSS:.2%})"
            )
            logger.warning("取引停止: %s", reason)
            return (False, reason)

        logger.debug(
            "損失上限チェック通過: daily=%.2f%%, weekly=%.2f%%, monthly=%.2f%%",
            daily_loss_rate * 100,
            weekly_loss_rate * 100,
            monthly_loss_rate * 100,
        )
        return (True, None)

    # ------------------------------------------------------------------
    # 4. 連続負けカウンター
    # ------------------------------------------------------------------

    def check_consecutive_losses(
        self,
        trade_history: list[dict],
    ) -> tuple[int, bool]:
        """
        直近の連続負け数をカウントし、上限超過で停止判定する。

        trade_history は close_time の昇順であることを前提とする。
        MAX_CONSECUTIVE_LOSSES（5）連敗で24時間停止。

        Args:
            trade_history: 取引履歴リスト。各要素は {"pl": float, ...}。

        Returns:
            (consecutive_count, is_stopped) のタプル。
            consecutive_count: 直近の連続負け数。
            is_stopped: True なら取引停止。
        """
        # 安全チェックでの例外は取引停止に倒す（C3: 安全側フォールバック）
        try:
            return self._check_consecutive_losses_inner(trade_history)
        except (KeyError, TypeError) as e:
            logger.error(
                "連続負けチェック中にデータ不正を検出。安全のため取引を停止します: %s", e
            )
            return (0, True)

    def _check_consecutive_losses_inner(
        self,
        trade_history: list[dict],
    ) -> tuple[int, bool]:
        """check_consecutive_losses の内部実装。"""
        consecutive_count = 0

        # 直近から遡ってカウント
        for trade in reversed(trade_history):
            if trade["pl"] < 0:
                consecutive_count += 1
            else:
                # 勝ちまたは引き分け（pl >= 0）で連続負けが途切れる
                break

        is_stopped = consecutive_count >= MAX_CONSECUTIVE_LOSSES

        if is_stopped:
            logger.warning(
                "連続負け上限到達: %d 連敗 (上限: %d)。24時間取引停止。",
                consecutive_count,
                MAX_CONSECUTIVE_LOSSES,
            )
        else:
            logger.debug(
                "連続負けチェック通過: %d 連敗 (上限: %d)",
                consecutive_count,
                MAX_CONSECUTIVE_LOSSES,
            )

        return (consecutive_count, is_stopped)

    # ------------------------------------------------------------------
    # 5. レバレッジチェック
    # ------------------------------------------------------------------

    def check_leverage(
        self,
        total_position_value: float,
        account_balance: float,
    ) -> tuple[float, bool]:
        """
        実効レバレッジをチェックする。

        実効レバレッジ = total_position_value / account_balance
        MAX_LEVERAGE（10倍）を超過する場合は取引不可。

        Args:
            total_position_value: 総ポジション価値
            account_balance: 口座残高

        Returns:
            (effective_leverage, is_allowed) のタプル。
            is_allowed=True なら取引許可。

        Raises:
            ValueError: account_balance が0以下の場合
        """
        if account_balance <= 0:
            raise ValueError(
                f"口座残高は正の値である必要があります: {account_balance}"
            )

        effective_leverage = total_position_value / account_balance
        is_allowed = effective_leverage <= MAX_LEVERAGE

        if not is_allowed:
            logger.warning(
                "レバレッジ超過: 実効レバレッジ=%.2f倍 (上限: %d倍)",
                effective_leverage,
                MAX_LEVERAGE,
            )
        else:
            logger.debug(
                "レバレッジチェック通過: 実効レバレッジ=%.2f倍 (上限: %d倍)",
                effective_leverage,
                MAX_LEVERAGE,
            )

        return (effective_leverage, is_allowed)

    # ------------------------------------------------------------------
    # 6. pip値取得（通貨ペア依存）
    # ------------------------------------------------------------------

    # フォールバック値（broker 取得失敗時のみ使用、CRITICAL ログ + できれば通知）
    # 旧来の単一定数 12.0 は USD≈120 円時代の値で、現代相場 (USD≈156) では
    # 23% 過小評価 → ロット過大計算リスク。決済通貨別に最近相場を反映する。
    # 値は 2026-05 時点の参考レンジ。クォート通貨でルックアップする。
    _FALLBACK_PIP_VALUE_JPY = 10.0
    _FALLBACK_QUOTE_TO_JPY: dict[str, float] = {
        "USD": 156.0,
        "EUR": 170.0,
        "GBP": 195.0,
        "AUD": 100.0,
        "NZD": 90.0,
        "CHF": 175.0,
        "CAD": 110.0,
    }
    # 上記辞書にもない場合の最終 fallback（USD 同等を仮定）
    _FALLBACK_PIP_VALUE_NON_JPY_DEFAULT = 0.0001 * 1000 * 156.0  # = 15.6

    def _fallback_pip_value_non_jpy(self, quote_currency: str, lot_size: int) -> float:
        """フォールバック pip_value を計算する。CRITICAL ログを記録。

        優先順位:
          1. _live_jpy_rate_cache (直近成功した quote→JPY レート)
          2. _FALLBACK_QUOTE_TO_JPY (静的デフォルト)
          3. _FALLBACK_PIP_VALUE_NON_JPY_DEFAULT (最終フォールバック)
        """
        cached = self._live_jpy_rate_cache.get(quote_currency)
        if cached is not None:
            value = 0.0001 * lot_size * cached
            logger.critical(
                "pip_value フォールバック発動（キャッシュ使用）: "
                "quote=%s, cached_jpy_rate=%.3f, pip_value=%.2f",
                quote_currency, cached, value,
            )
            return value

        rate = self._FALLBACK_QUOTE_TO_JPY.get(quote_currency)
        if rate is not None:
            value = 0.0001 * lot_size * rate
            logger.critical(
                "pip_value フォールバック発動（静的デフォルト使用）: "
                "quote=%s, fallback_jpy_rate=%.1f, pip_value=%.2f。"
                "broker からのレート取得不能 — 監視要。",
                quote_currency, rate, value,
            )
            return value

        logger.critical(
            "pip_value 最終フォールバック発動: quote=%s が未登録、"
            "USD 同等値 %.2f を使用。ロット計算が不正確な可能性大。",
            quote_currency, self._FALLBACK_PIP_VALUE_NON_JPY_DEFAULT,
        )
        return self._FALLBACK_PIP_VALUE_NON_JPY_DEFAULT

    def _get_pip_value(self, instrument: str, lot_size: int = 1000) -> float:
        """
        通貨ペアごとの1pipあたりの金額（円建て）を動的に計算する。

        返却値は lot_size 通貨単位あたりの1pip金額（円建て）。
        calculate_position_size() では lot_size=1000（1ロット=1,000通貨）基準で呼ばれる。

        JPYクロス: 0.01 * lot_size（例: 1,000通貨 → 10円/pip）
        非JPYペア: 0.0001 * lot_size * 決済通貨JPYレート
          - 決済通貨はペア後半3文字（例: EUR_USD → USD）
          - 決済通貨JPYレートをbroker_clientから取得

        broker_client未設定またはレート取得失敗時はPhase 1固定値にフォールバック。

        Args:
            instrument: 通貨ペア（例: "USD_JPY", "EUR_USD"）。
                        形式は "XXX_YYY"（アンダースコア区切り、各3文字）。
            lot_size: ロットサイズ（通貨単位、デフォルト1000）

        Returns:
            1pip当たりの金額（円建て、lot_size通貨単位基準）
        """
        is_jpy_cross = "JPY" in instrument.upper()

        if is_jpy_cross:
            # JPYクロス: 0.01 * lot_size（ブローカー不要）
            pip_value = 0.01 * lot_size
            logger.debug(
                "pip_value計算（JPYクロス）: instrument=%s, lot_size=%d, pip_value=%.2f",
                instrument, lot_size, pip_value,
            )
            return pip_value

        # --- 非JPYペア: 決済通貨のJPYレートが必要 ---

        # 決済通貨を特定（ペア後半3文字: EUR_USD → USD）
        parts = instrument.upper().replace(" ", "").split("_")
        if len(parts) != 2 or len(parts[1]) < 3:
            logger.warning(
                "通貨ペアフォーマットが不正: %s。フォールバック値を使用。",
                instrument,
            )
            return self._fallback_pip_value_non_jpy("USD", lot_size)

        quote_currency = parts[1][:3]
        rate_instrument = f"{quote_currency}_JPY"

        # broker_client未設定 → フォールバック
        if self._broker_client is None:
            logger.debug(
                "broker_client未設定のためフォールバック使用: instrument=%s, quote=%s",
                instrument, quote_currency,
            )
            return self._fallback_pip_value_non_jpy(quote_currency, lot_size)

        try:
            # ブローカーから最新レートを取得（M1足1本）
            df = self._broker_client.get_prices(rate_instrument, 1, "M1")
            jpy_rate = float(df["close"].iloc[-1])

            # 異常値チェック: レートが0以下は無効
            if jpy_rate <= 0:
                logger.error(
                    "取得した為替レートが異常値（0以下）: %s = %.6f。フォールバック使用。",
                    rate_instrument, jpy_rate,
                )
                return self._fallback_pip_value_non_jpy(quote_currency, lot_size)

            # 成功時はキャッシュ更新（次回フォールバック時に最新値を使える）
            self._live_jpy_rate_cache[quote_currency] = jpy_rate

            pip_value = 0.0001 * lot_size * jpy_rate
            logger.debug(
                "pip_value計算（非JPY）: instrument=%s, lot_size=%d, "
                "%s=%.4f, pip_value=%.2f",
                instrument, lot_size, rate_instrument, jpy_rate, pip_value,
            )
            return pip_value

        except Exception as e:
            # レート取得失敗 → フォールバック + WARNING（スタックトレース付き）
            logger.warning(
                "為替レート取得失敗。フォールバック使用: instrument=%s, "
                "rate_instrument=%s, error=%s",
                instrument, rate_instrument, e,
                exc_info=True,
            )
            return self._fallback_pip_value_non_jpy(quote_currency, lot_size)
