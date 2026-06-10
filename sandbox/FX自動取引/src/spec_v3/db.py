"""SPEC v3 — SQLite DB アクセス層

データ保管: `data/fx_spec_v3.db` (fx_spec_v2.db / fx_trading.db とは別ファイル)

## テーブル一覧
| テーブル | 役割 |
|---|---|
| llm_judgments    | LLM 判定全件 (取らなかったものも含む) |
| trades            | 実発注の DB ミラー (MT5 ticket 付き) |
| trade_closures    | 決済記録 (TP/SL/time_limit/regime_change/manual) |
| loop_health       | ループ稼働ヘルス (start/stop/error/heartbeat/kill_switch) |
| llm_api_cost      | LLM API コスト記録 (撤退条件 #4 早期検知) |

## 設計原則
- すべて UTC で記録
- `judged_at_utc` / `entry_at_utc` の time-zone は ISO8601 (+00:00)
- 抑制シグナル (NEUTRAL/CONTRADICT/REJECT) も全件 llm_judgments に記録
- 後付けバイアス防止のため、LLM プロンプトから渡したコンテキストの hash も保存
"""
from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


SCHEMA_SQL = """
-- LLM 判定全件 (signal_v2 が出した全シグナル、取らなかったものも含む)
CREATE TABLE IF NOT EXISTS llm_judgments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judged_at_utc TEXT NOT NULL,
    pair TEXT NOT NULL,
    signal_direction TEXT NOT NULL,             -- 'long' / 'short'
    entry_price REAL NOT NULL,
    sl_price REAL,
    tp_price REAL,
    sl_pips REAL,
    tp_pips REAL,
    atr REAL,
    signal_reason TEXT,

    -- LLM 判定結果
    llm_label TEXT NOT NULL,                    -- 'CONFIRM' / 'NEUTRAL' / 'CONTRADICT' / 'REJECT' / 'API_ERROR'
    llm_confidence REAL,
    llm_reasoning TEXT,

    -- 採用判定: 1 なら発注対象、0 なら見送り (理由は decision_reason)
    accepted INTEGER NOT NULL DEFAULT 0,
    decision_reason TEXT,                       -- 'accepted' / 'label_not_confirm' / 'below_confidence_threshold' / 'killswitch_blocked' / 'position_open' / 'api_error_failsafe'

    -- API コスト記録
    api_input_tokens INTEGER,
    api_output_tokens INTEGER,
    api_cost_usd REAL,

    -- フェイルセーフ: API エラーや JSON parse 失敗を保持
    api_error TEXT,

    -- 関連通貨 24h 変動 (LLM プロンプトに渡した参考情報、後付けバイアス検出用)
    context_json TEXT,

    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_judgments_judged_at ON llm_judgments(judged_at_utc);
CREATE INDEX IF NOT EXISTS idx_judgments_pair ON llm_judgments(pair);
CREATE INDEX IF NOT EXISTS idx_judgments_label ON llm_judgments(llm_label);
CREATE INDEX IF NOT EXISTS idx_judgments_accepted ON llm_judgments(accepted);

-- 実発注のミラー (MT5 ticket と紐づけ)
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mt5_ticket INTEGER UNIQUE,
    entry_at_utc TEXT NOT NULL,
    pair TEXT NOT NULL,
    direction TEXT NOT NULL,
    lots REAL NOT NULL,
    entry_price REAL NOT NULL,
    sl_price REAL,
    tp_price REAL,
    sl_pips REAL,
    tp_pips REAL,
    judgment_id INTEGER,                         -- llm_judgments.id への参照
    signal_reason TEXT,
    llm_label TEXT,
    llm_confidence REAL,
    status TEXT NOT NULL DEFAULT 'open',         -- 'open' / 'closed' / 'error'
    is_demo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (judgment_id) REFERENCES llm_judgments(id)
);
CREATE INDEX IF NOT EXISTS idx_trades_entry_at ON trades(entry_at_utc);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_pair ON trades(pair);
CREATE INDEX IF NOT EXISTS idx_trades_ticket ON trades(mt5_ticket);

-- 決済記録
CREATE TABLE IF NOT EXISTS trade_closures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL,
    exit_at_utc TEXT NOT NULL,
    exit_price REAL NOT NULL,
    exit_reason TEXT NOT NULL,                   -- 'tp', 'sl', 'tp_or_sl', 'time_limit', 'manual', 'kill_switch'
    pnl_pips REAL,
    pnl_jpy REAL,
    holding_minutes INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (trade_id) REFERENCES trades(id)
);
CREATE INDEX IF NOT EXISTS idx_closures_trade ON trade_closures(trade_id);
CREATE INDEX IF NOT EXISTS idx_closures_exit_at ON trade_closures(exit_at_utc);

-- ループ稼働ヘルス
CREATE TABLE IF NOT EXISTS loop_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_at_utc TEXT NOT NULL,
    event_type TEXT NOT NULL,                    -- 'start' / 'stop' / 'error' / 'heartbeat' / 'kill_switch' / 'retreat'
    pair TEXT,
    message TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_loop_health_at ON loop_health(event_at_utc);
CREATE INDEX IF NOT EXISTS idx_loop_health_type ON loop_health(event_type);

-- LLM API コスト日次累計 (撤退条件 #4: 月コスト > 5,000円 早期検知用)
-- 実際の日次集計は llm_judgments.api_cost_usd の SUM で算出可能だが、
-- 月別集計を高速にするためのインデックス兼サマリビュー
CREATE TABLE IF NOT EXISTS llm_api_cost_daily (
    date_utc TEXT PRIMARY KEY,                   -- YYYY-MM-DD (UTC)
    n_calls INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0.0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- キルスイッチ状態の永続化 (Ultra/Karen バグ⑤ 是正、2026-05-27)
-- 1 行のみのシングルトンテーブル (id=1 固定)。
-- daily_block_until / monthly_block_until / blocked_pairs / spread_baseline をプロセス再起動で復元する。
-- VPS タスクスケジューラの自動再起動 (RestartCount=5) で日次停止が吹き飛ぶ問題への対処。
CREATE TABLE IF NOT EXISTS kill_switch_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    daily_block_until TEXT,                      -- 'YYYY-MM-DD' or NULL
    monthly_block_until TEXT,                    -- 'YYYY-MM' or NULL
    blocked_pairs_json TEXT,                     -- JSON list (例: ["USD_JPY"])
    global_block_reason TEXT,                    -- NULL なら未発火
    spread_baseline_json TEXT,                   -- JSON dict (例: {"USD_JPY": 1.05})
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def utc_now_iso() -> str:
    """UTC 現在時刻を ISO8601 (秒精度) で返す"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_conn(db_path: Path) -> Iterator[sqlite3.Connection]:
    """SQLite 接続のコンテキストマネージャ (autocommit)"""
    conn = sqlite3.connect(str(db_path), isolation_level=None, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        # 同時接続耐性を上げるため WAL モード
        conn.execute("PRAGMA journal_mode=WAL")
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path) -> None:
    """DB 初期化 (テーブルなければ作成)"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
    logger.info("SPEC v3 DB initialized: %s", db_path)


# ============================================================
# llm_judgments
# ============================================================


def insert_llm_judgment(
    db_path: Path,
    *,
    judged_at_utc: str,
    pair: str,
    signal_direction: str,
    entry_price: float,
    sl_price: Optional[float],
    tp_price: Optional[float],
    sl_pips: Optional[float],
    tp_pips: Optional[float],
    atr: Optional[float],
    signal_reason: Optional[str],
    llm_label: str,
    llm_confidence: Optional[float],
    llm_reasoning: Optional[str],
    accepted: bool,
    decision_reason: str,
    api_input_tokens: Optional[int],
    api_output_tokens: Optional[int],
    api_cost_usd: Optional[float],
    api_error: Optional[str],
    context: Optional[dict],
) -> int:
    """LLM 判定 1 行を挿入し id を返す。"""
    ctx_json = json.dumps(context, ensure_ascii=False) if context else None
    with get_conn(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO llm_judgments (
                judged_at_utc, pair, signal_direction, entry_price,
                sl_price, tp_price, sl_pips, tp_pips, atr, signal_reason,
                llm_label, llm_confidence, llm_reasoning,
                accepted, decision_reason,
                api_input_tokens, api_output_tokens, api_cost_usd, api_error,
                context_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                judged_at_utc, pair, signal_direction, entry_price,
                sl_price, tp_price, sl_pips, tp_pips, atr, signal_reason,
                llm_label, llm_confidence, llm_reasoning,
                1 if accepted else 0, decision_reason,
                api_input_tokens, api_output_tokens, api_cost_usd, api_error,
                ctx_json,
            ),
        )
        return cur.lastrowid


# ============================================================
# trades / closures
# ============================================================


def insert_trade(
    db_path: Path,
    *,
    mt5_ticket: Optional[int],
    entry_at_utc: str,
    pair: str,
    direction: str,
    lots: float,
    entry_price: float,
    sl_price: Optional[float],
    tp_price: Optional[float],
    sl_pips: Optional[float],
    tp_pips: Optional[float],
    judgment_id: Optional[int],
    signal_reason: Optional[str],
    llm_label: Optional[str],
    llm_confidence: Optional[float],
    is_demo: bool = True,
) -> int:
    with get_conn(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO trades (
                mt5_ticket, entry_at_utc, pair, direction, lots, entry_price,
                sl_price, tp_price, sl_pips, tp_pips,
                judgment_id, signal_reason, llm_label, llm_confidence,
                status, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (
                mt5_ticket, entry_at_utc, pair, direction, lots, entry_price,
                sl_price, tp_price, sl_pips, tp_pips,
                judgment_id, signal_reason, llm_label, llm_confidence,
                1 if is_demo else 0,
            ),
        )
        return cur.lastrowid


def insert_trade_closure(
    db_path: Path,
    *,
    trade_id: int,
    exit_at_utc: str,
    exit_price: float,
    exit_reason: str,
    pnl_pips: Optional[float],
    pnl_jpy: Optional[float],
    holding_minutes: Optional[int],
) -> int:
    with get_conn(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO trade_closures (
                trade_id, exit_at_utc, exit_price, exit_reason,
                pnl_pips, pnl_jpy, holding_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (trade_id, exit_at_utc, exit_price, exit_reason,
             pnl_pips, pnl_jpy, holding_minutes),
        )
        conn.execute("UPDATE trades SET status='closed' WHERE id=?", (trade_id,))
        return cur.lastrowid


def get_open_trades(db_path: Path, pair: Optional[str] = None) -> list[sqlite3.Row]:
    """status='open' のトレード一覧。pair 指定で絞り込み可能。"""
    if not db_path.exists():
        return []
    with get_conn(db_path) as conn:
        if pair is None:
            cur = conn.execute(
                "SELECT * FROM trades WHERE status='open' ORDER BY id"
            )
        else:
            cur = conn.execute(
                "SELECT * FROM trades WHERE status='open' AND pair=? ORDER BY id",
                (pair,),
            )
        return list(cur.fetchall())


# ============================================================
# loop_health
# ============================================================


def insert_loop_health(
    db_path: Path,
    event_type: str,
    message: Optional[str] = None,
    pair: Optional[str] = None,
) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO loop_health (event_at_utc, event_type, pair, message)
            VALUES (?, ?, ?, ?)
            """,
            (utc_now_iso(), event_type, pair, message),
        )


