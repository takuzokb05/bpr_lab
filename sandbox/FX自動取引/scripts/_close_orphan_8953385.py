"""orphan position 8953385 (USD_JPY, BUY 0.02 lot @159.875) を精算してDBを同期。

- MT5 で TRADE_ACTION_DEAL (ORDER_TYPE_SELL, position=8953385) を発注
- 約定後に history_deals_get で実 close_price と pl を取得
- DB の trades.id=59 を status='closed' に更新

実行: ssh vps 経由で system Python から
"""
import sqlite3
import sys
from datetime import datetime, timezone

import MetaTrader5 as mt5

TICKET = 8953385
SYMBOL = "USDJPY-"
DB_PATH = r"C:\bpr_lab\sandbox\FX自動取引\data\fx_trading.db"


def main() -> int:
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}", file=sys.stderr)
        return 1

    try:
        # 1. 現状確認
        positions = mt5.positions_get(ticket=TICKET)
        if not positions:
            print(f"position {TICKET} は既にMT5上に存在しない（決済済みの可能性）")
            # DBチェックは継続
            position = None
        else:
            position = positions[0]
            print(f"=== Before close ===")
            print(f"  ticket={position.ticket}, symbol={position.symbol}")
            print(f"  type={position.type} (0=BUY, 1=SELL)")
            print(f"  volume={position.volume}, price_open={position.price_open}")
            print(f"  sl={position.sl}, tp={position.tp}")
            print(f"  profit={position.profit}, swap={position.swap}")

        # 2. クローズ発注（MT5に存在する場合のみ）
        if position is not None:
            tick = mt5.symbol_info_tick(SYMBOL)
            if tick is None:
                print(f"tick not available for {SYMBOL}", file=sys.stderr)
                return 2

            # BUY (type=0) を閉じるには SELL を発注
            order_type = mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY
            close_price_market = tick.bid if position.type == 0 else tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": position.volume,
                "type": order_type,
                "position": TICKET,
                "price": close_price_market,
                "deviation": 20,
                "type_time": mt5.ORDER_TIME_GTC,
                "comment": "manual_close_orphan_8953385",
            }

            # symbol_info().filling_mode のビットマスクで対応モードを判定
            info = mt5.symbol_info(SYMBOL)
            candidates = []
            if info is not None:
                fm = info.filling_mode
                if fm & 1:
                    candidates.append(mt5.ORDER_FILLING_FOK)
                if fm & 2:
                    candidates.append(mt5.ORDER_FILLING_IOC)
            candidates.append(mt5.ORDER_FILLING_RETURN)

            result = None
            attempted = []
            for filling in candidates:
                request["type_filling"] = filling
                # まずorder_checkで事前検証
                chk = mt5.order_check(request)
                if chk is None or chk.retcode != 0:
                    attempted.append(f"filling={filling} order_check retcode={chk.retcode if chk else 'None'}")
                    continue
                result = mt5.order_send(request)
                if result is not None and result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"  filling={filling} → OK")
                    break
                attempted.append(f"filling={filling} order_send retcode={result.retcode if result else 'None'} comment={result.comment if result else ''}")

            if result is None:
                print(f"order_send returned None: {mt5.last_error()}", file=sys.stderr)
                return 3
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"order_send failed: retcode={result.retcode}, "
                      f"comment={result.comment}", file=sys.stderr)
                return 4

            print(f"\n=== Close order filled ===")
            print(f"  result.order={result.order}, deal={result.deal}")
            print(f"  filling={request['type_filling']}, price={result.price}")
            print(f"  comment={result.comment}")

        # 3. 履歴から実PL取得
        # 直近10分の deals から position_id=TICKET を手動フィルタ
        # （PR #4 で確認済み: position= キーワードフィルタはVPS環境で機能しない）
        from_date = datetime.now(timezone.utc).replace(microsecond=0)
        from datetime import timedelta as _td
        from_date = from_date - _td(minutes=10)
        to_date = datetime.now(timezone.utc) + _td(minutes=1)
        all_deals = mt5.history_deals_get(from_date, to_date) or []

        my_deals = [d for d in all_deals if d.position_id == TICKET]
        # OUT (entry=1) の deal を取る
        close_deals = [d for d in my_deals if d.entry == 1]

        if not close_deals:
            print(f"\n[WARN] history_deals に position_id={TICKET} の OUT deal が見つからない")
            print("DB更新はスキップ。手動で確認してください。")
            return 5

        last_close = max(close_deals, key=lambda d: d.time)
        close_price = float(last_close.price)
        realized_pl = float(last_close.profit) + float(last_close.swap or 0.0) + float(last_close.commission or 0.0)
        closed_at = datetime.fromtimestamp(int(last_close.time), tz=timezone.utc)

        print(f"\n=== History deal (OUT) ===")
        print(f"  time={closed_at.isoformat()}")
        print(f"  price={close_price}")
        print(f"  profit={last_close.profit}, swap={last_close.swap}, "
              f"commission={last_close.commission}")
        print(f"  realized_pl={realized_pl}")

        # 4. DB更新
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                "SELECT id, trade_id, status, pl, close_price FROM trades WHERE trade_id=?",
                (str(TICKET),),
            )
            row = cur.fetchone()
            if row is None:
                print(f"\n[WARN] DB に trade_id={TICKET} が存在しない")
                return 6
            db_id, db_trade_id, db_status, db_pl, db_close_price = row
            print(f"\n=== DB before update ===")
            print(f"  id={db_id}, trade_id={db_trade_id}, status={db_status}")
            print(f"  pl={db_pl}, close_price={db_close_price}")

            conn.execute(
                """UPDATE trades
                   SET status='closed',
                       close_price=?,
                       pl=?,
                       closed_at=?
                   WHERE trade_id=?""",
                (close_price, realized_pl, closed_at.isoformat(), str(TICKET)),
            )

            cur = conn.execute(
                "SELECT status, pl, close_price, closed_at FROM trades WHERE trade_id=?",
                (str(TICKET),),
            )
            row = cur.fetchone()
            print(f"\n=== DB after update ===")
            print(f"  status={row[0]}, pl={row[1]}, close_price={row[2]}, closed_at={row[3]}")

        print(f"\n=== Done ===")
        return 0

    finally:
        mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())
