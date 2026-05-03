"""
T5: AI A/B テスト基盤のユニットテスト

検証対象:
  - AIBias の decision/reasons 副作用と to_record()
  - migrate_add_ai_columns.py の冪等性
  - analyze_ai_ab.py の集計ロジック（GroupStats / aggregate / build_report）
  - daily_summary.fetch_ai_ab_trades / build_ai_ab_text
  - PositionManager.open_position が ai_record を DB に永続化すること
"""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

# プロジェクトルート
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.ai_advisor import AIBias
from src.broker_client import BrokerClient
from src.position_manager import PositionManager
from src.risk_manager import KillSwitch, RiskManager
from src.strategy.base import Signal, StrategyBase


# ============================================================
# 動的に scripts/ モジュールをロード
# ============================================================


def _load_script(name: str):
    """scripts/<name>.py を独立モジュールとしてロードする。"""
    path = _root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


migrate_mod = _load_script("migrate_add_ai_columns")
analyze_mod = _load_script("analyze_ai_ab")
daily_mod = _load_script("daily_summary")


# ============================================================
# 1. AIBias テスト
# ============================================================


class TestAIBiasFields:
    def test_initial_decision_is_none(self):
        bias = AIBias(
            direction="bullish",
            confidence=0.8,
            regime="trending",
            key_levels={},
            reasoning="test",
            timestamp="2026-05-01T00:00:00+00:00",
        )
        assert bias.decision is None
        assert bias.reasons is None

    def test_evaluate_signal_sets_decision_confirm(self):
        bias = AIBias(
            direction="bullish", confidence=0.8, regime="trending",
            key_levels={}, reasoning="x", timestamp="",
        )
        out = bias.evaluate_signal("BUY")
        assert out == "CONFIRM"
        assert bias.decision == "CONFIRM"
        assert bias.reasons is not None
        assert "aligned" in bias.reasons

    def test_evaluate_signal_sets_decision_contradict(self):
        bias = AIBias(
            direction="bearish", confidence=0.8, regime="trending",
            key_levels={}, reasoning="x", timestamp="",
        )
        assert bias.evaluate_signal("BUY") == "CONTRADICT"
        assert bias.decision == "CONTRADICT"
        assert "opposite" in bias.reasons

    def test_evaluate_signal_low_confidence_neutral(self):
        bias = AIBias(
            direction="bullish", confidence=0.1, regime="trending",
            key_levels={}, reasoning="x", timestamp="",
        )
        assert bias.evaluate_signal("BUY") == "NEUTRAL"
        assert "low_confidence" in bias.reasons

    def test_evaluate_signal_volatile_high_conf_reject(self):
        bias = AIBias(
            direction="bullish", confidence=0.85, regime="volatile",
            key_levels={}, reasoning="x", timestamp="",
        )
        assert bias.evaluate_signal("BUY") == "REJECT"
        assert "volatile" in bias.reasons

    def test_to_record_returns_full_dict(self):
        bias = AIBias(
            direction="bearish", confidence=0.65, regime="ranging",
            key_levels={}, reasoning="x", timestamp="",
        )
        bias.evaluate_signal("SELL")
        rec = bias.to_record()
        assert rec["ai_decision"] == "CONFIRM"
        assert rec["ai_confidence"] == pytest.approx(0.65)
        assert rec["ai_direction"] == "bearish"
        assert rec["ai_regime"] == "ranging"
        assert rec["ai_reasons"] is not None

    def test_to_record_decision_none_before_eval(self):
        bias = AIBias(
            direction="bullish", confidence=0.5, regime="trending",
            key_levels={}, reasoning="x", timestamp="",
        )
        rec = bias.to_record()
        assert rec["ai_decision"] is None
        assert rec["ai_reasons"] is None
        assert rec["ai_confidence"] == pytest.approx(0.5)


# ============================================================
# 2. マイグレーション冪等性
# ============================================================


def _create_legacy_trades_db(path: Path) -> None:
    """旧スキーマ（AIカラム無し）の trades テーブルを作成する。"""
    with sqlite3.connect(str(path)) as conn:
        conn.execute(
            """CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT NOT NULL UNIQUE,
                instrument TEXT NOT NULL,
                units INTEGER NOT NULL,
                open_price REAL NOT NULL,
                close_price REAL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                pl REAL,
                opened_at TEXT NOT NULL,
                closed_at TEXT,
                status TEXT NOT NULL DEFAULT 'open'
            )"""
        )


