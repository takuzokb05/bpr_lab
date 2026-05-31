"""SPEC v2 § 2-1 季節判定 — 確定版 (2026-05-10)

## 確定方針 (HYPOTHESES_2-1.md v1.1 / STEP_C_NEW_P0_VERIFIED_SUMMARY.md)

- **対象通貨**: GBP_JPY 単一 (EUR_USD は除外、USD_JPY は補助)
- **層構造**: 二層 (M15 主層 + H1 主層)、D1 削除
- **採用閾値** (GBP_JPY):
  - M15 主層: YZ_vol(window=14) > 30%ile (ローリング)
  - H1 主層: YZ_vol(window=20) > 0.00175 (絶対閾値)
  - M15 補完層: CHOP(length=14) <25 (オプショナル、効果サイズ弱)
- **評価指標**: Spearman ρ + block bootstrap CI を主、TR は補助 (検証時)

## 用途
- TradingLoop に組み込み、各バーで「volatile レジーム」判定
- volatile = 二層一致 (M15 と H1 両方が条件満たす)
- calm = 両方とも満たさない
- transitional = 片方のみ満たす

## 検証根拠
- 全検証は GBP_JPY H1 5y / M15 2y で実施 (`data/mt5_GBP_JPY_*.csv`)
- 詳細: `docs/vision/research/STEP_C_NEW_P0_VERIFIED_SUMMARY.md`
- 仮説台帳: `docs/vision/HYPOTHESES_2-1.md` v1.1

## 注意
- **本モジュールは PoC 段階**。本番投入前にペーパートレード最低 1-3 か月必須
- M15 percentile 30%ile はローリング窓 (デフォルト 5000 バー = 約 2.5 か月) で計算
- H1 絶対閾値 0.00175 は GBP_JPY 専用、他通貨では使用不可
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class SeasonRegime(Enum):
    """季節レジーム (二層一致判定)"""
    VOLATILE = "volatile"          # 二層一致 = 高ボラティリティ局面
    CALM = "calm"                  # 両層とも条件未達 = 静穏
    TRANSITIONAL = "transitional"  # 片層のみ条件成立 = 過渡期
    INSUFFICIENT_DATA = "insufficient_data"  # データ不足


@dataclass
class SeasonalJudgment:
    """季節判定の結果"""
    regime: SeasonRegime
    m15_yz_vol: Optional[float]       # M15 YZ_vol 当該値
    m15_threshold: Optional[float]    # M15 30%ile 閾値 (ローリング)
    m15_above: Optional[bool]         # M15 が閾値を超えるか
    h1_yz_vol: Optional[float]        # H1 YZ_vol 当該値
    h1_threshold: float               # H1 絶対閾値 (GBP_JPY=0.00175)
    h1_above: Optional[bool]          # H1 が閾値を超えるか
    chop_optional: Optional[float] = None        # M15 CHOP 当該値 (オプション)
    chop_below_25: Optional[bool] = None         # CHOP <25 補完判定 (オプション)


# ============================================================
# 設定 (確定値)
# ============================================================
GBP_JPY_CONFIG = {
    "pair": "GBP_JPY",
    "m15_yz_window": 14,
    "h1_yz_window": 20,
    "m15_threshold_pct": 30,        # 30%ile
    "m15_rolling_window_bars": 5000,  # 約 2.5 か月分の M15
    "h1_threshold_abs": 0.00175,
    "chop_length": 14,
    "chop_threshold": 25,
}


# ============================================================
# 指標計算
# ============================================================
def calc_yang_zhang(df: pd.DataFrame, window: int) -> pd.Series:
    """Yang-Zhang volatility 推定量

    df は OHLC を持つ DataFrame。window バーの rolling 計算。
    """
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    c_prev = c.shift(1)
    log_oc_prev = np.log(o / c_prev)
    log_co = np.log(c / o)
    log_ho = np.log(h / o)
    log_lo = np.log(l / o)
    rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
    sigma_rs = rs.rolling(window).mean()
    sigma_o = log_oc_prev.rolling(window).var()
    sigma_c = log_co.rolling(window).var()
    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    yz = sigma_o + k * sigma_c + (1 - k) * sigma_rs
    return np.sqrt(yz)


def calc_chop(df: pd.DataFrame, length: int) -> pd.Series:
    """Choppiness Index (length バーの rolling)"""
    import pandas_ta as ta
    return ta.chop(df["high"], df["low"], df["close"], length=length)


# ============================================================
# 判定ロジック
# ============================================================
class SeasonalDetector:
    """SPEC v2 § 2-1 季節判定 (GBP_JPY 単一通貨専用)

    使い方:
        detector = SeasonalDetector(pair="GBP_JPY")
        judgment = detector.judge(m15_df, h1_df)
        if judgment.regime == SeasonRegime.VOLATILE:
            # シグナル生成
            ...
    """

    def __init__(self, pair: str = "GBP_JPY", config: Optional[dict] = None):
        if pair != "GBP_JPY":
            raise ValueError(
                f"SPEC v2 § 2-1 確定値は GBP_JPY 単一通貨専用 (pair='{pair}' は未検証)。"
                f"EUR_USD は除外、USD_JPY は補助候補で別検証必要。"
            )
        self.pair = pair
        self.config = config or GBP_JPY_CONFIG

    def judge(self, m15_df: pd.DataFrame, h1_df: pd.DataFrame,
              use_chop_optional: bool = False) -> SeasonalJudgment:
        """季節レジームを判定する。

        Args:
            m15_df: M15 OHLC DataFrame (最低 m15_rolling_window_bars + m15_yz_window バー)
            h1_df: H1 OHLC DataFrame (最低 h1_yz_window バー)
            use_chop_optional: M15 CHOP <25 を補完判定として利用するか

        Returns:
            SeasonalJudgment
        """
        cfg = self.config
        m15_n_min = cfg["m15_rolling_window_bars"] + cfg["m15_yz_window"]
        h1_n_min = cfg["h1_yz_window"]

        if len(m15_df) < m15_n_min or len(h1_df) < h1_n_min:
            return SeasonalJudgment(
                regime=SeasonRegime.INSUFFICIENT_DATA,
                m15_yz_vol=None, m15_threshold=None, m15_above=None,
                h1_yz_vol=None, h1_threshold=cfg["h1_threshold_abs"], h1_above=None,
            )

        # M15 YZ_vol 計算
        m15_yz_series = calc_yang_zhang(m15_df, window=cfg["m15_yz_window"])
        m15_yz_now = float(m15_yz_series.iloc[-1])

        # M15 30%ile 閾値 (ローリング窓)
        rolling_window = cfg["m15_rolling_window_bars"]
        m15_yz_history = m15_yz_series.iloc[-rolling_window - 1:-1].dropna()
        if len(m15_yz_history) < rolling_window // 2:
            return SeasonalJudgment(
                regime=SeasonRegime.INSUFFICIENT_DATA,
                m15_yz_vol=m15_yz_now, m15_threshold=None, m15_above=None,
                h1_yz_vol=None, h1_threshold=cfg["h1_threshold_abs"], h1_above=None,
            )
        m15_threshold = float(np.percentile(m15_yz_history.values, cfg["m15_threshold_pct"]))
        m15_above = m15_yz_now > m15_threshold

        # H1 YZ_vol 計算 + 絶対閾値判定
        h1_yz_series = calc_yang_zhang(h1_df, window=cfg["h1_yz_window"])
        h1_yz_now = float(h1_yz_series.iloc[-1])
        if np.isnan(h1_yz_now):
            return SeasonalJudgment(
                regime=SeasonRegime.INSUFFICIENT_DATA,
                m15_yz_vol=m15_yz_now, m15_threshold=m15_threshold, m15_above=m15_above,
                h1_yz_vol=None, h1_threshold=cfg["h1_threshold_abs"], h1_above=None,
            )
        h1_above = h1_yz_now > cfg["h1_threshold_abs"]

        # CHOP 補完 (オプショナル)
        chop_now = None
        chop_below_25 = None
        if use_chop_optional and len(m15_df) >= cfg["chop_length"] + 1:
            chop_series = calc_chop(m15_df, length=cfg["chop_length"])
            chop_now = float(chop_series.iloc[-1]) if not pd.isna(chop_series.iloc[-1]) else None
            if chop_now is not None:
                chop_below_25 = chop_now < cfg["chop_threshold"]

        # 二層一致判定
        if m15_above and h1_above:
            regime = SeasonRegime.VOLATILE
        elif not m15_above and not h1_above:
            regime = SeasonRegime.CALM
        else:
            regime = SeasonRegime.TRANSITIONAL

        return SeasonalJudgment(
            regime=regime,
            m15_yz_vol=m15_yz_now,
            m15_threshold=m15_threshold,
            m15_above=m15_above,
            h1_yz_vol=h1_yz_now,
            h1_threshold=cfg["h1_threshold_abs"],
            h1_above=h1_above,
            chop_optional=chop_now,
            chop_below_25=chop_below_25,
        )


# ============================================================
# 簡易セルフテスト
# ============================================================
if __name__ == "__main__":
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[2]
    m15_csv = ROOT / "data" / "mt5_GBP_JPY_M15_2y.csv"
    h1_csv = ROOT / "data" / "mt5_GBP_JPY_H1_5y.csv"

    if not m15_csv.exists() or not h1_csv.exists():
        print(f"CSV not found: {m15_csv}, {h1_csv}")
        exit(1)

    m15_df = pd.read_csv(m15_csv, parse_dates=["datetime"]).set_index("datetime").sort_index()
    h1_df = pd.read_csv(h1_csv, parse_dates=["datetime"]).set_index("datetime").sort_index()

    detector = SeasonalDetector(pair="GBP_JPY")
    judgment = detector.judge(m15_df, h1_df, use_chop_optional=True)

    print(f"\nSPEC v2 § 2-1 季節判定 (GBP_JPY 単一通貨専用)")
    print(f"=" * 80)
    print(f"M15 YZ_vol now      : {judgment.m15_yz_vol:.5f}" if judgment.m15_yz_vol else "M15 YZ_vol      : N/A")
    print(f"M15 30%ile threshold: {judgment.m15_threshold:.5f}" if judgment.m15_threshold else "M15 threshold   : N/A")
    print(f"M15 above threshold : {judgment.m15_above}")
    print(f"H1  YZ_vol now      : {judgment.h1_yz_vol:.5f}" if judgment.h1_yz_vol else "H1 YZ_vol       : N/A")
    print(f"H1  abs threshold   : {judgment.h1_threshold:.5f}")
    print(f"H1  above threshold : {judgment.h1_above}")
    if judgment.chop_optional is not None:
        print(f"M15 CHOP            : {judgment.chop_optional:.2f} (補完: <25 なら True = {judgment.chop_below_25})")
    print(f"=" * 80)
    print(f"季節レジーム判定    : {judgment.regime.value}")
