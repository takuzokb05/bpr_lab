"""
F4: risk_manager.py のユニットテスト

ポジションサイジング、ドローダウン制御、損失上限チェック、
連続負けカウンター、レバレッジチェック、キルスイッチを検証する。
SPEC.md F4 完了基準準拠。
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.risk_manager import KillSwitch, RiskManager


# ============================================================
# テスト用ヘルパー
# ============================================================

def _make_trade(pl: float, hours_ago: float = 0.0) -> dict:
    """テスト用の取引履歴エントリを作成する。"""
    close_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return {"pl": pl, "close_time": close_time}


def _make_trade_days_ago(pl: float, days_ago: float) -> dict:
    """テスト用の取引履歴エントリを日単位で作成する。"""
    close_time = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {"pl": pl, "close_time": close_time}


# ============================================================
# 1. ポジションサイジング
# ============================================================

class TestPositionSizing:
    """ポジションサイジングのテスト"""

    def test_basic_risk_rule(self):
        """口座100万円・SL50pipsでMAX_RISK_PER_TRADE(0.05%)ルールの基本計算を検証"""
        from src.config import MAX_RISK_PER_TRADE

        rm = RiskManager(account_balance=1_000_000)
        # 計算: 1,000,000 * MAX_RISK_PER_TRADE / (50 * 10.0)  (USD_JPY pip_value=10)
        lot_size = rm.calculate_position_size(
            balance=1_000_000,
            stop_loss_pips=50,
            instrument="USD_JPY",
        )
        assert lot_size == pytest.approx(1_000_000 * MAX_RISK_PER_TRADE / (50 * 10.0))

    def test_different_balance_and_sl(self):
        """異なる残高・SL幅での計算を検証（EUR_USD pip_value=12.0）"""
        from src.config import MAX_RISK_PER_TRADE

        rm = RiskManager(account_balance=500_000)
        lot_size = rm.calculate_position_size(
            balance=500_000,
            stop_loss_pips=30,
            instrument="EUR_USD",
        )
        assert lot_size == pytest.approx(500_000 * MAX_RISK_PER_TRADE / (30 * 12.0))

    def test_drawdown_reduce_halves_lot(self):
        """ドローダウン REDUCE レベル（10%）でポジションサイズが半減する"""
        from src.config import MAX_RISK_PER_TRADE

        # peak=1,000,000, current=900,000 → 10%ドローダウン → REDUCE
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        balance = 900_000  # 10%ドローダウン

        lot_size = rm.calculate_position_size(
            balance=balance,
            stop_loss_pips=50,
            instrument="USD_JPY",
        )
        # REDUCE: 通常 * 0.5
        normal = balance * MAX_RISK_PER_TRADE / (50 * 10.0)
        assert lot_size == pytest.approx(normal * 0.5)

    def test_drawdown_minimum_lot(self):
        """ドローダウン MINIMUM レベル（15%）で最小ロットに制限される"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        balance = 850_000  # 15%ドローダウン

        lot_size = rm.calculate_position_size(
            balance=balance,
            stop_loss_pips=50,
            instrument="USD_JPY",
        )
        # MINIMUM: 最小ロット 0.01
        assert lot_size == pytest.approx(0.01)

    def test_drawdown_stop_returns_zero(self):
        """ドローダウン STOP レベル（20%）で取引停止（ロット0）"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        balance = 800_000  # 20%ドローダウン

        lot_size = rm.calculate_position_size(
            balance=balance,
            stop_loss_pips=50,
            instrument="USD_JPY",
        )
        assert lot_size == 0.0

    def test_drawdown_emergency_returns_zero(self):
        """ドローダウン EMERGENCY レベル（25%）で取引停止（ロット0）"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        balance = 750_000  # 25%ドローダウン

        lot_size = rm.calculate_position_size(
            balance=balance,
            stop_loss_pips=50,
            instrument="USD_JPY",
        )
        assert lot_size == 0.0

    def test_invalid_balance_raises(self):
        """口座残高0以下で ValueError"""
        rm = RiskManager(account_balance=1_000_000)
        with pytest.raises(ValueError, match="口座残高"):
            rm.calculate_position_size(
                balance=0,
                stop_loss_pips=50,
                instrument="USD_JPY",
            )

    def test_invalid_sl_pips_raises(self):
        """SL幅0以下で ValueError"""
        rm = RiskManager(account_balance=1_000_000)
        with pytest.raises(ValueError, match="損切り幅"):
            rm.calculate_position_size(
                balance=1_000_000,
                stop_loss_pips=0,
                instrument="USD_JPY",
            )


