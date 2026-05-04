"""ConvictionScorer のテスト（監査P0-#1, P0-#2 回帰防止含む）"""
import numpy as np
import pandas as pd

from src.conviction_scorer import ConvictionScorer
from src.strategy.base import Signal


def _make_data(n: int = 200, base: float = 100.0, slope: float = 0.0) -> pd.DataFrame:
    """OHLCV合成データ。`slope` が線形トレンド成分（1バーあたりの上昇幅）"""
    np.random.seed(42)
    closes = base + np.arange(n) * slope + np.random.randn(n) * 0.05
    highs = closes + 0.1
    lows = closes - 0.1
    volumes = np.full(n, 1000.0)
    return pd.DataFrame({
        "open": closes, "high": highs, "low": lows, "close": closes, "volume": volumes,
    })


def test_score_rsi_buy_sell_asymmetric_audit_p0_1():
    """監査P0-#1: BUY と SELL で _score_rsi が異なる結果を返す"""
    scorer = ConvictionScorer()

    # BUY 戦略の発火直後想定: RSI=33（売られすぎ）
    indicators_oversold = {
        "current_rsi": 33.0, "current_adx": 25.0, "current_mfi": 35.0,
        "ma_long": pd.Series([100.0, 100.5]),
    }
    data = _make_data()

    result_buy = scorer.score(
        data=data, signal=Signal.BUY, regime=None, indicators=indicators_oversold,
    )
    result_sell = scorer.score(
        data=data, signal=Signal.SELL, regime=None, indicators=indicators_oversold,
    )

    # RSI=33 なら BUY は「売られすぎゾーン = 平均回帰候補」で 2点、
    # SELL は「売り下落しすぎ後 = 売りで稼ぐ余地少ない」で 0点になるべき
    assert result_buy.components["rsi"] > result_sell.components["rsi"], (
        f"RSI=33 で BUY rsi={result_buy.components['rsi']} <= "
        f"SELL rsi={result_sell.components['rsi']}: is_buy 分岐が機能していない"
    )


def test_score_rsi_buy_at_oversold_rewarded_audit_p0_1():
    """監査P0-#1: BUY で RSI 25-50 は最高得点"""
    scorer = ConvictionScorer()
    data = _make_data()
    for rsi_val in (28.0, 33.0, 45.0):
        result = scorer.score(
            data=data, signal=Signal.BUY, regime=None,
            indicators={
                "current_rsi": rsi_val, "current_adx": 25.0, "current_mfi": 30.0,
                "ma_long": pd.Series([100.0, 100.5]),
            },
        )
        assert result.components["rsi"] == 2, (
            f"BUY RSI={rsi_val} は売られすぎ〜中立で 2点期待、実際 {result.components['rsi']}"
        )


def test_score_rsi_sell_at_overbought_rewarded_audit_p0_1():
    """監査P0-#1: SELL で RSI 50-75 は最高得点"""
    scorer = ConvictionScorer()
    data = _make_data()
    for rsi_val in (55.0, 65.0, 72.0):
        result = scorer.score(
            data=data, signal=Signal.SELL, regime=None,
            indicators={
                "current_rsi": rsi_val, "current_adx": 25.0, "current_mfi": 70.0,
                "ma_long": pd.Series([100.5, 100.0]),
            },
        )
        assert result.components["rsi"] == 2, (
            f"SELL RSI={rsi_val} は中立〜買われすぎで 2点期待、実際 {result.components['rsi']}"
        )


def test_score_trend_relative_threshold_audit_p0_2():
    """監査P0-#2: 「横ばい」判定が価格スケールに対して相対的に動く

    旧 1e-8 では USDJPY=156 で実質「横ばい(=1)」が永遠に出ない。
    相対 1e-5 でなら、適切な小スロープで「横ばい」が返るはず。
    """
    scorer = ConvictionScorer()
    data = _make_data()

    # USDJPY 想定（base=156、slope は flat_threshold=156*1e-5=0.00156 未満）
    flat_ma = pd.Series([156.0, 156.0 + 1e-4])  # slope=0.0001 < 0.00156 → 横ばい
    result = scorer.score(
        data=data, signal=Signal.BUY, regime=None,
        indicators={
            "current_rsi": 33.0, "current_adx": 25.0, "current_mfi": 30.0,
            "ma_long": flat_ma,
        },
    )
    assert result.components["trend"] == 1, (
        f"slope=1e-4 / current=156 (相対 6.4e-7) は横ばい(=1)期待、実際 {result.components['trend']}"
    )


def test_score_trend_clear_uptrend_for_buy():
    """明確な上昇MAは BUY で 2点（横ばいでも逆行でもない）"""
    scorer = ConvictionScorer()
    data = _make_data()
    # 明確な上昇: slope=0.05 / current=156 (相対 3.2e-4) >> 1e-5 閾値
    rising_ma = pd.Series([155.95, 156.00])
    result = scorer.score(
        data=data, signal=Signal.BUY, regime=None,
        indicators={
            "current_rsi": 33.0, "current_adx": 25.0, "current_mfi": 30.0,
            "ma_long": rising_ma,
        },
    )
    assert result.components["trend"] == 2, (
        f"明確な上昇MAは BUY で 2点期待、実際 {result.components['trend']}"
    )
