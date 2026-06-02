"""API のドメインロジック（FastAPI 非依存・テスト可能）。

ここには Web フレームワークを import しない。SSE の文字列生成・Council の組み立て・
ペルソナの公開用シリアライズだけを置き、main.py（FastAPI）から薄く呼ぶ。
"""

from __future__ import annotations

import json
import os
import queue
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from itertools import count
from typing import Iterator

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# .env を読み込んでおく（ANTHROPIC_API_KEY / AI_TEAMS_MODEL 等）。**core を import する前に**
# 読むことで、DEFAULT_MODEL のように import 時点で確定する値も .env を反映できる。
# python-dotenv が無い環境でも動くよう import を握り潰す。override=False で既存の環境変数
# （明示 export）を尊重する（VPS/CI を壊さない）。
try:
    from dotenv import load_dotenv

    load_dotenv(_PROJECT_ROOT / ".env", override=False)
except ImportError:
    # python-dotenv 未インストールでも API 自体は動く（キー未設定なら Mock にフォールバック）。
    pass

from core import (  # noqa: E402 — .env を先に読むため core import はここ
    AnthropicClient,
    Council,
    DEFAULT_MODEL,
    GeminiClient,
    LLMClient,
    MockLLMClient,
    OpenAIClient,
    Persona,
    load_personas,
    load_personas_with_paths,
    persona_from_dict,
)

PERSONAS_DIR = _PROJECT_ROOT / "personas"
PRESETS_DIR = _PROJECT_ROOT / "presets"
PRESETS_BUILTIN_DIR = PRESETS_DIR / "builtin"


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


# -- 動作モード（env-gated） ------------------------------------------------
def byok_mode() -> bool:
    """BYOK（各自が自分の API キーを持参）モードか。

    共有/公開インスタンスでは AI_TEAMS_BYOK=1 を設定する。すると make_client は
    **サーバの ANTHROPIC_API_KEY を来訪者リクエストに一切使わず**、リクエスト毎に
    渡された api_key だけで実 LLM を呼ぶ（来訪者は自分のキーで課金）。未設定（個人/テスト）
    なら従来どおりサーバ env キーへフォールバックできる（後方互換）。
    """
    return os.environ.get("AI_TEAMS_BYOK", "").strip().lower() in ("1", "true", "yes")


def readonly_mode() -> bool:
    """編成 CRUD（ペルソナ/プリセットの作成・更新・削除）を禁止するか。

    共有インスタンスでは AI_TEAMS_READONLY=1 を設定し、来訪者がサーバ上のファイルを
    書き換え/量産/削除できないようにする（main.py 側で 403 にマップ）。
    """
    return os.environ.get("AI_TEAMS_READONLY", "").strip().lower() in ("1", "true", "yes")


# 対応プロバイダ。anthropic/openai/google は BYOK（各自が1社のキー）。local は内製（自前ホスト）LLM＝
# OpenAI 互換の自前推論サーバ（Ollama/vLLM）に base_url で繋ぐ。鍵不要・従量ゼロ。研究=Web 検索は
# Anthropic のみ対応（local も非対応で honest に劣化）。
PROVIDERS = ("anthropic", "openai", "google", "local")
_DEFAULT_PROVIDER = "anthropic"


def local_base_url() -> str:
    """内製（自前ホスト）LLM の OpenAI 互換エンドポイント。

    env AI_TEAMS_LOCAL_BASE_URL（例: http://127.0.0.1:11434/v1 ＝ Ollama、http://host:8000/v1 ＝ vLLM）。
    未設定なら空（＝内製は無効）。推論サーバは uvicorn と別ホストでよい（base_url で繋ぐだけ）。
    """
    return os.environ.get("AI_TEAMS_LOCAL_BASE_URL", "").strip()


def local_model() -> str:
    """内製 LLM のモデル名（env AI_TEAMS_LOCAL_MODEL、例: qwen3:14b）。未設定なら汎用 'qwen3'。"""
    return os.environ.get("AI_TEAMS_LOCAL_MODEL", "").strip() or "qwen3"


def local_enabled() -> bool:
    """内製 LLM が使えるよう設定されているか（base_url が設定済みか）。UI の出し分けに使う。"""
    return bool(local_base_url())


def local_search_mode() -> str:
    """内製（local）経路の Web 検索バックエンド。

    env AI_TEAMS_LOCAL_SEARCH:
      - "openrouter": base_url が OpenRouter のとき、web_search サーバツールで検索する
        （どのモデルでも検索可・$0.005/検索程度）。
      - ""（既定）: 検索なし（非 Anthropic と同じく honest に劣化）。
    将来 "searxng" 等を足せる拡張点。
    """
    return os.environ.get("AI_TEAMS_LOCAL_SEARCH", "").strip().lower()


def local_search_enabled() -> bool:
    """内製（local）経路で Web 検索が使える設定か（base_url 済み＋検索バックエンド指定済み）。"""
    return local_enabled() and local_search_mode() in ("openrouter",)


def research_providers() -> list[str]:
    """Web 検索（調査役）が使える provider 一覧。anthropic は常時、local は検索設定済みのとき。"""
    out = ["anthropic"]
    if local_search_enabled():
        out.append("local")
    return out


def force_local() -> bool:
    """サーバを丸ごと内製（local）に固定するか（env AI_TEAMS_FORCE_LOCAL）。

    True かつ local 設定済みなら、来訪者の provider 指定に関わらず**全実 LLM を内製に回す**
    （個人運用で「開源フロンティアAPIで全部動かす」最短スイッチ）。フロントの provider 選択 UI を
    増やさずに切り替えられる。local 未設定なら False（誤設定で落とさない）。
    """
    flag = os.environ.get("AI_TEAMS_FORCE_LOCAL", "").strip().lower() in ("1", "true", "yes")
    return flag and local_enabled()