# ============================================================
# 2. ドローダウン制御
# ============================================================

class TestDrawdownControl:
    """ドローダウン制御のテスト（5段階 + 境界値）"""

    def setup_method(self):
        """各テスト前に RiskManager を初期化"""
        self.rm = RiskManager(account_balance=1_000_000)

    def test_no_drawdown(self):
        """ドローダウンなし（残高 >= ピーク）"""
        rate, level, action = self.rm.check_drawdown(1_000_000, 1_000_000)
        assert rate == 0.0
        assert level is None
        assert action is None

    def test_small_drawdown_below_warning(self):
        """ドローダウン 4.9%（WARNING 未満）"""
        rate, level, action = self.rm.check_drawdown(951_000, 1_000_000)
        # 4.9% → どのレベルにも該当しない
        assert rate == pytest.approx(0.049)
        assert level is None
        assert action is None

    def test_warning_boundary_exact(self):
        """ドローダウン 5.0%ちょうど（WARNING 境界）"""
        rate, level, action = self.rm.check_drawdown(950_000, 1_000_000)
        assert rate == pytest.approx(0.05)
        assert level == "WARNING"
        assert action == "警告通知を送信"

    def test_warning_boundary_just_above(self):
        """ドローダウン 5.1%（WARNING 直上）"""
        rate, level, action = self.rm.check_drawdown(949_000, 1_000_000)
        assert rate == pytest.approx(0.051)
        assert level == "WARNING"

    def test_reduce_boundary_exact(self):
        """ドローダウン 10.0%ちょうど（REDUCE 境界）"""
        rate, level, action = self.rm.check_drawdown(900_000, 1_000_000)
        assert rate == pytest.approx(0.10)
        assert level == "REDUCE"
        assert action == "ポジションサイズを半減"

    def test_reduce_boundary_just_below(self):
        """ドローダウン 9.9%（REDUCE 未満 → WARNING）"""
        rate, level, action = self.rm.check_drawdown(901_000, 1_000_000)
        assert rate == pytest.approx(0.099)
        assert level == "WARNING"

    def test_minimum_boundary_exact(self):
        """ドローダウン 15.0%ちょうど（MINIMUM 境界）"""
        rate, level, action = self.rm.check_drawdown(850_000, 1_000_000)
        assert rate == pytest.approx(0.15)
        assert level == "MINIMUM"
        assert action == "最小ロットのみ許可"

    def test_stop_boundary_exact(self):
        """ドローダウン 20.0%ちょうど（STOP 境界）"""
        rate, level, action = self.rm.check_drawdown(800_000, 1_000_000)
        assert rate == pytest.approx(0.20)
        assert level == "STOP"
        assert action == "新規取引を全停止"

    def test_emergency_boundary_exact(self):
        """ドローダウン 25.0%ちょうど（EMERGENCY 境界）"""
        rate, level, action = self.rm.check_drawdown(750_000, 1_000_000)
        assert rate == pytest.approx(0.25)
        assert level == "EMERGENCY"
        assert action == "全ポジションを強制決済"

    def test_emergency_exceeded(self):
        """ドローダウン 30%超過（EMERGENCY を超えても EMERGENCY）"""
        rate, level, action = self.rm.check_drawdown(700_000, 1_000_000)
        assert rate == pytest.approx(0.30)
        assert level == "EMERGENCY"

    def test_invalid_peak_balance_raises(self):
        """最高残高0以下で ValueError"""
        with pytest.raises(ValueError, match="最高残高"):
            self.rm.check_drawdown(900_000, 0)

    def test_balance_above_peak(self):
        """残高がピークより高い場合はドローダウン0"""
        rate, level, action = self.rm.check_drawdown(1_100_000, 1_000_000)
        assert rate == 0.0
        assert level is None


# ============================================================
# 3. 損失上限チェック
# ============================================================

