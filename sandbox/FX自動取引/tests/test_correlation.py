"""
R5: 相関グループエクスポージャーチェックのユニットテスト

MAX_CORRELATION_EXPOSURE=2 の制限が正しく機能し、
同一相関グループ内で3つ目のポジションがブロックされることを検証する。
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.broker_client import BrokerClient
from src.config import MAX_CORRELATION_EXPOSURE
from src.position_manager import PositionManager
from src.risk_manager import KillSwitch, RiskManager
from src.strategy.base import Signal, StrategyBase


# ============================================================
# ヘルパー
# ============================================================


def _make_ohlcv_data(close_price: float = 150.0, rows: int = 50) -> pd.DataFrame:
    """テスト用のOHLCVデータを生成する。"""
    return pd.DataFrame({
        "open": [close_price] * rows,
        "high": [close_price + 0.5] * rows,
        "low": [close_price - 0.5] * rows,
        "close": [close_price] * rows,
        "volume": [1000] * rows,
    })


def _make_mock_broker() -> MagicMock:
    """モック化されたBrokerClientを生成する。"""
    broker = MagicMock(spec=BrokerClient)
    broker.get_account_summary.return_value = {"balance": 1_000_000}
    broker.get_positions.return_value = []
    # trade_idをインクリメントで返す
    broker._call_count = 0

    def _market_order(**kwargs):
        broker._call_count += 1
        return {
            "order_id": f"ORD-{broker._call_count:03d}",
            "trade_id": f"TRD-{broker._call_count:03d}",
            "price": kwargs.get("price", 150.0),
            "units": kwargs.get("units", 1000),
            "status": "filled",
        }

    broker.market_order.side_effect = _market_order
    return broker


def _make_mock_risk_manager() -> MagicMock:
    """モック化されたRiskManagerを生成する。"""
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


def _make_mock_strategy(
    stop_loss: float = 149.0, take_profit: float = 152.0
) -> MagicMock:
    """モック化されたStrategyBaseを生成する。"""
    strategy = MagicMock(spec=StrategyBase)
    strategy.calculate_stop_loss.return_value = stop_loss
    strategy.calculate_take_profit.return_value = take_profit
    return strategy


def _create_pm(broker: MagicMock = None, max_positions: int = 6) -> PositionManager:
    """テスト用PositionManagerを生成する。"""
    if broker is None:
        broker = _make_mock_broker()
    return PositionManager(
        broker_client=broker,
        risk_manager=_make_mock_risk_manager(),
        max_positions=max_positions,
    )


# ============================================================
# 1. 相関グループ内の制限テスト
# ============================================================


class TestCorrelationExposure:
    """相関グループエクスポージャーのテスト"""

    def test_two_jpy_cross_allowed(self):
        """JPY_CROSSグループで2ポジションは許可される（MAX=2）"""
        broker = _make_mock_broker()
        pm = _create_pm(broker=broker)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # 1つ目: USD_JPY
        result1 = pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        assert result1 is not None

        # 2つ目: EUR_JPY（同じJPY_CROSSグループ）
        strategy.calculate_stop_loss.return_value = 149.0
        result2 = pm.open_position("EUR_JPY", Signal.BUY, data, strategy)
        assert result2 is not None

        assert pm.position_count == 2

    def test_third_jpy_cross_blocked(self):
        """JPY_CROSSグループで3つ目のポジションはブロックされる"""
        broker = _make_mock_broker()
        pm = _create_pm(broker=broker)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # 1つ目: USD_JPY
        result1 = pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        assert result1 is not None

        # 2つ目: EUR_JPY
        result2 = pm.open_position("EUR_JPY", Signal.BUY, data, strategy)
        assert result2 is not None

        # 3つ目: GBP_JPY → ブロック
        result3 = pm.open_position("GBP_JPY", Signal.BUY, data, strategy)
        assert result3 is None
        assert pm.position_count == 2

    def test_unrelated_pairs_always_allowed(self):
        """相関グループが異なるペアは互いに制限されない"""
        broker = _make_mock_broker()
        pm = _create_pm(broker=broker)
        data = _make_ohlcv_data()

        # AUD_USDのSL/TPを非JPYペア向けに設定
        strategy_non_jpy = _make_mock_strategy(
            stop_loss=0.6400, take_profit=0.6700
        )
        strategy_jpy = _make_mock_strategy(
            stop_loss=149.0, take_profit=152.0
        )

        # AUD_USD（USD_GROUPのみ）
        result1 = pm.open_position("AUD_USD", Signal.BUY, data, strategy_non_jpy)
        assert result1 is not None

        # GBP_JPY（JPY_CROSSのみ）— AUD_USDとは相関グループが異なる
        result2 = pm.open_position("GBP_JPY", Signal.BUY, data, strategy_jpy)
        assert result2 is not None

        assert pm.position_count == 2

    def test_empty_positions_always_allowed(self):
        """保有ポジションが空の場合は常に許可"""
        pm = _create_pm()

        # 内部メソッドを直接テスト
        allowed, reason = pm._check_correlation_exposure("USD_JPY")
        assert allowed is True
        assert reason == ""

    def test_instrument_not_in_any_group_allowed(self):
        """相関グループに属さない通貨ペアは常に許可"""
        pm = _create_pm()

        # NZD_CAD はどの相関グループにも属さない
        allowed, reason = pm._check_correlation_exposure("NZD_CAD")
        assert allowed is True
        assert reason == ""

    def test_usd_group_also_checked(self):
        """USD_GROUPの制限も正しく機能する"""
        broker = _make_mock_broker()
        pm = _create_pm(broker=broker)
        data = _make_ohlcv_data()

        strategy_jpy = _make_mock_strategy(stop_loss=149.0, take_profit=152.0)
        strategy_non_jpy = _make_mock_strategy(stop_loss=1.0900, take_profit=1.1200)

        # USD_JPY（JPY_CROSS + USD_GROUP 両方に所属）
        result1 = pm.open_position("USD_JPY", Signal.BUY, data, strategy_jpy)
        assert result1 is not None

        # EUR_USD（USD_GROUP）
        result2 = pm.open_position("EUR_USD", Signal.BUY, data, strategy_non_jpy)
        assert result2 is not None

        # AUD_USD（USD_GROUP）→ USD_GROUPが2に達しているのでブロック
        strategy_aud = _make_mock_strategy(stop_loss=0.6400, take_profit=0.6700)
        result3 = pm.open_position("AUD_USD", Signal.BUY, data, strategy_aud)
        assert result3 is None
        assert pm.position_count == 2

    def test_correlation_check_reason_message(self):
        """ブロック時の理由メッセージにグループ名が含まれること"""
        broker = _make_mock_broker()
        pm = _create_pm(broker=broker)
        strategy = _make_mock_strategy()
        data = _make_ohlcv_data()

        # JPY_CROSSを2つ埋める
        pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        pm.open_position("EUR_JPY", Signal.BUY, data, strategy)

        # 3つ目で理由メッセージを確認
        allowed, reason = pm._check_correlation_exposure("GBP_JPY")
        assert allowed is False
        assert "JPY_CROSS" in reason
        assert str(MAX_CORRELATION_EXPOSURE) in reason
