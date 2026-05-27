"""SPEC v3 — LLM Direct Filter (Claude Sonnet 4.6)

`scripts/_cycle2_llm_filter.py` の検証実装をベースに、本番運用向けに整理。

## 役割
1. signal_v2 が出したシグナル + 市況コンテキストを LLM に渡す
2. CONFIRM / NEUTRAL / CONTRADICT / REJECT + confidence + reasoning を取得
3. 失敗時 (タイムアウト / 5xx / JSON parse 失敗 / 不正ラベル) は **API_ERROR** を返し、
   呼び出し側でフェイルセーフ (= 取らない) する

## リーク防止
- 過去ニュース要約は使わない (CYCLE2_PLAN.md L147-148, SPEC_V3.md § 3.3)
- 未来情報 (24h 後の高安値など) はそもそも build_context で渡さない

## モデル
- claude-sonnet-4-6 (SPEC_V3.md § 3.1)
- temperature=0.0, max_tokens=200, タイムアウト 30 秒
- リトライ最大 3 回 (指数バックオフ)
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================
# 定数 (SPEC_V3.md § 3.1 準拠)
# ============================================================

MODEL_ID = "claude-sonnet-4-6"
TEMPERATURE = 0.0
MAX_TOKENS = 200
API_TIMEOUT_SEC = 30.0
MAX_RETRIES = 3

# Claude Sonnet 4 系の概算単価 (USD/M tokens)
USD_PER_M_INPUT = 3.0
USD_PER_M_OUTPUT = 15.0

VALID_LABELS = {"CONFIRM", "NEUTRAL", "CONTRADICT", "REJECT"}

# ATR 計算定数 (signal_v2 と同じロジックを別複製、signal_v2 改変禁止のため、
# Ultra/Karen バグ⑥ 是正、2026-05-27)
ATR_PERIOD_DEFAULT = 14


def calc_atr(m15_df: pd.DataFrame, period: int = ATR_PERIOD_DEFAULT) -> Optional[float]:
    """ATR (Average True Range) を計算して最新値を返す。

    signal_v2.signal_v2.calc_atr と同じロジックを別途複製 (signal_v2 は改変禁止)。
    Phase 0' BT (`_cycle2_extract_signals.py`) で LLM プロンプトに渡していた
    ATR 値を Phase 2'A でも同等に渡すために使用。

    Args:
        m15_df: M15 OHLCV DataFrame (最低 period+1 本)
        period: ATR 期間 (デフォルト 14)

    Returns:
        最新の ATR 値 (float)、データ不足/NaN なら None
    """
    if m15_df is None or len(m15_df) < period + 1:
        return None
    h, l, c = m15_df["high"], m15_df["low"], m15_df["close"]
    prev_c = c.shift(1)
    tr = pd.concat([
        h - l,
        (h - prev_c).abs(),
        (l - prev_c).abs(),
    ], axis=1).max(axis=1)
    atr_series = tr.rolling(period).mean()
    val = atr_series.iloc[-1]
    if pd.isna(val):
        return None
    return float(val)


# ============================================================
# 結果型
# ============================================================


@dataclass
class LLMDecision:
    """LLM 判定結果。API_ERROR の場合は label='API_ERROR'。"""
    label: str                            # CONFIRM / NEUTRAL / CONTRADICT / REJECT / API_ERROR
    confidence: float                     # 0.0-1.0
    reasoning: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    error: Optional[str] = None           # API_ERROR の詳細

    @property
    def is_error(self) -> bool:
        return self.label == "API_ERROR"


# ============================================================
# プロンプト生成
# ============================================================

SYSTEM_PROMPT = (
    "あなたは FX 自動取引のリスク判定エージェントです。"
    "与えられたシグナル時点のコンテキストに基づき、取引を取るべきか判定します。"
    "回答は必ず JSON 形式 (コードブロック不要、平文 JSON のみ) で返してください。"
)


def build_context(
    pair: str,
    signal: dict,
    m15_df: pd.DataFrame,
    related_24h_changes: Optional[dict] = None,
    timestamp_utc: Optional[str] = None,
) -> dict:
    """LLM プロンプトに渡すコンテキスト dict を構築する (リーク列を含まない)。

    Args:
        pair: 通貨ペア (例: "USD_JPY")
        signal: signal_v2.TradeSignal を dict 化したもの
        m15_df: M15 OHLCV DataFrame (最低 100 本程度)
        related_24h_changes: {"USD_JPY": 0.45, "EUR_USD": -0.12, "GBP_USD": 0.08}
        timestamp_utc: シグナル時刻 (ISO8601、未指定なら m15_df の最終時刻 or "now")

    Returns:
        プロンプトテンプレートにそのまま渡せる dict
    """
    # M15 終値: 24h前/12h前/1h前 (M15 → 1 本 15 分)
    close_24h = float(m15_df["close"].iloc[-97]) if len(m15_df) >= 97 else None
    close_12h = float(m15_df["close"].iloc[-49]) if len(m15_df) >= 49 else None
    close_1h = float(m15_df["close"].iloc[-5]) if len(m15_df) >= 5 else None

    rel = related_24h_changes or {}
    return {
        "pair": pair,
        "timestamp_utc": timestamp_utc or "",
        "direction": signal.get("direction"),
        "entry_price": signal.get("entry_price"),
        "sl_price": signal.get("sl_price"),
        "tp_price": signal.get("tp_price"),
        "sl_pips": signal.get("sl_pips"),
        "tp_pips": signal.get("tp_pips"),
        "atr": signal.get("atr"),
        "m15_close_24h_ago": close_24h,
        "m15_close_12h_ago": close_12h,
        "m15_close_1h_ago": close_1h,
        "rel_usd_jpy_24h_pct": rel.get("USD_JPY"),
        "rel_eur_usd_24h_pct": rel.get("EUR_USD"),
        "rel_gbp_usd_24h_pct": rel.get("GBP_USD"),
    }


def build_user_prompt(context: dict) -> str:
    """SPEC_V3.md § 3.2 のプロンプトテンプレート (cycle2 LLM filter と同形式)"""

    def _fmt(v, suffix: str = "") -> str:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "N/A"
        return f"{v}{suffix}"

    return f"""[シグナル情報]
