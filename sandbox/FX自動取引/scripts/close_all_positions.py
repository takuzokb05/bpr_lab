"""全ポジション手動決済（デモ口座リセット用）"""
import MetaTrader5 as mt5

mt5.initialize()
positions = mt5.positions_get() or []
print(f"保有ポジション: {len(positions)}件")

total_pl = 0.0
for p in positions:
    tick = mt5.symbol_info_tick(p.symbol)
    if p.type == 0:
        close_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        close_type = mt5.ORDER_TYPE_BUY
        price = tick.ask

    for filling in (mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK,
                    mt5.ORDER_FILLING_RETURN):
        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": p.symbol,
            "volume": p.volume,
            "type": close_type,
            "price": price,
            "position": p.ticket,
            "type_filling": filling,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        result = mt5.order_send(req)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            total_pl += p.profit
            print(f"  ok ticket={p.ticket} {p.symbol} vol={p.volume} "
                  f"profit={p.profit}")
            break
    else:
        print(f"  NG ticket={p.ticket} {p.symbol}: "
              f"retcode={result.retcode} comment={result.comment}")

acc = mt5.account_info()
print(f"\n全決済 total_pl={total_pl:.2f}")
print(f"balance={acc.balance} equity={acc.equity} "
      f"margin={acc.margin} free_margin={acc.margin_free}")
mt5.shutdown()