class TestLossLimits:
    """日次・週次・月次の損失上限チェックのテスト"""

    def setup_method(self):
        """各テスト前に RiskManager を初期化"""
        self.rm = RiskManager(account_balance=1_000_000)

    def test_no_trades_allowed(self):
        """取引履歴が空なら許可"""
        is_allowed, reason = self.rm.check_loss_limits([])
        assert is_allowed is True
        assert reason is None

    def test_daily_loss_within_limit(self):
        """日次損失が上限内（4.9%）なら許可（STAGE2: 上限5%）"""
        trades = [
            _make_trade(-49_000, hours_ago=1),  # 4.9%
        ]
        is_allowed, reason = self.rm.check_loss_limits(trades)
        assert is_allowed is True

    def test_daily_loss_at_limit(self):
        """日次損失が上限到達（5.0%）で停止"""
        trades = [
            _make_trade(-50_000, hours_ago=1),  # 5.0%ちょうど
        ]
        is_allowed, reason = self.rm.check_loss_limits(trades)
        assert is_allowed is False
        assert "日次損失上限" in reason

    def test_daily_loss_just_above_limit(self):
        """日次損失が上限微超（5.1%）で停止"""
        trades = [
            _make_trade(-51_000, hours_ago=1),  # 5.1%
        ]
        is_allowed, reason = self.rm.check_loss_limits(trades)
        assert is_allowed is False
        assert "日次損失上限" in reason

    def test_weekly_loss_at_limit(self):
        """週次損失が上限到達（10.0%）で停止（STAGE2: 上限10%）"""
        # 日次5%未満に収まるように分散（合計10万円=10%）
        trades = [
            _make_trade(-25_000, hours_ago=30),
            _make_trade(-25_000, hours_ago=50),
            _make_trade(-25_000, hours_ago=72),
            _make_trade(-25_000, hours_ago=96),
        ]
        is_allowed, reason = self.rm.check_loss_limits(trades)
        assert is_allowed is False
        assert "週次損失上限" in reason

    def test_monthly_loss_at_limit(self):
        """月次損失が上限到達（20.0%）で停止（STAGE2: 上限20%）"""
        # 日次5%・週次10%の上限に引っかからないように分散（合計20万円=20%）
        trades = [
            _make_trade(-30_000, hours_ago=200),
            _make_trade(-30_000, hours_ago=250),
            _make_trade(-30_000, hours_ago=300),
            _make_trade(-30_000, hours_ago=350),
            _make_trade(-30_000, hours_ago=400),
            _make_trade(-30_000, hours_ago=450),
            _make_trade(-20_000, hours_ago=500),
        ]
        is_allowed, reason = self.rm.check_loss_limits(trades)
        assert is_allowed is False
        assert "月次損失上限" in reason

    def test_old_trades_not_counted(self):
        """30日以上前の取引は月次にもカウントされない"""
        trades = [
            _make_trade_days_ago(-100_000, days_ago=31),
        ]
        is_allowed, reason = self.rm.check_loss_limits(trades)
        assert is_allowed is True

    def test_winning_trades_not_counted_as_loss(self):
        """利益取引は損失にカウントされない"""
        trades = [
            _make_trade(50_000, hours_ago=1),  # 利益
            _make_trade(-5_000, hours_ago=2),  # 小さい損失
        ]
        is_allowed, reason = self.rm.check_loss_limits(trades)
        assert is_allowed is True


# ============================================================
# 4. 連続負けカウンター
# ============================================================

class TestConsecutiveLosses:
    """連続負けカウンターのテスト"""

    def setup_method(self):
        """各テスト前に RiskManager を初期化"""
        self.rm = RiskManager(account_balance=1_000_000)

    def test_no_trades(self):
        """取引履歴が空なら0連敗・停止なし"""
        count, is_stopped = self.rm.check_consecutive_losses([])
        assert count == 0
        assert is_stopped is False

    def test_no_consecutive_losses(self):
        """直近が勝ちなら0連敗"""
        trades = [
            {"pl": -100}, {"pl": -200}, {"pl": 500},
        ]
        count, is_stopped = self.rm.check_consecutive_losses(trades)
        assert count == 0
        assert is_stopped is False

    def test_three_consecutive_losses(self):
        """3連敗 → カウント3、停止なし"""
        trades = [
            {"pl": 500}, {"pl": -100}, {"pl": -200}, {"pl": -300},
        ]
        count, is_stopped = self.rm.check_consecutive_losses(trades)
        assert count == 3
        assert is_stopped is False

    def test_four_consecutive_losses_not_stopped(self):
        """4連敗 → カウント4、停止なし（上限5未満）"""
        trades = [
            {"pl": 500},
            {"pl": -100}, {"pl": -200}, {"pl": -300}, {"pl": -400},
        ]
        count, is_stopped = self.rm.check_consecutive_losses(trades)
        assert count == 4
        assert is_stopped is False

    def test_five_consecutive_losses_stopped(self):
        """5連敗 → カウント5、上限10未満なので停止しない（STAGE2: 上限を10に緩和）"""
        trades = [
            {"pl": 500},
            {"pl": -100}, {"pl": -200}, {"pl": -300},
            {"pl": -400}, {"pl": -500},
        ]
        count, is_stopped = self.rm.check_consecutive_losses(trades)
        assert count == 5
        assert is_stopped is False

    def test_six_consecutive_losses_stopped(self):
        """6連敗 → 上限10未満なので停止しない"""
        trades = [
            {"pl": -10}, {"pl": -20}, {"pl": -30},
            {"pl": -40}, {"pl": -50}, {"pl": -60},
        ]
        count, is_stopped = self.rm.check_consecutive_losses(trades)
        assert count == 6
        assert is_stopped is False

    def test_ten_consecutive_losses_stopped(self):
        """10連敗 → 上限到達で停止"""
        trades = [{"pl": -(i + 1) * 10} for i in range(10)]
        count, is_stopped = self.rm.check_consecutive_losses(trades)
        assert count == 10
        assert is_stopped is True

    def test_loss_break_resets_count(self):
        """途中で勝つと連続負けがリセットされる"""
        trades = [
            {"pl": -100}, {"pl": -200}, {"pl": -300},  # 3連敗
            {"pl": 100},                                 # 勝ち（リセット）
            {"pl": -400}, {"pl": -500},                  # 2連敗
        ]
        count, is_stopped = self.rm.check_consecutive_losses(trades)
        assert count == 2
        assert is_stopped is False

    def test_zero_pl_breaks_streak(self):
        """PL=0（引き分け）で連続負けが途切れる"""
        trades = [
            {"pl": -100}, {"pl": -200}, {"pl": 0}, {"pl": -300},
        ]
        count, is_stopped = self.rm.check_consecutive_losses(trades)
        assert count == 1  # 最後の-300だけ
        assert is_stopped is False


