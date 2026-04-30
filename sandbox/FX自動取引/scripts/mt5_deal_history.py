"""MT5から過去24時間の約定履歴（entry/exit）を取得してダンプ"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from datetime import datetime, timedelta

import MetaTrader5 as mt5

mt5.initialize()

# 過去24時間
to_date = datetime.now()
from_date = to_date - timedelta(hours=24)
deals = mt5.history_deals_get(from_date, to_date)

if deals is None or len(deals) == 0:
    print("過去24時間の約定履歴なし")
else:
    print(f"過去24時間の約定: {len(deals)}件")
    # position_id でグループ化
    positions = {}
    for d in deals:
        pid = d.position_id
        if pid not in positions:
            positions[pid] = []
        positions[pid].append(d)

    for pid, group in sorted(positions.items()):
        print(f"\n position_id={pid}")
        total_profit = 0.0
        for d in sorted(group, key=lambda x: x.time):
            t = datetime.fromtimestamp(d.time)
            # entry: 0=IN, 1=OUT, 2=INOUT, 3=OUT_BY
            entry_map = {0: "IN ", 1: "OUT", 2: "I/O", 3: "O/B"}
            entry_str = entry_map.get(d.entry, f"?{d.entry}")
            # type: 0=BUY, 1=SELL
            type_str = "BUY " if d.type == 0 else "SELL"
            total_profit += d.profit
            print(f"   {t} {entry_str} {type_str} {d.symbol} "
                  f"vol={d.volume} price={d.price} "
                  f"profit={d.profit} commission={d.commission} "
                  f"comment='{d.comment}'")
        print(f"   → position_total_profit={total_profit}")

mt5.shutdown()