# 応答の長さプリセット（ユーザーはトークン数を意識しない。質感だけ選ぶ）。
#   max_tokens: 1発言の出力上限。**上限**でありモデルは必要分で止まるので、上げても常時その量を
#     消費はしない（主に途中切れ＝truncation 防止）。
#   hint: build_context 末尾ナッジに差し込む長さの語句（""＝従来の「簡潔に」で後方互換）。
#     簡潔は graceful に短く、じっくりは「簡潔に」を外して深掘りを許可する。
VERBOSITY = {
    "brief": {
        # 2048: 推論モデル（gpt-5/gemini thinking）は出力予算に内部推論が食い込むため、また
        # 日本語は英語よりトークンを食うため、1024 では 3〜5 文でも途中切れし得る。上限は
        # ceiling でありスタイル指示(hint)で実際の長さは短く保たれる。
        "max_tokens": 2048,
        "hint": "結論と主な理由を3〜5文で簡潔に",
    },
    "standard": {
        "max_tokens": 4096,  # 旧既定 2048 では最上位モデルの厚い発言が途中で切れていた
        "hint": "",  # ""→「簡潔に」（従来挙動）。上限だけ引き上げて切れを防ぐ
    },
    "deep": {
        "max_tokens": 8192,
        "hint": "要点は押さえつつ、重要な論点は具体例・根拠・想定反論まで踏み込んで丁寧に",
    },
}
_DEFAULT_VERBOSITY = "standard"


def normalize_verbosity(v: str | None) -> str:
    """応答の長さプリセット名を正規化（未知/空は既定 standard）。"""
    v = (v or "").strip().lower()
    return v if v in VERBOSITY else _DEFAULT_VERBOSITY


def normalize_provider(provider: str | None) -> str:
    """provider 文字列を正規化（未知/空は既定 anthropic）。"gemini" は google、"ollama" 等は local に寄せる。"""
    p = (provider or "").strip().lower()
    if p in ("gemini", "google-gemini"):
        return "google"
    if p in ("local", "ollama", "vllm", "self-hosted", "selfhosted"):
        return "local"
    return p if p in PROVIDERS else _DEFAULT_PROVIDER


# -- LLM クライアント -------------------------------------------------------
def make_client(
    mock: bool = False,
    api_key: str | None = None,
    provider: str | None = None,
    max_tokens: int | None = None,
) -> LLMClient:
    """LLM クライアントを作る。優先順位は mock > 明示 api_key > サーバ env キー。

    provider で実体（Anthropic/OpenAI/Gemini）を選ぶ（1セッション=1 provider）。
    max_tokens は1発言の出力上限（None なら各クライアントの env 既定）。応答の長さプリセットから渡す。
    - mock=True: provider/キーに関わらず必ず Mock（検証・デモ・二重課金防止）。
    - api_key 指定: そのキーで該当 provider のクライアント（BYOK 本線。各自が自分の鍵で課金）。
    - api_key 無し:
        - BYOK モード → サーバ env キーは使わない。安全側で Mock（route が事前にキー必須を弾く想定）。
        - 非 BYOK（個人/テスト） → Anthropic のみサーバ env キー（ANTHROPIC_API_KEY）で従来動作。
    """
    if mock:
        return MockLLMClient()
    prov = normalize_provider(provider)
    # 内製（自前ホスト）LLM: OpenAI 互換の自前サーバへ base_url で繋ぐ。鍵不要。base_url 未設定なら
    # 黙って Mock（来訪者を落とさない／課金しない。UI は llm_status.local で出し分ける）。
    if prov == "local":
        base = local_base_url()
        if not base:
            return MockLLMClient()
        return OpenAIClient(
            api_key=api_key,
            base_url=base,
            model=local_model(),
            max_tokens=max_tokens,
            search_mode=local_search_mode(),
        )
    key = api_key
    if not key and not byok_mode() and prov == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")  # 非 BYOK 個人運用の後方互換（Anthropic のみ）
    if not key:
        return MockLLMClient()
    if prov == "openai":
        return OpenAIClient(api_key=key, max_tokens=max_tokens)
    if prov == "google":
        return GeminiClient(api_key=key, max_tokens=max_tokens)
    return AnthropicClient(api_key=key, max_tokens=max_tokens)


def llm_status() -> dict:
    """LLM 構成の公開ステータス（純関数）。API キーの値そのものは絶対に返さない。

    byok=True なら「各自キー持参」モード。この場合サーバ env キーは来訪者に使われない
    ため、api_key_set は常に False を返す（無認証の /health からの偵察情報を絞る）。
    非 BYOK では従来どおり api_key_set を返す（個人運用でフロントが実 LLM 可否を判定）。
    """
    byok = byok_mode()
    api_key_set = False if byok else bool(os.environ.get("ANTHROPIC_API_KEY"))
    local = local_enabled()
    forced = force_local()
    # フロントの provider 選択用。内製（local）は設定済みのときだけ出す（未設定なら選ばせない）。
    providers = ["anthropic", "openai", "google"]
    if local:
        providers.append("local")
    return {
        "llm": "byok" if byok else ("anthropic" if api_key_set else "mock"),
        "api_key_set": api_key_set,
        "byok": byok,
        "providers": providers,
        # 後方互換（単一）。新しくは research_providers（list）を見る。
        "research_provider": "anthropic",
        # Web 検索（調査役）が使える provider 一覧（anthropic ＋ 検索設定済みの local）。
        "research_providers": research_providers(),
        # 内製（自前ホスト/開源API）が使えるか（base_url 設定済み）。UI は「内製（キー不要）」を出し分ける。
        "local": local,
        # 内製経路で Web 検索が使えるか（OpenRouter 等の検索バックエンド設定済み）。
        "local_search": local_search_enabled(),
        # サーバを丸ごと内製に固定しているか（true なら全実 LLM を内製に回す＝キー不要で実 LLM 可）。
        "force_local": forced,
        # 編成 CRUD が書き込み禁止か（共有インスタンス）。フロントは「管理」UI を隠す。
        "readonly": readonly_mode(),
    }


# -- Web 検索（調査役） -----------------------------------------------------
#
# 凍結契約: 検索するのは「調査役」だけ。各ペルソナは検索しない＝重複ゼロ。結果は
# 「調査」話者のターンとして討論に乗せ、全員が共有する（新 SSE イベント型は増やさない）。
# mock / キー未設定では web_research が canned を返す（無料・テスト可）。real のみ課金。

