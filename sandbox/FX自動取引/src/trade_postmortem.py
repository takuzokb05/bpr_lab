"""
FX自動取引システム — トレード事後分析モジュール

決済されたトレードに対してLLMで勝因/敗因分析を行い、
パラメータ改善の示唆を提供する。
fire-and-forget型のデーモンスレッドで非同期実行し、
メインのトレーディングループをブロックしない。
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from src.config import (
    ANTHROPIC_API_KEY,
    POSTMORTEM_ENABLED,
    POSTMORTEM_MODEL_ID,
)

logger = logging.getLogger(__name__)

# Claude API
_CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
_CLAUDE_API_TIMEOUT = 60

# 事後分析プロンプト
_SYSTEM_PROMPT = """\
あなたは10年以上の経験を持つFXトレードアナリストです。
決済済みトレードの事後分析を行い、勝因・敗因を特定します。

重要な制約:
- 事実に基づいた分析のみ。後知恵バイアスを明示する
- パラメータ改善は具体的な数値で提案（「ADX閾値を15→18に」等）
- 提案は1つに絞る（複数の変更は因果関係を不明にする）
- 確信度の低い提案はしない

出力は必ず以下のJSON形式のみ:
{
  "outcome": "win" | "loss",
  "primary_cause": "<勝因または敗因を1文で>",
  "entry_analysis": "<エントリー時の状況分析を2文で>",
  "exit_analysis": "<決済時の状況分析を2文で>",
  "parameter_suggestion": {
    "parameter": "<パラメータ名 or null>",
    "current_value": "<現在値 or null>",
    "suggested_value": "<提案値 or null>",
    "reasoning": "<提案理由を1文で>"
  },
  "hindsight_warning": "<後知恵バイアスの注意点を1文で>"
}"""

_USER_PROMPT_TEMPLATE = """\
以下のトレード結果を分析してください。

## トレード情報
- 通貨ペア: {instrument}
- 方向: {direction}
- 数量: {units}
- エントリー価格: {open_price}
- 決済価格: {close_price}
- 損益: {pl}
- 保有期間: {duration}

## エントリー時の指標
{entry_indicators}

## 決済時の指標
{exit_indicators}

