"""
READ-ONLY: ticket=8953385 の MT5 上の状態を確認する。
何も変更しない。
"""
import sys
import io
from datetime import datetime, timedelta, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import MetaTrader5 as mt5

TICKET = 8953385

if not mt5.initialize():
    print(f"[ERROR] mt5.initialize failed: {mt5.last_error()}")
    sys.exit(1)

try:
    info = mt5.account_info()
    if info:
        print(f"[ACCOUNT] login={info.login} server={info.server} balance={info.balance} equity={info.equity}")
    else:
        print(f"[ACCOUNT] account_info=None err={mt5.last_error()}")

    print(f"\n=== positions_get(ticket={TICKET}) ===")
    positions = mt5.positions_get(ticket=TICKET)
    if positions is None:
        print(f"  positions_get=None err={mt5.last_error()}")
    else:
        print(f"  hits={len(positions)}")
        for p in positions:
            print(f"  ticket={p.ticket} symbol={p.symbol} type={p.type} volume={p.volume}")
            print(f"  price_open={p.price_open} sl={p.sl} tp={p.tp}")
            print(f"  price_current={p.price_current} profit={p.profit} swap={p.swap}")
            print(f"  time(open)={datetime.fromtimestamp(p.time, tz=timezone.utc).isoformat()}")
            print(f"  comment={p.comment} magic={p.magic}")

    print(f"\n=== positions_get() (all open positions, just to enumerate) ===")
    all_pos = mt5.positions_get()
    if all_pos is None:
        print(f"  None err={mt5.last_error()}")
    else:
        print(f"  total open={len(all_pos)}")
        for p in all_pos[:50]:
            print(f"  - ticket={p.ticket} symbol={p.symbol} vol={p.volume} sl={p.sl} tp={p.tp} profit={p.profit}")

    print(f"\n=== history_deals_get(position={TICKET}) ===")
    # 広めに過去90日
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=90)
    deals = mt5.history_deals_get(date_from, date_to, position=TICKET)
    if deals is None:
        print(f"  history_deals_get=None err={mt5.last_error()}")
    else:
        print(f"  deals={len(deals)}")
        for d in deals:
            print(f"  - ticket={d.ticket} order={d.order} position_id={d.position_id} symbol={d.symbol}")
            print(f"    type={d.type} entry={d.entry} volume={d.volume} price={d.price} profit={d.profit}")
            print(f"    time={datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat()} comment={d.comment}")

    # 念のため history_deals_get(position=) フィルタが効かない既知バグもあったので
    # ticket フィールドベースでも確認
    print(f"\n=== history_deals_get(date range, manual filter for position_id={TICKET}) ===")
    deals_all = mt5.history_deals_get(date_from, date_to)
    if deals_all is None:
        print(f"  None err={mt5.last_error()}")
    else:
        matched = [d for d in deals_all if d.position_id == TICKET]
        print(f"  total deals in range={len(deals_all)}, matching position_id={TICKET}: {len(matched)}")
        for d in matched:
            print(f"  - ticket={d.ticket} order={d.order} position_id={d.position_id} entry={d.entry} type={d.type}")
            print(f"    price={d.price} profit={d.profit} time={datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat()}")
            print(f"    comment={d.comment}")

    # history_orders も見ておく
    print(f"\n=== history_orders_get(date range, manual filter for position_id={TICKET}) ===")
    orders = mt5.history_orders_get(date_from, date_to)
    if orders is None:
        print(f"  None err={mt5.last_error()}")
    else:
        matched_o = [o for o in orders if getattr(o, 'position_id', None) == TICKET]
        print(f"  total orders={len(orders)}, matching position_id={TICKET}: {len(matched_o)}")
        for o in matched_o:
            print(f"  - ticket={o.ticket} state={o.state} type={o.type} volume_init={o.volume_initial}")
            print(f"    price_open={o.price_open} sl={o.sl} tp={o.tp} time_setup={datetime.fromtimestamp(o.time_setup, tz=timezone.utc).isoformat()}")
            print(f"    time_done={datetime.fromtimestamp(o.time_done, tz=timezone.utc).isoformat() if o.time_done else 'N/A'}")
            print(f"    comment={o.comment}")

finally:
    mt5.shutdown()

print("\n[DONE]")