# 「要調査:」マーカーを拾う正規表現（半角/全角コロンの両方を許容・行頭限定はしない）。
# モデルは "- 要調査:" "**要調査:**" "1. 要調査:" "…。要調査:" など多様に書くため、行頭限定だと
# 取りこぼす（→ 検索されず次の話者が進む事故）。強調記号を外して行内どこでも search で拾う。
_RESEARCH_QUERY_RE = re.compile(r"要調査\s*[:：]\s*(.+?)\s*$")
# 行から markdown 強調を外してからマッチする（** や ` を除去。_ は URL/識別子に出るので残す）。
_RESEARCH_EMPHASIS_RE = re.compile(r"[*＊`]")

# Web 検索の「新規クエリ」合計上限（暴走防止）。env AI_TEAMS_RESEARCH_CAP で可変（既定 12）。
# 旧既定 6 は中規模討論の中盤で枯れて「要調査が無視される」事故になった。dedup 済みの新規クエリ
# だけを数えるので、同じ問いの再検索は数に入らない。1検索 ≒ $0.005 なので 12 でも安い。
_RESEARCH_CAP = int(os.environ.get("AI_TEAMS_RESEARCH_CAP", "12"))


def run_research(client: LLMClient, query: str) -> str:
    """調査役による web 検索の薄いラッパ。client.web_research(query) をそのまま返す。

    mock / キー未設定なら canned（無料）、real のみ課金。例外は web_research 側で
    握って「（調査に失敗: …）」を返すので、ここでは討論を止めない。
    """
    return client.web_research(query)


def _extract_research_queries(text: str) -> list[str]:
    """発言本文から「要調査: <問い>」を抽出する（全角コロン可・箇条書き/強調/行内も拾う）。

    モデルは "- 要調査:" "**要調査:**" "1. 要調査:" "…。要調査:" のように多様に書くため、行頭限定だと
    取りこぼす（→ 検索されず次の話者が進む事故）。強調記号(* `)を外し、行内のどこに現れても search で
    拾う。research=False なら build_context が指示を出さない＝そもそもマーカーは現れない。
    """
    out: list[str] = []
    for raw in (text or "").splitlines():
        line = _RESEARCH_EMPHASIS_RE.sub("", raw)
        m = _RESEARCH_QUERY_RE.search(line)
        if not m:
            continue
        # query 末尾に残りがちな閉じ括弧/記号を軽く掃除（出典リンク等を巻き込まない）。
        q = m.group(1).strip().strip("」』）)").strip()
        if q:
            out.append(q)
    return out


# -- Council 組み立て -------------------------------------------------------
def build_council(
    persona_ids: list[str],
    *,
    rounds_per_phase: int = 1,
    red_team: bool = True,
    red_team_id: str | None = None,
    mock: bool = False,
    api_key: str | None = None,
    provider: str | None = None,
    verbosity: str | None = None,
    custom_personas: list[dict] | None = None,
    materials: str = "",
    research: bool = False,
) -> Council:
    """指定 id のペルソナで Council を作る。未知 id は KeyError。

    materials は全ペルソナが共有する「資料・前提」。Council 構築時に確定し、討論中は
    不変（_speak 経由で build_context に渡る）。materials="" で従来と完全同一。

    research=True で Web 検索（調査役）を有効化する。各ペルソナは「要調査: …」を書ける
    ようになり、producer がそれを拾って調査役が調べ、researcher ターンで全員に共有する。
    research=False（既定）では一切何もしない（後方互換）。
    """
    registry = {p.id: p for p in load_registry()}
    # クライアント定義のカスタムペルソナを重ねる（サーバ非保存・このセッション限定）。
    # persona_from_dict が検証（不正は ValueError → 呼び出し側で 400）。同 id はカスタムが優先。
    for cp in custom_personas or []:
        p = persona_from_dict(cp)
        registry[p.id] = p
    missing = [pid for pid in persona_ids if pid not in registry]
    if missing:
        raise KeyError(missing)
    personas = [registry[pid] for pid in persona_ids]
    # Web 検索（調査役）が使える provider でなければ強制 off にして、「要調査:」ナッジや
    # 無意味な researcher ターンが出ないようにする（honest な劣化）。anthropic は常時、
    # local は検索バックエンド（OpenRouter 等）が設定済みのときだけ research を許す。
    prov = normalize_provider(provider)
    research = research and prov in research_providers()
    # 応答の長さプリセット → 出力上限（途中切れ防止）＋発話スタイル指示。
    vb = VERBOSITY[normalize_verbosity(verbosity)]
    return Council(
        personas,
        make_client(mock, api_key, provider, max_tokens=vb["max_tokens"]),
        rounds_per_phase=rounds_per_phase,
        red_team=red_team,
        red_team_id=red_team_id,
        materials=materials,
        research=research,
        length_hint=vb["hint"],
    )


# -- intake（主訴確認） -----------------------------------------------------
#
# 討論の手前に「主訴を固め逸脱を防ぐ確認質問」を 2〜4 個出す。検証で判明した
# 「事実/数字なしの抽象進行」と「主訴からの逸脱」を準備フェーズで抑える狙い。
# mock or キー未設定なら LLM を呼ばず決定的な定型質問を返す（二重課金防止）。

# mock / キー未設定時に返す決定的な定型質問（曖昧点・制約・既に試したこと・"良い"の定義）。
_INTAKE_FALLBACK_QUESTIONS = [
    "この議題で最も解決したい core の問い（主訴）は何ですか。曖昧な点があれば明確にしてください。",
    "守るべき制約（予算・期限・体制・技術・法務など）はありますか。",
    "すでに試したこと・検討済みの案があれば教えてください（同じ結論の蒸し返しを避けるため）。",
    "この討論にとって「良い結論」とはどういう状態を指しますか（成功の定義）。",
]

