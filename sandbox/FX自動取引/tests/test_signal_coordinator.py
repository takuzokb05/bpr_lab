"""SignalCoordinator のテスト（監査B7 回帰防止含む）"""
import time

from src.signal_coordinator import (
    DEFAULT_REGISTER_TIMEOUT_SEC,
    COORDINATION_WINDOW_SEC,
    SignalCoordinator,
    _CLAUDE_API_TIMEOUT,
)


def test_default_timeout_covers_window_and_llm_audit_b7():
    """監査B7: register_signal のデフォルト timeout は window + LLM API + バッファを満たす。

    旧実装は timeout=10s 固定で、window_sec(5) + Claude API timeout(10) = 15s に
    対し早すぎ → LLM結果を待たずフォールバック承認 → レース状態。
    """
    assert DEFAULT_REGISTER_TIMEOUT_SEC >= COORDINATION_WINDOW_SEC + _CLAUDE_API_TIMEOUT, (
        f"DEFAULT_REGISTER_TIMEOUT_SEC={DEFAULT_REGISTER_TIMEOUT_SEC}s は"
        f"window({COORDINATION_WINDOW_SEC}s) + LLM({_CLAUDE_API_TIMEOUT}s) を満たさない"
    )


def test_register_signal_returns_true_when_llm_disabled():
    """LLM無効時は常に承認"""
    sc = SignalCoordinator(llm_enabled=False)
    assert sc.register_signal("USD_JPY", "BUY", adx=25.0) is True


def test_register_signal_single_signal_approved_in_window():
    """単一シグナルは window_sec 経過後に承認される"""
    sc = SignalCoordinator(window_sec=0.5, llm_enabled=False)
    start = time.time()
    result = sc.register_signal("USD_JPY", "BUY", adx=25.0)
    elapsed = time.time() - start
    # llm_enabled=False なので即時 True が返り、_evaluator_loop は走らない
    assert result is True
    assert elapsed < 1.0, f"想定外に長い待機: {elapsed:.2f}s"
