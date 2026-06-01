"""API のドメインロジック（FastAPI 非依存・テスト可能）。

ここには Web フレームワークを import しない。SSE の文字列生成・Council の組み立て・
ペルソナの公開用シリアライズだけを置き、main.py（FastAPI）から薄く呼ぶ。
"""

from __future__ import annotations

import json
import os
import queue
import threading
import uuid
from dataclasses import dataclass, field
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
    red_team: bool = True,
    red_team_id: str | None = None,
    mock: bool = False,
) -> Council:
    """指定 id のペルソナで Council を作る。未知 id は KeyError。"""
    registry = {p.id: p for p in load_registry()}
    missing = [pid for pid in persona_ids if pid not in registry]
    if missing:
        raise KeyError(missing)
    personas = [registry[pid] for pid in persona_ids]
    return Council(
        personas,
        make_client(mock),
        rounds_per_phase=rounds_per_phase,
        red_team=red_team,
        red_team_id=red_team_id,
    )


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


@dataclass
class HumanMessage:
    """人間からの割り込み入力。MVP は followup のみ。将来 intervention/rewind を kind で追加。"""

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
    status: str = "running"  # running | done | error
    thread: threading.Thread | None = None


SESSIONS: dict[str, Session] = {}
_REGISTRY_LOCK = threading.Lock()


def _append(session: Session, event: str, data: dict) -> None:
    """seq を採番してイベントを追加し、tail 中の読み手全員に通知する。"""
    with session.cond:
        seq = len(session.events)
        session.events.append({"seq": seq, "event": event, "data": data})
        session.cond.notify_all()


def _produce(session: Session) -> None:
    """バックグラウンドで council.run(emit=…) を完走させ、イベントを溜める。

    接続の有無に関わらず最後まで走る（再接続のため）。orchestrator は turn_start/delta を
    emit するので、Turn 確定後に turn_end を、全体の前後に start/done を付ける（設計 v2）。
    """

    def emit(ev: dict) -> None:
        etype = ev["type"]
        data = {k: v for k, v in ev.items() if k != "type"}
        _append(session, etype, data)

    try:
        _append(session, "start", {"topic": session.topic, "session_id": session.id})
        for turn in session.council.run(session.topic, emit=emit):
            _append(session, "turn_end", {"turn_id": turn.turn_id})
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
    """件数上限を超えたら、終了済み(running でない)セッションを古い順に破棄する。"""
    if len(SESSIONS) <= MAX_SESSIONS:
        return
    for sid, s in list(SESSIONS.items()):  # dict は挿入順 = 古い順
        if len(SESSIONS) <= MAX_SESSIONS:
            break
        if s.status != "running":
            del SESSIONS[sid]


def start_session(council: Council, topic: str) -> Session:
    """Session を生成・登録し、プロデューサスレッドを起動して返す。"""
    session = Session(id=uuid.uuid4().hex, topic=topic, council=council)
    with _REGISTRY_LOCK:
        _gc_locked()
        SESSIONS[session.id] = session
    thread = threading.Thread(target=_produce, args=(session,), daemon=True)
    session.thread = thread
    thread.start()
    return session


def get_session(session_id: str) -> Session | None:
    with _REGISTRY_LOCK:
        return SESSIONS.get(session_id)


def tail(session: Session, cursor: int = 0) -> Iterator[str]:
    """events[cursor:] を再生 → ライブ tail を SSE 文字列で yield する（再接続対応）。

    各 data に seq を載せる（クライアントの再接続カーソル用）。プロデューサが done/error で
    終端し、それまでに溜まったイベントを送り切ったら return する（ハングしない）。
    """
    while True:
        with session.cond:
            while cursor >= len(session.events) and session.status == "running":
                session.cond.wait()
            new = session.events[cursor:]
            cursor += len(new)
            finished = session.status != "running" and cursor >= len(session.events)
        for ev in new:
            yield sse(ev["event"], {**ev["data"], "seq": ev["seq"]})
        if finished:
            return
