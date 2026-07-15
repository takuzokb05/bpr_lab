"""第2サイクル: signal_v2 過去シグナル抽出 + LLM 補完用メタデータ生成

CYCLE2_PLAN.md Step 1 担当。

## 役割
過去 M15 OHLC データから signal_v2 (ATR breakout) ロジックでシグナルを抽出し、
LLM フィルタ判定用の市況コンテキストと、BT 用の正解ラベルを付与した CSV を出力。

## データ範囲
- M15: 2024-05〜2026-05 (約2年) - 既存 mt5_*_M15_2y.csv
- (注) CYCLE2_PLAN.md は「過去5年」だが M15 既存データは 2年。
   - GBP_JPY M15 5年は MT5 経由で取得が必要だが、本タスク60分以内では不可
   - PF 0.95 を算出した `_contrarian_bt.py` も 2年データを使用
   - シグナル件数1000+ が想定され、統計的妥当性は確保見込み

## 対象ペア
- **GBP_JPY (主)**: signal_v2 + VOLATILE フィルタ (Pragmatist BT 仕様 = PF 0.95 算出元)
- USD_JPY (副): signal_v2 単体 (VOLATILE フィルタは GBP_JPY 専用設計のため)
- EUR_USD (副): signal_v2 単体

## CSV ヘッダー (CYCLE2_PLAN 仕様準拠)
signal_id, pair, timestamp_utc, direction, entry_price, sl_price, tp_price, sl_pips, tp_pips, atr,
m15_close_24h_ago, m15_close_12h_ago, m15_close_1h_ago,
related_eur_usd_24h_change_pct, related_usd_jpy_24h_change_pct, related_gbp_usd_24h_change_pct,
day_of_week, hour_utc, is_tokyo_session, is_london_session, is_ny_session,
high_after_entry_24h, low_after_entry_24h, close_24h_after_entry,
actual_pnl_pips_sl_tp_first_touch, actual_pnl_pips_4h_close, actual_pnl_pips_24h_close,
spread_assumed_pips, win_loss_sl_tp, holding_minutes_first_touch

## 後付けバイアス禁止原則
- シグナル時点 (timestamp_utc) で使えない情報は LLM 入力には入れない
- 関連通貨 24h 変化率: シグナル時刻の **24h前→シグナル時刻** の close 変化 (過去情報のみ)
- 高値/安値/24h後close, actual_pnl_*: **正解ラベル** であり LLM には渡さない (BT 用のみ)
"""
from __future__ import annotations

import sys
from pathlib import Path
import csv

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.spec_v2.signal_v2 import (
    BREAKOUT_LOOKBACK, ATR_PERIOD, ATR_SL_MULT, ATR_TP_MULT, calc_atr,
)
from src.spec_v2.seasonal_detection import GBP_JPY_CONFIG, calc_yang_zhang

# ============================================================
# ペア別設定
# ============================================================
PAIR_CONFIG = {
    "GBP_JPY": {
        "pip_size": 0.01,         # JPY クロス
        "spread_pips": 1.5,       # タスク指示
        "use_volatile_filter": True,   # PF 0.95 算出元の仕様
        "csv_m15": "mt5_GBP_JPY_M15_2y.csv",
        "csv_h1": "mt5_GBP_JPY_H1_5y.csv",
    },
    "USD_JPY": {
        "pip_size": 0.01,
        "spread_pips": 1.0,
        "use_volatile_filter": False,  # VOLATILE フィルタは GBP_JPY 専用検証 → 副では使わない
        "csv_m15": "mt5_USD_JPY_M15_2y.csv",
        "csv_h1": "mt5_USD_JPY_H1_5y.csv",
    },
    "EUR_USD": {
        "pip_size": 0.0001,        # 非 JPY クロス
        "spread_pips": 1.0,
        "use_volatile_filter": False,
        "csv_m15": "mt5_EUR_USD_M15_2y.csv",
        "csv_h1": "mt5_EUR_USD_H1_5y.csv",
    },
}

