"""歴史査読: 亡き者DB から各通貨ペアの実績を集計する (v2)。

実際のスキーマに合わせた集計:
- 取引件数、勝率、PF、累計PnL (pl)
- 中央値保有時間 (opened_at -> closed_at)
- MaxDD (累積PnLカーブから)
- ai_decision / ai_regime / units(方向) 分解
"""
import sqlite3
import statistics
import sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:/Users/takuz/プロジェクト/bpr_lab/sandbox/FX自動取引")
DBS = [
    ROOT / "data/fx_trading_prod_snapshot.db",
    ROOT / "data/fx_trading.db",
]


def parse_dt(s):
    if s is None:
        return None
    s = str(s).strip()
    # +00:00 などのTZ部分を除去
    if "+" in s[10:]:
        s = s[: s.index("+", 10)]
    elif s.endswith("Z"):
        s = s[:-1]
    # 末尾のTZ "-HH:MM" も除去 (ただし日付の "-" は除外)
    if len(s) >= 22 and s[-6] == "-":
        s = s[:-6]
    # ".microseconds" は最大6桁に
    if "." in s:
        head, tail = s.split(".", 1)
        # 余計な文字をカット
        tail = tail[:6]
        s = head + "." + tail
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def aggregate_per_symbol(conn, where_extra=""):
    """ペア別実績集計。where_extra で追加フィルタ可能。"""
    # AIカラムの有無を確認
    cur = conn.execute("PRAGMA table_info(trades)")
    cols = {r[1] for r in cur.fetchall()}
    has_ai = "ai_decision" in cols
    if has_ai:
        sql = f"""SELECT instrument, status, pl, opened_at, closed_at, units,
                  ai_decision, ai_regime, ai_direction
                  FROM trades WHERE 1=1 {where_extra}"""
    else:
        sql = f"""SELECT instrument, status, pl, opened_at, closed_at, units,
                  NULL, NULL, NULL
                  FROM trades WHERE 1=1 {where_extra}"""
    cur = conn.execute(sql)
    rows = cur.fetchall()
    by_sym = {}
    for r in rows:
        sym, status, pl, ot, ct, units, ai_dec, ai_reg, ai_dir = r
        s = by_sym.setdefault(sym, {"pnls": [], "holds_min": [], "all": 0, "long": 0, "short": 0})
        s["all"] += 1
        if status not in ("closed", "CLOSED", "Closed"):
            continue
        try:
            p = float(pl) if pl is not None else 0.0
        except Exception:
            p = 0.0
        s["pnls"].append(p)
        try:
            u = int(units) if units is not None else 0
            if u > 0:
                s["long"] += 1
            elif u < 0:
                s["short"] += 1
        except Exception:
            pass
        odt = parse_dt(ot)
        cdt = parse_dt(ct)
        if odt and cdt:
            s["holds_min"].append((cdt - odt).total_seconds() / 60.0)

    out = {}
    for sym, s in by_sym.items():
        pnls = s["pnls"]
        n = len(pnls)
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        gp = sum(wins)
        gl = -sum(losses)
        pf = (gp / gl) if gl > 0 else (float("inf") if gp > 0 else 0.0)
        wr = (len(wins) / n) if n > 0 else 0.0
        cum = sum(pnls)
        med = statistics.median(s["holds_min"]) if s["holds_min"] else None
        mean = statistics.mean(s["holds_min"]) if s["holds_min"] else None
        # 保有時間分布の上位パーセント (>240min 比率) — PoC 4hr ミスマッチ検証
        if s["holds_min"]:
            n_over_240 = sum(1 for h in s["holds_min"] if h > 240)
            pct_over_240 = n_over_240 / len(s["holds_min"])
        else:
            pct_over_240 = None
        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for p in pnls:
            equity += p
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        avg_win = statistics.mean(wins) if wins else 0
        avg_loss = statistics.mean(losses) if losses else 0
        out[sym] = {
            "n_closed": n,
            "n_total": s["all"],
            "n_long": s["long"],
            "n_short": s["short"],
            "win_rate": wr,
            "pf": pf,
            "cum_pnl": cum,
            "med_hold_min": med,
            "mean_hold_min": mean,
            "pct_hold_over_240min": pct_over_240,
            "max_dd": max_dd,
            "gross_profit": gp,
            "gross_loss": gl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
        }
    return out


