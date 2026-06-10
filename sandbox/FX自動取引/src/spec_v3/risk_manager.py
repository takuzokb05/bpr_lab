"""SPEC v3 — リスク管理 (キルスイッチ + 撤退条件)

CLAUDE.md 安全性原則準拠:
- 日次最大損失上限: -1.5% 警告 / -3% 半量化 / -5% 停止
- 月間最大損失上限: -10% で月停止
- 元本 1%/trade の SL を超える発注は拒否
- 1 ペア同時 1 ポジション、全体 2 ポジション

キルスイッチ (SPEC_V3.md § 5.2):
- 連続 LLM API 障害 5 回 → 全ペア新規発注停止
- スプレッド 3 倍拡大 → 当該ペア新規発注停止
- (VIX > 30, ±3σ 急変はメモリ上のみ実装、外部データ依存のためデフォルト無効)

撤退条件 (SPEC_V3.md § 4.5、CYCLE2_PLAN.md L156-160):
1. 90 日 trades < 5 (当該ペア)
2. 直近 100 trades で PF < 1.0 維持 (当該ペア)
3. 累計 -3,000 JPY (当該ペア)
4. LLM API 月コスト > 5,000円 (システム全体、LLM 層無効化)
5. 両ペアで 1-3 が成立 (SPEC v3 全体停止)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.spec_v3 import db as v3_db

logger = logging.getLogger(__name__)


# ============================================================
# 損失上限 (元本に対する比率)
# ============================================================

DAILY_LOSS_WARN_PCT = 0.015          # -1.5%
DAILY_LOSS_HALF_PCT = 0.03           # -3%
DAILY_LOSS_STOP_PCT = 0.05           # -5%
MONTHLY_LOSS_STOP_PCT = 0.10         # -10%

# 元本 (Phase 2'A のデモ口座、SPEC v3 では JPY 1,000,000 想定)
DEFAULT_PRINCIPAL_JPY = 1_000_000.0

# 撤退条件
RETREAT_DAYS_NO_TRADES = 90
RETREAT_MIN_TRADES_REQUIRED = 5
RETREAT_PF_FLOOR = 1.0
RETREAT_PF_WINDOW = 100              # 直近 100 trades
# PF 撤退判定に必要な最小 trade 数。n=5 では 1 取引の異常値で発火する
# (2026-06-09: SL 未設定事故の 1 取引が PF を 1.25→0.739 に押し下げて発火)。
# FreqTrade MaxDrawdown protection の trade_limit=20 に倣う。
RETREAT_PF_MIN_TRADES = 20
RETREAT_CUMULATIVE_PNL_JPY = -3_000.0
RETREAT_LLM_COST_MONTHLY_USD = 5_000.0 / 150.0  # 5,000円 ÷ 150円/USD ≒ $33

# 撤退条件 #0 (Ultra H-② 是正、2026-05-28): lift = PF(LLM_after) - PF(base) が
# 3 ヶ月連続で +0.30 未満なら当該ペア停止。SPEC v3 § 4.5 の M2 提案を実装層に配線。
# - lift_window_days: 月 1 評価とするローリング 30 日のウィンドウ
# - lift_threshold: SPEC §4.5 の "+0.30"
# - lift_consecutive_months: 3 ヶ月連続 (= 3 回連続未達)
# - lift_min_trades: 月単位の PF を計算するために必要な最小 trade 数 (n<5 なら未確定扱い)
RETREAT_LIFT_THRESHOLD = 0.30
RETREAT_LIFT_WINDOW_DAYS = 30
RETREAT_LIFT_CONSECUTIVE_MONTHS = 3
RETREAT_LIFT_MIN_TRADES = 5

# キルスイッチ閾値
KILLSWITCH_LLM_CONSECUTIVE_FAILURES = 5
KILLSWITCH_SPREAD_MULTIPLIER = 3.0


# ============================================================
# キルスイッチ状態
# ============================================================


@dataclass
class KillSwitchState:
    """ループ間で共有するキルスイッチ状態。

    daily_block_until は SQLite (kill_switch_state テーブル) で永続化される。
    プロセス再起動時は v3_db.load_killswitch_state で復元、
    状態変化時は v3_db.save_killswitch_state で保存する。
    (Ultra/Karen バグ⑤ 是正、2026-05-27)
    """
    llm_consecutive_failures: int = 0
    blocked_pairs: set[str] = field(default_factory=set)
    global_block_reason: Optional[str] = None
    daily_block_until: Optional[str] = None  # 'YYYY-MM-DD' (日次損失で当日停止)
    monthly_block_until: Optional[str] = None  # 'YYYY-MM' (月次損失で月末まで停止)

    # スプレッドベースライン (ペア別の EMA、3 倍超で異常検知)
    # キー: pair, 値: float (pips)。Phase 2'A 起動時は SPREAD_WARN_THRESHOLD_PIPS の 1/3 で初期化
    spread_baseline: dict[str, float] = field(default_factory=dict)

    def is_blocked(self, pair: str) -> tuple[bool, Optional[str]]:
        """発注前チェック。(blocked, reason)"""
        # 日次損失で当日全停止
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.daily_block_until is not None and self.daily_block_until >= today:
            return True, f"daily_loss_stop_until_{self.daily_block_until}"
        # 月次損失で月末まで停止
        this_month = datetime.now(timezone.utc).strftime("%Y-%m")
        if self.monthly_block_until is not None and self.monthly_block_until >= this_month:
            return True, f"monthly_loss_stop_until_{self.monthly_block_until}"
        if self.global_block_reason is not None:
            return True, self.global_block_reason
        if pair in self.blocked_pairs:
            return True, f"pair_blocked:{pair}"
        return False, None

    # ============================================================
    # スプレッド異常検知 (Ultra/Karen バグ② 是正、2026-05-27)
    # SPEC v3 § 5.2 キルスイッチ #3 を実装層に配線
    # ============================================================

    def update_spread(self, pair: str, current_pips: float,
                      ema_alpha: float = 0.1) -> None:
        """ペア別スプレッドベースラインを EMA で更新。

        Phase 2'A 起動直後は baseline が None なので、最初の値で初期化する。
        以降は EMA (alpha=0.1) で緩やかに追従。スパイクで baseline が
        汚染されないよう、3 倍超のサンプルは更新に使わない。

        Args:
            pair: 通貨ペア (例: "USD_JPY")
            current_pips: 現在スプレッド (pips)
            ema_alpha: EMA の平滑化係数 (デフォルト 0.1)
        """
        if current_pips is None or current_pips <= 0:
            return
        prev = self.spread_baseline.get(pair)
        if prev is None or prev <= 0:
            self.spread_baseline[pair] = float(current_pips)
            return
        # 異常値は baseline 更新から除外 (baseline を汚染させない)
        if current_pips >= prev * KILLSWITCH_SPREAD_MULTIPLIER:
            logger.debug(
                "pair=%s スプレッド異常値 %.2f (baseline=%.2f) は EMA 更新からスキップ",
                pair, current_pips, prev,
            )
            return
        self.spread_baseline[pair] = (
            ema_alpha * float(current_pips) + (1.0 - ema_alpha) * prev
        )

    def check_spread_anomaly(self, pair: str, current_pips: float,
                              multiplier: float = KILLSWITCH_SPREAD_MULTIPLIER) -> bool:
        """現在スプレッドが基準値の N 倍を超えたら True (= 異常)。

        baseline がまだ確立されていない場合は False を返す (誤発火防止)。
        """
        if current_pips is None or current_pips <= 0:
            return False
        baseline = self.spread_baseline.get(pair)
        if baseline is None or baseline <= 0:
            return False
        return float(current_pips) >= baseline * multiplier

    def on_llm_success(self) -> None:
        if self.llm_consecutive_failures > 0:
            logger.info("LLM 連続失敗カウンタリセット (was=%d)", self.llm_consecutive_failures)
        self.llm_consecutive_failures = 0

    def on_llm_failure(self) -> bool:
        """LLM 失敗を記録。閾値到達でグローバルブロックを返す (True=ブロック発火)。"""
        self.llm_consecutive_failures += 1
        if self.llm_consecutive_failures >= KILLSWITCH_LLM_CONSECUTIVE_FAILURES:
            self.global_block_reason = (
                f"llm_api_consecutive_failures>={KILLSWITCH_LLM_CONSECUTIVE_FAILURES}"
            )
            logger.error("キルスイッチ発火: %s", self.global_block_reason)
            return True
        return False

    def block_pair(self, pair: str, reason: str) -> None:
        self.blocked_pairs.add(pair)
        logger.warning("ペア %s キルスイッチ発火: %s", pair, reason)

    def unblock_global(self) -> None:
        self.global_block_reason = None
        logger.info("グローバルキルスイッチ解除")

    def unblock_pair(self, pair: str) -> None:
        self.blocked_pairs.discard(pair)
        logger.info("ペア %s キルスイッチ解除", pair)


# ============================================================
# スプレッドチェック (キルスイッチ #3)
# ============================================================


def check_spread_anomaly(
    current_spread_pips: float,
    baseline_spread_pips: float,
    multiplier: float = KILLSWITCH_SPREAD_MULTIPLIER,
) -> bool:
    """現在スプレッドが基準値の N 倍を超えたら True (= 異常)"""
    if baseline_spread_pips <= 0:
        return False
    return current_spread_pips >= baseline_spread_pips * multiplier


# ============================================================
# 日次/月次損失チェック
# ============================================================


def check_daily_loss(
    db_path: Path,
    principal_jpy: float = DEFAULT_PRINCIPAL_JPY,
) -> dict:
    """当日 (UTC) の確定 PnL を集計し、警告/半量/停止レベルを返す。

    Returns:
        {
            "pnl_jpy": float,
            "pct_of_principal": float,
            "level": "ok" / "warn" / "half" / "stop"
        }
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not db_path.exists():
        return {"pnl_jpy": 0.0, "pct_of_principal": 0.0, "level": "ok"}

    with v3_db.get_conn(db_path) as conn:
        cur = conn.execute(
            """
            SELECT SUM(pnl_jpy) AS s
            FROM trade_closures
            WHERE substr(exit_at_utc, 1, 10) = ?
            """,
            (today,),
        )
        row = cur.fetchone()

    pnl = float(row["s"] or 0.0)
    pct = abs(pnl) / principal_jpy if pnl < 0 else 0.0

    level = "ok"
    if pnl < 0:
        if pct >= DAILY_LOSS_STOP_PCT:
            level = "stop"
        elif pct >= DAILY_LOSS_HALF_PCT:
            level = "half"
        elif pct >= DAILY_LOSS_WARN_PCT:
            level = "warn"

    return {"pnl_jpy": pnl, "pct_of_principal": pct, "level": level}


