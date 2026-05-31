"""API のドメインロジック（FastAPI 非依存・テスト可能）。

ここには Web フレームワークを import しない。SSE の文字列生成・Council の組み立て・
ペルソナの公開用シリアライズだけを置き、main.py（FastAPI）から薄く呼ぶ。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

from core import AnthropicClient, Council, LLMClient, MockLLMClient, Persona, load_personas

PERSONAS_DIR = Path(__file__).resolve().parent.parent / "personas"


# -- ペルソナ ---------------------------------------------------------------
def load_registry() -> list[Persona]:
    """personas/ 配下を読み込む。"""
    return load_personas(PERSONAS_DIR)


def persona_public(p: Persona) -> dict:
    """フロント公開用の安全なペルソナ表現（system_prompt は出さない）。"""
    return {
        "id": p.id,
        "display_name": p.display_name,
        "category": p.category,
        "accent": p.accent_color,
        "monogram": p.monogram,
        "tags": list(p.tags),
        "speaks": p.speaks,
        "model": p.model,
    }


# -- LLM クライアント -------------------------------------------------------
def make_client(mock: bool = False) -> LLMClient:
    """mock 指定、または API キー未設定なら MockLLMClient にフォールバック。"""
    if mock or not os.environ.get("ANTHROPIC_API_KEY"):
        return MockLLMClient()
    return AnthropicClient()


# -- Council 組み立て -------------------------------------------------------
def build_council(
    persona_ids: list[str],
    *,
    rounds_per_phase: int = 1,
    mock: bool = False,
) -> Council:
    """指定 id のペルソナで Council を作る。未知 id は KeyError。"""
    registry = {p.id: p for p in load_registry()}
    missing = [pid for pid in persona_ids if pid not in registry]
    if missing:
        raise KeyError(missing)
    personas = [registry[pid] for pid in persona_ids]
    return Council(personas, make_client(mock), rounds_per_phase=rounds_per_phase)


# -- SSE --------------------------------------------------------------------
def sse(event: str, data: dict) -> str:
    """1件の Server-Sent Event を SSE ワイヤ形式の文字列にする。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_council(council: Council, topic: str) -> Iterator[str]:
    """討論を進めつつ、start → turn* → done を SSE 文字列で逐次 yield する。"""
    yield sse("start", {"topic": topic})
    try:
        for turn in council.run(topic):
            yield sse(
                "turn",
                {
                    "speaker_id": turn.speaker_id,
                    "speaker_name": turn.speaker_name,
                    "content": turn.content,
                    "phase": turn.phase,
                    "round": turn.round,
                },
            )
    except Exception as exc:  # noqa: BLE001 — クライアントにエラーを通知して締める
        yield sse("error", {"message": str(exc)})
        return
    yield sse("done", {})
