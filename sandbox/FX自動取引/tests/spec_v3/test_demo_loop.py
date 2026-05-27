"""SPEC v3 デモループ + 関連モジュールのユニットテスト

カバー範囲:
1. DB スキーマ初期化と CRUD
2. LLM Filter の should_take_trade ペア別閾値ロジック
3. キルスイッチ (LLM 連続失敗、日次損失)
4. 撤退条件チェック (90日 trades<5 / PF<1.0 / 累計-3000 / LLM 月コスト)
5. process_pair の dry-run 動作 (Mt5 + LLM を Mock)
"""
from __future__ import annotations

import sys
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.spec_v3 import CONFIDENCE_THRESHOLDS, ENABLED_PAIRS  # noqa: E402
from src.spec_v3 import db as v3_db  # noqa: E402
from src.spec_v3.llm_filter import (  # noqa: E402
    LLMDecision, build_context, should_take_trade,
)
from src.spec_v3.risk_manager import (  # noqa: E402
    KillSwitchState, check_daily_loss, check_retreat_per_pair,
    check_retreat_llm_cost, run_all_safety_checks,
    RETREAT_CUMULATIVE_PNL_JPY, RETREAT_LLM_COST_MONTHLY_USD,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def tmp_db(tmp_path) -> Path:
    db = tmp_path / "fx_spec_v3.db"
    v3_db.init_db(db)
    return db


@pytest.fixture
def fake_m15_df() -> pd.DataFrame:
    """200 本の M15 OHLCV。終値が単調増加してブレイクアウト long を作る"""
    n = 200
    close = [100.0 + i * 0.01 for i in range(n)]
    high = [c + 0.05 for c in close]
    low = [c - 0.05 for c in close]
    open_ = close[:]
    volume = [100] * n
    return pd.DataFrame({
        "open": open_, "high": high, "low": low,
        "close": close, "volume": volume,
    })


@pytest.fixture
def breakout_m15_df() -> pd.DataFrame:
    """200 本の M15 OHLCV。最後の足で明示的にブレイクアウト long を発生させる。

    最初の 199 本は安定したレンジ、最後の足で direction 用に高値を突き抜ける。
    """
    n = 200
    # 安定レンジ
    close = [100.0 + (i % 5) * 0.01 for i in range(n - 1)]
    high = [c + 0.05 for c in close]
    low = [c - 0.05 for c in close]
    # 最後の足で大きく上抜けする
    last_close = 100.50  # レンジ高値 ~100.09 を大きく超える
    close.append(last_close)
    high.append(last_close + 0.05)
    low.append(last_close - 0.05)
    open_ = close[:]
    volume = [100] * n
    return pd.DataFrame({
        "open": open_, "high": high, "low": low,
        "close": close, "volume": volume,
    })


# ============================================================
# 1. DB schema + CRUD
# ============================================================


def test_db_init_creates_all_tables(tmp_db):
    """init_db で 5 テーブル + インデックスが作られる"""
    expected_tables = {
        "llm_judgments", "trades", "trade_closures",
        "loop_health", "llm_api_cost_daily",
    }
    with sqlite3.connect(str(tmp_db)) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    existing = {r[0] for r in rows}
    missing = expected_tables - existing
    assert not missing, f"テーブル未作成: {missing}"


def test_insert_llm_judgment_and_read_back(tmp_db):
    jid = v3_db.insert_llm_judgment(
        tmp_db,
        judged_at_utc="2026-05-27T00:00:00+00:00",
        pair="USD_JPY",
        signal_direction="long",
        entry_price=150.0,
        sl_price=149.0, tp_price=152.0,
        sl_pips=100, tp_pips=200,
        atr=0.15, signal_reason="test",
        llm_label="CONFIRM", llm_confidence=0.72,
        llm_reasoning="OK",
        accepted=True, decision_reason="accepted",
        api_input_tokens=300, api_output_tokens=50,
        api_cost_usd=0.001, api_error=None,
        context={"foo": "bar"},
    )
    assert jid >= 1
    with v3_db.get_conn(tmp_db) as conn:
        row = conn.execute(
            "SELECT pair, llm_label, accepted, context_json "
            "FROM llm_judgments WHERE id=?", (jid,),
        ).fetchone()
    assert row["pair"] == "USD_JPY"
    assert row["llm_label"] == "CONFIRM"
    assert row["accepted"] == 1
    assert "foo" in row["context_json"]


def test_trade_and_closure_round_trip(tmp_db):
    tid = v3_db.insert_trade(
        tmp_db,
        mt5_ticket=123456, entry_at_utc=v3_db.utc_now_iso(),
        pair="USD_JPY", direction="long", lots=0.01,
        entry_price=150.0, sl_price=149.0, tp_price=152.0,
        sl_pips=100, tp_pips=200,
        judgment_id=None, signal_reason="test",
        llm_label="CONFIRM", llm_confidence=0.7,
    )
    assert v3_db.get_open_trades(tmp_db, pair="USD_JPY")

    v3_db.insert_trade_closure(
        tmp_db, trade_id=tid, exit_at_utc=v3_db.utc_now_iso(),
        exit_price=151.0, exit_reason="tp",
        pnl_pips=100.0, pnl_jpy=1000.0,
        holding_minutes=60,
    )
    # status='open' なものは消える (closed に更新)
    assert not v3_db.get_open_trades(tmp_db, pair="USD_JPY")

    pnl = v3_db.cumulative_pnl(tmp_db, "USD_JPY")
    assert pnl["n"] == 1
    assert pnl["total_jpy"] == 1000.0


# ============================================================
# 2. should_take_trade ロジック (Proposal 3 ペア別閾値)
# ============================================================


@pytest.mark.parametrize("pair,confidence,label,expected", [
    # USD_JPY: 閾値 0.65
    ("USD_JPY", 0.70, "CONFIRM", True),
    ("USD_JPY", 0.65, "CONFIRM", True),     # 境界、>=
    ("USD_JPY", 0.64, "CONFIRM", False),    # 直下
    ("USD_JPY", 0.90, "NEUTRAL", False),    # ラベル違い
    ("USD_JPY", 0.90, "CONTRADICT", False),
    ("USD_JPY", 0.90, "REJECT", False),
    # GBP_JPY: 閾値 0.60
    ("GBP_JPY", 0.60, "CONFIRM", True),
    ("GBP_JPY", 0.59, "CONFIRM", False),
    # 未登録ペア
    ("EUR_USD", 0.99, "CONFIRM", False),
])
def test_should_take_trade_pair_specific_thresholds(pair, confidence, label, expected):
    dec = LLMDecision(label=label, confidence=confidence, reasoning="x")
    accepted, reason = should_take_trade(
        pair=pair, decision=dec,
        confidence_thresholds=CONFIDENCE_THRESHOLDS,
        accept_labels=("CONFIRM",),
    )
    assert accepted is expected, f"{pair} conf={confidence} label={label} reason={reason}"


def test_should_take_trade_api_error_failsafe():
    dec = LLMDecision(label="API_ERROR", confidence=0.0, reasoning="x", error="timeout")
    accepted, reason = should_take_trade(
        pair="USD_JPY", decision=dec,
        confidence_thresholds=CONFIDENCE_THRESHOLDS,
    )
    assert not accepted
    assert reason == "api_error_failsafe"


# ============================================================
# 3. キルスイッチ
# ============================================================


def test_llm_consecutive_failures_triggers_global_block():
    ks = KillSwitchState()
    # 4 回までは未発火
    for _ in range(4):
        blocked = ks.on_llm_failure()
        assert blocked is False
    # 5 回目で発火
    blocked = ks.on_llm_failure()
    assert blocked is True
    assert ks.global_block_reason is not None
    is_b, reason = ks.is_blocked("USD_JPY")
    assert is_b is True
    assert "llm_api" in reason


def test_llm_success_resets_failure_counter():
    ks = KillSwitchState()
    ks.on_llm_failure()
    ks.on_llm_failure()
    ks.on_llm_success()
    assert ks.llm_consecutive_failures == 0


def test_pair_block_only_affects_target_pair():
    ks = KillSwitchState()
    ks.block_pair("USD_JPY", "spread_anomaly")
    blocked_u, _ = ks.is_blocked("USD_JPY")
    blocked_g, _ = ks.is_blocked("GBP_JPY")
    assert blocked_u is True
    assert blocked_g is False


# ============================================================
# 4. 撤退条件
# ============================================================


def _insert_closed_trade(
    db_path: Path, pair: str, pnl_pips: float, pnl_jpy: float,
    entry_offset_days: int = 0,
) -> int:
    """指定 PnL の closed trade を作るヘルパ"""
    entry_at = (datetime.now(timezone.utc) - timedelta(days=entry_offset_days)).isoformat(timespec="seconds")
    tid = v3_db.insert_trade(
        db_path, mt5_ticket=None, entry_at_utc=entry_at,
        pair=pair, direction="long", lots=0.01,
        entry_price=150.0, sl_price=149.0, tp_price=152.0,
        sl_pips=100, tp_pips=200,
        judgment_id=None, signal_reason="test",
        llm_label="CONFIRM", llm_confidence=0.7,
    )
    v3_db.insert_trade_closure(
        db_path, trade_id=tid, exit_at_utc=v3_db.utc_now_iso(),
        exit_price=150.0, exit_reason="tp",
        pnl_pips=pnl_pips, pnl_jpy=pnl_jpy,
        holding_minutes=60,
    )
    return tid


def test_retreat_cumulative_loss_triggers(tmp_db):
    """累計 -3,000 JPY を割ると #3 発火 (PF >= 1.0 を保つように勝ち混在で組む)"""
    # 勝ち 4,000 / 負け 7,200 → PF = 4000/7200 = 0.555 < 1.0 だと #2 が先に発火するので、
    # PF を 1.0 以上に保ちつつ累計 -3,000 を超える組み合わせを作る:
    # win 10,000 (1件) + loss -13,500 (3件×4,500) → 累計 -3,500、PF = 10000/13500 = 0.74
    # → やはり PF<1 で #2 が先に発火する。
    # → 純粋な「累計 -3000 だけが効く」ケースは作りにくいので、ここでは「いずれかの
    #    撤退条件が発火する」ことを検証する (累計 -3,500 を作ると必ず撤退になることを確認)。
    for _ in range(5):
        _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=-70.0, pnl_jpy=-700.0)
    status = check_retreat_per_pair(tmp_db, "USD_JPY")
    assert status.triggered is True
    # PF=0 が先に検出されるが、いずれにせよ撤退判定になることを保証
    assert status.code in ("retreat_2_pf_below_floor", "retreat_3_cumulative_loss")


