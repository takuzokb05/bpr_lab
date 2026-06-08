"""FastAPI アプリ本体（ルーティングのみ薄く）。

起動: uvicorn api.main:app --reload --port 8000   （sandbox/ai-teams で実行）
本番 LLM を使うには環境変数 ANTHROPIC_API_KEY を設定。未設定ならモック応答で動く。
"""

from __future__ import annotations

import hmac
import logging
import time
from pathlib import Path
from typing import Literal, NoReturn

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import service
from core.llm_client import _env

app = FastAPI(title="AI Teams API", version="3.0.0")

# トークン認証で保護する API パスのプレフィックス。これら以外（静的フロント / や /_next、
# /health）は無認証で通す（SPA を読み込めるように・同一オリジン配信のため）。
_PROTECTED_PREFIXES = ("/sessions", "/personas", "/presets", "/intake")


def _allowed_origins() -> list[str]:
    """CORS の allow_origins を env から読む（カンマ区切り）。

    AI_COUNCIL_ALLOWED_ORIGINS 未設定なら従来既定 ["http://localhost:3000"]。
    空白を除去し、空要素は落とす。すべて空なら既定にフォールバック（後方互換）。
    """
    raw = _env("ALLOWED_ORIGINS")
    if not raw:
        return ["http://localhost:3000"]
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or ["http://localhost:3000"]


@app.middleware("http")
async def require_api_token(request: Request, call_next):
    """最小認証ミドルウェア（env-gated）。

    env AI_COUNCIL_API_TOKEN を読む。
    - 未設定 → 認証無効。何もせず通す（ローカル開発・既存テストはこの経路で無改修 pass）。
    - 設定あり → Authorization ヘッダが "Bearer {token}" と一致しなければ 401。
      ただし /health（稼働確認）と OPTIONS（CORS プリフライト）は常に通す。
    """
    token = _env("API_TOKEN")
    if token and request.method != "OPTIONS":
        # API（コスト・データ操作）パスだけ保護。静的フロント(/ や /_next)・/health は通す。
        path = request.url.path
        if any(path == p or path.startswith(p + "/") for p in _PROTECTED_PREFIXES):
            authorization = request.headers.get("authorization") or ""
            # 定数時間比較（タイミング攻撃でのトークン推測を防ぐ）。
            if not hmac.compare_digest(authorization, f"Bearer {token}"):
                return JSONResponse(status_code=401, content={"detail": "unauthorized"})
    return await call_next(request)


# CORS。allow_origins は env AI_COUNCIL_ALLOWED_ORIGINS で可変（未設定なら localhost:3000）。
# allow_headers=["*"] で Authorization ヘッダを許可（最小認証のため）。
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
    # クロスオリジン配信時もフロントが X-Session-Id（再接続用の seed）を読めるよう露出する。
    # 本番は同一オリジン（uvicorn が SPA 同居）なので未指定でも効くが、cross-origin でも契約を保つ。
    expose_headers=["X-Session-Id"],
)


# -- レート制限（簡易・インメモリ・単一ワーカー前提） -------------------------
# 公開時のコスト/DoS 抑止。クライアント IP ごとに固定窓でリクエスト数を制限する。
# cloudflared 経由では request.client.host が 127.0.0.1 になるため、実 IP は
# CF-Connecting-IP / X-Forwarded-For を優先して見る（無ければ接続元）。注意: これらの
# ヘッダは原理的に偽装可能なので「完全な本人特定」ではなく濫用のハードルを上げる多層防御。
_RATE_MAX = int(_env("RATE_MAX", "20"))  # 窓あたり許容数
_RATE_WINDOW = float(_env("RATE_WINDOW", "60"))  # 窓（秒）
_RATE_HITS: dict[str, list[float]] = {}


