"""
F12: position_manager.py のユニットテスト

ポジションのオープン・クローズ・同期・プロパティを検証する。
SPEC_phase2.md F12 完了基準準拠。
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.broker_client import BrokerClient
from src.config import MAX_OPEN_POSITIONS
from src.position_manager import PositionManager, PositionManagerError
from src.risk_manager import KillSwitch, RiskManager
from src.strategy.base import Signal, StrategyBase


# ============================================================
# テスト用フィクスチャ・ヘルパー
# ============================================================


def _make_ohlcv_data(close_price: float = 150.0, rows: int = 50) -> pd.DataFrame:
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
    broker.market_order.return_value = {
        "order_id": "ORD-001",
        "trade_id": "TRD-001",
        "price": 150.0,
        "units": 1000,
        "status": "filled",
    }
    broker.close_position.return_value = {
        "trade_id": "TRD-001",
        "realized_pl": 500.0,
        "close_price": 150.50,
    }
    broker.get_positions.return_value = []
    broker.get_account_summary.return_value = {"balance": 1_000_000}
    # デフォルト: 決済履歴は取得できない（pl_unknown経路をテスト可能にする）
    broker.get_closed_deal.return_value = None
    return broker


def _make_mock_risk_manager() -> MagicMock:
    """モック化されたRiskManagerを生成する。"""
    rm = MagicMock(spec=RiskManager)

    # キルスイッチ: デフォルトで取引許可
    kill_switch = MagicMock(spec=KillSwitch)
    kill_switch.is_trading_allowed.return_value = True
    kill_switch.reason = None
    rm.kill_switch = kill_switch

    # 損失上限チェック: デフォルトで許可
    rm.check_loss_limits.return_value = (True, None)

    # 連続負けチェック: デフォルトで停止なし
    rm.check_consecutive_losses.return_value = (0, False)

    # ポジションサイズ計算: デフォルトで1.0ロット
    rm.calculate_position_size.return_value = 1.0

    # 口座残高
    rm.account_balance = 1_000_000

    return rm


def _make_mock_strategy(
    stop_loss: float = 149.0, take_profit: float = 152.0
) -> MagicMock:
    """モック化されたStrategyBaseを生成する。"""
    strategy = MagicMock(spec=StrategyBase)
    strategy.calculate_stop_loss.return_value = stop_loss
    strategy.calculate_take_profit.return_value = take_profit
    return strategy


def _create_position_manager(
    broker: MagicMock = None,
    risk_manager: MagicMock = None,
    max_positions: int = MAX_OPEN_POSITIONS,
) -> PositionManager:
    """テスト用PositionManagerを生成する。"""
    if broker is None:
        broker = _make_mock_broker()
    if risk_manager is None:
        risk_manager = _make_mock_risk_manager()
    return PositionManager(
        broker_client=broker,
        risk_manager=risk_manager,
        max_positions=max_positions,
    )


# ============================================================
# 1. open_position テスト
# ============================================================


class TestOpenPosition:
    """open_position メソッドのテスト"""

    def test_buy_signal_success(self):
        """BUYシグナルでポジションオープン成功"""
        broker = _make_mock_broker()
        rm = _make_mock_risk_manager()
        strategy = _make_mock_strategy()
        pm = _create_position_manager(broker=broker, risk_manager=rm)

        data = _make_ohlcv_data(close_price=150.0)
        result = pm.open_position("USD_JPY", Signal.BUY, data, strategy)

        # 注文結果が返ること
        assert result is not None
        assert result["trade_id"] == "TRD-001"

        # ブローカーに成行注文が発注されたこと
        broker.market_order.assert_called_once()
        call_args = broker.market_order.call_args
        assert call_args.kwargs["instrument"] == "USD_JPY"
        # BUY → units は正
        assert call_args.kwargs["units"] > 0

        # ローカル状態に追加されたこと
        assert pm.position_count == 1
        positions = pm.get_open_positions()
        assert positions[0]["instrument"] == "USD_JPY"
        assert positions[0]["units"] > 0  # BUY → 正

    def test_sell_signal_success(self):
        """SELLシグナルでポジションオープン成功"""
        broker = _make_mock_broker()
        broker.market_order.return_value = {
            "order_id": "ORD-002",
            "trade_id": "TRD-002",
            "price": 150.0,
            "units": -1000,
            "status": "filled",
        }
        rm = _make_mock_risk_manager()
        strategy = _make_mock_strategy(stop_loss=151.0, take_profit=148.0)
        pm = _create_position_manager(broker=broker, risk_manager=rm)

        data = _make_ohlcv_data(close_price=150.0)
        result = pm.open_position("USD_JPY", Signal.SELL, data, strategy)

        # 注文結果が返ること
        assert result is not None
        assert result["trade_id"] == "TRD-002"

        # ブローカーに成行注文が発注されたこと
        broker.market_order.assert_called_once()
        call_args = broker.market_order.call_args
        # SELL → units は負
        assert call_args.kwargs["units"] < 0

        # ローカル状態に追加されたこと
        assert pm.position_count == 1
        positions = pm.get_open_positions()
        assert positions[0]["units"] < 0  # SELL → 負

    def test_hold_signal_returns_none(self):
        """HOLDシグナル → None返却"""
        pm = _create_position_manager()
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        result = pm.open_position("USD_JPY", Signal.HOLD, data, strategy)

        assert result is None
        assert pm.position_count == 0

    def test_kill_switch_active_returns_none(self):
        """キルスイッチ発動中 → None返却"""
        rm = _make_mock_risk_manager()
        rm.kill_switch.is_trading_allowed.return_value = False
        rm.kill_switch.reason = "daily_loss"
        pm = _create_position_manager(risk_manager=rm)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        result = pm.open_position("USD_JPY", Signal.BUY, data, strategy)

        assert result is None
        assert pm.position_count == 0

    def test_duplicate_instrument_returns_none(self):
        """同一通貨ペア重複 → None返却"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # 最初のポジションをオープン
        result1 = pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        assert result1 is not None

        # 同じ通貨ペアで2回目 → None
        broker.market_order.return_value = {
            "order_id": "ORD-002",
            "trade_id": "TRD-002",
            "price": 150.0,
            "units": 1000,
            "status": "filled",
        }
        result2 = pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        assert result2 is None
        assert pm.position_count == 1  # 1つのまま

    def test_max_positions_exceeded_returns_none(self):
        """最大ポジション数超過 → None返却"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker, max_positions=1)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # 1つ目をオープン
        result1 = pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        assert result1 is not None
        assert pm.position_count == 1

        # 2つ目は別通貨ペアだが、上限超過
        broker.market_order.return_value = {
            "order_id": "ORD-002",
            "trade_id": "TRD-002",
            "price": 1.1000,
            "units": 1000,
            "status": "filled",
        }
        result2 = pm.open_position("EUR_USD", Signal.BUY, data, strategy)
        assert result2 is None
        assert pm.position_count == 1

    def test_loss_limit_reached_returns_none(self):
        """損失上限到達 → None返却"""
        rm = _make_mock_risk_manager()
        rm.check_loss_limits.return_value = (False, "日次損失上限に到達")
        pm = _create_position_manager(risk_manager=rm)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        result = pm.open_position("USD_JPY", Signal.BUY, data, strategy)

        assert result is None
        assert pm.position_count == 0

    def test_consecutive_losses_limit_returns_none(self):
        """連続負け上限 → None返却"""
        rm = _make_mock_risk_manager()
        rm.check_consecutive_losses.return_value = (5, True)
        pm = _create_position_manager(risk_manager=rm)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        result = pm.open_position("USD_JPY", Signal.BUY, data, strategy)

        assert result is None
        assert pm.position_count == 0

    def test_position_size_zero_returns_none(self):
        """ポジションサイズ0 → None返却"""
        rm = _make_mock_risk_manager()
        rm.calculate_position_size.return_value = 0.0
        pm = _create_position_manager(risk_manager=rm)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        result = pm.open_position("USD_JPY", Signal.BUY, data, strategy)

        assert result is None
        assert pm.position_count == 0


# ============================================================
# 2. close_position テスト
# ============================================================


class TestClosePosition:
    """close_position メソッドのテスト"""

    def test_close_success_moves_to_history(self):
        """正常決済 → trade_historyに移動"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # ポジションオープン
        pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        assert pm.position_count == 1

        # ポジション決済
        result = pm.close_position("TRD-001")

        assert result is not None
        assert result["trade_id"] == "TRD-001"
        assert result["realized_pl"] == 500.0

        # ローカルから削除されていること
        assert pm.position_count == 0

        # trade_historyに移動していること
        history = pm.trade_history
        assert len(history) == 1
        assert history[0]["trade_id"] == "TRD-001"
        assert history[0]["instrument"] == "USD_JPY"
        assert history[0]["pl"] == 500.0
        assert history[0]["close_price"] == 150.50
        assert isinstance(history[0]["opened_at"], datetime)
        assert isinstance(history[0]["close_time"], datetime)

    def test_close_nonexistent_trade_returns_none(self):
        """存在しないtrade_id → None"""
        pm = _create_position_manager()

        result = pm.close_position("NONEXISTENT")

        assert result is None
        assert pm.position_count == 0
        assert len(pm.trade_history) == 0