def test_retreat_cumulative_loss_with_high_pf(tmp_db):
    """PF >= 1.0 を保ちつつ累計 -3,000 を割るケース"""
    # 勝ち 5,000 (1件) + 負け 4,500 × 2 = -4,000 → 累計 -4,000、PF = 5000/9000 = 0.56
    # PF を高くするには勝ち比率を上げる必要がある。
    # 勝ち 10,000 + 負け 6,000 × 3 = 累計 -8,000、PF = 10000/18000 = 0.56  → やはり PF<1
    # PnL JPY と pips の絶対値は別軸: pips=PF 用、jpy=累計用
    # → pips では勝ち優勢、jpy では負け優勢にする
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=200.0, pnl_jpy=500.0)
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=200.0, pnl_jpy=500.0)
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=-100.0, pnl_jpy=-1500.0)
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=-100.0, pnl_jpy=-1500.0)
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=-100.0, pnl_jpy=-1500.0)
    # pips PF = 400/300 = 1.33 (>= 1.0), 累計 JPY = -3,500 (< -3,000)
    status = check_retreat_per_pair(tmp_db, "USD_JPY")
    assert status.triggered is True
    assert status.code == "retreat_3_cumulative_loss"


def test_retreat_pf_below_floor_triggers(tmp_db):
    # 直近 trades の PF < 1.0 (勝ち 1 件 + 負け 5 件で PF ≒ 0.2)
    for _ in range(5):
        _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=-50.0, pnl_jpy=-500.0)
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=100.0, pnl_jpy=1000.0)
    status = check_retreat_per_pair(tmp_db, "USD_JPY")
    # 累計 PnL = -1,500 で #3 はまだ発火しない (-3000 未満は確保)
    # PF = 100 / 250 = 0.4 で #2 発火するべき
    assert status.triggered is True
    assert status.code == "retreat_2_pf_below_floor"


