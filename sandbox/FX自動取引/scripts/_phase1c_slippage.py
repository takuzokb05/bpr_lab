"""Phase 1X-Probe Job-C: 本番trades のスリッページ実測 (#7)

karen 反論「スリッページ実測がBTに正しく注入されていない」への定量答え。

手法:
1. 本番DB (snapshot) の trades から open_price / opened_at を取得
2. 同時刻の MT5 M15 OHLC（CSV）から「直前バーのclose」を「想定価格」として取得
3. 実約定価格 - 想定価格 = スリッページ pip
4. ペア別の分布（平均、中央値、95%ile）と現状の TYPICAL_SPREADS_PIPS の比較

注意: M15 closeを想定価格とするのは粗い。tick精度ではないが、ペア別の傾向は見える。
"""
from __future__ import annotations

import io
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

# 既存の TYPICAL_SPREADS_PIPS を import
sys.path.insert(0, str(ROOT))
from src.backtester import TYPICAL_SPREADS_PIPS  # noqa: E402


def load_trades(db_path: Path) -> pd.DataFrame:
    con = sqlite3.connect(str(db_path))
    df = pd.read_sql_query(
        "SELECT instrument, open_price, opened_at, close_price, closed_at, units, pl "
        "FROM trades WHERE status='closed' ORDER BY opened_at",
        con,
    )
    con.close()
    return df


def load_ohlc(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def get_prior_close(ohlc: pd.DataFrame, ts: pd.Timestamp):
    """ts 以前の最後の M15 バーの close を返す。"""
    if ts.tz is None:
        ts = ts.tz_localize("UTC")
    elif str(ts.tz) != "UTC":
        ts = ts.tz_convert("UTC")
    pos = ohlc.index.searchsorted(ts, side="right") - 1
    if pos < 0:
        return None
    return float(ohlc.iloc[pos]["close"])


def main():
    data_dir = ROOT / "data"
    prod_db = data_dir / "fx_trading_prod_snapshot.db"
    if not prod_db.exists():
        prod_db = data_dir / "fx_trading.db"
    if not prod_db.exists():
        print(f"⚠ DB が見つからない: {prod_db}")
        return

    pairs_csv = {
        "USD_JPY": data_dir / "mt5_USD_JPY_M15_2y.csv",
        "EUR_USD": data_dir / "mt5_EUR_USD_M15_2y.csv",
        "GBP_JPY": data_dir / "mt5_GBP_JPY_M15_2y.csv",
    }

    print(f"DB: {prod_db}")
    trades = load_trades(prod_db)
    print(f"closed trades: {len(trades)}")

    ohlc_cache = {}
    rows = []
    for _, t in trades.iterrows():
        inst = t["instrument"]
        csv = pairs_csv.get(inst)
        if csv is None or not csv.exists():
            continue
        if inst not in ohlc_cache:
            ohlc_cache[inst] = load_ohlc(csv)
        ohlc = ohlc_cache[inst]

        try:
            opened_at = pd.Timestamp(t["opened_at"])
        except Exception:
            continue
        expected = get_prior_close(ohlc, opened_at)
        if expected is None:
            continue
        actual = float(t["open_price"])
        units = int(t["units"])
        side = "BUY" if units > 0 else "SELL"

        # signed slippage:
        #   BUY: actual - expected (正なら高く買って不利)
        #   SELL: expected - actual (正なら安く売って不利)
        if side == "BUY":
            signed = actual - expected
        else:
            signed = expected - actual

        pip_size = 0.01 if "JPY" in inst else 0.0001
        signed_pips = signed / pip_size

        rows.append({
            "instrument": inst,
            "side": side,
            "opened_at": str(opened_at),
            "actual": actual,
            "expected": expected,
            "signed_pips": signed_pips,
            "abs_pips": abs(signed_pips),
        })

    df = pd.DataFrame(rows)
    print(f"\n計測対象: {len(df)} trades")

    # ペア別分布
    print(f"\n{'='*90}")
    print(f"スリッページ実測（pip単位、signed = 不利方向に正）")
    print(f"{'='*90}")
    print(f"{'Pair':<10} {'N':>4} {'Mean':>7} {'Median':>7} {'95%ile':>7} "
          f"{'Max':>7} | {'Current spread':>15}")
    print("-" * 90)
    for inst, group in df.groupby("instrument"):
        n = len(group)
        mean = group["signed_pips"].mean()
        median = group["signed_pips"].median()
        pct95 = group["signed_pips"].quantile(0.95)
        mx = group["signed_pips"].max()
        current = TYPICAL_SPREADS_PIPS.get(inst, 2.0)
        # 警告: 95%ile が現状値の2倍超なら過小評価
        warn = "⚠ 過小評価" if pct95 > current * 2 else ""
        print(f"{inst:<10} {n:>4} {mean:>+7.2f} {median:>+7.2f} {pct95:>+7.2f} "
              f"{mx:>+7.2f} | {current:>15.1f} {warn}")

    # 推奨スプレッド値（95%ile）
    print(f"\n{'='*90}")
    print(f"推奨スプレッド値 (95%ile を保守的に採用、絶対値)")
    print(f"{'='*90}")
    print(f"{'Pair':<10} {'Current':>8} {'Recommend (95%abs)':>22} {'Δ':>7}")
    print("-" * 60)
    for inst, group in df.groupby("instrument"):
        current = TYPICAL_SPREADS_PIPS.get(inst, 2.0)
        # abs ベースで 95%ile（実際の取引コスト）
        abs95 = group["abs_pips"].quantile(0.95)
        delta = abs95 - current
        marker = "↑" if delta > 0.5 else ("OK" if abs(delta) <= 0.5 else "↓")
        print(f"{inst:<10} {current:>8.1f} {abs95:>22.2f} {delta:>+7.2f} {marker}")

    # JSON 保存
    import json
    summary = {
        "n_trades": len(df),
        "by_pair": {},
        "current_spreads": TYPICAL_SPREADS_PIPS,
    }
    for inst, group in df.groupby("instrument"):
        summary["by_pair"][inst] = {
            "n": len(group),
            "signed_mean": float(group["signed_pips"].mean()),
            "signed_median": float(group["signed_pips"].median()),
            "signed_p95": float(group["signed_pips"].quantile(0.95)),
            "abs_mean": float(group["abs_pips"].mean()),
            "abs_p95": float(group["abs_pips"].quantile(0.95)),
            "abs_max": float(group["abs_pips"].max()),
        }
    out_json = data_dir / "phase1c_slippage.json"
    out_json.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\n[saved] {out_json}")


if __name__ == "__main__":
    main()
