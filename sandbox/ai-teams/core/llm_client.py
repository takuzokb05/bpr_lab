"""LLM クライアント（単一プロバイダー＝Anthropic をデフォルト）。

v2 の不安定さの主因だった「3社マルチ API 吸収」をやめ、IF を1つに統一する。
差し替え可能な抽象を残すので、特定ペルソナだけ別モデル/別プロバイダーにする拡張は
将来も可能（multiprovider は collapse 対策の任意機能として後付けできる）。

テストは MockLLMClient だけで完結する（anthropic パッケージ不要）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

# エンジン既定モデル。ペルソナ側で model を指定すればそちらが優先される。
DEFAULT_MODEL = "claude-sonnet-4-6"

# Anthropic Messages API が期待する message の形:
#   {"role": "user" | "assistant", "content": "..."}
Message = dict[str, str]


class LLMClient(ABC):
    """1発言を生成する統一インターフェース。"""

    @abstractmethod
    def generate(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
    ) -> str:
        """system プロンプトと会話履歴から、1人格の1発言を返す。"""
        raise NotImplementedError


class AnthropicClient(LLMClient):
    """本番用。anthropic SDK を遅延 import する。"""

    def __init__(self, api_key: str | None = None, max_tokens: int = 1024) -> None:
        import anthropic  # 遅延 import

        self._client = (
            anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        )
        self._max_tokens = max_tokens

    def generate(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
    ) -> str:
        resp = self._client.messages.create(
            model=model,
            system=system,
            messages=messages,
            max_tokens=self._max_tokens,
            temperature=temperature,
        )
        return "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        ).strip()


class MockLLMClient(LLMClient):
    """テスト/デモ用。API キー不要で決定的に動く。

    各呼び出しの (system, messages, model, temperature) を self.calls に記録するので、
    コンテキスト分離（自分=assistant / 他者=user）やモデル上書きを検証できる。
    responder を渡せば返答内容を差し替えられる。
    """

    def __init__(self, responder: Callable[[str, list[Message], str], str] | None = None) -> None:
        self.calls: list[dict] = []
        self._responder = responder

    def generate(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
    ) -> str:
        self.calls.append(
            {
                "system": system,
                "messages": messages,
                "model": model,
                "temperature": temperature,
            }
        )
        if self._responder is not None:
            return self._responder(system, messages, model)
        return f"(mock応答#{len(self.calls)})"
