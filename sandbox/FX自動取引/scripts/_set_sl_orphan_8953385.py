"""orphan position 8953385 に SL/TP を後付け設定。

土日（市場クローズ）でも TRADE_ACTION_SLTP は通ることが多い。
SL=158.875 (entry-100pips, 追加損失上限 -2000 JPY × 0.02 lot = -2000 JPY程度)
TP=161.000 (entry+112pips, 利益確定枠)

クローズは月曜の市場オープン直後に別途実施。
"""
import sqlite3
import sys
from datetime import datetime, timezone

import MetaTrader5 as mt5

TICKET = 8953385
SYMBOL = "USDJPY-"
DB_PATH = r"C:\bpr_lab\sandbox\FX自動取引\data\fx_trading.db"

# entry=159.875 から
NEW_SL = 158.875  # -100 pips (追加損失上限 ≈ 0.02 lot × 1000 pips × 0.001 ≈ 2,000 JPY)
NEW_TP = 161.000  # +112 pips


def main() -> int:
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}", file=sys.stderr)
        return 1

    try:
        positions = mt5.positions_get(ticket=TICKET)
        if not positions:
            print(f"position {TICKET} は MT5 に存在しない")
            return 2
        position = positions[0]
        print(f"=== Before SL/TP ===")
        print(f"  sl={position.sl}, tp={position.tp}")
        print(f"  profit={position.profit}, swap={position.swap}")

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": SYMBOL,
            "position": TICKET,
            "sl": NEW_SL,
            "tp": NEW_TP,
        }

        result = mt5.order_send(request)
        if result is None:
            print(f"order_send returned None: {mt5.last_error()}", file=sys.stderr)
            return 3
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"order_send failed: retcode={result.retcode}, comment={result.comment}",
                  file=sys.stderr)
            return 4

        print(f"\n=== SL/TP set ===")
        print(f"  result.comment={result.comment}")

        # 確認
        positions = mt5.positions_get(ticket=TICKET)
        if positions:
            position = positions[0]
            print(f"\n=== After SL/TP ===")
            print(f"  sl={position.sl}, tp={position.tp}")

        # DB 同期
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "UPDATE trades SET stop_loss=?, take_profit=? WHERE trade_id=?",
                (NEW_SL, NEW_TP, str(TICKET)),
            )
            cur = conn.execute(
                "SELECT stop_loss, take_profit FROM trades WHERE trade_id=?",
                (str(TICKET),),
            )
            row = cur.fetchone()
            print(f"\n=== DB updated ===")
            print(f"  stop_loss={row[0]}, take_profit={row[1]}")

        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())