def check_monthly_loss(
    db_path: Path,
    principal_jpy: float = DEFAULT_PRINCIPAL_JPY,
) -> dict:
    """当月 (UTC) の確定 PnL を集計"""
    ym = datetime.now(timezone.utc).strftime("%Y-%m")
    if not db_path.exists():
        return {"pnl_jpy": 0.0, "pct_of_principal": 0.0, "level": "ok"}

    with v3_db.get_conn(db_path) as conn:
        cur = conn.execute(
            """
            SELECT SUM(pnl_jpy) AS s
            FROM trade_closures
            WHERE substr(exit_at_utc, 1, 7) = ?
            """,
            (ym,),
        )
        row = cur.fetchone()

    pnl = float(row["s"] or 0.0)
    pct = abs(pnl) / principal_jpy if pnl < 0 else 0.0
    level = "stop" if pnl < 0 and pct >= MONTHLY_LOSS_STOP_PCT else "ok"
    return {"pnl_jpy": pnl, "pct_of_principal": pct, "level": level}


# ============================================================
# 撤退条件チェック (SPEC v3 § 4.5)
# ============================================================


@dataclass
class RetreatStatus:
    """撤退条件チェック結果"""
    pair: Optional[str]                   # None なら system-wide
    triggered: bool
    code: str                              # 'ok' or 'retreat_<n>_<detail>'
    message: str