_INTAKE_INSTRUCTION = (
    "あなたは討論ファシリテーターです。これから始まる討論の前に、依頼者の主訴を固め、"
    "討論が論点から逸脱しないようにするための確認質問を 2〜4 個作ってください。"
    "曖昧点・前提となる制約・すでに試したこと・『良い結論』の定義などを問う質問にしてください。"
    "質問文のみを改行区切りで出力し、前置きや番号・記号・解説は付けないこと。"
)


def _parse_intake_questions(text: str) -> list[str]:
    """LLM 出力を堅牢に質問 list へパースする。

    - 行分割し、各行の先頭の番号（1. / 1) / １．）や記号（- * ・ ● など）を除去。
    - 前後空白を除き、空行を捨てる。最大 4 件に切り詰める。
    """
    out: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        # 先頭の番号付け（"1." "1)" "1、" "１．" など）と箇条書き記号を剥がす。
        # 区切りは半角/全角の . ) ] 、． 。 : ： を許容（全角 '．' 対応）。
        line = re.sub(r"^[\s]*[\(\[（［]?[0-9０-９]+[\)\]．。.、，:：）］]?[\s]*", "", line)
        line = re.sub(r"^[\s]*[-*・●○◯••>＞]+[\s]*", "", line)
        line = line.strip()
        if line:
            out.append(line)
        if len(out) >= 4:
            break
    return out


def generate_intake_questions(
    topic: str,
    materials: str = "",
    *,
    mock: bool = False,
    api_key: str | None = None,
    provider: str | None = None,
) -> list[str]:
    """討論前の主訴確認質問を 2〜4 個返す。

    mock=True または（実キーが取得できない場合）LLM を呼ばず決定的な定型質問を返す
    （検証・コスト対策）。実呼び出し時は make_client(mock, api_key) 経由で LLM に依頼し、
    _parse_intake_questions で堅牢にパースする。LLM から取れなければ定型にフォールバック。
    """
    client = make_client(mock, api_key, provider)
    if isinstance(client, MockLLMClient):
        # mock / キー未設定: LLM を呼ばず定型（決定的）。
        return list(_INTAKE_FALLBACK_QUESTIONS)

    head = f"【議題】\n{topic}"
    if materials:
        head += f"\n\n【資料・前提】\n{materials}"
    try:
        text = client.generate(
            system=_INTAKE_INSTRUCTION,
            messages=[{"role": "user", "content": head}],
            model=DEFAULT_MODEL,
            temperature=0.3,
        )
    except Exception:  # noqa: BLE001 — LLM 失敗時は定型にフォールバック（討論は止めない）
        return list(_INTAKE_FALLBACK_QUESTIONS)
    questions = _parse_intake_questions(text)
    if len(questions) < 2:
        # パースで 2 個に満たなければ定型で補う（最低 2 個・最大 4 個を保証）。
        return list(_INTAKE_FALLBACK_QUESTIONS)
    return questions


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


# -- セッション（バックグラウンド実行＋イベントバッファ＋再接続） -----------------
#
# 設計 v2（INJECTION_DESIGN_2026-06.md）の中核。SSE は一方向なので、討論を HTTP 接続から
# 切り離してバックグラウンドスレッドで完走させ、Session が seq 付きイベントを溜める。
# 接続が切れても進行は続き、再接続時に events[cursor:] を再生 → ライブ継続できる。
# メモリ常駐・単一ワーカー前提（マルチワーカー共有ストアは Phase 6 永続化と一緒に）。

# 終了後も短時間残し、遅れた再接続が最終 transcript を再生できるようにする（簡易 GC）。
MAX_SESSIONS = 50

# 同時に「進行中（running/paused）」でいられるセッションの上限。floor-open の paused は
# 無期限待機で GC されないため、これが無いと公開時に大量生成でスレッド/メモリを枯渇させられる。
# env AI_TEAMS_MAX_ACTIVE で可変（既定 12）。超過時の生成は CapacityError → 429。
MAX_ACTIVE_SESSIONS = int(os.environ.get("AI_TEAMS_MAX_ACTIVE", "12"))


class CapacityError(RuntimeError):
    """同時進行セッション数が上限に達した（main.py で 429 にマップ）。"""


@dataclass
class HumanMessage:
    """人間からの割り込み入力。

    kind:
      - "followup": 追い質問。本編中は各 Turn 直後に注入、floor-open 中は deepen 1周のトリガ。
      - "close": floor-open で synthesis（議事録）を生成→再び floor-open。
      - "finish": floor-open でループを抜けて done。
    将来 intervention/rewind を kind で追加。
    """

    kind: str = "followup"
    text: str = ""
    target: str | None = None  # 将来のペルソナ指名。MVP 未使用


@dataclass
class Session:
    """討論1回分の実行状態。events は append-only の再生元（各 event に連番 seq）。"""

    id: str
    topic: str
    council: Council
    inbox: "queue.Queue[HumanMessage]" = field(default_factory=queue.Queue)
    events: list[dict] = field(default_factory=list)
    cond: threading.Condition = field(default_factory=threading.Condition)
    status: str = "running"  # running | paused | done | error
    thread: threading.Thread | None = None
    # 議場開放（floor-open）モデルを使うか。True なら本編フェーズ後に自動 synthesis せず
    # 一時停止（paused）してユーザー入力（followup/close/finish）を待つ。False なら従来どおり
    # 自動完走（直接 start_session を呼ぶ既存テストの後方互換）。HTTP（Web）は既定 True。
    interactive: bool = False
    # 追い質問の受付可否。仕上げ（summary/synthesis）に入ったら False にして、
    # それ以降の追い質問は受理せず 409 を返す（202 のまま永久ドロップを防ぐ）。
    accepting: bool = True
    # 協調キャンセル。停止操作で True にすると、プロデューサが次のターン前に打ち切る
    # （実 LLM の発注を止めてコストを抑える）。
    cancelled: bool = False


SESSIONS: dict[str, Session] = {}
_REGISTRY_LOCK = threading.Lock()


def _append(session: Session, event: str, data: dict) -> None:
    """seq と ts を採番してイベントを追加し、tail 中の読み手全員に通知する。

    ts（time.time()）は採番時に1回だけ確定して event dict に格納する。tail() は再生時に
    この保存済み ts をそのまま載せるので、再接続で同じイベントを再生しても ts は不変。
    """
    with session.cond:
        seq = len(session.events)
        session.events.append(
            {"seq": seq, "ts": time.time(), "event": event, "data": data}
        )
        session.cond.notify_all()