class TestMigration:
    def test_adds_all_ai_columns_on_legacy_db(self, tmp_path):
        db = tmp_path / "test.db"
        _create_legacy_trades_db(db)

        result = migrate_mod.migrate(db)
        assert result["table_exists"] is True
        assert set(result["added"]) == {
            "ai_decision", "ai_confidence", "ai_reasons",
            "ai_direction", "ai_regime",
        }
        assert result["skipped"] == []

        # 実カラムを確認
        with sqlite3.connect(str(db)) as conn:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(trades)").fetchall()}
        for c in ("ai_decision", "ai_confidence", "ai_reasons",
                  "ai_direction", "ai_regime"):
            assert c in cols

    def test_idempotent_second_run(self, tmp_path):
        db = tmp_path / "test.db"
        _create_legacy_trades_db(db)
        migrate_mod.migrate(db)
        # 2回目は全部スキップになる
        result = migrate_mod.migrate(db)
        assert result["added"] == []
        assert set(result["skipped"]) == {
            "ai_decision", "ai_confidence", "ai_reasons",
            "ai_direction", "ai_regime",
        }

    def test_dry_run_does_not_alter(self, tmp_path):
        db = tmp_path / "test.db"
        _create_legacy_trades_db(db)
        result = migrate_mod.migrate(db, dry_run=True)
        # dry-run でも report 上は added 扱い
        assert len(result["added"]) == 5
        with sqlite3.connect(str(db)) as conn:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(trades)").fetchall()}
        assert "ai_decision" not in cols  # 実体は変わっていない

    def test_no_table_returns_empty(self, tmp_path):
        db = tmp_path / "test.db"
        # 空DBを作るが trades テーブルは作らない
        sqlite3.connect(str(db)).close()
        result = migrate_mod.migrate(db)
        assert result["table_exists"] is False
        assert result["added"] == []

    def test_missing_db_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            migrate_mod.migrate(tmp_path / "nope.db")


# ============================================================
# 3. analyze_ai_ab 集計
# ============================================================