def compute_lift_per_pair(
    db_path: Path,
    pair: str,
    months_back: int = RETREAT_LIFT_CONSECUTIVE_MONTHS,
    window_days: int = RETREAT_LIFT_WINDOW_DAYS,
) -> dict:
    """撤退条件 #0 用: 過去 N ヶ月分の lift (= pf_filter - pf_base) を計算。

    Ultra H-② 是正 (2026-05-28): SPEC v3 § 4.5 撤退条件 #0 「lift vs base
    < +0.30 が 3 ヶ月連続」を実装層に配線。

    計算式:
        lift_month_i = pf_filter_month_i - pf_base_month_i

    - pf_filter_month_i: 当該月 (ローリング 30 日) の確定 trades の PF
      (= LLM 採用後の実 PnL ベース PF)
    - pf_base_month_i: 当該月の signal_v2 単独運用想定の PF
      (= 抑制シグナル仮想 PnL + 採用シグナル実 PnL の合算)

    現状制約: 抑制シグナル仮想 PnL 計算 (SPEC §8.4) は未実装のため、
    pf_base が None となる月が大半。lift 撤退は Phase 2'B 評価 (60-90 日後)
    までに suppressed-PnL パイプラインが導入された後に有効化する設計。
    Phase 2'A 30 日では 3 ヶ月連続条件が物理的に成立しないため発火しない。

    Returns:
        {
            "pair": pair,
            "months": [
                {"month", "pf_filter", "pf_base", "lift", "n_filter",
                 "n_signal", "below_threshold": bool | None},
                ...
            ],
            "consecutive_below": int,        # 末尾から連続して未達月数
            "all_evaluable": bool,           # 全月で pf_base が計算可能だったか
        }
    """
    filter_months = v3_db.monthly_pf_window(
        db_path, pair, months_back=months_back, window_days=window_days,
    )
    base_months = v3_db.signal_base_pf_window(
        db_path, pair, months_back=months_back, window_days=window_days,
    )
    base_by_month = {m["month"]: m for m in base_months}

    months_out: list[dict] = []
    all_evaluable = True
    for fm in filter_months:
        bm = base_by_month.get(fm["month"], {})
        pf_filter = fm.get("pf")
        pf_base = bm.get("pf")
        if pf_filter is None or pf_base is None:
            lift: Optional[float] = None
            below: Optional[bool] = None
            all_evaluable = False
        else:
            lift = float(pf_filter) - float(pf_base)
            below = lift < RETREAT_LIFT_THRESHOLD
        months_out.append({
            "month": fm["month"],
            "pf_filter": pf_filter,
            "pf_base": pf_base,
            "lift": lift,
            "n_filter": fm.get("n", 0),
            "n_signal": bm.get("n", 0),
            "below_threshold": below,
        })

    # 直近 (= 最新月) から連続して below_threshold=True の月数を数える
    # below=None (未確定) は連続を切る
    consecutive = 0
    for m in months_out:
        if m["below_threshold"] is True:
            consecutive += 1
        else:
            break

    return {
        "pair": pair,
        "months": months_out,
        "consecutive_below": consecutive,
        "all_evaluable": all_evaluable,
    }


