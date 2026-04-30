"""口座・ポジション・シンボル情報ダンプ（デバッグ用）"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from datetime import datetime, timedelta

import MetaTrader5 as mt5

mt5.initialize()
acc = mt5.account_info()
print(f"balance={acc.balance}, equity={acc.equity}, margin={acc.margin}, "
      f"free_margin={acc.margin_free}, leverage={acc.leverage}")

positions = mt5.positions_get() or []
print(f"positions={len(positions)}")
for p in positions:
    print(f"  ticket={p.ticket} {p.symbol} vol={p.volume} "
          f"type={p.type} profit={p.profit}")

# 過去24時間の約定履歴（読み取り専用API）
to_date = datetime.now()
from_date = to_date - timedelta(hours=24)
deals = mt5.history_deals_get(from_date, to_date) or []
print(f"\n--- 過去24h deals: {len(deals)}件 ---")
pos_groups = {}
for d in deals:
    pos_groups.setdefault(d.position_id, []).append(d)
for pid, group in sorted(pos_groups.items()):
    group.sort(key=lambda x: x.time)
    total = sum(d.profit for d in group)
    first = group[0]
    last = group[-1]
    t1 = datetime.fromtimestamp(first.time).strftime("%m-%d %H:%M")
    t2 = datetime.fromtimestamp(last.time).strftime("%m-%d %H:%M")
    type_str = "BUY" if first.type == 0 else "SELL"
    print(f" pos={pid} {first.symbol} {type_str} "
          f"open={t1} close={t2} "
          f"open_price={first.price} close_price={last.price} "
          f"profit={total:+.2f} comment='{last.comment}'")

for sym in ["AUDUSD-", "USDJPY-", "EURUSD-"]:
    info = mt5.symbol_info(sym)
    if info is None:
        print(f"{sym}: NOT FOUND")
        continue
    print(f"{sym}: volume_min={info.volume_min} "
          f"volume_step={info.volume_step} "
          f"volume_max={info.volume_max} "
          f"trade_mode={info.trade_mode} "
          f"filling_mode={info.filling_mode} "
          f"margin_initial={getattr(info, 'margin_initial', None)}")

mt5.shutdown()