def _seed_db(db_path: Path, rows: list[dict]) -> None:
    """テスト用 trades 行を投入する（AIカラム込みの新スキーマ）。"""
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT NOT NULL UNIQUE,
                instrument TEXT NOT NULL,
                units INTEGER NOT NULL,
                open_price REAL NOT NULL,
                close_price REAL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                pl REAL,
                opened_at TEXT NOT NULL,
                closed_at TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                ai_decision TEXT,
                ai_confidence REAL,
                ai_reasons TEXT,
                ai_direction TEXT,
                ai_regime TEXT
            )"""
        )
        for r in rows:
            conn.execute(
                """INSERT INTO trades
                   (trade_id, instrument, units, open_price, close_price,
                    stop_loss, take_profit, pl, opened_at, closed_at, status,
                    ai_decision, ai_confidence, ai_reasons, ai_direction, ai_regime)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'closed',
                           ?, ?, ?, ?, ?)""",
                (
                    r["trade_id"], r["instrument"], r["units"],
                    150.0, 150.5, 149.0, 152.0,
                    r["pl"], r["opened_at"], r["closed_at"],
                    r["ai_decision"], r["ai_confidence"], r.get("ai_reasons"),
                    r["ai_direction"], r["ai_regime"],
                ),
            )


class TestAnalyzeAggregate:
    def test_group_stats_basic(self):
        s = analyze_mod.GroupStats(label="x")
        s.add(100.0)
        s.add(-50.0)
        s.add(0.0)
        assert s.count == 3
        assert s.wins == 1
        assert s.losses == 1
        assert s.total_pl == pytest.approx(50.0)
        assert s.win_rate == pytest.approx(50.0)
        assert s.avg_pl == pytest.approx(50.0 / 3)

    def test_group_stats_ci95_zero_when_empty(self):
        s = analyze_mod.GroupStats(label="x")
        assert s.win_rate_ci95() == (0.0, 0.0)

    def test_group_stats_ci95_bounds_within_0_100(self):
        s = analyze_mod.GroupStats(label="x")
        for _ in range(10):
            s.add(100.0)
        low, high = s.win_rate_ci95()
        assert 0.0 <= low <= 100.0
        assert 0.0 <= high <= 100.0
        # 全勝 → CI 上限 100、下限 100 未満
        assert low < 100.0
        assert high == pytest.approx(100.0)

    def test_aggregate_decision_split(self):
        trades = [
            {"pl": 100.0, "ai_decision": "CONFIRM", "ai_direction": "bullish", "ai_confidence": 0.8},
            {"pl": -50.0, "ai_decision": "CONFIRM", "ai_direction": "bullish", "ai_confidence": 0.8},
            {"pl": 30.0, "ai_decision": "NEUTRAL", "ai_direction": "neutral", "ai_confidence": 0.2},
            {"pl": -20.0, "ai_decision": "CONTRADICT", "ai_direction": "bearish", "ai_confidence": 0.9},
        ]
        agg = analyze_mod.aggregate(trades)
        assert agg["by_decision"]["CONFIRM"].count == 2
        assert agg["by_decision"]["CONFIRM"].wins == 1
        assert agg["by_decision"]["CONFIRM"].losses == 1
        assert agg["by_decision"]["NEUTRAL"].count == 1
        assert agg["by_decision"]["CONTRADICT"].count == 1

        # NEUTRAL 除外比較
        assert agg["compare"]["all"].count == 4
        assert agg["compare"]["exclude_neutral"].count == 3

    def test_aggregate_confidence_bins(self):
        trades = [
            {"pl": 1.0, "ai_decision": "CONFIRM", "ai_direction": "bullish", "ai_confidence": 0.45},
            {"pl": 1.0, "ai_decision": "CONFIRM", "ai_direction": "bullish", "ai_confidence": 0.6},
            {"pl": 1.0, "ai_decision": "CONFIRM", "ai_direction": "bullish", "ai_confidence": 0.8},
            {"pl": 1.0, "ai_decision": "CONFIRM", "ai_direction": "bullish", "ai_confidence": 1.0},
        ]
        agg = analyze_mod.aggregate(trades)
        bins = agg["by_confidence"]
        assert bins["0.0-0.5"].count == 1
        assert bins["0.5-0.7"].count == 1
        assert bins["0.7-0.9"].count == 1
        assert bins["0.9-1.0"].count == 1  # 1.0 は inclusive

    def test_aggregate_skips_none_pl(self):
        trades = [
            {"pl": None, "ai_decision": "CONFIRM", "ai_direction": "bullish", "ai_confidence": 0.8},
            {"pl": 100.0, "ai_decision": "CONFIRM", "ai_direction": "bullish", "ai_confidence": 0.8},
        ]
        agg = analyze_mod.aggregate(trades)
        assert agg["compare"]["all"].count == 1

    def test_fetch_trades_filters_null_ai_decision(self, tmp_path):
        db = tmp_path / "ab.db"
        _seed_db(db, [
            {
                "trade_id": "T1", "instrument": "USD_JPY", "units": 1000,
                "pl": 100.0, "opened_at": "2026-04-15T00:00:00",
                "closed_at": "2026-04-15T01:00:00",
                "ai_decision": "CONFIRM", "ai_confidence": 0.8,
                "ai_direction": "bullish", "ai_regime": "trending",
            },
            {
                "trade_id": "T2", "instrument": "USD_JPY", "units": 1000,
                "pl": -50.0, "opened_at": "2026-04-15T00:00:00",
                "closed_at": "2026-04-15T01:00:00",
                "ai_decision": None, "ai_confidence": None,
                "ai_direction": None, "ai_regime": None,
            },
        ])
        rows = analyze_mod.fetch_trades(db)
        assert len(rows) == 1
        assert rows[0]["trade_id"] == "T1"

    def test_build_report_handles_empty(self):
        agg = analyze_mod.aggregate([])
        report = analyze_mod.build_report(agg, "全期間", 0)
        assert "AI A/B サマリ" in report
        assert "決着済み取引なし" in report

    def test_write_csv(self, tmp_path):
        trades = [
            {"pl": 100.0, "ai_decision": "CONFIRM", "ai_direction": "bullish", "ai_confidence": 0.8},
            {"pl": -50.0, "ai_decision": "CONFIRM", "ai_direction": "bullish", "ai_confidence": 0.8},
        ]
        agg = analyze_mod.aggregate(trades)
        out = tmp_path / "out" / "summary.csv"
        analyze_mod.write_csv(out, agg)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "axis" in content
        assert "by_decision" in content
        assert "CONFIRM" in content


# ============================================================
# 4. daily_summary.build_ai_ab_text
# ============================================================


class TestDailySummaryAiAb:
    def test_returns_none_when_empty(self):
        assert daily_mod.build_ai_ab_text([], "test") is None

    def test_produces_decision_breakdown(self):
        trades = [
            {"pl": 100.0, "ai_decision": "CONFIRM"},
            {"pl": -50.0, "ai_decision": "CONFIRM"},
            {"pl": 20.0, "ai_decision": "NEUTRAL"},
        ]
        out = daily_mod.build_ai_ab_text(trades, "直近30日")
        assert "AI A/B サマリ" in out
        assert "CONFIRM" in out
        assert "NEUTRAL" in out
        assert "勝率" in out

    def test_neutral_excluded_diff_appears(self):
        trades = [
            {"pl": 100.0, "ai_decision": "CONFIRM"},
            {"pl": 100.0, "ai_decision": "CONFIRM"},
            {"pl": -200.0, "ai_decision": "NEUTRAL"},
        ]
        out = daily_mod.build_ai_ab_text(trades, "テスト")
        # NEUTRAL を除くと勝率 100% になるので差分行が出る
        assert "NEUTRAL除外" in out

    def test_fetch_ai_ab_trades_handles_legacy_db(self, tmp_path):
        # AIカラム無しの旧スキーマDBで OperationalError → 空配列が返る
        db = tmp_path / "legacy.db"
        _create_legacy_trades_db(db)
        rows = daily_mod.fetch_ai_ab_trades(
            db,
            datetime(2026, 4, 1, tzinfo=timezone.utc),
            datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert rows == []


# ============================================================
# 5. PositionManager の ai_record 永続化
# ============================================================


def _make_ohlcv(close_price: float = 150.0, rows: int = 50) -> pd.DataFrame:
    return pd.DataFrame({
        "open": [close_price] * rows,
        "high": [close_price + 0.5] * rows,
        "low": [close_price - 0.5] * rows,
        "close": [close_price] * rows,
        "volume": [1000] * rows,
    })


def _mock_broker():
    broker = MagicMock(spec=BrokerClient)
    broker.market_order.return_value = {
        "trade_id": "TRD-AB-1", "order_id": "X", "price": 150.0,
        "units": 1000, "status": "filled",
    }
    broker.get_positions.return_value = []
    broker.get_account_summary.return_value = {"balance": 1_000_000}
    broker.get_closed_deal.return_value = None
    return broker


def _mock_rm():
    rm = MagicMock(spec=RiskManager)
    ks = MagicMock(spec=KillSwitch)
    ks.is_trading_allowed.return_value = True
    ks.reason = None
    rm.kill_switch = ks
    rm.check_loss_limits.return_value = (True, None)
    rm.check_consecutive_losses.return_value = (0, False)
    rm.calculate_position_size.return_value = 1.0
    rm.account_balance = 1_000_000
    return rm


def _mock_strategy():
    s = MagicMock(spec=StrategyBase)
    s.calculate_stop_loss.return_value = 149.0
    s.calculate_take_profit.return_value = 152.0
    return s


class TestPositionManagerAiPersistence:
    def test_open_position_persists_ai_record(self, tmp_path):
        db = tmp_path / "pm.db"
        pm = PositionManager(
            broker_client=_mock_broker(),
            risk_manager=_mock_rm(),
            db_path=db,
        )
        ai_record = {
            "ai_decision": "CONFIRM",
            "ai_confidence": 0.85,
            "ai_reasons": "aligned(BUY/bullish)",
            "ai_direction": "bullish",
            "ai_regime": "trending",
        }
        result = pm.open_position(
            "USD_JPY", Signal.BUY, _make_ohlcv(), _mock_strategy(),
            ai_record=ai_record,
        )
        assert result is not None

        with sqlite3.connect(str(db)) as conn:
            row = conn.execute(
                "SELECT ai_decision, ai_confidence, ai_reasons, ai_direction, ai_regime "
                "FROM trades WHERE trade_id = ?",
                ("TRD-AB-1",),
            ).fetchone()
        assert row == ("CONFIRM", 0.85, "aligned(BUY/bullish)", "bullish", "trending")

    def test_open_position_without_ai_record_writes_nulls(self, tmp_path):
        db = tmp_path / "pm.db"
        pm = PositionManager(
            broker_client=_mock_broker(),
            risk_manager=_mock_rm(),
            db_path=db,
        )
        result = pm.open_position(
            "USD_JPY", Signal.BUY, _make_ohlcv(), _mock_strategy(),
        )
        assert result is not None

        with sqlite3.connect(str(db)) as conn:
            row = conn.execute(
                "SELECT ai_decision, ai_confidence FROM trades WHERE trade_id=?",
                ("TRD-AB-1",),
            ).fetchone()
        assert row == (None, None)

    def test_init_db_migrates_legacy_schema(self, tmp_path):
        # 旧スキーマDBに対して PositionManager を初期化すると AI カラムが追加される
        db = tmp_path / "legacy.db"
        _create_legacy_trades_db(db)

        PositionManager(
            broker_client=_mock_broker(),
            risk_manager=_mock_rm(),
            db_path=db,
        )

        with sqlite3.connect(str(db)) as conn:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(trades)").fetchall()}
        assert "ai_decision" in cols
        assert "ai_confidence" in cols
        assert "ai_reasons" in cols
        assert "ai_direction" in cols
        assert "ai_regime" in cols
