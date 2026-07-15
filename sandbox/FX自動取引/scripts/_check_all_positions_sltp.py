# 全5取引のMT5注文SL/TP有無と決済理由を確認（VPS上で実行）
import json
from datetime import datetime, timezone

import MetaTrader5 as mt5

POSITIONS = [10188884, 10202563, 10203119, 10203848, 10205081]

if not mt5.initialize():
    print(json.dumps({"error": f"mt5.initialize failed: {mt5.last_error()}"}))
    raise SystemExit(1)

date_from = datetime(2026, 6, 6, tzinfo=timezone.utc)
date_to = datetime(2026, 6, 11, tzinfo=timezone.utc)

orders = mt5.history_orders_get(date_from, date_to) or []
deals = mt5.history_deals_get(date_from, date_to) or []

out = {}
for pid in POSITIONS:
    out[str(pid)] = {
        "orders": [
            {"ticket": o.ticket, "type": o.type, "sl": o.sl, "tp": o.tp,
             "reason": o.reason,
             "time": str(datetime.fromtimestamp(o.time_setup, tz=timezone.utc))}
            for o in orders if o.position_id == pid
        ],
        "deals": [
            {"entry": d.entry, "price": d.price, "profit": d.profit,
             "reason": d.reason,
             "time": str(datetime.fromtimestamp(d.time, tz=timezone.utc))}
            for d in deals if d.position_id == pid
        ],
    }

out["open_positions_now"] = len(mt5.positions_get() or [])
acc = mt5.account_info()
out["account"] = {"balance": acc.balance, "equity": acc.equity} if acc else None

mt5.shutdown()
print(json.dumps(out, ensure_ascii=False))