def _drain(inbox: "queue.Queue[HumanMessage]") -> list[HumanMessage]:
    """inbox に溜まった人間メッセージを非ブロッキングで全件取り出す（kind 不問）。"""
    out: list[HumanMessage] = []
    while True:
        try:
            out.append(inbox.get_nowait())
        except queue.Empty:
            break
    return out


def _drain_followups(inbox: "queue.Queue[HumanMessage]") -> list[HumanMessage]:
    """本編フェーズ中の注入用に kind=="followup" のみを drain する。

    close/finish が誤って人間ターン化されないよう、本編中は followup だけを拾う。
    close/finish は floor-open ループの inbox 待機側で処理する（誤って drain したものは
    inbox に戻す）。
    """
    out: list[HumanMessage] = []
    not_followup: list[HumanMessage] = []
    while True:
        try:
            msg = inbox.get_nowait()
        except queue.Empty:
            break
        if getattr(msg, "kind", "followup") == "followup":
            out.append(msg)
        else:
            not_followup.append(msg)
    # 本編中に届いた close/finish は inbox に戻し、floor-open で処理させる。
    for msg in not_followup:
        inbox.put(msg)
    return out


def post_message(session: Session, msg: HumanMessage) -> None:
    """人間メッセージをセッションの inbox に積む（プロデューサが次の drain で拾う）。"""
    session.inbox.put(msg)


def cancel_session(session: Session) -> None:
    """進行中の討論を協調的に打ち切る。

    プロデューサは次のターンの LLM 発注前に cancelled を見て break する（実 LLM の
    課金を止める）。既に発注済みの当該ターンは完走する（per-turn 粒度）。
    floor-open で inbox 待機中でも _FLOOR_WAIT_POLL ごとに cancelled を見て抜ける。
    """
    session.cancelled = True
    session.accepting = False


def close_floor(session: Session) -> None:
    """floor-open に close を投函する → プロデューサが synthesis（議事録）を生成し再び floor-open。"""
    post_message(session, HumanMessage(kind="close"))


def finish_floor(session: Session) -> None:
    """floor-open に finish を投函する → プロデューサが floor-open ループを抜けて done。"""
    post_message(session, HumanMessage(kind="finish"))


# floor-open 中の inbox 待機ポーリング間隔（秒）。cancelled を見られるよう短くブロックする。
_FLOOR_WAIT_POLL = 0.1


def _produce(session: Session) -> None:
    """バックグラウンドで討論を完走（非対話）または floor-open ループ（対話）で進める。

    接続の有無に関わらず走る（再接続のため）。orchestrator は turn_start/delta を emit するので、
    Turn 確定後に turn_end を、全体の前後に start/done を付ける（設計 v2）。

    interactive=False: 従来どおり council.run(...) を1回回して done（後方互換・非対話）。
    interactive=True: 本編（deliberate）後に floor-open ループへ入り、ユーザー入力
      （followup/close/finish）を待って deepen/synthesize し、finish で done。
    """

    def emit(ev: dict) -> None:
        etype = ev["type"]
        # 非対話のみ: 仕上げフェーズ（summary/synthesis）の turn_start を見た瞬間に追い質問を
        # 締め切る（受理したのに拾われない窓を塞ぐ）。対話（floor-open）では締めた後も deepen
        # できるので、followup は最後まで受理し続ける（ここで accepting を落とさない）。
        if (
            not session.interactive
            and etype == "turn_start"
            and ev.get("phase") in ("summary", "synthesis")
        ):
            session.accepting = False
        data = {k: v for k, v in ev.items() if k != "type"}
        _append(session, etype, data)

    try:
        _append(session, "start", {"topic": session.topic, "session_id": session.id})

        if not session.interactive:
            # --- 非対話（後方互換）: opening+本編+synthesis を自動完走 ---
            for turn in session.council.run(
                session.topic, emit=emit, pull=lambda: _drain_followups(session.inbox)
            ):
                _append(session, "turn_end", {"turn_id": turn.turn_id})
                # 停止操作（cancelled）なら、次のターンの LLM 発注前に打ち切る（コスト抑制）。
                if session.cancelled:
                    session.accepting = False
                    break
            _append(session, "done", {})
            _set_status(session, "done")
            return

        # --- 対話（floor-open）---
        council = session.council
        transcript: list = []
        ids = count()  # turn_id 採番。deliberate/deepen/synthesize で継続共有する。

        # Web 検索（調査役）の状態。research=False なら一切使わない（後方互換）。
        #   seen: 正規化済みクエリの重複排除集合（クエリ単位で重複ゼロ）。
        #   count: 累計検索回数（seed 含む。_RESEARCH_CAP で打ち止め）。
        research_seen: set[str] = set()
        research_state = {"count": 0}

        def _pickup_research(turn) -> None:
            """1ターンの本文から「要調査:」を拾い、新規クエリだけ調べて researcher ターンを挿入する。

            research=False なら何もしない。クエリは正規化（小文字 strip）して seen で重複排除し、
            _RESEARCH_CAP に達したら無視（暴走防止）。検索結果は researcher ターンとして
            transcript に乗り、全員が共有する（emit_research_turn が transcript.append する）。
            """
            if not council.research or session.cancelled:
                return  # 無効時、またはキャンセル後は新規検索を発火しない（コスト抑制）
            for query in _extract_research_queries(getattr(turn, "content", "") or ""):
                norm = query.lower().strip()
                if not norm or norm in research_seen:
                    continue
                if research_state["count"] >= _RESEARCH_CAP:
                    # cap 到達後は調べない（ログのみ・暴走防止）。
                    break
                rid = next(ids)
                # 検索の前に「調査中」を先出し（数十秒の検索中も UI に進行が見えるように・クエリ付き）。
                council.emit_research_start(emit, rid, query=query)
                brief = run_research(council.client, query)
                rt = council.emit_research_turn(
                    transcript, brief, emit=emit, turn_id=rid, emit_start=False
                )
                _append(session, "turn_end", {"turn_id": rt.turn_id})
                research_seen.add(norm)
                research_state["count"] += 1

        # Phase A: seed 調査（research=True のときだけ）。deliberate 開始前に topic を1回調べ、
        # researcher ターンとして全員の議論の土台に乗せる。seed を seen に登録し、カウンタ+1。
        if council.research:
            seed = session.topic
            seed_norm = seed.lower().strip()
            if seed_norm:
                seed_rid = next(ids)
                # 検索の前に「調査中」を先出し（最初の発言前の長い待ちを「『議題』を調べています…」で見せる）。
                council.emit_research_start(emit, seed_rid, query=seed)
                seed_brief = run_research(council.client, seed)
                seed_turn = council.emit_research_turn(
                    transcript, seed_brief, emit=emit, turn_id=seed_rid, emit_start=False
                )
                _append(session, "turn_end", {"turn_id": seed_turn.turn_id})
                research_seen.add(seed_norm)
                research_state["count"] += 1

        # 本編フェーズ（opening+発散/批判/収束）。本編中の追い質問は followup のみ注入。
        for turn in council.deliberate(
            session.topic, transcript, emit=emit,
            pull=lambda: _drain_followups(session.inbox), ids=ids,
        ):
            _append(session, "turn_end", {"turn_id": turn.turn_id})
            # 各ターン後に「要調査:」を拾って調べ、researcher ターンを挿入（research=False なら no-op）。
            _pickup_research(turn)
            if session.cancelled:
                session.accepting = False
                _append(session, "done", {})
                _set_status(session, "done")
                return

        # floor-open ループ。
        while True:
            if session.cancelled:
                break
            # (a) 一時停止に入る合図。
            _set_status(session, "paused")
            _append(session, "paused", {"phase": "floor_open"})

            # (b) inbox をブロッキング待機（無期限・無料）。cancelled を一定間隔で見て抜けられる。
            msg: HumanMessage | None = None
            while msg is None:
                if session.cancelled:
                    break
                try:
                    msg = session.inbox.get(timeout=_FLOOR_WAIT_POLL)
                except queue.Empty:
                    continue
            if msg is None:  # cancelled で抜けた
                break

            # (c) kind で分岐。
            if msg.kind == "finish":
                break
            if msg.kind == "close":
                _set_status(session, "running")
                for turn in council.synthesize(session.topic, transcript, emit=emit, ids=ids):
                    _append(session, "turn_end", {"turn_id": turn.turn_id})
                    if session.cancelled:
                        break
                # 締めても議場は開いたまま → a に戻って再び floor-open。
                continue
            # followup（既定）: 同時に届いた followup も束ねて drain し deepen 1周。
            _set_status(session, "running")
            extra = _drain_followups(session.inbox)
            for turn in council.deepen(
                session.topic, transcript, [msg, *extra], emit=emit, ids=ids
            ):
                _append(session, "turn_end", {"turn_id": turn.turn_id})
                # deepen 中のターンも「要調査:」を拾う（synthesize 中は拾わない）。
                _pickup_research(turn)
                if session.cancelled:
                    break
            # a に戻って再び floor-open。

        _append(session, "done", {})
        _set_status(session, "done")
    except Exception as exc:  # noqa: BLE001 — 読み手にエラーを通知して締める
        _append(session, "error", {"message": str(exc)})
        _set_status(session, "error")


