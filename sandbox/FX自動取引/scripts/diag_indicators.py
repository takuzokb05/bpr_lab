"""現在の各ペアの主要指標ダンプ（シグナル発火条件の近接度を見る）"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta

mt5.initialize()
pairs = [
    ("EUR_USD", "EURUSD-"),
    ("USD_JPY", "USDJPY-"),
    ("GBP_JPY", "GBPJPY-"),
]
for name, symbol in pairs:
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 300)
    if rates is None:
        print(f"{name}: データなし")
        continue
    df = pd.DataFrame(rates)
    close = df["close"]
    high = df["high"]
    low = df["low"]

    # 指標
    ma200 = ta.sma(close, length=200)
    rsi = ta.rsi(close, length=14)
    bb = ta.bbands(close, length=20, std=2.0)
    atr = ta.atr(high, low, close, length=14)
    adx_df = ta.adx(high, low, close, length=14)

    c = close.iloc[-1]
    m = ma200.iloc[-1]
    r = rsi.iloc[-1]
    bu = [col for col in bb.columns if col.startswith("BBU_")][0]
    bl = [col for col in bb.columns if col.startswith("BBL_")][0]
    a = adx_df[f"ADX_{14}"].iloc[-1]
    atv = atr.iloc[-1]

    print(f"\n[{name}] close={c:.5f} MA200={m:.5f} ({'>' if c>m else '<'}MA200)")
    print(f"  RSI={r:.1f}  ADX={a:.1f}  ATR={atv:.5f}")
    print(f"  BBU={bb[bu].iloc[-1]:.5f}  BBL={bb[bl].iloc[-1]:.5f}")
    # MTFPullback条件
    if c > m:
        need_rsi = 35
        dist = need_rsi - r
        print(f"  MTFPullback(BUY): 上昇トレンドYES、RSI<{need_rsi}必要 "
              f"(現{r:.1f}, {'発火' if r<need_rsi else f'あと{dist:.1f}下落'})")
    else:
        need_rsi = 65
        dist = r - need_rsi
        print(f"  MTFPullback(SELL): 下降トレンドYES、RSI>{need_rsi}必要 "
              f"(現{r:.1f}, {'発火' if r>need_rsi else f'あと{dist:.1f}上昇'})")
    # BollingerReversal条件 (GBP_JPYのみ)
    if name == "GBP_JPY":
        dist_u = bb[bu].iloc[-1] - c
        dist_l = c - bb[bl].iloc[-1]
        print(f"  BBReversal: BBU-close={dist_u:.3f}, close-BBL={dist_l:.3f}")
        print(f"    → SELL条件: close>=BBU({bb[bu].iloc[-1]:.3f}) AND RSI>=70")
        print(f"    → BUY条件:  close<={bb[bl].iloc[-1]:.3f} AND RSI<=30")

mt5.shutdown()