上記を分析し、勝因/敗因を特定してください。
改善提案がある場合は、具体的なパラメータ変更を1つだけ提案してください。"""


class TradePostMortem:
    """
    トレード事後分析を管理するクラス。

    エントリー時の指標スナップショットをDBに保存し、
    決済時にLLMで分析を実行する。
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path
        if db_path is not None:
            self._init_db()

    def _init_db(self) -> None:
        """事後分析用テーブルを作成する。"""
        if self._db_path is None:
            return
        with sqlite3.connect(str(self._db_path)) as conn:
            # エントリー時指標スナップショット
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT NOT NULL UNIQUE,
                    indicators_json TEXT NOT NULL,
                    captured_at TEXT NOT NULL
                )
                """
            )
            # 事後分析結果
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_postmortems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT NOT NULL UNIQUE,
                    analysis_json TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    # ------------------------------------------------------------------
    # エントリー時スナップショット保存
    # ------------------------------------------------------------------

    def save_entry_snapshot(
        self, trade_id: str, indicators: dict
    ) -> None:
        """
        エントリー時の指標スナップショットをDBに保存する。

        Args:
            trade_id: トレードID
            indicators: compute_indicators()の返却値から抽出したスカラー値dict
        """
        if self._db_path is None:
            return

        # Seriesは保存できないのでスカラー値のみ抽出
        snapshot = _extract_scalars(indicators)

        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO trade_snapshots
                       (trade_id, indicators_json, captured_at)
                       VALUES (?, ?, ?)""",
                    (
                        trade_id,
                        json.dumps(snapshot, ensure_ascii=False),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
        except sqlite3.Error as e:
            logger.warning("エントリースナップショット保存失敗: %s", e)

    # ------------------------------------------------------------------
    # 事後分析トリガー（fire-and-forget）
    # ------------------------------------------------------------------

    def trigger_analysis(
        self,
        trade_id: str,
        instrument: str,
        units: int,
        open_price: float,
        close_price: float,
        pl: float,
        opened_at: datetime,
        closed_at: datetime,
        exit_indicators: Optional[dict] = None,
    ) -> None:
        """
        事後分析をバックグラウンドで実行する。

        デーモンスレッドで非同期実行し、メインループをブロックしない。
        """
        if not POSTMORTEM_ENABLED:
            return
        if not ANTHROPIC_API_KEY:
            logger.debug("ANTHROPIC_API_KEY未設定のため事後分析スキップ")
            return

        t = threading.Thread(
            target=self._run_analysis,
            args=(
                trade_id, instrument, units, open_price, close_price,
                pl, opened_at, closed_at, exit_indicators,
            ),
            daemon=True,
            name=f"postmortem-{trade_id}",
        )
        t.start()

    def _run_analysis(
        self,
        trade_id: str,
        instrument: str,
        units: int,
        open_price: float,
        close_price: float,
        pl: float,
        opened_at: datetime,
        closed_at: datetime,
        exit_indicators: Optional[dict],
    ) -> None:
        """事後分析の実行本体（バックグラウンドスレッド内）。"""
        try:
            # エントリー時スナップショットをDBから取得
            entry_snapshot = self._load_entry_snapshot(trade_id)

            # 決済時指標のスカラー抽出
            exit_snapshot = _extract_scalars(exit_indicators) if exit_indicators else {}

            # 保有期間算出
            duration = closed_at - opened_at
            duration_str = f"{duration.total_seconds() / 3600:.1f}時間"

            # 方向判定
            direction = "BUY" if units > 0 else "SELL"

            # エントリー/決済指標のフォーマット
            entry_text = _format_indicators(entry_snapshot) if entry_snapshot else "（スナップショットなし）"
            exit_text = _format_indicators(exit_snapshot) if exit_snapshot else "（指標なし）"

            # Claude API呼び出し
            user_prompt = _USER_PROMPT_TEMPLATE.format(
                instrument=instrument,
                direction=direction,
                units=abs(units),
                open_price=f"{open_price:.5f}",
                close_price=f"{close_price:.5f}",
                pl=f"{pl:+.2f}",
                duration=duration_str,
                entry_indicators=entry_text,
                exit_indicators=exit_text,
            )

            analysis = self._call_claude(user_prompt)
            if analysis is None:
                return

            # DB保存
            self._save_analysis(trade_id, analysis)

            logger.info(
                "[PostMortem] %s %s: %s → %s | 原因: %s",
                instrument,
                direction,
                "勝ち" if pl > 0 else "負け",
                f"{pl:+.2f}",
                analysis.get("primary_cause", "不明"),
            )

        except Exception as e:
            logger.warning("事後分析エラー (trade_id=%s): %s", trade_id, e)

    # ------------------------------------------------------------------
    # Claude API
    # ------------------------------------------------------------------

    # 事後分析プロンプトは日本語の長文 JSON（5フィールド + 4ネスト）を要求する。
    # 旧 max_tokens=512 では UTF-8 日本語で確実に切れる（実測: 5/4 09:13 に
    # 「Unterminated string starting at: line 12 column 24 (char 664)」発生）。
    # 1024 で多くは収まるが、安全マージンを取って初回 1536、truncated 検出時に
    # _MAX_TOKENS_RETRY (3072) で 1 度だけリトライする。
    _MAX_TOKENS_INITIAL = 1536
    _MAX_TOKENS_RETRY = 3072

    def _call_claude(self, user_prompt: str) -> Optional[dict]:
        """Claude APIで事後分析を実行する。

        truncation (stop_reason=max_tokens) を検出したら 1 度だけ大きい
        max_tokens でリトライする。それでも parse 不可なら None を返す。
        """
        for attempt, max_tokens in enumerate(
            (self._MAX_TOKENS_INITIAL, self._MAX_TOKENS_RETRY), start=1,
        ):
            result = self._call_claude_once(user_prompt, max_tokens)
            if result is None:
                return None  # API エラーや timeout — リトライしない
            parsed, was_truncated = result
            if parsed is not None:
                return parsed
            if not was_truncated or attempt == 2:
                # truncation 以外の parse 失敗 or 既にリトライ済み → 諦める
                return None
            logger.info(
                "事後分析: max_tokens=%d で truncated。max_tokens=%d でリトライ",
                max_tokens, self._MAX_TOKENS_RETRY,
            )
        return None

    def _call_claude_once(
        self, user_prompt: str, max_tokens: int,
    ) -> Optional[tuple[Optional[dict], bool]]:
        """1 回 Claude API を呼ぶ。

        Returns:
            None: API エラー（接続失敗/timeout/HTTP 5xx 等、リトライ不可）
            (parsed_dict, False): parse 成功
            (None, True): truncation で parse 失敗（リトライ候補）
            (None, False): truncation 以外の parse 失敗（リトライ不可）
        """
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": POSTMORTEM_MODEL_ID,
            "max_tokens": max_tokens,
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
            body = resp.json()
        except requests.exceptions.Timeout:
            logger.warning("事後分析API タイムアウト")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning("事後分析APIエラー: %s", e)
            return None

        stop_reason = body.get("stop_reason")
        content = body.get("content", [{}])[0].get("text", "")
        json_str = content.strip()
        # ```json ... ``` フェンスを剥がす
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            )

        try:
            return (json.loads(json_str), False)
        except json.JSONDecodeError as e:
            was_truncated = stop_reason == "max_tokens"
            # 診断用: 失敗位置周辺を抜粋（256 文字以内、機密ではない）
            excerpt = json_str[:512] + (" ...[truncated]" if len(json_str) > 512 else "")
            logger.warning(
                "事後分析JSON parse 失敗 (stop_reason=%s, max_tokens=%d): %s | excerpt=%r",
                stop_reason, max_tokens, e, excerpt,
            )
            return (None, was_truncated)

    # ------------------------------------------------------------------
    # DB操作
    # ------------------------------------------------------------------

    def _load_entry_snapshot(self, trade_id: str) -> Optional[dict]:
        """エントリー時スナップショットをDBから取得する。"""
        if self._db_path is None:
            return None
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                row = conn.execute(
                    "SELECT indicators_json FROM trade_snapshots WHERE trade_id = ?",
                    (trade_id,),
                ).fetchone()
            if row:
                return json.loads(row[0])
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.warning("エントリースナップショット読込失敗: %s", e)
        return None

    def _save_analysis(self, trade_id: str, analysis: dict) -> None:
        """事後分析結果をDBに保存する。"""
        if self._db_path is None:
            return
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO trade_postmortems
                       (trade_id, analysis_json, model, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (
                        trade_id,
                        json.dumps(analysis, ensure_ascii=False),
                        POSTMORTEM_MODEL_ID,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
        except sqlite3.Error as e:
            logger.warning("事後分析結果の保存失敗: %s", e)


# ============================================================
# ヘルパー関数
# ============================================================


def _extract_scalars(indicators: Optional[dict]) -> dict:
    """指標キャッシュからシリアライズ可能なスカラー値のみ抽出する。"""
    if indicators is None:
        return {}
    scalar_keys = [
        "current_rsi", "current_adx", "current_atr", "current_mfi",
        "ma_short_current", "ma_long_current",
        "ma_short_prev", "ma_long_prev",
        "atr_ratio", "bbw_ratio",
    ]
    result = {}
    for key in scalar_keys:
        val = indicators.get(key)
        if val is not None:
            result[key] = round(float(val), 5)
    return result


def _format_indicators(snapshot: dict) -> str:
    """指標スナップショットを人間が読める文字列に変換する。"""
    if not snapshot:
        return "（データなし）"
    lines = []
    label_map = {
        "current_rsi": "RSI(14)",
        "current_adx": "ADX(14)",
        "current_atr": "ATR(14)",
        "current_mfi": "MFI(14)",
        "ma_short_current": "MA(20)",
        "ma_long_current": "MA(50)",
        "atr_ratio": "ATR比率",
        "bbw_ratio": "BBW比率",
    }
    for key, label in label_map.items():
        val = snapshot.get(key)
        if val is not None:
            lines.append(f"- {label}: {val}")
    return "\n".join(lines) if lines else "（データなし）"
