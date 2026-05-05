"""
F13: trading_loop.py のユニットテスト

トレーディングループの1イテレーション実行、キルスイッチ連動、
エラーハンドリング、ループ制御を検証する。
SPEC_phase2.md F13 完了基準準拠。
"""

import logging
import threading
import time
from unittest.mock import MagicMock, PropertyMock, patch

import pandas as pd
import pytest

from src.broker_client import BrokerClient
from src.position_manager import PositionManager
from src.risk_manager import KillSwitch, RiskManager
from src.strategy.base import Signal, StrategyBase
from src.trading_loop import TradingLoop, TradingLoopError


# T4導入後の互換: 既存テストはセッション時間外でも実行されるため
# is_in_allowed_session を常時 True にパッチする。
# ペア別ADX閾値も既存テストでは0として無効化する。
@pytest.fixture(autouse=True)
def _bypass_t4_filters():
    fake_pair_cfg = {
        "allowed_sessions": [],
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "adx_threshold": 0,  # 既存テストではADX閾値を無効化
        "atr_sl_mult": 2.0,
        "atr_tp1_mult": 1.0,
        "atr_tp2_mult": 3.0,
    }
    with patch("src.trading_loop.is_in_allowed_session", return_value=True), \
         patch("src.trading_loop.get_active_session_label", return_value="TEST"), \
         patch("src.trading_loop.get_pair_config", return_value=fake_pair_cfg):
        yield


# ============================================================
# テスト用ヘルパー
# ============================================================


def _make_ohlcv_data(close_price: float = 150.0, rows: int = 100) -> pd.DataFrame:
    """テスト用のOHLCVデータを生成する。"""
    data = {
        "open": [close_price] * rows,
        "high": [close_price + 0.5] * rows,
        "low": [close_price - 0.5] * rows,
        "close": [close_price] * rows,
        "volume": [1000] * rows,
    }
    return pd.DataFrame(data)


def _make_mock_broker() -> MagicMock:
    """モック化されたBrokerClientを生成する。"""
    broker = MagicMock(spec=BrokerClient)
    broker.get_account_summary.return_value = {"balance": 1_000_000}
    broker.get_prices.return_value = _make_ohlcv_data()
    broker.get_positions.return_value = []
    broker.market_order.return_value = {
        "order_id": "ORD-001",
        "trade_id": "TRD-001",
        "price": 150.0,
        "units": 1000,
        "status": "filled",
    }
    return broker


def _make_mock_position_manager() -> MagicMock:
    """モック化されたPositionManagerを生成する。"""
    pm = MagicMock(spec=PositionManager)
    pm.trade_history = []
    pm.position_count = 0
    pm.sync_with_broker.return_value = {
        "synced": 0,
        "local_only": [],
        "broker_only": [],
    }
    pm.open_position.return_value = {
        "order_id": "ORD-001",
        "trade_id": "TRD-001",
        "price": 150.0,
    }
    pm.close_all_positions.return_value = {
        "closed": [],
        "failed": [],
        "total": 0,
    }
    return pm


def _make_mock_risk_manager() -> MagicMock:
    """モック化されたRiskManagerを生成する。"""
    rm = MagicMock(spec=RiskManager)

    # キルスイッチ: デフォルトで未発動
    kill_switch = MagicMock(spec=KillSwitch)
    kill_switch.is_active = False
    kill_switch.reason = None
    kill_switch.is_trading_allowed.return_value = True
    kill_switch.should_auto_deactivate.return_value = False
    rm.kill_switch = kill_switch

    # キルスイッチ評価: デフォルトで全条件クリア
    rm.evaluate_kill_switch.return_value = None

    # ドローダウンチェック: デフォルトで正常
    rm.check_drawdown.return_value = (0.01, None, None)

    # ピーク残高
    rm.peak_balance = 1_000_000

    return rm


def _make_mock_strategy(signal: Signal = Signal.BUY) -> MagicMock:
    """モック化されたStrategyBaseを生成する。"""
    strategy = MagicMock(spec=StrategyBase)
    strategy.generate_signal.return_value = signal
    strategy.calculate_stop_loss.return_value = 149.0
    strategy.calculate_take_profit.return_value = 152.0
    return strategy