def _set_status(session: Session, status: str) -> None:
    with session.cond:
        session.status = status
        session.cond.notify_all()


def _gc_locked() -> None:
    """件数上限を超えたら、終了済み（done/error）セッションを古い順に破棄する。

    running / paused（floor-open で入力待機中）は進行中とみなして残す。
    """
    if len(SESSIONS) <= MAX_SESSIONS:
        return
    for sid, s in list(SESSIONS.items()):  # dict は挿入順 = 古い順
        if len(SESSIONS) <= MAX_SESSIONS:
            break
        if s.status in ("done", "error"):
            del SESSIONS[sid]


def start_session(council: Council, topic: str, *, interactive: bool = False) -> Session:
    """Session を生成・登録し、プロデューサスレッドを起動して返す。

    interactive=False（既定）なら従来どおり自動完走する（直接呼ぶ既存テストの後方互換）。
    interactive=True なら本編後に floor-open（一時停止）してユーザー入力を待つ。
    """
    session = Session(
        id=uuid.uuid4().hex, topic=topic, council=council, interactive=interactive
    )
    with _REGISTRY_LOCK:
        _gc_locked()
        # 進行中（running/paused）の同時上限。paused は GC されないので、ここで生成を絞り
        # スレッド/メモリ枯渇（公開時の DoS）を防ぐ。done/error は数に含めない。
        active = sum(1 for s in SESSIONS.values() if s.status in _ALIVE_STATUSES)
        if active >= MAX_ACTIVE_SESSIONS:
            raise CapacityError(
                f"同時に進行できる討論は {MAX_ACTIVE_SESSIONS} 件までです。"
                "進行中の討論を終了してから再度お試しください。"
            )
        SESSIONS[session.id] = session
    thread = threading.Thread(target=_produce, args=(session,), daemon=True)
    session.thread = thread
    thread.start()
    return session


def get_session(session_id: str) -> Session | None:
    with _REGISTRY_LOCK:
        return SESSIONS.get(session_id)


_ALIVE_STATUSES = ("running", "paused")
_FINAL_STATUSES = ("done", "error")


# floor-open（paused）中などアイドル時の keepalive 間隔（秒）。バッファするプロキシ
# （cloudflared クイックトンネル等）に溜めたデータを flush させ、モバイル/プロキシの idle 切断も防ぐ。
# floor-open など idle 時の keepalive 間隔（秒）。プロキシ/モバイルの idle 切断を防ぐ。
# 本命の cloudflared バッファ対策は「再接続を POST で叩く」こと（GET はバッファ、POST は素通し）。
# 以下は補助（一部プロキシで stream を早く開かせる初回パディング＋idle keepalive）。
_HEARTBEAT_S = 15.0
_OPEN_PADDING = ":" + (" " * 1024) + "\n\n"
_HEARTBEAT = ": hb\n\n"