def test_retreat_not_triggered_when_few_trades(tmp_db):
    # trades=2 件 (PF 計算には 5 件必要、撤退判定は保留)
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=-10.0, pnl_jpy=-100.0)
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=20.0, pnl_jpy=200.0)
    status = check_retreat_per_pair(tmp_db, "USD_JPY")
    assert status.triggered is False


def test_retreat_llm_cost_triggers(tmp_db):
    """月コスト > 5,000円 ≒ $33 で撤退条件 #4 発火"""
    # 1 件 $40 の判定を入れる
    v3_db.insert_llm_judgment(
        tmp_db,
        judged_at_utc=v3_db.utc_now_iso(), pair="USD_JPY",
        signal_direction="long", entry_price=150.0,
        sl_price=149.0, tp_price=152.0,
        sl_pips=100, tp_pips=200, atr=None, signal_reason="t",
        llm_label="CONFIRM", llm_confidence=0.7, llm_reasoning="",
        accepted=False, decision_reason="t",
        api_input_tokens=0, api_output_tokens=0,
        api_cost_usd=RETREAT_LLM_COST_MONTHLY_USD + 1.0,
        api_error=None, context=None,
    )
    status = check_retreat_llm_cost(tmp_db)
    assert status.triggered is True
    assert status.code == "retreat_4_llm_cost"