# ============================================================
# 5. レバレッジ制限
# ============================================================

class TestLeverageCheck:
    """レバレッジチェックのテスト"""

    def setup_method(self):
        """各テスト前に RiskManager を初期化"""
        self.rm = RiskManager(account_balance=1_000_000)

    def test_low_leverage_allowed(self):
        """レバレッジ5倍 → 許可"""
        leverage, is_allowed = self.rm.check_leverage(5_000_000, 1_000_000)
        assert leverage == pytest.approx(5.0)
        assert is_allowed is True

    def test_leverage_exactly_10_allowed(self):
        """レバレッジ10倍ちょうど → 許可"""
        leverage, is_allowed = self.rm.check_leverage(10_000_000, 1_000_000)
        assert leverage == pytest.approx(10.0)
        assert is_allowed is True

    def test_leverage_10_1_rejected(self):
        """レバレッジ10.1倍 → 拒否"""
        leverage, is_allowed = self.rm.check_leverage(10_100_000, 1_000_000)
        assert leverage == pytest.approx(10.1)
        assert is_allowed is False

    def test_leverage_25_rejected(self):
        """レバレッジ25倍 → 拒否"""
        leverage, is_allowed = self.rm.check_leverage(25_000_000, 1_000_000)
        assert leverage == pytest.approx(25.0)
        assert is_allowed is False

    def test_no_position_allowed(self):
        """ポジションなし（0倍） → 許可"""
        leverage, is_allowed = self.rm.check_leverage(0, 1_000_000)
        assert leverage == pytest.approx(0.0)
        assert is_allowed is True

    def test_invalid_balance_raises(self):
        """口座残高0以下で ValueError"""
        with pytest.raises(ValueError, match="口座残高"):
            self.rm.check_leverage(5_000_000, 0)


# ============================================================
# 6. キルスイッチ
# ============================================================