def _create_trading_loop(
    broker: MagicMock = None,
    position_manager: MagicMock = None,
    risk_manager: MagicMock = None,
    strategy: MagicMock = None,
    instrument: str = "USD_JPY",
    check_interval_sec: int = 60,
    max_consecutive_errors: int = 10,
) -> TradingLoop:
    """テスト用TradingLoopを生成する。"""
    if broker is None:
        broker = _make_mock_broker()
    if position_manager is None:
        position_manager = _make_mock_position_manager()
    if risk_manager is None:
        risk_manager = _make_mock_risk_manager()
    if strategy is None:
        strategy = _make_mock_strategy()

    return TradingLoop(
        broker_client=broker,
        position_manager=position_manager,
        risk_manager=risk_manager,
        strategy=strategy,
        instrument=instrument,
        check_interval_sec=check_interval_sec,
        max_consecutive_errors=max_consecutive_errors,
    )


# ============================================================
# 1. run_once 正常フロー
# ============================================================


class TestRunOnceNormalFlow:
    """run_once の正常フローテスト"""

    def test_run_once_normal_flow(self):
        """正常1イテレーション（BUYシグナル → open_position呼出）"""
        broker = _make_mock_broker()
        pm = _make_mock_position_manager()
        rm = _make_mock_risk_manager()
        strategy = _make_mock_strategy(signal=Signal.BUY)

        loop = _create_trading_loop(
            broker=broker,
            position_manager=pm,
            risk_manager=rm,
            strategy=strategy,
        )

        result = loop.run_once()

        # 残高更新
        rm.update_balance.assert_called_once_with(1_000_000)

        # キルスイッチ評価
        rm.evaluate_kill_switch.assert_called_once()

        # ブローカー同期
        pm.sync_with_broker.assert_called_once()

        # 価格データ取得
        broker.get_prices.assert_called_once()

        # シグナル生成
        strategy.generate_signal.assert_called_once()

        # ポジションオープン
        pm.open_position.assert_called_once()
        call_args = pm.open_position.call_args
        assert call_args.kwargs["instrument"] == "USD_JPY"
        assert call_args.kwargs["signal"] == Signal.BUY

        # 結果が返されること
        assert result is not None
        assert result["trade_id"] == "TRD-001"

        # イテレーションカウント
        assert loop.iteration_count == 1

    def test_run_once_hold_signal(self):
        """HOLDシグナル → open_position未呼出"""
        pm = _make_mock_position_manager()
        strategy = _make_mock_strategy(signal=Signal.HOLD)

        loop = _create_trading_loop(
            position_manager=pm,
            strategy=strategy,
        )

        result = loop.run_once()

        # open_position は呼ばれない
        pm.open_position.assert_not_called()

        # 結果はNone
        assert result is None

        # イテレーションカウントは増える
        assert loop.iteration_count == 1


# ============================================================
# 2. キルスイッチ連動テスト
# ============================================================


