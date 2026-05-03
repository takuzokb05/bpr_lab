"""MT5 から長期 OHLCV データを CSV に export する。

yfinance の M15 60日上限を突破して長期検証 (USD/JPY 5年 M15 等) を
可能にするためのデータ取得スクリプト。

## 実行環境
VPS (MT5 ターミナル稼働中) で実行する。ローカルでは動かない。

## 使い方
```bash
# VPS 上で
python scripts/export_mt5_history.py --instrument USD_JPY --timeframe M15 --years 5
python scripts/export_mt5_history.py --instrument EUR_USD --timeframe M15 --years 5
python scripts/export_mt5_history.py --instrument GBP_JPY --timeframe M15 --years 5

# 出力: data/mt5_<INSTRUMENT>_<TF>_<YEARS>y.csv
```

## なぜ MT5 か
- yfinance: M15 60日まで、H1 730日までが上限
- MT5: ブローカー (外為ファイネスト) のティック/ロウ足を 5 年以上取得可能
- 本番取引と同じ価格ソース → バックテスト/実戦の整合性が高い

詳細根拠: docs/remaining_tasks.md P1 #2, docs/strategy_validation_h1.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# MT5 の timeframe enum（VPS 上では import 可能、ローカル import エラー時は None）
try:
    import MetaTrader5 as mt5

    TIMEFRAME_MAP = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    TIMEFRAME_MAP = {}
    MT5_AVAILABLE = False


# 外為ファイネスト MT5 のシンボル接尾辞
SYMBOL_SUFFIX = "-"


def to_mt5_symbol(instrument: str) -> str:
    """USD_JPY → USDJPY-（外為ファイネスト形式）"""
    return instrument.replace("_", "") + SYMBOL_SUFFIX


def fetch_history(instrument: str, timeframe: str, years: int) -> pd.DataFrame:
    """MT5 から指定期間の OHLCV を取得する。

    内部で `mt5.copy_rates_range()` を使う。`copy_rates_from()` は
    最大バー数指定で取得するが、長期間で本数が読めないため範囲指定方式を採用。
    """
    if not MT5_AVAILABLE:
        raise RuntimeError(
            "MetaTrader5 モジュールが import できません。VPS 上で実行してください。",
        )
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize 失敗: {mt5.last_error()}")

    try:
        symbol = to_mt5_symbol(instrument)
        tf = TIMEFRAME_MAP.get(timeframe.upper())
        if tf is None:
            raise ValueError(
                f"未知の timeframe: {timeframe}. 有効: {list(TIMEFRAME_MAP.keys())}",
            )

        # シンボル選択（MT5 の Market Watch に追加）
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(
                f"symbol_select 失敗: {symbol} ({mt5.last_error()})",
            )

        end = datetime.now(timezone.utc)
        start = end.replace(year=end.year - years)
        print(f"[fetch] {symbol} {timeframe} {start.date()} → {end.date()}")

        rates = mt5.copy_rates_range(symbol, tf, start, end)
        if rates is None or len(rates) == 0:
            raise RuntimeError(
                f"履歴データが取得できませんでした: {symbol} {timeframe} "
                f"({mt5.last_error()})",
            )

        df = pd.DataFrame(rates)
        df["datetime"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df = df.rename(columns={
            "open": "open", "high": "high", "low": "low", "close": "close",
            "tick_volume": "volume",
        })
        df = df[["datetime", "open", "high", "low", "close", "volume"]]
        df = df.set_index("datetime").sort_index()
        return df
    finally:
        mt5.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--instrument", required=True, help="例: USD_JPY")
    parser.add_argument("--timeframe", default="M15", help="M1/M5/M15/M30/H1/H4/D1")
    parser.add_argument("--years", type=int, default=5, help="取得年数")
    parser.add_argument(
        "--out-dir", type=Path, default=ROOT / "data",
        help="出力先ディレクトリ",
    )
    args = parser.parse_args()

    if not MT5_AVAILABLE:
        print(
            "ERROR: MetaTrader5 モジュールが import できません。"
            "VPS 上 (MT5 ターミナル稼働環境) で実行してください。",
            file=sys.stderr,
        )
        return 1

    df = fetch_history(args.instrument, args.timeframe, args.years)
    n = len(df)
    print(f"[done] {n} bars 取得 ({df.index.min()} → {df.index.max()})")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"mt5_{args.instrument}_{args.timeframe}_{args.years}y.csv"
    df.to_csv(out)
    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"[saved] {out} ({size_mb:.1f} MB)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
