"""
F13: trading_loop.py のユニットテスト

トレーディングループの1イテレーション実行、キルスイッチ連動、
エラーハンドリング、ループ制御を検証する。
SPEC_phase2.md F13 完了基準準拠。
"""

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