def _trust_proxy_ip() -> bool:
    """プロキシ系ヘッダ（cf-connecting-ip / x-forwarded-for）を信頼するか。

    既定 "1"（現行挙動維持＝cloudflared 経由で実 IP を見る）。"0" のときはこれらの
    偽装可能ヘッダを信頼せず、接続元 request.client.host のみでレート制限する。
    """
    return _env("TRUST_PROXY_IP", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _client_ip(request: Request) -> str:
    # プロキシヘッダ信頼が無効なら偽装可能な cf/xff を見ず接続元のみ使う（ヘッダ偽装対策）。
    if _trust_proxy_ip():
        cf = request.headers.get("cf-connecting-ip")
        if cf:
            return cf.strip()
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_check(request: Request) -> None:
    """固定窓レート制限。超過なら 429。LLM/コストを伴う重い経路で呼ぶ。"""
    ip = _client_ip(request)
    now = time.monotonic()
    hits = [t for t in _RATE_HITS.get(ip, ()) if now - t < _RATE_WINDOW]
    if len(hits) >= _RATE_MAX:
        _RATE_HITS[ip] = hits
        raise HTTPException(
            status_code=429,
            detail="リクエストが多すぎます。しばらく待って再度お試しください。",
        )
    hits.append(now)
    _RATE_HITS[ip] = hits
    if len(_RATE_HITS) > 1024:  # 肥大防止: 期限切れエントリを掃除
        stale = [
            k
            for k, v in _RATE_HITS.items()
            if not any(now - t < _RATE_WINDOW for t in v)
        ]
        for k in stale:
            _RATE_HITS.pop(k, None)


def _assert_writable() -> None:
    """読み取り専用モード（共有インスタンス）では編成の書き込みを 403 で拒否する。"""
    if service.readonly_mode():
        raise HTTPException(
            status_code=403,
            detail="この公開インスタンスでは編成の作成・変更・削除はできません（読み取り専用）。",
        )


@app.on_event("startup")
def _warn_public_writable() -> None:
    """公開時の安全策。書込可（readonly でない）かつ BYOK でない構成は、同梱ペルソナ/プリセットを
    来訪者が誤って上書き・削除し得るため、共有公開なら AI_COUNCIL_READONLY=1 を推奨する旨を1回警告する。
    """
    if not service.readonly_mode() and not service.byok_mode():
        logging.getLogger("uvicorn.error").warning(
            "書込可能かつ非 BYOK 構成です。共有公開する場合は AI_COUNCIL_READONLY=1 を推奨します"
            "（同梱ペルソナ/プリセットの誤上書き・削除を防ぐため）。"
        )


def _resolve_api_key(
    mock: bool, key_header: str | None, provider: str | None = None
) -> str | None:
    """実 LLM 呼び出しに使う API キーを決める（BYOK ガード）。

    - mock=True: キー不要（None を返す。make_client が Mock を返す）。
    - provider=local（内製・自前ホスト）: キー不要（None。make_client が base_url で繋ぐ）。BYOK でも 400 にしない。
    - BYOK モードで実 LLM を要求したのにキー未提供 → 400（来訪者は自分のキーが必須）。
    - それ以外: 渡されたキー（無ければ None ＝ 非 BYOK で Anthropic はサーバ env キーへフォールバック可）。
    キーはどこにもログ/保存しない（クライアントのメモリ内のみ・セッション終了で消える）。
    """
    if mock:
        return None
    if service.normalize_provider(provider) == "local":
        return None  # 内製は鍵不要。BYOK 公開時でも local は所有者の自前サーバを使う（鍵を求めない）。
    key = (key_header or "").strip() or None
    if service.byok_mode() and not key:
        raise HTTPException(
            status_code=400,
            detail="このインスタンスは各自の API キーが必要です（左の設定でプロバイダを選びキーを入力してください）。",
        )
    return key


class IntakeQA(BaseModel):
    """主訴確認の 1 問 1 答（質問とユーザー回答のペア）。回答は任意・空可。"""

    question: str = Field(..., min_length=1)
    answer: str = ""


# 「資料・前提」テキストの上限（文字）。毎ターン再注入されるため過大プロンプトを入口で弾く。
_MATERIALS_MAX = 20000


class CustomPersona(BaseModel):
    """クライアント（ブラウザ）定義のペルソナ。サーバには保存せず、このセッション限定で
    レジストリに重ねて使う（readonly な共有インスタンスでも各自が自分の編成を持てる）。

    category はパネリスト系のみ許可（司会/議長/書記の構造役は乗っ取らせない）。id は
    パストラバーサル防止と衝突回避のため charset 制限（書込はしないが speaker_id 等に使う）。
    system_prompt と件数に上限を設けて実 LLM のトークン費・濫用を抑える。
    """

    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    display_name: str = Field(..., min_length=1, max_length=80)
    system_prompt: str = Field(..., min_length=1, max_length=4000)
    category: Literal["thinking", "founders", "philosophers"] = "thinking"
    tags: list[str] = Field(default_factory=list, max_length=8)
    model: str | None = None
    # ピッカー表示専用の一行説明＋詳細（サーバ非保存・討論プロンプトには不使用）。受け口に無いと
    # extra='ignore' で捨てられるため明示。表示のみだが濫用防止に長さ上限を付ける。
    description: str | None = Field(default=None, max_length=200)
    detail: str | None = Field(default=None, max_length=600)


class SessionRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    persona_ids: list[str] = Field(..., min_length=1)
    rounds_per_phase: int = Field(1, ge=1, le=5)
    red_team: bool = True
    red_team_id: str | None = None
    mock: bool = False
    # 議場開放（floor-open）モデル。Web（HTTP）は既定で本編後に一時停止し、ユーザーの
    # 追い質問 / 締め（議事録） / 終了 を待つ。False にすると従来どおり自動完走する。
    interactive: bool = True
    # 全ペルソナが共有する「資料・前提」テキスト（任意）。intake の Q&A と合成して Council に渡す。
    # materials は毎ターン全ペルソナの文脈へ再注入されるため、上限を設けて実LLMのトークン費暴走を防ぐ。
    materials: str = Field("", max_length=_MATERIALS_MAX)
    # 主訴確認（intake）の回答（任意）。空でも動く。資料の末尾に Q&A として連結する。
    intake: list[IntakeQA] = Field(default_factory=list)
    # Web 検索（調査役）を有効にするか。True なら seed 調査＋各ペルソナの「要調査:」を
    # 調査役が調べて全員に共有する。False（既定）では一切検索しない（後方互換・無料）。
    research: bool = False
    # 応答の長さプリセット（ユーザーはトークン数を意識しない）。simple/standard/deep を
    # max_tokens 上限＋発話スタイル指示にマップ。既定 standard（旧挙動だが上限を上げ切れ防止）。
    verbosity: Literal["brief", "standard", "deep"] = "standard"
    # 討論モード（エンジン・プリセット）の id。local 経路でのみ有効。サーバ側 allowlist で
    # (model, verbosity) に解決される（許可制）。未知/未指定なら verbosity をそのまま使う。
    preset: str | None = Field(default=None, max_length=40)
    # 発散→批判 の間に司会のブリッジ（叩く価値のある案を名指しして的を絞る）を挟むか。
    # A/B 検証で批判フェーズが明確に深まる（噛み合う）ことを確認したため既定 True（全討論で挟む）。
    # 明示 false で従来どおりにも戻せる。
    phase_bridge: bool = True
    # ② 問題再定義ゲート: 発散の前に各パネリストが議題を自分の視点で捉え直す1周を挟むか。
    # 司会1人のフレーミングでは吸収できない解釈ズレを多視点で炙り出す（コスト/時間は1周増える）。
    # 既定 false で従来同一。
    redefine: bool = False
    # クライアント定義のカスタムペルソナ（サーバ非保存・このセッション限定）。persona_ids から
    # これらの id を参照できる。件数上限で濫用・コスト暴走を防ぐ。
    custom_personas: list[CustomPersona] = Field(default_factory=list, max_length=12)


class IntakeRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    materials: str | None = Field(None, max_length=_MATERIALS_MAX)
    # 検証・デモ時に LLM を呼ばず定型質問を返す（二重課金防止）。
    mock: bool = False


def _compose_materials(materials: str, intake: list[IntakeQA]) -> str:
    """ユーザー materials と intake の Q&A を1つの「資料・前提」テキストに合成する。

    intake は回答済み（answer 非空）の項目だけを「【確認事項への回答】Q: …\nA: …」形式で
    連結する。materials が空で intake も空なら空文字（＝従来と完全同一の Council）。
    """
    parts: list[str] = []
    if materials and materials.strip():
        parts.append(materials.strip())
    qa_lines: list[str] = []
    for qa in intake:
        answer = (qa.answer or "").strip()
        if not answer:
            continue  # 未回答（スキップ）は載せない
        qa_lines.append(f"Q: {qa.question.strip()}\nA: {answer}")
    if qa_lines:
        parts.append("【確認事項への回答】\n" + "\n\n".join(qa_lines))
    composed = "\n\n".join(parts)
    # 防御的上限（materials の Field 上限 + intake 回答の余地）。超過時は明示して切り詰める。
    cap = _MATERIALS_MAX + 4000
    if len(composed) > cap:
        composed = composed[:cap] + "\n\n…（資料が長いため以降を省略）"
    return composed


@app.get("/health")
def health() -> dict:
    """稼働確認 + LLM 構成。API キーの値そのものは返さない（漏洩防止）。"""
    return {"status": "ok", **service.llm_status()}


@app.get("/personas")
def list_personas() -> list[dict]:
    return [service.persona_public(p) for p in service.load_registry()]


_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


@app.post("/intake")
def intake(
    req: IntakeRequest,
    request: Request,
    x_llm_provider: str | None = Header(default=None, alias="X-LLM-Provider"),
    x_llm_key: str | None = Header(default=None, alias="X-LLM-Key"),
    x_anthropic_key: str | None = Header(default=None, alias="X-Anthropic-Key"),
) -> dict:
    """討論前の主訴確認質問を 2〜4 個返す（回答は任意・スキップ可）。

    mock=True なら LLM を呼ばず定型質問。実呼び出しは BYOK のユーザーキー（X-LLM-Key、provider は
    X-LLM-Provider）を使う。X-Anthropic-Key は後方互換。レート制限あり。
    """
    _rate_check(request)
    # force_local 時は来訪者の provider 指定に関わらず内製（local）へ固定する。
    eff_provider = "local" if service.force_local() else x_llm_provider
    api_key = _resolve_api_key(req.mock, x_llm_key or x_anthropic_key, eff_provider)
    questions = service.generate_intake_questions(
        req.topic, req.materials or "", mock=req.mock, api_key=api_key, provider=eff_provider
    )
    return {"questions": questions}


@app.post("/sessions")
def create_session(
    req: SessionRequest,
    request: Request,
    x_llm_provider: str | None = Header(default=None, alias="X-LLM-Provider"),
    x_llm_key: str | None = Header(default=None, alias="X-LLM-Key"),
    x_anthropic_key: str | None = Header(default=None, alias="X-Anthropic-Key"),
) -> StreamingResponse:
    """討論をバックグラウンドで開始し、cursor 0 から tail する SSE を返す。

    プロデューサは接続が切れても完走するので、後から GET /sessions/{id}/stream で
    再接続して取りこぼしを再生できる。`start` イベントに session_id が載る。
    実 LLM は BYOK のユーザーキー（X-LLM-Key、provider は X-LLM-Provider）を使う。
    X-Anthropic-Key は後方互換。レート制限・同時上限あり。
    """
    _rate_check(request)
    # force_local 時は来訪者の provider 指定に関わらず内製（local）へ固定する。
    eff_provider = "local" if service.force_local() else x_llm_provider
    api_key = _resolve_api_key(req.mock, x_llm_key or x_anthropic_key, eff_provider)
    # 資料・前提 + intake の Q&A を合成（どちらも空なら "" ＝従来と完全同一の Council）。
    composed_materials = _compose_materials(req.materials, req.intake)
    try:
        council = service.build_council(
            req.persona_ids,
            rounds_per_phase=req.rounds_per_phase,
            red_team=req.red_team,
            red_team_id=req.red_team_id,
            mock=req.mock,
            api_key=api_key,
            provider=eff_provider,
            verbosity=req.verbosity,
            preset=req.preset,
            custom_personas=[cp.model_dump() for cp in req.custom_personas],
            materials=composed_materials,
            research=req.research,
            phase_bridge=req.phase_bridge,
            redefine=req.redefine,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"unknown persona ids: {exc.args[0]}")
    except ValueError as exc:  # パネリスト0人など
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        session = service.start_session(council, req.topic, interactive=req.interactive)
    except service.CapacityError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    # start イベント前にストリームが切れてもクライアントが session_id を得て再接続できるよう、
    # レスポンスヘッダにも session.id を載せる（sse.ts が X-Session-Id を読む契約）。
    return StreamingResponse(
        service.tail(session, cursor=0),
        media_type="text/event-stream",
        headers={**_SSE_HEADERS, "X-Session-Id": session.id},
    )


# GET と POST の両方を受ける。**cloudflared クイックトンネルは GET ストリームをバッファして
# 流さない**（キャッシュ対象扱い）が POST は素通しするため、フロントは再接続を POST で叩く。
@app.api_route("/sessions/{session_id}/stream", methods=["GET", "POST"])
def reconnect_session(session_id: str, cursor: int = 0) -> StreamingResponse:
    """再接続。events[cursor:] を再生 → ライブ tail。未知 id は 404。"""
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="unknown session id")
    return StreamingResponse(
        service.tail(session, cursor=cursor),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


# -- 追い質問（人間からの割り込み） -----------------------------------------
class FollowupRequest(BaseModel):
    # kind は Literal["followup"] のみ（他値は pydantic が 422 にする）。MVP は追い質問だけ。
    kind: Literal["followup"] = "followup"
    text: str = Field(..., min_length=1, max_length=2000)
    target: str | None = None


@app.post("/sessions/{session_id}/messages")
def post_session_message(
    session_id: str, req: FollowupRequest, request: Request
) -> JSONResponse:
    """追い質問を割り込ませる。成功は 202 {"queued": true}。

    本編フェーズ中（running）は各 Turn 直後に注入、floor-open 中（paused）は deepen 1周の
    トリガになる。未知 session は 404、running/paused でないセッションも 404。
    """
    # 追い質問は deepen ラウンドの実 LLM を起動するため、コスト/濫用抑止にレート制限を掛ける。
    _rate_check(request)
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="unknown session id")
    if session.status not in ("running", "paused"):
        raise HTTPException(status_code=404, detail="session is not running")
    # 非対話で仕上げ（summary/synthesis）に入った後は受け付けない。202 で受理したのに二度と
    # drain されず永久ドロップする窓を塞ぐ。対話（floor-open）では accepting は落とさない。
    if not session.accepting:
        raise HTTPException(status_code=409, detail="session is finalizing; no more followups")
    service.post_message(
        session,
        service.HumanMessage(kind=req.kind, text=req.text, target=req.target),
    )
    return JSONResponse(status_code=202, content={"queued": True})


