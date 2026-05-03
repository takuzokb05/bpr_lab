"""
T3: ATR連動SL/TP + 段階的部分利確 のユニットテスト

カバー範囲:
- calculate_atr_based_levels: ATR ベース SL/TP1/TP2 算出
- StrategyBase.calculate_tp_levels: 既定実装（USE_ATR_BASED_TP の分岐）
- PositionManager.partial_close: 部分決済とローカル状態更新
- PositionManager.update_stop_loss: SLトレーリング
- TradingLoop._manage_partial_take_profits: TP1到達検知 → partial_close → SLトレーリング
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src import config
from src.broker_client import BrokerClient
from src.position_manager import PositionManager
from src.risk_manager import KillSwitch, RiskManager, calculate_atr_based_levels
from src.strategy.base import Signal, StrategyBase, TpLevels
from src.strategy.ma_crossover import RsiMaCrossover
from src.trading_loop import TradingLoop


# ============================================================
# ヘルパー
# ============================================================


def _make_ohlcv(rows: int = 50, close: float = 150.0, atr_seed: float = 0.3) -> pd.DataFrame:
    """ATR が安定計算できる程度のレンジを持つ OHLCV を生成する。"""
    rng = np.random.default_rng(seed=42)
    close_arr = np.full(rows, close) + rng.normal(0, 0.05, rows)
    high_arr = close_arr + atr_seed
    low_arr = close_arr - atr_seed
    open_arr = close_arr.copy()
    return pd.DataFrame({
        "open": open_arr,
        "high": high_arr,
        "low": low_arr,
        "close": close_arr,
        "volume": [1000] * rows,
    })


def _make_mock_broker() -> MagicMock:
    broker = MagicMock(spec=BrokerClient)
    broker.market_order.return_value = {
        "trade_id": "TRD-100", "order_id": "ORD-100",
        "price": 150.0, "units": 1000, "status": "filled",
    }
    broker.get_positions.return_value = []
    broker.get_account_summary.return_value = {"balance": 1_000_000}
    broker.get_closed_deal.return_value = None
    # T3: 部分決済とSL変更のデフォルト戻り値
    broker.partial_close_position.return_value = {
        "trade_id": "TRD-100",
        "closed_units": 500,
        "remaining_units": 500,
        "close_price": 150.5,
        "realized_pl": 250.0,
    }
    broker.modify_position_sl.return_value = {
        "trade_id": "TRD-100",
        "stop_loss": 150.0,
    }
    return broker


def _make_mock_risk_manager() -> MagicMock:
    rm = MagicMock(spec=RiskManager)
    kill_switch = MagicMock(spec=KillSwitch)
    kill_switch.is_trading_allowed.return_value = True
    kill_switch.reason = None
    rm.kill_switch = kill_switch
    rm.check_loss_limits.return_value = (True, None)
    rm.check_consecutive_losses.return_value = (0, False)
    rm.calculate_position_size.return_value = 1.0
    rm.account_balance = 1_000_000
    return rm


# ============================================================
# 1. calculate_atr_based_levels
# ============================================================


class TestCalculateAtrBasedLevels:

    def test_buy_levels(self):
        """BUY: SL は entry より下、TP1/TP2 は entry より上"""
        data = _make_ohlcv(rows=50, close=150.0, atr_seed=0.3)
        levels = calculate_atr_based_levels(150.0, "BUY", data)

        assert isinstance(levels, TpLevels)
        assert levels.stop_loss < 150.0
        assert levels.tp1 > 150.0
        assert levels.tp2 > levels.tp1
        # SL = 1.5×ATR、TP1 = 1.0×ATR、TP2 = 3.0×ATR の関係
        atr = levels.atr
        assert pytest.approx(150.0 - levels.stop_loss, rel=1e-6) == atr * config.ATR_SL_MULT
        assert pytest.approx(levels.tp1 - 150.0, rel=1e-6) == atr * config.ATR_TP1_MULT
        assert pytest.approx(levels.tp2 - 150.0, rel=1e-6) == atr * config.ATR_TP2_MULT

    def test_sell_levels(self):
        """SELL: SL は entry より上、TP1/TP2 は entry より下"""
        data = _make_ohlcv(rows=50, close=150.0, atr_seed=0.3)
        levels = calculate_atr_based_levels(150.0, "SELL", data)

        assert levels.stop_loss > 150.0
        assert levels.tp1 < 150.0
        assert levels.tp2 < levels.tp1
        atr = levels.atr
        assert pytest.approx(levels.stop_loss - 150.0, rel=1e-6) == atr * config.ATR_SL_MULT
        assert pytest.approx(150.0 - levels.tp1, rel=1e-6) == atr * config.ATR_TP1_MULT
        assert pytest.approx(150.0 - levels.tp2, rel=1e-6) == atr * config.ATR_TP2_MULT

    def test_invalid_direction(self):
        data = _make_ohlcv()
        with pytest.raises(ValueError, match="direction"):
            calculate_atr_based_levels(150.0, "INVALID", data)

    def test_atr_unavailable(self):
        """ATR 計算不能（データ不足）→ ValueError"""
        small = _make_ohlcv(rows=5)
        with pytest.raises(ValueError, match="ATR"):
            calculate_atr_based_levels(150.0, "BUY", small)

    def test_atr_value_override(self):
        """atr_value 引数で ATR 計算をスキップできる"""
        data = _make_ohlcv()
        levels = calculate_atr_based_levels(150.0, "BUY", data, atr_value=0.5)
        assert levels.atr == 0.5
        assert pytest.approx(150.0 - levels.stop_loss, rel=1e-6) == 0.5 * config.ATR_SL_MULT

    def test_zero_atr_rejected(self):
        data = _make_ohlcv()
        with pytest.raises(ValueError, match="ATR"):
            calculate_atr_based_levels(150.0, "BUY", data, atr_value=0.0)

    def test_pair_overrides_applied(self):
        """T4: ペア別 sl_mult/tp1_mult/tp2_mult が優先される"""
        data = _make_ohlcv()
        levels = calculate_atr_based_levels(
            150.0, "BUY", data, atr_value=0.5,
            sl_mult=2.0, tp1_mult=1.5, tp2_mult=4.0,
        )
        assert pytest.approx(150.0 - levels.stop_loss, rel=1e-6) == 0.5 * 2.0
        assert pytest.approx(levels.tp1 - 150.0, rel=1e-6) == 0.5 * 1.5
        assert pytest.approx(levels.tp2 - 150.0, rel=1e-6) == 0.5 * 4.0

    def test_partial_pair_override_falls_back_for_missing(self):
        """sl_mult のみ指定、TP は global にフォールバック"""
        data = _make_ohlcv()
        levels = calculate_atr_based_levels(
            150.0, "BUY", data, atr_value=0.5, sl_mult=2.5,
        )
        assert pytest.approx(150.0 - levels.stop_loss, rel=1e-6) == 0.5 * 2.5
        assert pytest.approx(levels.tp1 - 150.0, rel=1e-6) == 0.5 * config.ATR_TP1_MULT
        assert pytest.approx(levels.tp2 - 150.0, rel=1e-6) == 0.5 * config.ATR_TP2_MULT


# ============================================================
# 2. StrategyBase.calculate_tp_levels（既定実装）
# ============================================================


class TestStrategyTpLevels:

    def test_atr_mode_uses_atr_based(self, monkeypatch):
        monkeypatch.setattr(config, "USE_ATR_BASED_TP", True)
        strategy = RsiMaCrossover()
        data = _make_ohlcv(rows=50)
        levels = strategy.calculate_tp_levels(150.0, "BUY", data)
        assert isinstance(levels, TpLevels)
        assert levels.atr is not None
        # SL = 1.5 × ATR
        assert pytest.approx(150.0 - levels.stop_loss, rel=1e-6) == levels.atr * config.ATR_SL_MULT

    def test_legacy_mode_falls_back(self, monkeypatch):
        monkeypatch.setattr(config, "USE_ATR_BASED_TP", False)
        strategy = RsiMaCrossover()
        data = _make_ohlcv(rows=50)
        levels = strategy.calculate_tp_levels(150.0, "BUY", data)
        # 旧来パス: tp1 == tp2（部分利確しない動作）
        assert levels.tp1 == levels.tp2
        assert levels.atr is None

    def test_pair_config_overrides_via_strategy(self, monkeypatch):
        """T4: pair_config 経由で戦略がペア別係数を使う"""
        monkeypatch.setattr(config, "USE_ATR_BASED_TP", True)
        strategy = RsiMaCrossover()
        data = _make_ohlcv(rows=50)
        # GBP_JPY 想定の高ボラ係数
        pair_cfg = {"atr_sl_mult": 2.0, "atr_tp1_mult": 1.5, "atr_tp2_mult": 4.0}
        levels = strategy.calculate_tp_levels(150.0, "BUY", data, pair_config=pair_cfg)
        atr = levels.atr
        assert pytest.approx(150.0 - levels.stop_loss, rel=1e-6) == atr * 2.0
        assert pytest.approx(levels.tp1 - 150.0, rel=1e-6) == atr * 1.5
        assert pytest.approx(levels.tp2 - 150.0, rel=1e-6) == atr * 4.0


# ============================================================
# 3. PositionManager.partial_close
# ============================================================


class TestPartialClose:

    def _setup(self):
        broker = _make_mock_broker()
        rm = _make_mock_risk_manager()
        pm = PositionManager(broker_client=broker, risk_manager=rm, max_positions=6)

        # BUY 1000 のポジションを手動で挿入
        pm._open_positions.append({
            "trade_id": "TRD-100",
            "instrument": "USD_JPY",
            "units": 1000,
            "open_price": 150.0,
            "stop_loss": 149.5,
            "take_profit": 151.5,
            "opened_at": datetime.now(timezone.utc),
            "unrealized_pl": 0.0,
            "tp1": 150.5,
            "tp2": 151.5,
            "atr_at_open": 0.5,
            "partial_closed": False,
            "sl_trailed": False,
        })
        return pm, broker

    def test_partial_close_success(self):
        pm, broker = self._setup()
        result = pm.partial_close("TRD-100", ratio=0.5)
        assert result is not None
        broker.partial_close_position.assert_called_once_with("TRD-100", 0.5)

        positions = pm.get_open_positions()
        assert len(positions) == 1
        # 残量にローカル units が更新されている（符号維持）
        assert positions[0]["units"] == 500
        assert positions[0]["partial_closed"] is True

        # 部分決済分が trade_history にも記録される
        assert any(t.get("is_partial") for t in pm.trade_history)

    def test_partial_close_idempotent(self):
        """二度目の partial_close はスキップされる"""
        pm, broker = self._setup()
        pm.partial_close("TRD-100", ratio=0.5)
        broker.partial_close_position.reset_mock()

        result = pm.partial_close("TRD-100", ratio=0.5)
        assert result is None
        broker.partial_close_position.assert_not_called()

    def test_partial_close_invalid_ratio(self):
        pm, broker = self._setup()
        assert pm.partial_close("TRD-100", ratio=0.0) is None
        assert pm.partial_close("TRD-100", ratio=1.0) is None
        assert pm.partial_close("TRD-100", ratio=-0.5) is None
        broker.partial_close_position.assert_not_called()

    def test_partial_close_unknown_position(self):
        pm, broker = self._setup()
        assert pm.partial_close("UNKNOWN", ratio=0.5) is None
        broker.partial_close_position.assert_not_called()

    def test_partial_close_broker_returns_none(self):
        pm, broker = self._setup()
        broker.partial_close_position.return_value = None
        result = pm.partial_close("TRD-100", ratio=0.5)
        assert result is None
        # ローカル状態は変化しない
        positions = pm.get_open_positions()
        assert positions[0]["units"] == 1000
        assert positions[0]["partial_closed"] is False

    def test_partial_close_sell_position(self):
        """SELL ポジションでも符号を維持して残量更新"""
        broker = _make_mock_broker()
        broker.partial_close_position.return_value = {
            "trade_id": "TRD-200",
            "closed_units": 500,
            "remaining_units": 500,
            "close_price": 149.5,
            "realized_pl": 250.0,
        }
        rm = _make_mock_risk_manager()
        pm = PositionManager(broker_client=broker, risk_manager=rm, max_positions=6)
        pm._open_positions.append({
            "trade_id": "TRD-200",
            "instrument": "USD_JPY",
            "units": -1000,
            "open_price": 150.0,
            "stop_loss": 150.5,
            "take_profit": 148.5,
            "opened_at": datetime.now(timezone.utc),
            "unrealized_pl": 0.0,
            "tp1": 149.5,
            "tp2": 148.5,
            "atr_at_open": 0.5,
            "partial_closed": False,
            "sl_trailed": False,
        })
        pm.partial_close("TRD-200", ratio=0.5)
        positions = pm.get_open_positions()
        assert positions[0]["units"] == -500  # 符号維持


# ============================================================
# 4. PositionManager.update_stop_loss
# ============================================================


class TestUpdateStopLoss:

    def test_update_sl_success(self):
        broker = _make_mock_broker()
        rm = _make_mock_risk_manager()
        pm = PositionManager(broker_client=broker, risk_manager=rm, max_positions=6)
        pm._open_positions.append({
            "trade_id": "TRD-100",
            "instrument": "USD_JPY",
            "units": 1000,
            "open_price": 150.0,
            "stop_loss": 149.5,
            "take_profit": 151.5,
            "opened_at": datetime.now(timezone.utc),
            "unrealized_pl": 0.0,
        })
        result = pm.update_stop_loss("TRD-100", 150.0)
        assert result is not None
        broker.modify_position_sl.assert_called_once_with("TRD-100", 150.0)

        positions = pm.get_open_positions()
        assert positions[0]["stop_loss"] == 150.0
        assert positions[0]["sl_trailed"] is True

    def test_update_sl_unknown_position(self):
        broker = _make_mock_broker()
        rm = _make_mock_risk_manager()
        pm = PositionManager(broker_client=broker, risk_manager=rm, max_positions=6)
        assert pm.update_stop_loss("UNKNOWN", 150.0) is None
        broker.modify_position_sl.assert_not_called()


# ============================================================
# 5. TradingLoop._manage_partial_take_profits
# ============================================================


class TestManagePartialTp:

    def _setup_loop_with_position(self, units: int, tp1: float, partial_closed: bool = False):
        broker = _make_mock_broker()
        rm = _make_mock_risk_manager()
        pm = PositionManager(broker_client=broker, risk_manager=rm, max_positions=6)
        pm._open_positions.append({
            "trade_id": "TRD-100",
            "instrument": "USD_JPY",
            "units": units,
            "open_price": 150.0,
            "stop_loss": 149.5 if units > 0 else 150.5,
            "take_profit": 151.5 if units > 0 else 148.5,
            "opened_at": datetime.now(timezone.utc),
            "unrealized_pl": 0.0,
            "tp1": tp1,
            "tp2": 153.0 if units > 0 else 147.0,
            "atr_at_open": 0.5,
            "partial_closed": partial_closed,
            "sl_trailed": False,
        })
        strategy = MagicMock(spec=StrategyBase)
        loop = TradingLoop(
            broker_client=broker,
            position_manager=pm,
            risk_manager=rm,
            strategy=strategy,
            instrument="USD_JPY",
        )
        return loop, pm, broker

    def test_tp1_hit_buy_triggers_partial_close_and_trailing(self, monkeypatch):
        monkeypatch.setattr(config, "TRAILING_SL_TO_BREAKEVEN", True)
        loop, pm, broker = self._setup_loop_with_position(units=1000, tp1=150.5)

        # 最新バーで high が tp1 を超える OHLCV
        data = pd.DataFrame({
            "open": [150.0, 150.2],
            "high": [150.3, 150.7],  # 最新 high = 150.7 >= tp1=150.5
            "low": [149.9, 150.1],
            "close": [150.2, 150.6],
            "volume": [1000, 1000],
        })

        loop._manage_partial_take_profits(data)

        broker.partial_close_position.assert_called_once()
        # SL が entry(150.0) にトレーリングされる
        broker.modify_position_sl.assert_called_once()
        call_args = broker.modify_position_sl.call_args
        assert call_args[0][1] == 150.0  # 新SL = entry

    def test_tp1_not_hit_no_action(self):
        loop, pm, broker = self._setup_loop_with_position(units=1000, tp1=150.5)
        data = pd.DataFrame({
            "open": [150.0], "high": [150.2], "low": [149.9], "close": [150.1], "volume": [1000],
        })
        loop._manage_partial_take_profits(data)
        broker.partial_close_position.assert_not_called()
        broker.modify_position_sl.assert_not_called()

    def test_tp1_hit_sell_triggers_partial_close(self):
        loop, pm, broker = self._setup_loop_with_position(units=-1000, tp1=149.5)
        # SELL: low が tp1=149.5 以下に下がる
        data = pd.DataFrame({
            "open": [150.0], "high": [150.2], "low": [149.3], "close": [149.7], "volume": [1000],
        })
        loop._manage_partial_take_profits(data)
        broker.partial_close_position.assert_called_once()

    def test_partial_already_closed_skipped(self):
        loop, pm, broker = self._setup_loop_with_position(
            units=1000, tp1=150.5, partial_closed=True,
        )
        data = pd.DataFrame({
            "open": [150.0], "high": [150.7], "low": [150.0], "close": [150.6], "volume": [1000],
        })
        loop._manage_partial_take_profits(data)
        broker.partial_close_position.assert_not_called()

    def test_other_instrument_skipped(self):
        loop, pm, broker = self._setup_loop_with_position(units=1000, tp1=150.5)
        # ポジションを別 instrument に変更
        pm._open_positions[0]["instrument"] = "EUR_USD"
        data = pd.DataFrame({
            "open": [150.0], "high": [150.7], "low": [150.0], "close": [150.6], "volume": [1000],
        })
        loop._manage_partial_take_profits(data)
        broker.partial_close_position.assert_not_called()

    def test_no_tp1_skipped(self):
        """旧来モード（tp1=None）のポジションはスキップ"""
        loop, pm, broker = self._setup_loop_with_position(units=1000, tp1=150.5)
        pm._open_positions[0]["tp1"] = None
        data = pd.DataFrame({
            "open": [150.0], "high": [150.7], "low": [150.0], "close": [150.6], "volume": [1000],
        })
        loop._manage_partial_take_profits(data)
        broker.partial_close_position.assert_not_called()

    def test_trailing_disabled(self, monkeypatch):
        """TRAILING_SL_TO_BREAKEVEN=False 時は SL 変更を呼ばない"""
        monkeypatch.setattr(
            "src.trading_loop.TRAILING_SL_TO_BREAKEVEN", False,
        )
        loop, pm, broker = self._setup_loop_with_position(units=1000, tp1=150.5)
        data = pd.DataFrame({
            "open": [150.0], "high": [150.7], "low": [150.0], "close": [150.6], "volume": [1000],
        })
        loop._manage_partial_take_profits(data)
        broker.partial_close_position.assert_called_once()
        broker.modify_position_sl.assert_not_called()


# ============================================================
# 6. PositionManager.open_position の T3 統合
# ============================================================


class TestOpenPositionWithAtrLevels:

    def test_open_position_records_tp_levels(self, monkeypatch):
        """USE_ATR_BASED_TP=True で open_position が tp1/tp2/atr_at_open を保存する"""
        monkeypatch.setattr("src.position_manager.USE_ATR_BASED_TP", True)
        broker = _make_mock_broker()
        rm = _make_mock_risk_manager()
        pm = PositionManager(broker_client=broker, risk_manager=rm, max_positions=6)

        strategy = RsiMaCrossover()
        data = _make_ohlcv(rows=80, close=150.0, atr_seed=0.3)

        pm.open_position("USD_JPY", Signal.BUY, data, strategy)

        positions = pm.get_open_positions()
        assert len(positions) == 1
        pos = positions[0]
        assert pos["tp1"] is not None
        assert pos["tp2"] is not None
        assert pos["atr_at_open"] is not None
        # tp2 > tp1 > entry (BUY なので)
        assert pos["tp2"] > pos["tp1"] > pos["open_price"]

    def test_open_position_legacy_mode_no_tp_levels(self, monkeypatch):
        """USE_ATR_BASED_TP=False で tp1/tp2 は None"""
        monkeypatch.setattr("src.position_manager.USE_ATR_BASED_TP", False)
        broker = _make_mock_broker()
        rm = _make_mock_risk_manager()
        pm = PositionManager(broker_client=broker, risk_manager=rm, max_positions=6)
        strategy = RsiMaCrossover()
        data = _make_ohlcv(rows=80, close=150.0, atr_seed=0.3)

        pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        positions = pm.get_open_positions()
        assert positions[0]["tp1"] is None
        assert positions[0]["tp2"] is None
        assert positions[0]["atr_at_open"] is None