class TestKillSwitch:
    """キルスイッチのテスト"""

    def setup_method(self):
        """各テスト前に KillSwitch を初期化"""
        self.ks = KillSwitch()

    def test_initial_state(self):
        """初期状態: 未発動"""
        assert self.ks.is_active is False
        assert self.ks.reason is None
        assert self.ks.activated_at is None
        assert self.ks.is_trading_allowed() is True

    def test_activate_daily_loss(self):
        """日次損失キルの発動"""
        self.ks.activate("daily_loss")
        assert self.ks.is_active is True
        assert self.ks.reason == "daily_loss"
        assert self.ks.activated_at is not None
        assert self.ks.is_trading_allowed() is False

    def test_activate_consecutive_losses(self):
        """連続負けキルの発動"""
        self.ks.activate("consecutive_losses")
        assert self.ks.is_active is True
        assert self.ks.reason == "consecutive_losses"

    def test_activate_volatility(self):
        """ボラティリティキルの発動"""
        self.ks.activate("volatility")
        assert self.ks.is_active is True
        assert self.ks.reason == "volatility"

    def test_activate_spread(self):
        """スプレッドキルの発動"""
        self.ks.activate("spread")
        assert self.ks.is_active is True
        assert self.ks.reason == "spread"

    def test_activate_api_disconnect(self):
        """API切断キルの発動"""
        self.ks.activate("api_disconnect")
        assert self.ks.is_active is True
        assert self.ks.reason == "api_disconnect"

    def test_activate_manual(self):
        """手動キルの発動"""
        self.ks.activate("manual")
        assert self.ks.is_active is True
        assert self.ks.reason == "manual"

    def test_activate_invalid_reason_raises(self):
        """不正な理由で ValueError"""
        with pytest.raises(ValueError, match="不正なキルスイッチ理由"):
            self.ks.activate("invalid_reason")

    def test_deactivate(self):
        """キルスイッチの解除"""
        self.ks.activate("manual")
        assert self.ks.is_active is True

        self.ks.deactivate()
        assert self.ks.is_active is False
        assert self.ks.reason is None
        assert self.ks.activated_at is None
        assert self.ks.is_trading_allowed() is True

    def test_deactivate_when_not_active(self):
        """未発動時の解除は何もしない（エラーなし）"""
        self.ks.deactivate()  # 例外が出なければOK
        assert self.ks.is_active is False

    def test_all_six_reasons_valid(self):
        """6種類全ての発動理由が受け入れられる"""
        valid_reasons = [
            "daily_loss",
            "consecutive_losses",
            "volatility",
            "spread",
            "api_disconnect",
            "manual",
        ]
        for reason in valid_reasons:
            ks = KillSwitch()
            ks.activate(reason)
            assert ks.is_active is True
            assert ks.reason == reason


# ============================================================
# 7. RiskManager 初期化
# ============================================================

class TestRiskManagerInit:
    """RiskManager の初期化テスト"""

    def test_valid_initialization(self):
        """正常な初期化"""
        rm = RiskManager(account_balance=1_000_000)
        assert rm.account_balance == 1_000_000
        assert rm.peak_balance == 1_000_000
        assert rm.kill_switch.is_active is False

    def test_invalid_balance_raises(self):
        """口座残高0以下で ValueError"""
        with pytest.raises(ValueError, match="口座残高"):
            RiskManager(account_balance=0)

    def test_negative_balance_raises(self):
        """口座残高が負で ValueError"""
        with pytest.raises(ValueError, match="口座残高"):
            RiskManager(account_balance=-100_000)


# ============================================================
# 8. update_balance
# ============================================================

class TestUpdateBalance:
    """update_balance のテスト"""

    def test_update_balance_normal(self):
        """残高更新が正常に反映される"""
        rm = RiskManager(account_balance=1_000_000)
        rm.update_balance(1_100_000)
        assert rm.account_balance == 1_100_000

    def test_update_balance_updates_peak(self):
        """残高がピーク超過時にピーク残高も更新"""
        rm = RiskManager(account_balance=1_000_000)
        rm.update_balance(1_200_000)
        assert rm.peak_balance == 1_200_000

    def test_update_balance_does_not_lower_peak(self):
        """残高がピーク以下でもピーク残高は下がらない"""
        rm = RiskManager(account_balance=1_000_000)
        rm.update_balance(900_000)
        assert rm.peak_balance == 1_000_000
        assert rm.account_balance == 900_000

    def test_update_balance_zero_allowed(self):
        """残高0は許可される（ただし取引は停止すべき）"""
        rm = RiskManager(account_balance=1_000_000)
        rm.update_balance(0)
        assert rm.account_balance == 0

    def test_update_balance_negative_raises(self):
        """負の残高で ValueError"""
        rm = RiskManager(account_balance=1_000_000)
        with pytest.raises(ValueError, match="負の値"):
            rm.update_balance(-100)


# ============================================================
# 9. 安全側フォールバック
# ============================================================

