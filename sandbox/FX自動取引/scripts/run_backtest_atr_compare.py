"""T3: ATR連動SL/TP + 段階的部分利確 vs 旧来固定R:R 比較バックテスト

USD_JPY / EUR_USD / GBP_JPY の M15 60日データで、
旧来 (RsiMaCrossoverBT) と新方式 (RsiMaCrossoverAtrBT) を並行実行し、
主要メトリクスを比較表示する。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import yfinance as yf

from src.backtester import (
    BacktestEngine,
    RsiMaCrossoverAtrBT,
    RsiMaCrossoverBT,
)


PAIRS = [
    ("USD_JPY", "USDJPY=X"),
    ("EUR_USD", "EURUSD=X"),
    ("GBP_JPY", "GBPJPY=X"),
]

METRICS = [
    ("total_trades", "Trades", "{:>6}"),
    ("win_rate", "Win%", "{:>6.1f}"),
    ("profit_factor", "PF", "{:>6.2f}"),
    ("max_drawdown", "DD%", "{:>7.2f}"),
    ("sharpe_ratio", "SR", "{:>6.2f}"),
    ("return_pct", "Ret%", "{:>7.2f}"),
]


def fetch_m15(ticker: str, period: str = "60d") -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval="15m",
                     auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError(f"no data for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df.columns = [c.lower() for c in df.columns]
    df["volume"] = df["volume"].replace(0, 1)
    return df[["open", "high", "low", "close", "volume"]]


def fmt(value, fmt_str: str) -> str:
    if value is None:
        return "{:>6}".format("N/A")
    try:
        return fmt_str.format(value)
    except (TypeError, ValueError):
        return "{:>6}".format(str(value))


def run_one(pair_name: str, ticker: str) -> dict:
    print(f"\n=== {pair_name} ({ticker}) M15 60日 ===")
    df = fetch_m15(ticker)
    print(f"data: {len(df)}本 ({df.index[0]} 〜 {df.index[-1]})")

    bt_data = BacktestEngine.prepare_data(df)
    results = {}
    for label, strat_cls in (
        ("legacy", RsiMaCrossoverBT),
        ("atr_partial", RsiMaCrossoverAtrBT),
    ):
        try:
            with BacktestEngine() as engine:
                r = engine.run(
                    bt_data, strat_cls,
                    cash=1_000_000, commission=0.00002, margin=1/25,
                    instrument=pair_name, auto_spread=True,
                )
            results[label] = r
        except Exception as e:
            print(f"  {label} FAILED: {e}")
            results[label] = None
    return results


def print_table(all_results: dict[str, dict]):
    """ペア × {legacy, atr_partial} の比較表を出力。"""
    header = ["Pair", "Mode"] + [m[1] for m in METRICS]
    fmt_header = "{:<10} {:<12}" + " " * 2 + " ".join("{:>7}" for _ in METRICS)
    print("\n" + "=" * 70)
    print("BACKTEST COMPARISON: legacy (固定R:R) vs atr_partial (T3)")
    print("=" * 70)
    print(fmt_header.format(*header))
    print("-" * 70)
    for pair, modes in all_results.items():
        for mode_label in ("legacy", "atr_partial"):
            r = modes.get(mode_label)
            if r is None:
                row = [pair, mode_label] + ["N/A"] * len(METRICS)
                print(fmt_header.format(*row))
                continue
            row = [pair, mode_label]
            for key, _, f in METRICS:
                row.append(fmt(r.get(key), f))
            print(("{:<10} {:<12}  " + " ".join(["{:>7}"] * len(METRICS))).format(*row))
        print()


if __name__ == "__main__":
    all_results = {}
    for pair_name, ticker in PAIRS:
        try:
            all_results[pair_name] = run_one(pair_name, ticker)
        except Exception as e:
            print(f"  {pair_name} FAILED: {e}")
            all_results[pair_name] = {}
    print_table(all_results)
