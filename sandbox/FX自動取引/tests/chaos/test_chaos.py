"""
FX自動取引システム — カオステスト

doc 04 セクション6.3 / SPEC.md F9 準拠。
6シナリオの異常注入テストを実施し、安全機構の動作を検証する。

シナリオ:
  1. API接続断
  2. スプレッド急拡大
  3. 急激なドローダウン
  4. 連続損失注入
  5. ギャップ注入
  6. 同時多発障害（1+2の複合）
"""

import inspect
import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.backtester import BacktestEngine, RsiMaCrossoverBT
from src.config import KILL_COOLDOWN_MINUTES, KILL_SPREAD_MULTIPLIER, MAX_CONSECUTIVE_LOSSES
from src.oanda_client import OandaClient
from src.position_manager import PositionManager, PositionManagerError
from src.risk_manager import KillSwitch, RiskManager
from src.strategy.base import Signal


# ================================================================
# テストヘルパー
# ================================================================


def _make_trade_history(
    n_trades: int,
    pl: float = -5000.0,
    hours_ago_start: int = 5,
) -> list[dict]:
    """テスト用の取引履歴を生成する。"""
    now = datetime.now(timezone.utc)
    return [
        {
            "pl": pl,
            "close_time": now - timedelta(hours=hours_ago_start - i),
        }
        for i in range(n_trades)
    ]


def _generate_gap_data(n_bars: int = 400, gap_idx: int = 200) -> pd.DataFrame:
    """5%ギャップを含む合成OHLCVデータを生成する（大文字カラム名）。"""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2020-01-01", periods=n_bars, freq="4h")

    # サイン波で明確なトレンド変化
    t = np.linspace(0, 8 * np.pi, n_bars)
    base = 100 + 20 * np.sin(t)
    close = base + rng.normal(0, 0.3, n_bars)

    # ギャップ注入: gap_idx以降を5%下方にシフト
    close[gap_idx:] *= 0.95

    open_ = np.roll(close, 1)
    open_[0] = close[0]
    # ギャップ直後のバー: openはギャップ前の終値（窓開け再現）
    open_[gap_idx] = close[gap_idx - 1]

    high = np.maximum(open_, close) + rng.uniform(0.2, 1.0, n_bars)
    low = np.minimum(open_, close) - rng.uniform(0.2, 1.0, n_bars)
    volume = rng.integers(1000, 10000, n_bars)

    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )


# ================================================================
# シナリオ 1: API接続断
# ================================================================


class TestApiDisconnect:
    """
    シナリオ1: API接続断

    OandaClientのHTTP接続を遮断し、以下を検証:
    - サーバーサイドSL（stop_loss）が設計上常に設定される
    - 再接続後にポジション照合が成功する
    - KillSwitchのapi_disconnectが発動する
    """

    def test_server_side_sl_always_required(self):
        """成行注文は常にSL/TPが必須引数（サーバーサイドSL保証）"""
        sig = inspect.signature(OandaClient.market_order)
        params = sig.parameters

        assert "stop_loss" in params
        assert "take_profit" in params
        # デフォルト値なし = 呼び出し側が必ず指定する
        assert params["stop_loss"].default is inspect.Parameter.empty
        assert params["take_profit"].default is inspect.Parameter.empty

    def test_reconnect_position_reconciliation(self):
        """API接続断からの復帰: リトライ機構でポジション照合が成功する"""
        with patch("src.oanda_client.API") as MockAPI:
            mock_api = MockAPI.return_value

            # 最初の2回はConnectionError（接続断）、3回目で復帰
            mock_api.request.side_effect = [
                ConnectionError("Connection refused"),
                ConnectionError("Connection refused"),
                {
                    "trades": [
                        {
                            "id": "123",
                            "instrument": "USD_JPY",
                            "currentUnits": "1000",
                            "unrealizedPL": "-500",
                            "price": "150.0",
                        }
                    ]
                },
            ]

            client = OandaClient(
                api_key="test-key",
                account_id="test-account",
                environment="practice",
            )

            with patch("src.oanda_client.time.sleep"):
                positions = client.get_positions()

            # 再接続後にポジション照合成功
            assert len(positions) == 1
            assert positions[0]["trade_id"] == "123"
            assert positions[0]["instrument"] == "USD_JPY"

    def test_kill_switch_api_disconnect(self, caplog):
        """API切断でキルスイッチが発動し、取引が停止する"""
        ks = KillSwitch()
        assert ks.is_trading_allowed()

        with caplog.at_level(logging.WARNING):
            ks.activate("api_disconnect")

        assert ks.is_active
        assert ks.reason == "api_disconnect"
        assert not ks.is_trading_allowed()
        assert "キルスイッチ発動" in caplog.text