# 関連通貨ペア (24h 変化率算出用) - 全ペアに対する共通ベース
RELATED_PAIRS = {
    "EUR_USD": ROOT / "data" / "mt5_EUR_USD_H1_5y.csv",
    "USD_JPY": ROOT / "data" / "mt5_USD_JPY_H1_5y.csv",
    "GBP_USD": ROOT / "data" / "mt5_GBP_USD_H1_5y.csv",
}

# セッション定義 (UTC)
# Tokyo: 0-9 UTC (= 9-18 JST)
# London: 7-16 UTC
# NY: 13-22 UTC
def is_session(hour_utc: int, name: str) -> bool:
    if name == "tokyo":
        return 0 <= hour_utc < 9
    if name == "london":
        return 7 <= hour_utc < 16
    if name == "ny":
        return 13 <= hour_utc < 22
    return False


# ============================================================
# データ読み込み
# ============================================================
def load_m15(csv_name: str) -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / csv_name, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def load_h1(csv_name: str) -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / csv_name, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def load_related_close_h1() -> dict:
    """関連通貨 H1 close を辞書化 (24h 変化率算出用)"""
    out = {}
    for pair, path in RELATED_PAIRS.items():
        df = pd.read_csv(path, parse_dates=["datetime"])
        df = df.set_index("datetime").sort_index()
        out[pair] = df["close"]
    return out


# ============================================================
# VOLATILE フィルタ (GBP_JPY 専用) - contrarian_bt.py と同じ仕様
# ============================================================
def compute_volatile_mask(m15: pd.DataFrame, h1: pd.DataFrame) -> pd.Series:
    """GBP_JPY VOLATILE 判定マスクを M15 index で返す。

    contrarian_bt.py と同じロジック:
    - M15 YZ_vol > M15 ローリング 30%ile
    - H1 YZ_vol > 0.00175 (絶対閾値)
    """
    m15 = m15.copy()
    h1 = h1.copy()

    m15["yz_vol"] = calc_yang_zhang(m15, window=GBP_JPY_CONFIG["m15_yz_window"])
    h1["yz_vol"] = calc_yang_zhang(h1, window=GBP_JPY_CONFIG["h1_yz_window"])

    m15["yz_p30"] = m15["yz_vol"].rolling(GBP_JPY_CONFIG["m15_rolling_window_bars"]).quantile(0.30)

    h1_yz = h1[["yz_vol"]].rename(columns={"yz_vol": "h1_yz_vol"}).reset_index()
    m15_r = m15.reset_index()
    m15_r = pd.merge_asof(m15_r, h1_yz, on="datetime", direction="backward")
    m15_r = m15_r.set_index("datetime")

    H1_THR = GBP_JPY_CONFIG["h1_threshold_abs"]
    volatile = (m15_r["yz_vol"] > m15_r["yz_p30"]) & (m15_r["h1_yz_vol"] > H1_THR)
    return volatile


