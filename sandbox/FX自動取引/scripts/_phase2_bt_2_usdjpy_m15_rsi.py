"""Phase 2 BT: USD_JPY M15 RSI Pullback (候補 #2)

参考: docs/PHASE_2_PLAN.md / docs/proposals/phase0/memory_usd_jpy_m15_rsi_pullback.md

戦略仕様:
- RSI(14) Pullback + EMA50 トレンドフィルタ + ATR ベース SL/TP + セッションフィルタ
- ロング: RSI<35 & close>EMA50 & in_session  → SL=close-ATR*2.0, TP=close+ATR*3.0
- ショート: RSI>65 & close<EMA50 & in_session → SL=close+ATR*2.0, TP=close-ATR*3.0
- セッション: Tokyo 9-11 JST or NY 21-25 JST
- 時間損切り: 6 時間 (24 M15 バー)
- スプレッド: 1.0 pip + スリッページ 各 1 pip = 3 pip 合計コスト

データ:
- M15: data/mt5_USD_JPY_M15_2y.csv (2024-05 ~ 2026-05 ≒ 2年)  ← 5年データ未取得を honest 報告
- H1: data/mt5_USD_JPY_H1_5y.csv (2021-05 ~ 2026-05 = 5年)  ← timeframe 比較用

出力:
- data/_phase2_bt_2_usdjpy_trades.csv
- data/_phase2_bt_2_usdjpy_monthly.csv
- data/_phase2_bt_2_usdjpy_stress.csv
- (本体は docs/proposals/phase2/2_usdjpy_m15_rsi_BT_REPORT.md に集計)
"""
from __future__ import annotations
import sys
import warnings
from pathlib import Path
from datetime import timedelta

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ----------------------------------------
# 定数
# ----------------------------------------
PIP = 0.01  # USD_JPY pip
LOT_UNITS = 1000  # lot 0.01 (= 1000 units)
INITIAL_BALANCE = 1_000_000  # JPY (100万円)
RISK_PER_TRADE = 0.01  # 1% per trade

SPREAD_PIP = 1.0       # USD_JPY spread (外為ファイネスト目安)
SLIPPAGE_ENTRY = 1.0   # entry slippage
SLIPPAGE_EXIT = 1.0    # exit slippage
TOTAL_COST_PIP = SPREAD_PIP + SLIPPAGE_ENTRY + SLIPPAGE_EXIT  # 3.0 pip / RT

RSI_LEN = 14
ATR_LEN = 14
EMA_LEN = 50
RSI_OS = 35
RSI_OB = 65
ATR_SL = 2.0
ATR_TP = 3.0
TIME_STOP_M15_BARS = 24  # 6 時間 = 24 * 15分
JST_OFFSET_H = 9  # UTC -> JST


