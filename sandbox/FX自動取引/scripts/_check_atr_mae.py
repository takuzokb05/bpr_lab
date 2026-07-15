"""USD_JPY 7取引のATR・MAE・ATR×1.5 SLシミュレーション + 最適エントリー逆引き"""
import sys
import json
from datetime import datetime, timezone, timedelta

import MetaTrader5 as mt5
import pandas as pd

# MT5 ターミナル既ログイン前提
if not mt5.initialize():
    print(f"MT5 init failed: {mt5.last_error()}")
    sys.exit(1)

SYMBOL = 'USDJPY-'
PIP = 0.01

trades = [
    # (id, side, open_time_utc, close_time_utc, open_price, sl, close_price, pl)
    (3,  'BUY',  '2026-04-21T10:06:57', '2026-04-21T13:54:36', 159.210, 159.064, 159.193, -119),
    (10, 'BUY',  '2026-04-21T10:18:45', '2026-04-21T13:54:37', 159.216, 159.079, 159.193, -161),
    (15, 'BUY',  '2026-04-21T10:21:00', '2026-04-21T13:54:38', 159.205, 159.068, 159.192, -91),
    (19, 'BUY',  '2026-04-22T05:30:59', '2026-04-22T18:16:26', 159.145, 159.022, 159.424, +837),
    (29, 'BUY',  '2026-04-23T11:54:32', '2026-04-23T17:49:14', 159.518, 159.384, 159.382, -408),
    (35, 'BUY',  '2026-04-24T11:05:05', '2026-04-24T14:21:45', 159.601, 159.477, 159.474, -508),
    (40, 'SELL', '2026-04-27T16:54:15', '2026-04-28T04:01:18', 159.372, 159.512, 159.512, -469),
]


def get_m15(symbol, start, end):
    """M15 rates between start and end (UTC datetime)"""
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M15, start, end)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df


def calc_atr(df, period=14):
    """Wilder's ATR"""
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()


