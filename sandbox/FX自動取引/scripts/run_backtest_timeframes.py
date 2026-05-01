"""タイムフレーム別バックテスト（M15/H1/H4/D）

同じMA Crossover+RSI+ADX戦略で時間足だけ変えて勝率を比較する。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import yfinance as yf
from src.backtester import BacktestEngine, RsiMaCrossoverBT


# (interval, period) ペア。yfinanceの制約に従う
TIMEFRAMES = [
    ("15m", "60d"),   # M15
    ("1h",  "720d"),  # H1 約2年
    ("4h",  "720d"),  # H4 約2年（4hはyfinance未対応のため1hから再サンプル）
    ("1d",  "2y"),    # D1
]

TICKERS = ["USDJPY=X", "EURUSD=X", "GBPJPY=X"]


def fetch_ohlcv(ticker: str, interval: str, period: str) -> pd.DataFrame:
    """yfinanceからOHLCVを取得し、4hなら1hから再サンプルする。"""
    if interval == "4h":
        base = yf.download(ticker, period=period, interval="1h",
                           auto_adjust=False, progress=False)
        if base.empty:
            raise ValueError(f"no 1h data for {ticker}")
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
            raise ValueError(f"no data for {ticker} {interval}")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df.columns = [c.lower() for c in df.columns]

    df["volume"] = df["volume"].replace(0, 1)
    return df[["open", "high", "low", "close", "volume"]]


def run(ticker: str, interval: str, period: str) -> dict:
    df = fetch_ohlcv(ticker, interval, period)
    bt_data = BacktestEngine.prepare_data(df)
    with BacktestEngine() as engine:
        result = engine.run(
            bt_data,
            RsiMaCrossoverBT,
            cash=1_000_000,
            commission=0.00002,
            margin=1/25,
        )
    return {
        "ticker": ticker,
        "interval": interval,
        "bars": len(bt_data),
        "trades": result.get("total_trades"),
        "win_rate": result.get("win_rate"),
        "pf": result.get("profit_factor"),
        "max_dd": result.get("max_drawdown"),
        "sharpe": result.get("sharpe_ratio"),
        "total_return": result.get("total_return"),
    }


def main():
    rows = []
    for ticker in TICKERS:
        for interval, period in TIMEFRAMES:
            try:
                r = run(ticker, interval, period)
                rows.append(r)
            except Exception as e:
                rows.append({
                    "ticker": ticker, "interval": interval,
                    "error": str(e)[:80],
                })

    # サマリ表
    print(f"\n{'ticker':10s} {'tf':5s} {'bars':>6s} {'trades':>6s} "
          f"{'wr%':>6s} {'pf':>6s} {'dd%':>7s} {'sharpe':>7s} {'ret%':>8s}")
    for r in rows:
        if "error" in r:
            print(f"{r['ticker']:10s} {r['interval']:5s} ERROR: {r['error']}")
        else:
            wr = r["win_rate"] or 0
            pf = r["pf"] or 0
            dd = r["max_dd"] or 0
            sr = r["sharpe"] or 0
            ret = r["total_return"] or 0
            trades = r["trades"] or 0
            print(f"{r['ticker']:10s} {r['interval']:5s} {r['bars']:>6d} "
                  f"{trades:>6d} {wr:>6.1f} {pf:>6.2f} {dd:>7.1f} "
                  f"{sr:>7.2f} {ret:>8.1f}")


if __name__ == "__main__":
    main()