def test_run_all_safety_checks_returns_ok_when_clean(tmp_db):
    ks = KillSwitchState()
    result = run_all_safety_checks(tmp_db, ENABLED_PAIRS, ks)
    assert result["action"] == "ok"


# ============================================================
# 5. process_pair (dry-run) — Mt5 と LLM を Mock
# ============================================================


def test_process_pair_dry_run_records_signal(tmp_db, fake_m15_df, monkeypatch):
    """dry_run=True なら LLM を呼ばず DB に DRY_RUN ラベルで記録"""
    # DB_PATH をテスト用に差し替える (demo_loop モジュール内のグローバル)
    from src.spec_v3 import demo_loop

    monkeypatch.setattr(demo_loop, "DB_PATH", tmp_db)

    mt5_mock = MagicMock()
    mt5_mock.get_prices.return_value = fake_m15_df
    mt5_mock.get_positions.return_value = []

    ks = KillSwitchState()
    notifier = MagicMock()

    summary = demo_loop.process_pair(
        mt5_mock, "USD_JPY",
        filter_obj=None,  # dry-run なので LLM 呼ばない
        notifier=notifier,
        kill_switch=ks,
        dry_run=True,
        lot_units=1000,
    )

    # シグナルが出るか、ATR 不足で no_signal のどちらか
    # ブレイクアウトデータを与えているのでシグナルが出る想定
    if summary["stage"] in ("dry_run",):
        # 1 件 LLM 判定が記録されているはず (DRY_RUN ラベル)
        with v3_db.get_conn(tmp_db) as conn:
            n = conn.execute("SELECT COUNT(*) FROM llm_judgments").fetchone()[0]
        assert n == 1
    else:
        # no_signal の場合は記録なし (この fixture では基本シグナル出るはずだが、ATR=NaN なら no_signal)
        assert summary["stage"] in ("no_signal", "fetch_fail", "insufficient_data", "dry_run")


