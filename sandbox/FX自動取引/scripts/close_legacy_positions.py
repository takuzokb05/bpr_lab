"""検証前の残存大ロットポジションを手動決済（デモ口座用）"""
import MetaTrader5 as mt5

LEGACY_TICKETS = [8587819, 8587822]

mt5.initialize()
for ticket in LEGACY_TICKETS:
    positions = mt5.positions_get(ticket=ticket)
    if not positions:
        print(f"ticket={ticket}: not found (既に決済済みの可能性)")
        continue
    p = positions[0]
    tick = mt5.symbol_info_tick(p.symbol)
    # 買いポジション(type=0)はsell決済、売り(type=1)はbuy決済
    if p.type == 0:
        close_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        close_type = mt5.ORDER_TYPE_BUY
        price = tick.ask

    # filling mode: IOC(2)をデフォルトに試行、NG時にFOK(1)も試す
    for filling in (mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK,
                    mt5.ORDER_FILLING_RETURN):
        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": p.symbol,
            "volume": p.volume,
            "type": close_type,
            "price": price,
            "position": ticket,
            "type_filling": filling,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        result = mt5.order_send(req)
        print(f"ticket={ticket} {p.symbol} vol={p.volume} "
              f"filling={filling} retcode={result.retcode} "
              f"comment={result.comment}")
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"  → 決済成功: profit={p.profit}")
            break

acc = mt5.account_info()
print(f"\n決済後: balance={acc.balance} margin={acc.margin} "
      f"free_margin={acc.margin_free}")
mt5.shutdown()
