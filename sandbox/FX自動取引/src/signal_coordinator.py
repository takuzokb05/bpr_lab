"""
FX自動取引システム — シグナル協調モジュール

複数通貨ペアのシグナルを時間ウィンドウ内で集約し、
相関リスクをLLMで評価する。
ルールベースの相関チェック（R5: PositionManager._check_correlation_exposure）
を補完する動的判断レイヤー。
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import requests

from src.config import ANTHROPIC_API_KEY, COORDINATOR_MODEL_ID

logger = logging.getLogger(__name__)

# Claude API
_CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
_CLAUDE_API_TIMEOUT = 10

# デフォルト設定
COORDINATION_WINDOW_SEC: float = 5.0  # シグナル集約ウィンドウ（秒）
CORRELATION_LLM_ENABLED: bool = True  # LLM相関判断の有効/無効

# 監査B7: register_signal のデフォルト待機時間は window_sec + LLM timeout + バッファ。
# 旧実装は 10s 固定で、ウィンドウ5s + Claude API 10s = 15s に対して timeout が早く切れ、
# LLM評価結果を待たずに「フォールバック承認」して発注 → 数秒後に拒否判定が出ても遅い、
# というレース状態が発生していた。
_REGISTER_SIGNAL_TIMEOUT_BUFFER_SEC: float = 2.0
DEFAULT_REGISTER_TIMEOUT_SEC: float = (
    COORDINATION_WINDOW_SEC + _CLAUDE_API_TIMEOUT + _REGISTER_SIGNAL_TIMEOUT_BUFFER_SEC
)

_SYSTEM_PROMPT = """\
あなたはFXポートフォリオマネージャーです。
複数通貨ペアの同時シグナルを評価し、相関リスクを判断します。

重要な制約:
- 同一通貨を含むペアの同方向シグナルは相関リスクが高い
  （例: USD_JPY BUY + EUR_USD SELL = 共にUSD買い）
- 独立した機会は並行保有を推奨
- 相関が高い場合は最もADXが高いペアを優先