@app.post("/sessions/{session_id}/close", status_code=202)
def close_session(session_id: str, request: Request) -> JSONResponse:
    """floor-open を締める（議事録 synthesis を生成）。body なし。成功は 202。

    HumanMessage(kind="close") を inbox に積む。プロデューサは synthesis を1回回し、
    締めた後も議場は開いたまま（再び floor-open）＝終了後の深掘りも可能。
    未知 session、running/paused でないセッションは 404。
    """
    # close は synthesis（議事録）の実 LLM ラウンドを起動するため、レート制限を掛ける。
    _rate_check(request)
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="unknown session id")
    if session.status not in ("running", "paused"):
        raise HTTPException(status_code=404, detail="session is not running")
    # cancel 済/終了処理中（accepting=False）は受理しても drain されず永久ドロップするので 409。
    if not session.accepting:
        raise HTTPException(status_code=409, detail="session is finalizing; cannot close")
    service.close_floor(session)
    return JSONResponse(status_code=202, content={"queued": True})


@app.post("/sessions/{session_id}/finish", status_code=202)
def finish_session(session_id: str) -> JSONResponse:
    """floor-open を終了する（done）。body なし。成功は 202。

    HumanMessage(kind="finish") を inbox に積む。プロデューサは floor-open ループを抜けて
    done で締める。未知 session、既に終了済み（done/error）のセッションは 404。
    """
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="unknown session id")
    if session.status in ("done", "error"):
        raise HTTPException(status_code=404, detail="session is already finished")
    # cancel 済/終了処理中（accepting=False）は受理しても drain されず永久ドロップするので 409。
    if not session.accepting:
        raise HTTPException(status_code=409, detail="session is finalizing; cannot finish")
    service.finish_floor(session)
    return JSONResponse(status_code=202, content={"queued": True})