class TestKillSwitchIntegration:
    """キルスイッチ連動のテスト"""

    def test_run_once_kill_switch_skips(self):
        """キルスイッチ発動中 → 新規取引スキップ"""
        pm = _make_mock_position_manager()
        rm = _make_mock_risk_manager()

        # キルスイッチ発動中（evaluate_kill_switchは新たにdaily_lossを返す）
        rm.evaluate_kill_switch.return_value = "daily_loss"
        rm.kill_switch.is_active = False  # 初回は未発動

        # activate 後は is_active を True にする
        def activate_side_effect(reason):
            rm.kill_switch.is_active = True
            rm.kill_switch.reason = reason
        rm.kill_switch.activate.side_effect = activate_side_effect

        # ドローダウンはSTOP未満（EMERGENCY決済を避ける）
        rm.check_drawdown.return_value = (0.20, "STOP", "新規取引を全停止")

        # should_auto_deactivateはFalse
        rm.kill_switch.should_auto_deactivate.return_value = False

        loop = _create_trading_loop(
            position_manager=pm,
            risk_manager=rm,
        )

        result = loop.run_once()

        # キルスイッチ発動
        rm.kill_switch.activate.assert_called_once_with("daily_loss")

        # 新規取引はスキップ
        pm.open_position.assert_not_called()

        # 結果はNone
        assert result is None

    def test_run_once_emergency_closes_all(self):
        """EMERGENCY → close_all_positions呼出"""
        pm = _make_mock_position_manager()
        rm = _make_mock_risk_manager()

        # キルスイッチ評価: daily_loss
        rm.evaluate_kill_switch.return_value = "daily_loss"
        rm.kill_switch.is_active = False

        def activate_side_effect(reason):
            rm.kill_switch.is_active = True
            rm.kill_switch.reason = reason
        rm.kill_switch.activate.side_effect = activate_side_effect

        # EMERGENCY ドローダウン
        rm.check_drawdown.return_value = (0.25, "EMERGENCY", "全ポジションを強制決済")

        # should_auto_deactivate は False（解除しない）
        rm.kill_switch.should_auto_deactivate.return_value = False

        loop = _create_trading_loop(
            position_manager=pm,
            risk_manager=rm,
        )

        result = loop.run_once()

        # 全ポジション強制決済が呼ばれること
        pm.close_all_positions.assert_called_once()
        call_args = pm.close_all_positions.call_args
        assert "EMERGENCY" in call_args.kwargs.get("reason", call_args.args[0] if call_args.args else "")

        # 新規取引はスキップ
        pm.open_position.assert_not_called()

    def test_run_once_kill_auto_deactivate(self):
        """解除条件成立 → deactivate呼出"""
        pm = _make_mock_position_manager()
        rm = _make_mock_risk_manager()
        strategy = _make_mock_strategy(signal=Signal.BUY)

        # キルスイッチ発動中だが、evaluate_kill_switchはNone（条件クリア）
        rm.evaluate_kill_switch.return_value = None
        rm.kill_switch.is_active = True
        rm.kill_switch.reason = "volatility"

        # 自動解除条件を満たす
        rm.kill_switch.should_auto_deactivate.return_value = True

        # deactivate 後は is_active を False にする
        def deactivate_side_effect():
            rm.kill_switch.is_active = False
            rm.kill_switch.reason = None
        rm.kill_switch.deactivate.side_effect = deactivate_side_effect

        loop = _create_trading_loop(
            position_manager=pm,
            risk_manager=rm,
            strategy=strategy,
        )

        result = loop.run_once()

        # deactivate が呼ばれること
        rm.kill_switch.deactivate.assert_called_once()

        # 解除後は通常フロー → open_position が呼ばれること
        pm.open_position.assert_called_once()


# ============================================================
# 3. エラーハンドリングテスト
# ============================================================


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_run_once_api_error_logs(self):
        """API例外 → last_error にセット、例外は上位に伝播"""
        broker = _make_mock_broker()
        broker.get_account_summary.side_effect = ConnectionError("API接続エラー")

        loop = _create_trading_loop(broker=broker)

        # run_once は例外を上位に伝播する
        with pytest.raises(ConnectionError, match="API接続エラー"):
            loop.run_once()

        # イテレーションカウントは増えない（例外で中断）
        assert loop.iteration_count == 0

    def test_consecutive_errors_stops_loop(self):
        """max_consecutive_errors 超過でループ停止"""
        broker = _make_mock_broker()
        broker.get_account_summary.side_effect = ConnectionError("API接続エラー")

        loop = _create_trading_loop(
            broker=broker,
            check_interval_sec=1,
            max_consecutive_errors=2,
        )

        # start() をバックグラウンドで実行して停止を確認
        # time.sleep のモックで高速化
        with patch("src.trading_loop.time.sleep"):
            loop.start()

        # ループ停止確認
        assert loop.is_running is False

        # last_error に最後のエラーが記録されていること
        assert loop.last_error is not None
        assert "API接続エラー" in loop.last_error


# ============================================================
# 4. ループ制御テスト
# ============================================================