def aggregate_per_strategy_proxy(conn):
    """ai_decision / ai_regime を「戦略プロキシ」として分解。"""
    cur = conn.execute("PRAGMA table_info(trades)")
    cols = {r[1] for r in cur.fetchall()}
    if "ai_decision" not in cols:
        return {}
    cur = conn.execute(
        """
        SELECT instrument, ai_decision, ai_regime, status, pl
        FROM trades
        WHERE status IN ('closed','CLOSED','Closed')
        """
    )
    rows = cur.fetchall()
    groups = {}
    for sym, ad, ar, st, pl in rows:
        try:
            p = float(pl) if pl is not None else 0.0
        except Exception:
            p = 0.0
        key = (sym, ad or "n/a", ar or "n/a")
        groups.setdefault(key, []).append(p)
    return groups


def main():
    for dbpath in DBS:
        print(f"\n{'=' * 70}")
        print(f"DB: {dbpath.name}  size={dbpath.stat().st_size if dbpath.exists() else 0}")
        print("=" * 70)
        if not dbpath.exists():
            continue
        conn = sqlite3.connect(str(dbpath))

        # 全件サマリ
        try:
            cur = conn.execute("SELECT MIN(opened_at), MAX(closed_at) FROM trades WHERE status='closed'")
            mn, mx = cur.fetchone()
            print(f"取引期間 (closed): {mn} 〜 {mx}")
        except Exception:
            pass

        # 状態別件数
        cur = conn.execute("SELECT status, COUNT(*) FROM trades GROUP BY status")
        print("状態別件数:", dict(cur.fetchall()))

        # ペア別集計
        stats = aggregate_per_symbol(conn)
        print("\n  通貨ペア別実績 (closed のみ集計):")
        print(f"  {'sym':<10} {'n_cls':>5} {'n_all':>5} {'L/S':>9} {'wr':>6} {'pf':>7} {'cum_pnl':>11} {'med_min':>8} {'>240m%':>7} {'maxDD':>8}")
        # TOTAL算出用
        total_pnls = []
        for sym in sorted(stats.keys()):
            s = stats[sym]
            pf_str = f"{s['pf']:.3f}" if s['pf'] != float('inf') else "inf"
            mh = f"{s['med_hold_min']:.1f}" if s['med_hold_min'] is not None else "n/a"
            pct240 = f"{s['pct_hold_over_240min']:.1%}" if s['pct_hold_over_240min'] is not None else "n/a"
            print(
                f"  {sym:<10} {s['n_closed']:>5d} {s['n_total']:>5d} "
                f"{s['n_long']:>4d}/{s['n_short']:<3d} "
                f"{s['win_rate']:>5.1%} {pf_str:>7} {s['cum_pnl']:>11.2f} "
                f"{mh:>8} {pct240:>7} {s['max_dd']:>8.2f}"
            )

        # 全体
        cur = conn.execute("SELECT pl FROM trades WHERE status='closed' AND pl IS NOT NULL")
        all_pnls = [float(r[0]) for r in cur.fetchall()]
        wins = [p for p in all_pnls if p > 0]
        losses = [p for p in all_pnls if p < 0]
        gp = sum(wins)
        gl = -sum(losses)
        pf = gp / gl if gl > 0 else 0
        print(f"\n  TOTAL: n={len(all_pnls)}, wins={len(wins)}, losses={len(losses)}, wr={len(wins)/len(all_pnls) if all_pnls else 0:.1%}, pf={pf:.3f}, cum={sum(all_pnls):.2f}")

        # 戦略プロキシ (ai_decision × ai_regime)
        groups = aggregate_per_strategy_proxy(conn)
        print("\n  ペア × ai_decision × ai_regime 別 (件数>=2 のみ):")
        print(f"  {'sym':<10} {'ai_decision':<15} {'ai_regime':<12} {'n':>4} {'wr':>6} {'pf':>7} {'cum':>10}")
        for (sym, ad, ar), pnls in sorted(groups.items()):
            if len(pnls) < 2:
                continue
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p < 0]
            gp = sum(wins)
            gl = -sum(losses)
            pf = gp / gl if gl > 0 else (float("inf") if gp > 0 else 0)
            wr = len(wins) / len(pnls) if pnls else 0
            pf_str = f"{pf:.3f}" if pf != float('inf') else "inf"
            print(f"  {sym:<10} {ad:<15} {ar:<12} {len(pnls):>4d} {wr:>5.1%} {pf_str:>7} {sum(pnls):>10.2f}")

        # キルスイッチ発動の理由集計
        try:
            cur = conn.execute("SELECT reason, COUNT(*) FROM kill_switch_log GROUP BY reason ORDER BY COUNT(*) DESC")
            ks = cur.fetchall()
            if ks:
                print("\n  キルスイッチ発動理由 (上位):")
                for reason, n in ks[:10]:
                    print(f"    [{n}回] {reason[:100]}")
        except Exception:
            pass

        conn.close()


if __name__ == "__main__":
    main()
