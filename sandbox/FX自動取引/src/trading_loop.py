"""
FX自動取引システム — トレーディングループモジュール

メインのトレーディングループを管理する。
各イテレーションで残高取得・キルスイッチ評価・ブローカー同期・
シグナル生成・注文発注を順番に実行する。
SPEC_phase2.md F13 準拠。
"""

import logging
import time
from typing import Optional

import pandas as pd
import pandas_ta as ta

from src.ai_advisor import AIAdvisor
from src.bear_researcher import BearResearcher
from src.broker_client import BrokerClient
from src.config import ATR_PERIOD, BEAR_RESEARCHER_ENABLED, MAIN_TIMEFRAME
from src.conviction_scorer import ConvictionScorer
from src.position_manager import PositionManager
from src.regime_detector import RegimeDetector
from src.risk_manager import RiskManager
from src.slack_notifier import SlackNotifier
from src.strategy.base import Signal, StrategyBase
from src.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)


class TradingLoopError(Exception):
    """トレーディングループ固有のエラー"""


class TradingLoop:
    """
    メインのトレーディングループ。

    ブローカー接続・リスク管理・戦略を統合し、
    一定間隔でシグナル生成→注文発注を繰り返す。
    キルスイッチとの連動により、異常時の自動停止・自動解除を行う。
    """

    def __init__(
        self,
        broker_client: BrokerClient,
        position_manager: PositionManager,
        risk_manager: RiskManager,
        strategy: StrategyBase,
        instrument: str = "USD_JPY",
        granularity: str = MAIN_TIMEFRAME,
        check_interval_sec: int = 60,
        max_consecutive_errors: int = 10,
        notifier: Optional[TelegramNotifier] = None,
        ai_advisor: Optional[AIAdvisor] = None,
        slack_notifier: Optional[SlackNotifier] = None,
        bear_researcher: Optional[BearResearcher] = None,
    ) -> None:
        """
        Args:
            broker_client: ブローカークライアント（価格データ・口座情報取得）
            position_manager: ポジション管理（オープン・クローズ・同期）
            risk_manager: リスク管理（キルスイッチ・ポジションサイジング）
            strategy: 取引戦略（シグナル生成）
            instrument: 取引対象の通貨ペア
            granularity: メインタイムフレーム
            check_interval_sec: イテレーション間の待機秒数
            max_consecutive_errors: 連続エラー許容回数（超過でループ停止）

        Raises:
            ValueError: check_interval_sec が0以下の場合
            ValueError: max_consecutive_errors が1未満の場合
        """
        if check_interval_sec <= 0:
            raise ValueError(
                f"check_interval_sec は正の値である必要があります: {check_interval_sec}"
            )
        if max_consecutive_errors < 1:
            raise ValueError(
                f"max_consecutive_errors は1以上である必要があります: "
                f"{max_consecutive_errors}"
            )

        self._broker_client = broker_client
        self._position_manager = position_manager
        self._risk_manager = risk_manager
        self._strategy = strategy
        self._instrument = instrument
        self._granularity = granularity
        self._check_interval_sec = check_interval_sec
        self._max_consecutive_errors = max_consecutive_errors

        self._notifier = notifier
        self._ai_advisor = ai_advisor
        self._slack_notifier = slack_notifier
        self._bear_researcher = bear_researcher

        self._running: bool = False
        self._iteration_count: int = 0
        self._last_error: Optional[str] = None
        self._consecutive_error_count: int = 0

        # 前回イテレーションのATR/spread情報（キルスイッチ評価用キャッシュ）
        self._last_atr: Optional[float] = None
        self._normal_atr: Optional[float] = None
        self._last_spread: Optional[float] = None
        self._normal_spread: Optional[float] = None

        # Phase 3: レジーム検出 + conviction score
        self._regime_detector = RegimeDetector()
        self._conviction_scorer = ConvictionScorer()

    # ------------------------------------------------------------------
    # メインループ制御
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        無限ループを開始する。

        KeyboardInterrupt または stop() で安全に停止する。
        各イテレーションで run_once() を呼び出し、
        check_interval_sec 秒待機する。
        連続エラーが max_consecutive_errors を超過するとループを自動停止する。
        """
        self._running = True
        logger.info(
            "トレーディングループ開始: instrument=%s, granularity=%s, "
            "interval=%ds, max_errors=%d",
            self._instrument,
            self._granularity,
            self._check_interval_sec,
            self._max_consecutive_errors,
        )

        try:
            while self._running:
                try:
                    self.run_once()
                    # 正常完了 → 連続エラーカウントをリセット
                    self._consecutive_error_count = 0
                except Exception as e:
                    self._consecutive_error_count += 1
                    self._last_error = str(e)
                    logger.error(
                        "イテレーションエラー (%d/%d): %s",
                        self._consecutive_error_count,
                        self._max_consecutive_errors,
                        e,
                        exc_info=True,
                    )

                    # 3回以上の連続エラーで通知
                    if self._consecutive_error_count >= 3:
                        error_msg = self._last_error or "不明なエラー"
                        if self._notifier:
                            self._notifier.notify_error(
                                error_msg, self._consecutive_error_count,
                            )
                        if self._slack_notifier:
                            self._slack_notifier.notify_error(
                                error_msg, self._consecutive_error_count,
                            )

                    # 連続エラー上限超過でループ停止
                    if self._consecutive_error_count > self._max_consecutive_errors:
                        logger.critical(
                            "連続エラーが上限(%d)を超過しました。"
                            "トレーディングループを緊急停止します。",
                            self._max_consecutive_errors,
                        )
                        self._running = False
                        break

                # ループ中かつ次のイテレーションまで待機
                if self._running:
                    time.sleep(self._check_interval_sec)

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt を受信。トレーディングループを停止します。")
        finally:
            self._running = False
            logger.info(
                "トレーディングループ停止: total_iterations=%d",
                self._iteration_count,
            )

    def stop(self) -> None:
        """ループを安全に停止する。"""
        logger.info("トレーディングループの停止を要求しました。")
        self._running = False

    # ------------------------------------------------------------------
    # 1イテレーション
    # ------------------------------------------------------------------

    def run_once(self) -> Optional[dict]:
        """
        ループの1イテレーションを実行する。

        処理手順:
        1. 口座残高取得 → risk_manager.update_balance()
        2. evaluate_kill_switch() でキルスイッチ判定
           - 理由あり → kill_switch.activate(reason)
           - EMERGENCY レベルなら position_manager.close_all_positions()
        3. キルスイッチ発動中なら should_auto_deactivate() で解除判定
           - 解除条件満たす → deactivate()
           - そうでなければ新規取引スキップ
        4. position_manager.sync_with_broker()
        5. broker_client.get_prices(instrument, 100, granularity)
        6. strategy.generate_signal(data)
        7. BUY/SELL → position_manager.open_position()
        8. iteration_count += 1

        Returns:
            注文結果dict（取引実行時）。取引なしの場合は None。

        Raises:
            各ステップで発生した例外はそのまま上位に伝播する。
        """
        order_result: Optional[dict] = None

        # 1. 口座残高の取得・更新
        account_summary = self._broker_client.get_account_summary()
        current_balance = account_summary["balance"]
        self._risk_manager.update_balance(current_balance)

        # 2. キルスイッチ総合評価（前回イテレーションのATR/spreadを使用）
        trade_history = self._position_manager.trade_history
        kill_reason = self._risk_manager.evaluate_kill_switch(
            current_balance=current_balance,
            trade_history=trade_history,
            current_atr=self._last_atr,
            normal_atr=self._normal_atr,
            current_spread=self._last_spread,
            normal_spread=self._normal_spread,
        )

        if kill_reason is not None:
            # キルスイッチ発動
            if not self._risk_manager.kill_switch.is_active:
                self._risk_manager.kill_switch.activate(kill_reason)
                if self._notifier:
                    self._notifier.notify_kill_switch(kill_reason, True)
                if self._slack_notifier:
                    self._slack_notifier.notify_kill_switch(kill_reason, True)

            # EMERGENCY レベルなら全ポジション強制決済
            _, level_name, _ = self._risk_manager.check_drawdown(
                current_balance, self._risk_manager.peak_balance
            )
            if level_name == "EMERGENCY":
                logger.critical(
                    "EMERGENCY ドローダウン検出: 全ポジション強制決済を実行します。"
                )
                self._position_manager.close_all_positions(
                    reason="EMERGENCY ドローダウン"
                )

        # 3. キルスイッチ発動中の処理
        if self._risk_manager.kill_switch.is_active:
            # 自動解除判定
            if self._risk_manager.kill_switch.should_auto_deactivate():
                logger.info(
                    "キルスイッチ自動解除条件を満たしました: reason=%s",
                    self._risk_manager.kill_switch.reason,
                )
                self._risk_manager.kill_switch.deactivate()
                if self._notifier:
                    self._notifier.notify_kill_switch("自動解除", False)
                if self._slack_notifier:
                    self._slack_notifier.notify_kill_switch("自動解除", False)
            else:
                # 解除条件を満たさない → 新規取引スキップ
                logger.info(
                    "キルスイッチ発動中のため新規取引をスキップ: reason=%s",
                    self._risk_manager.kill_switch.reason,
                )
                self._iteration_count += 1
                return None

        # 4. ブローカーとのポジション同期
        self._position_manager.sync_with_broker()

        # 5. 価格データ取得
        data = self._broker_client.get_prices(
            self._instrument, 100, self._granularity
        )

        # 5b. ATR/spreadキャッシュ更新（次回イテレーションのキルスイッチ評価用）
        if len(data) >= ATR_PERIOD + 1:
            atr_series = ta.atr(
                data["high"], data["low"], data["close"], length=ATR_PERIOD
            )
            if atr_series is not None and not atr_series.empty:
                current_atr = atr_series.iloc[-1]
                if not pd.isna(current_atr):
                    self._last_atr = float(current_atr)
                    # 通常ATR = 全期間の中央値（安定した基準値）
                    valid_atr = atr_series.dropna()
                    if len(valid_atr) > 0:
                        self._normal_atr = float(valid_atr.median())

        # 5c. spreadキャッシュ更新（キルスイッチのスプレッド監視用）
        try:
            current_spread = self._broker_client.get_spread(self._instrument)
            if current_spread is not None and current_spread >= 0:
                self._last_spread = current_spread
                if self._normal_spread is None:
                    # 初回: 現在値を通常値として設定
                    self._normal_spread = current_spread
                else:
                    # EMA（α=0.1）で通常値を更新（急変を平滑化）
                    alpha = 0.1
                    self._normal_spread = (
                        (1 - alpha) * self._normal_spread
                        + alpha * current_spread
                    )
        except Exception as e:
            logger.debug(
                "スプレッド取得失敗（前回値を継続使用）: %s", e
            )

        # 6. レジーム検出（Phase 3）
        regime_info = self._regime_detector.detect(data)
        logger.info(
            "レジーム判定: %s (確信度=%.2f, エクスポージャー=%.1f, ADX=%.1f)",
            regime_info.regime.value,
            regime_info.confidence,
            regime_info.exposure_multiplier,
            regime_info.adx,
        )

        # レジームがVOLATILEなら取引停止
        if regime_info.exposure_multiplier == 0.0:
            logger.warning(
                "高ボラティリティ検出（ATR比率=%.2f）。新規取引を停止。",
                regime_info.atr_ratio,
            )
            self._iteration_count += 1
            return None

        # 7. シグナル生成
        signal = self._strategy.generate_signal(data)

        # 8. BUY/SELL シグナルなら conviction score で評価
        if signal in (Signal.BUY, Signal.SELL):
            conviction = self._conviction_scorer.score(data, signal, regime_info)
            logger.info(
                "conviction score: %d/10 (倍率=%.1f, 取引=%s) — %s",
                conviction.score,
                conviction.position_size_multiplier,
                conviction.should_trade,
                conviction.reasoning,
            )

            if not conviction.should_trade:
                logger.info(
                    "conviction不足（%d < 閾値）。シグナル %s を見送り。",
                    conviction.score,
                    signal.value,
                )
            else:
                # エクスポージャー倍率 = レジーム倍率 × conviction倍率
                combined_multiplier = (
                    regime_info.exposure_multiplier
                    * conviction.position_size_multiplier
                )

                # AIフィルター適用（AIは最終判断しない、倍率調整のみ）
                ai_eval = "N/A"
                if self._ai_advisor:
                    bias = self._ai_advisor.get_bias(self._instrument)
                    if bias:
                        ai_eval = bias.evaluate_signal(signal.value)
                        ai_multiplier = bias.position_size_multiplier(ai_eval)
                        logger.info(
                            "AIフィルター: %s (direction=%s, confidence=%.2f) → 倍率%.2f",
                            ai_eval, bias.direction, bias.confidence, ai_multiplier,
                        )
                        if ai_eval == "REJECT":
                            logger.warning(
                                "AIフィルター: REJECT（%s）。シグナルを見送り。",
                                bias.reasoning,
                            )
                            self._iteration_count += 1
                            return None
                        combined_multiplier *= ai_multiplier

                # Bear Researcher: 逆張り検証（テクニカル矛盾点の検出）
                if self._bear_researcher:
                    bear_verdict = self._bear_researcher.verify(
                        data, signal, regime_info,
                    )
                    if bear_verdict.severity >= 0.4:
                        logger.warning(
                            "Bear Researcher警告: severity=%.2f, penalty=%.2f, リスク=%s",
                            bear_verdict.severity,
                            bear_verdict.penalty_multiplier,
                            bear_verdict.risk_factors,
                        )
                        combined_multiplier *= bear_verdict.penalty_multiplier

                logger.info(
                    "シグナル実行: %s, instrument=%s, "
                    "ポジションサイズ倍率=%.2f (レジーム%.1f × conviction%.1f × AI=%s)",
                    signal.value,
                    self._instrument,
                    combined_multiplier,
                    regime_info.exposure_multiplier,
                    conviction.position_size_multiplier,
                    ai_eval,
                )
                if self._notifier:
                    self._notifier.notify_signal(self._instrument, signal.value)
                if self._slack_notifier:
                    self._slack_notifier.notify_signal(
                        self._instrument,
                        signal.value,
                        conviction_score=conviction.score,
                        regime=regime_info.regime.value,
                    )
                order_result = self._position_manager.open_position(
                    instrument=self._instrument,
                    signal=signal,
                    data=data,
                    strategy=self._strategy,
                )
        else:
            logger.debug(
                "HOLDシグナル: instrument=%s, iteration=%d",
                self._instrument,
                self._iteration_count + 1,
            )

        # 8. イテレーションカウント更新
        self._iteration_count += 1

        return order_result

    # ------------------------------------------------------------------
    # プロパティ
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """ループが実行中かどうか"""
        return self._running

    @property
    def iteration_count(self) -> int:
        """完了したイテレーション数"""
        return self._iteration_count

    @property
    def last_error(self) -> Optional[str]:
        """最後に発生したエラーメッセージ。エラーなしの場合は None。"""
        return self._last_error
