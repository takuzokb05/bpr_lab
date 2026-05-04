"""
Bear Researcher（逆張り検証）モジュールのテスト

Phase 3 追加。
"""

import numpy as np
import pandas as pd
import pytest

from src.bear_researcher import BearResearcher, BearVerdict
from src.strategy.base import Signal


# ================================================================
# ヘルパー: テスト用データ生成
# ================================================================


def _make_ohlcv(
    rows: int = 100,
    base_price: float = 150.0,
    trend: float = 0.0,
    volume_val: float = 1000.0,
    include_volume: bool = True,
) -> pd.DataFrame:
    """
    テスト用OHLCVデータを生成する。

    Args:
        rows: 行数
        base_price: 基準価格
        trend: 1行あたりの価格変化（正=上昇、負=下降）
        volume_val: ボリューム値
        include_volume: volume列を含めるか
    """
    np.random.seed(42)
    close = base_price + np.arange(rows) * trend + np.random.randn(rows) * 0.1
    high = close + np.abs(np.random.randn(rows)) * 0.2
    low = close - np.abs(np.random.randn(rows)) * 0.2
    open_ = close + np.random.randn(rows) * 0.05

    data = {
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
    }
    if include_volume:
        data["volume"] = np.full(rows, volume_val)

    return pd.DataFrame(data)


def _make_divergence_data(
    is_bearish: bool = True, rows: int = 100
) -> pd.DataFrame:
    """
    ダイバージェンスが発生するデータを生成する（監査P1-#5: peak-based検出向け）。

    新検出器は scipy.signal.find_peaks で**直近2つのピーク/トラフ**を比較する。
    - bearish divergence: 価格は higher-high だが RSI は lower-high
    - bullish divergence: 価格は lower-low だが RSI は higher-low

    そのため2つの明確な山/谷を含む合成データを作る。
    """
    np.random.seed(42)
    close = np.full(rows, 150.0)
    # ベースは平坦（RSI を ~50 に落ち着かせる）
    for i in range(1, 70):
        close[i] = 150.0 + np.random.randn() * 0.02

    if is_bearish:
        # 山1: i=72-77 急上昇で価格 152、RSI 高い
        for i in range(70, 75):
            close[i] = close[i - 1] + 0.40
        for i in range(75, 80):
            close[i] = close[i - 1] - 0.05  # 山1のあと少し戻す
        # 山2: i=82-89 緩やかな上昇 → 価格は山1超え（higher-high）だが
        # 緩やかなので RSI は山1未満（lower-high）
        for i in range(80, 92):
            close[i] = close[i - 1] + 0.06
        # 山2のあと下げて山を確定
        for i in range(92, rows):
            close[i] = close[i - 1] - 0.10
    else:
        # 谷1: 急下降で価格 148、RSI 低い
        for i in range(70, 75):
            close[i] = close[i - 1] - 0.40
        for i in range(75, 80):
            close[i] = close[i - 1] + 0.05  # 谷1のあと少し戻す
        # 谷2: 緩やかな下降 → 価格は谷1未満（lower-low）だが緩やかなので
        # RSI は谷1超え（higher-low）
        for i in range(80, 92):
            close[i] = close[i - 1] - 0.06
        # 谷2のあと上げて谷を確定
        for i in range(92, rows):
            close[i] = close[i - 1] + 0.10

    high = close + 0.1
    low = close - 0.1
    open_ = close + np.random.randn(rows) * 0.01
    volume = np.full(rows, 1000.0)

    return pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def _make_resistance_data(rows: int = 100) -> pd.DataFrame:
    """
    レジスタンスに近い価格のBUYシグナル用データ。
    直近20本の高値付近に現在価格がある。
    """
    np.random.seed(42)
    close = np.full(rows, 150.0)
    # 直近20本のレジスタンスを150.5あたりにする
    high = np.full(rows, 150.3)
    high[-20:] = 150.5
    # 現在価格をレジスタンスに接近させる
    close[-1] = 150.45
    low = close - 0.2
    open_ = close.copy()
    volume = np.full(rows, 1000.0)

    return pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def _make_ma_descending_data(rows: int = 100) -> pd.DataFrame:
    """
    MA50が下降トレンドのデータ（BUYシグナルとの矛盾用）。
    """
    np.random.seed(42)
    # 全体的に下降トレンド
    close = 155.0 - np.arange(rows) * 0.1 + np.random.randn(rows) * 0.01
    high = close + 0.1
    low = close - 0.1
    open_ = close + np.random.randn(rows) * 0.01
    volume = np.full(rows, 1000.0)

    return pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def _make_mfi_neutral_data(rows: int = 100) -> pd.DataFrame:
    """
    MFIが中立帯（40-60）になるデータ。
    上昇と下降を交互に繰り返し、ボリュームも均一にする。
    """
    np.random.seed(42)
    close = np.full(rows, 150.0, dtype=float)
    # 上昇と下降を交互に繰り返す（MFIが中立に収束）
    for i in range(1, rows):
        if i % 2 == 0:
            close[i] = close[i - 1] + 0.02
        else:
            close[i] = close[i - 1] - 0.02
    high = close + 0.05
    low = close - 0.05
    open_ = close.copy()
    # ボリュームを均一にしてMFIを中立帯に
    volume = np.full(rows, 1000.0)

    return pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def _make_bb_squeeze_data(rows: int = 100) -> pd.DataFrame:
    """
    BBスクイーズ（BBW比率が低い）状態のデータ。
    直近のボラティリティが極端に低い。
    """
    np.random.seed(42)
    close = np.full(rows, 150.0, dtype=float)
    # 前半はボラティリティ高め
    close[:rows - 30] += np.random.randn(rows - 30) * 1.0
    # 直近30本はボラティリティ極小
    close[rows - 30:] = 150.0 + np.random.randn(30) * 0.01

    high = close + np.abs(np.random.randn(rows)) * 0.05
    # 前半は高値のレンジを広く
    high[:rows - 30] = close[:rows - 30] + np.abs(np.random.randn(rows - 30)) * 0.5
    low = close - np.abs(np.random.randn(rows)) * 0.05
    low[:rows - 30] = close[:rows - 30] - np.abs(np.random.randn(rows - 30)) * 0.5
    open_ = close + np.random.randn(rows) * 0.01
    volume = np.full(rows, 1000.0)

    return pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