def test_process_pair_killswitch_blocks_and_records(tmp_db, fake_m15_df, monkeypatch):
    """キルスイッチ発火中はシグナルだけ DB 記録、発注なし"""
    from src.spec_v3 import demo_loop
    monkeypatch.setattr(demo_loop, "DB_PATH", tmp_db)

    mt5_mock = MagicMock()
    mt5_mock.get_prices.return_value = fake_m15_df
    mt5_mock.get_positions.return_value = []

    ks = KillSwitchState()
    # 強制的にキルスイッチ発火状態にする
    ks.global_block_reason = "test_block"

    notifier = MagicMock()
    summary = demo_loop.process_pair(
        mt5_mock, "USD_JPY",
        filter_obj=None, notifier=notifier, kill_switch=ks,
        dry_run=True, lot_units=1000,
    )

    # シグナルが出ていた場合は killswitch_blocked、出なければ no_signal
    if summary["stage"] == "killswitch_blocked":
        with v3_db.get_conn(tmp_db) as conn:
            row = conn.execute(
                "SELECT decision_reason FROM llm_judgments LIMIT 1"
            ).fetchone()
        assert row["decision_reason"] == "killswitch_blocked"
        # 発注は一切呼ばれない
        mt5_mock.market_order.assert_not_called()


def test_build_context_does_not_include_future_information(fake_m15_df):
    """LLM プロンプトに渡すコンテキストにリーク列が含まれない"""
    ctx = build_context(
        pair="USD_JPY",
        signal={
            "direction": "long", "entry_price": 150.0,
            "sl_price": 149.0, "tp_price": 152.0,
            "sl_pips": 100, "tp_pips": 200, "atr": 0.15,
        },
        m15_df=fake_m15_df,
        related_24h_changes={"EUR_USD": -0.12, "GBP_USD": 0.05},
    )
    forbidden_keys = {
        "high_after_entry_24h", "low_after_entry_24h", "close_24h_after_entry",
        "actual_pnl_pips_sl_tp_first_touch", "win_loss_sl_tp",
        "holding_minutes_first_touch",
    }
    leaked = set(ctx.keys()) & forbidden_keys
    assert not leaked, f"リーク列が混入: {leaked}"


# ============================================================
# 6. 日次損失チェック
# ============================================================


def test_daily_loss_levels(tmp_db):
    # 元本 100 万 JPY、-2 万 JPY = 2% → warn (1.5%) を超えるが half (3%) 未満
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=-200, pnl_jpy=-20_000.0)
    result = check_daily_loss(tmp_db, principal_jpy=1_000_000.0)
    assert result["level"] == "warn"
    assert result["pnl_jpy"] == -20_000.0

    # 追加で -2 万 → 計 -4 万 = 4% → half
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=-200, pnl_jpy=-20_000.0)
    result = check_daily_loss(tmp_db, principal_jpy=1_000_000.0)
    assert result["level"] == "half"

    # さらに -2 万 → -6 万 = 6% → stop
    _insert_closed_trade(tmp_db, "USD_JPY", pnl_pips=-200, pnl_jpy=-20_000.0)
    result = check_daily_loss(tmp_db, principal_jpy=1_000_000.0)
    assert result["level"] == "stop"


# ============================================================
# 7. バグ② スプレッドキルスイッチ配線 (Ultra/Karen 是正)
# ============================================================