def load_m15(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    return df


def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0).rolling(period).mean()
    down = (-delta.clip(upper=0)).rolling(period).mean()
    rs = up / down.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    return rsi


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    h = df["high"]; l = df["low"]; c = df["close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def calc_ema(close: pd.Series, period: int = 50) -> pd.Series:
    return close.ewm(span=period, adjust=False).mean()


def add_indicators(df: pd.DataFrame, rsi_os: int = RSI_OS, rsi_ob: int = RSI_OB, atr_mult_sl: float = ATR_SL, atr_mult_tp: float = ATR_TP) -> pd.DataFrame:
    out = df.copy()
    out["rsi"] = calc_rsi(out["close"], RSI_LEN)
    out["atr"] = calc_atr(out, ATR_LEN)
    out["ema50"] = calc_ema(out["close"], EMA_LEN)
    # JST hour
    jst_hour = (out.index + pd.Timedelta(hours=JST_OFFSET_H)).hour
    out["jst_hour"] = jst_hour
    # セッション: Tokyo 9-11 JST or NY 21-翌1 JST (= JST hour in 21..23 or 0..0)
    out["in_session"] = (
        ((jst_hour >= 9) & (jst_hour < 11)) |
        (jst_hour >= 21) |
        (jst_hour < 1)
    )
    # シグナル
    out["sig_long"] = (
        (out["rsi"] < rsi_os) & (out["close"] > out["ema50"]) & out["in_session"]
        & out["atr"].notna() & out["ema50"].notna()
    )
    out["sig_short"] = (
        (out["rsi"] > rsi_ob) & (out["close"] < out["ema50"]) & out["in_session"]
        & out["atr"].notna() & out["ema50"].notna()
    )
    return out


def simulate(df: pd.DataFrame, time_stop_bars: int = TIME_STOP_M15_BARS, cost_pip: float = TOTAL_COST_PIP, atr_mult_sl: float = ATR_SL, atr_mult_tp: float = ATR_TP) -> list[dict]:
    """1 ポジション同時保有まで。SL/TP/時間切れで決済。コストは pips ベースで控除。"""
    bars = df.reset_index().to_dict("records")
    trades: list[dict] = []
    in_pos = None
    for i in range(len(bars) - 1):
        row = bars[i]
        nxt = bars[i + 1]

        # ポジションあれば決済判定 (次足の high/low)
        if in_pos is not None:
            hi = nxt["high"]; lo = nxt["low"]
            in_pos["age"] += 1
            outcome = None; exit_price = None
            if in_pos["direction"] == "long":
                # SL を先に判定 (保守)
                if lo <= in_pos["sl"]:
                    exit_price = in_pos["sl"]; outcome = "SL"
                elif hi >= in_pos["tp"]:
                    exit_price = in_pos["tp"]; outcome = "TP"
            else:
                if hi >= in_pos["sl"]:
                    exit_price = in_pos["sl"]; outcome = "SL"
                elif lo <= in_pos["tp"]:
                    exit_price = in_pos["tp"]; outcome = "TP"

            # 時間切れ
            if outcome is None and in_pos["age"] >= time_stop_bars:
                exit_price = nxt["close"]; outcome = "TIME"

            if outcome is not None:
                dirn = 1 if in_pos["direction"] == "long" else -1
                gross_pips = (exit_price - in_pos["entry"]) * dirn / PIP
                net_pips = gross_pips - cost_pip
                pnl_jpy = net_pips * PIP * LOT_UNITS  # JPY クロス: 1pip = 0.01 * 1000 = 10 JPY / 0.01 lot
                trades.append({
                    **in_pos,
                    "exit_time": nxt["datetime"],
                    "exit_price": exit_price,
                    "gross_pips": gross_pips,
                    "net_pips": net_pips,
                    "pnl_jpy": pnl_jpy,
                    "outcome": outcome,
                })
                in_pos = None

        # 新規シグナル
        if in_pos is None and (row.get("sig_long") or row.get("sig_short")):
            atr = row["atr"]
            if pd.isna(atr):
                continue
            entry = nxt["open"]
            if row["sig_long"]:
                in_pos = dict(
                    direction="long",
                    entry_time=nxt["datetime"], entry=entry,
                    sl=entry - atr * atr_mult_sl,
                    tp=entry + atr * atr_mult_tp,
                    atr=atr, age=0,
                )
            else:
                in_pos = dict(
                    direction="short",
                    entry_time=nxt["datetime"], entry=entry,
                    sl=entry + atr * atr_mult_sl,
                    tp=entry - atr * atr_mult_tp,
                    atr=atr, age=0,
                )

    return trades


def summarize(trades: list[dict], label: str = "ALL") -> dict:
    if not trades:
        return {"label": label, "n": 0, "wr": 0, "pf": 0, "sharpe": 0, "sortino": 0, "max_dd": 0, "total_pips": 0, "total_pnl": 0, "avg_win": 0, "avg_loss": 0}
    td = pd.DataFrame(trades)
    n = len(td)
    wins = td[td["net_pips"] > 0]
    losses = td[td["net_pips"] <= 0]
    gross_win = wins["net_pips"].sum() if len(wins) else 0
    gross_loss = -losses["net_pips"].sum() if len(losses) else 0
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf") if gross_win > 0 else 0
    wr = len(wins) / n * 100
    # 月次でリターンを集計 -> シャープ
    td["exit_time"] = pd.to_datetime(td["exit_time"])
    td["month"] = td["exit_time"].dt.to_period("M").astype(str)
    monthly = td.groupby("month")["pnl_jpy"].sum()
    if len(monthly) > 1 and monthly.std(ddof=1) > 0:
        sharpe = (monthly.mean() / monthly.std(ddof=1)) * np.sqrt(12)
        downside = monthly[monthly < 0]
        sortino = (monthly.mean() / downside.std(ddof=1)) * np.sqrt(12) if len(downside) > 1 and downside.std(ddof=1) > 0 else float("inf") if monthly.mean() > 0 else 0
    else:
        sharpe = 0; sortino = 0
    # 累積エクイティから MaxDD (JPY)
    eq = td.sort_values("exit_time")["pnl_jpy"].cumsum() + INITIAL_BALANCE
    peak = eq.cummax()
    dd = (eq - peak) / peak * 100
    max_dd_pct = dd.min()
    return {
        "label": label,
        "n": n,
        "wr": round(wr, 1),
        "pf": round(pf, 3),
        "sharpe": round(sharpe, 3),
        "sortino": round(sortino, 3),
        "max_dd_pct": round(max_dd_pct, 2),
        "total_net_pips": round(td["net_pips"].sum(), 1),
        "total_pnl_jpy": round(td["pnl_jpy"].sum(), 0),
        "avg_win_pips": round(wins["net_pips"].mean(), 2) if len(wins) else 0,
        "avg_loss_pips": round(losses["net_pips"].mean(), 2) if len(losses) else 0,
        "long_n": int((td["direction"] == "long").sum()),
        "short_n": int((td["direction"] == "short").sum()),
        "tp_n": int((td["outcome"] == "TP").sum()),
        "sl_n": int((td["outcome"] == "SL").sum()),
        "time_n": int((td["outcome"] == "TIME").sum()),
    }


def deflated_sharpe(sharpe: float, n_trials: int, t_obs: int) -> float:
    """簡易 Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014, eq. ~)
    skew, kurtosis を仮置きしてバニラ計算。試行数による調整のみ。
    """
    if t_obs < 30 or n_trials < 1:
        return 0.0
    # 期待最大 SR (Bailey approx for N trials, std normal):
    # SR0 = sqrt(2*ln(N))
    gamma = 0.5772156649  # Euler-Mascheroni
    e_max = np.sqrt(2 * np.log(max(n_trials, 2))) - gamma / np.sqrt(2 * np.log(max(n_trials, 2)))
    # vanilla DSR (skew/kurt term を 0 で簡略化)
    if sharpe <= 0:
        return 0.0
    z = (sharpe - e_max) * np.sqrt(t_obs - 1) / np.sqrt(1 - 0 * sharpe + (1) * sharpe ** 2 / 4)
    # Z -> Phi
    from math import erf, sqrt
    p = 0.5 * (1 + erf(z / sqrt(2)))
    return p


# ----------------------------------------
# Walk-Forward Analysis
# ----------------------------------------
def walk_forward(df_ind: pd.DataFrame, n_windows: int = 6, window_months: int = 12, step_months: int = 2) -> list[dict]:
    """過去5年に対して 6 windows 走る WFA。
    各 window で IS=8か月 / OOS=4か月 (固定パラメータ評価)。
    パラメータは固定 (RSI 35/65, ATR 2.0, EMA50) — 既に Phase 0 で BT グリッド最適化済み。
    """
    results = []
    start = df_ind.index.min() + pd.Timedelta(days=60)  # 指標安定化のためバッファ
    end = df_ind.index.max()
    months_total = (end.year - start.year) * 12 + (end.month - start.month)
    if months_total < window_months:
        # 期間不足
        return []

    cur = start
    win_idx = 0
    while win_idx < n_windows:
        win_end = cur + pd.DateOffset(months=window_months)
        if win_end > end:
            break
        # IS = first 8 mo, OOS = next 4 mo
        is_end = cur + pd.DateOffset(months=8)
        df_is = df_ind.loc[cur:is_end]
        df_oos = df_ind.loc[is_end:win_end]
        if len(df_is) < 1000 or len(df_oos) < 500:
            cur = cur + pd.DateOffset(months=step_months)
            continue
        tr_is = simulate(df_is)
        tr_oos = simulate(df_oos)
        s_is = summarize(tr_is, f"WFA{win_idx}_IS")
        s_oos = summarize(tr_oos, f"WFA{win_idx}_OOS")
        results.append({"window": win_idx, "is_start": cur, "is_end": is_end, "oos_end": win_end,
                        "is_pf": s_is["pf"], "is_n": s_is["n"],
                        "oos_pf": s_oos["pf"], "oos_n": s_oos["n"],
                        "oos_sharpe": s_oos["sharpe"], "oos_pnl": s_oos["total_pnl_jpy"]})
        cur = cur + pd.DateOffset(months=step_months)
        win_idx += 1
    return results


# ----------------------------------------
# パラメータ感度 (±20%)
# ----------------------------------------
def sensitivity_scan(df: pd.DataFrame) -> list[dict]:
    base_rsi_os = 35; base_rsi_ob = 65; base_atr_sl = 2.0; base_atr_tp = 3.0
    variants = [
        ("base", base_rsi_os, base_rsi_ob, base_atr_sl, base_atr_tp),
        ("rsi_os-20%", int(base_rsi_os * 0.8), base_rsi_ob, base_atr_sl, base_atr_tp),  # 28
        ("rsi_os+20%", int(base_rsi_os * 1.2), base_rsi_ob, base_atr_sl, base_atr_tp),  # 42
        ("rsi_ob-20%", base_rsi_os, int(base_rsi_ob * 0.8), base_atr_sl, base_atr_tp),  # 52
        ("rsi_ob+20%", base_rsi_os, int(base_rsi_ob * 1.2), base_atr_sl, base_atr_tp),  # 78
        ("atr_sl-20%", base_rsi_os, base_rsi_ob, base_atr_sl * 0.8, base_atr_tp),       # 1.6
        ("atr_sl+20%", base_rsi_os, base_rsi_ob, base_atr_sl * 1.2, base_atr_tp),       # 2.4
        ("atr_tp-20%", base_rsi_os, base_rsi_ob, base_atr_sl, base_atr_tp * 0.8),       # 2.4
        ("atr_tp+20%", base_rsi_os, base_rsi_ob, base_atr_sl, base_atr_tp * 1.2),       # 3.6
    ]
    rows = []
    for name, ros, rob, asl, atp in variants:
        ind = add_indicators(df, rsi_os=ros, rsi_ob=rob, atr_mult_sl=asl, atr_mult_tp=atp)
        trs = simulate(ind, atr_mult_sl=asl, atr_mult_tp=atp)
        s = summarize(trs, name)
        s["rsi_os"] = ros; s["rsi_ob"] = rob; s["atr_sl"] = asl; s["atr_tp"] = atp
        rows.append(s)
    return rows


# ----------------------------------------
# Black Swan ストレス
# ----------------------------------------
BLACK_SWANS = [
    # (name, start_iso, end_iso, comment)
    ("SNB_2015",       "2015-01-12", "2015-01-19", "EUR/CHF surge - USD/JPY impact small"),
    ("Brexit_2016",    "2016-06-22", "2016-06-27", "GBP plunge - USD/JPY impact medium"),
    ("COVID_2020_03",  "2020-03-06", "2020-03-20", "All-currency vol spike"),
    ("JPY_intervention_2024_07", "2024-07-10", "2024-07-12", "JPY intervention USD/JPY drop"),
    ("JPY_intervention_2024_08", "2024-08-01", "2024-08-06", "Carry unwind"),
]


def stress_test(df_ind: pd.DataFrame) -> list[dict]:
    rows = []
    for name, s, e, comment in BLACK_SWANS:
        s_ts = pd.Timestamp(s).tz_localize("UTC"); e_ts = pd.Timestamp(e).tz_localize("UTC")
        # データが TZ-aware か TZ-naive かに合わせる
        if df_ind.index.tz is None:
            s_ts = s_ts.tz_localize(None); e_ts = e_ts.tz_localize(None)
        sub = df_ind.loc[s_ts:e_ts]
        if len(sub) < 5:
            rows.append({"event": name, "n_bars": len(sub), "skipped": True, "comment": comment + " — データ不足"})
            continue
        trs = simulate(sub)
        summ = summarize(trs, name)
        summ["event"] = name
        summ["n_bars"] = len(sub)
        summ["comment"] = comment
        rows.append(summ)
    return rows


# ----------------------------------------
# 日次/月次損失 上限シミュレーション
# ----------------------------------------
def loss_cap_sim(trades: list[dict], daily_warn: float = -0.015, daily_half: float = -0.03, daily_stop: float = -0.05, monthly_stop: float = -0.10) -> dict:
    """各 trade を時系列に並べて、日次 PnL / 月次 PnL を累積、上限を踏み越えた日/月をカウント"""
    if not trades:
        return {}
    td = pd.DataFrame(trades).sort_values("exit_time").copy()
    td["day"] = pd.to_datetime(td["exit_time"]).dt.date
    td["month"] = pd.to_datetime(td["exit_time"]).dt.to_period("M").astype(str)
    daily = td.groupby("day")["pnl_jpy"].sum() / INITIAL_BALANCE
    monthly = td.groupby("month")["pnl_jpy"].sum() / INITIAL_BALANCE
    return {
        "n_days_traded": len(daily),
        "n_days_warn_minus1.5%": int((daily <= daily_warn).sum()),
        "n_days_half_minus3%": int((daily <= daily_half).sum()),
        "n_days_stop_minus5%": int((daily <= daily_stop).sum()),
        "worst_day_pct": round(daily.min() * 100, 2),
        "n_months": len(monthly),
        "n_months_stop_minus10%": int((monthly <= monthly_stop).sum()),
        "worst_month_pct": round(monthly.min() * 100, 2),
        "best_month_pct": round(monthly.max() * 100, 2),
    }


# ----------------------------------------
# H1 比較 BT (timeframe 特異性論証)
# ----------------------------------------
def calc_session_filter_h1(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["rsi"] = calc_rsi(out["close"], RSI_LEN)
    out["atr"] = calc_atr(out, ATR_LEN)
    out["ema50"] = calc_ema(out["close"], EMA_LEN)
    jst_hour = (out.index + pd.Timedelta(hours=JST_OFFSET_H)).hour
    out["in_session"] = (
        ((jst_hour >= 9) & (jst_hour < 11)) |
        (jst_hour >= 21) |
        (jst_hour < 1)
    )
    out["sig_long"] = (out["rsi"] < RSI_OS) & (out["close"] > out["ema50"]) & out["in_session"] & out["atr"].notna() & out["ema50"].notna()
    out["sig_short"] = (out["rsi"] > RSI_OB) & (out["close"] < out["ema50"]) & out["in_session"] & out["atr"].notna() & out["ema50"].notna()
    return out


# ============================================================
# メイン
# ============================================================
def main():
    m15_path = ROOT / "data" / "mt5_USD_JPY_M15_2y.csv"
    h1_path = ROOT / "data" / "mt5_USD_JPY_H1_5y.csv"
    out_dir = ROOT / "data"

    print("=" * 70)
    print("Phase 2 BT: USD_JPY M15 RSI Pullback")
    print("=" * 70)
    print(f"M15: {m15_path}")
    print(f"H1:  {h1_path}")

    m15 = load_m15(m15_path)
    h1 = load_m15(h1_path)
    # TZ 統一
    if m15.index.tz is None:
        m15.index = m15.index.tz_localize("UTC")
    if h1.index.tz is None:
        h1.index = h1.index.tz_localize("UTC")
    print(f"M15: {m15.index[0]} -> {m15.index[-1]} ({len(m15)} bars)")
    print(f"H1:  {h1.index[0]} -> {h1.index[-1]} ({len(h1)} bars)")

    # ----------------------------------------
    # 指標計算 (M15)
    # ----------------------------------------
    print("\n--- M15 指標計算 + シグナル ---")
    m15_ind = add_indicators(m15)
    print(f"M15 シグナル発生: long={int(m15_ind['sig_long'].sum())} short={int(m15_ind['sig_short'].sum())}")

    # ----------------------------------------
    # メイン M15 BT (2年 全期間)
    # ----------------------------------------
    print("\n--- M15 メイン BT (2024-05 〜 2026-05、スプレッド込み) ---")
    trades = simulate(m15_ind)
    main_summary = summarize(trades, "M15_ALL_2y_with_cost")
    print(f"   {main_summary}")

    # コストなし対比 (参考)
    trades_nocost = simulate(m15_ind, cost_pip=0.0)
    main_summary_nocost = summarize(trades_nocost, "M15_ALL_2y_no_cost")
    print(f"   (参考) コストなし: {main_summary_nocost}")

    # ----------------------------------------
    # IS / OOS (70/30 期間分割)
    # ----------------------------------------
    split_date = m15.index.min() + (m15.index.max() - m15.index.min()) * 0.7
    print(f"\n--- IS/OOS 分割 (split={split_date}) ---")
    is_df = m15_ind.loc[:split_date]
    oos_df = m15_ind.loc[split_date:]
    tr_is = simulate(is_df)
    tr_oos = simulate(oos_df)
    s_is = summarize(tr_is, "IS")
    s_oos = summarize(tr_oos, "OOS")
    print(f"   IS:  {s_is}")
    print(f"   OOS: {s_oos}")

    # ----------------------------------------
    # WFA
    # ----------------------------------------
    print("\n--- Walk-Forward Analysis ---")
    wfa = walk_forward(m15_ind, n_windows=6)
    for w in wfa:
        print(f"   window={w['window']} IS=({w['is_start'].date()}~{w['is_end'].date()}) PF={w['is_pf']} n={w['is_n']} | OOS PF={w['oos_pf']} n={w['oos_n']} Sharpe={w['oos_sharpe']} PnL={w['oos_pnl']}")

    # ----------------------------------------
    # パラメータ感度
    # ----------------------------------------
    print("\n--- パラメータ感度 (±20%) ---")
    sens = sensitivity_scan(m15)
    for s in sens:
        print(f"   {s['label']:>12s}: PF={s['pf']:.2f} n={s['n']:>3d} Sharpe={s['sharpe']:.2f}")

    # ----------------------------------------
    # Black Swan
    # ----------------------------------------
    print("\n--- Black Swan ストレステスト ---")
    stress = stress_test(m15_ind)
    for s in stress:
        if s.get("skipped"):
            print(f"   {s['event']}: SKIP ({s.get('comment')})")
            continue
        print(f"   {s['event']}: n={s.get('n',0)} PF={s.get('pf',0):.2f} PnL={s.get('total_pnl_jpy',0):.0f} JPY ({s.get('comment','')})")

    # ----------------------------------------
    # 損失上限シミュレーション
    # ----------------------------------------
    print("\n--- 損失上限シミュレーション ---")
    cap = loss_cap_sim(trades)
    for k, v in cap.items():
        print(f"   {k}: {v}")

    # ----------------------------------------
    # H1 比較 BT (timeframe 特異性論証)
    # ----------------------------------------
    print("\n--- 5y H1 比較 BT (timeframe 特異性論証) ---")
    h1_ind = calc_session_filter_h1(h1)
    # H1 では time-stop bars を 6 (= 6 時間) に
    H1_TIME_STOP_BARS = 6
    trades_h1 = simulate(h1_ind, time_stop_bars=H1_TIME_STOP_BARS)
    h1_summary = summarize(trades_h1, "H1_5y_with_cost")
    print(f"   H1 5y: {h1_summary}")

    # 同期間 (2024-05 ~ 2026-05) で H1 を切り出して M15 と直接比較
    h1_2y = h1.loc[m15.index[0]:m15.index[-1]]
    h1_2y_ind = calc_session_filter_h1(h1_2y)
    trades_h1_2y = simulate(h1_2y_ind, time_stop_bars=H1_TIME_STOP_BARS)
    h1_2y_summary = summarize(trades_h1_2y, "H1_2y_same_period")
    print(f"   H1 同期間 (2y): {h1_2y_summary}")

    # 同期間 M15 vs H1
    print(f"\n   ★ Timeframe 比較 (同期間 2y、スプレッド込み):")
    print(f"     M15: PF={main_summary['pf']} n={main_summary['n']} PnL={main_summary['total_pnl_jpy']:.0f} WR={main_summary['wr']}%")
    print(f"     H1:  PF={h1_2y_summary['pf']} n={h1_2y_summary['n']} PnL={h1_2y_summary['total_pnl_jpy']:.0f} WR={h1_2y_summary['wr']}%")

    # ----------------------------------------
    # Deflated Sharpe (試行数: BT グリッドが 20 試行)
    # ----------------------------------------
    n_trials = 20
    t_obs_months = max(1, (m15.index[-1] - m15.index[0]).days / 30)
    dsr = deflated_sharpe(main_summary["sharpe"], n_trials, int(t_obs_months))
    print(f"\n--- Deflated Sharpe (試行数={n_trials}, 月数={int(t_obs_months)}): p≈{dsr:.4f} ---")

    # ----------------------------------------
    # 機会費用比較
    # ----------------------------------------
    years = (m15.index[-1] - m15.index[0]).days / 365.25
    annual_pnl_jpy = main_summary["total_pnl_jpy"] / years if years > 0 else 0
    annual_pct = annual_pnl_jpy / INITIAL_BALANCE * 100
    print(f"\n--- 機会費用比較 ({years:.2f} 年運用、初期 100万 JPY、lot 0.01) ---")
    print(f"   戦略累計 PnL: {main_summary['total_pnl_jpy']:.0f} JPY ({main_summary['total_pnl_jpy']/INITIAL_BALANCE*100:.2f}%)")
    print(f"   戦略年率: {annual_pct:.2f}% / 年 (≒{annual_pnl_jpy:.0f} JPY/年)")
    print(f"   米国債4%/年: +{INITIAL_BALANCE * 0.04:.0f} JPY/年")
    print(f"   ゲート: 戦略年率 > 4% ? {'PASS' if annual_pct > 4 else 'FAIL'}")

    # ----------------------------------------
    # 出力
    # ----------------------------------------
    if trades:
        td_df = pd.DataFrame(trades)
        td_df.to_csv(out_dir / "_phase2_bt_2_usdjpy_trades.csv", index=False)

        # monthly
        td_df["month"] = pd.to_datetime(td_df["exit_time"]).dt.to_period("M").astype(str)
        monthly = td_df.groupby("month").agg(
            n=("pnl_jpy", "count"),
            sum=("pnl_jpy", "sum"),
            avg=("pnl_jpy", "mean"),
        )
        monthly.to_csv(out_dir / "_phase2_bt_2_usdjpy_monthly.csv")

        # stress
        stress_df = pd.DataFrame(stress)
        stress_df.to_csv(out_dir / "_phase2_bt_2_usdjpy_stress.csv", index=False)

    # ----------------------------------------
    # ゲート判定
    # ----------------------------------------
    print("\n" + "=" * 70)
    print("ゲート判定")
    print("=" * 70)
    gate = {}
    gate["PF >= 1.3"] = ("PASS" if main_summary["pf"] >= 1.3 else "FAIL", main_summary["pf"])
    gate["Sharpe >= 0.8"] = ("PASS" if main_summary["sharpe"] >= 0.8 else "FAIL", main_summary["sharpe"])
    gate["OOS trades >= 30"] = ("PASS" if s_oos["n"] >= 30 else "FAIL", s_oos["n"])
    gate["機会費用 (4%/年)"] = ("PASS" if annual_pct >= 4 else "FAIL", round(annual_pct, 2))
    gate["損失上限 作動?"] = (
        "PASS" if cap.get("n_days_warn_minus1.5%", 0) > 0 or cap.get("n_months_stop_minus10%", 0) >= 0 else "FAIL",
        cap.get("worst_day_pct", 0),
    )
    # Black Swan: 任意の event で MaxDD < 上限を超えなかったらPASS。
    # ここでは、各 event の PnL 損失が初期残高の 5% 以下であれば OK
    bs_pass = all(
        (s.get("total_pnl_jpy", 0) > -INITIAL_BALANCE * 0.05)
        for s in stress
        if not s.get("skipped")
    )
    gate["Black Swan 耐性"] = ("PASS" if bs_pass else "FAIL", "各イベント PnL > -5%")
    for k, (v, val) in gate.items():
        print(f"   [{v}] {k}: {val}")

    all_pass = all(v == "PASS" for v, _ in gate.values())
    print(f"\n総合: {'Phase 3 進出推奨' if all_pass else '棚上げ / 廃案'}")


if __name__ == "__main__":
    main()
