"""SPEC v2 PoC 用 SQLite DB アクセスヘルパー

亡き者の世界 (data/fx_trading.db) と物理分離するため、
専用 DB `data/fx_spec_v2.db` を使う。

## テーブル
1. `seasonal_judgments`: SeasonalDetector の判定ログ (1 行 = 1 ループ評価)
2. `trades`        : デモ口座での実発注の DB ミラー (MT5 ticket を持つ)
3. `trade_closures`: 決済履歴 (TP/SL/時間損切り/手動)
4. `loop_health`   : ループ稼働ヘルス (起動/停止、エラー履歴)

## 設計原則
- 既存 fx_trading.db のスキーマを継承しない (ゼロベース再構築哲学)
- デモ口座の発注を直接 DB ミラー、仮想エントリー層は持たない
- 単一通貨 (GBP_JPY) 専用、`pair` 列は固定値だが将来拡張のため保持
- 全テーブルに `created_at` を持たせ、UTC で記録
"""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS seasonal_judgments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judged_at_utc TEXT NOT NULL,
    pair TEXT NOT NULL DEFAULT 'GBP_JPY',
    regime TEXT NOT NULL,
    m15_yz_vol REAL,
    m15_threshold REAL,
    m15_above INTEGER,
    h1_yz_vol REAL,
    h1_threshold REAL NOT NULL,
    h1_above INTEGER,
    chop_optional REAL,
    chop_below_25 INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_seasonal_judged_at ON seasonal_judgments(judged_at_utc);
CREATE INDEX IF NOT EXISTS idx_seasonal_regime ON seasonal_judgments(regime);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mt5_ticket INTEGER UNIQUE,                       -- MT5 ポジションチケット
    entry_at_utc TEXT NOT NULL,
    pair TEXT NOT NULL DEFAULT 'GBP_JPY',
    direction TEXT NOT NULL,                          -- 'long' / 'short'
    lots REAL NOT NULL,
    entry_price REAL NOT NULL,
    sl_price REAL,
    tp_price REAL,
    sl_pips REAL,
    tp_pips REAL,
    judgment_id INTEGER,
    signal_reason TEXT,
    status TEXT NOT NULL DEFAULT 'open',              -- 'open' / 'closed' / 'error'
    is_demo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (judgment_id) REFERENCES seasonal_judgments(id)
);
CREATE INDEX IF NOT EXISTS idx_trades_at ON trades(entry_at_utc);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_ticket ON trades(mt5_ticket);

CREATE TABLE IF NOT EXISTS trade_closures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL,
    exit_at_utc TEXT NOT NULL,
    exit_price REAL NOT NULL,
    exit_reason TEXT NOT NULL,                        -- 'tp', 'sl', 'time_limit', 'regime_change', 'manual'
    pnl_pips REAL,
    pnl_jpy REAL,
    holding_minutes INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (trade_id) REFERENCES trades(id)
);
CREATE INDEX IF NOT EXISTS idx_closures_trade ON trade_closures(trade_id);

CREATE TABLE IF NOT EXISTS loop_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_at_utc TEXT NOT NULL,
    event_type TEXT NOT NULL,                         -- 'start' / 'stop' / 'error' / 'heartbeat' / 'kill_switch'
    message TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_loop_health_at ON loop_health(event_at_utc);
"""


def utc_now_iso() -> str:
    """UTC 現在時刻を ISO8601 文字列で返す"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_conn(db_path: Path):
    """SQLite 接続のコンテキストマネージャ"""
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path) -> None:
    """DB 初期化 (テーブルなければ作成)"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
    logger.info(f"DB initialized: {db_path}")


def insert_seasonal_judgment(
    db_path: Path, judged_at_utc: str, regime: str,
    m15_yz_vol: Optional[float], m15_threshold: Optional[float], m15_above: Optional[bool],
    h1_yz_vol: Optional[float], h1_threshold: float, h1_above: Optional[bool],
    chop_optional: Optional[float] = None, chop_below_25: Optional[bool] = None,
    notes: Optional[str] = None,
) -> int:
    """季節判定の 1 行を挿入し、id を返す"""
    with get_conn(db_path) as conn:
        cur = conn.execute("""
            INSERT INTO seasonal_judgments
            (judged_at_utc, pair, regime, m15_yz_vol, m15_threshold, m15_above,
             h1_yz_vol, h1_threshold, h1_above, chop_optional, chop_below_25, notes)
            VALUES (?, 'GBP_JPY', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            judged_at_utc, regime, m15_yz_vol, m15_threshold,
            int(m15_above) if m15_above is not None else None,
            h1_yz_vol, h1_threshold,
            int(h1_above) if h1_above is not None else None,
            chop_optional,
            int(chop_below_25) if chop_below_25 is not None else None,
            notes,
        ))
        return cur.lastrowid