# ============================================================
# 集計クエリ (Slack 死活 / 日次サマリ / 撤退条件チェック用)
# ============================================================


def count_judgments_since(
    db_path: Path,
    since_iso: str,
    pair: Optional[str] = None,
) -> dict:
    """since 以降の LLM 判定分布を集計"""
    if not db_path.exists():
        return {"total": 0, "by_label": {}}
    with get_conn(db_path) as conn:
        if pair is None:
            cur = conn.execute(
                """
                SELECT llm_label, COUNT(*) AS cnt
                FROM llm_judgments
                WHERE judged_at_utc >= ?
                GROUP BY llm_label
                """,
                (since_iso,),
            )
        else:
            cur = conn.execute(
                """
                SELECT llm_label, COUNT(*) AS cnt
                FROM llm_judgments
                WHERE judged_at_utc >= ? AND pair = ?
                GROUP BY llm_label
                """,
                (since_iso, pair),
            )
        by_label = {row["llm_label"]: int(row["cnt"]) for row in cur.fetchall()}
    return {"total": sum(by_label.values()), "by_label": by_label}


def get_recent_trades(
    db_path: Path,
    *,
    pair: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[sqlite3.Row]:
    """決済済 trades を新しい順に。limit で最新 N 件に絞れる。"""
    if not db_path.exists():
        return []
    query = (
        "SELECT t.*, c.exit_at_utc, c.exit_price, c.exit_reason, "
        "  c.pnl_pips, c.pnl_jpy, c.holding_minutes "
        "FROM trades t JOIN trade_closures c ON c.trade_id = t.id "
        "WHERE t.status='closed' "
    )
    params: list = []
    if pair is not None:
        query += "AND t.pair=? "
        params.append(pair)
    query += "ORDER BY c.exit_at_utc DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    with get_conn(db_path) as conn:
        return list(conn.execute(query, params).fetchall())


def cumulative_pnl(
    db_path: Path,
    pair: Optional[str] = None,
) -> dict:
    """確定 PnL の累計 (JPY / pips / 件数)"""
    if not db_path.exists():
        return {"n": 0, "total_jpy": 0.0, "total_pips": 0.0}
    with get_conn(db_path) as conn:
        if pair is None:
            cur = conn.execute(
                """
                SELECT COUNT(*) AS n, SUM(pnl_pips) AS pips, SUM(pnl_jpy) AS jpy
                FROM trade_closures
                """,
            )
        else:
            cur = conn.execute(
                """
                SELECT COUNT(*) AS n, SUM(c.pnl_pips) AS pips, SUM(c.pnl_jpy) AS jpy
                FROM trade_closures c
                JOIN trades t ON t.id = c.trade_id
                WHERE t.pair = ?
                """,
                (pair,),
            )
        row = cur.fetchone()
    return {
        "n": int(row["n"] or 0),
        "total_pips": float(row["pips"] or 0.0),
        "total_jpy": float(row["jpy"] or 0.0),
    }


def llm_cost_in_month(db_path: Path, ym: Optional[str] = None) -> dict:
    """指定月 (YYYY-MM、UTC) の LLM API コスト合計と件数。
    ym=None なら現在の UTC 月。
    """
    if ym is None:
        ym = datetime.now(timezone.utc).strftime("%Y-%m")
    if not db_path.exists():
        return {"ym": ym, "n_calls": 0, "cost_usd": 0.0}
    prefix = ym + "-"
    with get_conn(db_path) as conn:
        cur = conn.execute(
            """
            SELECT COUNT(*) AS n, SUM(api_cost_usd) AS cost
            FROM llm_judgments
            WHERE substr(judged_at_utc, 1, 8) = ?
            """,
            (prefix,),
        )
        row = cur.fetchone()
    return {
        "ym": ym,
        "n_calls": int(row["n"] or 0),
        "cost_usd": float(row["cost"] or 0.0),
    }


def days_since_first_trade(db_path: Path, pair: str) -> Optional[int]:
    """当該ペアで最初の trade からの経過日数。trade が無ければ None。"""
    if not db_path.exists():
        return None
    with get_conn(db_path) as conn:
        cur = conn.execute(
            "SELECT MIN(entry_at_utc) AS first_at FROM trades WHERE pair=?",
            (pair,),
        )
        row = cur.fetchone()
    first_at = row["first_at"] if row else None
    if not first_at:
        return None
    first_dt = datetime.fromisoformat(first_at.replace("Z", "+00:00"))
    if first_dt.tzinfo is None:
        first_dt = first_dt.replace(tzinfo=timezone.utc)
    return int((datetime.now(timezone.utc) - first_dt).total_seconds() / 86400)


def trade_count(db_path: Path, pair: str) -> int:
    """当該ペアでこれまで開いた trade 件数"""
    if not db_path.exists():
        return 0
    with get_conn(db_path) as conn:
        cur = conn.execute(
            "SELECT COUNT(*) AS n FROM trades WHERE pair=?",
            (pair,),
        )
        row = cur.fetchone()
    return int(row["n"] or 0)


def monthly_pf_window(
    db_path: Path,
    pair: str,
    months_back: int = 3,
    window_days: int = 30,
) -> list[dict]:
    """過去 N ヶ月分の月別 PF (ローリング 30 日) を新しい順で返す。

    Ultra H-② 是正 (2026-05-28): 撤退条件 #0 (lift) 用。
    各月 (UTC) について、その月末から window_days 遡った期間の確定 trades の
    PF と件数を計算する。

    Returns:
        [
            {"month": "YYYY-MM", "pf": float | None, "n": int,
             "wins_pips": float, "losses_pips": float},
            ...
        ]
        新しい月から順に最大 months_back 件返す。
        n < 5 (RETREAT_LIFT_MIN_TRADES 未満) は pf=None としてマーク。
    """
    out: list[dict] = []
    if not db_path.exists():
        return out
    now = datetime.now(timezone.utc)
    with get_conn(db_path) as conn:
        for i in range(months_back):
            # i=0 は当月の末日、i=1 は前月の末日、…
            # 簡易: 現在から (i * 30) 日遡った点を「月の評価時点」とし、
            # その時点から更に window_days 遡ったウィンドウで PF を取る。
            anchor = now - _timedelta_days(i * 30)
            window_end = anchor
            window_start = anchor - _timedelta_days(window_days)
            cur = conn.execute(
                """
                SELECT c.pnl_pips
                FROM trade_closures c
                JOIN trades t ON t.id = c.trade_id
                WHERE t.pair = ?
                  AND c.exit_at_utc >= ?
                  AND c.exit_at_utc <  ?
                  AND c.pnl_pips IS NOT NULL
                """,
                (pair,
                 window_start.isoformat(timespec="seconds"),
                 window_end.isoformat(timespec="seconds")),
            )
            pnls = [float(row["pnl_pips"]) for row in cur.fetchall()]
            n = len(pnls)
            wins = sum(p for p in pnls if p > 0)
            losses = -sum(p for p in pnls if p < 0)
            if n < 5:
                pf: Optional[float] = None
            elif losses <= 0:
                pf = float("inf") if wins > 0 else 0.0
            else:
                pf = wins / losses
            out.append({
                "month": anchor.strftime("%Y-%m"),
                "pf": pf,
                "n": n,
                "wins_pips": wins,
                "losses_pips": losses,
            })
    return out


def _timedelta_days(days: int):
    """timedelta(days=days) を返す簡易ヘルパ (datetime.py 経由)。"""
    from datetime import timedelta
    return timedelta(days=days)


def signal_base_pf_window(
    db_path: Path,
    pair: str,
    months_back: int = 3,
    window_days: int = 30,
) -> list[dict]:
    """過去 N ヶ月分の base PF (LLM 非適用シナリオの近似) を返す。

    Ultra H-② 是正 (2026-05-28): 撤退条件 #0 (lift) の base 計算用。

    現状の DB には「LLM に却下されたシグナルが取れていたら得られたであろう PnL」
    (= 抑制シグナル仮想 PnL) が記録されていない (SPEC §8.4 で口約束済、
    未実装、レビュー J 節で再指摘)。
    そのため base PF は「現状は信号源不足で計算不能」を表す
    `pf=None` を返す月が多くなる。

    将来的に suppressed-PnL 計算スクリプト (`_spec_v3_suppressed_pnl.py`) が
    導入されたらここで `llm_judgments` を全件 (accepted=0 含む) 走査し、
    エントリ価格と 24h 後挙動から仮想 PnL を計算する。

    Returns:
        monthly_pf_window と同じスキーマ。pf は現時点ほぼ None。
        ペア別の base 表現を月別に並べる。
    """
    out: list[dict] = []
    if not db_path.exists():
        return out
    now = datetime.now(timezone.utc)
    with get_conn(db_path) as conn:
        for i in range(months_back):
            anchor = now - _timedelta_days(i * 30)
            window_end = anchor
            window_start = anchor - _timedelta_days(window_days)
            # 現時点では accepted=1 (実発注された判定) のみ確定 PnL を持つので、
            # base = (accepted=1 の確定 PnL) ∪ (accepted=0 の仮想 PnL=None)
            # から「accepted=0 の数が多い場合は計算不能 (None)」とする。
            cur = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN accepted=1 THEN 1 ELSE 0 END) AS n_accept,
                    SUM(CASE WHEN accepted=0 THEN 1 ELSE 0 END) AS n_reject
                FROM llm_judgments
                WHERE pair=?
                  AND judged_at_utc >= ?
                  AND judged_at_utc <  ?
                """,
                (pair,
                 window_start.isoformat(timespec="seconds"),
                 window_end.isoformat(timespec="seconds")),
            )
            row = cur.fetchone()
            n_accept = int(row["n_accept"] or 0)
            n_reject = int(row["n_reject"] or 0)
            n_total = n_accept + n_reject
            # 抑制シグナル仮想 PnL が未実装の段階では base PF は計算不能。
            # 月単位の signal 数が分かるので「シグナル発生はあった」ことだけ記録。
            out.append({
                "month": anchor.strftime("%Y-%m"),
                "pf": None,
                "n": n_total,
                "n_accept": n_accept,
                "n_reject": n_reject,
                "wins_pips": 0.0,
                "losses_pips": 0.0,
            })
    return out


def recent_pf(
    db_path: Path, pair: str, n_trades: int = 100, min_trades: int = 5,
) -> Optional[float]:
    """直近 n_trades の Profit Factor。trade<min_trades なら None (撤退条件 #1 と区別)"""
    if not db_path.exists():
        return None
    with get_conn(db_path) as conn:
        cur = conn.execute(
            """
            SELECT c.pnl_pips
            FROM trade_closures c
            JOIN trades t ON t.id = c.trade_id
            WHERE t.pair = ? AND c.pnl_pips IS NOT NULL
            ORDER BY c.exit_at_utc DESC
            LIMIT ?
            """,
            (pair, n_trades),
        )
        pnls = [float(row["pnl_pips"]) for row in cur.fetchall()]
    if len(pnls) < min_trades:
        return None
    wins = sum(p for p in pnls if p > 0)
    losses = -sum(p for p in pnls if p < 0)
    if losses <= 0:
        return float("inf") if wins > 0 else 0.0
    return wins / losses


def confirm_confidence_outcomes(
    db_path: Path, pair: str, since_iso: Optional[str] = None,
) -> list[tuple[float, int]]:
    """採用群 (CONFIRM 発注 → 決済済) の (confidence, win) リストを返す。

    confidence の判別力 (AUC) 計測用。win = 確定 PnL > 0。
    trades.llm_confidence × trade_closures.pnl_jpy を JOIN する。
    抑制 (未採用) シグナルは trade にならないため含まれない
    (= 採用群内での判別力を測る。抑制群の仮想 PnL は別途 suppressed-PnL で)。
    """
    if not db_path.exists():
        return []
    q = (
        "SELECT t.llm_confidence AS conf, c.pnl_jpy AS pnl "
        "FROM trades t JOIN trade_closures c ON c.trade_id = t.id "
        "WHERE t.pair = ? AND t.llm_confidence IS NOT NULL AND c.pnl_jpy IS NOT NULL"
    )
    params: list = [pair]
    if since_iso:
        q += " AND c.exit_at_utc >= ?"
        params.append(since_iso)
    with get_conn(db_path) as conn:
        rows = conn.execute(q, params).fetchall()
    return [(float(r["conf"]), 1 if (r["pnl"] or 0.0) > 0 else 0) for r in rows]


# ============================================================
# kill_switch_state (永続化、Ultra/Karen バグ⑤ 是正)
# ============================================================


def save_killswitch_state(
    db_path: Path,
    *,
    daily_block_until: Optional[str],
    monthly_block_until: Optional[str],
    blocked_pairs: Optional[set[str]] = None,
    global_block_reason: Optional[str] = None,
    spread_baseline: Optional[dict[str, float]] = None,
) -> None:
    """キルスイッチ状態を SQLite に永続化 (UPSERT、id=1 固定)。

    VPS タスクスケジューラの自動再起動 (RestartCount=5) で安全装置が
    吹き飛ぶ問題への対処。状態変化時に呼び出される。
    """
    blocked_json = json.dumps(sorted(blocked_pairs)) if blocked_pairs else None
    baseline_json = (
        json.dumps(spread_baseline, ensure_ascii=False) if spread_baseline else None
    )
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO kill_switch_state (
                id, daily_block_until, monthly_block_until,
                blocked_pairs_json, global_block_reason, spread_baseline_json, updated_at
            ) VALUES (1, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                daily_block_until=excluded.daily_block_until,
                monthly_block_until=excluded.monthly_block_until,
                blocked_pairs_json=excluded.blocked_pairs_json,
                global_block_reason=excluded.global_block_reason,
                spread_baseline_json=excluded.spread_baseline_json,
                updated_at=datetime('now')
            """,
            (
                daily_block_until, monthly_block_until,
                blocked_json, global_block_reason, baseline_json,
            ),
        )


def load_killswitch_state(db_path: Path) -> dict:
    """キルスイッチ状態を SQLite から復元。

    Returns:
        {
            "daily_block_until": Optional[str],
            "monthly_block_until": Optional[str],
            "blocked_pairs": set[str],
            "global_block_reason": Optional[str],
            "spread_baseline": dict[str, float],
        }
        未保存なら全て初期値 (None / 空集合 / 空 dict)。
    """
    default = {
        "daily_block_until": None,
        "monthly_block_until": None,
        "blocked_pairs": set(),
        "global_block_reason": None,
        "spread_baseline": {},
    }
    if not db_path.exists():
        return default
    with get_conn(db_path) as conn:
        cur = conn.execute(
            """
            SELECT daily_block_until, monthly_block_until,
                   blocked_pairs_json, global_block_reason, spread_baseline_json
            FROM kill_switch_state WHERE id = 1
            """,
        )
        row = cur.fetchone()
    if row is None:
        return default
    try:
        blocked = set(json.loads(row["blocked_pairs_json"])) if row["blocked_pairs_json"] else set()
    except (json.JSONDecodeError, TypeError):
        blocked = set()
    try:
        baseline = json.loads(row["spread_baseline_json"]) if row["spread_baseline_json"] else {}
    except (json.JSONDecodeError, TypeError):
        baseline = {}
    return {
        "daily_block_until": row["daily_block_until"],
        "monthly_block_until": row["monthly_block_until"],
        "blocked_pairs": blocked,
        "global_block_reason": row["global_block_reason"],
        "spread_baseline": baseline,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    test_db = root / "data" / "fx_spec_v3.db"
    init_db(test_db)
    print(f"DB initialized: {test_db}")