def tail(session: Session, cursor: int = 0) -> Iterator[str]:
    """events[cursor:] を再生 → ライブ tail を SSE 文字列で yield する（再接続対応）。

    各 data に seq と ts を載せる（seq=再接続カーソル用、ts=採番時刻で再接続再生でも不変）。
    終端は status が done/error のときだけ。running/paused（floor-open 入力待機）では
    接続を保ち cond.wait で待ち続ける（paused で SSE を閉じない）。

    バッファするプロキシ対策に、先頭でパディング、各バッチ後と待機タイムアウト時に heartbeat
    （`: hb` コメント＝クライアントは無視）を流して確実に flush させ、idle 接続も保つ。
    """
    yield _OPEN_PADDING
    while True:
        with session.cond:
            if cursor >= len(session.events) and session.status in _ALIVE_STATUSES:
                session.cond.wait(timeout=_HEARTBEAT_S)
            new = session.events[cursor:]
            cursor += len(new)
            finished = (
                session.status in _FINAL_STATUSES and cursor >= len(session.events)
            )
        for ev in new:
            yield sse(ev["event"], {**ev["data"], "seq": ev["seq"], "ts": ev["ts"]})
        if finished:
            return
        # backlog/新規を出した直後・待機タイムアウト時とも heartbeat を流して flush＋keepalive。
        yield _HEARTBEAT


# -- ペルソナ CRUD ----------------------------------------------------------
#
# personas/{category}/{id}.yaml に保存する。書き出すキーは known セットのみ。
# id→実パスの対応は load_personas_with_paths で取り、category 変更時は旧パスを unlink する
# （ファイル名から id を推測しない＝jobs.yaml の id=steve_jobs のような不一致に対応）。

# YAML に書き出すキー（persona_from_dict の known と揃える）。
_PERSONA_WRITE_KEYS = (
    "id",
    "display_name",
    "system_prompt",
    "category",
    "avatar",
    "model",
    "temperature",
    "tags",
    "speaks",
    "accent",
)


def slugify(text: str) -> str:
    """表示名などから安全な id（小文字英数とハイフン）を作る。空なら 'persona'。"""
    text = (text or "").strip().lower()
    # 英数とハイフン・アンダースコア以外を区切りに潰す
    slug = re.sub(r"[^a-z0-9_-]+", "-", text).strip("-")
    return slug or "persona"


_SLUG_RE = re.compile(r"^[a-z0-9_-]+$")


def _validate_id(value: str, *, kind: str) -> None:
    """書込先パスに使う id を検証する（パストラバーサル防止）。

    `../` や絶対パス・区切り文字を含む id で PERSONAS_DIR/PRESETS_DIR の外に
    書き込まれる/既存ファイルを上書きされるのを防ぐ。小文字英数・ハイフン・
    アンダースコアのみ許可。不正なら ValueError（呼び出し側で 400 にマップ）。
    """
    if not isinstance(value, str) or not _SLUG_RE.match(value):
        raise ValueError(
            f"invalid {kind} id: 小文字英数字・ハイフン・アンダースコアのみ使用できます"
        )


def _assert_within(path: Path, base: Path) -> None:
    """多層防御: 解決後パスが base 配下であることを保証する（外なら ValueError）。"""
    if not path.resolve().is_relative_to(base.resolve()):
        raise ValueError("invalid path: 書込先がディレクトリ外です")


def persona_detail(p: Persona) -> dict:
    """編集画面向けの完全表現。persona_public に system_prompt/temperature/avatar を足す。

    accent は accent_color（フォールバック後）ではなく **生値** で上書きする（編集時に
    「未指定（=カテゴリ色）」と「明示指定」を区別できるように）。
    """
    detail = persona_public(p)
    detail["system_prompt"] = p.system_prompt
    detail["temperature"] = p.temperature
    detail["avatar"] = p.avatar
    detail["accent"] = p.accent  # 生値で上書き（未指定なら None）
    return detail


def get_persona_detail(persona_id: str) -> dict:
    """1件の編集用詳細を返す。未知 id は KeyError（404 にマップ）。"""
    for p in load_registry():
        if p.id == persona_id:
            return persona_detail(p)
    raise KeyError(persona_id)


def _persona_path(category: str, persona_id: str) -> Path:
    return PERSONAS_DIR / category / f"{persona_id}.yaml"


def _write_persona_file(path: Path, data: dict) -> None:
    """known キーのみを safe_dump で書き出す。"""
    import yaml

    out = {k: data[k] for k in _PERSONA_WRITE_KEYS if k in data and data[k] is not None}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            out, f, allow_unicode=True, sort_keys=False, default_flow_style=False
        )


def save_persona(data: dict, *, expect_id: str | None = None) -> Persona:
    """ペルソナを作成（expect_id=None）または更新（expect_id=既存id）して保存する。

    - persona_from_dict で検証（ValueError は呼び出し側で 400 にマップ）。
    - 新規作成で id 衝突 → ValueError("persona id exists")（409 にマップ）。
    - 更新で expect_id が存在しない → KeyError（404 にマップ）。
    - 保存先 = personas/{category}/{id}.yaml。category 変更時は **旧パスを unlink**。
      旧パスは load_personas_with_paths が返す id→実パスから取る（ファイル名から推測しない）。
    - 手順: 新ファイル書込 → 旧ファイル unlink。書込失敗時は新ファイルを削除してロールバック。
    """
    persona = persona_from_dict(data)  # 検証（ValueError）
    _validate_id(persona.id, kind="persona")  # パストラバーサル防止
    pairs = load_personas_with_paths(PERSONAS_DIR)
    id_to_path = {p.id: path for p, path in pairs}

    new_path = _persona_path(persona.category, persona.id)
    _assert_within(new_path, PERSONAS_DIR)  # 多層防御

    if expect_id is None:
        # 新規作成: id 衝突を弾く
        if persona.id in id_to_path:
            raise ValueError("persona id exists")
        old_path: Path | None = None
    else:
        # 更新: 対象が存在しなければ 404
        if expect_id not in id_to_path:
            raise KeyError(expect_id)
        # id 変更先が別の既存 id と衝突するなら弾く
        if persona.id != expect_id and persona.id in id_to_path:
            raise ValueError("persona id exists")
        old_path = id_to_path[expect_id]

    # 新ファイル書込 → 旧ファイル unlink（順序厳守）。書込失敗時はロールバック。
    existed_before = new_path.exists()
    try:
        _write_persona_file(new_path, data)
    except Exception:
        # 書き出し途中で失敗したら、今回新規作成したファイルを消す（既存上書き時は残す）。
        if not existed_before and new_path.exists():
            new_path.unlink()
        raise

    if old_path is not None and old_path.resolve() != new_path.resolve():
        # category や id の変更でパスが動いた → 旧ファイルを削除
        try:
            old_path.unlink()
        except FileNotFoundError:
            pass

    return persona


