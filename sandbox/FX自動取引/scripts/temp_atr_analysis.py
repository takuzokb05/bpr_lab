"""
READ-ONLY: USD/JPY 過去7取引について「ATR連動SL/TPなら救えたか」を実証分析。

各取引について:
  1. エントリー直前のATR(14) M15
  2. 実SL幅(pips)
  3. ATR×1.5 SL幅(pips)
  4. 保有期間中のMAE(pips, 不利方向)
  5. 仮想シミュレーション: ATR×1.5 SL & TP1=ATR×1.0 / TP2=ATR×3.0
     - SL/TPヒット時刻と最終損益(pips, 通貨単位*pip換算)

何も変更しない。
"""
import sys
import io
import json
from datetime import datetime, timedelta, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import MetaTrader5 as mt5
import pandas as pd
import numpy as np

SYMBOL = "USDJPY-"
TIMEFRAME = mt5.TIMEFRAME_M15  # M15
ATR_PERIOD = 14
PIP = 0.01  # USD/JPY: 0.01 = 1pip (業界標準。3桁目はpipette=0.1pip)

# 対象取引(team-leadからの指示そのまま)
TRADES = [
    # id, opened_utc, closed_utc, side, units, open, sl, close, pl
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


def calc_atr_wilder(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder's ATR (RMA)。dfはOHLC列を持つ前提。"""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    # Wilder smoothing = EMA with alpha=1/period
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    return atr


def fetch_m15(symbol: str, date_from: datetime, date_to: datetime) -> pd.DataFrame:
    rates = mt5.copy_rates_range(symbol, TIMEFRAME, date_from, date_to)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"copy_rates_range returned empty for {symbol} {date_from}~{date_to} err={mt5.last_error()}")
    df = pd.DataFrame(rates)
    df["time_utc"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.set_index("time_utc").sort_index()
    return df[["open", "high", "low", "close", "tick_volume"]]


def simulate_atr_sl_tp(
    bars: pd.DataFrame,
    side: str,
    entry_price: float,
    entry_time: datetime,
    actual_close_time: datetime,
    actual_close_price: float,
    atr_at_entry: float,
    sl_mult: float = 1.5,
    tp1_mult: float = 1.0,
    tp2_mult: float = 3.0,
) -> dict:
    """エントリー直後〜実際クローズ時刻までのバーを順に走査し、SL/TP ヒットを判定。

    バー内の最高値・最安値で判定（保守的に SL→TP の順でチェックする）。
    """
    sl_dist = atr_at_entry * sl_mult
    tp1_dist = atr_at_entry * tp1_mult
    tp2_dist = atr_at_entry * tp2_mult

    if side == "BUY":
        sl_price = entry_price - sl_dist
        tp1_price = entry_price + tp1_dist
        tp2_price = entry_price + tp2_dist
    else:  # SELL
        sl_price = entry_price + sl_dist
        tp1_price = entry_price - tp1_dist
        tp2_price = entry_price - tp2_dist

    # entry_time 以降のバーを順に
    walk = bars[(bars.index >= entry_time) & (bars.index <= actual_close_time + timedelta(minutes=15))]

    hit_event = None  # "SL" / "TP1" / "TP2"
    hit_time = None
    hit_price = None
    mae_pips = 0.0  # 最大不利幅(pips, 正の値)
    mfe_pips = 0.0  # 最大有利幅(pips, 正の値)

    for ts, bar in walk.iterrows():
        bar_high = bar["high"]
        bar_low = bar["low"]

        # MAE / MFE 更新（実際の決済時刻までで集計したい）
        if ts <= actual_close_time:
            if side == "BUY":
                cur_mae = (entry_price - bar_low) / PIP
                cur_mfe = (bar_high - entry_price) / PIP
            else:
                cur_mae = (bar_high - entry_price) / PIP
                cur_mfe = (entry_price - bar_low) / PIP
            mae_pips = max(mae_pips, cur_mae)
            mfe_pips = max(mfe_pips, cur_mfe)

        if hit_event is not None:
            continue  # MAE/MFEだけ実クローズ時刻まで継続

        # 仮想SL/TPヒット判定
        if side == "BUY":
            sl_hit = bar_low <= sl_price
            tp2_hit = bar_high >= tp2_price
            tp1_hit = bar_high >= tp1_price
        else:
            sl_hit = bar_high >= sl_price
            tp2_hit = bar_low <= tp2_price
            tp1_hit = bar_low <= tp1_price

        # 保守的に SL を優先、次に TP2、次に TP1 の順で判定
        if sl_hit:
            hit_event = "SL"
            hit_time = ts
            hit_price = sl_price
        elif tp2_hit:
            hit_event = "TP2"
            hit_time = ts
            hit_price = tp2_price
        elif tp1_hit:
            hit_event = "TP1"
            hit_time = ts
            hit_price = tp1_price

    # 何もヒットしなかった場合は実際のクローズ価格で決済
    if hit_event is None:
        hit_event = "ACTUAL_CLOSE"
        hit_time = actual_close_time
        hit_price = actual_close_price

    if side == "BUY":
        sim_pl_pips = (hit_price - entry_price) / PIP
    else:
        sim_pl_pips = (entry_price - hit_price) / PIP

    return {
        "sl_dist_pips": sl_dist / PIP,
        "tp1_dist_pips": tp1_dist / PIP,
        "tp2_dist_pips": tp2_dist / PIP,
        "sl_price": sl_price,
        "tp1_price": tp1_price,
        "tp2_price": tp2_price,
        "hit_event": hit_event,
        "hit_time": hit_time.isoformat() if hit_time else None,
        "hit_price": hit_price,
        "sim_pl_pips": sim_pl_pips,
        "mae_pips": mae_pips,
        "mfe_pips": mfe_pips,
    }


def main():
    if not mt5.initialize():
        print(f"[ERROR] mt5.initialize failed: {mt5.last_error()}")
        sys.exit(1)

    try:
        info = mt5.account_info()
        if info:
            print(f"[ACCOUNT] login={info.login} server={info.server}")

        # 全期間カバーするM15足を一括取得（4/20〜4/29）
        date_from = datetime(2026, 4, 20, 0, 0, tzinfo=timezone.utc)
        date_to = datetime(2026, 4, 29, 0, 0, tzinfo=timezone.utc)
        bars = fetch_m15(SYMBOL, date_from, date_to)
        print(f"[BARS] M15 fetched: {len(bars)} bars from {bars.index[0]} to {bars.index[-1]}")

        # ATR(14) を全期間に対して計算
        atr_series = calc_atr_wilder(bars, ATR_PERIOD)

        rows = []
        for tid, opened_s, closed_s, side, units, open_p, sl_p, close_p, actual_pl_jpy in TRADES:
            opened = parse_utc(opened_s)
            closed = parse_utc(closed_s)

            # エントリー直前のATR = エントリー時刻**未満**で最も新しいM15バー終値時点のATR
            # M15バーは [open_time, open_time+15min) 区間。バーの time_utc は OPEN time。
            # エントリー直前 = entry_time の **直前に閉じたバー** の ATR を使う
            prior_bars = atr_series[atr_series.index < opened]
            if len(prior_bars) == 0:
                print(f"[WARN] No prior bars for trade {tid}")
                continue
            atr_entry_time = prior_bars.index[-1]
            atr_value = float(prior_bars.iloc[-1])
            atr_pips = atr_value / PIP

            # 実SL幅
            actual_sl_dist = abs(open_p - sl_p)
            actual_sl_pips = actual_sl_dist / PIP

            # シミュレーション
            sim = simulate_atr_sl_tp(
                bars=bars,
                side=side,
                entry_price=open_p,
                entry_time=opened,
                actual_close_time=closed,
                actual_close_price=close_p,
                atr_at_entry=atr_value,
            )

            # 損益円換算: sim_pl_pips * PIP * units = price_diff * units = JPY
            # (USD/JPY のクロス円ペアは units * 価格差 がそのまま円損益)
            sim_pl_jpy = sim["sim_pl_pips"] * PIP * units

            row = {
                "id": tid,
                "side": side,
                "units": units,
                "opened_utc": opened_s,
                "closed_utc": closed_s,
                "entry_price": open_p,
                "actual_sl_price": sl_p,
                "actual_close_price": close_p,
                "actual_pl_jpy": actual_pl_jpy,
                "atr_M15_at_entry": round(atr_value, 5),
                "atr_pips": round(atr_pips, 2),
                "atr_bar_time_used": atr_entry_time.isoformat(),
                "actual_sl_pips": round(actual_sl_pips, 2),
                "atr_x1.5_sl_pips": round(sim["sl_dist_pips"], 2),
                "sl_widening_pips": round(sim["sl_dist_pips"] - actual_sl_pips, 2),
                "mae_pips": round(sim["mae_pips"], 2),
                "mfe_pips": round(sim["mfe_pips"], 2),
                "saved_by_atr_sl": sim["mae_pips"] < sim["sl_dist_pips"],  # MAE が ATR×1.5 以内なら救済
                "sim_hit_event": sim["hit_event"],
                "sim_hit_time": sim["hit_time"],
                "sim_hit_price": round(sim["hit_price"], 5),
                "sim_pl_pips": round(sim["sim_pl_pips"], 2),
                "sim_pl_jpy": round(sim_pl_jpy, 1),
                "improvement_jpy": round(sim_pl_jpy - actual_pl_jpy, 1),
            }
            rows.append(row)

        # CSV風テーブル出力
        df = pd.DataFrame(rows)
        print("\n=== 結果テーブル ===")
        with pd.option_context("display.max_columns", None, "display.width", 240):
            print(df.to_string(index=False))

        # CSV保存
        csv_path = "C:/bpr_lab/sandbox/FX自動取引/data/atr_analysis_USD_JPY_7trades.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n[CSV saved] {csv_path}")

        # 集計サマリ
        loss_trades = df[df["actual_pl_jpy"] < 0]
        win_trades = df[df["actual_pl_jpy"] > 0]
        saved_count = int(loss_trades["saved_by_atr_sl"].sum())
        print(f"\n=== 集計サマリ ===")
        print(f"全7取引 / 負け{len(loss_trades)}件 / 勝ち{len(win_trades)}件")
        print(f"負けのうち「ATR×1.5 SL なら MAE 内に収まり救えた」件数: {saved_count}/{len(loss_trades)}")
        print(f"  （MAE < ATR×1.5 SL幅 だった = SLヒットせず保有継続できた）")

        # 4/21の3件は同時刻バンドル
        bundle_421 = df[df["id"].isin([3, 10, 15])]
        non_bundle = df[~df["id"].isin([3, 10, 15])]
        print(f"\n=== 4/21バンドル (id=3,10,15) ===")
        print(f"  実損益合計: {bundle_421['actual_pl_jpy'].sum()} JPY")
        print(f"  仮想損益合計: {bundle_421['sim_pl_jpy'].sum():.1f} JPY")
        print(f"  改善: {bundle_421['improvement_jpy'].sum():.1f} JPY")
        print(f"  ※同時刻発注=実質1セット")

        print(f"\n=== その他4取引 (id=19,29,35,40) ===")
        for _, r in non_bundle.iterrows():
            print(f"  id={r['id']} actual={r['actual_pl_jpy']:+} sim={r['sim_pl_jpy']:+.1f} (event={r['sim_hit_event']}) improvement={r['improvement_jpy']:+.1f}")
        print(f"  実損益合計: {non_bundle['actual_pl_jpy'].sum()} JPY")
        print(f"  仮想損益合計: {non_bundle['sim_pl_jpy'].sum():.1f} JPY")
        print(f"  改善: {non_bundle['improvement_jpy'].sum():.1f} JPY")

        print(f"\n=== 全体 (バンドル1セット扱い: id=15を代表値, 他4件) ===")
        bundle_rep = df[df["id"] == 15].iloc[0]
        whole = pd.concat([pd.DataFrame([bundle_rep]), non_bundle])
        print(f"  実損益合計（バンドル合算）: {bundle_421['actual_pl_jpy'].sum() + non_bundle['actual_pl_jpy'].sum()} JPY")
        print(f"  仮想損益合計（バンドル合算）: {bundle_421['sim_pl_jpy'].sum() + non_bundle['sim_pl_jpy'].sum():.1f} JPY")

        # JSONも出す
        json_path = "C:/bpr_lab/sandbox/FX自動取引/data/atr_analysis_USD_JPY_7trades.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2, default=str)
        print(f"[JSON saved] {json_path}")

    finally:
        mt5.shutdown()

    print("\n[DONE]")


if __name__ == "__main__":
    main()
