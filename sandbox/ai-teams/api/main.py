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
    mock: bool = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/personas")
def list_personas() -> list[dict]:
    return [service.persona_public(p) for p in service.load_registry()]


@app.post("/sessions")
def create_session(req: SessionRequest) -> StreamingResponse:
    try:
        council = service.build_council(
            req.persona_ids, rounds_per_phase=req.rounds_per_phase, mock=req.mock
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"unknown persona ids: {exc.args[0]}")
    except ValueError as exc:  # パネリスト0人など
        raise HTTPException(status_code=400, detail=str(exc))

    return StreamingResponse(
        service.stream_council(council, req.topic),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
