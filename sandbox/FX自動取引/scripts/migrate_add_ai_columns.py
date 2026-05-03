"""
FX自動取引システム — trades テーブルへ AI バイアスカラムを追加するマイグレーション

T5: AI A/Bテスト基盤の一部。既存の trades テーブルに以下のカラムを冪等に追加する:
  - ai_decision   TEXT   ('CONFIRM' / 'CONTRADICT' / 'NEUTRAL' / 'REJECT')
  - ai_confidence REAL   (0.0 - 1.0)
  - ai_reasons    TEXT   (AIBias.reasoning の保存先)
  - ai_direction  TEXT   ('bullish' / 'bearish' / 'neutral')
  - ai_regime     TEXT   ('trending' / 'ranging' / 'volatile' / 'unknown')

特徴:
  - PRAGMA table_info で重複検出 → 何度実行しても同じ結果になる（冪等）
  - 既存行は NULL のままになる（集計時は WHERE ai_decision IS NOT NULL でフィルタ）
  - DBが存在しなければ何もしない（DB自体は別の初期化処理が作る）

実行例:
  python scripts/migrate_add_ai_columns.py
  python scripts/migrate_add_ai_columns.py --db data/fx_trading.db
  python scripts/migrate_add_ai_columns.py --dry-run

VPS本番への適用手順:
  1. 念のためDBをバックアップ
       Copy-Item C:\\bpr_lab\\fx_trading\\data\\fx_trading.db `
                 C:\\bpr_lab\\fx_trading\\data\\fx_trading.db.bak_$(Get-Date -Format yyyyMMdd_HHmmss)
  2. マイグレーション実行
       cd C:\\bpr_lab\\fx_trading
       python scripts\\migrate_add_ai_columns.py
  3. 確認（5カラムが存在することを確認）
       python scripts\\migrate_add_ai_columns.py --dry-run
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

from src.config import DB_PATH  # noqa: E402

logger = logging.getLogger(__name__)

# 追加対象カラム定義 (カラム名, SQL型)
AI_COLUMNS: list[tuple[str, str]] = [
    ("ai_decision", "TEXT"),
    ("ai_confidence", "REAL"),
    ("ai_reasons", "TEXT"),
    ("ai_direction", "TEXT"),
    ("ai_regime", "TEXT"),
]


def get_existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """指定テーブルの既存カラム名集合を返す。テーブル未作成なら空集合。"""
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """指定テーブルが存在するか。"""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cur.fetchone() is not None


def migrate(db_path: Path, dry_run: bool = False) -> dict:
    """
    trades テーブルに AI カラムを冪等に追加する。

    Args:
        db_path: SQLite DB パス
        dry_run: True の場合、ALTER 実行はせず差分のみ報告

    Returns:
        {"added": [カラム名...], "skipped": [既存カラム名...], "table_exists": bool}

    Raises:
        FileNotFoundError: DB ファイルが存在しない場合
    """
    if not db_path.exists():
        raise FileNotFoundError(f"DBファイルが存在しません: {db_path}")

    result: dict = {"added": [], "skipped": [], "table_exists": False}

    with sqlite3.connect(str(db_path)) as conn:
        if not table_exists(conn, "trades"):
            logger.warning(
                "tradesテーブルが存在しません。PositionManager 初回起動で作成されます。"
            )
            return result

        result["table_exists"] = True
        existing = get_existing_columns(conn, "trades")
        logger.info("trades 既存カラム数: %d", len(existing))

        for col_name, col_type in AI_COLUMNS:
            if col_name in existing:
                logger.info("スキップ（既存）: %s", col_name)
                result["skipped"].append(col_name)
                continue

            if dry_run:
                logger.info("[dry-run] 追加予定: %s %s", col_name, col_type)
                result["added"].append(col_name)
                continue

            sql = f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}"
            logger.info("実行: %s", sql)
            conn.execute(sql)
            result["added"].append(col_name)

        if not dry_run:
            conn.commit()

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="trades テーブルに AI バイアスカラムを追加（冪等）"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help=f"SQLite DBパス（デフォルト: {DB_PATH}）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ALTER 実行せず、差分のみ報告",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.info("=== AI カラムマイグレーション 開始 ===")
    logger.info("DB: %s", args.db)
    if args.dry_run:
        logger.info("[dry-run モード] 実 ALTER は行いません")

    try:
        result = migrate(args.db, dry_run=args.dry_run)
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except sqlite3.Error as e:
        logger.exception("SQLiteエラー: %s", e)
        return 2

    logger.info(
        "結果: 追加=%d %s / スキップ=%d %s / table_exists=%s",
        len(result["added"]), result["added"],
        len(result["skipped"]), result["skipped"],
        result["table_exists"],
    )
    logger.info("=== AI カラムマイグレーション 完了 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