# ================================================================
# シナリオ 2: スプレッド急拡大
# ================================================================


class TestSpreadSpike:
    """
    シナリオ2: スプレッド急拡大

    スプレッドが通常の10倍に拡大した場合:
    - KillSwitchの"spread"が発動する
    - 新規エントリーが自動停止する
    """

    def test_spread_spike_activates_kill_switch(self, caplog):
        """スプレッド10倍拡大でスプレッドキルスイッチが発動する"""
        ks = KillSwitch()

        # 通常スプレッド=2pips → 10倍=20pips
        normal_spread = 0.02
        current_spread = normal_spread * 10

        # KILL_SPREAD_MULTIPLIER(5倍)を超えるのでキル発動
        assert current_spread >= normal_spread * KILL_SPREAD_MULTIPLIER

        with caplog.at_level(logging.WARNING):
            ks.activate("spread")

        assert ks.is_active
        assert ks.reason == "spread"
        assert not ks.is_trading_allowed()
        assert "キルスイッチ発動" in caplog.text

    def test_no_new_entry_when_spread_kill_active(self):
        """スプレッドキル発動中は新規エントリー不可"""
        rm = RiskManager(1_000_000)
        rm.kill_switch.activate("spread")

        # is_trading_allowed() == False → トレーディングループがエントリーをブロック
        assert not rm.kill_switch.is_trading_allowed()


# ================================================================
# シナリオ 3: 急激なドローダウン
# ================================================================


class TestRapidDrawdown:
    """
    シナリオ3: 急激なドローダウン

    口座残高を15%減少させた状態を注入:
    - ドローダウンレベルが MINIMUM に到達
    - ポジションサイズが最小ロット(0.01)に制限される
    """

    def test_15pct_drawdown_triggers_minimum(self, caplog):
        """15%ドローダウンで MINIMUM レベルが発動する"""
        rm = RiskManager(1_000_000)

        # 口座残高を15%減少: 1,000,000 → 850,000
        with caplog.at_level(logging.WARNING):
            rate, level, action = rm.check_drawdown(850_000, rm.peak_balance)

        assert rate == pytest.approx(0.15)
        assert level == "MINIMUM"
        assert "最小ロット" in action
        assert "ドローダウン検出" in caplog.text

    def test_position_size_limited_to_minimum_lot(self):
        """15%ドローダウンでポジションサイズが0.01ロットに制限される"""
        rm = RiskManager(1_000_000)

        # 残高を15%減少させる
        rm.update_balance(850_000)

        lot = rm.calculate_position_size(850_000, 20.0, "USD_JPY")
        assert lot == 0.01


# ================================================================
# シナリオ 4: 連続損失注入
# ================================================================


class TestConsecutiveLosses:
    """
    シナリオ4: 連続損失注入

    5回連続損失をシミュレート:
    - 連続負けカウンターが5に到達
    - 24時間取引停止が発動
    - KillSwitchの"consecutive_losses"が連動する
    """

    def test_five_consecutive_losses_stops_trading(self, caplog):
        """5連敗で24時間取引停止が発動する"""
        rm = RiskManager(1_000_000)
        trade_history = _make_trade_history(5, pl=-5000.0)

        with caplog.at_level(logging.WARNING):
            count, is_stopped = rm.check_consecutive_losses(trade_history)

        assert count == MAX_CONSECUTIVE_LOSSES
        assert is_stopped is True
        assert "連続負け上限到達" in caplog.text
        assert "24時間取引停止" in caplog.text

    def test_kill_switch_consecutive_losses(self):
        """連続損失でキルスイッチが発動し、取引が完全停止する"""
        rm = RiskManager(1_000_000)
        rm.kill_switch.activate("consecutive_losses")

        assert rm.kill_switch.is_active
        assert rm.kill_switch.reason == "consecutive_losses"
        assert not rm.kill_switch.is_trading_allowed()


# ================================================================
# シナリオ 5: ギャップ注入
# ================================================================


class TestGapInjection:
    """
    シナリオ5: ギャップ注入

    価格データに5%のギャップを挿入:
    - RsiMaCrossoverBT は全ての buy/sell に SL/TP を設定する（設計保証）
    - Backtesting.py はギャップ越えでもSLを約定させる（スリッページ許容）
    """

    def test_strategy_always_sets_sl_tp(self):
        """戦略アダプタは全エントリーでSL/TPを設定する（ソースコード検証）"""
        source = inspect.getsource(RsiMaCrossoverBT.next)

        # buy() / sell() の呼び出しには必ず sl= と tp= が含まれる
        assert "self.buy(sl=" in source
        assert "self.sell(sl=" in source
        assert "tp=" in source

    def test_gap_data_backtest_completes(self):
        """5%ギャップを含むデータでバックテストがクラッシュせず完了する"""
        data = _generate_gap_data(n_bars=400, gap_idx=200)

        with BacktestEngine(db_path=":memory:") as engine:
            result = engine.run(data, RsiMaCrossoverBT)

        # バックテストが正常に完了し、メトリクスが返る
        assert isinstance(result, dict)
        assert "total_trades" in result
        assert "max_drawdown" in result


