"""
F1: config.py のユニットテスト

設定値の定義・バリデーション・環境変数読み込みを検証する。
"""

import os
from unittest.mock import patch

import pytest

from src import config
from src.config import (
    ConfigValidationError,
    validate_config,
    validate_or_raise,
    # 定数が定義されていることの確認
    MAX_RISK_PER_TRADE,
    MAX_RISK_PER_TRADE_HARD,
    MAX_LEVERAGE,
    DRAWDOWN_LEVELS,
    MAX_DAILY_LOSS,
    MAX_WEEKLY_LOSS,
    MAX_MONTHLY_LOSS,
    MAX_CONSECUTIVE_LOSSES,
    MAX_OPEN_POSITIONS,
    MAX_CORRELATION_EXPOSURE,
    MA_SHORT_PERIOD,
    MA_LONG_PERIOD,
    RSI_PERIOD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    ATR_PERIOD,
    ATR_MULTIPLIER,
    MIN_RISK_REWARD,
    MAIN_TIMEFRAME,
    API_TIMEOUT,
    API_MAX_RETRIES,
    KILL_ATR_MULTIPLIER,
    KILL_SPREAD_MULTIPLIER,
    KILL_API_DISCONNECT_SEC,
    DB_PATH,
)


class TestConstantDefinitions:
    """全定数が正しい値で定義されていることを検証"""

    def test_risk_per_trade(self):
        # STAGE2(2026-04-21): バックテストDD-41%対応で0.05%に抑制
        assert MAX_RISK_PER_TRADE == 0.0005
        assert MAX_RISK_PER_TRADE_HARD == 0.02

    def test_leverage(self):
        assert MAX_LEVERAGE == 10

    def test_drawdown_levels(self):
        assert len(DRAWDOWN_LEVELS) == 5
        assert DRAWDOWN_LEVELS[0.05] == "WARNING"
        assert DRAWDOWN_LEVELS[0.10] == "REDUCE"
        assert DRAWDOWN_LEVELS[0.15] == "MINIMUM"
        assert DRAWDOWN_LEVELS[0.20] == "STOP"
        assert DRAWDOWN_LEVELS[0.25] == "EMERGENCY"

    def test_loss_limits(self):
        # STAGE2(2026-04-21): 本来値（日次5%/週10%/月20%）
        assert MAX_DAILY_LOSS == 0.05
        assert MAX_WEEKLY_LOSS == 0.10
        assert MAX_MONTHLY_LOSS == 0.20

    def test_consecutive_losses(self):
        # STAGE2: 本来5→10で一旦緩め
        assert MAX_CONSECUTIVE_LOSSES == 10

    def test_position_limits(self):
        assert MAX_OPEN_POSITIONS == 6
        assert MAX_CORRELATION_EXPOSURE == 2

    def test_strategy_params(self):
        assert MA_SHORT_PERIOD == 20
        assert MA_LONG_PERIOD == 50
        assert RSI_PERIOD == 14
        assert RSI_OVERBOUGHT == 70
        assert RSI_OVERSOLD == 30
        assert ATR_PERIOD == 14
        assert ATR_MULTIPLIER == 2.0
        assert MIN_RISK_REWARD == 2.0

    def test_timeframe(self):
        # STAGE3(2026-04-21): RsiPullback戦略（旧名 MTFPullback）のベストTFはM15
        assert MAIN_TIMEFRAME == "M15"

    def test_api_settings(self):
        assert API_TIMEOUT == 30
        assert API_MAX_RETRIES == 3

    def test_kill_switch_thresholds(self):
        assert KILL_ATR_MULTIPLIER == 3.0
        assert KILL_SPREAD_MULTIPLIER == 5.0
        assert KILL_API_DISCONNECT_SEC == 30

    def test_db_path(self):
        assert DB_PATH.name == "fx_trading.db"
        assert "data" in str(DB_PATH)


class TestValidation:
    """バリデーション機能のテスト"""

    def test_valid_config(self):
        """正常な設定値ではエラーなし"""
        errors = validate_config()
        assert len(errors) == 0

    def test_risk_per_trade_out_of_range(self):
        """MAX_RISK_PER_TRADEが範囲外でエラー"""
        with patch.object(config, "MAX_RISK_PER_TRADE", 1.5):
            errors = validate_config()
            risk_errors = [e for e in errors if e.field_name == "MAX_RISK_PER_TRADE"]
            assert len(risk_errors) >= 1

    def test_risk_per_trade_exceeds_hard_limit(self):
        """MAX_RISK_PER_TRADEがハードリミットを超過でエラー"""
        with patch.object(config, "MAX_RISK_PER_TRADE", 0.05), \
             patch.object(config, "MAX_RISK_PER_TRADE_HARD", 0.02):
            errors = validate_config()
            assert any("超えています" in e.message for e in errors)

    def test_leverage_out_of_range(self):
        """MAX_LEVERAGEが日本の法的上限を超過でエラー"""
        with patch.object(config, "MAX_LEVERAGE", 30):
            errors = validate_config()
            lev_errors = [e for e in errors if e.field_name == "MAX_LEVERAGE"]
            assert len(lev_errors) == 1
            assert "25倍" in lev_errors[0].message

    def test_ma_periods_invalid(self):
        """短期MAが長期MA以上でエラー"""
        with patch.object(config, "MA_SHORT_PERIOD", 50), \
             patch.object(config, "MA_LONG_PERIOD", 20):
            errors = validate_config()
            ma_errors = [e for e in errors if e.field_name == "MA_SHORT_PERIOD"]
            assert len(ma_errors) == 1

    def test_rsi_thresholds_invalid(self):
        """RSI閾値が逆転でエラー"""
        with patch.object(config, "RSI_OVERSOLD", 80), \
             patch.object(config, "RSI_OVERBOUGHT", 20):
            errors = validate_config()
            rsi_errors = [e for e in errors if "RSI" in e.field_name]
            assert len(rsi_errors) == 1

    def test_validate_or_raise_exits_on_error(self):
        """バリデーションエラー時にSystemExitを送出"""
        with patch.object(config, "MAX_RISK_PER_TRADE", 5.0):
            with pytest.raises(SystemExit) as exc_info:
                validate_or_raise()
            assert "設定エラー" in str(exc_info.value)

    def test_validate_or_raise_passes_when_valid(self):
        """正常な設定ではSystemExitを送出しない"""
        validate_or_raise()  # 例外が出なければOK


class TestConfigValidationError:
    """ConfigValidationErrorデータクラスのテスト"""

    def test_fields(self):
        err = ConfigValidationError(field_name="TEST", message="テストメッセージ")
        assert err.field_name == "TEST"
        assert err.message == "テストメッセージ"
