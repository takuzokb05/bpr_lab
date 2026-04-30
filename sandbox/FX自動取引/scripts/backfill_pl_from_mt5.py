"""MT5の取引履歴から close_price=0, pl=0 で記録されたトレードを修復する。

PR #2 デプロイ前(〜2026-04-30 13:32 JST)に SL/TP自動決済された取引は
close_price=0.0, pl=0.0 で DB 保存される不具合があった。
本スクリプトは該当行に対し MT5 history_deals_get を呼んで
close_price / realized_pl / closed_at を復元する。

使い方: python scripts/backfill_pl_from_mt5.py [--dry-run]
"""
import argparse
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import MetaTrader5 as mt5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="DBを更新せず計画のみ表示")
    parser.add_argument("--db", default="data/fx_trading.db", help="DBパス")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return 1

    if not mt5.initialize():
        print(f"MT5初期化失敗: {mt5.last_error()}")
        return 1

    try:
        return run_backfill(db_path, dry_run=args.dry_run)
    finally:
        mt5.shutdown()


def run_backfill(db_path: Path, *, dry_run: bool) -> int:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # 対象: status='closed' なのに close_price=0 となっているもの
    rows = cur.execute(
        """SELECT id, trade_id, instrument, units, open_price, opened_at
           FROM trades
           WHERE status='closed' AND close_price=0 AND pl=0
           ORDER BY opened_at"""
    ).fetchall()

    if not rows:
        print("バックフィル対象なし（既に全件PL記録済み）")
        return 0

    print(f"バックフィル対象: {len(rows)}件")
    print()

    # MT5 history は時間範囲を要求。対象期間の最古〜最新+α でまとめて取る
    oldest = min(r["opened_at"] for r in rows)
    date_from = datetime.fromisoformat(oldest.replace("Z", "+00:00")) - timedelta(days=1)
    date_to = datetime.now(timezone.utc) + timedelta(days=1)

    # 全期間の deal を一括取得して position_id で手動フィルタする
    # （MT5 Python API の position= キーワードはバージョンによってフィルタが効かないため）
    all_deals = mt5.history_deals_get(date_from, date_to) or []
    deals_by_position: dict[int, list] = {}
    for d in all_deals:
        deals_by_position.setdefault(d.position_id, []).append(d)
    print(f"取得 deal 総数: {len(all_deals)} 件、 position 数: {len(deals_by_position)}")
    print()

    fixed = 0
    not_found = 0
    failed = 0

    for r in rows:
        trade_id = r["trade_id"]
        try:
            ticket = int(trade_id)
        except (TypeError, ValueError):
            print(f"  SKIP id={r['id']} trade_id={trade_id} (数値変換不可)")
            not_found += 1
            continue

        deals = deals_by_position.get(ticket, [])
        if not deals:
            print(f"  NOT_FOUND id={r['id']} trade_id={ticket} ({r['instrument']})")
            not_found += 1
            continue

        # OUT (1) または INOUT (2) を決済 deal とみなす
        close_deals = [d for d in deals if d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_INOUT)]
        if not close_deals:
            print(f"  NO_CLOSE id={r['id']} trade_id={ticket} (entry deal のみ)")
            not_found += 1
            continue

        realized_pl = sum(
            d.profit + getattr(d, "swap", 0.0) + getattr(d, "commission", 0.0)
            for d in close_deals
        )
        last_close = max(close_deals, key=lambda d: d.time)
        close_price = float(last_close.price)
        closed_at = datetime.fromtimestamp(last_close.time, tz=timezone.utc).isoformat()

        action = "DRY" if dry_run else "FIX"
        print(
            f"  {action} id={r['id']} trade_id={ticket} {r['instrument']} "
            f"units={r['units']} open={r['open_price']} → close={close_price} pl={realized_pl:.2f}"
        )

        if not dry_run:
            try:
                cur.execute(
                    "UPDATE trades SET close_price=?, pl=?, closed_at=? WHERE id=?",
                    (close_price, realized_pl, closed_at, r["id"]),
                )
                fixed += 1
            except Exception as e:
                print(f"    UPDATE FAILED: {e}")
                failed += 1
        else:
            fixed += 1

    if not dry_run:
        con.commit()
    con.close()

    print()
    print(f"=== サマリ ===")
    print(f"  対象      : {len(rows)} 件")
    print(f"  修復      : {fixed} 件 {'(dry-run)' if dry_run else ''}")
    print(f"  履歴未検出: {not_found} 件")
    print(f"  UPDATE失敗: {failed} 件")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
