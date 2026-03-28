"""
FX自動取引システム — バックテストエンジンのテスト

src/backtester.py の BacktestEngine / RsiMaCrossoverBT / ヘルパー関数をテストする。
SPEC.md F8 テストケース準拠（15件）。
"""

import numpy as np
import pandas as pd
import pytest

from src.backtester import (
    BacktestEngine,
    BacktestError,
    RsiMaCrossoverBT,
    apply_fill_rate_adjustment,
    calculate_spread,
)
from src.config import (
    ADX_PERIOD,
    ADX_THRESHOLD,
    ATR_MULTIPLIER,
    ATR_PERIOD,
    MA_LONG_PERIOD,
    MA_SHORT_PERIOD,
    MIN_RISK_REWARD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    RSI_PERIOD,
)


# ================================================================
# テストヘルパー: 合成OHLCVデータ生成
# ================================================================


def _generate_prepared_data(n_bars: int = 400, seed: int = 42) -> pd.DataFrame:
    """
    Backtesting.py用の合成OHLCVデータを生成する（大文字カラム名）。

    サイン波ベースの価格変動を生成し、MAクロスオーバーが確実に
    複数回発生するようにする。
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n_bars, freq="4h")

    # サイン波で明確なトレンド変化を作る（振幅20、4サイクル/400本）
    t = np.linspace(0, 8 * np.pi, n_bars)
    base = 100 + 20 * np.sin(t)
    noise = rng.normal(0, 0.3, n_bars)
    close = base + noise

    # OHLC関係を保持（high >= max(open, close), low <= min(open, close)）
    open_ = np.roll(close, 1)
    open_[0] = close[0]
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


def _generate_raw_data(n_bars: int = 400, seed: int = 42) -> pd.DataFrame:
    """DataCollector出力相当の小文字カラム名OHLCVデータを生成する。"""
    df = _generate_prepared_data(n_bars, seed)
    df.columns = [c.lower() for c in df.columns]
    return df


# ================================================================
# フィクスチャ
# ================================================================


@pytest.fixture
def engine():
    """インメモリDBのBacktestEngine"""
    with BacktestEngine(db_path=":memory:") as eng:
        yield eng


@pytest.fixture
def prepared_data():
    """400本の合成OHLCVデータ（大文字カラム名）"""
    return _generate_prepared_data(n_bars=400)


@pytest.fixture
def large_data():
    """600本の合成OHLCVデータ（ウォークフォワード用）"""
    return _generate_prepared_data(n_bars=600, seed=123)


# ================================================================
# 1-2. prepare_data テスト
# ================================================================


class TestPrepareData:
    """BacktestEngine.prepare_data() のテスト"""

    def test_column_name_conversion(self):
        """小文字カラム名が大文字に変換される"""
        raw = _generate_raw_data(n_bars=100)
        assert list(raw.columns) == ["open", "high", "low", "close", "volume"]

        result = BacktestEngine.prepare_data(raw)
        assert list(result.columns) == ["Open", "High", "Low", "Close", "Volume"]

    def test_nan_removal(self):
        """NaN行が除去される"""
        raw = _generate_raw_data(n_bars=100)
        # 先頭3行にNaNを挿入
        raw.iloc[0, 0] = np.nan
        raw.iloc[1, 2] = np.nan
        raw.iloc[2, 4] = np.nan

        result = BacktestEngine.prepare_data(raw)
        assert len(result) == 97
        assert not result.isnull().any().any()


# ================================================================
# 3-5. run テスト
# ================================================================


class TestRun:
    """BacktestEngine.run() のテスト"""

    def test_run_executes_successfully(self, engine, prepared_data):
        """合成データでバックテストが実行できる"""
        result = engine.run(prepared_data, RsiMaCrossoverBT)
        assert isinstance(result, dict)
        assert isinstance(result["total_trades"], int)
        assert result["total_trades"] >= 0

    def test_run_short_data_raises(self, engine):
        """データが短すぎるとBacktestError"""
        short_data = _generate_prepared_data(n_bars=30)
        with pytest.raises(BacktestError, match="データ不足"):
            engine.run(short_data, RsiMaCrossoverBT)

    def test_run_metrics_present(self, engine, prepared_data):
        """主要メトリクスが全て含まれる"""
        result = engine.run(prepared_data, RsiMaCrossoverBT)

        expected_keys = [
            "sharpe_ratio",
            "max_drawdown",
            "win_rate",
            "profit_factor",
            "total_trades",
            "return_pct",
            "equity_final",
            "sortino_ratio",
            "calmar_ratio",
            "avg_trade_pct",
            "sqn",
        ]
        for key in expected_keys:
            assert key in result, f"キー '{key}' が結果に含まれていません"


# ================================================================
# 6-8. run_in_out_sample テスト
# ================================================================


class TestInOutSample:
    """BacktestEngine.run_in_out_sample() のテスト"""

    def test_result_structure(self, engine, prepared_data):
        """IS/OOS結果の構造を検証する"""
        result = engine.run_in_out_sample(
            prepared_data, RsiMaCrossoverBT, split_ratio=0.7
        )

        assert "in_sample" in result
        assert "out_of_sample" in result
        assert "wfe" in result

        # IS/OOS結果はrun()と同じメトリクスを持つ
        assert "sharpe_ratio" in result["in_sample"]
        assert "total_trades" in result["in_sample"]
        assert "sharpe_ratio" in result["out_of_sample"]
        assert "total_trades" in result["out_of_sample"]

    def test_wfe_calculation(self, engine, prepared_data):
        """WFE = OOS_SR / IS_SR が正しく計算される"""
        result = engine.run_in_out_sample(
            prepared_data, RsiMaCrossoverBT, split_ratio=0.7
        )

        sr_is = result["in_sample"]["sharpe_ratio"]
        sr_oos = result["out_of_sample"]["sharpe_ratio"]
        wfe = result["wfe"]

        if sr_is is not None and sr_oos is not None and sr_is != 0:
            assert wfe == pytest.approx(sr_oos / sr_is, rel=1e-6)
        else:
            # IS_SR が 0 または None → WFE は None
            assert wfe is None

    def test_insufficient_data_raises(self, engine):
        """データ不足時にBacktestError（OOS側が短すぎる）"""
        # 100本 × 0.7 → IS=70, OOS=30 → OOS < 60 でエラー
        short_data = _generate_prepared_data(n_bars=100)
        with pytest.raises(BacktestError, match="データ不足"):
            engine.run_in_out_sample(short_data, RsiMaCrossoverBT)


# ================================================================
# 9-10. run_walk_forward テスト
# ================================================================


class TestWalkForward:
    """BacktestEngine.run_walk_forward() のテスト"""

    def test_window_count(self, engine, large_data):
        """指定したウィンドウ数の結果が返る"""
        n_windows = 3
        result = engine.run_walk_forward(
            large_data, RsiMaCrossoverBT, n_windows=n_windows
        )

        assert "windows" in result
        assert len(result["windows"]) == n_windows

        for i, w in enumerate(result["windows"]):
            assert w["window"] == i + 1
            assert "in_sample" in w
            assert "out_of_sample" in w
            assert "wfe" in w

    def test_wfe_mean_calculation(self, engine, large_data):
        """WFE平均が各ウィンドウのWFEの平均と一致する"""
        result = engine.run_walk_forward(
            large_data, RsiMaCrossoverBT, n_windows=3
        )

        wfe_values = [w["wfe"] for w in result["windows"] if w["wfe"] is not None]

        if wfe_values:
            expected_mean = float(np.mean(wfe_values))
            assert result["wfe_mean"] == pytest.approx(expected_mean, rel=1e-6)
        else:
            assert result["wfe_mean"] is None


# ================================================================
# 11-12. save_result / load_results テスト
# ================================================================


class TestPersistence:
    """結果のSQLite永続化テスト"""

    def test_save_and_load_roundtrip(self, engine, prepared_data):
        """保存した結果を読み込めるラウンドトリップ検証"""
        result = engine.run(prepared_data, RsiMaCrossoverBT)
        engine.save_result(result, "USD_JPY", "H4")

        loaded = engine.load_results("USD_JPY", "H4")
        assert len(loaded) == 1

        row = loaded[0]
        assert row["instrument"] == "USD_JPY"
        assert row["granularity"] == "H4"
        assert row["strategy_name"] == "RsiMaCrossover"
        assert row["run_type"] == "single"
        assert row["sharpe_ratio"] == result["sharpe_ratio"]
        assert row["total_trades"] == result["total_trades"]

    def test_multiple_saves_order(self, engine, prepared_data):
        """複数回保存した結果が新しい順に読み込まれる"""
        result1 = engine.run(prepared_data, RsiMaCrossoverBT)
        engine.save_result(result1, "USD_JPY", "H4")

        result2 = engine.run(prepared_data, RsiMaCrossoverBT, cash=2_000_000)
        engine.save_result(result2, "USD_JPY", "H4")

        loaded = engine.load_results("USD_JPY", "H4")
        assert len(loaded) == 2
        # ORDER BY run_at DESC: 新しい方が先
        assert loaded[0]["run_at"] >= loaded[1]["run_at"]


# ================================================================
# 13. RsiMaCrossoverBT テスト
# ================================================================


class TestRsiMaCrossoverBT:
    """戦略アダプタの設定・動作テスト"""

    def test_parameters_match_config(self):
        """アダプタのパラメータがconfig.pyの定数と一致する"""
        assert RsiMaCrossoverBT.ma_short == MA_SHORT_PERIOD
        assert RsiMaCrossoverBT.ma_long == MA_LONG_PERIOD
        assert RsiMaCrossoverBT.rsi_period == RSI_PERIOD
        assert RsiMaCrossoverBT.rsi_overbought == RSI_OVERBOUGHT
        assert RsiMaCrossoverBT.rsi_oversold == RSI_OVERSOLD
        assert RsiMaCrossoverBT.atr_period == ATR_PERIOD
        assert RsiMaCrossoverBT.atr_multiplier == ATR_MULTIPLIER
        assert RsiMaCrossoverBT.min_risk_reward == MIN_RISK_REWARD
        assert RsiMaCrossoverBT.adx_period == ADX_PERIOD
        assert RsiMaCrossoverBT.adx_threshold == ADX_THRESHOLD


# ================================================================
# 14. スリッページテスト
# ================================================================


class TestSlippage:
    """スリッページ（spread）の影響テスト"""

    def test_spread_affects_return(self, engine, prepared_data):
        """spread有りの場合、リターンが低下する（または同等）"""
        result_no_spread = engine.run(
            prepared_data, RsiMaCrossoverBT, spread=0.0
        )

        spread = calculate_spread("USD_JPY", 100.0, pip_spread=1.0)
        result_with_spread = engine.run(
            prepared_data, RsiMaCrossoverBT, spread=spread
        )

        # トレードがある場合、spreadのコストでリターンが下がる
        if (
            result_no_spread["total_trades"] > 0
            and result_with_spread["total_trades"] > 0
        ):
            assert (
                result_with_spread["return_pct"] <= result_no_spread["return_pct"]
            )

        # calculate_spread の値を検証
        # USD_JPY: pip=0.01, pip_spread=1.0, price=100
        # → (0.01 * 1.0) / 100 = 0.0001
        assert spread == pytest.approx(0.0001, rel=1e-6)

        # 非JPYペアの検証
        spread_eurusd = calculate_spread("EUR_USD", 1.1, pip_spread=1.0)
        assert spread_eurusd == pytest.approx(0.0001 / 1.1, rel=1e-6)


# ================================================================
# 15. apply_fill_rate_adjustment テスト
# ================================================================


class TestFillRateAdjustment:
    """約定率補正のテスト"""

    def test_adjustment_values(self):
        """補正値が正しく計算される"""
        result = {
            "total_trades": 100,
            "return_pct": 10.0,
            "sharpe_ratio": 1.5,
        }

        adjusted = apply_fill_rate_adjustment(result, fill_rate=0.8)

        # raw値が保持される
        assert adjusted["raw_total_trades"] == 100
        assert adjusted["raw_return_pct"] == 10.0
        assert adjusted["raw_sharpe_ratio"] == 1.5

        # 補正値
        assert adjusted["adjusted_total_trades"] == 80  # 100 * 0.8
        assert adjusted["adjusted_return_pct"] == pytest.approx(8.0)  # 10 * 0.8
        assert adjusted["adjusted_sharpe_ratio"] == pytest.approx(
            1.5 * (0.8**0.5)
        )

        # fill_rate が記録される
        assert adjusted["fill_rate"] == 0.8


# ================================================================
# 16-17. M3: fill_rate 自動適用テスト
# ================================================================


class TestRunFillRate:
    """BacktestEngine.run() の fill_rate オプションテスト"""

    def test_run_with_fill_rate(self, engine, prepared_data):
        """fill_rate=0.8 指定 → adjusted_* キーが存在する"""
        result = engine.run(
            prepared_data, RsiMaCrossoverBT, fill_rate=0.8
        )

        # fill_rate が記録される
        assert result["fill_rate"] == 0.8

        # raw_* / adjusted_* キーが存在する
        assert "raw_total_trades" in result
        assert "raw_return_pct" in result
        assert "raw_sharpe_ratio" in result
        assert "adjusted_total_trades" in result

        # 補正値が元の値 * fill_rate である
        if result["raw_return_pct"] is not None:
            assert result["adjusted_return_pct"] == pytest.approx(
                result["raw_return_pct"] * 0.8
            )

    def test_run_without_fill_rate(self, engine, prepared_data):
        """fill_rate=None（デフォルト） → raw_* キーが存在しない"""
        result = engine.run(prepared_data, RsiMaCrossoverBT)

        # fill_rate 未指定時は補正キーが存在しない
        assert "raw_total_trades" not in result
        assert "raw_return_pct" not in result
        assert "raw_sharpe_ratio" not in result
        assert "adjusted_total_trades" not in result
        assert "fill_rate" not in result


# ================================================================
# 18-19. M4: spread 自動適用テスト
# ================================================================


class TestRunAutoSpread:
    """BacktestEngine.run() の auto_spread オプションテスト"""

    def test_run_with_auto_spread(self, engine, prepared_data):
        """auto_spread=True + instrument指定 → spreadが自動計算される"""
        # spread=0.0 + auto_spread=True → 自動計算
        result_auto = engine.run(
            prepared_data, RsiMaCrossoverBT,
            instrument="USD_JPY", auto_spread=True,
        )

        # 手動でspreadを計算して実行した結果と比較
        price = float(prepared_data["Close"].iloc[-1])
        manual_spread = calculate_spread("USD_JPY", price)
        result_manual = engine.run(
            prepared_data, RsiMaCrossoverBT, spread=manual_spread,
        )

        # 同じ結果が得られるはず
        assert result_auto["total_trades"] == result_manual["total_trades"]
        if result_auto["return_pct"] is not None and result_manual["return_pct"] is not None:
            assert result_auto["return_pct"] == pytest.approx(
                result_manual["return_pct"], rel=1e-6
            )

    def test_run_auto_spread_manual_priority(self, engine, prepared_data):
        """auto_spread=True + spread手動指定 → 手動値が優先される"""
        manual_spread = 0.005  # 大きめのspreadを手動指定

        # auto_spread=True でも spread が手動指定されていれば手動値を使う
        result_manual = engine.run(
            prepared_data, RsiMaCrossoverBT,
            spread=manual_spread, instrument="USD_JPY", auto_spread=True,
        )

        # spread=0.005 を直接指定した場合と同じ結果になるはず
        result_direct = engine.run(
            prepared_data, RsiMaCrossoverBT, spread=manual_spread,
        )

        assert result_manual["total_trades"] == result_direct["total_trades"]
        if result_manual["return_pct"] is not None and result_direct["return_pct"] is not None:
            assert result_manual["return_pct"] == pytest.approx(
                result_direct["return_pct"], rel=1e-6
            )


# ================================================================
# 20-21. L1: n_windows 自動調整テスト
# ================================================================


class TestWalkForwardAutoAdjust:
    """BacktestEngine.run_walk_forward() の auto_adjust オプションテスト"""

    def test_walk_forward_auto_adjust(self, engine):
        """少ないデータで n_windows=5 → 自動調整で縮小される"""
        # MA_LONG_PERIOD=50 → min_segment=60
        # 200本 / (5+1) = 33 < 60 → 自動調整が発動
        # 200 // 60 - 1 = 2 に調整される
        small_data = _generate_prepared_data(n_bars=200, seed=99)

        result = engine.run_walk_forward(
            small_data, RsiMaCrossoverBT, n_windows=5, auto_adjust=True
        )

        # 自動調整により n_windows < 5 で実行される
        assert "windows" in result
        assert len(result["windows"]) < 5
        assert len(result["windows"]) > 0

        # 各ウィンドウの結果が正しい構造を持つ
        for w in result["windows"]:
            assert "in_sample" in w
            assert "out_of_sample" in w
            assert "wfe" in w

    def test_walk_forward_no_auto_adjust(self, engine):
        """auto_adjust=False → データ不足時に既存のBacktestError"""
        small_data = _generate_prepared_data(n_bars=200, seed=99)

        with pytest.raises(BacktestError, match="データ不足"):
            engine.run_walk_forward(
                small_data, RsiMaCrossoverBT,
                n_windows=5, auto_adjust=False,
            )