class TestLoopControl:
    """ループ制御のテスト"""

    def test_start_stop(self):
        """start() → stop() で安全に停止"""
        loop = _create_trading_loop(check_interval_sec=1)

        # time.sleepをモックして即時進行
        call_count = 0

        def mock_sleep(sec):
            nonlocal call_count
            call_count += 1
            # 2イテレーション後に停止
            if call_count >= 2:
                loop.stop()

        with patch("src.trading_loop.time.sleep", side_effect=mock_sleep):
            loop.start()

        # ループ停止確認
        assert loop.is_running is False

        # イテレーションが実行されたこと
        assert loop.iteration_count >= 2

    def test_iteration_count(self):
        """run_once 3回で iteration_count == 3"""
        loop = _create_trading_loop()

        loop.run_once()
        loop.run_once()
        loop.run_once()

        assert loop.iteration_count == 3

    def test_balance_update_and_drawdown_check(self):
        """残高更新とDD判定の連動"""
        broker = _make_mock_broker()
        broker.get_account_summary.return_value = {"balance": 900_000}

        rm = _make_mock_risk_manager()
        rm.peak_balance = 1_000_000

        loop = _create_trading_loop(broker=broker, risk_manager=rm)

        loop.run_once()

        # update_balance が新しい残高で呼ばれたこと
        rm.update_balance.assert_called_once_with(900_000)

        # evaluate_kill_switch が正しい残高で呼ばれたこと
        call_args = rm.evaluate_kill_switch.call_args
        assert call_args.kwargs["current_balance"] == 900_000


# ============================================================
# 6. T4: 時間帯フィルター・ペア別パラメータ統合テスト
# ============================================================


class TestT4SessionAndPairFilters:
    """T4: trading_loop 統合 — 時間帯フィルター + ペア別ADX閾値"""

    def test_outside_session_skips_signal(self):
        """時間帯外なら戦略のシグナル生成すら呼ばれずスキップ"""
        pm = _make_mock_position_manager()
        strategy = _make_mock_strategy(signal=Signal.BUY)

        fake_pair_cfg = {
            "allowed_sessions": [{"start": "09:00", "end": "15:00",
                                  "label": "Tokyo"}],
            "rsi_oversold": 30, "rsi_overbought": 70, "adx_threshold": 0,
            "atr_sl_mult": 2.0, "atr_tp1_mult": 1.0, "atr_tp2_mult": 3.0,
        }

        with patch("src.trading_loop.is_in_allowed_session", return_value=False), \
             patch("src.trading_loop.get_pair_config",
                   return_value=fake_pair_cfg):
            loop = TradingLoop(
                broker_client=_make_mock_broker(),
                position_manager=pm,
                risk_manager=_make_mock_risk_manager(),
                strategy=strategy,
                instrument="EUR_USD",
                check_interval_sec=60,
            )
            result = loop.run_once()

        assert result is None
        # 時間帯外なら戦略は呼ばれない
        strategy.generate_signal.assert_not_called()
        pm.open_position.assert_not_called()

    def test_inside_session_proceeds(self):
        """時間帯内なら通常通り戦略まで進む"""
        pm = _make_mock_position_manager()
        strategy = _make_mock_strategy(signal=Signal.BUY)

        fake_pair_cfg = {
            "allowed_sessions": [{"start": "00:00", "end": "23:59",
                                  "label": "ALL"}],
            "rsi_oversold": 30, "rsi_overbought": 70, "adx_threshold": 0,
            "atr_sl_mult": 2.0, "atr_tp1_mult": 1.0, "atr_tp2_mult": 3.0,
        }

        with patch("src.trading_loop.is_in_allowed_session", return_value=True), \
             patch("src.trading_loop.get_pair_config",
                   return_value=fake_pair_cfg):
            loop = TradingLoop(
                broker_client=_make_mock_broker(),
                position_manager=pm,
                risk_manager=_make_mock_risk_manager(),
                strategy=strategy,
                instrument="EUR_USD",
                check_interval_sec=60,
            )
            loop.run_once()

        # 戦略が呼ばれること（時間帯内）
        strategy.generate_signal.assert_called_once()
        # pair_config がkwargsで渡ること
        call_kwargs = strategy.generate_signal.call_args.kwargs
        assert "pair_config" in call_kwargs
        assert call_kwargs["pair_config"]["adx_threshold"] == 0

    def test_pair_adx_threshold_blocks_low_adx_signal(self):
        """ペア別 ADX 閾値が高ければ低ADXシグナルはスキップ"""
        # フラットOHLCV → ADXは0近辺。閾値50 → スキップされる
        pm = _make_mock_position_manager()
        strategy = _make_mock_strategy(signal=Signal.BUY)

        fake_pair_cfg = {
            "allowed_sessions": [{"start": "00:00", "end": "23:59",
                                  "label": "ALL"}],
            "rsi_oversold": 30, "rsi_overbought": 70,
            "adx_threshold": 99.0,  # 実用上絶対超えない値
            "atr_sl_mult": 2.0, "atr_tp1_mult": 1.0, "atr_tp2_mult": 3.0,
        }

        with patch("src.trading_loop.is_in_allowed_session", return_value=True), \
             patch("src.trading_loop.get_pair_config",
                   return_value=fake_pair_cfg):
            loop = TradingLoop(
                broker_client=_make_mock_broker(),
                position_manager=pm,
                risk_manager=_make_mock_risk_manager(),
                strategy=strategy,
                instrument="EUR_USD",
                check_interval_sec=60,
            )
            result = loop.run_once()

        # 戦略は呼ばれるがpair ADXフィルターでブロックされ open されない
        assert result is None


