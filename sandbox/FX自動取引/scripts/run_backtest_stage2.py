"""Stage 2設定で3ヶ月バックテスト実行

yfinanceからUSDJPY M15データを取得し、現在の設定で勝率・期待値を計算する。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import yfinance as yf
from src.backtester import BacktestEngine, RsiMaCrossoverBT


def fetch_m15_data(ticker: str, period: str = "60d") -> pd.DataFrame:
    """yfinanceからM15相当のデータを取得。
    Backtesting.pyはDatetimeIndexを要求するので、indexを維持しつつ
    小文字OHLCVカラムで返す（prepare_dataがcapitalizeする）。
    """
    df = yf.download(ticker, period=period, interval="15m",
                     auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError(f"no data for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df.columns = [c.lower() for c in df.columns]
    # volume==0 のバーが多いためダミー値で補完（ATR/ADX計算に影響しない）
    df["volume"] = df["volume"].replace(0, 1)
    return df[["open", "high", "low", "close", "volume"]]


def run(ticker: str):
    print(f"\n=== {ticker} M15 60日 バックテスト ===")
    df = fetch_m15_data(ticker)
    print(f"data: {len(df)}本 ({df.index[0]} 〜 {df.index[-1]})")

    bt_data = BacktestEngine.prepare_data(df)
    with BacktestEngine() as engine:
        result = engine.run(
            bt_data,
            RsiMaCrossoverBT,
            cash=1_000_000,
            commission=0.00002,
            margin=1/25,
        )
    # _extract_metrics の返却dictキー
    for key in ["total_trades", "win_rate", "total_return", "max_drawdown",
                "sharpe_ratio", "profit_factor", "expectancy", "avg_trade"]:
        if key in result:
            print(f"  {key}: {result[key]}")


if __name__ == "__main__":
    for t in ["USDJPY=X", "EURUSD=X", "GBPJPY=X"]:
        try:
            run(t)
        except Exception as e:
            print(f"  {t} FAILED: {e}")