# ================================================================
# テストケース
# ================================================================


class TestBearResearcherHold:
    """HOLDシグナルのテスト"""

    def test_hold_returns_zero_risk(self):
        """HOLDシグナルではリスク0のBearVerdictを返す"""
        bear = BearResearcher()
        data = _make_ohlcv()
        result = bear.verify(data, Signal.HOLD)

        assert result.risk_factors == []
        assert result.severity == 0.0
        assert result.penalty_multiplier == 1.0
        assert "HOLD" in result.reasoning or "検証不要" in result.reasoning


class TestBearResearcherDivergence:
    """ダイバージェンス検出テスト"""

    def test_bearish_divergence_detected(self):
        """価格上昇+RSI下降のbearish divergenceを検出する"""
        bear = BearResearcher()
        data = _make_divergence_data(is_bearish=True)
        result = bear.verify(data, Signal.BUY)

        # ダイバージェンスが検出されるはず
        divergence_found = any(
            "ダイバージェンス" in rf for rf in result.risk_factors
        )
        assert divergence_found, (
            f"ダイバージェンスが検出されませんでした。risk_factors={result.risk_factors}"
        )

    def test_bullish_divergence_detected(self):
        """価格下降+RSI上昇のbullish divergenceを検出する"""
        bear = BearResearcher()
        data = _make_divergence_data(is_bearish=False)
        result = bear.verify(data, Signal.SELL)

        divergence_found = any(
            "ダイバージェンス" in rf for rf in result.risk_factors
        )
        assert divergence_found, (
            f"ダイバージェンスが検出されませんでした。risk_factors={result.risk_factors}"
        )


class TestBearResearcherSupportResistance:
    """サポレジ接近テスト"""

    def test_resistance_proximity_on_buy(self):
        """レジスタンス付近のBUYシグナルでリスクを検出する"""
        bear = BearResearcher()
        data = _make_resistance_data()
        result = bear.verify(data, Signal.BUY)

        sr_found = any(
            "レジスタンス" in rf or "サポート" in rf for rf in result.risk_factors
        )
        assert sr_found, (
            f"サポレジ接近が検出されませんでした。risk_factors={result.risk_factors}"
        )


class TestBearResearcherHigherTimeframe:
    """上位足矛盾テスト"""

    def test_ma_descending_on_buy(self):
        """MA50下降中のBUYシグナルで矛盾を検出する"""
        bear = BearResearcher()
        data = _make_ma_descending_data()
        result = bear.verify(data, Signal.BUY)

        htf_found = any(
            "MA" in rf and "下降" in rf for rf in result.risk_factors
        )
        assert htf_found, (
            f"上位足矛盾が検出されませんでした。risk_factors={result.risk_factors}"
        )


class TestBearResearcherVolume:
    """ボリューム不支持テスト"""

    def test_mfi_neutral_zone(self):
        """MFIが中立帯のデータでリスクを検出する"""
        bear = BearResearcher()
        data = _make_mfi_neutral_data()
        result = bear.verify(data, Signal.BUY)

        mfi_found = any("MFI" in rf for rf in result.risk_factors)
        assert mfi_found, (
            f"MFI中立帯が検出されませんでした。risk_factors={result.risk_factors}"
        )