def calc_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_macd(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal, macd - signal


def calc_bb(close, period=20, k=2):
    ma = close.rolling(period).mean()
    sd = close.rolling(period).std()
    return ma + k*sd, ma, ma - k*sd


def calc_adx(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    plus_dm[(plus_dm - minus_dm) < 0] = 0
    minus_dm[minus_dm < 0] = 0
    minus_dm[(minus_dm - plus_dm) < 0] = 0
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.ewm(alpha=1/period, adjust=False).mean()


def parse_dt(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


print('=' * 100)
print('USD_JPY 7取引: ATR/MAE/ATR×1.5 SLシミュレーション')
print('=' * 100)

results_atr = []
results_optimal = []

for tid, side, open_str, close_str, op, sl, cp, pl in trades:
    open_dt = parse_dt(open_str)
    close_dt = parse_dt(close_str)

    # 過去64本のM15でATR計算
    pre_start = open_dt - timedelta(hours=20)
    df_pre = get_m15(SYMBOL, pre_start, open_dt + timedelta(minutes=15))
    if df_pre is None or len(df_pre) < 16:
        print(f"#{tid}: M15データ取得失敗 (件数={0 if df_pre is None else len(df_pre)})")
        continue
    atr = calc_atr(df_pre, 14)
    atr_at_open = atr.iloc[-1]
    atr_pips = atr_at_open / PIP

    # 実際のSL幅
    actual_sl_pips = abs(op - sl) / PIP

    # ATR×1.5 SL
    atr15_sl_pips = atr_pips * 1.5
    atr15_sl_price = op - atr15_sl_pips * PIP if side == 'BUY' else op + atr15_sl_pips * PIP

    # 保有期間中のM15データ
    df_hold = get_m15(SYMBOL, open_dt, close_dt + timedelta(minutes=15))
    if df_hold is None or len(df_hold) == 0:
        print(f"#{tid}: 保有期間データ取得失敗")
        continue

    # MAE (最大不利変動)
    if side == 'BUY':
        mae_price = df_hold['low'].min()
        mae_pips = (op - mae_price) / PIP  # 正の数=逆行
        mfe_price = df_hold['high'].max()
        mfe_pips = (mfe_price - op) / PIP  # 正の数=順行
    else:
        mae_price = df_hold['high'].max()
        mae_pips = (mae_price - op) / PIP
        mfe_price = df_hold['low'].min()
        mfe_pips = (op - mfe_price) / PIP

    # ATR×1.5 SLヒットしたか
    if side == 'BUY':
        atr15_hit = (df_hold['low'].min() <= atr15_sl_price)
    else:
        atr15_hit = (df_hold['high'].max() >= atr15_sl_price)

    # ATR×1.0 TP1, ATR×3.0 TP2
    tp1_price = op + atr_pips*1.0*PIP if side == 'BUY' else op - atr_pips*1.0*PIP
    tp2_price = op + atr_pips*3.0*PIP if side == 'BUY' else op - atr_pips*3.0*PIP
    if side == 'BUY':
        tp1_hit = (df_hold['high'].max() >= tp1_price)
        tp2_hit = (df_hold['high'].max() >= tp2_price)
    else:
        tp1_hit = (df_hold['low'].min() <= tp1_price)
        tp2_hit = (df_hold['low'].min() <= tp2_price)

    # シミュレーション結果サマリ
    if atr15_hit:
        sim_outcome = 'ATR×1.5 SLヒット → 同等の負け'
    elif tp1_hit and tp2_hit:
        sim_outcome = 'TP1+TP2両ヒット → 大勝'
    elif tp1_hit:
        sim_outcome = 'TP1のみヒット(部分利確) → 小勝or引き分け'
    else:
        sim_outcome = '保有期間内に決済条件未到達 → 期間延長必要'

    results_atr.append({
        'id': tid, 'side': side, 'pl': pl,
        'atr_pips': round(atr_pips, 1),
        'actual_sl_pips': round(actual_sl_pips, 1),
        'atr15_sl_pips': round(atr15_sl_pips, 1),
        'mae_pips': round(mae_pips, 1),
        'mfe_pips': round(mfe_pips, 1),
        'atr15_sl_hit': atr15_hit,
        'tp1_hit': tp1_hit,
        'tp2_hit': tp2_hit,
        'sim_outcome': sim_outcome,
    })

    # === 最適エントリー逆引き ===
    win_start = open_dt - timedelta(hours=12)
    win_end = open_dt + timedelta(hours=12)
    df_win = get_m15(SYMBOL, win_start, win_end)
    if df_win is not None and len(df_win) > 50:
        # 200本程度先まで取得して指標計算用
        df_win['rsi'] = calc_rsi(df_win['close'], 14)
        df_win['macd'], df_win['macd_sig'], df_win['macd_hist'] = calc_macd(df_win['close'])
        df_win['bb_u'], df_win['bb_m'], df_win['bb_l'] = calc_bb(df_win['close'])
        df_win['adx'] = calc_adx(df_win, 14)
        if len(df_win) >= 200:
            df_win['ma200'] = df_win['close'].rolling(200).mean()
        else:
            df_win['ma200'] = df_win['close'].rolling(min(50, len(df_win))).mean()

        if side == 'BUY':
            # 期間内の最安値M15足
            opt_idx = df_win['low'].idxmin()
            opt_price = df_win.loc[opt_idx, 'low']
            opp_loss_pips = (op - opt_price) / PIP
        else:
            opt_idx = df_win['high'].idxmax()
            opt_price = df_win.loc[opt_idx, 'high']
            opp_loss_pips = (opt_price - op) / PIP

        opt_row = df_win.loc[opt_idx]
        results_optimal.append({
            'id': tid, 'side': side,
            'actual_open': op, 'actual_open_time': open_dt,
            'optimal_price': round(opt_price, 3),
            'optimal_time': opt_row['time'],
            'opportunity_loss_pips': round(opp_loss_pips, 1),
            'opt_rsi': round(opt_row['rsi'], 1),
            'opt_macd_hist': round(opt_row['macd_hist'], 5),
            'opt_adx': round(opt_row['adx'], 1),
            'opt_bb_pos': 'lower' if opt_row['low'] <= opt_row['bb_l'] else ('upper' if opt_row['high'] >= opt_row['bb_u'] else 'middle'),
            'opt_vs_ma200': round((opt_price - opt_row['ma200']) / PIP, 1),
        })

# 結果出力
print('\n=== ATR/MAE/シミュレーション結果 ===')
print(f"{'id':<4}{'side':<6}{'pl':<8}{'ATR pips':<10}{'実SL pips':<12}{'ATR×1.5 pips':<14}{'MAE pips':<11}{'MFE pips':<11}{'ATR×1.5でも切られた':<22}{'結果'}")
for r in results_atr:
    print(f"{r['id']:<4}{r['side']:<6}{r['pl']:<+8}{r['atr_pips']:<10}{r['actual_sl_pips']:<12}{r['atr15_sl_pips']:<14}{r['mae_pips']:<11}{r['mfe_pips']:<11}{('YES' if r['atr15_sl_hit'] else 'NO'):<22}{r['sim_outcome']}")

# サマリ
n = len(results_atr)
saved = sum(1 for r in results_atr if (not r['atr15_sl_hit']) and r['pl'] < 0)
worse = sum(1 for r in results_atr if r['atr15_sl_hit'] and r['pl'] < 0)
neutral_or_better = sum(1 for r in results_atr if r['pl'] > 0)
print(f"\n--- サマリ ---")
print(f"総数: {n}件")
print(f"負け取引: {sum(1 for r in results_atr if r['pl']<0)}件")
print(f"  ATR×1.5 SLでも切られた: {worse}件")
print(f"  ATR×1.5 SLなら救えた: {saved}件")

# 最適エントリー結果
print('\n=== 最適エントリー逆引き (±12h窓) ===')
print(f"{'id':<4}{'side':<6}{'実open':<10}{'実時刻':<22}{'最適価格':<10}{'最適時刻':<22}{'機会損失pips':<14}{'opt_RSI':<10}{'opt_MACDh':<12}{'opt_ADX':<10}{'BB位置':<10}{'MA200距離pips'}")
for r in results_optimal:
    print(f"{r['id']:<4}{r['side']:<6}{r['actual_open']:<10}{str(r['actual_open_time'])[:19]:<22}{r['optimal_price']:<10}{str(r['optimal_time'])[:19]:<22}{r['opportunity_loss_pips']:<+14}{r['opt_rsi']:<10}{r['opt_macd_hist']:<+12}{r['opt_adx']:<10}{r['opt_bb_pos']:<10}{r['opt_vs_ma200']:+}")

# 実エントリー時の指標 (比較用)
print('\n=== 実エントリー時の指標（参考） ===')
for tid, side, open_str, close_str, op, sl, cp, pl in trades:
    open_dt = parse_dt(open_str)
    df = get_m15(SYMBOL, open_dt - timedelta(hours=60), open_dt + timedelta(minutes=15))
    if df is None or len(df) < 30:
        continue
    df['rsi'] = calc_rsi(df['close'], 14)
    df['macd'], df['macd_sig'], df['macd_hist'] = calc_macd(df['close'])
    df['bb_u'], df['bb_m'], df['bb_l'] = calc_bb(df['close'])
    df['adx'] = calc_adx(df, 14)
    if len(df) >= 200:
        df['ma200'] = df['close'].rolling(200).mean()
    else:
        df['ma200'] = df['close'].rolling(min(50, len(df))).mean()
    last = df.iloc[-1]
    bb_pos = 'lower' if last['low'] <= last['bb_l'] else ('upper' if last['high'] >= last['bb_u'] else 'middle')
    ma_dist = (op - last['ma200']) / PIP
    print(f"#{tid} {side} pl={pl:+}: RSI={last['rsi']:.1f} MACDh={last['macd_hist']:+.5f} ADX={last['adx']:.1f} BB={bb_pos} MA200距離={ma_dist:+.1f}pips")

mt5.shutdown()