@app.delete("/sessions/{session_id}", status_code=202)
def cancel_session(session_id: str) -> JSONResponse:
    """進行中の討論を停止する（協調キャンセル）。

    実 LLM の発注を次のターン前に打ち切ってコストを抑える。未知 session は 404。
    既に終了済みでも冪等に 202 を返す。
    """
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="unknown session id")
    service.cancel_session(session)
    return JSONResponse(status_code=202, content={"cancelled": True})


# -- 例外マッピング（ValueError / KeyError → HTTP） -------------------------
def _raise_value_error(exc: ValueError) -> NoReturn:
    """ValueError を HTTP に変換する（必ず raise する＝戻らない）。

    - "exists" を含む（id 衝突）→ 409
    - "read-only" を含む（builtin 編集）→ 409
    - それ以外（検証エラー・未知 persona など）→ 400
    """
    msg = str(exc)
    if "exists" in msg or "read-only" in msg:
        raise HTTPException(status_code=409, detail=msg)
    raise HTTPException(status_code=400, detail=msg)


# -- プリセット CRUD --------------------------------------------------------
class PresetUpsert(BaseModel):
    # id は書込先パスに使うため charset を制限（パストラバーサル防止・入口で 422）。
    id: str = Field(..., min_length=1, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1)
    description: str | None = None
    persona_ids: list[str] = Field(..., min_length=1)
    rounds_per_phase: int = Field(1, ge=1, le=5)
    red_team: bool = True
    red_team_id: str | None = None


