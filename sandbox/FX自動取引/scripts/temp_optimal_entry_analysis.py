"""
READ-ONLY: USD/JPY 7取引について「本来のベストエントリータイミング」を逆引き分析する。

出力:
  1. 各取引の実エントリー vs 最適エントリー（実最安/最高値、機会損失pips）
  2. 最適時点での RSI/MACD/BB/ADX/MA200距離/H4方向
  3. 最適時点で現行ロジック (MTFPullback / RsiMaCrossover) のシグナルが出ていたか
  4. 実 vs 最適の指標差分から「拾えなかった原因」を抽出
  5. 改善候補の優先順リスト（3件以上で再現するもののみ）

何も変更しない。
"""
import sys
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta

SYMBOL = "USDJPY-"
PIP = 0.01

# 戦略パラメータ（src/config.py / mtf_pullback.py から）
MTF_TREND_MA = 200
MTF_RSI_OVERSOLD = 35
MTF_RSI_OVERBOUGHT = 65
RSI_PERIOD = 14
MA_SHORT = 20
MA_LONG = 50
MA_CROSS_LOOKBACK = 5
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
ADX_PERIOD = 14
ADX_THRESHOLD = 15.0
MFI_PERIOD = 14
MFI_OVERBOUGHT = 80
MFI_OVERSOLD = 20

TRADES = [
    (3,  "2026-04-21T10:06:57", "2026-04-21T13:54:36", "BUY",  7190, 159.210, 159.064, 159.193, -119),
    (10, "2026-04-21T10:18:45", "2026-04-21T13:54:37", "BUY",  7521, 159.216, 159.079, 159.193, -161),
    (15, "2026-04-21T10:21:00", "2026-04-21T13:54:38", "BUY",  7521, 159.205, 159.068, 159.192,  -91),
    (19, "2026-04-22T05:30:59", "2026-04-22T18:16:26", "BUY",  3807, 159.145, 159.022, 159.424, +837),
    (29, "2026-04-23T11:54:32", "2026-04-23T17:49:14", "BUY",  3872, 159.518, 159.384, 159.382, -408),
    (35, "2026-04-24T11:05:05", "2026-04-24T14:21:45", "BUY",  4482, 159.601, 159.477, 159.474, -508),
    (40, "2026-04-27T16:54:15", "2026-04-28T04:01:18", "SELL", 3811, 159.372, 159.512, 159.512, -469),
]