# ============================================================
# 6. パイプライン1行サマリログ（観測性）
# ============================================================


class TestPipelineTraceLog:
    """_signal_pipeline が各ステージの通過/却下を1行 INFO に集約することを検証。

    本番ログから「いま何が起きたか」を読み取れるようにするための観測性機構。
    既存の個別 INFO ログを置き換えるのではなく、サマリ行を追加する形で実装。
    """

    @staticmethod
    def _get_pipeline_lines(caplog) -> list[str]:
        """caplog から `[XXX] pipeline:` で始まる INFO 行のみ抽出する。"""
        return [
            r.getMessage()
            for r in caplog.records
            if r.levelname == "INFO" and "pipeline:" in r.getMessage()
        ]

    def test_execute_emits_pipeline_summary_with_decision(self, caplog):
        """通常のBUY実行時、DECISION=EXECUTE と最終倍率を含むサマリ1行が出る。"""
        caplog.set_level(logging.INFO, logger="src.trading_loop")
        strategy = _make_mock_strategy(signal=Signal.BUY)
        loop = _create_trading_loop(strategy=strategy)

        loop.run_once()

        lines = self._get_pipeline_lines(caplog)
        assert len(lines) == 1, f"サマリは1行のみ期待: {lines}"
        line = lines[0]
        assert "[USD_JPY]" in line
        assert "session=PASS" in line
        assert "regime=" in line
        assert "strategy=BUY" in line
        assert "DECISION=EXECUTE" in line
        assert "mult=" in line

    def test_session_skip_emits_skip_decision(self, caplog):
        """時間帯外なら session=SKIP / DECISION=SKIP の1行で終わる。"""
        caplog.set_level(logging.INFO, logger="src.trading_loop")

        # _bypass_t4_filters fixture を上書きして session を閉じる
        with patch("src.trading_loop.is_in_allowed_session", return_value=False):
            loop = _create_trading_loop()
            loop.run_once()

        lines = self._get_pipeline_lines(caplog)
        assert len(lines) == 1
        line = lines[0]
        assert "session=SKIP" in line
        assert "DECISION=SKIP" in line
        # 後続ステージは記録されない
        assert "regime=" not in line
        assert "strategy=" not in line

    def test_session_skip_does_not_emit_legacy_info(self, caplog):
        """session SKIP 時、旧『時間帯フィルター: 許可セッション外』INFO ログは
        出ない（pipeline サマリと重複するため DEBUG に格下げ済み）。
        """
        caplog.set_level(logging.DEBUG, logger="src.trading_loop")

        with patch("src.trading_loop.is_in_allowed_session", return_value=False):
            loop = _create_trading_loop()
            loop.run_once()

        # INFO レベル以上の旧メッセージは存在しないこと
        info_records = [
            r for r in caplog.records
            if r.levelname == "INFO"
            and "時間帯フィルター" in r.getMessage()
        ]
        assert info_records == [], (
            f"旧『時間帯フィルター』INFO が残存: {[r.getMessage() for r in info_records]}"
        )

        # ただし DEBUG レベルでは引き続き記録されている（深掘り用）
        debug_records = [
            r for r in caplog.records
            if r.levelname == "DEBUG"
            and "時間帯フィルター" in r.getMessage()
        ]
        assert len(debug_records) == 1, (
            "DEBUG レベルの詳細ログは残っているべき"
        )

    def test_strategy_hold_includes_diagnostics_reason(self, caplog):
        """戦略がHOLDかつ last_diagnostics に hold_reason がある場合、その理由がサマリに載る。"""
        caplog.set_level(logging.INFO, logger="src.trading_loop")

        strategy = _make_mock_strategy(signal=Signal.HOLD)
        # 実戦略と同じく last_diagnostics プロパティで HOLD 理由を返す
        type(strategy).last_diagnostics = PropertyMock(
            return_value={"hold_reason": "RSI=52 が押し目水準未達"}
        )

        loop = _create_trading_loop(strategy=strategy)
        loop.run_once()

        lines = self._get_pipeline_lines(caplog)
        assert len(lines) == 1
        line = lines[0]
        assert "strategy=HOLD" in line
        assert "RSI=52 が押し目水準未達" in line
        assert "DECISION=HOLD" in line

    def test_strategy_hold_without_diagnostics_falls_back_to_default(self, caplog):
        """last_diagnostics が None でも 'no signal' フォールバックでサマリが出る。"""
        caplog.set_level(logging.INFO, logger="src.trading_loop")

        strategy = _make_mock_strategy(signal=Signal.HOLD)
        type(strategy).last_diagnostics = PropertyMock(return_value=None)

        loop = _create_trading_loop(strategy=strategy)
        loop.run_once()

        lines = self._get_pipeline_lines(caplog)
        assert len(lines) == 1
        assert "strategy=HOLD" in lines[0]
        assert "no signal" in lines[0]
        assert "DECISION=HOLD" in lines[0]

    def test_pair_adx_reject_emits_reject_decision(self, caplog):
        """ペア別ADX閾値で却下されたら pair_adx=REJECT / DECISION=REJECT が出る。"""
        caplog.set_level(logging.INFO, logger="src.trading_loop")

        # ADX閾値を高めに設定 → 検出ADX(0付近)で必ず却下
        strict_pair_cfg = {
            "allowed_sessions": [],
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "adx_threshold": 99,  # 実質ブロック
            "atr_sl_mult": 2.0,
            "atr_tp1_mult": 1.0,
            "atr_tp2_mult": 3.0,
        }

        strategy = _make_mock_strategy(signal=Signal.BUY)

        with patch(
            "src.trading_loop.get_pair_config", return_value=strict_pair_cfg,
        ):
            loop = _create_trading_loop(strategy=strategy)
            loop.run_once()

        lines = self._get_pipeline_lines(caplog)
        assert len(lines) == 1
        line = lines[0]
        assert "strategy=BUY" in line
        assert "pair_adx=REJECT" in line
        assert "DECISION=REJECT" in line

    def test_pipeline_summary_is_single_line_per_iteration(self, caplog):
        """1イテレーションあたりサマリ行は必ず1行（多重出力されない）。"""
        caplog.set_level(logging.INFO, logger="src.trading_loop")

        loop = _create_trading_loop()
        loop.run_once()
        loop.run_once()
        loop.run_once()

        lines = self._get_pipeline_lines(caplog)
        assert len(lines) == 3, f"3イテレーションで3行のはず: {lines}"

    def test_regime_volatile_emits_skip_decision(self, caplog):
        """VOLATILE 検出（exposure_multiplier=0.0）で regime=SKIP / DECISION=SKIP。"""
        caplog.set_level(logging.INFO, logger="src.trading_loop")

        # RegimeDetector を VOLATILE 相当に差し替え
        fake_regime = MagicMock()
        fake_regime.regime = MagicMock()
        fake_regime.regime.value = "volatile"
        fake_regime.confidence = 0.95
        fake_regime.exposure_multiplier = 0.0
        fake_regime.atr_ratio = 3.5
        fake_regime.adx = 35.0

        loop = _create_trading_loop()
        loop._regime_detector = MagicMock()
        loop._regime_detector.detect.return_value = fake_regime

        loop.run_once()

        lines = self._get_pipeline_lines(caplog)
        assert len(lines) == 1
        line = lines[0]
        assert "session=PASS" in line
        assert "regime=SKIP" in line
        assert "VOLATILE" in line
        assert "DECISION=SKIP" in line

    def test_conviction_reject_emits_reject_decision(self, caplog):
        """conviction.should_trade=False で conviction=REJECT / DECISION=REJECT。"""
        caplog.set_level(logging.INFO, logger="src.trading_loop")

        # ConvictionScorer を should_trade=False に差し替え
        fake_conviction = MagicMock()
        fake_conviction.score = 3
        fake_conviction.position_size_multiplier = 0.0
        fake_conviction.should_trade = False
        fake_conviction.reasoning = "確信度3/10"

        strategy = _make_mock_strategy(signal=Signal.BUY)
        loop = _create_trading_loop(strategy=strategy)
        loop._conviction_scorer = MagicMock()
        loop._conviction_scorer.score.return_value = fake_conviction

        loop.run_once()

        lines = self._get_pipeline_lines(caplog)
        assert len(lines) == 1
        line = lines[0]
        assert "conviction=REJECT" in line
        assert "3/10" in line
        assert "DECISION=REJECT" in line

    def test_ai_reject_emits_reject_decision(self, caplog):
        """AIフィルター REJECT で ai=REJECT / DECISION=REJECT、reasoning が trace に含まれる。"""
        caplog.set_level(logging.INFO, logger="src.trading_loop")

        # AIAdvisor: bias.evaluate_signal が REJECT を返す
        fake_bias = MagicMock()
        fake_bias.direction = "BEARISH"
        fake_bias.confidence = 0.85
        fake_bias.reasoning = "上位足ダイバージェンスで反転濃厚"
        fake_bias.evaluate_signal.return_value = "REJECT"
        fake_bias.position_size_multiplier.return_value = 0.0
        fake_bias.to_record.return_value = {"direction": "BEARISH"}

        fake_advisor = MagicMock()
        fake_advisor.get_bias.return_value = fake_bias

        strategy = _make_mock_strategy(signal=Signal.BUY)
        loop = _create_trading_loop(strategy=strategy)
        loop._ai_advisor = fake_advisor

        loop.run_once()

        lines = self._get_pipeline_lines(caplog)
        assert len(lines) == 1
        line = lines[0]
        assert "ai=REJECT" in line
        # reasoning は MAXLEN(40) で切り詰められるが先頭の特徴語は残る
        assert "上位足" in line
        assert "DECISION=REJECT" in line

    def test_bear_warn_appears_in_trace_but_executes(self, caplog):
        """Bear severity が閾値超え → trace に bear=WARN を残しつつ EXECUTE 継続。"""
        caplog.set_level(logging.INFO, logger="src.trading_loop")

        # BearResearcher: severity=0.6 で WARN（BEAR_SEVERITY_THRESHOLD=0.4超え）
        fake_verdict = MagicMock()
        fake_verdict.severity = 0.6
        fake_verdict.penalty_multiplier = 0.7
        fake_verdict.risk_factors = ["divergence", "support_resistance"]

        fake_bear = MagicMock()
        fake_bear.verify.return_value = fake_verdict

        strategy = _make_mock_strategy(signal=Signal.BUY)
        loop = _create_trading_loop(strategy=strategy)
        loop._bear_researcher = fake_bear

        loop.run_once()

        lines = self._get_pipeline_lines(caplog)
        assert len(lines) == 1
        line = lines[0]
        assert "bear=WARN" in line
        assert "sev=0.60" in line
        assert "pen=0.70" in line
        assert "DECISION=EXECUTE" in line