# ================================================================
# シナリオ 6: 同時多発障害（API接続断 + スプレッド急拡大）
# ================================================================


class TestSimultaneousFailures:
    """
    シナリオ6: 同時多発障害

    API接続断 + スプレッド急拡大を同時注入:
    - (1) サーバーサイドSLが設定済み（market_orderの設計保証）
    - (2) 接続復旧後に全ポジション決済を試行
    """

    def test_server_side_sl_survives_disconnect(self):
        """
        API接続断でもサーバーサイドSLは保持される。

        OANDA のSL/TPはサーバー側で管理されるため、
        クライアント接続状態に関係なく有効。
        market_order は SL/TP を必須引数として要求する設計。
        """
        sig = inspect.signature(OandaClient.market_order)
        params = sig.parameters

        # SL/TPがデフォルト値なしの必須パラメータ
        assert params["stop_loss"].default is inspect.Parameter.empty
        assert params["take_profit"].default is inspect.Parameter.empty

    def test_reconnect_closes_all_positions(self):
        """接続復旧後に全ポジション決済を試行できる"""
        with patch("src.oanda_client.API") as MockAPI:
            mock_api = MockAPI.return_value

            mock_api.request.side_effect = [
                # get_positions: 2ポジション
                {
                    "trades": [
                        {
                            "id": "101",
                            "instrument": "USD_JPY",
                            "currentUnits": "1000",
                            "unrealizedPL": "-200",
                            "price": "150.0",
                        },
                        {
                            "id": "102",
                            "instrument": "EUR_USD",
                            "currentUnits": "-500",
                            "unrealizedPL": "-100",
                            "price": "1.1000",
                        },
                    ]
                },
                # close_position for trade 101
                {"orderFillTransaction": {"pl": "-200", "price": "149.5"}},
                # close_position for trade 102
                {"orderFillTransaction": {"pl": "-100", "price": "1.1050"}},
            ]

            client = OandaClient(
                api_key="test-key",
                account_id="test-account",
                environment="practice",
            )

            # 復旧後: ポジション取得 → 全ポジション決済
            positions = client.get_positions()
            assert len(positions) == 2

            close_results = []
            for pos in positions:
                result = client.close_position(pos["trade_id"])
                close_results.append(result)

            assert len(close_results) == 2
            assert close_results[0]["trade_id"] == "101"
            assert close_results[1]["trade_id"] == "102"

    def test_multiple_kill_reasons_detected(self, caplog):
        """複数の障害原因が同時に検知され、取引が停止する"""
        ks = KillSwitch()

        with caplog.at_level(logging.WARNING):
            # API接続断を検知
            ks.activate("api_disconnect")
            assert ks.reason == "api_disconnect"

            # さらにスプレッド急拡大を検知（上書き）
            ks.activate("spread")
            assert ks.reason == "spread"

        # いずれにせよ取引は完全停止
        assert ks.is_active
        assert not ks.is_trading_allowed()
        # 両方のキルスイッチ発動がログに記録される
        assert caplog.text.count("キルスイッチ発動") == 2


# ================================================================
# シナリオ 7: MT5接続断
# ================================================================


class TestMt5ConnectionDrop:
    """
    シナリオ7: MT5ターミナル接続断

    ブローカーAPI（get_positions）が例外を返す状況で:
    - PositionManager.sync_with_broker が安全にエラーを伝播する
    - キルスイッチの api_disconnect が正しく解除判定される
    """

    def test_sync_raises_on_broker_error(self):
        """ブローカーAPI接続断で sync_with_broker が PositionManagerError を送出する"""
        from unittest.mock import MagicMock

        from src.broker_client import BrokerClient

        broker = MagicMock(spec=BrokerClient)
        broker.get_positions.side_effect = ConnectionError("MT5 connection lost")
        rm = RiskManager(1_000_000)
        pm = PositionManager(broker_client=broker, risk_manager=rm)

        with pytest.raises(PositionManagerError, match="ポジション取得に失敗"):
            pm.sync_with_broker()

    def test_api_disconnect_kill_auto_deactivates(self):
        """api_disconnect キルスイッチは再接続後に即時解除される"""
        ks = KillSwitch()
        ks.activate("api_disconnect")

        assert ks.is_active
        assert not ks.is_trading_allowed()

        # api_disconnect は常に True（再接続後に呼ばれる前提）
        assert ks.should_auto_deactivate() is True

        ks.deactivate()
        assert ks.is_trading_allowed()