# ============================================================
# 3. close_all_positions テスト
# ============================================================


class TestCloseAllPositions:
    """close_all_positions メソッドのテスト"""

    @patch.object(PositionManager, "_check_correlation_exposure", return_value=(True, ""))
    def test_close_all_success(self, _mock_corr):
        """全ポジション一括決済"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker, max_positions=3)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # 3つのポジションをオープン
        instruments = ["USD_JPY", "EUR_USD", "GBP_USD"]
        trade_ids = ["TRD-001", "TRD-002", "TRD-003"]

        for i, (inst, tid) in enumerate(zip(instruments, trade_ids)):
            broker.market_order.return_value = {
                "order_id": f"ORD-{i+1:03d}",
                "trade_id": tid,
                "price": 150.0 if "JPY" in inst else 1.1000,
                "units": 1000,
                "status": "filled",
            }
            # 非JPYペアのSL/TPも合理的な値を設定
            if "JPY" not in inst:
                strategy.calculate_stop_loss.return_value = 1.0900
                strategy.calculate_take_profit.return_value = 1.1200
            else:
                strategy.calculate_stop_loss.return_value = 149.0
                strategy.calculate_take_profit.return_value = 152.0

            result = pm.open_position(inst, Signal.BUY, data, strategy)
            assert result is not None, f"ポジション {inst} のオープンに失敗"

        assert pm.position_count == 3

        # 各決済で異なるclose_positionレスポンスを返す
        close_results = [
            {"trade_id": "TRD-001", "realized_pl": 100.0, "close_price": 150.10},
            {"trade_id": "TRD-002", "realized_pl": -50.0, "close_price": 1.0950},
            {"trade_id": "TRD-003", "realized_pl": 200.0, "close_price": 1.3050},
        ]
        broker.close_position.side_effect = close_results

        # 一括決済
        results = pm.close_all_positions(reason="EMERGENCY")

        # M-4: dict形式で成功/失敗/合計を返す
        assert results["total"] == 3
        assert len(results["closed"]) == 3
        assert results["failed"] == []
        assert pm.position_count == 0
        assert len(pm.trade_history) == 3

    @patch.object(PositionManager, "_check_correlation_exposure", return_value=(True, ""))
    def test_close_all_partial_failure(self, _mock_corr):
        """一括決済で一部が失敗しても残りは決済を継続する"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker, max_positions=3)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # 3つのポジションをオープン
        instruments = ["USD_JPY", "EUR_USD", "GBP_USD"]
        trade_ids = ["TRD-001", "TRD-002", "TRD-003"]

        for i, (inst, tid) in enumerate(zip(instruments, trade_ids)):
            broker.market_order.return_value = {
                "order_id": f"ORD-{i+1:03d}",
                "trade_id": tid,
                "price": 150.0 if "JPY" in inst else 1.1000,
                "units": 1000,
                "status": "filled",
            }
            if "JPY" not in inst:
                strategy.calculate_stop_loss.return_value = 1.0900
                strategy.calculate_take_profit.return_value = 1.1200
            else:
                strategy.calculate_stop_loss.return_value = 149.0
                strategy.calculate_take_profit.return_value = 152.0

            result = pm.open_position(inst, Signal.BUY, data, strategy)
            assert result is not None

        assert pm.position_count == 3

        # 2番目の決済でエラー発生、1番目と3番目は成功
        broker.close_position.side_effect = [
            {"trade_id": "TRD-001", "realized_pl": 100.0, "close_price": 150.10},
            ConnectionError("MT5 connection lost"),
            {"trade_id": "TRD-003", "realized_pl": 200.0, "close_price": 1.3050},
        ]

        results = pm.close_all_positions(reason="EMERGENCY")

        # 成功2件、失敗1件
        assert results["total"] == 3
        assert len(results["closed"]) == 2
        assert len(results["failed"]) == 1
        assert "TRD-002" in results["failed"]

        # 決済成功した2件は履歴に、失敗1件はローカルに残る
        assert len(pm.trade_history) == 2


