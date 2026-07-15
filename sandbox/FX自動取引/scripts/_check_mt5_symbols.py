"""MT5 接続テスト + 必要シンボルの利用可能性確認"""
import MetaTrader5 as mt5

ok = mt5.initialize()
print("initialize:", ok)
if not ok:
    print("error:", mt5.last_error())
    raise SystemExit(1)

syms = ["EURUSD-", "GBPUSD-", "AUDUSD-", "NZDUSD-", "USDCHF-", "USDCAD-", "USDJPY-"]
for s in syms:
    info = mt5.symbol_info(s)
    if info:
        print(f"{s}: found, spread={info.spread}, point={info.point}, digits={info.digits}")
    else:
        print(f"{s}: NOT FOUND")

mt5.shutdown()
