"""コインテグレーション BT 用に必要な通貨ペアの D1 データを MT5 から取得して CSV 保存

候補ペア:
- EUR_USD, GBP_USD, AUD_USD, NZD_USD, USD_CHF, USD_CAD, USD_JPY
過去 5 年 D1 (約 1300 バー)
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5
import pandas as pd

OUT_DIR = ROOT / "data"
OUT_DIR.mkdir(exist_ok=True)

PAIRS = ["EUR_USD", "GBP_USD", "AUD_USD", "NZD_USD", "USD_CHF", "USD_CAD", "USD_JPY"]

# D1 5 年: 約 1300 バー、安全に 1500 取得
TF = mt5.TIMEFRAME_D1
COUNT = 1500


def to_mt5_symbol(instrument: str) -> str:
    return instrument.replace("_", "") + "-"


def fetch(instrument: str) -> pd.DataFrame:
    symbol = to_mt5_symbol(instrument)
    rates = mt5.copy_rates_from_pos(symbol, TF, 0, COUNT)
    if rates is None:
        raise RuntimeError(f"copy_rates failed for {symbol}: {mt5.last_error()}")
    df = pd.DataFrame(rates)
    df["datetime"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.set_index("datetime").sort_index()
    df = df.rename(columns={"tick_volume": "volume"})
    return df[["open", "high", "low", "close", "volume"]]


def main():
    ok = mt5.initialize()
    if not ok:
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        for pair in PAIRS:
            df = fetch(pair)
            out = OUT_DIR / f"mt5_{pair}_D1_5y.csv"
            df.to_csv(out)
            print(f"saved {out}  bars={len(df)}  range={df.index[0]} -> {df.index[-1]}")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