出力は必ず以下のJSON形式のみ:
{
  "correlated": true | false,
  "correlation_type": "<通貨相関の種類を1文で>",
  "recommended_pairs": ["<優先すべきペアリスト>"],
  "reasoning": "<判断理由を2文で>"
}"""


@dataclass
class PendingSignal:
    """集約待ちのシグナル"""
    instrument: str
    signal: str          # "BUY" or "SELL"
    adx: float
    timestamp: float     # time.time()
    event: threading.Event = field(default_factory=threading.Event)
    approved: bool = True


class SignalCoordinator:
    """
    複数スレッドからのシグナルを時間ウィンドウ内で集約し、
    相関リスクをLLMで評価する協調器。

    使い方:
    1. TradingLoopがシグナル検出時に register_signal() を呼ぶ
    2. ウィンドウ内に他のシグナルが来たらLLMで相関評価
    3. register_signal() はブロッキングで結果（承認/拒否）を返す
    """

    def __init__(
        self,
        window_sec: float = COORDINATION_WINDOW_SEC,
        llm_enabled: bool = CORRELATION_LLM_ENABLED,
    ) -> None:
        self._window_sec = window_sec
        self._llm_enabled = llm_enabled
        self._lock = threading.Lock()
        self._pending: list[PendingSignal] = []
        self._evaluator_running = False

    def register_signal(
        self,
        instrument: str,
        signal: str,
        adx: float = 0.0,
        timeout: Optional[float] = None,
    ) -> bool:
        """
        シグナルを登録し、相関評価結果を待つ。

        Args:
            instrument: 通貨ペア
            signal: "BUY" or "SELL"
            adx: 現在のADX値（優先度判断用）
            timeout: 最大待機時間（秒）

        Returns:
            True: 取引承認、False: 相関リスクにより拒否
        """
        if not self._llm_enabled or not ANTHROPIC_API_KEY:
            return True  # LLM無効時は常に承認

        # 監査B7: timeout 未指定なら window_sec + LLM API timeout + バッファ から自動算出
        if timeout is None:
            timeout = (
                self._window_sec + _CLAUDE_API_TIMEOUT
                + _REGISTER_SIGNAL_TIMEOUT_BUFFER_SEC
            )

        pending = PendingSignal(
            instrument=instrument,
            signal=signal,
            adx=adx,
            timestamp=time.time(),
        )

        with self._lock:
            self._pending.append(pending)
            # 評価スレッドが未起動なら起動
            if not self._evaluator_running:
                self._evaluator_running = True
                t = threading.Thread(
                    target=self._evaluator_loop,
                    daemon=True,
                    name="signal-coordinator",
                )
                t.start()

        # 結果を待つ（タイムアウト付き）
        if pending.event.wait(timeout=timeout):
            return pending.approved
        else:
            # タイムアウト → 安全側で承認（ルールベース相関チェックが別途ある）
            logger.warning(
                "[SignalCoordinator] タイムアウト: %s %s（承認にフォールバック）",
                instrument, signal,
            )
            return True

    def _evaluator_loop(self) -> None:
        """ウィンドウ時間待ってから集約評価を実行する。"""
        time.sleep(self._window_sec)

        with self._lock:
            # ウィンドウ内のシグナルを取り出し
            now = time.time()
            window_signals = [
                p for p in self._pending
                if now - p.timestamp <= self._window_sec * 2
            ]
            self._pending = []
            self._evaluator_running = False

        if len(window_signals) <= 1:
            # 単一シグナル → 無条件承認
            for sig in window_signals:
                sig.approved = True
                sig.event.set()
            return

        # 2件以上 → LLM評価
        logger.info(
            "[SignalCoordinator] %d件の同時シグナルを評価中...",
            len(window_signals),
        )

        recommended = self._evaluate_correlation(window_signals)

        for sig in window_signals:
            if recommended is None:
                # LLM失敗 → 全承認（フォールバック）
                sig.approved = True
            else:
                sig.approved = sig.instrument in recommended
                if not sig.approved:
                    logger.info(
                        "[SignalCoordinator] 相関リスクにより拒否: %s %s",
                        sig.instrument, sig.signal,
                    )
            sig.event.set()

    def _evaluate_correlation(
        self, signals: list[PendingSignal]
    ) -> Optional[list[str]]:
        """LLMで相関評価し、推奨ペアリストを返す。失敗時はNone。"""
        signal_desc = "\n".join(
            f"- {s.instrument} {s.signal} (ADX={s.adx:.1f})"
            for s in signals
        )
        user_prompt = (
            f"以下の{len(signals)}件のシグナルが同時に発生しました:\n"
            f"{signal_desc}\n\n"
            f"これらは独立した取引機会ですか？"
            f"相関リスクがある場合、どのペアを優先すべきですか？"
        )

        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": COORDINATOR_MODEL_ID,
            "max_tokens": 256,
            "system": _SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        try:
            resp = requests.post(
                _CLAUDE_API_URL,
                headers=headers,
                json=payload,
                timeout=_CLAUDE_API_TIMEOUT,
            )
            resp.raise_for_status()

            content = resp.json().get("content", [{}])[0].get("text", "")
            json_str = content.strip()
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(
                    line for line in lines if not line.strip().startswith("```")
                )

            result = json.loads(json_str)
            recommended = result.get("recommended_pairs", [])

            logger.info(
                "[SignalCoordinator] LLM評価: correlated=%s, recommended=%s, reason=%s",
                result.get("correlated"),
                recommended,
                result.get("reasoning", ""),
            )

            return recommended if recommended else [s.instrument for s in signals]

        except Exception as e:
            logger.warning("[SignalCoordinator] LLM評価失敗（全承認にフォールバック）: %s", e)
            return None