# ============================================================
# シグナル抽出 (signal_v2 ロジック + ペア別設定)
# ============================================================
def extract_signals_for_pair(pair: str, related_closes: dict) -> list:
    """1ペア分のシグナル + メタデータ抽出"""
    cfg = PAIR_CONFIG[pair]
    pip_size = cfg["pip_size"]
    spread_pips = cfg["spread_pips"]

    print(f"\n=== {pair} 抽出開始 ===")
    m15 = load_m15(cfg["csv_m15"])
    print(f"  M15 期間: {m15.index[0]} -> {m15.index[-1]} ({len(m15)} bars)")

    # ATR
    m15["atr"] = calc_atr(m15, ATR_PERIOD)

    # Breakout lookback (直前 20 本、最新除く)
    m15["lookback_high"] = m15["high"].shift(1).rolling(BREAKOUT_LOOKBACK).max()
    m15["lookback_low"] = m15["low"].shift(1).rolling(BREAKOUT_LOOKBACK).min()

    # VOLATILE フィルタ
    if cfg["use_volatile_filter"]:
        h1 = load_h1(cfg["csv_h1"])
        # M15 期間に合わせて H1 をスライス (バッファ込)
        h1 = h1.loc[m15.index[0] - pd.Timedelta(hours=200):m15.index[-1]].copy()
        volatile_mask = compute_volatile_mask(m15, h1)
        print(f"  VOLATILE バー: {int(volatile_mask.sum())} / {len(m15)} ({volatile_mask.mean()*100:.1f}%)")
    else:
        volatile_mask = pd.Series(True, index=m15.index)

    # signal 判定 (ブレイクアウト)
    m15["sig_long"] = volatile_mask & (m15["close"] > m15["lookback_high"]) & m15["atr"].notna()
    m15["sig_short"] = volatile_mask & (m15["close"] < m15["lookback_low"]) & m15["atr"].notna()

    n_sig_long = int(m15["sig_long"].sum())
    n_sig_short = int(m15["sig_short"].sum())
    print(f"  生シグナル: long={n_sig_long}, short={n_sig_short}, total={n_sig_long+n_sig_short}")

    # トレードシミュレーション (1ポジション制限、SL/TP first-touch)
    UNITS = 1000  # lot 0.01 換算
    rows = []
    in_position = None
    m15_r = m15.reset_index()

    for i in range(len(m15_r) - 1):
        row = m15_r.iloc[i]
        next_row = m15_r.iloc[i + 1]

        # 既存ポジションのチェック (SL/TP first-touch)
        if in_position is not None:
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
            else:
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
                gross_pips = (exit_price - in_position["entry"]) * dirn / pip_size
                pips = gross_pips - spread_pips
                in_position["exit_time"] = next_row["datetime"]
                in_position["exit_price"] = exit_price
                in_position["actual_pnl_pips_sl_tp"] = pips
                in_position["win_loss"] = "WIN" if pips > 0 else "LOSS"
                in_position["outcome"] = outcome
                rows.append(in_position)
                in_position = None

        # 新規シグナル (ポジションなしなら)
        if in_position is None and not pd.isna(row["atr"]):
            atr = row["atr"]
            if row["sig_long"] or row["sig_short"]:
                direction = "long" if row["sig_long"] else "short"
                entry = next_row["open"]
                if direction == "long":
                    sl = entry - atr * ATR_SL_MULT
                    tp = entry + atr * ATR_TP_MULT
                else:
                    sl = entry + atr * ATR_SL_MULT
                    tp = entry - atr * ATR_TP_MULT

                sl_pips_abs = abs(entry - sl) / pip_size
                tp_pips_abs = abs(entry - tp) / pip_size

                in_position = dict(
                    pair=pair,
                    signal_timestamp=row["datetime"],   # シグナル判定された M15 close 時刻
                    entry_time=next_row["datetime"],     # 実エントリー時刻 (次足 open)
                    direction=direction,
                    entry=entry,
                    sl=sl,
                    tp=tp,
                    atr=atr,
                    sl_pips=sl_pips_abs,
                    tp_pips=tp_pips_abs,
                    signal_idx=i,
                    entry_idx=i + 1,
                )

    print(f"  完結トレード: {len(rows)}")

    # ============================================================
    # 各トレードにメタデータ付与
    # ============================================================
    # 高速化のため m15 を index 化したものを別途持つ
    m15_indexed = m15.copy()

    enriched = []
    for idx, t in enumerate(rows):
        signal_ts = t["signal_timestamp"]  # シグナル時点 (LLM 入力の "現在")
        entry_ts = t["entry_time"]
        entry_price = t["entry"]

        # シグナル時点の過去 close (24h, 12h, 1h ago)
        # M15 だと 24h=96本前, 12h=48本前, 1h=4本前
        signal_idx = t["signal_idx"]
        close_24h_ago = float(m15_r.iloc[max(0, signal_idx - 96)]["close"]) if signal_idx >= 96 else None
        close_12h_ago = float(m15_r.iloc[max(0, signal_idx - 48)]["close"]) if signal_idx >= 48 else None
        close_1h_ago = float(m15_r.iloc[max(0, signal_idx - 4)]["close"]) if signal_idx >= 4 else None

        # 関連通貨 24h 変化率 (シグナル時刻基準)
        related_changes = {}
        for rp, rs in related_closes.items():
            # シグナル時刻以下で最新の close (lookahead 防止のため <= signal_ts)
            past = rs.loc[:signal_ts]
            if len(past) < 25:
                related_changes[rp] = None
                continue
            now_close = past.iloc[-1]
            # 24h 前 = 1日前 (H1 なので 24本前)
            ago_idx = -25 if len(past) >= 25 else -len(past)
            past_close = past.iloc[ago_idx]
            if past_close > 0:
                related_changes[rp] = float((now_close - past_close) / past_close * 100)
            else:
                related_changes[rp] = None

        # 時刻メタデータ (シグナル時刻ベース)
        # signal_ts は UTC (元データが UTC)
        # tz 情報を落として hour 抽出 (timezone-aware なら tz_convert("UTC") 後 tz_localize(None))
        ts_for_hour = signal_ts
        if hasattr(ts_for_hour, "tz") and ts_for_hour.tz is not None:
            ts_for_hour = ts_for_hour.tz_convert("UTC")
        hour_utc = ts_for_hour.hour
        day_of_week = ts_for_hour.dayofweek  # 0=Mon

        # 24h 後の実挙動 (BT 用、LLM には渡さない正解ラベル)
        # entry から +24h の高値・安値・終値
        entry_idx = t["entry_idx"]
        end_idx = min(entry_idx + 96, len(m15_r) - 1)  # 24h = 96 M15 bars
        window_24h = m15_r.iloc[entry_idx:end_idx + 1]
        if len(window_24h) > 0:
            high_after_24h = float(window_24h["high"].max())
            low_after_24h = float(window_24h["low"].min())
            close_24h_after = float(window_24h.iloc[-1]["close"])

            # 4h 後 close
            end_idx_4h = min(entry_idx + 16, len(m15_r) - 1)  # 4h = 16 M15 bars
            close_4h_after = float(m15_r.iloc[end_idx_4h]["close"])

            # 4h close pnl
            dirn = 1 if t["direction"] == "long" else -1
            pnl_4h_close = (close_4h_after - entry_price) * dirn / pip_size - spread_pips
            pnl_24h_close = (close_24h_after - entry_price) * dirn / pip_size - spread_pips
        else:
            high_after_24h = None
            low_after_24h = None
            close_24h_after = None
            pnl_4h_close = None
            pnl_24h_close = None

        # 保有時間 (first touch まで)
        if "exit_time" in t and t["exit_time"] is not None:
            holding_min = (t["exit_time"] - entry_ts).total_seconds() / 60
        else:
            holding_min = None

        signal_id = f"{pair}_{idx:05d}_{signal_ts.strftime('%Y%m%d_%H%M%S')}"

        enriched.append({
            "signal_id": signal_id,
            "pair": pair,
            "timestamp_utc": signal_ts.isoformat() if hasattr(signal_ts, "isoformat") else str(signal_ts),
            "direction": t["direction"],
            "entry_price": round(entry_price, 5),
            "sl_price": round(t["sl"], 5),
            "tp_price": round(t["tp"], 5),
            "sl_pips": round(t["sl_pips"], 2),
            "tp_pips": round(t["tp_pips"], 2),
            "atr": round(t["atr"], 6),
            "m15_close_24h_ago": round(close_24h_ago, 5) if close_24h_ago is not None else None,
            "m15_close_12h_ago": round(close_12h_ago, 5) if close_12h_ago is not None else None,
            "m15_close_1h_ago": round(close_1h_ago, 5) if close_1h_ago is not None else None,
            "related_eur_usd_24h_change_pct": round(related_changes.get("EUR_USD"), 4) if related_changes.get("EUR_USD") is not None else None,
            "related_usd_jpy_24h_change_pct": round(related_changes.get("USD_JPY"), 4) if related_changes.get("USD_JPY") is not None else None,
            "related_gbp_usd_24h_change_pct": round(related_changes.get("GBP_USD"), 4) if related_changes.get("GBP_USD") is not None else None,
            "day_of_week": day_of_week,
            "hour_utc": hour_utc,
            "is_tokyo_session": int(is_session(hour_utc, "tokyo")),
            "is_london_session": int(is_session(hour_utc, "london")),
            "is_ny_session": int(is_session(hour_utc, "ny")),
            "high_after_entry_24h": round(high_after_24h, 5) if high_after_24h is not None else None,
            "low_after_entry_24h": round(low_after_24h, 5) if low_after_24h is not None else None,
            "close_24h_after_entry": round(close_24h_after, 5) if close_24h_after is not None else None,
            "actual_pnl_pips_sl_tp_first_touch": round(t["actual_pnl_pips_sl_tp"], 2),
            "actual_pnl_pips_4h_close": round(pnl_4h_close, 2) if pnl_4h_close is not None else None,
            "actual_pnl_pips_24h_close": round(pnl_24h_close, 2) if pnl_24h_close is not None else None,
            "spread_assumed_pips": spread_pips,
            "win_loss_sl_tp": t["win_loss"],
            "holding_minutes_first_touch": round(holding_min, 1) if holding_min is not None else None,
        })

    return enriched


