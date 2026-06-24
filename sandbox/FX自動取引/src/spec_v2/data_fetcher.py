"""SPEC v2 PoC データ取得ヘルパー

mt5_client をラップして、SeasonalDetector が要求する 2 時間軸の DataFrame を一発取得する。

## 取得仕様
- M15: 5014 本 (= rolling 5000 + window 14)
- H1 : 200 本 (= window 20 + 余裕)

## 哲学的注釈
- mt5_client は I/O 層として PoC でそのまま流用 (PREMISE.md「コードベース骨格は継承」)
- ただし旧運用の symbol mapping や retry ロジックも継承するため、
  GBP_JPY 単独でも問題なく動作することを起動時に確認すること
"""
from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from src.mt5_client import Mt5Client

logger = logging.getLogger(__name__)


# SeasonalDetector が要求する最低本数
M15_REQUIRED_BARS = 5014  # rolling 5000 + window 14 + α
H1_REQUIRED_BARS = 200    # window 20 + α (実用上の余裕)


def fetch_m15_h1_for_seasonal(
    client: Mt5Client, pair: str = "GBP_JPY",
    m15_bars: int = M15_REQUIRED_BARS,
    h1_bars: int = H1_REQUIRED_BARS,
) -> dict:
    """SeasonalDetector に渡す M15 + H1 OHLC DataFrame を取得する。

    Args:
        client: 接続済み Mt5Client
        pair: 通貨ペア (デフォルト GBP_JPY)
        m15_bars: M15 取得本数 (最低 5014)
        h1_bars: H1 取得本数 (最低 35)

    Returns:
        {"m15": M15 DataFrame, "h1": H1 DataFrame, "fetched_at": ISO 文字列}

    Raises:
        ValueError: 取得本数が要件を満たさない場合
    """
    if pair != "GBP_JPY":
        raise ValueError(f"PoC では GBP_JPY 単独運用のみ対応 (pair='{pair}' は未検証)")

    logger.info(f"fetching M15={m15_bars} bars and H1={h1_bars} bars for {pair}")

    m15_df = client.get_prices(pair, count=m15_bars, granularity="M15")
    h1_df = client.get_prices(pair, count=h1_bars, granularity="H1")

    if len(m15_df) < M15_REQUIRED_BARS:
        raise ValueError(
            f"M15 データ不足: {len(m15_df)} 本 < 必要 {M15_REQUIRED_BARS} 本。"
            f"VPS 起動から十分な時間が経過していない可能性"
        )
    if len(h1_df) < 35:
        raise ValueError(f"H1 データ不足: {len(h1_df)} 本 < 必要 35 本")

    fetched_at = pd.Timestamp.utcnow().isoformat(timespec="seconds")
    logger.info(f"fetched: M15={len(m15_df)} bars, H1={len(h1_df)} bars at {fetched_at}")

    return {
        "m15": m15_df,
        "h1": h1_df,
        "fetched_at": fetched_at,
    }


def get_current_mid_price(client: Mt5Client, pair: str = "GBP_JPY") -> Optional[float]:
    """現在の bid/ask の中間値を取得 (仮想エントリー用)"""
    if pair != "GBP_JPY":
        raise ValueError(f"PoC では GBP_JPY 単独運用のみ対応")

    # 最新 1 本の close を mid 価格として代用 (PoC 仕様、bid/ask はデモ口座差小さい)
    df = client.get_prices(pair, count=1, granularity="M1")
    if len(df) == 0:
        return None
    return float(df["close"].iloc[-1])