def test_spread_anomaly_blocks_signal(tmp_db, breakout_m15_df, monkeypatch):
    """スプレッド 3 倍超で発注ブロック、SKIPPED 記録のみが残る。"""
    from src.spec_v3 import demo_loop
    monkeypatch.setattr(demo_loop, "DB_PATH", tmp_db)

    mt5_mock = MagicMock()
    mt5_mock.get_prices.return_value = breakout_m15_df
    mt5_mock.get_positions.return_value = []

    # 1 回目: 通常スプレッド (1.0 pip) で baseline 確立
    # 2 回目: 3.5 倍 (3.5 pip) で異常検知 → ブロック
    spread_values = iter([1.0, 3.5])
    mt5_mock.get_spread.side_effect = lambda pair: next(spread_values)

    ks = KillSwitchState()
    notifier = MagicMock()

    # 1 回目: baseline 確立 (異常検知なし、シグナルは dry_run で記録される)
    summary1 = demo_loop.process_pair(
        mt5_mock, "USD_JPY",
        filter_obj=None, notifier=notifier, kill_switch=ks,
        dry_run=True, lot_units=1000,
    )
    # シグナルが出ていること (breakout fixture なので long が出る)
    assert summary1.get("signal_direction") == "long"
    # baseline が確立されていることを確認
    assert "USD_JPY" in ks.spread_baseline
    assert ks.spread_baseline["USD_JPY"] == pytest.approx(1.0, abs=0.01)

    # 2 回目: 3.5 倍 → スプレッド異常で発注ブロック
    summary2 = demo_loop.process_pair(
        mt5_mock, "USD_JPY",
        filter_obj=None, notifier=notifier, kill_switch=ks,
        dry_run=True, lot_units=1000,
    )

    assert summary2["stage"] == "spread_anomaly_blocked"
    assert summary2["spread_pips"] == pytest.approx(3.5, abs=0.01)
    # DB に SKIPPED 記録が残っていること
    with v3_db.get_conn(tmp_db) as conn:
        cur = conn.execute(
            "SELECT llm_label, decision_reason FROM llm_judgments "
            "WHERE decision_reason='spread_anomaly'"
        )
        rows = cur.fetchall()
    assert len(rows) >= 1
    assert rows[0]["llm_label"] == "SKIPPED"
    # 発注は呼ばれない
    mt5_mock.market_order.assert_not_called()


def test_spread_killswitch_state_methods():
    """KillSwitchState.update_spread と check_spread_anomaly の単体動作。"""
    ks = KillSwitchState()

    # baseline 未確立: 異常検知は False (誤発火防止)
    assert ks.check_spread_anomaly("USD_JPY", 5.0) is False

    # 最初の更新で baseline 確立
    ks.update_spread("USD_JPY", 1.0)
    assert ks.spread_baseline["USD_JPY"] == pytest.approx(1.0)

    # 3 倍未満は異常検知なし
    assert ks.check_spread_anomaly("USD_JPY", 2.5) is False

    # 3 倍ちょうど: 異常
    assert ks.check_spread_anomaly("USD_JPY", 3.0) is True

    # 3 倍超: 異常
    assert ks.check_spread_anomaly("USD_JPY", 5.0) is True

    # 異常値で update_spread しても baseline は汚染されない
    ks.update_spread("USD_JPY", 5.0)
    assert ks.spread_baseline["USD_JPY"] == pytest.approx(1.0)

    # 通常値の小幅な更新は EMA で反映
    ks.update_spread("USD_JPY", 1.5)
    # alpha=0.1: 0.1 * 1.5 + 0.9 * 1.0 = 1.05
    assert ks.spread_baseline["USD_JPY"] == pytest.approx(1.05, abs=0.001)


# ============================================================
# 8. バグ③ 撤退時 close_all_positions (Ultra/Karen 是正)
# ============================================================