# ============================================================
# サマリ計算
# ============================================================
def summarize(rows: list, label: str) -> dict:
    if not rows:
        return {"label": label, "n": 0}
    df = pd.DataFrame(rows)
    pnl = df["actual_pnl_pips_sl_tp_first_touch"]
    wins = pnl[pnl > 0]
    losses = pnl[pnl <= 0]
    n_win = len(wins)
    n_loss = len(losses)
    gross_win = wins.sum()
    gross_loss = -losses.sum() if n_loss else 0.0001
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")

    return {
        "label": label,
        "n": len(df),
        "win_rate_pct": round(n_win / len(df) * 100, 2),
        "avg_win_pips": round(wins.mean(), 2) if n_win else 0,
        "avg_loss_pips": round(losses.mean(), 2) if n_loss else 0,
        "total_pips": round(pnl.sum(), 2),
        "PF": round(pf, 3),
        "n_wins": n_win,
        "n_losses": n_loss,
    }


# ============================================================
# メイン
# ============================================================
def main():
    print("===== 第2サイクル signal_v2 過去シグナル抽出 =====\n")

    print("関連通貨 H1 close 読み込み中...")
    related_closes = load_related_close_h1()
    for k, v in related_closes.items():
        print(f"  {k}: {len(v)} rows ({v.index[0]} -> {v.index[-1]})")

    all_rows = []
    summaries = []
    for pair in ["GBP_JPY", "USD_JPY", "EUR_USD"]:
        rows = extract_signals_for_pair(pair, related_closes)
        all_rows.extend(rows)
        summaries.append(summarize(rows, pair))

    # CSV 出力
    out_csv = ROOT / "data" / "signal_v2_historical_signals.csv"
    if all_rows:
        keys = list(all_rows[0].keys())
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\nCSV 出力: {out_csv} ({len(all_rows)} rows)")

    # サマリ表示
    print("\n========== サマリ ==========")
    for s in summaries:
        print(f"\n[{s['label']}]")
        for k, v in s.items():
            if k != "label":
                print(f"  {k}: {v}")

    # 全体
    print("\n[ALL]")
    overall = summarize(all_rows, "ALL")
    for k, v in overall.items():
        if k != "label":
            print(f"  {k}: {v}")

    # メタデータ欠損度
    print("\n========== メタデータ完全度 ==========")
    df = pd.DataFrame(all_rows)
    for col in ["m15_close_24h_ago", "m15_close_12h_ago", "m15_close_1h_ago",
                "related_eur_usd_24h_change_pct", "related_usd_jpy_24h_change_pct",
                "related_gbp_usd_24h_change_pct"]:
        missing = df[col].isna().sum()
        print(f"  {col}: missing={missing}/{len(df)} ({missing/len(df)*100:.1f}%)")


if __name__ == "__main__":
    main()
