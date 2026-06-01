"""LLM クライアント（単一プロバイダー＝Anthropic をデフォルト）。

v2 の不安定さの主因だった「3社マルチ API 吸収」をやめ、IF を1つに統一する。
差し替え可能な抽象を残すので、特定ペルソナだけ別モデル/別プロバイダーにする拡張は
将来も可能（multiprovider は collapse 対策の任意機能として後付けできる）。

テストは MockLLMClient だけで完結する（anthropic パッケージ不要）。
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Callable, Iterator

# エンジン既定モデル。ペルソナ側で model を指定すればそちらが優先される。
# 意思決定の討論は低頻度・高単価でも質を優先するため既定を Opus にする。
# コスト優先なら .env の AI_TEAMS_MODEL=claude-sonnet-4-6 等で上書きできる。
DEFAULT_MODEL = os.environ.get("AI_TEAMS_MODEL", "claude-opus-4-8")

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

    def generate_stream(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """1発言をテキスト差分（delta）の列として yield する。

        既定実装は `generate()` の結果を1チャンクとして返すフォールバック。
        ストリーミング対応のクライアントはこれをオーバーライドする。
        delta を連結すると `generate()` と同じ全文になることを契約とする。
        """
        text = self.generate(
            system=system, messages=messages, model=model, temperature=temperature
        )
        if text:
            yield text


# temperature を受け付けないモデル（API が 400 "temperature is deprecated" を返す）。
# Opus 4.8 以降が該当。該当モデルには temperature を送らない。
_TEMP_UNSUPPORTED_MARKERS = ("opus-4-8",)


def _supports_temperature(model: str) -> bool:
    return not any(m in model for m in _TEMP_UNSUPPORTED_MARKERS)


class AnthropicClient(LLMClient):
    """本番用。anthropic SDK を遅延 import する。"""

    def __init__(self, api_key: str | None = None, max_tokens: int | None = None) -> None:
        import anthropic  # 遅延 import

        self._client = (
            anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        )
        # 1024 では Opus 4.8 の豊かな発言が文中で切れる。既定 2048・AI_TEAMS_MAX_TOKENS で可変。
        # max_tokens は上限であり、モデルは必要分で停止するので過大でも常時その量を消費はしない。
        self._max_tokens = max_tokens or int(os.environ.get("AI_TEAMS_MAX_TOKENS", "2048"))

    def _params(self, *, system: str, messages: list[Message], model: str, temperature: float) -> dict:
        """API 呼び出しパラメータ。temperature 非対応モデルには temperature を含めない。"""
        params: dict = {
            "model": model,
            "system": system,
            "messages": messages,
            "max_tokens": self._max_tokens,
        }
        if _supports_temperature(model):
            params["temperature"] = temperature
        return params

    def generate(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
    ) -> str:
        resp = self._client.messages.create(
            **self._params(system=system, messages=messages, model=model, temperature=temperature)
        )
        return "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        ).strip()

    def generate_stream(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        # Anthropic SDK の messages.stream() からテキスト差分を逐次 yield する。
        with self._client.messages.stream(
            **self._params(system=system, messages=messages, model=model, temperature=temperature)
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield text


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

    def generate_stream(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        # generate() と同じ呼び出し記録・同じ全文を保ったまま、決定的に数チャンクへ割る。
        # delta を連結すると generate() と一致する（テストの契約）。
        text = self.generate(
            system=system, messages=messages, model=model, temperature=temperature
        )
        if not text:
            return
        # 環境変数 AI_TEAMS_MOCK_DELAY（秒）でチャンク毎に待つ。実LLMを使わずに
        # ストリーミングの“ライブ感”を再現・検証するための affordance（既定0＝従来動作）。
        import os
        import time

        delay = float(os.environ.get("AI_TEAMS_MOCK_DELAY", "0") or "0")
        chunks = 3
        size = max(1, (len(text) + chunks - 1) // chunks)
        for i in range(0, len(text), size):
            if delay > 0:
                time.sleep(delay)
            yield text[i : i + size]
