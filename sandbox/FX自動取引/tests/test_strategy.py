"""
戦略モジュールのテスト

F6: 戦略基底クラス (Signal, StrategyBase) のテスト
F7: RSIフィルター付きMAクロスオーバー戦略 (RsiMaCrossover) のテスト
"""

import numpy as np
import pandas as pd
import pytest

from src.strategy.base import Signal, StrategyBase
from src.strategy.ma_crossover import RsiMaCrossover


# ============================================================
# テスト用ヘルパー: 合成OHLCVデータ生成
# ============================================================


def _make_ohlcv(close_prices: np.ndarray, spread: float = 0.001) -> pd.DataFrame:
    """
    close価格系列からOHLCVのDataFrameを生成する。

    high = close + spread, low = close - spread, open = close（簡略化）
    volumeは一定値。ATR計算にはhigh/low/closeが必要。

    Args:
        close_prices: 終値の配列
        spread: high/lowのオフセット幅

    Returns:
        OHLCV形式のDataFrame
    """
    n = len(close_prices)
    return pd.DataFrame(
        {
            "open": close_prices,
            "high": close_prices + spread,
            "low": close_prices - spread,
            "close": close_prices,
            "volume": np.full(n, 1000.0),
        }
    )


def _make_golden_cross_data() -> pd.DataFrame:
    """
    MA(20)がMA(50)を上抜ける（ゴールデンクロス）データを生成する。

    下降トレンド → 横ばい → のこぎり波上昇という構成で、
    のこぎり波（2本上昇+1本下降）により RSI < 70 を維持しつつ
    ADX > 25 を確保してゴールデンクロスを発生させる。
    クロスオーバーが発生したバーでデータを切る。

    Returns:
        ゴールデンクロスが最終バーで発生するOHLCVデータ
        （RSI < 70, ADX > 25）
    """
    np.random.seed(42)
    n_bars = 160
    prices = np.empty(n_bars)

    # 0-69: 下降トレンド（MA20 < MA50を確立）
    for i in range(70):
        prices[i] = 100.0 - i * 0.08 + np.random.normal(0, 0.03)

    # 70-89: 底値圏で横ばい（ノイズ付き）
    for i in range(20):
        prices[70 + i] = prices[69] + np.random.normal(0, 0.04)

    # 90-159: のこぎり波上昇（2本上昇+1本下降でRSI抑制、ADX維持）
    base = prices[89]
    for i in range(70):
        cycle = i % 3
        if cycle < 2:
            base_offset = (i // 3) * 0.18 + cycle * 0.10
        else:
            base_offset = (i // 3) * 0.18 + 0.10 - 0.06
        prices[90 + i] = base + base_offset + np.random.normal(0, 0.03)

    # small spread → ADXが方向性を反映しやすい
    df_full = _make_ohlcv(prices, spread=0.06)
    import pandas_ta as ta

    ma_short = ta.sma(df_full["close"], length=20)
    ma_long = ta.sma(df_full["close"], length=50)

    crossover_bar = None
    for i in range(70, n_bars):
        if (
            pd.notna(ma_short.iloc[i])
            and pd.notna(ma_long.iloc[i])
            and pd.notna(ma_short.iloc[i - 1])
            and pd.notna(ma_long.iloc[i - 1])
            and ma_short.iloc[i - 1] <= ma_long.iloc[i - 1]
            and ma_short.iloc[i] > ma_long.iloc[i]
        ):
            crossover_bar = i
            break

    # クロスオーバーバーまでのデータを返す
    return df_full.iloc[: crossover_bar + 1].reset_index(drop=True)


def _make_dead_cross_data() -> pd.DataFrame:
    """
    MA(20)がMA(50)を下抜ける（デッドクロス）データを生成する。

    上昇トレンド → 天井圏横ばい → のこぎり波下降という構成で、
    のこぎり波（2本下降+1本上昇）により RSI > 30 を維持しつつ
    ADX > 25 を確保してデッドクロスを発生させる。
    クロスオーバーが発生したバーでデータを切る。

    Returns:
        デッドクロスが最終バーで発生するOHLCVデータ
        （RSI > 30, ADX > 25）
    """
    np.random.seed(42)
    n_bars = 160
    prices = np.empty(n_bars)

    # 0-69: 上昇トレンド（MA20 > MA50を確立）
    for i in range(70):
        prices[i] = 100.0 + i * 0.08 + np.random.normal(0, 0.03)

    # 70-89: 天井圏で横ばい（ノイズ付き）
    for i in range(20):
        prices[70 + i] = prices[69] + np.random.normal(0, 0.04)

    # 90-159: のこぎり波下降（2本下降+1本上昇でRSI抑制、ADX維持）
    base = prices[89]
    for i in range(70):
        cycle = i % 3
        if cycle < 2:
            base_offset = -(i // 3) * 0.18 - cycle * 0.10
        else:
            base_offset = -(i // 3) * 0.18 - 0.10 + 0.06
        prices[90 + i] = base + base_offset + np.random.normal(0, 0.03)

    # small spread → ADXが方向性を反映しやすい
    df_full = _make_ohlcv(prices, spread=0.06)
    import pandas_ta as ta

    ma_short = ta.sma(df_full["close"], length=20)
    ma_long = ta.sma(df_full["close"], length=50)

    crossover_bar = None
    for i in range(70, n_bars):
        if (
            pd.notna(ma_short.iloc[i])
            and pd.notna(ma_long.iloc[i])
            and pd.notna(ma_short.iloc[i - 1])
            and pd.notna(ma_long.iloc[i - 1])
            and ma_short.iloc[i - 1] >= ma_long.iloc[i - 1]
            and ma_short.iloc[i] < ma_long.iloc[i]
        ):
            crossover_bar = i
            break

    # デッドクロスバーまでのデータを返す
    return df_full.iloc[: crossover_bar + 1].reset_index(drop=True)


def _make_golden_cross_high_rsi_data() -> pd.DataFrame:
    """
    MA(20)がMA(50)を上抜けるが、RSIが70以上のデータを生成する。

    下降トレンド → 横ばい → 急上昇という構成で、
    急激な上昇によりRSIを70以上に押し上げつつゴールデンクロスを発生させる。
    RSIフィルターによりHOLDが返されることを検証する。

    Returns:
        ゴールデンクロスだがRSI >= 70 のOHLCVデータ
    """
    np.random.seed(123)
    n_bars = 120
    prices = np.empty(n_bars)

    # 0-59: 下降トレンド
    for i in range(60):
        prices[i] = 100.0 - i * 0.04 + np.random.normal(0, 0.03)

    # 60-89: 底値圏で横ばい
    for i in range(30):
        prices[60 + i] = prices[59] + np.random.normal(0, 0.05)

    # 90-119: 急上昇（RSIが70以上になるほど急激に）
    base = prices[89]
    for i in range(30):
        prices[90 + i] = base + i * 0.20 + np.random.normal(0, 0.03)

    # ゴールデンクロスが発生するバーを特定して、そこでデータを切る
    df_full = _make_ohlcv(prices)
    import pandas_ta as ta

    ma_short = ta.sma(df_full["close"], length=20)
    ma_long = ta.sma(df_full["close"], length=50)

    crossover_bar = None
    for i in range(60, n_bars):
        if (
            pd.notna(ma_short.iloc[i])
            and pd.notna(ma_long.iloc[i])
            and pd.notna(ma_short.iloc[i - 1])
            and pd.notna(ma_long.iloc[i - 1])
            and ma_short.iloc[i - 1] <= ma_long.iloc[i - 1]
            and ma_short.iloc[i] > ma_long.iloc[i]
        ):
            crossover_bar = i
            break

    # クロスオーバーバーまでのデータを返す
    return df_full.iloc[: crossover_bar + 1].reset_index(drop=True)


# ============================================================
# F6 テスト: 戦略基底クラス
# ============================================================


class TestSignalEnum:
    """Signal列挙型のテスト"""

    def test_signal_has_buy(self) -> None:
        """Signal EnumにBUYが存在すること"""
        assert hasattr(Signal, "BUY")
        assert Signal.BUY.value == "BUY"

    def test_signal_has_sell(self) -> None:
        """Signal EnumにSELLが存在すること"""
        assert hasattr(Signal, "SELL")
        assert Signal.SELL.value == "SELL"

    def test_signal_has_hold(self) -> None:
        """Signal EnumにHOLDが存在すること"""
        assert hasattr(Signal, "HOLD")
        assert Signal.HOLD.value == "HOLD"


class TestStrategyBase:
    """StrategyBase ABCクラスのテスト"""

    def test_cannot_instantiate_abc(self) -> None:
        """StrategyBaseは抽象クラスのため直接インスタンス化できないこと"""
        with pytest.raises(TypeError):
            StrategyBase()  # type: ignore[abstract]

    def test_subclass_must_implement_all_methods(self) -> None:
        """抽象メソッドを全て実装しないサブクラスもインスタンス化できないこと"""

        class IncompleteStrategy(StrategyBase):
            """generate_signalのみ実装（不完全）"""

            def generate_signal(self, data: pd.DataFrame) -> Signal:
                return Signal.HOLD

        with pytest.raises(TypeError):
            IncompleteStrategy()  # type: ignore[abstract]


# ============================================================
# F7 テスト: RsiMaCrossover
# ============================================================


class TestRsiMaCrossoverSignal:
    """RsiMaCrossover.generate_signal() のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前にストラテジーインスタンスを生成"""
        self.strategy = RsiMaCrossover()

    def test_buy_signal_on_golden_cross(self) -> None:
        """買いシグナル: MA短期がMA長期を上抜け + RSI < 70 のとき BUY"""
        data = _make_golden_cross_data()
        signal = self.strategy.generate_signal(data)
        assert signal == Signal.BUY, (
            f"ゴールデンクロスで BUY が返されるべきだが {signal} が返された"
        )

    def test_sell_signal_on_dead_cross(self) -> None:
        """売りシグナル: MA短期がMA長期を下抜け + RSI > 30 のとき SELL"""
        data = _make_dead_cross_data()
        signal = self.strategy.generate_signal(data)
        assert signal == Signal.SELL, (
            f"デッドクロスで SELL が返されるべきだが {signal} が返された"
        )

    def test_hold_when_rsi_overbought(self) -> None:
        """RSIフィルター: MA上抜けだがRSI >= 70 のとき HOLD（買われすぎ排除）"""
        data = _make_golden_cross_high_rsi_data()
        signal = self.strategy.generate_signal(data)
        assert signal == Signal.HOLD, (
            f"RSI >= 70 で HOLD が返されるべきだが {signal} が返された"
        )

    def test_hold_on_insufficient_data(self) -> None:
        """データ不足: 50行未満のDataFrameで HOLD"""
        # MA_LONG_PERIOD = 50 なので49行のデータを生成
        short_data = _make_ohlcv(np.linspace(100, 105, 49))
        signal = self.strategy.generate_signal(short_data)
        assert signal == Signal.HOLD, (
            f"データ不足で HOLD が返されるべきだが {signal} が返された"
        )


class TestRsiMaCrossoverStopLoss:
    """RsiMaCrossover.calculate_stop_loss() のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前にストラテジーインスタンスを生成"""
        self.strategy = RsiMaCrossover()

    def _make_atr_data(self, n_bars: int = 30) -> pd.DataFrame:
        """
        ATR計算用データを生成する。

        一定スプレッドのOHLCVデータを作成し、ATR値が安定するようにする。
        spread=0.5 → 各バーの真のレンジ ≈ 1.0
        ATR(14) ≈ 1.0 程度になることを期待。
        """
        close_prices = np.full(n_bars, 150.0)
        return _make_ohlcv(close_prices, spread=0.5)

    def test_stop_loss_buy_direction(self) -> None:
        """BUY方向の損切り: entry_price - ATR * 2.0"""
        data = self._make_atr_data()
        entry_price = 150.0
        sl = self.strategy.calculate_stop_loss(entry_price, "BUY", data)

        # BUYの損切りはエントリー価格より低くなるべき
        assert sl < entry_price, (
            f"BUY方向のSLはentry_price({entry_price})より小さいべきだが {sl}"
        )

    def test_stop_loss_sell_direction(self) -> None:
        """SELL方向の損切り: entry_price + ATR * 2.0"""
        data = self._make_atr_data()
        entry_price = 150.0
        sl = self.strategy.calculate_stop_loss(entry_price, "SELL", data)

        # SELLの損切りはエントリー価格より高くなるべき
        assert sl > entry_price, (
            f"SELL方向のSLはentry_price({entry_price})より大きいべきだが {sl}"
        )

    def test_stop_loss_atr_calculation(self) -> None:
        """ATRベースの損切り価格が数値的に正しいこと"""
        data = self._make_atr_data()
        entry_price = 150.0

        sl_buy = self.strategy.calculate_stop_loss(entry_price, "BUY", data)
        sl_sell = self.strategy.calculate_stop_loss(entry_price, "SELL", data)

        # BUYとSELLのSLはエントリー価格から等距離（ATR*2.0）
        distance_buy = entry_price - sl_buy
        distance_sell = sl_sell - entry_price
        assert distance_buy == pytest.approx(distance_sell, rel=1e-6), (
            f"BUYとSELLのSL距離が等しくないべき: BUY={distance_buy}, SELL={distance_sell}"
        )

    def test_stop_loss_insufficient_data_raises(self) -> None:
        """ATR計算不能時: ValueErrorが送出される"""
        # ATR_PERIOD=14 に対してデータが少なすぎる
        short_data = _make_ohlcv(np.array([150.0, 151.0, 149.0]), spread=0.5)
        entry_price = 150.0
        with pytest.raises(ValueError, match="ATR計算不能"):
            self.strategy.calculate_stop_loss(entry_price, "BUY", short_data)

    def test_stop_loss_invalid_direction_raises(self) -> None:
        """不正なdirectionでValueErrorが送出される"""
        data = self._make_atr_data()
        with pytest.raises(ValueError, match="direction"):
            self.strategy.calculate_stop_loss(150.0, "INVALID", data)


class TestRsiMaCrossoverTakeProfit:
    """RsiMaCrossover.calculate_take_profit() のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前にストラテジーインスタンスを生成"""
        self.strategy = RsiMaCrossover()

    def test_take_profit_buy(self) -> None:
        """BUY方向の利確: entry_price + risk * MIN_RISK_REWARD"""
        entry_price = 150.0
        stop_loss = 148.0  # risk = 2.0
        tp = self.strategy.calculate_take_profit(entry_price, "BUY", stop_loss)

        # MIN_RISK_REWARD = 2.0 → tp = 150.0 + 2.0 * 2.0 = 154.0
        expected_tp = 154.0
        assert tp == pytest.approx(expected_tp), (
            f"BUY TPは{expected_tp}であるべきだが {tp}"
        )

    def test_take_profit_sell(self) -> None:
        """SELL方向の利確: entry_price - risk * MIN_RISK_REWARD"""
        entry_price = 150.0
        stop_loss = 152.0  # risk = 2.0
        tp = self.strategy.calculate_take_profit(entry_price, "SELL", stop_loss)

        # MIN_RISK_REWARD = 2.0 → tp = 150.0 - 2.0 * 2.0 = 146.0
        expected_tp = 146.0
        assert tp == pytest.approx(expected_tp), (
            f"SELL TPは{expected_tp}であるべきだが {tp}"
        )

    def test_risk_reward_ratio(self) -> None:
        """利確と損切りのリスクリワード比がMIN_RISK_REWARD以上であること"""
        entry_price = 150.0
        stop_loss = 148.5  # risk = 1.5
        tp = self.strategy.calculate_take_profit(entry_price, "BUY", stop_loss)

        risk = abs(entry_price - stop_loss)
        reward = abs(tp - entry_price)
        actual_rr = reward / risk

        assert actual_rr >= 2.0, (
            f"リスクリワード比は2.0以上であるべきだが {actual_rr:.2f}"
        )

    def test_take_profit_zero_risk_raises(self) -> None:
        """損切り幅ゼロ（SL=entry_price）でValueErrorが送出される"""
        with pytest.raises(ValueError, match="損切り幅がゼロ"):
            self.strategy.calculate_take_profit(150.0, "BUY", 150.0)

    def test_take_profit_invalid_direction_raises(self) -> None:
        """不正なdirectionでValueErrorが送出される"""
        with pytest.raises(ValueError, match="direction"):
            self.strategy.calculate_take_profit(150.0, "INVALID", 148.0)


# ============================================================
# F15 テスト: ADXフィルター
# ============================================================


def _make_range_bound_golden_cross_data() -> pd.DataFrame:
    """
    ゴールデンクロスは発生するが、ADX < 25（レンジ相場）のデータを生成する。

    小さなspreadと穏やかな値動きにより、ADXが低くなる。
    既存の旧データ生成ロジックを使用（ADX ≈ 19、閾値25未満）。

    Returns:
        ゴールデンクロスが最終バーで発生するがADX < 25のOHLCVデータ
    """
    np.random.seed(42)
    n_bars = 120
    prices = np.empty(n_bars)

    # 0-59: 緩やかな下降トレンド
    for i in range(60):
        prices[i] = 100.0 - i * 0.04 + np.random.normal(0, 0.05)

    # 60-89: 底値圏で横ばい
    for i in range(30):
        prices[60 + i] = prices[59] + np.random.normal(0, 0.08)

    # 90-119: 緩やかな上昇
    base = prices[89]
    for i in range(30):
        prices[90 + i] = base + i * 0.08 + np.random.normal(0, 0.05)

    # 小さいspread → ADXが低くなる
    df_full = _make_ohlcv(prices, spread=0.001)
    import pandas_ta as ta

    ma_short = ta.sma(df_full["close"], length=20)
    ma_long = ta.sma(df_full["close"], length=50)

    crossover_bar = None
    for i in range(60, n_bars):
        if (
            pd.notna(ma_short.iloc[i])
            and pd.notna(ma_long.iloc[i])
            and pd.notna(ma_short.iloc[i - 1])
            and pd.notna(ma_long.iloc[i - 1])
            and ma_short.iloc[i - 1] <= ma_long.iloc[i - 1]
            and ma_short.iloc[i] > ma_long.iloc[i]
        ):
            crossover_bar = i
            break

    return df_full.iloc[: crossover_bar + 1].reset_index(drop=True)


class TestAdxFilter:
    """ADXフィルター（F15）のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前にストラテジーインスタンスを生成"""
        self.strategy = RsiMaCrossover()

    def test_hold_when_adx_below_threshold(self) -> None:
        """ADXフィルター: ADX < 25 のレンジ相場ではゴールデンクロスでもHOLD"""
        data = _make_range_bound_golden_cross_data()
        signal = self.strategy.generate_signal(data)
        assert signal == Signal.HOLD, (
            f"ADX < 25 で HOLD が返されるべきだが {signal} が返された"
        )

    def test_buy_signal_with_adx_filter(self) -> None:
        """ADXフィルター通過: ADX > 25 + ゴールデンクロス + RSI < 70 で BUY"""
        data = _make_golden_cross_data()

        # データが条件を満たしていることを事前検証
        import pandas_ta as ta

        adx_df = ta.adx(data["high"], data["low"], data["close"], length=14)
        adx_val = adx_df["ADX_14"].iloc[-1]
        assert adx_val > 25.0, (
            f"テストデータのADXが25を超えるべきだが {adx_val:.2f}"
        )

        signal = self.strategy.generate_signal(data)
        assert signal == Signal.BUY, (
            f"ADX > 25 + ゴールデンクロス + RSI < 70 で BUY が返されるべきだが"
            f" {signal} が返された"
        )

    def test_sell_signal_with_adx_filter(self) -> None:
        """ADXフィルター通過: ADX > 25 + デッドクロス + RSI > 30 で SELL"""
        data = _make_dead_cross_data()

        # データが条件を満たしていることを事前検証
        import pandas_ta as ta

        adx_df = ta.adx(data["high"], data["low"], data["close"], length=14)
        adx_val = adx_df["ADX_14"].iloc[-1]
        assert adx_val > 25.0, (
            f"テストデータのADXが25を超えるべきだが {adx_val:.2f}"
        )

        signal = self.strategy.generate_signal(data)
        assert signal == Signal.SELL, (
            f"ADX > 25 + デッドクロス + RSI > 30 で SELL が返されるべきだが"
            f" {signal} が返された"
        )

    def test_adx_nan_returns_hold(self) -> None:
        """ADXがNaNの場合（データ不足）はHOLDを返す"""
        # MA_LONG_PERIOD(50)以上だがADX計算には不十分になるよう
        # 全て同じ値のデータを使用（ADXがNaNになる）
        flat_prices = np.full(55, 100.0)
        data = _make_ohlcv(flat_prices, spread=0.0)
        signal = self.strategy.generate_signal(data)
        assert signal == Signal.HOLD, (
            f"ADXがNaNの場合 HOLD が返されるべきだが {signal} が返された"
        )