def parse_utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def fetch_bars(symbol: str, timeframe, date_from: datetime, date_to: datetime) -> pd.DataFrame:
    rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"copy_rates_range empty: {symbol} {timeframe} {date_from}~{date_to} err={mt5.last_error()}")
    df = pd.DataFrame(rates)
    df["time_utc"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.set_index("time_utc").sort_index()
    return df


def calc_indicators_m15(df: pd.DataFrame) -> pd.DataFrame:
    """M15 dfに各指標列を追加して返す。"""
    out = df.copy()
    out["rsi14"] = ta.rsi(out["close"], length=RSI_PERIOD)
    macd = ta.macd(out["close"], fast=12, slow=26, signal=9)
    if macd is not None and not macd.empty:
        # pandas_ta returns columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        out["macd"] = macd.iloc[:, 0]
        out["macd_hist"] = macd.iloc[:, 1]
        out["macd_signal"] = macd.iloc[:, 2]
    bb = ta.bbands(out["close"], length=20, std=2.0)
    if bb is not None and not bb.empty:
        # BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB_20_2.0, BBP_20_2.0
        out["bb_lower"] = bb.iloc[:, 0]
        out["bb_mid"] = bb.iloc[:, 1]
        out["bb_upper"] = bb.iloc[:, 2]
        out["bb_pct"] = bb.iloc[:, 4]  # %B: 0=lower, 1=upper
    adx_df = ta.adx(out["high"], out["low"], out["close"], length=ADX_PERIOD)
    if adx_df is not None and not adx_df.empty:
        out["adx14"] = adx_df[f"ADX_{ADX_PERIOD}"]
    out["ma200"] = ta.sma(out["close"], length=MTF_TREND_MA)
    out["ma_short"] = ta.sma(out["close"], length=MA_SHORT)
    out["ma_long"] = ta.sma(out["close"], length=MA_LONG)
    # MFI: tick_volume を volume として使う
    if "tick_volume" in out.columns:
        try:
            out["mfi14"] = ta.mfi(out["high"], out["low"], out["close"], out["tick_volume"], length=MFI_PERIOD)
        except Exception:
            out["mfi14"] = float("nan")
    return out


def find_optimal_bar(bars_in_window: pd.DataFrame, side: str) -> tuple:
    """期間内のBUYなら最安値(low)、SELLなら最高値(high)とその時刻を返す。"""
    if side == "BUY":
        idx = bars_in_window["low"].idxmin()
        price = bars_in_window.loc[idx, "low"]
    else:
        idx = bars_in_window["high"].idxmax()
        price = bars_in_window.loc[idx, "high"]
    return idx, price


def check_mtf_pullback_signal(row: pd.Series, side_wanted: str) -> tuple:
    """その時点のM15バー(open完了状態)で MTFPullback がシグナルを出していたか。

    Returns: (signal_str, hold_reason)
    """
    close = row["close"]
    ma200 = row.get("ma200")
    rsi = row.get("rsi14")
    if pd.isna(ma200) or pd.isna(rsi):
        return "NaN", "indicators NaN"
    if close > ma200 and rsi < MTF_RSI_OVERSOLD:
        return "BUY", None
    if close < ma200 and rsi > MTF_RSI_OVERBOUGHT:
        return "SELL", None
    if close > ma200:
        return "HOLD", f"上昇トレンドだがRSI={rsi:.1f}≥{MTF_RSI_OVERSOLD}"
    return "HOLD", f"下降トレンドだがRSI={rsi:.1f}≤{MTF_RSI_OVERBOUGHT}"


def check_rsi_ma_crossover_signal(bars_until: pd.DataFrame, side_wanted: str) -> tuple:
    """直近 MA_CROSS_LOOKBACK 本以内の MA20/50 クロス + RSI/ADX/MFI フィルター。"""
    if len(bars_until) < MA_CROSS_LOOKBACK + 1:
        return "NaN", "data short"
    last = bars_until.iloc[-1]
    rsi = last.get("rsi14")
    adx = last.get("adx14")
    mfi = last.get("mfi14")
    if pd.isna(rsi) or pd.isna(adx):
        return "NaN", "indicators NaN"

    # クロス検出
    short = bars_until["ma_short"]
    long = bars_until["ma_long"]
    recent_cross_up = False
    recent_cross_down = False
    for i in range(1, MA_CROSS_LOOKBACK + 1):
        if i + 1 > len(bars_until):
            break
        prev = bars_until.iloc[-i - 1]
        cur = bars_until.iloc[-i]
        if pd.isna(prev["ma_short"]) or pd.isna(prev["ma_long"]) or pd.isna(cur["ma_short"]) or pd.isna(cur["ma_long"]):
            continue
        if prev["ma_short"] <= prev["ma_long"] and cur["ma_short"] > cur["ma_long"]:
            recent_cross_up = True
        if prev["ma_short"] >= prev["ma_long"] and cur["ma_short"] < cur["ma_long"]:
            recent_cross_down = True

    if adx < ADX_THRESHOLD:
        return "HOLD", f"ADX弱({adx:.1f}<{ADX_THRESHOLD})"

    if recent_cross_up and rsi < RSI_OVERBOUGHT:
        if not pd.isna(mfi) and mfi >= MFI_OVERBOUGHT:
            return "HOLD", f"MFI買われすぎ({mfi:.1f}≥{MFI_OVERBOUGHT})"
        return "BUY", None
    if recent_cross_down and rsi > RSI_OVERSOLD:
        if not pd.isna(mfi) and mfi <= MFI_OVERSOLD:
            return "HOLD", f"MFI売られすぎ({mfi:.1f}≤{MFI_OVERSOLD})"
        return "SELL", None

    return "HOLD", f"クロスなし(up={recent_cross_up}, down={recent_cross_down})"


def get_state_at(time_target: datetime, bars: pd.DataFrame) -> Optional[pd.Series]:
    """time_target 時点で「直前に閉じた M15 バー」の指標を返す。"""
    prior = bars[bars.index < time_target]
    if len(prior) == 0:
        return None
    return prior.iloc[-1].copy()


def get_h4_direction(time_target: datetime, h4_bars: pd.DataFrame) -> str:
    """time_target 直前の H4 バーの方向(up/down/flat)。"""
    prior = h4_bars[h4_bars.index < time_target]
    if len(prior) == 0:
        return "n/a"
    last = prior.iloc[-1]
    if last["close"] > last["open"] * 1.0001:
        return "up"
    if last["close"] < last["open"] * 0.9999:
        return "down"
    return "flat"


def main():
    if not mt5.initialize():
        print(f"[ERROR] mt5.initialize failed: {mt5.last_error()}")
        sys.exit(1)

    try:
        # 4/20〜4/29で十分カバー（±12時間 + 各種MA/ATRバッファ）
        # MA200 M15 は約2日分必要なので余裕を持って4/15から取得
        date_from = datetime(2026, 4, 15, 0, 0, tzinfo=timezone.utc)
        date_to = datetime(2026, 4, 29, 0, 0, tzinfo=timezone.utc)
        m15 = fetch_bars(SYMBOL, mt5.TIMEFRAME_M15, date_from, date_to)
        h4 = fetch_bars(SYMBOL, mt5.TIMEFRAME_H4, date_from, date_to)
        print(f"[BARS] M15={len(m15)} H4={len(h4)}")

        m15 = calc_indicators_m15(m15)

        # ±12時間 と ±2時間 の2スコープで分析
        WINDOW_HOURS = 12  # team-lead指示
        opt_rows = []
        for tid, opened_s, closed_s, side, units, open_p, sl_p, close_p, actual_pl in TRADES:
            opened = parse_utc(opened_s)
            window_from = opened - timedelta(hours=WINDOW_HOURS)
            window_to = opened + timedelta(hours=WINDOW_HOURS)
            win_bars = m15[(m15.index >= window_from) & (m15.index <= window_to)]
            if len(win_bars) == 0:
                print(f"[WARN] no bars in window for trade {tid}")
                continue

            opt_time, opt_price = find_optimal_bar(win_bars, side)
            # opportunity loss in pips
            if side == "BUY":
                opp_loss_pips = (open_p - opt_price) / PIP  # 正なら最適より高く買った
            else:
                opp_loss_pips = (opt_price - open_p) / PIP  # 正なら最適より安く売った

            # 狭い窓 ±2時間 でも最適点を別途算出
            narrow_from = opened - timedelta(hours=2)
            narrow_to = opened + timedelta(hours=2)
            narrow_bars = m15[(m15.index >= narrow_from) & (m15.index <= narrow_to)]
            if len(narrow_bars) > 0:
                narrow_opt_time, narrow_opt_price = find_optimal_bar(narrow_bars, side)
                if side == "BUY":
                    narrow_opp_loss = (open_p - narrow_opt_price) / PIP
                else:
                    narrow_opp_loss = (narrow_opt_price - open_p) / PIP
            else:
                narrow_opt_time, narrow_opt_price, narrow_opp_loss = None, None, None

            # 状態取得（実エントリー時点と最適時点）
            state_actual = get_state_at(opened, m15)
            state_opt = get_state_at(opt_time + timedelta(seconds=1), m15)  # 最適バーが完了した直後
            state_narrow = get_state_at(narrow_opt_time + timedelta(seconds=1), m15) if narrow_opt_time else None
            h4_dir_actual = get_h4_direction(opened, h4)
            h4_dir_opt = get_h4_direction(opt_time + timedelta(seconds=1), h4)
            h4_dir_narrow = get_h4_direction(narrow_opt_time + timedelta(seconds=1), h4) if narrow_opt_time else "n/a"

            # 現行ロジック判定（最適時点）
            mtf_sig_opt, mtf_reason_opt = ("n/a", "no state")
            mac_sig_opt, mac_reason_opt = ("n/a", "no state")
            if state_opt is not None:
                mtf_sig_opt, mtf_reason_opt = check_mtf_pullback_signal(state_opt, side)
                # MA Crossoverは履歴必要
                bars_until_opt = m15[m15.index <= opt_time]
                mac_sig_opt, mac_reason_opt = check_rsi_ma_crossover_signal(bars_until_opt, side)

            # 現行ロジック判定（実エントリー時点）— 比較のため
            mtf_sig_actual, mtf_reason_actual = ("n/a", "no state")
            mac_sig_actual, mac_reason_actual = ("n/a", "no state")
            if state_actual is not None:
                mtf_sig_actual, mtf_reason_actual = check_mtf_pullback_signal(state_actual, side)
                bars_until_act = m15[m15.index < opened]
                mac_sig_actual, mac_reason_actual = check_rsi_ma_crossover_signal(bars_until_act, side)

            row = {
                "id": tid,
                "side": side,
                "entry_time": opened_s,
                "entry_price": open_p,
                "opt_time": opt_time.isoformat(),
                "opt_price": float(opt_price),
                "opp_loss_pips": round(opp_loss_pips, 1),
                "minutes_diff": round((opt_time - opened).total_seconds() / 60, 1),
                "narrow_opt_time": narrow_opt_time.isoformat() if narrow_opt_time else None,
                "narrow_opt_price": float(narrow_opt_price) if narrow_opt_price else None,
                "narrow_opp_loss_pips": round(narrow_opp_loss, 1) if narrow_opp_loss is not None else None,
                "narrow_minutes_diff": round((narrow_opt_time - opened).total_seconds() / 60, 1) if narrow_opt_time else None,
                # 実エントリー時点の指標
                "act_close": float(state_actual["close"]) if state_actual is not None else None,
                "act_rsi": round(float(state_actual["rsi14"]), 1) if state_actual is not None and not pd.isna(state_actual["rsi14"]) else None,
                "act_macd_hist": round(float(state_actual["macd_hist"]), 5) if state_actual is not None and not pd.isna(state_actual["macd_hist"]) else None,
                "act_bb_pct": round(float(state_actual["bb_pct"]), 3) if state_actual is not None and not pd.isna(state_actual["bb_pct"]) else None,
                "act_adx": round(float(state_actual["adx14"]), 1) if state_actual is not None and not pd.isna(state_actual["adx14"]) else None,
                "act_mfi": round(float(state_actual["mfi14"]), 1) if state_actual is not None and "mfi14" in state_actual.index and not pd.isna(state_actual["mfi14"]) else None,
                "act_ma200_dist_pips": round((float(state_actual["close"]) - float(state_actual["ma200"])) / PIP, 1) if state_actual is not None and not pd.isna(state_actual["ma200"]) else None,
                "act_h4_dir": h4_dir_actual,
                "act_mtf_sig": mtf_sig_actual,
                "act_mtf_reason": mtf_reason_actual,
                "act_mac_sig": mac_sig_actual,
                "act_mac_reason": mac_reason_actual,
                # 最適時点の指標
                "opt_close": float(state_opt["close"]) if state_opt is not None else None,
                "opt_rsi": round(float(state_opt["rsi14"]), 1) if state_opt is not None and not pd.isna(state_opt["rsi14"]) else None,
                "opt_macd_hist": round(float(state_opt["macd_hist"]), 5) if state_opt is not None and not pd.isna(state_opt["macd_hist"]) else None,
                "opt_bb_pct": round(float(state_opt["bb_pct"]), 3) if state_opt is not None and not pd.isna(state_opt["bb_pct"]) else None,
                "opt_adx": round(float(state_opt["adx14"]), 1) if state_opt is not None and not pd.isna(state_opt["adx14"]) else None,
                "opt_mfi": round(float(state_opt["mfi14"]), 1) if state_opt is not None and "mfi14" in state_opt.index and not pd.isna(state_opt["mfi14"]) else None,
                "opt_ma200_dist_pips": round((float(state_opt["close"]) - float(state_opt["ma200"])) / PIP, 1) if state_opt is not None and not pd.isna(state_opt["ma200"]) else None,
                "opt_h4_dir": h4_dir_opt,
                "opt_mtf_sig": mtf_sig_opt,
                "opt_mtf_reason": mtf_reason_opt,
                "opt_mac_sig": mac_sig_opt,
                "opt_mac_reason": mac_reason_opt,
                # 狭い窓 ±2h の最適点指標
                "narrow_rsi": round(float(state_narrow["rsi14"]), 1) if state_narrow is not None and not pd.isna(state_narrow.get("rsi14", float("nan"))) else None,
                "narrow_macd_hist": round(float(state_narrow["macd_hist"]), 5) if state_narrow is not None and not pd.isna(state_narrow.get("macd_hist", float("nan"))) else None,
                "narrow_bb_pct": round(float(state_narrow["bb_pct"]), 3) if state_narrow is not None and not pd.isna(state_narrow.get("bb_pct", float("nan"))) else None,
                "narrow_adx": round(float(state_narrow["adx14"]), 1) if state_narrow is not None and not pd.isna(state_narrow.get("adx14", float("nan"))) else None,
                "narrow_mfi": round(float(state_narrow["mfi14"]), 1) if state_narrow is not None and "mfi14" in state_narrow.index and not pd.isna(state_narrow["mfi14"]) else None,
                "narrow_ma200_dist_pips": round((float(state_narrow["close"]) - float(state_narrow["ma200"])) / PIP, 1) if state_narrow is not None and not pd.isna(state_narrow.get("ma200", float("nan"))) else None,
                "narrow_h4_dir": h4_dir_narrow,
            }
            opt_rows.append(row)

        df = pd.DataFrame(opt_rows)
        with pd.option_context("display.max_columns", None, "display.width", 280):
            print("\n=== 機会損失と最適時刻 ===")
            cols_a = ["id", "side", "entry_time", "entry_price", "opt_time", "opt_price", "opp_loss_pips", "minutes_diff"]
            print(df[cols_a].to_string(index=False))

            print("\n=== 実エントリー時点の指標 ===")
            cols_b = ["id", "side", "act_rsi", "act_macd_hist", "act_bb_pct", "act_adx", "act_mfi", "act_ma200_dist_pips", "act_h4_dir", "act_mtf_sig", "act_mac_sig"]
            print(df[cols_b].to_string(index=False))

            print("\n=== 最適時点の指標 ===")
            cols_c = ["id", "side", "opt_rsi", "opt_macd_hist", "opt_bb_pct", "opt_adx", "opt_mfi", "opt_ma200_dist_pips", "opt_h4_dir", "opt_mtf_sig", "opt_mac_sig"]
            print(df[cols_c].to_string(index=False))

            print("\n=== シグナル比較 (実 vs 最適) ===")
            for _, r in df.iterrows():
                print(f"  id={r['id']} ({r['side']}) opp_loss={r['opp_loss_pips']:.1f}pips, time_diff={r['minutes_diff']}分")
                print(f"    [実]  MTF={r['act_mtf_sig']:5s} ({r['act_mtf_reason']}) | MAC={r['act_mac_sig']:5s} ({r['act_mac_reason']})")
                print(f"    [最適] MTF={r['opt_mtf_sig']:5s} ({r['opt_mtf_reason']}) | MAC={r['opt_mac_sig']:5s} ({r['opt_mac_reason']})")

        # 保存
        csv_path = "C:/bpr_lab/sandbox/FX自動取引/data/optimal_entry_USD_JPY_7trades.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n[CSV saved] {csv_path}")
        json_path = "C:/bpr_lab/sandbox/FX自動取引/data/optimal_entry_USD_JPY_7trades.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(opt_rows, f, ensure_ascii=False, indent=2, default=str)
        print(f"[JSON saved] {json_path}")

        # 改善候補抽出（パターン集計）
        print("\n=== パターン集計 ===")
        # 1. 最適時点で MTF がシグナル出していたか
        mtf_opt_signaled = (df["opt_mtf_sig"] == df["side"]).sum()
        mac_opt_signaled = (df["opt_mac_sig"] == df["side"]).sum()
        print(f"最適時点で MTFPullback が同方向シグナル: {mtf_opt_signaled}/{len(df)}件")
        print(f"最適時点で MA Crossover が同方向シグナル: {mac_opt_signaled}/{len(df)}件")

        # 2. 実 vs 最適 RSI 差
        df["rsi_delta"] = df["opt_rsi"] - df["act_rsi"]
        print(f"\nRSI delta (最適 - 実) 分布:")
        print(df[["id", "side", "act_rsi", "opt_rsi", "rsi_delta"]].to_string(index=False))

        # 3. 各取引の最適時点の RSI が「拾える閾値」だったか
        buy_trades = df[df["side"] == "BUY"]
        sell_trades = df[df["side"] == "SELL"]
        print(f"\nBUY取引 ({len(buy_trades)}件) 最適時点のRSI: 最低={buy_trades['opt_rsi'].min()}, 最高={buy_trades['opt_rsi'].max()}, 平均={buy_trades['opt_rsi'].mean():.1f}")
        if len(sell_trades) > 0:
            print(f"SELL取引 ({len(sell_trades)}件) 最適時点のRSI: 最低={sell_trades['opt_rsi'].min()}, 最高={sell_trades['opt_rsi'].max()}, 平均={sell_trades['opt_rsi'].mean():.1f}")

        # 4. 機会損失の規模
        print(f"\n機会損失 (pips): mean={df['opp_loss_pips'].mean():.1f}, max={df['opp_loss_pips'].max():.1f}, min={df['opp_loss_pips'].min():.1f}")
        print(f"時間差 (分, 最適-実): mean={df['minutes_diff'].mean():.1f}, max={df['minutes_diff'].max():.1f}, min={df['minutes_diff'].min():.1f}")

        # 5. BB %B 状態
        print(f"\nBB %B 比較:")
        print(df[["id", "side", "act_bb_pct", "opt_bb_pct"]].to_string(index=False))

        # 6. 狭い窓 ±2h の最適点
        print(f"\n=== 狭い窓 ±2h の最適エントリー ===")
        print(df[["id", "side", "entry_price", "narrow_opt_time", "narrow_opt_price", "narrow_opp_loss_pips", "narrow_minutes_diff"]].to_string(index=False))
        print(f"\n  ±2h機会損失: mean={df['narrow_opp_loss_pips'].mean():.1f}pips, max={df['narrow_opp_loss_pips'].max():.1f}, min={df['narrow_opp_loss_pips'].min():.1f}")
        print(f"\n=== 狭い窓 ±2h 最適点の指標 ===")
        print(df[["id", "side", "narrow_rsi", "narrow_macd_hist", "narrow_bb_pct", "narrow_adx", "narrow_mfi", "narrow_ma200_dist_pips", "narrow_h4_dir"]].to_string(index=False))

        # 7. BUY取引で H4 が "down" のもの = 逆張りBUYしている可能性
        h4_misalign = df[((df["side"] == "BUY") & (df["act_h4_dir"] == "down")) | ((df["side"] == "SELL") & (df["act_h4_dir"] == "up"))]
        print(f"\n=== H4方向と取引方向の逆 ===")
        print(f"逆張り取引数: {len(h4_misalign)}/{len(df)}")
        if len(h4_misalign) > 0:
            print(h4_misalign[["id", "side", "act_h4_dir", "entry_price"]].to_string(index=False))

        # 8. 各取引の MA200 vs price で「上か下か」の整合
        print(f"\n=== MA200距離（実エントリー時点） ===")
        for _, r in df.iterrows():
            d = r["act_ma200_dist_pips"]
            ok = "○" if (r["side"] == "BUY" and d > 0) or (r["side"] == "SELL" and d < 0) else "× (逆方向トレンド中)"
            print(f"  id={r['id']} {r['side']} ma200_dist={d:+.1f}pips {ok}")

    finally:
        mt5.shutdown()

    print("\n[DONE]")


if __name__ == "__main__":
    main()