class TestSafetyFallback:
    """安全側フォールバック（不正データ）のテスト"""

    def setup_method(self):
        self.rm = RiskManager(account_balance=1_000_000)

    def test_loss_limits_missing_key_stops_trading(self):
        """取引履歴に必須キーがない場合、取引停止"""
        bad_trades = [{"amount": 100}]  # "pl" キーがない
        is_allowed, reason = self.rm.check_loss_limits(bad_trades)
        assert is_allowed is False
        assert "データ不正" in reason

    def test_consecutive_losses_missing_key_stops_trading(self):
        """取引履歴に必須キーがない場合、連続負けは停止扱い"""
        bad_trades = [{"amount": 100}]  # "pl" キーがない
        count, is_stopped = self.rm.check_consecutive_losses(bad_trades)
        assert count == 0
        assert is_stopped is True

    def test_loss_limits_none_pl_stops_trading(self):
        """plがNoneの場合、取引停止"""
        bad_trades = [{"pl": None, "close_time": datetime.now(timezone.utc)}]
        is_allowed, reason = self.rm.check_loss_limits(bad_trades)
        assert is_allowed is False

    def test_loss_limits_naive_datetime_ok(self):
        """timezone-naive datetime でもエラーにならない（UTCとして扱う）"""
        trades = [
            {"pl": -5_000, "close_time": datetime.now()},  # naive
        ]
        is_allowed, reason = self.rm.check_loss_limits(trades)
        # 0.5%損失 < 2%上限 → 許可
        assert is_allowed is True


# ============================================================
# 10. pip_value 動的計算（F11）
# ============================================================

class TestDynamicPipValue:
    """_get_pip_value() の動的計算テスト（F11）"""

    def _make_mock_broker(self, close_price: float):
        """指定したclose価格を返すモックbroker_clientを作成する。"""
        from unittest.mock import MagicMock

        import pandas as pd

        mock_broker = MagicMock()
        df = pd.DataFrame({"close": [close_price]})
        mock_broker.get_prices.return_value = df
        return mock_broker

    def test_jpy_cross_dynamic_default_lot(self):
        """JPYクロスの動的pip_value計算（デフォルトlot_size=1000）"""
        mock_broker = self._make_mock_broker(150.0)
        rm = RiskManager(account_balance=1_000_000, broker_client=mock_broker)

        # JPYクロス: 0.01 * 1000 = 10.0（ブローカーAPIは呼ばれない）
        pip_value = rm._get_pip_value("USD_JPY")
        assert pip_value == pytest.approx(10.0)
        mock_broker.get_prices.assert_not_called()

    def test_jpy_cross_dynamic_custom_lot(self):
        """JPYクロスの動的pip_value計算（lot_size=10000）"""
        mock_broker = self._make_mock_broker(150.0)
        rm = RiskManager(account_balance=1_000_000, broker_client=mock_broker)

        # JPYクロス: 0.01 * 10000 = 100.0
        pip_value = rm._get_pip_value("EUR_JPY", lot_size=10000)
        assert pip_value == pytest.approx(100.0)
        mock_broker.get_prices.assert_not_called()

    def test_non_jpy_dynamic_with_usdjpy_rate(self):
        """非JPYペアの動的pip_value計算（USD/JPYレート使用）"""
        # EUR_USD → 決済通貨USD → USD_JPYレートが必要
        mock_broker = self._make_mock_broker(150.0)
        rm = RiskManager(account_balance=1_000_000, broker_client=mock_broker)

        # 非JPY: 0.0001 * 1000 * 150.0 = 15.0
        pip_value = rm._get_pip_value("EUR_USD")
        assert pip_value == pytest.approx(15.0)
        mock_broker.get_prices.assert_called_once_with("USD_JPY", 1, "M1")

    def test_non_jpy_dynamic_gbpusd(self):
        """GBP_USDの動的pip_value計算（USD_JPYレート使用）"""
        mock_broker = self._make_mock_broker(145.50)
        rm = RiskManager(account_balance=1_000_000, broker_client=mock_broker)

        # GBP_USD → 決済通貨USD → USD_JPY = 145.50
        # 0.0001 * 1000 * 145.50 = 14.55
        pip_value = rm._get_pip_value("GBP_USD")
        assert pip_value == pytest.approx(14.55)
        mock_broker.get_prices.assert_called_once_with("USD_JPY", 1, "M1")

    def test_non_jpy_dynamic_custom_lot(self):
        """非JPYペアの動的pip_value計算（lot_size=10000）"""
        mock_broker = self._make_mock_broker(150.0)
        rm = RiskManager(account_balance=1_000_000, broker_client=mock_broker)

        # 0.0001 * 10000 * 150.0 = 150.0
        pip_value = rm._get_pip_value("EUR_USD", lot_size=10000)
        assert pip_value == pytest.approx(150.0)

    def test_fallback_no_broker_client_jpy(self):
        """broker_client未設定時のフォールバック（JPYクロス）"""
        rm = RiskManager(account_balance=1_000_000)  # broker_client=None

        # JPYクロス: 0.01 * 1000 = 10.0（フォールバック値と同値だが動的計算結果）
        pip_value = rm._get_pip_value("USD_JPY")
        assert pip_value == pytest.approx(10.0)

    def test_fallback_no_broker_client_non_jpy(self):
        """broker_client未設定時のフォールバック（非JPYペア → 固定値12.0）"""
        rm = RiskManager(account_balance=1_000_000)  # broker_client=None

        pip_value = rm._get_pip_value("EUR_USD")
        assert pip_value == pytest.approx(12.0)

    def test_fallback_broker_api_failure(self):
        """ブローカーAPI失敗時のフォールバック（非JPYペア → 固定値12.0）"""
        from unittest.mock import MagicMock

        mock_broker = MagicMock()
        mock_broker.get_prices.side_effect = ConnectionError("API接続エラー")
        rm = RiskManager(account_balance=1_000_000, broker_client=mock_broker)

        pip_value = rm._get_pip_value("EUR_USD")
        assert pip_value == pytest.approx(12.0)

    def test_fallback_rate_zero(self):
        """取得レート0の場合のフォールバック（異常値 → 固定値12.0）"""
        mock_broker = self._make_mock_broker(0.0)
        rm = RiskManager(account_balance=1_000_000, broker_client=mock_broker)

        pip_value = rm._get_pip_value("EUR_USD")
        assert pip_value == pytest.approx(12.0)

    def test_fallback_rate_negative(self):
        """取得レートが負の場合のフォールバック（異常値 → 固定値12.0）"""
        mock_broker = self._make_mock_broker(-100.0)
        rm = RiskManager(account_balance=1_000_000, broker_client=mock_broker)

        pip_value = rm._get_pip_value("EUR_USD")
        assert pip_value == pytest.approx(12.0)

    def test_calculate_position_size_uses_dynamic_pip_value(self):
        """calculate_position_sizeが動的pip_valueを使用することの確認"""
        from src.config import MAX_RISK_PER_TRADE

        # USD_JPYレート = 150.0 → EUR_USD pip_value = 0.0001 * 1000 * 150 = 15.0
        mock_broker = self._make_mock_broker(150.0)
        rm = RiskManager(account_balance=1_000_000, broker_client=mock_broker)

        lot_size = rm.calculate_position_size(
            balance=1_000_000,
            stop_loss_pips=50,
            instrument="EUR_USD",
        )
        expected = 1_000_000 * MAX_RISK_PER_TRADE / (50 * 15.0)
        assert lot_size == pytest.approx(expected)

    def test_calculate_position_size_fallback_without_broker(self):
        """broker_client未設定時にcalculate_position_sizeがフォールバック値を使用"""
        from src.config import MAX_RISK_PER_TRADE

        rm = RiskManager(account_balance=1_000_000)  # broker_client=None

        # フォールバック pip_value=12.0 で計算
        lot_size = rm.calculate_position_size(
            balance=1_000_000,
            stop_loss_pips=50,
            instrument="EUR_USD",
        )
        expected = 1_000_000 * MAX_RISK_PER_TRADE / (50 * 12.0)
        assert lot_size == pytest.approx(expected)

    def test_backward_compatibility_init_without_broker(self):
        """後方互換性: broker_client引数なしでRiskManagerを初期化できる"""
        rm = RiskManager(account_balance=500_000)
        assert rm.account_balance == 500_000
        assert rm._broker_client is None


