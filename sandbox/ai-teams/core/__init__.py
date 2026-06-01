"""AI Teams v3 — core パッケージ。

UI 非依存の討論オーケストレーション・エンジン。
詳細な設計判断は ../REBUILD_PLAN.md と ../RESEARCH_2026-05_orchestration.md を参照。
"""

from .personas import (
    Persona,
    persona_from_dict,
    load_personas,
    load_personas_with_paths,
)
from .llm_client import LLMClient, AnthropicClient, MockLLMClient, DEFAULT_MODEL
from .context import build_context
from .orchestrator import Council, Turn, RoundRobinScheduler

__all__ = [
    "Persona",
    "persona_from_dict",
    "load_personas",
    "load_personas_with_paths",
    "LLMClient",
    "AnthropicClient",
    "MockLLMClient",
    "DEFAULT_MODEL",
    "build_context",
    "Council",
    "Turn",
    "RoundRobinScheduler",
]