def insert_trade(
    db_path: Path, mt5_ticket: Optional[int], entry_at_utc: str, direction: str,
    lots: float, entry_price: float,
    sl_price: Optional[float], tp_price: Optional[float],
    sl_pips: Optional[float], tp_pips: Optional[float],
    judgment_id: Optional[int], signal_reason: str,
    is_demo: bool = True,
) -> int:
    """発注済みトレードを記録 (MT5 ticket は発注成功時のみ)"""
    with get_conn(db_path) as conn:
        cur = conn.execute("""
            INSERT INTO trades
            (mt5_ticket, entry_at_utc, direction, lots, entry_price,
             sl_price, tp_price, sl_pips, tp_pips,
             judgment_id, signal_reason, status, is_demo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
        """, (mt5_ticket, entry_at_utc, direction, lots, entry_price,
              sl_price, tp_price, sl_pips, tp_pips,
              judgment_id, signal_reason, int(is_demo)))
        return cur.lastrowid


def insert_trade_closure(
    db_path: Path, trade_id: int, exit_at_utc: str,
    exit_price: float, exit_reason: str,
    pnl_pips: Optional[float], pnl_jpy: Optional[float],
    holding_minutes: Optional[int],
) -> int:
    """決済を記録し、trades.status を 'closed' に更新"""
    with get_conn(db_path) as conn:
        cur = conn.execute("""
            INSERT INTO trade_closures
            (trade_id, exit_at_utc, exit_price, exit_reason,
             pnl_pips, pnl_jpy, holding_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (trade_id, exit_at_utc, exit_price, exit_reason,
              pnl_pips, pnl_jpy, holding_minutes))
        conn.execute("UPDATE trades SET status='closed' WHERE id=?", (trade_id,))
        return cur.lastrowid


def get_open_trades(db_path: Path) -> list[sqlite3.Row]:
    """status='open' のトレードをすべて返す"""
    with get_conn(db_path) as conn:
        cur = conn.execute("SELECT * FROM trades WHERE status='open' ORDER BY id")
        return list(cur.fetchall())


def insert_loop_health(
    db_path: Path, event_type: str, message: Optional[str] = None,
) -> None:
    """ループ稼働ヘルスログ"""
    with get_conn(db_path) as conn:
        conn.execute("""
            INSERT INTO loop_health (event_at_utc, event_type, message)
            VALUES (?, ?, ?)
        """, (utc_now_iso(), event_type, message))


def daily_summary(db_path: Path, date_iso: str) -> dict:
    """指定日 (UTC YYYY-MM-DD) の判定分布と PnL のサマリ"""
    with get_conn(db_path) as conn:
        cur = conn.execute("""
            SELECT regime, COUNT(*) AS cnt
            FROM seasonal_judgments
            WHERE substr(judged_at_utc, 1, 10) = ?
            GROUP BY regime
        """, (date_iso,))
        regime_dist = {row["regime"]: row["cnt"] for row in cur.fetchall()}

        cur = conn.execute("""
            SELECT COUNT(*) AS n, SUM(pnl_pips) AS total_pips, SUM(pnl_jpy) AS total_jpy
            FROM trade_closures
            WHERE substr(exit_at_utc, 1, 10) = ?
        """, (date_iso,))
        row = cur.fetchone()
        pnl = {
            "n_closed": row["n"] or 0,
            "total_pips": row["total_pips"] or 0.0,
            "total_jpy": row["total_jpy"] or 0.0,
        }

        cur = conn.execute("SELECT COUNT(*) AS n FROM trades WHERE status='open'")
        n_open = cur.fetchone()["n"]

    return {
        "date": date_iso,
        "regime_distribution": regime_dist,
        "pnl": pnl,
        "n_open_trades": n_open,
    }


if __name__ == "__main__":
    test_db = Path(__file__).resolve().parents[2] / "data" / "fx_spec_v2.db"
    init_db(test_db)
    print(f"DB initialized at: {test_db}")
    print(f"Tables: seasonal_judgments, trades, trade_closures, loop_health")