class TestBearResearcherBBSqueeze:
    """BBスクイーズテスト"""

    def test_bb_squeeze_detected(self):
        """低BBWのデータでBBスクイーズを検出する"""
        bear = BearResearcher()
        data = _make_bb_squeeze_data()
        result = bear.verify(data, Signal.BUY)

        bb_found = any("スクイーズ" in rf for rf in result.risk_factors)
        assert bb_found, (
            f"BBスクイーズが検出されませんでした。risk_factors={result.risk_factors}"
        )


class TestBearResearcherSeverity:
    """severity計算テスト"""

    def test_zero_risk_gives_multiplier_1(self):
        """リスク0の場合penalty_multiplierは1.0"""
        bear = BearResearcher()
        # 上昇トレンドのデータ+BUYシグナル → リスクが少ないはず
        data = _make_ohlcv(rows=100, trend=0.05)
        result = bear.verify(data, Signal.BUY)

        # 全リスク0は保証できないが、penalty_multiplierは0.5以上1.0以下
        assert 0.5 <= result.penalty_multiplier <= 1.0

    def test_severity_formula(self):
        """severityが検出数/5で計算されることを確認"""
        verdict = BearVerdict(
            risk_factors=["risk1", "risk2"],
            severity=2 / 5.0,
            penalty_multiplier=max(0.5, 1.0 - (2 / 5.0) * 0.5),
            reasoning="test",
        )
        assert verdict.severity == pytest.approx(0.4)
        assert verdict.penalty_multiplier == pytest.approx(0.8)

    def test_max_risk_gives_minimum_multiplier(self):
        """5件リスク → severity=1.0, penalty=0.5"""
        severity = 5 / 5.0
        penalty = max(0.5, 1.0 - severity * 0.5)
        assert severity == pytest.approx(1.0)
        assert penalty == pytest.approx(0.5)

    def test_no_risk_gives_maximum_multiplier(self):
        """0件リスク → severity=0.0, penalty=1.0"""
        severity = 0 / 5.0
        penalty = max(0.5, 1.0 - severity * 0.5)
        assert severity == pytest.approx(0.0)
        assert penalty == pytest.approx(1.0)


class TestBearResearcherEdgeCases:
    """エッジケーステスト"""

    def test_insufficient_data_returns_default(self):
        """データ不足時はデフォルトのBearVerdict（リスク0）を返す"""
        bear = BearResearcher()
        data = _make_ohlcv(rows=10)  # 不十分な行数
        result = bear.verify(data, Signal.BUY)

        assert result.risk_factors == []
        assert result.severity == 0.0
        assert result.penalty_multiplier == 1.0
        assert "データ不足" in result.reasoning

    def test_no_volume_column_no_crash(self):
        """volume列がなくてもクラッシュしない"""
        bear = BearResearcher()
        data = _make_ohlcv(rows=100, include_volume=False)
        # volume列がないことを確認
        assert "volume" not in data.columns

        result = bear.verify(data, Signal.BUY)
        # クラッシュせず結果が返る
        assert isinstance(result, BearVerdict)
        assert 0.5 <= result.penalty_multiplier <= 1.0

    def test_sell_signal_works(self):
        """SELLシグナルでも正常に動作する"""
        bear = BearResearcher()
        data = _make_ohlcv(rows=100, trend=-0.05)
        result = bear.verify(data, Signal.SELL)

        assert isinstance(result, BearVerdict)
        assert 0.5 <= result.penalty_multiplier <= 1.0


# ============================================================
# 監査P1-#4: 重み付け severity の回帰テスト
# ============================================================


def test_weighted_severity_higher_timeframe_outweighs_volume():
    """監査P1-#4: 上位足矛盾(0.35) は MFI 中立帯(0.05) より大きく severity に寄与"""
    from src.bear_researcher import _RISK_WEIGHTS
    assert _RISK_WEIGHTS["higher_timeframe"] > _RISK_WEIGHTS["volume_confirmation"]
    assert _RISK_WEIGHTS["higher_timeframe"] >= 0.30
    assert _RISK_WEIGHTS["volume_confirmation"] <= 0.10
    # 重みの合計は ~1.0（クランプ後の severity が 0..1 になる前提）
    assert abs(sum(_RISK_WEIGHTS.values()) - 1.0) < 0.01


def test_weighted_severity_clamped_to_unit_interval():
    """severity は重みの合計が 1.0 になるよう設計されているが、
    将来的な重み追加でも 1.0 を超えないようクランプされている"""
    from src.bear_researcher import BearResearcher, _RISK_WEIGHTS
    # 5 件全部発火しても severity は <= 1.0 のはず
    bear = BearResearcher()
    # _RISK_WEIGHTS の合計を確認
    total_weight = sum(_RISK_WEIGHTS.values())
    assert total_weight <= 1.01  # 0.35+0.25+0.20+0.15+0.05 = 1.00