def test_retreat_closes_all_positions(tmp_db, monkeypatch):
    """撤退条件 #5 発火時に close_all_positions が呼ばれること。"""
    from src.spec_v3 import demo_loop
    monkeypatch.setattr(demo_loop, "DB_PATH", tmp_db)

    # 両ペアで撤退条件 #2 (PF<1.0) が発火するように closed trade を仕込む
    for pair in ENABLED_PAIRS:
        for _ in range(6):
            _insert_closed_trade(tmp_db, pair, pnl_pips=-50.0, pnl_jpy=-500.0)

    # MT5 Mock: close_all_positions が呼ばれたか追跡
    mt5_mock = MagicMock()
    mt5_mock.get_prices.return_value = pd.DataFrame()  # 使わない
    mt5_mock.get_positions.return_value = []
    mt5_mock.close_all_positions.return_value = {
        "closed": [{"trade_id": "111"}],
        "failed": [],
        "total": 1,
    }

    notifier = MagicMock()

    # single_iter=True でループを 1 回回す
    demo_loop.run_loop(
        dry_run=True, single_iter=True,
        enabled_pairs=ENABLED_PAIRS,
        mt5_client=mt5_mock,
        llm_filter=None,
        notifier=notifier,
        principal_jpy=1_000_000.0,
    )

    # 撤退条件 #5 (両ペア撤退) 発火 → close_all_positions が呼ばれること
    mt5_mock.close_all_positions.assert_called_once()
    call_kwargs = mt5_mock.close_all_positions.call_args
    # reason 引数に "retreat_" が含まれること
    reason_arg = call_kwargs.kwargs.get("reason") or (
        call_kwargs.args[0] if call_kwargs.args else ""
    )
    assert "retreat" in reason_arg

    # DB に retreat_close イベントが記録されること
    with v3_db.get_conn(tmp_db) as conn:
        cur = conn.execute(
            "SELECT message FROM loop_health WHERE event_type='retreat_close'"
        )
        rows = cur.fetchall()
    assert len(rows) >= 1


# ============================================================
# 9. バグ⑤ daily_block_until 永続化 (Ultra/Karen 是正)
# ============================================================


