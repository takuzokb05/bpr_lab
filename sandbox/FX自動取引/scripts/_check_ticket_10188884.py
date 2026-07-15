# ticket 10188884 のMT5注文・約定履歴を確認（VPS上で実行）
import json
from datetime import datetime, timezone

import MetaTrader5 as mt5

if not mt5.initialize():
    print(json.dumps({"error": f"mt5.initialize failed: {mt5.last_error()}"}))
    raise SystemExit(1)

date_from = datetime(2026, 6, 7, tzinfo=timezone.utc)
date_to = datetime(2026, 6, 10, tzinfo=timezone.utc)

out = {}

# position_id でフィルタ（position= キーワードは効かない環境があるため手動フィルタ）
orders = mt5.history_orders_get(date_from, date_to) or []
out["orders"] = [
    {
        "ticket": o.ticket, "position_id": o.position_id, "type": o.type,
        "state": o.state, "sl": o.sl, "tp": o.tp,
        "price_open": o.price_open, "volume": o.volume_initial,
        "time_setup": str(datetime.fromtimestamp(o.time_setup, tz=timezone.utc)),
        "comment": o.comment, "reason": o.reason,
    }
    for o in orders if o.position_id == 10188884
]

deals = mt5.history_deals_get(date_from, date_to) or []
out["deals"] = [
    {
        "ticket": d.ticket, "position_id": d.position_id, "type": d.type,
        "entry": d.entry, "price": d.price, "volume": d.volume,
        "profit": d.profit, "time": str(datetime.fromtimestamp(d.time, tz=timezone.utc)),
        "comment": d.comment, "reason": d.reason,
    }
    for d in deals if d.position_id == 10188884
]

mt5.shutdown()
print(json.dumps(out, ensure_ascii=False))