def check_retreat_per_pair(db_path: Path, pair: str) -> RetreatStatus:
    """ペア別撤退条件 0-3 をチェック。

    0. lift vs base < +0.30 が 3 ヶ月連続 → 撤退 (Ultra H-② 是正、2026-05-28)
    1. 90 日経過したのに trades < 5 → 撤退
    2. 直近 100 trades の PF < 1.0 (n>=5) → 撤退
    3. 累計 PnL < -3,000 JPY → 撤退
    """
    # 0. lift 撤退 (SPEC §4.5 #0)
    lift_info = compute_lift_per_pair(db_path, pair)
    if (lift_info["all_evaluable"]
            and lift_info["consecutive_below"] >= RETREAT_LIFT_CONSECUTIVE_MONTHS):
        last_lifts = ", ".join(
            f"{m['month']}={m['lift']:.2f}"
            for m in lift_info["months"]
            if m["lift"] is not None
        )
        return RetreatStatus(
            pair=pair, triggered=True,
            code="retreat_0_lift_below_threshold",
            message=(
                f"{pair} lift vs base < +{RETREAT_LIFT_THRESHOLD:.2f} が "
                f"{RETREAT_LIFT_CONSECUTIVE_MONTHS} ヶ月連続 ({last_lifts})"
            ),
        )

    # 1. シグナル少なすぎ
    days = v3_db.days_since_first_trade(db_path, pair)
    n_trades = v3_db.trade_count(db_path, pair)
    if days is not None and days >= RETREAT_DAYS_NO_TRADES and n_trades < RETREAT_MIN_TRADES_REQUIRED:
        return RetreatStatus(
            pair=pair, triggered=True,
            code="retreat_1_too_few_signals",
            message=f"{pair} は {days} 日経過したが trades={n_trades} < {RETREAT_MIN_TRADES_REQUIRED}",
        )

    # 2. PF 維持失敗 (最小サンプル RETREAT_PF_MIN_TRADES 未満では判定しない)
    pf = v3_db.recent_pf(
        db_path, pair, n_trades=RETREAT_PF_WINDOW,
        min_trades=RETREAT_PF_MIN_TRADES,
    )
    if pf is not None and pf < RETREAT_PF_FLOOR:
        return RetreatStatus(
            pair=pair, triggered=True,
            code="retreat_2_pf_below_floor",
            message=f"{pair} 直近 {RETREAT_PF_WINDOW} trades の PF={pf:.3f} < {RETREAT_PF_FLOOR}",
        )

    # 3. 累計損失
    pnl = v3_db.cumulative_pnl(db_path, pair=pair)
    if pnl["total_jpy"] <= RETREAT_CUMULATIVE_PNL_JPY:
        return RetreatStatus(
            pair=pair, triggered=True,
            code="retreat_3_cumulative_loss",
            message=f"{pair} 累計 PnL={pnl['total_jpy']:.0f} JPY ≤ {RETREAT_CUMULATIVE_PNL_JPY:.0f}",
        )

    return RetreatStatus(pair=pair, triggered=False, code="ok", message="ok")


