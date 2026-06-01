"""FastAPI アプリ本体（ルーティングのみ薄く）。

起動: uvicorn api.main:app --reload --port 8000   （sandbox/ai-teams で実行）
本番 LLM を使うには環境変数 ANTHROPIC_API_KEY を設定。未設定ならモック応答で動く。
"""

from __future__ import annotations

import os
from typing import Literal, NoReturn

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from . import service

app = FastAPI(title="AI Teams API", version="3.0.0")

# 開発中の Next.js フロント（localhost:3000）からの呼び出しを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class IntakeQA(BaseModel):
    """主訴確認の 1 問 1 答（質問とユーザー回答のペア）。回答は任意・空可。"""

    question: str = Field(..., min_length=1)
    answer: str = ""


# 「資料・前提」テキストの上限（文字）。毎ターン再注入されるため過大プロンプトを入口で弾く。
_MATERIALS_MAX = 20000


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
def intake(req: IntakeRequest) -> dict:
    """討論前の主訴確認質問を 2〜4 個返す（回答は任意・スキップ可）。

    mock=True または API キー未設定なら LLM を呼ばず決定的な定型質問を返す（二重課金防止）。
    """
    questions = service.generate_intake_questions(
        req.topic, req.materials or "", mock=req.mock
    )
    return {"questions": questions}


@app.post("/sessions")
def create_session(req: SessionRequest) -> StreamingResponse:
    """討論をバックグラウンドで開始し、cursor 0 から tail する SSE を返す。

    プロデューサは接続が切れても完走するので、後から GET /sessions/{id}/stream で
    再接続して取りこぼしを再生できる。`start` イベントに session_id が載る。
    """
    # 資料・前提 + intake の Q&A を合成（どちらも空なら "" ＝従来と完全同一の Council）。
    composed_materials = _compose_materials(req.materials, req.intake)
    try:
        council = service.build_council(
            req.persona_ids,
            rounds_per_phase=req.rounds_per_phase,
            red_team=req.red_team,
            red_team_id=req.red_team_id,
            mock=req.mock,
            materials=composed_materials,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"unknown persona ids: {exc.args[0]}")
    except ValueError as exc:  # パネリスト0人など
        raise HTTPException(status_code=400, detail=str(exc))

    session = service.start_session(council, req.topic, interactive=req.interactive)
    return StreamingResponse(
        service.tail(session, cursor=0),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@app.get("/sessions/{session_id}/stream")
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
def post_session_message(session_id: str, req: FollowupRequest) -> JSONResponse:
    """追い質問を割り込ませる。成功は 202 {"queued": true}。

    本編フェーズ中（running）は各 Turn 直後に注入、floor-open 中（paused）は deepen 1周の
    トリガになる。未知 session は 404、running/paused でないセッションも 404。
    """
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
def close_session(session_id: str) -> JSONResponse:
    """floor-open を締める（議事録 synthesis を生成）。body なし。成功は 202。

    HumanMessage(kind="close") を inbox に積む。プロデューサは synthesis を1回回し、
    締めた後も議場は開いたまま（再び floor-open）＝終了後の深掘りも可能。
    未知 session、running/paused でないセッションは 404。
    """
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="unknown session id")
    if session.status not in ("running", "paused"):
        raise HTTPException(status_code=404, detail="session is not running")
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
    try:
        return service.save_preset(req.model_dump(), create=True)
    except ValueError as exc:
        _raise_value_error(exc)


@app.put("/presets/{preset_id}")
def update_preset(preset_id: str, req: PresetUpsert) -> dict:
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
    try:
        service.delete_preset(preset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown preset id")
    except ValueError as exc:
        _raise_value_error(exc)


# -- ペルソナ CRUD ----------------------------------------------------------
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


@app.get("/personas/{persona_id}")
def get_persona(persona_id: str) -> dict:
    try:
        return service.get_persona_detail(persona_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown persona id")


@app.post("/personas", status_code=201)
def create_persona(req: PersonaUpsert) -> dict:
    try:
        persona = service.save_persona(req.model_dump(), expect_id=None)
    except ValueError as exc:
        _raise_value_error(exc)
    return service.persona_detail(persona)


@app.put("/personas/{persona_id}")
def update_persona(persona_id: str, req: PersonaUpsert) -> dict:
    try:
        persona = service.save_persona(req.model_dump(), expect_id=persona_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown persona id")
    except ValueError as exc:
        _raise_value_error(exc)
    return service.persona_detail(persona)


@app.delete("/personas/{persona_id}", status_code=204)
def remove_persona(persona_id: str) -> None:
    try:
        service.delete_persona(persona_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown persona id")
