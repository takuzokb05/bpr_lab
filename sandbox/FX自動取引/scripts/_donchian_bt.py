"""Donchian Channel ブレイクアウト (D1) 簡易バックテスト

目的:
- Phase 0 補強候補「長期トレンドフォロー」の Gate 0 PF を実測する
- 過去5年 (2020-10 〜 2026-05) で 3 ペア (GBP_JPY, USD_JPY, EUR_USD) を測定
- 完璧ではない、±50% の精度で十分 (_contrarian_bt.py と同じ精度感)

ルール (古典 Turtle System 簡易版):
- N=20日高値を当日終値が上抜けたら次足 open で long エントリー
- N=20日安値を当日終値が下抜けたら次足 open で short エントリー
- SL: ATR(14) × 2.0
- Trailing stop: 直近 10日安値 (long) / 10日高値 (short) — Turtle exit
- 同時保有は 1 ポジション (簡易)
- スプレッド: JPY ペア -2 pips、EUR_USD -1 pip 控除
- lot 0.01 で JPY 換算 (EUR_USD は USD→JPY @ 150 で簡易換算)
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# ----------------------------------------
# パラメータ (Turtle 流の古典値)
# ----------------------------------------
ENTRY_LOOKBACK = 20  # N日高値/安値ブレイク
EXIT_LOOKBACK = 10   # Turtle exit (反対方向 10日高値/安値)
ATR_PERIOD = 14
ATR_SL_MULT = 2.0    # 初期 SL
UNITS = 1000         # lot 0.01

# ペアごとの設定
PAIR_CONFIG = {
    "GBP_JPY": {"csv": "mt5_GBP_JPY_D1_10y.csv", "pip": 0.01, "spread_pips": 2.0, "jpy_quote": True},
    "USD_JPY": {"csv": "mt5_USD_JPY_D1_10y.csv", "pip": 0.01, "spread_pips": 2.0, "jpy_quote": True},
    "EUR_USD": {"csv": "mt5_EUR_USD_D1_10y.csv", "pip": 0.0001, "spread_pips": 1.0, "jpy_quote": False},
}

# EUR_USD の USD→JPY 換算 (簡易、固定 150)
USD_JPY_FIXED = 150.0


def calc_atr(df: pd.DataFrame, period: int) -> pd.Series:
    """ATR(period) 計算 (Wilder smoothing 簡易版、EMA で代替)"""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def run_bt(pair: str) -> dict:
    cfg = PAIR_CONFIG[pair]
    df = pd.read_csv(ROOT / "data" / cfg["csv"], parse_dates=["datetime"]).set_index("datetime").sort_index()
    df = df[df.index >= "2020-10-14"]  # 5年強

    df["atr"] = calc_atr(df, ATR_PERIOD)
    df["high_n"] = df["high"].shift(1).rolling(ENTRY_LOOKBACK).max()
    df["low_n"] = df["low"].shift(1).rolling(ENTRY_LOOKBACK).min()
    df["high_exit"] = df["high"].shift(1).rolling(EXIT_LOOKBACK).max()
    df["low_exit"] = df["low"].shift(1).rolling(EXIT_LOOKBACK).min()

    df["sig_long"] = (df["close"] > df["high_n"]) & df["atr"].notna()
    df["sig_short"] = (df["close"] < df["low_n"]) & df["atr"].notna()

    df = df.reset_index()
    trades = []
    pos = None

    for i in range(len(df) - 1):
        row = df.iloc[i]
        nxt = df.iloc[i + 1]

        # 既存ポジ管理: 翌足 high/low で SL or trailing exit 判定
        if pos is not None:
            hi, lo = nxt["high"], nxt["low"]
            # trailing stop 更新 (各バーで更新)
            if pos["direction"] == "long":
                trail = row["low_exit"]
                if not pd.isna(trail):
                    pos["sl"] = max(pos["sl"], trail)  # ロングは sl を引き上げ
                if lo <= pos["sl"]:
                    exit_price = pos["sl"]
                    outcome = "TRAIL_SL" if pos["sl"] > pos["entry"] - pos["atr"] * ATR_SL_MULT * 0.99 else "INIT_SL"
                    pos["exit_time"] = nxt["datetime"]
                    pos["exit_price"] = exit_price
                    dirn = 1
                    pips = (exit_price - pos["entry"]) * dirn / cfg["pip"] - cfg["spread_pips"]
                    pos["pips"] = pips
                    if cfg["jpy_quote"]:
                        pnl_jpy = pips * cfg["pip"] * UNITS
                    else:
                        # EUR_USD: pips * pip_size * units = USD → JPY 換算
                        pnl_jpy = pips * cfg["pip"] * UNITS * USD_JPY_FIXED
                    pos["pnl_jpy"] = pnl_jpy
                    pos["outcome"] = outcome
                    trades.append(pos)
                    pos = None
            else:  # short
                trail = row["high_exit"]
                if not pd.isna(trail):
                    pos["sl"] = min(pos["sl"], trail)
                if hi >= pos["sl"]:
                    exit_price = pos["sl"]
                    outcome = "TRAIL_SL" if pos["sl"] < pos["entry"] + pos["atr"] * ATR_SL_MULT * 0.99 else "INIT_SL"
                    pos["exit_time"] = nxt["datetime"]
                    pos["exit_price"] = exit_price
                    dirn = -1
                    pips = (exit_price - pos["entry"]) * dirn / cfg["pip"] - cfg["spread_pips"]
                    pos["pips"] = pips
                    if cfg["jpy_quote"]:
                        pnl_jpy = pips * cfg["pip"] * UNITS
                    else:
                        pnl_jpy = pips * cfg["pip"] * UNITS * USD_JPY_FIXED
                    pos["pnl_jpy"] = pnl_jpy
                    pos["outcome"] = outcome
                    trades.append(pos)
                    pos = None

        # 新規エントリー (ポジなしのみ)
        if pos is None and not pd.isna(row["atr"]):
            atr = row["atr"]
            if row["sig_long"]:
                entry = nxt["open"]
                sl = entry - atr * ATR_SL_MULT
                pos = dict(
                    pair=pair, direction="long", entry_time=nxt["datetime"],
                    entry=entry, sl=sl, atr=atr,
                )
            elif row["sig_short"]:
                entry = nxt["open"]
                sl = entry + atr * ATR_SL_MULT
                pos = dict(
                    pair=pair, direction="short", entry_time=nxt["datetime"],
                    entry=entry, sl=sl, atr=atr,
                )

    if not trades:
        return {"pair": pair, "n": 0}

    td = pd.DataFrame(trades)
    td["hold_days"] = (pd.to_datetime(td["exit_time"]) - pd.to_datetime(td["entry_time"])).dt.total_seconds() / 86400

    n = len(td)
    wins = td[td["pips"] > 0]
    losses = td[td["pips"] <= 0]
    wr = len(wins) / n * 100 if n else 0

    gw = wins["pips"].sum()
    gl = -losses["pips"].sum() if len(losses) else 0.0001
    pf = gw / gl if gl > 0 else float("inf")

    # スプレッド除外版 PF (純シグナル評価)
    td["pips_nospread"] = td["pips"] + cfg["spread_pips"]
    gw_ns = td[td["pips_nospread"] > 0]["pips_nospread"].sum()
    gl_ns = -td[td["pips_nospread"] <= 0]["pips_nospread"].sum() if (td["pips_nospread"] <= 0).any() else 0.0001
    pf_nospread = gw_ns / gl_ns if gl_ns > 0 else float("inf")

    total_pips = td["pips"].sum()
    total_pnl_jpy = td["pnl_jpy"].sum()

    # 月次
    td["exit_time"] = pd.to_datetime(td["exit_time"])
    td["month"] = td["exit_time"].dt.strftime("%Y-%m")
    monthly = td.groupby("month")["pnl_jpy"].sum()
    sharpe = (monthly.mean() / monthly.std() * np.sqrt(12)) if len(monthly) > 1 and monthly.std() > 0 else 0

    # MaxDD
    equity = td["pnl_jpy"].cumsum()
    peak = equity.cummax()
    dd = equity - peak
    max_dd = dd.min()

    return {
        "pair": pair, "n": n, "wr": wr, "pf": pf, "pf_nospread": pf_nospread,
        "total_pips": total_pips, "total_pnl_jpy": total_pnl_jpy,
        "sharpe": sharpe, "max_dd": max_dd,
        "avg_hold_days": td["hold_days"].mean(),
        "yearly_pnl": monthly.mean() * 12,
        "trades_df": td,
    }


if __name__ == "__main__":
    print(f"Donchian {ENTRY_LOOKBACK}/{EXIT_LOOKBACK} D1 BT (5年, ATR_SL_MULT={ATR_SL_MULT})\n")
    results = []
    for pair in PAIR_CONFIG.keys():
        r = run_bt(pair)
        results.append(r)
        if r["n"] == 0:
            print(f"[{pair}] NO TRADES")
            continue
        print(f"[{pair}]")
        print(f"  trades={r['n']}, wr={r['wr']:.1f}%, PF={r['pf']:.2f} (no-spread PF={r['pf_nospread']:.2f})")
        print(f"  total_pips={r['total_pips']:.0f}, total_pnl_jpy={r['total_pnl_jpy']:.0f}")
        print(f"  sharpe={r['sharpe']:.2f}, max_dd={r['max_dd']:.0f} JPY")
        print(f"  avg_hold={r['avg_hold_days']:.1f}日, 年間PnL推定={r['yearly_pnl']:.0f} JPY")
        print()

    # 3 ペア合算
    all_td = pd.concat([r["trades_df"] for r in results if r["n"] > 0])
    all_td = all_td.sort_values("exit_time")
    n_total = len(all_td)
    gw = all_td[all_td["pips"] > 0]["pnl_jpy"].sum()
    gl = -all_td[all_td["pips"] <= 0]["pnl_jpy"].sum() if (all_td["pips"] <= 0).any() else 0.0001
    pf_all = gw / gl if gl > 0 else float("inf")
    total_pnl_all = all_td["pnl_jpy"].sum()
    eq = all_td["pnl_jpy"].cumsum()
    pk = eq.cummax()
    dd = (eq - pk).min()

    print(f"=== 3ペア合算 ===")
    print(f"trades={n_total}, PF={pf_all:.2f}, total_pnl_jpy={total_pnl_all:.0f}")
    print(f"max_dd={dd:.0f} JPY, 年間PnL推定={total_pnl_all/5:.0f} JPY (5年)")

    out = ROOT / "data" / "_donchian_bt_trades.csv"
    all_td.to_csv(out, index=False)
    print(f"\nsaved: {out}")