# ============================================================
# 11. キルスイッチ総合評価（F14: evaluate_kill_switch）
# ============================================================

class TestEvaluateKillSwitch:
    """evaluate_kill_switch() のテスト"""

    def test_evaluate_dd_stop_triggers(self):
        """DD STOP到達で "daily_loss" 返却"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        # 20%ドローダウン → STOP レベル
        result = rm.evaluate_kill_switch(
            current_balance=800_000,
            trade_history=[],
        )
        assert result == "daily_loss"

    def test_evaluate_dd_emergency_triggers(self):
        """DD EMERGENCY到達で "daily_loss" 返却"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        # 25%ドローダウン → EMERGENCY レベル
        result = rm.evaluate_kill_switch(
            current_balance=750_000,
            trade_history=[],
        )
        assert result == "daily_loss"

    def test_evaluate_daily_loss_triggers(self):
        """日次損失上限で "daily_loss" 返却（STAGE2: 上限5%）"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        # 日次損失5%以上（ドローダウンはSTOP未満に保つ）
        trades = [
            _make_trade(-50_000, hours_ago=1),  # 5% → 上限到達
        ]
        result = rm.evaluate_kill_switch(
            current_balance=950_000,  # DD 5% → WARNING〜REDUCEレベル
            trade_history=trades,
        )
        assert result == "daily_loss"

    def test_evaluate_consecutive_losses_triggers(self):
        """10連敗で "consecutive_losses" 返却（STAGE2: 上限10）"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        # 損失合計が小さく日次上限に引っかからないように、close_timeも設定
        trades = [_make_trade(-100, hours_ago=i + 1) for i in range(10)]
        result = rm.evaluate_kill_switch(
            current_balance=990_000,  # DD小さい
            trade_history=trades,
        )
        assert result == "consecutive_losses"

    def test_evaluate_volatility_triggers(self):
        """ATR基準の3倍で "volatility" 返却"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        result = rm.evaluate_kill_switch(
            current_balance=990_000,
            trade_history=[],
            current_atr=0.03,
            normal_atr=0.01,  # 0.03 >= 0.01 * 3.0
        )
        assert result == "volatility"

    def test_evaluate_spread_triggers(self):
        """スプレッド基準の5倍で "spread" 返却"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        result = rm.evaluate_kill_switch(
            current_balance=990_000,
            trade_history=[],
            current_spread=0.05,
            normal_spread=0.01,  # 0.05 >= 0.01 * 5.0
        )
        assert result == "spread"

    def test_evaluate_all_clear(self):
        """全条件クリアで None 返却"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        result = rm.evaluate_kill_switch(
            current_balance=990_000,  # DD 1% → 問題なし
            trade_history=[],
            current_atr=0.01,
            normal_atr=0.01,  # ATR正常
            current_spread=0.01,
            normal_spread=0.01,  # スプレッド正常
        )
        assert result is None

    def test_evaluate_exception_returns_safe(self):
        """例外発生で安全側（"manual" — 手動解除強制）"""
        rm = RiskManager(account_balance=1_000_000)
        rm._peak_balance = 1_000_000
        # check_drawdown に不正な値を渡して例外を誘発
        # peak_balance を0に設定して例外を発生させる
        rm._peak_balance = 0
        result = rm.evaluate_kill_switch(
            current_balance=900_000,
            trade_history=[],
        )
        assert result == "manual"


# ============================================================
# 12. キルスイッチ自動解除（F14: should_auto_deactivate）
# ============================================================

class TestKillSwitchAutoDeactivate:
    """should_auto_deactivate() のテスト"""

    def test_daily_loss_deactivate_next_day(self):
        """daily_loss → 翌日0:00 UTC以降で True"""
        ks = KillSwitch()
        ks.activate("daily_loss")
        # activated_at を確定的な時刻に設定
        activated_time = datetime(2025, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        ks._activated_at = activated_time
        # 翌日0:00 UTC
        next_day = datetime(2025, 6, 16, 0, 0, 0, tzinfo=timezone.utc)
        assert ks.should_auto_deactivate(current_time=next_day) is True

    def test_daily_loss_not_deactivate_same_day(self):
        """daily_loss → 同日は False"""
        ks = KillSwitch()
        ks.activate("daily_loss")
        activated_time = datetime(2025, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        ks._activated_at = activated_time
        # 同日23:59
        same_day = datetime(2025, 6, 15, 23, 59, 59, tzinfo=timezone.utc)
        assert ks.should_auto_deactivate(current_time=same_day) is False

    def test_consecutive_losses_deactivate_after_24h(self):
        """24時間経過で True"""
        ks = KillSwitch()
        ks.activate("consecutive_losses")
        activated_time = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        ks._activated_at = activated_time
        # 24時間後
        after_24h = datetime(2025, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
        assert ks.should_auto_deactivate(current_time=after_24h) is True

    def test_manual_never_auto_deactivate(self):
        """manual → 常に False"""
        ks = KillSwitch()
        ks.activate("manual")
        # 未来の時刻でも解除されない
        far_future = datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert ks.should_auto_deactivate(current_time=far_future) is False

    def test_volatility_deactivate_after_cooldown(self):
        """volatility → クールダウン（5分）経過後にTrue"""
        from src.config import KILL_COOLDOWN_MINUTES

        ks = KillSwitch()
        ks.activate("volatility")
        activated_time = datetime(2025, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        ks._activated_at = activated_time

        # クールダウン前 → False
        before_cooldown = datetime(2025, 6, 15, 10, 4, 0, tzinfo=timezone.utc)
        assert ks.should_auto_deactivate(current_time=before_cooldown) is False

        # クールダウン後 → True
        after_cooldown = activated_time + timedelta(minutes=KILL_COOLDOWN_MINUTES)
        assert ks.should_auto_deactivate(current_time=after_cooldown) is True

    def test_not_active_returns_false(self):
        """未発動時は False"""
        ks = KillSwitch()
        assert ks.should_auto_deactivate() is False
