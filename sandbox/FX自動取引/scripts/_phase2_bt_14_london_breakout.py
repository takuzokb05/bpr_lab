"""Phase 2 BT: 候補 #14 London Breakout Adaptive

戦略概要:
- アジアセッション (UTC 0:00-7:59) のレンジを記録
- ロンドン開場直後 (UTC 8:00-9:30) のブレイクで順張りエントリー
- フィルタ: MACD (12,26,9) histogram 同方向 + RSI(14) 中央線同方向
- ATR(14) ベースの SL/TP (SL = ATR×1.5、TP = ATR×3.0)
- NY セッションクローズ (UTC 21:00) で強制 close
- ニュースフィルタ: NFP 第1金曜 UTC13:30 / FOMC / BoE / ECB の直前1時間 〜 1時間後を回避
- 月次 Optuna 最適化 (G0-B 自己改善メカニズム)
- Walk-Forward: 6ヶ月学習 / 1ヶ月運用 windows

ペア: GBP_USD (主)、EUR_USD、USD_JPY
データ: H1 過去5年 (2021-05 〜 2026-05)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# ----------------------------------------
# 共通設定
# ----------------------------------------
PAIR_CONFIG = {
    "GBP_USD": {"csv": "mt5_GBP_USD_H1_5y.csv", "pip": 0.0001, "spread_pips": 1.5, "slippage_pips": 2.0, "jpy_quote": False},
    "EUR_USD": {"csv": "mt5_EUR_USD_H1_5y.csv", "pip": 0.0001, "spread_pips": 1.0, "slippage_pips": 2.0, "jpy_quote": False},
    "USD_JPY": {"csv": "mt5_USD_JPY_H1_5y.csv", "pip": 0.01, "spread_pips": 1.0, "slippage_pips": 2.0, "jpy_quote": True},
}

UNITS = 1000  # lot 0.01 相当
USD_JPY_FIXED = 150.0  # USD→JPY 換算固定値 (簡易)
INITIAL_EQUITY = 1_000_000.0  # 100万円口座

# デフォルトパラメータ (Optuna 最適化対象)
DEFAULT_PARAMS = {
    "asia_start_h": 0,      # アジアレンジ開始 UTC hour
    "asia_end_h": 8,        # アジアレンジ終了 (排他)
    "break_start_h": 8,     # ブレイク判定開始
    "break_end_h": 10,      # ブレイク判定終了 (排他)
    "force_close_h": 21,    # 強制 close hour (NY セッション後半)
    "buffer_pips": 2.0,     # ブレイクバッファ
    "atr_period": 14,
    "atr_sl_mult": 1.5,
    "atr_tp_mult": 3.0,
    "rsi_period": 14,
    "rsi_threshold": 50.0,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
}


# ----------------------------------------
# インジケータ
# ----------------------------------------
def calc_atr(df: pd.DataFrame, period: int) -> pd.Series:
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


def calc_rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(span=period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(span=period, adjust=False).mean()
    rs = gain / (loss + 1e-12)
    return 100 - (100 / (1 + rs))


def calc_macd(close: pd.Series, fast: int, slow: int, signal: int) -> pd.Series:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    return hist


# ----------------------------------------
# ニュースフィルタ
# ----------------------------------------
def is_news_blackout(dt: pd.Timestamp) -> bool:
    """高インパクトイベント前後 1時間を回避。
    - NFP: 毎月第1金曜 UTC 13:30 → 12:30-14:30 を回避
    - FOMC: 第3水曜 UTC 18:00 → 17:00-19:00 (近似)
    - ECB: 第1木曜 UTC 12:45 → 11:45-13:45
    - BoE: 第1木曜 UTC 12:00 → 11:00-13:00
    完全な経済カレンダー連携でないが、保守的な近似。
    """
    if dt.tzinfo is None:
        dt = dt.tz_localize("UTC")
    weekday = dt.weekday()  # 月=0
    day = dt.day
    hour = dt.hour
    # 第1金曜 NFP (1-7日の金曜)
    if weekday == 4 and 1 <= day <= 7:
        if 12 <= hour <= 14:
            return True
    # 第1木曜 ECB/BoE
    if weekday == 3 and 1 <= day <= 7:
        if 11 <= hour <= 14:
            return True
    # 第3水曜 FOMC (15-21日の水曜)
    if weekday == 2 and 15 <= day <= 21:
        if 17 <= hour <= 19:
            return True
    return False


# ----------------------------------------
# データロード
# ----------------------------------------
def load_data(pair: str) -> pd.DataFrame:
    cfg = PAIR_CONFIG[pair]
    df = pd.read_csv(DATA / cfg["csv"], parse_dates=["datetime"])
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df = df.set_index("datetime").sort_index()
    df = df[df.index >= "2021-05-07"]
    return df


def prepare_features(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    df = df.copy()
    df["atr"] = calc_atr(df, params["atr_period"])
    df["rsi"] = calc_rsi(df["close"], params["rsi_period"])
    df["macd_hist"] = calc_macd(df["close"], params["macd_fast"], params["macd_slow"], params["macd_signal"])
    df["hour"] = df.index.hour
    df["date"] = df.index.date
    return df


# ----------------------------------------
# BT コア
# ----------------------------------------
@dataclass
class Trade:
    pair: str
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str  # long/short
    entry_price: float
    exit_price: float
    sl: float
    tp: float
    asia_high: float
    asia_low: float
    range_size: float
    atr: float
    pips: float
    pnl_jpy: float
    outcome: str  # TP/SL/FORCE_CLOSE
    holding_bars: int


def run_bt_single_pair(pair: str, df_full: pd.DataFrame, params: dict,
                       date_start: Optional[pd.Timestamp] = None,
                       date_end: Optional[pd.Timestamp] = None,
                       news_filter: bool = True) -> list[Trade]:
    """単一ペア・単一パラメータでのバックテスト実行"""
    cfg = PAIR_CONFIG[pair]
    pip = cfg["pip"]
    spread = cfg["spread_pips"] * pip
    slip = cfg["slippage_pips"] * pip

    df = df_full
    if date_start is not None:
        df = df[df.index >= date_start]
    if date_end is not None:
        df = df[df.index < date_end]
    if len(df) < 50:
        return []

    df = prepare_features(df, params)

    trades: list[Trade] = []
    # 日ごとに処理
    for date, day_df in df.groupby(df.index.date):
        if len(day_df) < 10:
            continue
        # アジアレンジ (asia_start_h ~ asia_end_h-1)
        asia = day_df[(day_df["hour"] >= params["asia_start_h"]) & (day_df["hour"] < params["asia_end_h"])]
        if len(asia) < 3:
            continue
        asia_high = asia["high"].max()
        asia_low = asia["low"].min()
        range_size = asia_high - asia_low
        # range が極端に小さい/大きい場合スキップ (極小 = ノイズ、極大 = 既にトレンド)
        atr_at_break_start = asia["atr"].iloc[-1]
        if pd.isna(atr_at_break_start) or atr_at_break_start <= 0:
            continue
        if range_size < 0.3 * atr_at_break_start or range_size > 5.0 * atr_at_break_start:
            continue

        # ブレイク判定窓 (break_start_h ~ break_end_h-1)
        break_window = day_df[(day_df["hour"] >= params["break_start_h"]) & (day_df["hour"] < params["break_end_h"])]
        if len(break_window) == 0:
            continue

        buf = params["buffer_pips"] * pip
        position: Optional[Trade] = None

        for ts, row in break_window.iterrows():
            if news_filter and is_news_blackout(ts):
                continue
            if pd.isna(row["atr"]) or pd.isna(row["macd_hist"]) or pd.isna(row["rsi"]):
                continue

            high = row["high"]
            low = row["low"]
            close = row["close"]
            atr_v = row["atr"]

            # long ブレイク
            if high > asia_high + buf:
                if row["macd_hist"] > 0 and row["rsi"] > params["rsi_threshold"]:
                    entry = asia_high + buf + slip  # スリッページ込みエントリー
                    sl = entry - params["atr_sl_mult"] * atr_v
                    tp = entry + params["atr_tp_mult"] * atr_v
                    position = Trade(
                        pair=pair, entry_time=ts, exit_time=ts, direction="long",
                        entry_price=entry, exit_price=entry, sl=sl, tp=tp,
                        asia_high=asia_high, asia_low=asia_low, range_size=range_size,
                        atr=atr_v, pips=0, pnl_jpy=0, outcome="OPEN", holding_bars=0,
                    )
                    break
            # short ブレイク
            elif low < asia_low - buf:
                if row["macd_hist"] < 0 and row["rsi"] < params["rsi_threshold"]:
                    entry = asia_low - buf - slip
                    sl = entry + params["atr_sl_mult"] * atr_v
                    tp = entry - params["atr_tp_mult"] * atr_v
                    position = Trade(
                        pair=pair, entry_time=ts, exit_time=ts, direction="short",
                        entry_price=entry, exit_price=entry, sl=sl, tp=tp,
                        asia_high=asia_high, asia_low=asia_low, range_size=range_size,
                        atr=atr_v, pips=0, pnl_jpy=0, outcome="OPEN", holding_bars=0,
                    )
                    break

        if position is None:
            continue

        # 強制 close まで保有
        manage_window = day_df[(day_df.index > position.entry_time) & (day_df["hour"] < params["force_close_h"])]
        closed = False
        for ts, row in manage_window.iterrows():
            hi, lo = row["high"], row["low"]
            position.holding_bars += 1
            if position.direction == "long":
                if lo <= position.sl:
                    position.exit_time = ts
                    position.exit_price = position.sl
                    position.outcome = "SL"
                    closed = True
                    break
                if hi >= position.tp:
                    position.exit_time = ts
                    position.exit_price = position.tp
                    position.outcome = "TP"
                    closed = True
                    break
            else:
                if hi >= position.sl:
                    position.exit_time = ts
                    position.exit_price = position.sl
                    position.outcome = "SL"
                    closed = True
                    break
                if lo <= position.tp:
                    position.exit_time = ts
                    position.exit_price = position.tp
                    position.outcome = "TP"
                    closed = True
                    break

        if not closed:
            # 強制 close (NY セッション後半)
            close_window = day_df[(day_df["hour"] >= params["force_close_h"])]
            if len(close_window) > 0:
                cl_row = close_window.iloc[0]
                position.exit_time = close_window.index[0]
                position.exit_price = cl_row["open"]
                position.outcome = "FORCE_CLOSE"
                position.holding_bars += 1
            else:
                # その日のデータが無ければ最後の bar で close
                last_row = day_df.iloc[-1]
                position.exit_time = day_df.index[-1]
                position.exit_price = last_row["close"]
                position.outcome = "EOD_CLOSE"

        # PnL 計算 (スプレッドはエントリーで往復片側、エグジットでスリッページ)
        dirn = 1 if position.direction == "long" else -1
        gross_diff = (position.exit_price - position.entry_price) * dirn
        # コスト: スプレッド (往復) + 決済スリッページ
        cost = spread + slip
        net_diff = gross_diff - cost
        position.pips = net_diff / pip
        if cfg["jpy_quote"]:
            position.pnl_jpy = net_diff * UNITS
        else:
            position.pnl_jpy = net_diff * UNITS * USD_JPY_FIXED
        trades.append(position)

    return trades


# ----------------------------------------
# 統計
# ----------------------------------------
def stats_from_trades(trades: list[Trade]) -> dict:
    if not trades:
        return {"n": 0, "pf": 0.0, "win_rate": 0.0, "total_pnl": 0.0, "avg_pnl": 0.0,
                "sharpe": 0.0, "sortino": 0.0, "max_dd": 0.0, "max_dd_pct": 0.0,
                "longest_loss_streak": 0, "longest_win_streak": 0, "expectancy": 0.0}
    pnl = np.array([t.pnl_jpy for t in trades])
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else float("inf")
    win_rate = len(wins) / len(pnl) * 100
    total = pnl.sum()
    avg = pnl.mean()
    # Sharpe (年率): 1日 1取引以下、年250営業日換算
    daily_std = pnl.std(ddof=1) if len(pnl) > 1 else 0
    if daily_std > 0:
        sharpe = (avg / daily_std) * np.sqrt(250)
    else:
        sharpe = 0.0
    downside = pnl[pnl < 0]
    downside_std = downside.std(ddof=1) if len(downside) > 1 else 0
    if downside_std > 0:
        sortino = (avg / downside_std) * np.sqrt(250)
    else:
        sortino = 0.0
    # MaxDD (equity curve ベース)
    equity = INITIAL_EQUITY + np.cumsum(pnl)
    peak = np.maximum.accumulate(equity)
    dd = peak - equity
    max_dd = dd.max()
    max_dd_pct = (dd / peak * 100).max()
    # 連勝/連敗
    streak = 0
    longest_win = 0
    longest_loss = 0
    last_sign = 0
    for p in pnl:
        sign = 1 if p > 0 else (-1 if p < 0 else 0)
        if sign == last_sign and sign != 0:
            streak += 1
        else:
            streak = 1 if sign != 0 else 0
        if sign > 0:
            longest_win = max(longest_win, streak)
        elif sign < 0:
            longest_loss = max(longest_loss, streak)
        last_sign = sign
    # 期待値 (1取引あたり)
    expectancy = avg
    return {
        "n": len(pnl),
        "pf": float(pf),
        "win_rate": float(win_rate),
        "total_pnl": float(total),
        "avg_pnl": float(avg),
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "max_dd": float(max_dd),
        "max_dd_pct": float(max_dd_pct),
        "longest_loss_streak": int(longest_loss),
        "longest_win_streak": int(longest_win),
        "expectancy": float(expectancy),
    }


def deflated_sharpe_ratio(sr: float, n: int, n_trials: int = 1, skew: float = 0, kurt: float = 3) -> float:
    """Bailey & Lopez de Prado (2014) の Deflated Sharpe Ratio (近似)。
    n_trials = Optuna 試行回数を多重検定補正で考慮。
    """
    if n < 30 or sr == 0:
        return 0.0
    # SR^2 standard error
    var_sr = (1 - skew * sr + (kurt - 1) / 4 * sr ** 2) / (n - 1)
    sr_std = np.sqrt(max(var_sr, 1e-10))
    # 多重検定補正 (Bonferroni 風: log(n_trials) の expected max)
    # E[max SR] ≈ sqrt(2 log n_trials) (Bailey 簡易近似)
    if n_trials > 1:
        em_sr = sr_std * np.sqrt(2 * np.log(n_trials))
    else:
        em_sr = 0
    # Deflated SR (PSR with multiple testing) — z-score
    dsr_z = (sr - em_sr) / sr_std
    # 標準正規 CDF
    from math import erf
    return 0.5 * (1 + erf(dsr_z / np.sqrt(2)))


# ----------------------------------------
# Walk-Forward Analysis
# ----------------------------------------
def walk_forward(pair: str, df: pd.DataFrame, params: dict,
                 train_months: int = 6, test_months: int = 1) -> pd.DataFrame:
    """Walk-Forward Analysis: train_months で学習、test_months で運用、step=test_months"""
    start = df.index.min()
    end = df.index.max()

    results = []
    cur = start + pd.DateOffset(months=train_months)
    while cur + pd.DateOffset(months=test_months) <= end:
        test_start = cur
        test_end = test_start + pd.DateOffset(months=test_months)
        trades = run_bt_single_pair(pair, df, params, test_start, test_end)
        st = stats_from_trades(trades)
        results.append({
            "window_start": test_start, "window_end": test_end,
            **{k: v for k, v in st.items() if k in ["n", "pf", "win_rate", "total_pnl", "sharpe"]}
        })
        cur = cur + pd.DateOffset(months=test_months)
    return pd.DataFrame(results)


# ----------------------------------------
# Optuna 月次最適化
# ----------------------------------------
def optuna_optimize(pair: str, df: pd.DataFrame, train_start: pd.Timestamp, train_end: pd.Timestamp,
                    n_trials: int = 30) -> tuple[dict, float]:
    """学習期間でパラメータを Optuna 最適化、(best_params, best_pf) を返す"""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        p = DEFAULT_PARAMS.copy()
        p["asia_end_h"] = trial.suggest_int("asia_end_h", 6, 9)
        p["break_start_h"] = p["asia_end_h"]
        p["break_end_h"] = trial.suggest_int("break_end_h", p["asia_end_h"] + 1, p["asia_end_h"] + 3)
        p["buffer_pips"] = trial.suggest_float("buffer_pips", 1.0, 5.0)
        p["atr_sl_mult"] = trial.suggest_float("atr_sl_mult", 1.0, 2.5)
        p["atr_tp_mult"] = trial.suggest_float("atr_tp_mult", 1.5, 4.0)
        p["rsi_threshold"] = trial.suggest_float("rsi_threshold", 45.0, 55.0)

        trades = run_bt_single_pair(pair, df, p, train_start, train_end)
        if len(trades) < 5:
            return -10.0
        st = stats_from_trades(trades)
        if st["pf"] == float("inf"):
            return 5.0
        # 罰則: trades 少なすぎは PF だけ高くても信用しない
        if st["n"] < 10:
            return st["pf"] * 0.5
        return st["pf"]

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    best_p = DEFAULT_PARAMS.copy()
    best_p.update(study.best_params)
    if "asia_end_h" in study.best_params:
        best_p["break_start_h"] = best_p["asia_end_h"]
    return best_p, study.best_value


def monthly_optuna_walk(pair: str, df: pd.DataFrame, train_months: int = 12,
                        n_trials: int = 20) -> tuple[list[Trade], pd.DataFrame]:
    """月次 Optuna 再最適化を walk-forward で適用。
    OOS trades の蓄積と Optuna 履歴を返す。
    """
    start = df.index.min()
    end = df.index.max()
    cur = start + pd.DateOffset(months=train_months)

    all_oos_trades: list[Trade] = []
    history = []
    prev_params: Optional[dict] = None

    while cur + pd.DateOffset(months=1) <= end:
        train_start = cur - pd.DateOffset(months=train_months)
        train_end = cur
        test_start = cur
        test_end = cur + pd.DateOffset(months=1)

        try:
            best_p, best_pf_train = optuna_optimize(pair, df, train_start, train_end, n_trials=n_trials)
        except Exception as e:
            best_p = prev_params if prev_params else DEFAULT_PARAMS.copy()
            best_pf_train = 0.0

        # フォールバック: 新パラメータの train PF < 直前 train PF × 0.8 → 直前を採用
        if prev_params is not None and "_prev_train_pf" in prev_params:
            if best_pf_train < prev_params["_prev_train_pf"] * 0.8:
                used_params = {k: v for k, v in prev_params.items() if not k.startswith("_")}
                fallback = True
            else:
                used_params = best_p
                fallback = False
        else:
            used_params = best_p
            fallback = False

        oos_trades = run_bt_single_pair(pair, df, used_params, test_start, test_end)
        oos_st = stats_from_trades(oos_trades)

        history.append({
            "month_start": test_start,
            "train_start": train_start,
            "train_pf": best_pf_train,
            "oos_n": oos_st["n"],
            "oos_pf": oos_st["pf"],
            "oos_total_pnl": oos_st["total_pnl"],
            "fallback": fallback,
            **{f"p_{k}": v for k, v in used_params.items()},
        })

        all_oos_trades.extend(oos_trades)
        prev_params = used_params.copy()
        prev_params["_prev_train_pf"] = best_pf_train

        cur = cur + pd.DateOffset(months=1)

    return all_oos_trades, pd.DataFrame(history)


# ----------------------------------------
# Black Swan ストレステスト
# ----------------------------------------
BLACK_SWAN_EVENTS = [
    # (名前, 開始, 終了)
    ("Brexit_2016", "2016-06-23", "2016-06-30"),  # データ範囲外、参考
    ("COVID_2020_03", "2020-03-09", "2020-03-31"),  # データ範囲外
    ("USD_JPY_intervention_2024_07", "2024-07-08", "2024-07-15"),
    ("USD_JPY_intervention_2024_08", "2024-08-02", "2024-08-09"),
    ("Carry_unwind_2024_08", "2024-08-02", "2024-08-09"),
]


def stress_test(pair: str, df: pd.DataFrame, params: dict) -> list[dict]:
    results = []
    for name, start, end in BLACK_SWAN_EVENTS:
        s = pd.Timestamp(start, tz="UTC")
        e = pd.Timestamp(end, tz="UTC")
        # データ範囲内のみ
        if s < df.index.min() or e > df.index.max():
            results.append({"event": name, "pair": pair, "n_trades": 0, "total_pnl": 0.0,
                            "max_loss": 0.0, "in_range": False})
            continue
        trades = run_bt_single_pair(pair, df, params, s, e)
        st = stats_from_trades(trades)
        max_loss = min([t.pnl_jpy for t in trades], default=0.0)
        results.append({
            "event": name, "pair": pair, "n_trades": st["n"], "total_pnl": st["total_pnl"],
            "max_loss": float(max_loss), "win_rate": st["win_rate"], "in_range": True,
        })
    return results


# ----------------------------------------
# パラメータ感度
# ----------------------------------------
def sensitivity_analysis(pair: str, df: pd.DataFrame, base_params: dict) -> pd.DataFrame:
    """主要パラメータを ±20% 変動させ PF/Sharpe の安定性を評価"""
    results = []
    targets = ["buffer_pips", "atr_sl_mult", "atr_tp_mult", "rsi_threshold"]
    for k in targets:
        for delta_pct in [-20, -10, 0, 10, 20]:
            p = base_params.copy()
            base_v = base_params[k]
            p[k] = base_v * (1 + delta_pct / 100)
            trades = run_bt_single_pair(pair, df, p)
            st = stats_from_trades(trades)
            results.append({
                "param": k, "delta_pct": delta_pct, "value": p[k],
                "n": st["n"], "pf": st["pf"], "sharpe": st["sharpe"],
                "total_pnl": st["total_pnl"], "max_dd_pct": st["max_dd_pct"],
            })
    return pd.DataFrame(results)


# ----------------------------------------
# キルスイッチ / リスク管理シミュレーション
# ----------------------------------------
def simulate_risk_limits(trades: list[Trade]) -> dict:
    """日次 -1.5% 警告 / -3% 半量 / -5% 停止、月次 -10% 停止 のシミュレーション"""
    if not trades:
        return {"daily_warn_days": 0, "daily_halt_days": 0, "monthly_halt_months": 0,
                "killswitch_triggered": False}
    df = pd.DataFrame([{
        "date": t.entry_time.date(),
        "month": pd.Timestamp(t.entry_time).to_period("M"),
        "pnl": t.pnl_jpy
    } for t in trades])
    daily = df.groupby("date")["pnl"].sum()
    daily_pct = daily / INITIAL_EQUITY * 100
    daily_warn = (daily_pct <= -1.5).sum()
    daily_half = (daily_pct <= -3.0).sum()
    daily_halt = (daily_pct <= -5.0).sum()
    monthly = df.groupby("month")["pnl"].sum()
    monthly_pct = monthly / INITIAL_EQUITY * 100
    monthly_halt = (monthly_pct <= -10.0).sum()
    return {
        "daily_warn_days": int(daily_warn),
        "daily_half_days": int(daily_half),
        "daily_halt_days": int(daily_halt),
        "monthly_halt_months": int(monthly_halt),
        "killswitch_triggered": bool(daily_halt > 0 or monthly_halt > 0),
        "worst_day_pct": float(daily_pct.min()),
        "worst_month_pct": float(monthly_pct.min()),
    }


# ----------------------------------------
# main
# ----------------------------------------
def main():
    pairs = ["GBP_USD", "EUR_USD", "USD_JPY"]
    all_trades = []
    all_monthly_history = []
    all_stress = []
    pair_summary = {}

    print("=" * 60)
    print("Phase 2 BT #14: London Breakout Adaptive")
    print("=" * 60)

    for pair in pairs:
        print(f"\n[{pair}] Loading data ...")
        df = load_data(pair)
        print(f"  bars: {len(df)}, span: {df.index.min()} → {df.index.max()}")

        # 1. ベースライン BT (全期間、デフォルトパラメータ)
        print(f"[{pair}] Baseline BT (default params) ...")
        baseline_trades = run_bt_single_pair(pair, df, DEFAULT_PARAMS)
        baseline_st = stats_from_trades(baseline_trades)
        print(f"  baseline: n={baseline_st['n']} PF={baseline_st['pf']:.3f} "
              f"WR={baseline_st['win_rate']:.1f}% Sharpe={baseline_st['sharpe']:.2f} "
              f"total={baseline_st['total_pnl']:.0f} JPY")

        # 2. IS/OOS split (70/30)
        split_date = df.index.min() + (df.index.max() - df.index.min()) * 0.7
        is_trades = run_bt_single_pair(pair, df, DEFAULT_PARAMS, df.index.min(), split_date)
        oos_trades = run_bt_single_pair(pair, df, DEFAULT_PARAMS, split_date, df.index.max())
        is_st = stats_from_trades(is_trades)
        oos_st = stats_from_trades(oos_trades)
        print(f"  IS:  n={is_st['n']} PF={is_st['pf']:.3f}")
        print(f"  OOS: n={oos_st['n']} PF={oos_st['pf']:.3f}")

        # 3. Walk-Forward (固定パラメータ)
        print(f"[{pair}] Walk-Forward (6mo train / 1mo test) ...")
        wf = walk_forward(pair, df, DEFAULT_PARAMS, train_months=6, test_months=1)
        wf["pair"] = pair
        windows_ok = (wf["pf"] >= 1.0).sum()
        print(f"  WF windows: {len(wf)}, PF >=1.0: {windows_ok}/{len(wf)}")

        # 4. 月次 Optuna 最適化 walk
        print(f"[{pair}] Monthly Optuna walk-forward (n_trials=15) ...")
        opt_oos_trades, monthly_hist = monthly_optuna_walk(pair, df, train_months=12, n_trials=15)
        opt_st = stats_from_trades(opt_oos_trades)
        print(f"  Optuna OOS: n={opt_st['n']} PF={opt_st['pf']:.3f} "
              f"Sharpe={opt_st['sharpe']:.2f} MaxDD={opt_st['max_dd_pct']:.2f}%")
        monthly_hist["pair"] = pair
        all_monthly_history.append(monthly_hist)

        # 5. パラメータ感度
        print(f"[{pair}] Sensitivity analysis ...")
        sens = sensitivity_analysis(pair, df, DEFAULT_PARAMS)
        sens["pair"] = pair

        # 6. Black Swan
        print(f"[{pair}] Stress test ...")
        stress = stress_test(pair, df, DEFAULT_PARAMS)
        all_stress.extend(stress)

        # 7. Deflated Sharpe (Optuna OOS ベース、n_trials は全Optuna試行数)
        n_trials_total = len(monthly_hist) * 15
        dsr = deflated_sharpe_ratio(opt_st["sharpe"], opt_st["n"], n_trials=max(n_trials_total, 1))

        # 8. リスク管理シミュレーション
        risk_sim = simulate_risk_limits(opt_oos_trades)

        pair_summary[pair] = {
            "baseline": baseline_st,
            "is": is_st,
            "oos": oos_st,
            "optuna_oos": opt_st,
            "wf_windows_total": len(wf),
            "wf_windows_pf_ge_1": int(windows_ok),
            "deflated_sharpe": float(dsr),
            "risk_sim": risk_sim,
            "sensitivity": sens.to_dict("records"),
        }

        # トレード詳細
        for t in baseline_trades:
            all_trades.append({
                "pair": pair, "type": "baseline_full",
                **{k: v for k, v in asdict(t).items() if k != "pair"}
            })
        for t in opt_oos_trades:
            all_trades.append({
                "pair": pair, "type": "optuna_oos",
                **{k: v for k, v in asdict(t).items() if k != "pair"}
            })

    # ----------- 集約 -----------
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for pair, s in pair_summary.items():
        print(f"\n[{pair}]")
        print(f"  Baseline (5y): n={s['baseline']['n']} PF={s['baseline']['pf']:.3f} "
              f"Sharpe={s['baseline']['sharpe']:.2f} MaxDD={s['baseline']['max_dd_pct']:.2f}%")
        print(f"  Optuna OOS:    n={s['optuna_oos']['n']} PF={s['optuna_oos']['pf']:.3f} "
              f"Sharpe={s['optuna_oos']['sharpe']:.2f} Sortino={s['optuna_oos']['sortino']:.2f}")
        print(f"  WF windows PF>=1.0: {s['wf_windows_pf_ge_1']}/{s['wf_windows_total']}")
        print(f"  DSR (multi-test): {s['deflated_sharpe']:.3f}")
        print(f"  Worst day/month: {s['risk_sim']['worst_day_pct']:.2f}% / "
              f"{s['risk_sim']['worst_month_pct']:.2f}%")

    # ----------- CSV 出力 -----------
    out_trades = DATA / "_phase2_bt_14_london_trades.csv"
    pd.DataFrame(all_trades).to_csv(out_trades, index=False)
    print(f"\nTrades CSV: {out_trades}")

    # 月次集計
    monthly_rows = []
    for pair, s in pair_summary.items():
        # baseline 全期間のトレードから月次集計
        df_t = pd.DataFrame([{"month": pd.Timestamp(t["entry_time"]).to_period("M"),
                              "pair": t["pair"], "pnl": t["pnl_jpy"], "outcome": t["outcome"]}
                             for t in all_trades if t["pair"] == pair and t["type"] == "optuna_oos"])
        if len(df_t):
            mg = df_t.groupby("month").agg(n=("pnl", "count"),
                                            total_pnl=("pnl", "sum"),
                                            wins=("pnl", lambda x: (x > 0).sum()),
                                            losses=("pnl", lambda x: (x < 0).sum())).reset_index()
            mg["pair"] = pair
            mg["win_rate"] = mg["wins"] / mg["n"] * 100
            monthly_rows.append(mg)
    if monthly_rows:
        pd.concat(monthly_rows).to_csv(DATA / "_phase2_bt_14_london_monthly.csv", index=False)
        print(f"Monthly CSV: {DATA / '_phase2_bt_14_london_monthly.csv'}")

    pd.DataFrame(all_stress).to_csv(DATA / "_phase2_bt_14_london_stress.csv", index=False)
    print(f"Stress CSV: {DATA / '_phase2_bt_14_london_stress.csv'}")

    pd.concat(all_monthly_history).to_csv(DATA / "_phase2_bt_14_london_optuna.csv", index=False)
    print(f"Optuna history CSV: {DATA / '_phase2_bt_14_london_optuna.csv'}")

    # ----------- 結果を JSON でも残す (レポート生成用) -----------
    import json
    summary_path = DATA / "_phase2_bt_14_london_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({pair: {
            "baseline": s["baseline"],
            "is": s["is"],
            "oos": s["oos"],
            "optuna_oos": s["optuna_oos"],
            "wf_windows_total": s["wf_windows_total"],
            "wf_windows_pf_ge_1": s["wf_windows_pf_ge_1"],
            "deflated_sharpe": s["deflated_sharpe"],
            "risk_sim": s["risk_sim"],
        } for pair, s in pair_summary.items()}, f, indent=2, default=str)
    print(f"Summary JSON: {summary_path}")

    return pair_summary, all_trades, all_stress


if __name__ == "__main__":
    main()
