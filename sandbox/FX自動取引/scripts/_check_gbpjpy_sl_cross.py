# 取引1の保有期間中にGBPJPYがSL水準213.535をいつ越えたか確認（VPS上で実行）
import json
from datetime import datetime, timezone

import MetaTrader5 as mt5

if not mt5.initialize():
    print(json.dumps({"error": str(mt5.last_error())}))
    raise SystemExit(1)

# MT5サーバ時刻 (UTC+3扱い) で entry=2026-06-08 00:34 〜 exit=2026-06-09 00:35
date_from = datetime(2026, 6, 8, 0, 30, tzinfo=timezone.utc)
date_to = datetime(2026, 6, 9, 1, 0, tzinfo=timezone.utc)

rates = mt5.copy_rates_range("GBPJPY", mt5.TIMEFRAME_M15, date_from, date_to)
SL = 213.535

out = {"n_bars": 0 if rates is None else len(rates), "first_cross": None, "max_high": None}
if rates is not None and len(rates):
    out["max_high"] = float(max(r["high"] for r in rates))
    for r in rates:
        if r["high"] >= SL:
            out["first_cross"] = str(datetime.fromtimestamp(int(r["time"]), tz=timezone.utc))
            out["cross_high"] = float(r["high"])
            break

mt5.shutdown()
print(json.dumps(out))
