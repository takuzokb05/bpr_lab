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
    LLMClient,
    MockLLMClient,
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


# -- LLM クライアント -------------------------------------------------------
def make_client(mock: bool = False) -> LLMClient:
    """mock 指定、または API キー未設定なら MockLLMClient にフォールバック。

    mock=True はキーの有無に関わらず必ず Mock を返す（検証・デモ時の二重課金防止）。
    """
    if mock or not os.environ.get("ANTHROPIC_API_KEY"):
        return MockLLMClient()
    return AnthropicClient()


def llm_status() -> dict:
    """LLM 構成の公開ステータス（純関数）。API キーの値そのものは絶対に返さない。

    api_key_set=True かつ非 mock 起動なら Anthropic を実呼び出しする、という前提を
    フロントに伝えるための情報。キー文字列は含めない（漏洩防止）。
    """
    api_key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return {"llm": "anthropic" if api_key_set else "mock", "api_key_set": api_key_set}


# -- Web 検索（調査役） -----------------------------------------------------
#
# 凍結契約: 検索するのは「調査役」だけ。各ペルソナは検索しない＝重複ゼロ。結果は
# 「調査」話者のターンとして討論に乗せ、全員が共有する（新 SSE イベント型は増やさない）。
# mock / キー未設定では web_research が canned を返す（無料・テスト可）。real のみ課金。

# 「要調査:」マーカーを行頭から拾う正規表現（半角/全角コロンの両方を許容）。
_RESEARCH_QUERY_RE = re.compile(r"^\s*要調査\s*[:：]\s*(.+?)\s*$")

# Web 検索の合計回数上限（seed 1 + 派生 5 ＝ 暴走防止）。cap 到達後は無視（ログのみ）。
_RESEARCH_CAP = 6


def run_research(client: LLMClient, query: str) -> str:
    """調査役による web 検索の薄いラッパ。client.web_research(query) をそのまま返す。

    mock / キー未設定なら canned（無料）、real のみ課金。例外は web_research 側で
    握って「（調査に失敗: …）」を返すので、ここでは討論を止めない。
    """
    return client.web_research(query)


def _extract_research_queries(text: str) -> list[str]:
    """発言本文から「要調査: <問い>」（全角コロンも可）の問いを行単位で抽出する。

    行頭の「要調査:」「要調査：」に続く文字列を取り出し trim。空は除く。
    research=False なら build_context が指示を出さない＝そもそもマーカーは現れない。
    """
    out: list[str] = []
    for raw in (text or "").splitlines():
        m = _RESEARCH_QUERY_RE.match(raw)
        if not m:
            continue
        q = m.group(1).strip()
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
        materials=materials,
        research=research,
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
    topic: str, materials: str = "", *, mock: bool = False
) -> list[str]:
    """討論前の主訴確認質問を 2〜4 個返す。

    mock=True または API キー未設定なら LLM を呼ばず決定的な定型質問を返す（検証・コスト
    対策）。実呼び出し時は make_client 経由で LLM に依頼し、_parse_intake_questions で
    堅牢にパースする。LLM が 2 個未満しか返さなかった等で取れなければ定型にフォールバック。
    """
    client = make_client(mock)
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
                brief = run_research(council.client, query)
                rid = next(ids)
                rt = council.emit_research_turn(transcript, brief, emit=emit, turn_id=rid)
                _append(session, "turn_end", {"turn_id": rt.turn_id})
                research_seen.add(norm)
                research_state["count"] += 1

        # Phase A: seed 調査（research=True のときだけ）。deliberate 開始前に topic を1回調べ、
        # researcher ターンとして全員の議論の土台に乗せる。seed を seen に登録し、カウンタ+1。
        if council.research:
            seed = session.topic
            seed_norm = seed.lower().strip()
            if seed_norm:
                seed_brief = run_research(council.client, seed)
                seed_rid = next(ids)
                seed_turn = council.emit_research_turn(
                    transcript, seed_brief, emit=emit, turn_id=seed_rid
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


def tail(session: Session, cursor: int = 0) -> Iterator[str]:
    """events[cursor:] を再生 → ライブ tail を SSE 文字列で yield する（再接続対応）。

    各 data に seq と ts を載せる（seq=再接続カーソル用、ts=採番時刻で再接続再生でも不変）。
    終端は status が done/error のときだけ。running/paused（floor-open 入力待機）では
    接続を保ち cond.wait で待ち続ける（paused で SSE を閉じない）。
    """
    while True:
        with session.cond:
            while cursor >= len(session.events) and session.status in _ALIVE_STATUSES:
                session.cond.wait()
            new = session.events[cursor:]
            cursor += len(new)
            finished = (
                session.status in _FINAL_STATUSES and cursor >= len(session.events)
            )
        for ev in new:
            yield sse(ev["event"], {**ev["data"], "seq": ev["seq"], "ts": ev["ts"]})
        if finished:
            return


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
