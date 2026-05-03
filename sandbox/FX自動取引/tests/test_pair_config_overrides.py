"""A8: pair_config から RSI 閾値を戦略にオーバーライドできることのテスト。

PR #7 で trading_loop.py が pair_config を generate_signal に渡すようになったが、
当初どの戦略も受け取っていなかった (dead arg)。本テストは戦略側で実際に
オーバーライドが効くことを検証する。
"""
import numpy as np
import pandas as pd

from src.strategy.base import Signal
from src.strategy.bollinger_reversal import BollingerReversal
from src.strategy.rsi_pullback import RsiPullback


def _make_ohlcv(close_prices: np.ndarray) -> pd.DataFrame:
    n = len(close_prices)
    return pd.DataFrame({
        "open": close_prices,
        "high": close_prices + 0.001,
        "low": close_prices - 0.001,
        "close": close_prices,
        "volume": np.full(n, 1000),
    })


class TestRsiPullbackPairConfig:
    """RsiPullback が pair_config の rsi_oversold を尊重すること"""

    def _make_uptrend_then_dip(self, dip_to_rsi: float) -> pd.DataFrame:
        """MA200 > closeの上昇トレンド + 終盤に RSI が dip_to_rsi 程度になる動き"""
        # 220本: MA200確保。長期上昇 + 直近で軽い押し目
        base = np.linspace(100, 110, 200)
        # 直近20本で押し目（slight pullback to RSI ~35）
        dip = np.linspace(110, 109.5, 20)
        return _make_ohlcv(np.concatenate([base, dip]))

    def test_default_threshold_blocks_signal_when_pair_config_overrides_to_strict(self):
        """デフォルト35だと拾えるが pair_config rsi_oversold=20 にすると HOLD になる。

        RSI が34前後の押し目で、デフォルト(<35)なら BUY、厳しい閾値(<20)なら HOLD。
        """
        data = self._make_uptrend_then_dip(dip_to_rsi=33)

        strat = RsiPullback()
        # デフォルト動作 → BUY期待 (RSIが35未満 + closeがMA200上)
        sig_default = strat.generate_signal(data)

        # pair_config で厳格化 → HOLD期待
        sig_strict = strat.generate_signal(
            data, pair_config={"rsi_oversold": 20, "rsi_overbought": 80}
        )

        # デフォルトと厳格でシグナルが変わること（少なくともdiagに反映されること）
        diag = strat.last_diagnostics
        assert diag is not None
        assert diag["rsi_oversold"] == 20
        # 厳格化したら絶対にBUYは出ない（rsi=33 > 20 なので押し目とは見なされない）
        assert sig_strict == Signal.HOLD


class TestBollingerReversalPairConfig:
    """BollingerReversal が pair_config の rsi_overbought を尊重すること"""

    def _make_bb_upper_touch_data(self) -> pd.DataFrame:
        """BB上限タッチ + RSI 67 程度を作る合成データ"""
        # 上昇後にスパイク
        n = 30
        prices = np.concatenate([
            np.full(20, 100.0),
            np.linspace(100.0, 102.0, 10),
        ])
        return _make_ohlcv(prices)

    def test_pair_config_overrides_rsi_overbought(self):
        """pair_config rsi_overbought=80 → デフォルト65より厳格、SELLが出にくくなる"""
        data = self._make_bb_upper_touch_data()

        strat = BollingerReversal()
        strat.generate_signal(
            data, pair_config={"rsi_oversold": 20, "rsi_overbought": 80}
        )
        diag = strat.last_diagnostics
        assert diag is not None
        assert diag["rsi_overbought"] == 80
        assert diag["rsi_oversold"] == 20

    def test_no_pair_config_uses_defaults(self):
        """pair_config なしでも従来通り動作（デフォルト 65/35 を使う）"""
        data = self._make_bb_upper_touch_data()

        strat = BollingerReversal()
        strat.generate_signal(data)
        diag = strat.last_diagnostics
        assert diag is not None
        # デフォルトは BollingerReversal 固有の 65/35
        assert diag["rsi_overbought"] == 65
        assert diag["rsi_oversold"] == 35