- ペア: {context['pair']}
- 時刻 (UTC): {context.get('timestamp_utc', 'N/A')}
- 方向: {context['direction']}
- エントリー: {_fmt(context['entry_price'])}
- SL: {_fmt(context['sl_price'])} ({_fmt(context['sl_pips'])} pips)
- TP: {_fmt(context['tp_price'])} ({_fmt(context['tp_pips'])} pips)
- ATR: {_fmt(context.get('atr'))}

[市況コンテキスト]
- M15 終値 24h前: {_fmt(context['m15_close_24h_ago'])}
- M15 終値 12h前: {_fmt(context['m15_close_12h_ago'])}
- M15 終値 1h前: {_fmt(context['m15_close_1h_ago'])}
- USD/JPY 24h 変化: {_fmt(context['rel_usd_jpy_24h_pct'], '%')}
- EUR/USD 24h 変化: {_fmt(context['rel_eur_usd_24h_pct'], '%')}
- GBP/USD 24h 変化: {_fmt(context['rel_gbp_usd_24h_pct'], '%')}

[判定]
以下の JSON だけを返してください (前後の説明文や ``` は付けない):
{{
  "decision": "CONFIRM" | "NEUTRAL" | "CONTRADICT" | "REJECT",
  "confidence": 0.0-1.0 の小数,
  "reasoning": "1-2文の判定理由 (日本語)"
}}

判定基準:
- CONFIRM: シグナル方向を取るべき (強い同意)
- NEUTRAL: 取ってよい (積極推奨ではない)
- CONTRADICT: 反対方向を取るべき
- REJECT: 取らない (危険な状況、流動性低下、レンジで逆張り、等)
"""


# ============================================================
# JSON パース (`_cycle2_llm_filter.py` と同等のロバスト実装)
# ============================================================


def _parse_llm_json(text: str) -> dict:
    s = text.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        s = "\n".join(lines).strip()
    if not s.startswith("{"):
        first = s.find("{")
        last = s.rfind("}")
        if first >= 0 and last > first:
            s = s[first : last + 1]
    return json.loads(s)


# ============================================================
# LLM Filter 本体
# ============================================================


class LLMFilter:
    """Claude Sonnet 4.6 を呼び出して判定を行うフィルタ。

    インスタンス化に成功した時点で API キーは有効。
    判定失敗時は LLMDecision(label='API_ERROR') を返し、例外は投げない。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = MODEL_ID,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_TOKENS,
        max_retries: int = MAX_RETRIES,
        timeout: float = API_TIMEOUT_SEC,
    ) -> None:
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY が見つかりません。"
                ".env または環境変数で設定してください。"
            )

        # 遅延 import (テスト時に anthropic 未インストールでも判定型を import 可能にする)
        from anthropic import Anthropic
        self._client = Anthropic(api_key=api_key, timeout=timeout)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._max_retries = max_retries

    def judge(self, context: dict) -> LLMDecision:
        """1 シグナル分の判定。失敗時は LLMDecision(label='API_ERROR')。"""
        # 遅延 import (Mock テストで anthropic を import せずに済むように)
        try:
            from anthropic import APIError, APIStatusError, RateLimitError
        except ImportError:  # pragma: no cover
            APIError = APIStatusError = RateLimitError = Exception  # type: ignore

        prompt = build_user_prompt(context)
        last_error: Optional[str] = None
        backoff = 2.0

        for attempt in range(1, self._max_retries + 1):
            try:
                resp = self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw_text = "".join(
                    block.text for block in resp.content
                    if getattr(block, "type", None) == "text"
                )
                usage_in = resp.usage.input_tokens
                usage_out = resp.usage.output_tokens
                cost = (
                    usage_in / 1_000_000 * USD_PER_M_INPUT
                    + usage_out / 1_000_000 * USD_PER_M_OUTPUT
                )

                try:
                    parsed = _parse_llm_json(raw_text)
                except json.JSONDecodeError as e:
                    last_error = f"JSON parse: {e} raw={raw_text[:200]!r}"
                    logger.warning("LLM JSON parse 失敗 (attempt %d): %s",
                                   attempt, last_error)
                    if attempt < self._max_retries:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    return LLMDecision(
                        label="API_ERROR", confidence=0.0,
                        reasoning=f"[parse_error] {last_error[:120]}",
                        input_tokens=usage_in, output_tokens=usage_out,
                        cost_usd=cost, error=last_error,
                    )

                label = str(parsed.get("decision", "")).upper().strip()
                if label not in VALID_LABELS:
                    last_error = f"invalid label: {label!r}"
                    logger.warning("LLM 判定不正 (attempt %d): %s",
                                   attempt, last_error)
                    if attempt < self._max_retries:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    return LLMDecision(
                        label="API_ERROR", confidence=0.0,
                        reasoning=f"[invalid_label] {label}",
                        input_tokens=usage_in, output_tokens=usage_out,
                        cost_usd=cost, error=last_error,
                    )

                confidence = float(parsed.get("confidence", 0.0) or 0.0)
                # 範囲外の confidence は clip
                confidence = max(0.0, min(1.0, confidence))
                reasoning = str(parsed.get("reasoning", ""))[:500]

                return LLMDecision(
                    label=label,
                    confidence=confidence,
                    reasoning=reasoning,
                    input_tokens=usage_in,
                    output_tokens=usage_out,
                    cost_usd=cost,
                )

            except RateLimitError as e:
                last_error = f"RateLimit: {e}"
                logger.warning("LLM RateLimit (attempt %d): %s",
                               attempt, last_error)
                time.sleep(backoff)
                backoff *= 2
            except APIStatusError as e:  # type: ignore[misc]
                status = getattr(e, "status_code", 0) or 0
                last_error = f"APIStatus {status}: {e}"
                logger.warning("LLM APIStatus (attempt %d): %s",
                               attempt, last_error)
                if attempt < self._max_retries and 500 <= status < 600:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    break
            except APIError as e:  # type: ignore[misc]
                last_error = f"APIError: {e}"
                logger.warning("LLM APIError (attempt %d): %s",
                               attempt, last_error)
                time.sleep(backoff)
                backoff *= 2
            except Exception as e:  # noqa: BLE001
                last_error = f"{type(e).__name__}: {e}"
                logger.exception("LLM 予期せぬエラー (attempt %d)", attempt)
                time.sleep(backoff)
                backoff *= 2

        return LLMDecision(
            label="API_ERROR", confidence=0.0,
            reasoning=f"[api_error] {last_error}",
            input_tokens=0, output_tokens=0, cost_usd=0.0,
            error=last_error,
        )


def should_take_trade(
    pair: str,
    decision: LLMDecision,
    confidence_thresholds: dict[str, float],
    accept_labels: tuple[str, ...] = ("CONFIRM",),
) -> tuple[bool, str]:
    """採用判定: (採用するか, 理由) を返す。

    Proposal 3 ルール:
    - label が CONFIRM のみ採用 (NEUTRAL/CONTRADICT/REJECT は除外)
    - confidence >= ペア別閾値 (USD_JPY 0.65 / GBP_JPY 0.60)
    - API_ERROR はフェイルセーフで採用しない
    """
    if decision.is_error:
        return False, "api_error_failsafe"
    if decision.label not in accept_labels:
        return False, f"label_{decision.label.lower()}"
    threshold = confidence_thresholds.get(pair)
    if threshold is None:
        return False, "pair_not_enabled"
    if decision.confidence < threshold:
        return False, f"below_confidence_threshold({decision.confidence:.2f}<{threshold:.2f})"
    return True, "accepted"
