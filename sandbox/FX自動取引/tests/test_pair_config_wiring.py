"""監査 C4 配線漏れの回帰防止テスト。

PR #11 (pair_config 全ペア 35/65) と PR #13 (EUR/USD 30/70) は
本番投入されたが、戦略コード (mtf_pullback.py / bollinger_reversal.py) が
pair_config を読まずクラス定数を使い続けていたため**実取引に効いていなかった**。

このテストは「pair_config の値が strategy.generate_signal に届いて
オーバーライドされる」ことを保証する。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.strategy.base import Signal
from src.strategy.bollinger_reversal import BollingerReversal
from src.strategy.mtf_pullback import MTFPullback


def _ohlcv_uptrend(n: int = 220, dip_to_close: float = 109.5) -> pd.DataFrame:
    """MA200 < close（上昇トレンド）+ 直近で軽い押し目を作る。"""
    base = np.linspace(100, 110, 200)
    dip = np.linspace(110, dip_to_close, 20)
    close = np.concatenate([base, dip])
    return pd.DataFrame({
        "open": close,
        "high": close + 0.05,
        "low": close - 0.05,
        "close": close,
        "volume": np.full(n, 1000),
    })


def _ohlcv_bb_squeeze(n: int = 30) -> pd.DataFrame:
    """BB 上限付近 + RSI 高めを作る合成データ。"""
    prices = np.concatenate([
        np.full(20, 100.0),
        np.linspace(100.0, 102.0, 10),
    ])
    return pd.DataFrame({
        "open": prices,
        "high": prices + 0.001,
        "low": prices - 0.001,
        "close": prices,
        "volume": np.full(n, 1000),
    })


class TestMTFPullbackPairConfigWiring:
    """MTFPullback の pair_config kwargs オーバーライドが効くこと。"""

    def test_pair_config_threshold_changes_diagnostics(self):
        """pair_config の rsi_oversold/overbought が diag に反映される"""
        strat = MTFPullback()
        data = _ohlcv_uptrend(dip_to_close=109.5)

        # デフォルト (35/65)
        strat.generate_signal(data)
        diag_default = strat.last_diagnostics
        assert diag_default["rsi_oversold"] == 35
        assert diag_default["rsi_overbought"] == 65

        # pair_config で 30/70 に上書き
        strat.generate_signal(
            data, pair_config={"rsi_oversold": 30, "rsi_overbought": 70},
        )
        diag_strict = strat.last_diagnostics
        assert diag_strict["rsi_oversold"] == 30
        assert diag_strict["rsi_overbought"] == 70

    def test_pair_config_strict_blocks_buy_signal(self):
        """rsi_oversold を厳しく (30) すると BUY シグナルが消える。

        合成データで RSI が 32 程度になる押し目を用意。
        - デフォルト 35: BUY (RSI 32 < 35)
        - 厳格 30:     HOLD (RSI 32 > 30)
        """
        # RSI が 30〜35 の範囲に入るようなデータ
        data = _ohlcv_uptrend(dip_to_close=109.7)

        strat = MTFPullback()
        sig_default = strat.generate_signal(data)
        rsi_observed = strat.last_diagnostics["rsi"]

        strat2 = MTFPullback()
        sig_strict = strat2.generate_signal(
            data, pair_config={"rsi_oversold": 30, "rsi_overbought": 70},
        )

        # デフォルト 35 で RSI < 35 なら BUY、厳格 30 で RSI > 30 なら HOLD
        if 30 < rsi_observed < 35:
            assert sig_default == Signal.BUY
            assert sig_strict == Signal.HOLD


class TestBollingerReversalPairConfigWiring:
    """BollingerReversal の pair_config kwargs オーバーライドが効くこと。"""

    def test_pair_config_threshold_changes_diagnostics(self):
        """pair_config の rsi_oversold/overbought が diag に反映される"""
        data = _ohlcv_bb_squeeze()

        strat = BollingerReversal()
        strat.generate_signal(data)
        diag_default = strat.last_diagnostics
        # BollingerReversal クラスデフォルトは 65/35
        assert diag_default["rsi_oversold"] == 35
        assert diag_default["rsi_overbought"] == 65

        strat.generate_signal(
            data, pair_config={"rsi_oversold": 25, "rsi_overbought": 75},
        )
        diag_override = strat.last_diagnostics
        assert diag_override["rsi_oversold"] == 25
        assert diag_override["rsi_overbought"] == 75

    def test_no_pair_config_uses_class_defaults(self):
        """pair_config なし or 空 dict ならクラスデフォルト (35/65) を使う"""
        data = _ohlcv_bb_squeeze()

        strat = BollingerReversal()
        strat.generate_signal(data, pair_config=None)
        assert strat.last_diagnostics["rsi_oversold"] == 35
        assert strat.last_diagnostics["rsi_overbought"] == 65

        strat.generate_signal(data, pair_config={})
        assert strat.last_diagnostics["rsi_oversold"] == 35
        assert strat.last_diagnostics["rsi_overbought"] == 65