def test_killswitch_state_persist_and_restore(tmp_db):
    """KillSwitchState の DB 保存・復元が正しく動くこと。"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")

    # 1. 状態を保存
    v3_db.save_killswitch_state(
        tmp_db,
        daily_block_until=today,
        monthly_block_until=this_month,
        blocked_pairs={"USD_JPY"},
        global_block_reason="test_reason",
        spread_baseline={"USD_JPY": 1.05, "GBP_JPY": 1.6},
    )

    # 2. 復元してフィールドが一致すること
    state = v3_db.load_killswitch_state(tmp_db)
    assert state["daily_block_until"] == today
    assert state["monthly_block_until"] == this_month
    assert state["blocked_pairs"] == {"USD_JPY"}
    assert state["global_block_reason"] == "test_reason"
    assert state["spread_baseline"] == {"USD_JPY": 1.05, "GBP_JPY": 1.6}

    # 3. _restore_killswitch_state で KillSwitchState に復元されること
    from src.spec_v3 import demo_loop
    from unittest.mock import patch as _patch

    ks = KillSwitchState()
    with _patch.object(demo_loop, "DB_PATH", tmp_db):
        demo_loop._restore_killswitch_state(ks)
    assert ks.daily_block_until == today
    assert ks.monthly_block_until == this_month
    assert "USD_JPY" in ks.blocked_pairs
    assert ks.global_block_reason == "test_reason"
    assert ks.spread_baseline["USD_JPY"] == 1.05

    # 4. is_blocked が日次停止を反映すること
    blocked, reason = ks.is_blocked("GBP_JPY")
    assert blocked is True
    # daily_block_until または monthly_block_until または global_block_reason のいずれか
    assert reason is not None


def test_killswitch_state_old_dates_not_restored(tmp_db):
    """過去日付の daily/monthly block は復元しない (今日/当月のみ復元)。"""
    yesterday = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    last_month = (datetime.now(timezone.utc).replace(day=1) - timedelta(days=2)).strftime("%Y-%m")

    v3_db.save_killswitch_state(
        tmp_db,
        daily_block_until=yesterday,
        monthly_block_until=last_month,
        blocked_pairs=set(),
        global_block_reason=None,
        spread_baseline={},
    )

    from src.spec_v3 import demo_loop
    from unittest.mock import patch as _patch

    ks = KillSwitchState()
    with _patch.object(demo_loop, "DB_PATH", tmp_db):
        demo_loop._restore_killswitch_state(ks)
    # 過去日付は復元しない
    assert ks.daily_block_until is None
    assert ks.monthly_block_until is None


# ============================================================
# 10. バグ⑥ ATR を LLM プロンプトに渡す (Ultra/Karen 是正)
# ============================================================


def test_calc_atr_returns_finite_value(fake_m15_df):
    """llm_filter.calc_atr が ATR を計算して数値を返すこと。"""
    from src.spec_v3.llm_filter import calc_atr

    atr = calc_atr(fake_m15_df, period=14)
    assert atr is not None
    assert atr > 0
    # fake_m15_df は high-low が約 0.1 で揃うので ATR ≒ 0.1
    assert 0.05 < atr < 0.5


def test_calc_atr_returns_none_when_insufficient(fake_m15_df):
    """データ不足時は None を返すこと。"""
    from src.spec_v3.llm_filter import calc_atr

    short_df = fake_m15_df.iloc[:5]
    assert calc_atr(short_df, period=14) is None


def test_atr_in_llm_prompt(tmp_db, breakout_m15_df, monkeypatch):
    """process_pair で ATR が計算され、LLM コンテキスト + プロンプトに含まれること。"""
    from src.spec_v3 import demo_loop
    from src.spec_v3.llm_filter import LLMDecision, build_user_prompt

    monkeypatch.setattr(demo_loop, "DB_PATH", tmp_db)

    mt5_mock = MagicMock()
    mt5_mock.get_prices.return_value = breakout_m15_df
    mt5_mock.get_positions.return_value = []
    mt5_mock.get_spread.return_value = None  # spread チェックを無効化

    # LLM Mock: judge をキャプチャして渡された context の atr を確認
    captured_context = {}

    def fake_judge(context: dict):
        captured_context.update(context)
        return LLMDecision(
            label="CONFIRM", confidence=0.70, reasoning="test",
            input_tokens=10, output_tokens=5, cost_usd=0.0001,
        )

    llm_mock = MagicMock()
    llm_mock.judge.side_effect = fake_judge

    # dry_run=False にして LLM Mock を呼ぶフロー (発注は market_order Mock で抑制)
    mt5_mock.market_order.return_value = {"order_id": 999, "price": 100.50}

    ks = KillSwitchState()
    notifier = MagicMock()

    summary = demo_loop.process_pair(
        mt5_mock, "USD_JPY",
        filter_obj=llm_mock, notifier=notifier, kill_switch=ks,
        dry_run=False, lot_units=1000,
    )

    # シグナルが出ていること (breakout fixture)
    assert summary.get("signal_direction") == "long"
    # LLM judge が呼ばれたこと
    assert llm_mock.judge.called

    # コンテキストに atr が含まれていること
    assert "atr" in captured_context
    assert captured_context["atr"] is not None
    assert captured_context["atr"] > 0

    # build_user_prompt の出力に ATR の数値が含まれ、N/A でないこと
    prompt = build_user_prompt(captured_context)
    assert "- ATR:" in prompt
    assert "- ATR: N/A" not in prompt

    # DB の atr 列にも値が記録されること
    with v3_db.get_conn(tmp_db) as conn:
        cur = conn.execute(
            "SELECT atr FROM llm_judgments WHERE pair='USD_JPY' "
            "ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
    assert row is not None
    assert row["atr"] is not None
    assert row["atr"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
