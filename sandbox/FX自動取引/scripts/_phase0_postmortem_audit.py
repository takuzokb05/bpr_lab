"""Phase 0 調査: postmortem テーブルの実態を確認するワンショットスクリプト。

確認項目:
- テーブル一覧
- 各テーブルの件数
- 直近 postmortem の analysis_json 中身（parameter_suggestion の存在確認）
- 期間別の出現頻度
"""
import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fx_trading.db"


def main() -> None:
    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        return

    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    print("=" * 60)
    print("1. TABLES")
    print("=" * 60)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    for t in tables:
        print(f"  - {t}")

    print()
    print("=" * 60)
    print("2. ROW COUNTS")
    print("=" * 60)
    for t in ("trades", "trade_snapshots", "trade_postmortems",
              "kill_switch_log"):
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"  {t:30s}: {cur.fetchone()[0]}")
        except sqlite3.Error as e:
            print(f"  {t:30s}: NO TABLE ({e})")

    print()
    print("=" * 60)
    print("3. POSTMORTEM 直近30日の出現頻度")
    print("=" * 60)
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        cur.execute(
            "SELECT COUNT(*) FROM trade_postmortems WHERE created_at >= ?",
            (cutoff,),
        )
        recent = cur.fetchone()[0]
        print(f"  直近30日の postmortem 件数: {recent}")
    except sqlite3.Error as e:
        print(f"  ERR: {e}")

    print()
    print("=" * 60)
    print("4. 直近5件の analysis_json 構造")
    print("=" * 60)
    try:
        cur.execute(
            "SELECT trade_id, created_at, analysis_json "
            "FROM trade_postmortems ORDER BY created_at DESC LIMIT 5"
        )
        rows = cur.fetchall()
        if not rows:
            print("  (no rows)")
        for trade_id, created, aj in rows:
            try:
                a = json.loads(aj)
            except json.JSONDecodeError as e:
                print(f"  --- trade={trade_id} {created}: JSON parse ERR {e}")
                continue
            print(f"  --- trade={trade_id} {created}")
            print(f"      outcome: {a.get('outcome')}")
            cause = a.get("primary_cause", "")[:100]
            print(f"      primary_cause: {cause}")
            ps = a.get("parameter_suggestion") or {}
            print(
                f"      param_suggestion: param={ps.get('parameter')}, "
                f"cur={ps.get('current_value')}, "
                f"sug={ps.get('suggested_value')}"
            )
    except sqlite3.Error as e:
        print(f"  ERR: {e}")

    print()
    print("=" * 60)
    print("5. parameter_suggestion 集約（全件）")
    print("=" * 60)
    try:
        cur.execute("SELECT analysis_json FROM trade_postmortems")
        all_rows = cur.fetchall()
        param_counter: Counter[str] = Counter()
        non_null = 0
        null_count = 0
        parse_err = 0
        for (aj,) in all_rows:
            try:
                a = json.loads(aj)
            except json.JSONDecodeError:
                parse_err += 1
                continue
            ps = a.get("parameter_suggestion") or {}
            param = ps.get("parameter")
            if param:
                param_counter[param] += 1
                non_null += 1
            else:
                null_count += 1
        print(f"  total       : {len(all_rows)}")
        print(f"  with param  : {non_null}")
        print(f"  null param  : {null_count}")
        print(f"  parse_err   : {parse_err}")
        print(f"  param頻度Top10:")
        for name, cnt in param_counter.most_common(10):
            print(f"    {cnt:4d}  {name}")
    except sqlite3.Error as e:
        print(f"  ERR: {e}")

    con.close()


if __name__ == "__main__":
    main()
