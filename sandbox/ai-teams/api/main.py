"""FastAPI アプリ本体（ルーティングのみ薄く）。

起動: uvicorn api.main:app --reload --port 8000   （sandbox/ai-teams で実行）
本番 LLM を使うには環境変数 ANTHROPIC_API_KEY を設定。未設定ならモック応答で動く。
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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


class SessionRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    persona_ids: list[str] = Field(..., min_length=1)
    rounds_per_phase: int = Field(1, ge=1, le=5)
    red_team: bool = True
    red_team_id: str | None = None
    mock: bool = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/personas")
def list_personas() -> list[dict]:
    return [service.persona_public(p) for p in service.load_registry()]


_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


@app.post("/sessions")
def create_session(req: SessionRequest) -> StreamingResponse:
    """討論をバックグラウンドで開始し、cursor 0 から tail する SSE を返す。

    プロデューサは接続が切れても完走するので、後から GET /sessions/{id}/stream で
    再接続して取りこぼしを再生できる。`start` イベントに session_id が載る。
    """
    try:
        council = service.build_council(
            req.persona_ids,
            rounds_per_phase=req.rounds_per_phase,
            red_team=req.red_team,
            red_team_id=req.red_team_id,
            mock=req.mock,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"unknown persona ids: {exc.args[0]}")
    except ValueError as exc:  # パネリスト0人など
        raise HTTPException(status_code=400, detail=str(exc))

    session = service.start_session(council, req.topic)
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
