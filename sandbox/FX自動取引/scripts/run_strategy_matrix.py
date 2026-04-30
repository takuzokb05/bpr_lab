"""戦略×ペア×タイムフレーム 並列バックテスト

5戦略 × 3ペア × 3TF = 45組合せで実行し、PF/勝率/DDを表形式で出力する。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import yfinance as yf

from src.backtester import BacktestEngine, RsiMaCrossoverBT
from src.strategy.variants_bt import STRATEGIES


ALL_STRATEGIES = {"MAcrossover": RsiMaCrossoverBT, **STRATEGIES}

TIMEFRAMES = [
    ("15m", "60d"),
    ("1h",  "720d"),
    ("4h",  "720d"),
]
TICKERS = ["USDJPY=X", "EURUSD=X", "GBPJPY=X"]


def fetch_ohlcv(ticker: str, interval: str, period: str) -> pd.DataFrame:
    if interval == "4h":
        base = yf.download(ticker, period=period, interval="1h",
                           auto_adjust=False, progress=False)
        if base.empty:
            raise ValueError("no data")
        if isinstance(base.columns, pd.MultiIndex):
            base.columns = [c[0] for c in base.columns]
        base.columns = [c.lower() for c in base.columns]
        df = base.resample("4h").agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum",
        }).dropna()
    else:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=False, progress=False)
        if df.empty:
            raise ValueError("no data")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df.columns = [c.lower() for c in df.columns]
    df["volume"] = df["volume"].replace(0, 1)
    return df[["open", "high", "low", "close", "volume"]]


def run_one(ticker, interval, period, strategy_name, strategy_cls):
    df = fetch_ohlcv(ticker, interval, period)
    bt_data = BacktestEngine.prepare_data(df)
    with BacktestEngine() as engine:
        result = engine.run(
            bt_data, strategy_cls,
            cash=1_000_000, commission=0.00002, margin=1/25,
        )
    return {
        "strategy": strategy_name,
        "ticker": ticker.replace("=X", ""),
        "tf": interval,
        "bars": len(bt_data),
        "trades": result.get("total_trades") or 0,
        "wr": result.get("win_rate") or 0,
        "pf": result.get("profit_factor") or 0,
        "dd": result.get("max_drawdown") or 0,
        "sharpe": result.get("sharpe_ratio") or 0,
    }


def main():
    rows = []
    total = len(ALL_STRATEGIES) * len(TICKERS) * len(TIMEFRAMES)
    i = 0
    for strat_name, strat_cls in ALL_STRATEGIES.items():
        for ticker in TICKERS:
            for interval, period in TIMEFRAMES:
                i += 1
                try:
                    r = run_one(ticker, interval, period, strat_name, strat_cls)
                    rows.append(r)
                except Exception as e:
                    rows.append({
                        "strategy": strat_name, "ticker": ticker,
                        "tf": interval, "error": str(e)[:60],
                    })

    # ソート: PF降順
    ok = [r for r in rows if "error" not in r]
    ng = [r for r in rows if "error" in r]
    ok.sort(key=lambda r: (r["pf"], r["wr"]), reverse=True)

    print(f"\n{'strategy':20s} {'ticker':8s} {'tf':4s} "
          f"{'trades':>6s} {'wr%':>5s} {'pf':>5s} {'dd%':>6s} {'sr':>6s}")
    for r in ok:
        marker = " ★" if r["pf"] > 1.5 and r["trades"] >= 30 else "  "
        print(f"{r['strategy']:20s} {r['ticker']:8s} {r['tf']:4s} "
              f"{r['trades']:>6d} {r['wr']:>5.1f} {r['pf']:>5.2f} "
              f"{r['dd']:>6.1f} {r['sharpe']:>6.2f}{marker}")
    if ng:
        print("\n[ERRORS]")
        for r in ng:
            print(f"  {r['strategy']} {r['ticker']} {r['tf']}: {r['error']}")


if __name__ == "__main__":
    main()