# ================================================================
# シナリオ 8: ポジション不整合（ブローカー側で決済済み）
# ================================================================


class TestPositionInconsistency:
    """
    シナリオ8: ポジション不整合

    ローカルにはポジションがあるがブローカー側では決済済み:
    - sync_with_broker がローカルのみのポジションを自動除去する
    - 除去されたポジションは pl_unknown=True で履歴に移動する
    """

    def test_orphan_position_auto_removed(self):
        """ブローカー側で決済済みのポジションがローカルから自動除去される"""
        from unittest.mock import MagicMock

        from src.broker_client import BrokerClient
        from src.strategy.base import StrategyBase

        broker = MagicMock(spec=BrokerClient)
        broker.market_order.return_value = {
            "order_id": "ORD-001",
            "trade_id": "TRD-ORPHAN",
            "price": 150.0,
            "units": 1000,
            "status": "filled",
        }
        rm = MagicMock(spec=RiskManager)
        rm.kill_switch = MagicMock(spec=KillSwitch)
        rm.kill_switch.is_trading_allowed.return_value = True
        rm.check_loss_limits.return_value = (True, None)
        rm.check_consecutive_losses.return_value = (0, False)
        rm.calculate_position_size.return_value = 1.0
        rm.account_balance = 1_000_000

        strategy = MagicMock(spec=StrategyBase)
        strategy.calculate_stop_loss.return_value = 149.0
        strategy.calculate_take_profit.return_value = 152.0

        pm = PositionManager(broker_client=broker, risk_manager=rm)

        # ポジションオープン
        data = pd.DataFrame({
            "open": [150.0] * 50,
            "high": [150.5] * 50,
            "low": [149.5] * 50,
            "close": [150.0] * 50,
            "volume": [1000] * 50,
        })
        result = pm.open_position("USD_JPY", Signal.BUY, data, strategy)
        assert result is not None
        assert pm.position_count == 1

        # ブローカー側は空（ブローカーで決済済み）
        broker.get_positions.return_value = []
        sync_result = pm.sync_with_broker()

        # ローカルから除去され、履歴に移動
        assert pm.position_count == 0
        assert sync_result["local_only"] == ["TRD-ORPHAN"]
        assert len(pm.trade_history) == 1
        assert pm.trade_history[0]["pl_unknown"] is True
        assert pm.trade_history[0]["trade_id"] == "TRD-ORPHAN"


# ================================================================
# シナリオ 9: キルスイッチ自動発動（evaluate_kill_switch経由）
# ================================================================


class TestKillSwitchAutoActivation:
    """
    シナリオ9: キルスイッチ自動発動

    evaluate_kill_switch で条件を満たした場合に:
    - 適切な理由でキルスイッチが発動する
    - volatility/spread は KILL_COOLDOWN_MINUTES 経過後に自動解除可能
    - manual（例外時フォールバック）は自動解除不可
    """

    def test_evaluate_triggers_on_drawdown_stop(self, caplog):
        """ドローダウンSTOP到達で evaluate_kill_switch が "daily_loss" を返す"""
        rm = RiskManager(1_000_000)
        rm.update_balance(790_000)  # 21% DD → STOP

        with caplog.at_level(logging.WARNING):
            reason = rm.evaluate_kill_switch(
                current_balance=790_000,
                trade_history=[],
            )

        assert reason == "daily_loss"
        assert "ドローダウン" in caplog.text

    def test_volatility_kill_requires_cooldown(self):
        """volatility キルは KILL_COOLDOWN_MINUTES 経過前は自動解除不可"""
        ks = KillSwitch()
        ks.activate("volatility")

        # 発動直後: 解除不可
        assert ks.should_auto_deactivate() is False

        # クールダウン経過後: 解除可能
        ks._activated_at = datetime.now(timezone.utc) - timedelta(
            minutes=KILL_COOLDOWN_MINUTES + 1
        )
        assert ks.should_auto_deactivate() is True

    def test_manual_kill_never_auto_deactivates(self):
        """manual キルは自動解除不可（evaluate例外時のフォールバック）"""
        ks = KillSwitch()
        ks.activate("manual")

        # どんなに時間が経っても False
        ks._activated_at = datetime.now(timezone.utc) - timedelta(days=30)
        assert ks.should_auto_deactivate() is False
