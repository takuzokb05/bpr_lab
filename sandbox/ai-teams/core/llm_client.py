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
        max_tokens: int | None = None,
    ) -> str:
        """system プロンプトと会話履歴から、1人格の1発言を返す。

        max_tokens を渡すとこの呼び出しの出力上限を上書きする（None なら構築時の既定）。
        議事録（synthesis）は討論全体を1枚に圧縮し単一発言より長くなるため、大きめを渡す。
        """
        raise NotImplementedError

    def generate_stream(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """1発言をテキスト差分（delta）の列として yield する。

        既定実装は `generate()` の結果を1チャンクとして返すフォールバック。
        ストリーミング対応のクライアントはこれをオーバーライドする。
        delta を連結すると `generate()` と同じ全文になることを契約とする。
        max_tokens はこの呼び出しの出力上限の上書き（None なら構築時の既定）。
        """
        text = self.generate(
            system=system,
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if text:
            yield text

    def web_research(self, query: str) -> str:
        """query を web 検索し、出典付きの簡潔なブリーフ（1文字列）を返す。

        基底実装は LLM/検索を一切呼ばず、決定的な canned 文字列を返す（無料・テスト可）。
        実検索する AnthropicClient だけがこれをオーバーライドする。検索するのは討論の
        「調査役」だけで、各ペルソナは検索しない＝重複ゼロ・課金は調査ターンに限定。
        """
        return f"（モック調査結果: {query} ／出典なし・検証用）"


# temperature を受け付けないモデル（API が 400 "temperature is deprecated" を返す）。
# Opus 4.8 以降が該当。該当モデルには temperature を送らない。
_TEMP_UNSUPPORTED_MARKERS = ("opus-4-8",)


def _supports_temperature(model: str) -> bool:
    return not any(m in model for m in _TEMP_UNSUPPORTED_MARKERS)


# 調査役（web_research）の研究プロンプト雛形。憶測を禁じ、調べて分かった事実だけを
# 各項目に出典 URL を付けて箇条書き化させる。{query} に調べたい問いを差し込む。
_RESEARCH_PROMPT_TEMPLATE = (
    "次について web 検索し、意思決定に必要な事実・統計・先行事例を、各項目に出典URLを"
    "付けて簡潔にブリーフ化せよ。憶測や一般論は書かず、調べて分かったことだけを箇条書きで。"
    ": {query}"
)


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

    def _params(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
    ) -> dict:
        """API 呼び出しパラメータ。temperature 非対応モデルには temperature を含めない。"""
        params: dict = {
            "model": model,
            "system": system,
            "messages": messages,
            "max_tokens": self._max_tokens if max_tokens is None else max_tokens,
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
        max_tokens: int | None = None,
    ) -> str:
        resp = self._client.messages.create(
            **self._params(
                system=system, messages=messages, model=model,
                temperature=temperature, max_tokens=max_tokens,
            )
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
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        # Anthropic SDK の messages.stream() からテキスト差分を逐次 yield する。
        with self._client.messages.stream(
            **self._params(
                system=system, messages=messages, model=model,
                temperature=temperature, max_tokens=max_tokens,
            )
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield text

    def web_research(self, query: str) -> str:
        """Anthropic web_search ツールで query を調べ、出典付きブリーフを1文字列で返す。

        messages.create(..., tools=[{type:"web_search_20250305", name:"web_search", ...}]) を
        呼ぶ。応答 content は server_tool_use → web_search_tool_result → text(複数, 各 text
        block の .citations[].url に出典) の並びになる。text block を連結し、各 citation の
        URL を集めて末尾に「出典:\n- url...」として付す。temperature は tools 経路でも
        opus-4-8 には送らない（_supports_temperature と同じ判定）。

        例外時は「（調査に失敗: 理由）」を返し、討論は止めない（呼び出し側が継続できる）。
        """
        prompt = _RESEARCH_PROMPT_TEMPLATE.format(query=query)
        params: dict = {
            "model": DEFAULT_MODEL,
            "max_tokens": self._max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 4,
                }
            ],
        }
        # tools 経路でも temperature 非対応モデル（opus-4-8）には temperature を送らない。
        if _supports_temperature(DEFAULT_MODEL):
            params["temperature"] = 0.3
        try:
            resp = self._client.messages.create(**params)
        except Exception as exc:  # noqa: BLE001 — 失敗しても討論を止めず、その旨を返す
            return f"（調査に失敗: {exc}）"

        texts: list[str] = []
        urls: list[str] = []
        seen_urls: set[str] = set()
        for block in resp.content:
            if getattr(block, "type", None) != "text":
                continue
            text = getattr(block, "text", "") or ""
            if text:
                texts.append(text)
            # 各 text block の citations から出典 URL を集める（重複は除く・順序維持）。
            for citation in getattr(block, "citations", None) or []:
                url = getattr(citation, "url", None) or (
                    citation.get("url") if isinstance(citation, dict) else None
                )
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    urls.append(url)

        brief = "\n".join(texts).strip()
        if urls:
            brief += "\n\n出典:\n" + "\n".join(f"- {u}" for u in urls)
        if not brief:
            return f"（調査結果が空でした: {query}）"
        return brief


# 各 provider の既定モデル（env で上書き可）。BYOK では各自が1社のキーだけ入れる想定で、
# その provider の既定モデルを全ペルソナに使う（ペルソナの model 上書きは Anthropic 用 ID なので
# 非 Anthropic では無視＝混線防止。発言の多様性は system プロンプトで担保する）。
#
# モデル名は更新が速い。ここは **2026-06 時点の現行フラッグシップ（GA）** を置き、新型が出たら
# env（AI_TEAMS_OPENAI_MODEL / AI_TEAMS_GEMINI_MODEL）で差し替える運用にする。
#   OpenAI: gpt-5.5（推奨フラッグシップ）。安価重視なら gpt-5.4 / gpt-5.4-mini、
#           最新 Instant 追従なら chat-latest エイリアス。
#   Gemini: gemini-3.5-flash（GA・現行の高性能）。上位は gemini-2.5-pro 系、
#           自動追従は gemini-flash-latest エイリアス（preview に振れる点に注意）。
_OPENAI_DEFAULT_MODEL = os.environ.get("AI_TEAMS_OPENAI_MODEL", "gpt-5.5")
_GEMINI_DEFAULT_MODEL = os.environ.get("AI_TEAMS_GEMINI_MODEL", "gemini-3.5-flash")

# 非 Anthropic provider では Web 検索（調査役）は未対応。その旨を正直に返す（討論は止めない）。
_RESEARCH_UNSUPPORTED = "（Web 検索は現在 Anthropic 選択時のみ対応です。検索なしで進めます。）"

# OpenAI の GPT-5 / o 系（推論モデル）は temperature を既定(1)以外受け付けない（400）。
# これらのモデル名にマッチしたら temperature を送らない（gpt-4o 等の従来モデルには送る）。
_OPENAI_NO_TEMP_MARKERS = ("gpt-5", "o1", "o3", "o4")


class OpenAIClient(LLMClient):
    """OpenAI Chat Completions を Anthropic と同じ IF に正規化する（BYOK・各自キー）。

    v2 を不安定化させた「1プロセスで複数 provider を同時に吸収」はしない。1セッション=1 provider=
    このクライアント1個に限定する。ペルソナの model 上書き（Anthropic 用 ID）は無視し、この
    provider の既定モデルを使う。Web 検索は未対応（honest に伝える）。
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        base_url: str | None = None,
        search_mode: str = "",
    ) -> None:
        from openai import OpenAI  # 遅延 import（未インストールでも他 provider は動く）

        # base_url を渡すと OpenAI 互換の自前推論サーバ（Ollama/vLLM）や開源フロンティアAPI
        # （DeepSeek/GLM/Qwen, OpenRouter）に向く＝内製（自前ホスト/開源）LLM。
        # この local 経路では max_completion_tokens/reasoning_effort 非対応のことが多いので、_params で
        # 古典的な max_tokens + temperature に切り替える（per-persona temperature がそのまま効く）。
        self._local = bool(base_url)
        # web_research を直 HTTP で叩くため base_url / api_key を保持する（OpenRouter は SDK 標準の
        # tools 経路と互換でないため）。search_mode="openrouter" のとき web_search サーバツールを使う。
        self._search_mode = (search_mode or "").strip().lower()
        self._base_url = (base_url or "").rstrip("/")
        key = (api_key or os.environ.get("AI_TEAMS_LOCAL_API_KEY") or "local") if base_url else api_key
        self._api_key_value = key
        kwargs: dict = {}
        if base_url:
            kwargs["base_url"] = base_url
            # ローカル(Ollama 等)は鍵不要だが OpenAI SDK が api_key を要求するためダミーを入れる。
            kwargs["api_key"] = key
        elif api_key:
            kwargs["api_key"] = api_key
        self._client = OpenAI(**kwargs) if kwargs else OpenAI()
        self._model = model or _OPENAI_DEFAULT_MODEL
        self._max_tokens = max_tokens or int(os.environ.get("AI_TEAMS_MAX_TOKENS", "2048"))

    def _messages(self, system: str, messages: list[Message]) -> list[Message]:
        # OpenAI は system を messages 先頭ロールで渡す。
        return [{"role": "system", "content": system}, *messages]

    def _openrouter_provider(self) -> dict | None:
        """OpenRouter の provider ルーティング設定。

        OpenRouter は1モデルを複数の下流プロバイダに分散ルーティングする。一部（Venice 等）は
        コンテンツフィルタが強く、討論の正当な批判を "inappropriate content" で弾いて発言が
        空/エラーになる。env AI_TEAMS_OPENROUTER_IGNORE（カンマ区切り・既定 "Venice"）で除外する。
        OpenRouter 以外の base_url（Ollama/vLLM 等）では None（provider 概念が無い）。
        """
        if "openrouter" not in self._base_url:
            return None
        ignore = [
            s.strip()
            for s in os.environ.get("AI_TEAMS_OPENROUTER_IGNORE", "Venice").split(",")
            if s.strip()
        ]
        return {"ignore": ignore, "allow_fallbacks": True} if ignore else None

    def _params(
        self,
        system: str,
        messages: list[Message],
        temperature: float,
        max_tokens: int | None = None,
    ) -> dict:
        """chat.completions のパラメータ。新旧モデル差を吸収する。

        - 出力上限は **max_completion_tokens**（max_tokens は非推奨で GPT-5/o 系は拒否）。
          max_tokens 引数で呼び出し毎に上書きできる（議事録など長い出力用。None なら構築時既定）。
        - GPT-5 / o 系（推論モデル）は temperature 既定(1)以外を拒否するので送らない。代わりに
          reasoning_effort を低め（既定 low）にする。理由: max_completion_tokens に内部推論が
          食い込むので、推論を抑えて可視発言にトークンを回す＋討論用途では速度/コストを優先。
        - gpt-4o 等の従来モデルには temperature を渡す（_OPENAI_NO_TEMP_MARKERS で判定）。
        """
        mt = self._max_tokens if max_tokens is None else max_tokens
        params: dict = {
            "model": self._model,  # 渡された model（Claude ID の可能性）は使わない
            "messages": self._messages(system, messages),
        }
        if self._local:
            # 内製（OpenAI 互換の自前サーバ・Ollama/vLLM・OpenRouter）。max_completion_tokens/
            # reasoning_effort は非対応のことが多いので、古典的な max_tokens + temperature を使う。
            params["max_tokens"] = mt
            params["temperature"] = temperature
            extra: dict = {}
            # 思考モデル（Kimi K2.6 / DeepSeek V4 Pro 等）は reasoning が max_tokens を食い、可視発言が
            # 枯れて空ターン化する。OpenRouter の reasoning 制御で抑え、応答の長さ(verbosity)が可視
            # 出力に効くようにする。既定 low。AI_TEAMS_LOCAL_REASONING="" で無効（生挙動）。
            effort = os.environ.get("AI_TEAMS_LOCAL_REASONING", "low").strip()
            if effort:
                extra["reasoning"] = {"effort": effort}
            # 検閲の強い下流プロバイダ（Venice 等）を避ける（正当な批判の弾かれを防ぐ）。
            prov = self._openrouter_provider()
            if prov:
                extra["provider"] = prov
            if extra:
                params["extra_body"] = extra
            return params
        # クラウド OpenAI（GPT-5/o 系は max_completion_tokens・temperature 非対応で reasoning_effort）。
        params["max_completion_tokens"] = mt
        if any(m in self._model for m in _OPENAI_NO_TEMP_MARKERS):
            effort = os.environ.get("AI_TEAMS_OPENAI_REASONING", "low").strip()
            if effort:
                params["reasoning_effort"] = effort
        else:
            params["temperature"] = temperature
        return params

    def _retry_no_reasoning(
        self, system: str, messages: list[Message], temperature: float, max_tokens: int | None = None
    ) -> str:
        """空ターン救済: reasoning を切り max_tokens を増やして1回だけ非ストリームで取り直す。

        思考モデル（Kimi/DeepSeek Pro 等）が reasoning に出力枠を食われ、可視発言が空になった場合の
        フォールバック。reasoning を無効化すれば予算が全部可視出力に回るので、ほぼ必ず本文が返る。
        max_tokens は呼び出し側の上限（議事録は大きい）に揃える。失敗しても空文字を返す（討論は止めない）。
        """
        try:
            extra: dict = {"reasoning": {"enabled": False}}
            prov = self._openrouter_provider()
            if prov:
                extra["provider"] = prov
            params: dict = {
                "model": self._model,
                "messages": self._messages(system, messages),
                "max_tokens": max(self._max_tokens if max_tokens is None else max_tokens, 4096),
                "temperature": temperature,
                "extra_body": extra,
            }
            resp = self._client.chat.completions.create(**params)
            return (resp.choices[0].message.content or "").strip()
        except Exception:  # noqa: BLE001 — 救済の失敗で討論を止めない
            return ""

    def generate(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        resp = self._client.chat.completions.create(
            **self._params(system, messages, temperature, max_tokens)
        )
        content = (resp.choices[0].message.content or "").strip()
        # local（思考モデル）が空を返したら reasoning を切って取り直す（空ターン防止）。
        if self._local and not content:
            content = self._retry_no_reasoning(system, messages, temperature, max_tokens)
        return content

    def generate_stream(
        self,
        *,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        stream = self._client.chat.completions.create(
            **self._params(system, messages, temperature, max_tokens), stream=True
        )
        got: list[str] = []
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                got.append(delta)
                yield delta
        # local（思考モデル）が何も発しなかったら reasoning を切って取り直し、その全文を流す
        # （「発言者が無言で次へ流れる」空ターンの根治）。
        if self._local and not "".join(got).strip():
            retry = self._retry_no_reasoning(system, messages, temperature, max_tokens)
            if retry:
                yield retry

    def web_research(self, query: str) -> str:
        """内製（local）経路の Web 検索。

        search_mode="openrouter" のとき、OpenRouter の web_search **サーバツール**を有効にした
        chat.completions を1回呼び、本文＋出典(url_citation)を返す（どのモデルでも検索可）。
        OpenRouter は SDK 標準の tools 経路と互換でないため直 HTTP で叩く。
        検索バックエンド未設定（""）のときは honest に「未対応」を返す（討論は止めない）。
        """
        if self._search_mode == "openrouter":
            return self._openrouter_web_research(query)
        return _RESEARCH_UNSUPPORTED

    def _openrouter_web_research(self, query: str) -> str:
        import json
        import urllib.request

        prompt = _RESEARCH_PROMPT_TEMPLATE.format(query=query)
        body: dict = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [{"type": "openrouter:web_search"}],
            "max_tokens": self._max_tokens,
        }
        # 検閲の強い下流プロバイダ（Venice 等）を避ける（検索結果が弾かれないように）。
        prov = self._openrouter_provider()
        if prov:
            body["provider"] = prov
        url = f"{self._base_url}/chat/completions"
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key_value}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 — 失敗しても討論を止めず、その旨を返す
            return f"（調査に失敗: {exc}）"

        choices = data.get("choices") or [{}]
        msg = choices[0].get("message", {}) if choices else {}
        text = (msg.get("content") or "").strip()
        # url_citation annotations から出典 URL を集める（重複排除・順序維持）。
        urls: list[str] = []
        seen: set[str] = set()
        for ann in msg.get("annotations") or []:
            uc = ann.get("url_citation") or {}
            u = uc.get("url")
            if u and u not in seen:
                seen.add(u)
                urls.append(u)
        if urls:
            text += "\n\n出典:\n" + "\n".join(f"- {u}" for u in urls)
        if not text:
            return f"（調査結果が空でした: {query}）"
        return text


class GeminiClient(LLMClient):
    """Google Gemini（google-genai SDK）を Anthropic と同じ IF に正規化する（BYOK・各自キー）。

    OpenAIClient と同じ方針（1セッション1 provider・model 上書き無視・検索未対応）。
    Gemini はロールが user/model なので assistant→model に変換し、system は config の
    system_instruction で渡す。
    """

    def __init__(self, api_key: str | None = None, model: str | None = None, max_tokens: int | None = None) -> None:
        from google import genai  # 遅延 import

        self._client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self._model = model or _GEMINI_DEFAULT_MODEL
        self._max_tokens = max_tokens or int(os.environ.get("AI_TEAMS_MAX_TOKENS", "2048"))

    def _contents(self, messages: list[Message]) -> list[dict]:
        # Gemini: role は "user" | "model"。Anthropic の assistant を model に読み替える。
        out: list[dict] = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            out.append({"role": role, "parts": [{"text": m["content"]}]})
        return out

    def _config(self, system: str, temperature: float, max_tokens: int | None = None):
        from google.genai import types

        # temperature は Gemini 3 では非推奨（送らず既定に従う）。max_tokens で呼び出し毎に上書き可。
        kwargs: dict = {
            "system_instruction": system,
            "max_output_tokens": self._max_tokens if max_tokens is None else max_tokens,
        }
        # 思考(thinking)は既定 ON で max_output_tokens を食い、可視出力が枯れる（ほぼ空応答に
        # なりうる）。討論用途では低めに固定して発言にトークンを回す（env AI_TEAMS_GEMINI_THINKING で可変）。
        level = os.environ.get("AI_TEAMS_GEMINI_THINKING", "low").strip()
        if level:
            try:
                kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=level)
            except Exception:
                pass  # SDK が thinking_level 非対応なら無理に付けない（古い SDK 等）
        return types.GenerateContentConfig(**kwargs)

    def generate(
        self, *, system: str, messages: list[Message], model: str,
        temperature: float = 0.7, max_tokens: int | None = None,
    ) -> str:
        resp = self._client.models.generate_content(
            model=self._model,
            contents=self._contents(messages),
            config=self._config(system, temperature, max_tokens),
        )
        return (getattr(resp, "text", "") or "").strip()

    def generate_stream(
        self, *, system: str, messages: list[Message], model: str,
        temperature: float = 0.7, max_tokens: int | None = None,
    ) -> Iterator[str]:
        stream = self._client.models.generate_content_stream(
            model=self._model,
            contents=self._contents(messages),
            config=self._config(system, temperature, max_tokens),
        )
        for chunk in stream:
            text = getattr(chunk, "text", None)
            if text:
                yield text

    def web_research(self, query: str) -> str:
        return _RESEARCH_UNSUPPORTED


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
        max_tokens: int | None = None,
    ) -> str:
        self.calls.append(
            {
                "system": system,
                "messages": messages,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
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
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        # generate() と同じ呼び出し記録・同じ全文を保ったまま、決定的に数チャンクへ割る。
        # delta を連結すると generate() と一致する（テストの契約）。
        text = self.generate(
            system=system, messages=messages, model=model,
            temperature=temperature, max_tokens=max_tokens,
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
