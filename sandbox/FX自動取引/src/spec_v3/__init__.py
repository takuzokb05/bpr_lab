"""SPEC v3 — signal_v2 + LLM Direct Filter (Proposal 3)

CYCLE2_PLAN.md ゲート PASS を受けたデモ運用層。
- ベース戦略: src/spec_v2/signal_v2.py (改変禁止)
- LLM 補完層: Claude Sonnet 4.6 で CONFIRM/NEUTRAL/CONTRADICT/REJECT 判定
- ペア別 confidence 閾値で取捨選択:
    USD_JPY: CONFIRM × confidence ≥ 0.65 (PF 1.565)
    GBP_JPY: CONFIRM × confidence ≥ 0.60 (PF 1.294)

詳細仕様は docs/SPEC_V3.md と
docs/proposals/cycle2/IMPROVEMENT_META_ANALYSIS.md を参照。
"""
from __future__ import annotations

# ペア別 confidence 閾値 (Proposal 3 確定値)
CONFIDENCE_THRESHOLDS: dict[str, float] = {
    "USD_JPY": 0.65,
    "GBP_JPY": 0.60,
}

# 取引対象ペア (確定)
ENABLED_PAIRS: tuple[str, ...] = ("USD_JPY", "GBP_JPY")

# 取引採用ラベル (Proposal 3 では CONFIRM のみ、NEUTRAL/CONTRADICT/REJECT は除外)
ACCEPT_DECISIONS: tuple[str, ...] = ("CONFIRM",)

# (旧 SPREAD_WARN_THRESHOLD_PIPS は M1 で EMA baseline 方式の
# KillSwitchState.check_spread_anomaly() に置換済、karen D-2 で削除推奨)

__all__ = [
    "CONFIDENCE_THRESHOLDS",
    "ENABLED_PAIRS",
    "ACCEPT_DECISIONS",
]