def delete_persona(persona_id: str) -> None:
    """ペルソナを削除する。未知 id は KeyError（404 にマップ）。実パスは id→path で引く。"""
    pairs = load_personas_with_paths(PERSONAS_DIR)
    id_to_path = {p.id: path for p, path in pairs}
    if persona_id not in id_to_path:
        raise KeyError(persona_id)
    try:
        id_to_path[persona_id].unlink()
    except FileNotFoundError:
        # 既に消えていれば成功扱い（冪等）。生 OSError を 500 にしない。
        pass


# -- プリセット -------------------------------------------------------------
#
# presets/builtin/ … 同梱（builtin:true, 読取専用）。presets/ 直下 … ユーザー（書込可）。
# スキーマ: {id, name, description?, persona_ids[], rounds_per_phase=1, red_team=true,
#           red_team_id?, builtin}

_PRESET_WRITE_KEYS = (
    "id",
    "name",
    "description",
    "persona_ids",
    "rounds_per_phase",
    "red_team",
    "red_team_id",
)


def preset_public(preset: dict) -> dict:
    """プリセットの公開表現（builtin フラグを明示）。"""
    return {
        "id": preset["id"],
        "name": preset.get("name", preset["id"]),
        "description": preset.get("description"),
        "persona_ids": list(preset.get("persona_ids", [])),
        "rounds_per_phase": int(preset.get("rounds_per_phase", 1)),
        "red_team": bool(preset.get("red_team", True)),
        "red_team_id": preset.get("red_team_id"),
        "builtin": bool(preset.get("builtin", False)),
    }


def _preset_from_file(path: Path, *, builtin: bool) -> dict:
    import yaml

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: トップレベルは mapping である必要があります")
    data.setdefault("id", path.stem)
    data["builtin"] = builtin
    return data


def load_presets() -> list[dict]:
    """builtin + ユーザーの全プリセットを id でソートして返す（公開表現）。

    同 id が両方にあればユーザー側を優先する（上書き想定）。
    """
    presets: dict[str, dict] = {}
    if PRESETS_BUILTIN_DIR.is_dir():
        for path in sorted(PRESETS_BUILTIN_DIR.glob("*.y*ml")):
            p = _preset_from_file(path, builtin=True)
            presets[p["id"]] = p
    if PRESETS_DIR.is_dir():
        for path in sorted(PRESETS_DIR.glob("*.y*ml")):  # 直下のみ（builtin/ は除外）
            p = _preset_from_file(path, builtin=False)
            presets[p["id"]] = p
    return [preset_public(presets[pid]) for pid in sorted(presets)]


def get_preset(preset_id: str) -> dict:
    """1件取得。未知 id は KeyError（404 にマップ）。"""
    for p in load_presets():
        if p["id"] == preset_id:
            return p
    raise KeyError(preset_id)


def _user_preset_path(preset_id: str) -> Path:
    return PRESETS_DIR / f"{preset_id}.yaml"


def _validate_preset_personas(persona_ids: list[str]) -> None:
    """persona_ids が全て実在することを確認する。未知があれば ValueError。"""
    known = {p.id for p in load_personas(PERSONAS_DIR)}
    missing = [pid for pid in persona_ids if pid not in known]
    if missing:
        raise ValueError(f"unknown persona ids: {missing}")


def _existing_preset_or_none(preset_id: str) -> dict | None:
    try:
        return get_preset(preset_id)
    except KeyError:
        return None


def save_preset(data: dict, *, create: bool) -> dict:
    """プリセットを作成（create=True）または更新（create=False）して保存する。

    - create=True で id 衝突 → ValueError("preset id exists")（409）。
    - update で対象が存在しない → KeyError（404）。
    - builtin プリセットへの更新 → ValueError("builtin preset is read-only")（409）。
    - 未知 persona → ValueError("unknown persona ids: [...]")（400）。
    - 保存先は必ず presets/ 直下（ユーザー領域）。builtin/ には書かない。
    """
    import yaml

    preset_id = data["id"]
    _validate_id(preset_id, kind="preset")  # パストラバーサル防止
    existing = _existing_preset_or_none(preset_id)

    if create:
        if existing is not None:
            raise ValueError("preset id exists")
    else:
        if existing is None:
            raise KeyError(preset_id)
        if existing.get("builtin"):
            raise ValueError("builtin preset is read-only")

    _validate_preset_personas(list(data.get("persona_ids", [])))

    out = {k: data[k] for k in _PRESET_WRITE_KEYS if k in data and data[k] is not None}
    out["id"] = preset_id
    path = _user_preset_path(preset_id)
    _assert_within(path, PRESETS_DIR)  # 多層防御
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            out, f, allow_unicode=True, sort_keys=False, default_flow_style=False
        )
    return get_preset(preset_id)


def delete_preset(preset_id: str) -> None:
    """プリセットを削除する。未知 id は KeyError（404）。builtin は ValueError（409）。"""
    existing = _existing_preset_or_none(preset_id)
    if existing is None:
        raise KeyError(preset_id)
    if existing.get("builtin"):
        raise ValueError("builtin preset is read-only")
    _user_preset_path(preset_id).unlink()
