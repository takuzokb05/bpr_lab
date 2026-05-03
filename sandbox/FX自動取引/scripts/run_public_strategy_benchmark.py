"""公開実装ベンチマーク（task #17）

freqtrade HLHB / Linda Raschke Holy Grail を Python ポートし、
本番 RsiPullback と同じデータ・同じ評価条件で比較する。

出力:
- data/strategy_benchmark.csv
- 標準出力に整形比較表
- docs/public_strategy_benchmark.md は別途生成

評価メトリクス:
- PF, Sharpe, MaxDD, WinRate, Trades, ReturnPct
- Sharpe 95% CI（年率換算 SE = sqrt(1/N)、N=Trades）
- IS/OOS 70:30 分割で WFE
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import yfinance as yf  # noqa: E402

from src.backtester import BacktestEngine  # noqa: E402
from src.strategy._bench_hlhb import HlhbBenchBT  # noqa: E402
from src.strategy._bench_holy_grail import HolyGrailBenchBT  # noqa: E402
from src.strategy.variants_bt import MTFPullbackBT  # noqa: E402

# ---- 設定 ----------------------------------------------------------------
TICKERS = {
    "USD_JPY": "USDJPY=X",
    "EUR_USD": "EURUSD=X",
    "GBP_JPY": "GBPJPY=X",
}
INTERVAL = "15m"
PERIOD = "60d"  # yfinance の 15m は最大 60 日

STRATEGIES = {
    # 本番 RsiPullback と等価ロジック（MA200 + RSI 35/65 + ATR SL/TP）
    "RsiPullback": MTFPullbackBT,
    "freqtrade_HLHB": HlhbBenchBT,
    "HolyGrail": HolyGrailBenchBT,
}

CACHE_DIR = ROOT / "data"
OUT_CSV = ROOT / "data" / "strategy_benchmark.csv"


# ---- ヘルパー -------------------------------------------------------------
def cache_path(pair_key: str, interval: str) -> Path:
    """data/_yf_cache_<pair>_<interval>.csv のパスを返す（strategy-validator と共有）"""
    safe = pair_key.replace("=X", "").replace("/", "_")
    return CACHE_DIR / f"_yf_cache_{safe}_{interval}.csv"


def fetch_ohlcv(ticker: str, pair_key: str, interval: str, period: str) -> pd.DataFrame:
    """yfinance から OHLCV を取得（CSV キャッシュ共有）"""
    cp = cache_path(pair_key, interval)
    if cp.exists():
        df = pd.read_csv(cp, index_col=0, parse_dates=True)
        if not df.empty:
            return df

    df = yf.download(
        ticker, period=period, interval=interval,
        auto_adjust=False, progress=False,
    )
    if df.empty:
        raise ValueError(f"yfinance returned empty for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df.columns = [c.lower() for c in df.columns]
    df["volume"] = df["volume"].replace(0, 1)
    df = df[["open", "high", "low", "close", "volume"]]

    cp.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cp)
    return df


def sharpe_ci(sharpe: float | None, n_trades: int | None) -> tuple[float | None, float | None]:
    """Sharpe Ratio の 95% 信頼区間 (近似: SE = sqrt(1/N))

    厳密にはリターンの自己相関なども絡むが、ベンチマーク比較として
    トレード数の少なさ由来の不確実性を可視化する目的で十分。
    """
    if sharpe is None or n_trades is None or n_trades < 2:
        return (None, None)
    se = math.sqrt(1.0 / n_trades)
    return (sharpe - 1.96 * se, sharpe + 1.96 * se)


def fmt_ci(lo: float | None, hi: float | None) -> str:
    if lo is None or hi is None:
        return "(N/A)"
    return f"({lo:+.2f}, {hi:+.2f})"


# ---- 本体 ---------------------------------------------------------------
def run_benchmark() -> list[dict]:
    rows: list[dict] = []

    for pair_key, ticker in TICKERS.items():
        print(f"\n[fetch] {pair_key} ({ticker}) {INTERVAL} {PERIOD}")
        try:
            df = fetch_ohlcv(ticker, pair_key, INTERVAL, PERIOD)
        except Exception as e:
            print(f"  [skip] data fetch failed: {e}")
            continue
        bars = len(df)
        print(f"  bars={bars}")

        bt_data = BacktestEngine.prepare_data(df)

        for strat_name, strat_cls in STRATEGIES.items():
            print(f"  [run] {strat_name}")
            try:
                with BacktestEngine(db_path=":memory:") as eng:
                    # フル期間結果
                    full = eng.run(
                        bt_data, strat_cls,
                        cash=1_000_000, commission=0.00002, margin=1 / 25,
                        instrument=pair_key, auto_spread=True,
                    )
                    # IS/OOS 70:30
                    try:
                        wf = eng.run_in_out_sample(
                            bt_data, strat_cls, split_ratio=0.7,
                            cash=1_000_000, commission=0.00002, margin=1 / 25,
                            instrument=pair_key, auto_spread=True,
                        )
                        wfe = wf.get("wfe")
                        oos_pf = wf["out_of_sample"].get("profit_factor")
                        oos_sr = wf["out_of_sample"].get("sharpe_ratio")
                        oos_trades = wf["out_of_sample"].get("total_trades")
                    except Exception as e:
                        print(f"    [WFE skip] {e}")
                        wfe = None
                        oos_pf = oos_sr = oos_trades = None
            except Exception as e:
                print(f"    [error] {e}")
                rows.append({
                    "strategy": strat_name, "pair": pair_key,
                    "error": str(e)[:100],
                })
                continue

            sr = full.get("sharpe_ratio")
            n = full.get("total_trades") or 0
            ci_lo, ci_hi = sharpe_ci(sr, n)

            rows.append({
                "strategy": strat_name,
                "pair": pair_key,
                "bars": bars,
                "trades": n,
                "win_rate": full.get("win_rate"),
                "profit_factor": full.get("profit_factor"),
                "max_drawdown": full.get("max_drawdown"),
                "sharpe_ratio": sr,
                "sharpe_ci_lo": ci_lo,
                "sharpe_ci_hi": ci_hi,
                "return_pct": full.get("return_pct"),
                "wfe": wfe,
                "oos_pf": oos_pf,
                "oos_sr": oos_sr,
                "oos_trades": oos_trades,
            })

    return rows


def print_table(rows: list[dict]) -> None:
    ok = [r for r in rows if "error" not in r]
    ng = [r for r in rows if "error" in r]

    header = (
        f"\n{'Strategy':16s} {'Pair':8s} {'Trades':>6s} "
        f"{'WR%':>5s} {'PF':>5s} {'Sharpe':>7s} {'95%CI':>18s} "
        f"{'DD%':>6s} {'Ret%':>7s} {'WFE':>6s}"
    )
    print(header)
    print("-" * len(header))
    for r in sorted(ok, key=lambda x: (x["pair"], x["strategy"])):
        sr = r.get("sharpe_ratio")
        sr_str = f"{sr:>+7.2f}" if sr is not None else "    N/A"
        ci = fmt_ci(r.get("sharpe_ci_lo"), r.get("sharpe_ci_hi"))
        wr = r.get("win_rate") or 0
        pf = r.get("profit_factor") or 0
        dd = r.get("max_drawdown") or 0
        ret = r.get("return_pct") or 0
        wfe = r.get("wfe")
        wfe_str = f"{wfe:>+6.2f}" if wfe is not None else "   N/A"
        print(
            f"{r['strategy']:16s} {r['pair']:8s} {r['trades']:>6d} "
            f"{wr:>5.1f} {pf:>5.2f} {sr_str} {ci:>18s} "
            f"{dd:>6.1f} {ret:>+7.2f} {wfe_str}"
        )

    if ng:
        print("\n[ERRORS]")
        for r in ng:
            print(f"  {r['strategy']} {r['pair']}: {r.get('error')}")


def save_csv(rows: list[dict]) -> None:
    if not rows:
        return
    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\n[saved] {OUT_CSV}")


def main() -> None:
    rows = run_benchmark()
    print_table(rows)
    save_csv(rows)


if __name__ == "__main__":
    main()