def check_retreat_llm_cost(db_path: Path) -> RetreatStatus:
    """撤退条件 #4: LLM API 月コスト > 5,000円"""
    cost = v3_db.llm_cost_in_month(db_path)
    if cost["cost_usd"] >= RETREAT_LLM_COST_MONTHLY_USD:
        return RetreatStatus(
            pair=None, triggered=True,
            code="retreat_4_llm_cost",
            message=(
                f"LLM 月コスト ${cost['cost_usd']:.2f} >= ${RETREAT_LLM_COST_MONTHLY_USD:.2f} "
                f"(≒ ¥{cost['cost_usd'] * 150:.0f}) 撤退条件 #4 発動"
            ),
        )
    return RetreatStatus(pair=None, triggered=False, code="ok", message="ok")


def check_retreat_system_wide(
    db_path: Path,
    enabled_pairs: tuple[str, ...],
) -> RetreatStatus:
    """撤退条件 #5: 全ペアで 1-3 が成立した場合は SPEC v3 全体終了"""
    triggered_pairs = []
    for pair in enabled_pairs:
        st = check_retreat_per_pair(db_path, pair)
        if st.triggered:
            triggered_pairs.append((pair, st.code))
    if len(triggered_pairs) == len(enabled_pairs) and enabled_pairs:
        return RetreatStatus(
            pair=None, triggered=True,
            code="retreat_5_all_pairs",
            message=f"全ペアで撤退条件成立: {triggered_pairs}",
        )
    return RetreatStatus(pair=None, triggered=False, code="ok", message="ok")


# ============================================================
# 統括: ループから呼び出す簡易インターフェース
# ============================================================


def run_all_safety_checks(
    db_path: Path,
    enabled_pairs: tuple[str, ...],
    kill_switch: KillSwitchState,
    principal_jpy: float = DEFAULT_PRINCIPAL_JPY,
) -> dict:
    """各種安全チェックを一括実行し、結果を返す。

    Returns:
        {
            "daily": {...},
            "monthly": {...},
            "per_pair_retreat": {pair: RetreatStatus, ...},
            "llm_cost_retreat": RetreatStatus,
            "system_retreat": RetreatStatus,
            "action": "ok" / "warn" / "half_size" / "daily_stop" / "monthly_stop" / "retreat_*"
        }
    """
    daily = check_daily_loss(db_path, principal_jpy)
    monthly = check_monthly_loss(db_path, principal_jpy)
    per_pair = {p: check_retreat_per_pair(db_path, p) for p in enabled_pairs}
    llm_cost = check_retreat_llm_cost(db_path)
    system = check_retreat_system_wide(db_path, enabled_pairs)

    # 日次損失レベルでブロックを設定
    if daily["level"] == "stop":
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        kill_switch.daily_block_until = today
        action = "daily_stop"
    elif monthly["level"] == "stop":
        action = "monthly_stop"
    elif system.triggered:
        action = system.code
    elif llm_cost.triggered:
        action = llm_cost.code
    elif any(s.triggered for s in per_pair.values()):
        action = next(s.code for s in per_pair.values() if s.triggered)
    elif daily["level"] == "half":
        action = "half_size"
    elif daily["level"] == "warn":
        action = "warn"
    else:
        action = "ok"

    return {
        "daily": daily,
        "monthly": monthly,
        "per_pair_retreat": per_pair,
        "llm_cost_retreat": llm_cost,
        "system_retreat": system,
        "action": action,
    }