@app.get("/presets")
def list_presets() -> list[dict]:
    return service.load_presets()


@app.get("/presets/{preset_id}")
def get_preset(preset_id: str) -> dict:
    try:
        return service.get_preset(preset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown preset id")


@app.post("/presets", status_code=201)
def create_preset(req: PresetUpsert) -> dict:
    _assert_writable()
    try:
        return service.save_preset(req.model_dump(), create=True)
    except ValueError as exc:
        _raise_value_error(exc)


@app.put("/presets/{preset_id}")
def update_preset(preset_id: str, req: PresetUpsert) -> dict:
    _assert_writable()
    data = req.model_dump()
    data["id"] = preset_id  # パスの id を正とする
    try:
        return service.save_preset(data, create=False)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown preset id")
    except ValueError as exc:
        _raise_value_error(exc)


@app.delete("/presets/{preset_id}", status_code=204)
def remove_preset(preset_id: str) -> None:
    _assert_writable()
    try:
        service.delete_preset(preset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown preset id")
    except ValueError as exc:
        _raise_value_error(exc)


# -- ペルソナ CRUD ----------------------------------------------------------
class PersonaRelationshipIn(BaseModel):
    # 因縁（対立/盟友/師弟）の1件。to は相手の persona id（charset 制限でパストラバーサル/不整合防止）。
    to: str = Field(..., min_length=1, pattern=r"^[a-z0-9_-]+$")
    type: Literal["rival", "ally", "mentor", "student"]
    note: str | None = None


class PersonaUpsert(BaseModel):
    # id は書込先パスに使うため charset を制限（パストラバーサル防止・入口で 422）。
    id: str = Field(..., min_length=1, pattern=r"^[a-z0-9_-]+$")
    display_name: str = Field(..., min_length=1)
    system_prompt: str = Field(..., min_length=1)
    # category は 6 種のみ（不正は入口で 422）。
    category: Literal[
        "facilitation", "chair", "scribe", "thinking", "founders", "philosophers"
    ] = "thinking"
    # レガシー絵文字フィールド。UI は使わず、既定は None（YAML に書き出さない）。
    avatar: str | None = None
    model: str | None = None
    temperature: float | None = None
    tags: list[str] = Field(default_factory=list)
    speaks: bool = True
    accent: str | None = None
    # ピッカー表示用の一行説明。relationships と同じ罠: 受け口に無いと extra='ignore' で黙って捨てられ、
    # save_persona は全置換のため編集保存で既存 YAML の description が消える。明示が必須。None なら
    # _write_persona_file が書き出さない＝空のまま（クリアも兼ねる）。公開サーバ濫用防止に長さ上限。
    description: str | None = Field(default=None, max_length=200)
    # 「詳細」で開く詳しい説明（偉人の背景＋持ち味 等）。description と同じく明示しないと
    # extra='ignore' で捨てられ、全置換 save で編集時に消える。None なら書き出さない。
    detail: str | None = Field(default=None, max_length=600)
    # 因縁（relationships）。受け口に無いと extra='ignore' で捨てられ編集保存で消えるため明示。
    # model_dump で dict 化され save_persona→persona_from_dict→YAML 保存まで通る（service 側は対応済み）。
    relationships: list[PersonaRelationshipIn] = Field(default_factory=list)


@app.get("/personas/{persona_id}")
def get_persona(persona_id: str) -> dict:
    # 共有公開（readonly）では編集 UI が使えない（canManage=false）ため、system_prompt を含む
    # 詳細は返さず persona_public 相当（system_prompt 無し）に絞る（無認証での露出防止）。
    if service.readonly_mode():
        for p in service.load_registry():
            if p.id == persona_id:
                return service.persona_public(p)
        raise HTTPException(status_code=404, detail="unknown persona id")
    try:
        return service.get_persona_detail(persona_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown persona id")


@app.post("/personas", status_code=201)
def create_persona(req: PersonaUpsert) -> dict:
    _assert_writable()
    try:
        persona = service.save_persona(req.model_dump(), expect_id=None)
    except ValueError as exc:
        _raise_value_error(exc)
    return service.persona_detail(persona)


@app.put("/personas/{persona_id}")
def update_persona(persona_id: str, req: PersonaUpsert) -> dict:
    _assert_writable()
    try:
        persona = service.save_persona(req.model_dump(), expect_id=persona_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown persona id")
    except ValueError as exc:
        _raise_value_error(exc)
    return service.persona_detail(persona)


@app.delete("/personas/{persona_id}", status_code=204)
def remove_persona(persona_id: str) -> None:
    _assert_writable()
    try:
        service.delete_persona(persona_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown persona id")


# -- フロント静的配信（同一オリジン） ---------------------------------------
# web/out（Next.js の static export）があれば "/" にマウントして SPA を配信する。
# **全 API ルートの後に置く**ので /sessions 等が優先され、それ以外（/ や /_next/*）は
# 静的ファイルを返す。out が無い環境（ローカル開発・テスト）ではマウントせず従来どおり。
# これにより uvicorn 1プロセスで API とフロントを同一オリジン配信でき、CORS 不要・低RAM。
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "web" / "out"
if _FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
