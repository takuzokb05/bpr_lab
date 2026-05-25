"""Contrarian pragmatist 用 signal_v2 簡易 2 年バックテスト (GBP_JPY M15)

目的:
- SPEC v2 PoC が経済性 (実利) として成立するか、桁感を把握する
- 完璧ではない。±50% の精度で十分

ルール:
- SeasonalDetector で VOLATILE 判定された M15 バーで signal_v2.generate_signal を実行
- direction が long/short になったら次足の open でエントリー (現実的なフィル仮定)
- SL/TP は signal_v2 仕様 (ATR(14) × 1.5 / × 3.0)
- スプレッド -2 pips を毎トレード控除
- lot 0.01 (= 1000 units) で JPY 換算
- データ範囲: 2024-05-07 〜 2026-05-07 (M15 2 年)
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.spec_v2.seasonal_detection import (
    SeasonalDetector, SeasonRegime, GBP_JPY_CONFIG, calc_yang_zhang
)
from src.spec_v2.signal_v2 import (
    BREAKOUT_LOOKBACK, ATR_PERIOD, ATR_SL_MULT, ATR_TP_MULT, PIP_SIZE, calc_atr
)

# ----------------------------------------
# データ読み込み
# ----------------------------------------
m15_csv = ROOT / "data" / "mt5_GBP_JPY_M15_2y.csv"
h1_csv = ROOT / "data" / "mt5_GBP_JPY_H1_5y.csv"

m15 = pd.read_csv(m15_csv, parse_dates=["datetime"]).set_index("datetime").sort_index()
h1_all = pd.read_csv(h1_csv, parse_dates=["datetime"]).set_index("datetime").sort_index()

# M15 期間に合わせる
m15_start = m15.index[0]
m15_end = m15.index[-1]
print(f"M15 期間: {m15_start} -> {m15_end} ({len(m15)} bars)")

# H1 を M15 範囲 + バッファでスライス
h1 = h1_all.loc[m15_start - pd.Timedelta(hours=200):m15_end].copy()
print(f"H1 期間: {h1.index[0]} -> {h1.index[-1]} ({len(h1)} bars)")

# ----------------------------------------
# 事前計算: M15 YZ_vol, H1 YZ_vol, M15 ATR
# ----------------------------------------
print("計算: M15 YZ_vol...")
m15["yz_vol"] = calc_yang_zhang(m15, window=GBP_JPY_CONFIG["m15_yz_window"])

print("計算: H1 YZ_vol...")
h1["yz_vol"] = calc_yang_zhang(h1, window=GBP_JPY_CONFIG["h1_yz_window"])

print("計算: M15 ATR(14)...")
m15["atr"] = calc_atr(m15, ATR_PERIOD)

# M15 ローリング 30%ile (ローリング窓 5000 = 約 2.5 か月)
print("計算: M15 30%ile (rolling 5000)...")
m15["yz_p30"] = m15["yz_vol"].rolling(GBP_JPY_CONFIG["m15_rolling_window_bars"]).quantile(0.30)

# H1 yz_vol を M15 にリサンプル (asof で直近 H1 値を持ってくる)
print("マージ: H1 yz_vol を M15 に...")
h1_yz = h1[["yz_vol"]].rename(columns={"yz_vol": "h1_yz_vol"})
m15 = pd.merge_asof(
    m15.reset_index(), h1_yz.reset_index(),
    on="datetime", direction="backward"
).set_index("datetime")

# Breakout lookback の高値/安値 (直前 20 本、最新除く)
print("計算: 直近 20 本 high/low...")
m15["lookback_high"] = m15["high"].shift(1).rolling(BREAKOUT_LOOKBACK).max()
m15["lookback_low"] = m15["low"].shift(1).rolling(BREAKOUT_LOOKBACK).min()

# ----------------------------------------
# VOLATILE 判定 + ブレイクアウト判定
# ----------------------------------------
H1_THR = GBP_JPY_CONFIG["h1_threshold_abs"]
m15["volatile"] = (
    (m15["yz_vol"] > m15["yz_p30"]) &
    (m15["h1_yz_vol"] > H1_THR)
)

m15["sig_long"] = m15["volatile"] & (m15["close"] > m15["lookback_high"]) & m15["atr"].notna()
m15["sig_short"] = m15["volatile"] & (m15["close"] < m15["lookback_low"]) & m15["atr"].notna()

n_volatile = int(m15["volatile"].sum())
n_signal_long = int(m15["sig_long"].sum())
n_signal_short = int(m15["sig_short"].sum())
print(f"\n=== 統計 ===")
print(f"M15 総バー: {len(m15)}")
print(f"VOLATILE 判定バー: {n_volatile} ({n_volatile/len(m15)*100:.1f}%)")
print(f"VOLATILE 中 long シグナル: {n_signal_long}")
print(f"VOLATILE 中 short シグナル: {n_signal_short}")
print(f"シグナル発生率 (VOLATILE 中): {(n_signal_long+n_signal_short)/max(n_volatile,1)*100:.2f}%")

# ----------------------------------------
# トレードシミュレーション
# ----------------------------------------
# 1 シグナル発生 → 次足 open でエントリー → SL/TP ヒットまで保有
# 同時保有は 1 ポジションのみ (簡易)

UNITS = 1000  # lot 0.01
SPREAD_PIPS = 2.0  # GBP_JPY デモ実測ベース (実取引データから推定)

# index 化
m15 = m15.reset_index()
trades = []
in_position = None  # dict or None

for i in range(len(m15) - 1):
    row = m15.iloc[i]
    next_row = m15.iloc[i + 1]

    # 既存ポジションのチェック
    if in_position is not None:
        # 次足の high/low で SL/TP ヒット判定
        # 同足内で両方ヒットしたら SL 優先 (保守)
        hi = next_row["high"]
        lo = next_row["low"]
        if in_position["direction"] == "long":
            if lo <= in_position["sl"]:
                exit_price = in_position["sl"]
                outcome = "SL"
            elif hi >= in_position["tp"]:
                exit_price = in_position["tp"]
                outcome = "TP"
            else:
                exit_price = None
                outcome = None
        else:  # short
            if hi >= in_position["sl"]:
                exit_price = in_position["sl"]
                outcome = "SL"
            elif lo <= in_position["tp"]:
                exit_price = in_position["tp"]
                outcome = "TP"
            else:
                exit_price = None
                outcome = None

        if exit_price is not None:
            dirn = 1 if in_position["direction"] == "long" else -1
            pips = (exit_price - in_position["entry"]) * dirn / PIP_SIZE - SPREAD_PIPS
            pnl_jpy = pips * PIP_SIZE * UNITS  # JPY クロス
            in_position["exit_time"] = next_row["datetime"]
            in_position["exit_price"] = exit_price
            in_position["pips"] = pips
            in_position["pnl_jpy"] = pnl_jpy
            in_position["outcome"] = outcome
            trades.append(in_position)
            in_position = None

    # 新規シグナル (ポジションなしなら)
    if in_position is None and not pd.isna(row["atr"]):
        atr = row["atr"]
        if row["sig_long"]:
            entry = next_row["open"]
            sl = entry - atr * ATR_SL_MULT
            tp = entry + atr * ATR_TP_MULT
            in_position = dict(
                direction="long", entry_time=next_row["datetime"], entry=entry,
                sl=sl, tp=tp, atr=atr,
            )
        elif row["sig_short"]:
            entry = next_row["open"]
            sl = entry + atr * ATR_SL_MULT
            tp = entry - atr * ATR_TP_MULT
            in_position = dict(
                direction="short", entry_time=next_row["datetime"], entry=entry,
                sl=sl, tp=tp, atr=atr,
            )

# ----------------------------------------
# 集計
# ----------------------------------------
if not trades:
    print("\nNO TRADES")
    sys.exit(0)

td = pd.DataFrame(trades)
td["entry_time"] = pd.to_datetime(td["entry_time"])
td["exit_time"] = pd.to_datetime(td["exit_time"])
td["hold_min"] = (td["exit_time"] - td["entry_time"]).dt.total_seconds() / 60

n_total = len(td)
wins = td[td["pips"] > 0]
losses = td[td["pips"] <= 0]
n_win = len(wins)
n_loss = len(losses)
wr = n_win / n_total * 100

total_pips = td["pips"].sum()
total_pnl = td["pnl_jpy"].sum()
avg_win_pips = wins["pips"].mean() if n_win else 0
avg_loss_pips = losses["pips"].mean() if n_loss else 0
gross_win = wins["pips"].sum()
gross_loss = -losses["pips"].sum() if n_loss else 0.0001
pf = gross_win / gross_loss if gross_loss > 0 else float("inf")

# 月次 PnL
td["month"] = td["exit_time"].dt.strftime("%Y-%m")
monthly = td.groupby("month")["pnl_jpy"].agg(["sum", "count"])
monthly_pnl = monthly["sum"]
sharpe = (monthly_pnl.mean() / monthly_pnl.std() * np.sqrt(12)) if len(monthly_pnl) > 1 and monthly_pnl.std() > 0 else 0

# 最大ドローダウン
equity = td["pnl_jpy"].cumsum()
peak = equity.cummax()
dd = (equity - peak)
max_dd = dd.min()

print(f"\n=== バックテスト結果 (2024-05 〜 2026-05, lot 0.01) ===")
print(f"トレード総数: {n_total}")
print(f"勝率: {wr:.1f}% ({n_win}/{n_total})")
print(f"平均勝ち pips: {avg_win_pips:.1f}")
print(f"平均負け pips: {avg_loss_pips:.1f}")
print(f"累計 pips: {total_pips:.1f}")
print(f"累計 PnL (JPY, lot 0.01): {total_pnl:.0f}")
print(f"PF: {pf:.2f}")
print(f"月次 PnL std (JPY): {monthly_pnl.std():.0f}")
print(f"月次 PnL mean (JPY): {monthly_pnl.mean():.0f}")
print(f"年間 PnL 推定 (JPY): {monthly_pnl.mean() * 12:.0f}")
print(f"シャープ (年率, 月次ベース): {sharpe:.2f}")
print(f"最大 DD (JPY): {max_dd:.0f}")

print(f"\n=== 月次内訳 ===")
print(monthly.to_string())

# 保存
td.to_csv(ROOT / "data" / "_contrarian_bt_trades.csv", index=False)
monthly.to_csv(ROOT / "data" / "_contrarian_bt_monthly.csv")
print(f"\nsaved: data/_contrarian_bt_trades.csv, _contrarian_bt_monthly.csv")