# ============================================================
# 4. sync_with_broker テスト
# ============================================================


class TestSyncWithBroker:
    """sync_with_broker メソッドのテスト"""

    def test_sync_full_match(self):
        """完全一致: ローカルとブローカーが同一"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # ポジションオープン
        pm.open_position("USD_JPY", Signal.BUY, data, strategy)

        # ブローカーも同じポジションを返す
        broker.get_positions.return_value = [
            {
                "trade_id": "TRD-001",
                "instrument": "USD_JPY",
                "units": 1000,
                "unrealized_pl": 250.0,
            }
        ]

        result = pm.sync_with_broker()

        assert result["synced"] == 1
        assert result["local_only"] == []
        assert result["broker_only"] == []

        # 未実現損益が更新されていること
        positions = pm.get_open_positions()
        assert positions[0]["unrealized_pl"] == 250.0

    def test_sync_local_only(self):
        """ローカルのみのポジション検出 → 自動除去（決済履歴未取得 → pl_unknown）"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # ローカルにポジションオープン
        pm.open_position("USD_JPY", Signal.BUY, data, strategy)

        # ブローカーは空（ブローカー側で決済済み）
        broker.get_positions.return_value = []
        # デフォルトで get_closed_deal は None を返す → pl_unknown経路

        result = pm.sync_with_broker()

        assert result["synced"] == 0
        assert result["local_only"] == ["TRD-001"]
        assert result["broker_only"] == []

        # H-3: ローカルのみのポジションが自動除去されていること
        assert pm.position_count == 0

        # 履歴に移動済み（pl_unknown=True）
        assert len(pm.trade_history) == 1
        assert pm.trade_history[0]["trade_id"] == "TRD-001"
        assert pm.trade_history[0]["pl_unknown"] is True
        assert pm.trade_history[0]["close_price"] == 0.0
        assert pm.trade_history[0]["pl"] == 0.0

    def test_sync_local_only_recovers_pl_from_history(self):
        """SL/TP自動決済時にブローカー履歴から close_price/pl を復元"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        pm.open_position("USD_JPY", Signal.BUY, data, strategy)

        broker.get_positions.return_value = []
        closed_at = datetime(2026, 4, 23, 10, 0, 0, tzinfo=timezone.utc)
        broker.get_closed_deal.return_value = {
            "trade_id": "TRD-001",
            "close_price": 150.85,
            "realized_pl": 423.5,
            "closed_at": closed_at,
        }

        result = pm.sync_with_broker()

        assert result["local_only"] == ["TRD-001"]
        broker.get_closed_deal.assert_called_once_with("TRD-001")

        assert len(pm.trade_history) == 1
        entry = pm.trade_history[0]
        assert entry["trade_id"] == "TRD-001"
        assert entry["pl_unknown"] is False
        assert entry["close_price"] == 150.85
        assert entry["pl"] == 423.5
        assert entry["close_time"] == closed_at

    def test_sync_local_only_falls_back_when_history_raises(self):
        """get_closed_deal が例外を投げてもpl_unknownで保存して継続"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        pm.open_position("USD_JPY", Signal.BUY, data, strategy)

        broker.get_positions.return_value = []
        broker.get_closed_deal.side_effect = RuntimeError("MT5 API down")

        result = pm.sync_with_broker()

        assert result["local_only"] == ["TRD-001"]
        assert pm.position_count == 0
        assert pm.trade_history[0]["pl_unknown"] is True

    def test_sync_broker_only(self):
        """ブローカーのみのポジション検出"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker)

        # ローカルは空
        assert pm.position_count == 0

        # ブローカーにはポジションがある
        broker.get_positions.return_value = [
            {
                "trade_id": "TRD-999",
                "instrument": "EUR_USD",
                "units": 5000,
                "unrealized_pl": -100.0,
            }
        ]

        result = pm.sync_with_broker()

        assert result["synced"] == 0
        assert result["local_only"] == []
        assert result["broker_only"] == ["TRD-999"]


# ============================================================
# 5. プロパティテスト
# ============================================================


class TestProperties:
    """プロパティのテスト"""

    def test_position_count(self):
        """position_count プロパティ"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker, max_positions=3)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # 初期状態
        assert pm.position_count == 0

        # ポジションオープン
        pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        assert pm.position_count == 1

        # 2つ目のポジション
        broker.market_order.return_value = {
            "order_id": "ORD-002",
            "trade_id": "TRD-002",
            "price": 1.1000,
            "units": 1000,
            "status": "filled",
        }
        strategy.calculate_stop_loss.return_value = 1.0900
        strategy.calculate_take_profit.return_value = 1.1200
        pm.open_position("EUR_USD", Signal.BUY, data, strategy)
        assert pm.position_count == 2

    def test_trade_history_property(self):
        """trade_history プロパティ"""
        broker = _make_mock_broker()
        pm = _create_position_manager(broker=broker)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # 初期状態
        assert pm.trade_history == []

        # ポジションオープン→決済
        pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        pm.close_position("TRD-001")

        # 取引履歴に追加されていること
        history = pm.trade_history
        assert len(history) == 1
        assert history[0]["trade_id"] == "TRD-001"
        assert history[0]["pl"] == 500.0

        # trade_historyプロパティがコピーを返すこと（内部状態の保護）
        history.append({"fake": True})
        assert len(pm.trade_history) == 1  # 内部状態は変化しない
