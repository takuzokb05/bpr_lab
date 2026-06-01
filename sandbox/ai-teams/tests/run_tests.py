"""core エンジンの検証（pytest 不要・stdlib のみ・API キー不要）。

実行: python3 tests/run_tests.py
v2 の2大バグ（人格混線 / 沈黙）が構造的に解けていることをモックで証明する。
"""

import sys
from pathlib import Path

# core/ を import できるように親ディレクトリを通す
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import Council, MockLLMClient, Persona, Turn, build_context  # noqa: E402
from api import service  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ok  - {msg}")
    else:
        print(f"  FAIL- {msg}")
        _failures.append(msg)


def make(id_, cat="thinking", model=None, speaks=True):
    return Persona(
        id=id_,
        display_name=id_.upper(),
        system_prompt=f"あなたは {id_} です。",
        category=cat,
        model=model,
        speaks=speaks,
    )


# ---------------------------------------------------------------------------
def test_context_isolation():
    """バグ①対策: 自分=assistant / 他者=【名前】付き user になっているか。"""
    print("[test] context isolation (人格混線対策)")
    a, b, c = make("a"), make("b"), make("c")
    transcript = [
        Turn("a", "A", "a-said", "発散", 0),
        Turn("b", "B", "b-said", "発散", 0),
        Turn("c", "C", "c-said", "発散", 0),
    ]
    system, messages = build_context(transcript=transcript, active=b, topic="T")

    check(system == b.system_prompt, "system は active(B) のプロンプト")
    check(messages[0]["role"] == "user", "先頭メッセージは user（Anthropic 要件）")
    check(messages[-1]["role"] == "user", "末尾メッセージは user（指名ナッジ）")

    # B から見た役割割り当て
    roles = [m["role"] for m in messages]
    # events: topic(u), A(u), B(a), C(u), nudge(u) → merge → [u, a, u]
    check(roles == ["user", "assistant", "user"], f"role が交互に正規化される: {roles}")

    assistant_msgs = [m["content"] for m in messages if m["role"] == "assistant"]
    check(assistant_msgs == ["b-said"], "B 自身の発言だけが assistant（ラベル無し）")

    all_user_text = "\n".join(m["content"] for m in messages if m["role"] == "user")
    check("【A】" in all_user_text, "他者 A は【A】付きで user 側に出る")
    check("【C】" in all_user_text, "他者 C は【C】付きで user 側に出る")
    check("【B】" not in all_user_text, "B 自身は他者ラベル化されない（混線源を断つ）")
    check("a-said" in all_user_text and "c-said" in all_user_text, "他者の発言内容は user 側")
    check("b-said" not in all_user_text, "B 自身の発言は user 側に混入しない")


# ---------------------------------------------------------------------------
def test_no_silence_and_round_robin():
    """バグ②対策: 全パネリストが各ラウンドで必ず1回発言し、書記は喋らない。"""
    print("[test] no-silence & round-robin (沈黙対策)")
    personas = [
        make("mod", cat="facilitation"),
        make("logic"),
        make("idea"),
        make("empathy"),
        make("scribe", cat="scribe", speaks=False),
        make("chair", cat="chair"),
    ]
    client = MockLLMClient()
    # 1フェーズ×2ラウンドだけに絞って検証
    council = Council(
        personas,
        client,
        phases=[("発散", "d", True)],
        rounds_per_phase=2,
    )
    turns = list(council.run("議題X"))

    speakers = [t.speaker_id for t in turns]
    panel = {"logic", "idea", "empathy"}

    check(speakers[0] == "mod", "司会がオープニングを担当")
    check(speakers[-1] == "chair", "議長が最後に統合（chairman パターン）")
    check("scribe" not in speakers, "書記(speaks=False)は一度も発言しない")

    # 発散フェーズの発言だけ取り出す
    diverge = [t for t in turns if t.phase == "発散"]
    r0 = {t.speaker_id for t in diverge if t.round == 0}
    r1 = {t.speaker_id for t in diverge if t.round == 1}
    check(r0 == panel, f"ラウンド0で全パネリストが発言（沈黙ゼロ）: {r0}")
    check(r1 == panel, f"ラウンド1で全パネリストが発言（沈黙ゼロ）: {r1}")

    # ラウンドロビンは開始位置を回す
    order_r0 = [t.speaker_id for t in diverge if t.round == 0]
    order_r1 = [t.speaker_id for t in diverge if t.round == 1]
    check(order_r0[0] != order_r1[0], f"ラウンドごとに口火役が回る: {order_r0} -> {order_r1}")


# ---------------------------------------------------------------------------
def test_model_override():
    """collapse 対策: persona.model がエンジン既定より優先されること。"""
    print("[test] per-persona model override (均質化対策の土台)")
    personas = [
        make("mod", cat="facilitation"),
        make("logic", model="claude-opus-4-8"),
        make("idea"),  # 既定モデル
    ]
    client = MockLLMClient()
    council = Council(
        personas, client, default_model="claude-sonnet-4-6",
        phases=[("発散", "d", True)], rounds_per_phase=1,
    )
    list(council.run("議題Y"))

    used = {}
    # calls の system からどのペルソナの呼び出しかを判定
    for call in client.calls:
        if "logic" in call["system"]:
            used.setdefault("logic", call["model"])
        elif "idea" in call["system"]:
            used.setdefault("idea", call["model"])
    check(used.get("logic") == "claude-opus-4-8", "model 指定ペルソナは上書きモデルを使う")
    check(used.get("idea") == "claude-sonnet-4-6", "未指定ペルソナは既定モデルを使う")


# ---------------------------------------------------------------------------
def test_persona_public():
    """API 公開表現は system_prompt を出さず、accent/monogram を含む。"""
    print("[test] persona_public serialization")
    p = Persona(
        id="logic", display_name="論理担当", system_prompt="秘密のプロンプト",
        category="thinking",
    )
    pub = service.persona_public(p)
    check("system_prompt" not in pub, "system_prompt は公開されない")
    check(pub["accent"] == "#5B7C8A", f"thinking のカテゴリ色が入る: {pub['accent']}")
    check(pub["monogram"] == "論", f"モノグラムは先頭1文字: {pub['monogram']}")
    jobs = Persona(id="j", display_name="Steve Jobs", system_prompt="x", category="founders")
    check(service.persona_public(jobs)["monogram"] == "SJ", "ラテン2語名はイニシャル2文字")


def test_sse_stream():
    """SSE: start → turn* → done の順で、ワイヤ形式・JSON が正しいか。"""
    print("[test] SSE stream (途中経過の逐次配信)")
    import json

    council = service.build_council(
        ["moderator", "logic", "idea", "empathy", "chair"],
        rounds_per_phase=1,
        mock=True,
    )
    events = list(service.stream_council(council, "議題Z"))

    # ワイヤ形式
    check(all(e.startswith("event: ") for e in events), "各イベントが 'event: ' で始まる")
    check(all(e.endswith("\n\n") for e in events), "各イベントが空行で終わる（SSE区切り）")

    kinds = [e.split("\n", 1)[0].removeprefix("event: ") for e in events]
    check(kinds[0] == "start", "最初は start")
    check(kinds[-1] == "done", "最後は done")
    check("error" not in kinds, "error イベントは出ない")

    turns = [e for e, k in zip(events, kinds) if k == "turn"]
    # opening1 + (3人×3フェーズ=9) + summary1 + synthesis1 = 12
    check(len(turns) == 12, f"turn 数が想定どおり: {len(turns)}")

    # data 行の JSON 検証（最初の turn）
    data_line = [ln for ln in turns[0].splitlines() if ln.startswith("data: ")][0]
    payload = json.loads(data_line.removeprefix("data: "))
    for key in ("speaker_id", "speaker_name", "content", "phase", "round"):
        check(key in payload, f"turn payload に {key} が含まれる")
    check(payload["speaker_id"] == "moderator", "先頭 turn は司会")


# ---------------------------------------------------------------------------
def test_red_team():
    """Red Team 保証: 指名パネリストの発言時に反対役の特命が注入される。"""
    print("[test] red team guarantee (同調バイアス対策)")
    from core.orchestrator import RED_TEAM_DIRECTIVE

    personas = [
        make("mod", cat="facilitation"),
        make("logic"),
        make("idea"),
        make("chair", cat="chair"),
    ]
    client = MockLLMClient()
    # red_team を logic に明示
    council = Council(
        personas, client, red_team=True, red_team_id="logic",
        phases=[("発散", "d", True)], rounds_per_phase=1,
    )
    check(council.red_team_id == "logic", "red_team_id が設定される")
    list(council.run("議題R"))

    # logic の呼び出しメッセージに Red Team 特命が入り、idea には入らない
    redteam_seen = False
    other_clean = True
    marker = RED_TEAM_DIRECTIVE[:20]
    for call in client.calls:
        joined = "\n".join(m["content"] for m in call["messages"])
        if "logic" in call["system"]:
            if marker in joined:
                redteam_seen = True
        elif "idea" in call["system"]:
            if marker in joined:
                other_clean = False
    check(redteam_seen, "Red Team 指名者(logic)の発言に反対役の特命が注入される")
    check(other_clean, "非指名者(idea)には反対役の特命が入らない")

    # パネリスト2人なら既定で先頭が Red Team
    duo = Council(
        [make("mod", cat="facilitation"), make("aaa"), make("bbb"), make("chair", cat="chair")],
        MockLLMClient(), red_team=True,
        phases=[("発散", "d", True)], rounds_per_phase=1,
    )
    check(duo.red_team_id == "aaa", "パネリスト2人以上なら既定で先頭が Red Team")
    # パネリスト1人なら Red Team は立てない（全員反対では討論にならない）
    solo1 = Council(
        [make("mod", cat="facilitation"), make("only"), make("chair", cat="chair")],
        MockLLMClient(), red_team=True,
        phases=[("発散", "d", True)], rounds_per_phase=1,
    )
    check(solo1.red_team_id is None, "パネリスト1人なら Red Team は立てない")


def test_exec_summary():
    """エグゼクティブサマリ: synthesis の前に summary フェーズが1回出る。"""
    print("[test] exec summary 3-line")
    council = service.build_council(
        ["moderator", "logic", "idea", "chair"],
        rounds_per_phase=1, mock=True,
    )
    turns = list(council.run("議題S"))
    phases = [t.phase for t in turns]
    check("summary" in phases, "summary フェーズが存在する")
    check(
        phases.index("summary") < phases.index("synthesis"),
        "summary は synthesis より前に出る（UI上段用）",
    )
    summary_turn = next(t for t in turns if t.phase == "summary")
    check(summary_turn.speaker_id == "chair", "サマリは議長が書く")


def test_streaming():
    """core ストリーミング: emit で turn_start→delta*→turn_end、delta連結＝content。"""
    print("[test] core streaming (emit: turn_start/delta/turn_end)")

    # 1. llm: generate_stream の連結が generate と一致
    c = MockLLMClient()
    full = c.generate(system="s", messages=[{"role": "user", "content": "x"}], model="m")
    c2 = MockLLMClient()
    chunks = list(
        c2.generate_stream(system="s", messages=[{"role": "user", "content": "x"}], model="m")
    )
    check(len(chunks) >= 1, "generate_stream は1個以上のチャンクを返す")
    check("".join(chunks) == full, "delta 連結が generate と一致")
    check(len(c2.calls) == 1, "generate_stream も calls に1回記録する（generate と同じ）")

    # 2. orchestrator: emit 経路で turn_start/delta を捕捉、消費側が turn_end を出す
    personas = [
        make("mod", cat="facilitation"),
        make("logic"),
        make("idea"),
        make("chair", cat="chair"),
    ]
    council = Council(
        personas, MockLLMClient(), phases=[("発散", "d", True)], rounds_per_phase=1
    )
    events: list[dict] = []
    turns: list[Turn] = []
    for turn in council.run("議題T", emit=events.append):
        # API 層を模して、Turn 確定後に turn_end を出す（設計 v2）
        events.append({"type": "turn_end", "turn_id": turn.turn_id})
        turns.append(turn)

    check(events[0]["type"] == "turn_start", f"最初の emit は turn_start: {events[0]['type']}")

    start_ids = [e["turn_id"] for e in events if e["type"] == "turn_start"]
    check(
        start_ids == list(range(len(start_ids))),
        f"turn_id が 0 から単調増加: {start_ids}",
    )
    check(
        [t.turn_id for t in turns] == start_ids,
        "yield された Turn の turn_id が turn_start と一致",
    )

    # ターンごとに turn_start … delta* … turn_end の順序、delta連結＝content
    for turn in turns:
        evs = [e["type"] for e in events if e.get("turn_id") == turn.turn_id]
        check(
            evs[0] == "turn_start" and evs[-1] == "turn_end",
            f"turn {turn.turn_id}: turn_start で始まり turn_end で終わる",
        )
        check(
            all(t == "delta" for t in evs[1:-1]),
            f"turn {turn.turn_id}: 中間イベントは delta のみ",
        )
        deltas = [
            e["text"]
            for e in events
            if e["type"] == "delta" and e["turn_id"] == turn.turn_id
        ]
        check("".join(deltas) == turn.content, f"turn {turn.turn_id}: delta 連結 = content")

    # 3. emit=None（後方互換）は従来どおり Turn だけを yield し、内容は決定的に一致
    council_none = Council(
        [
            make("mod", cat="facilitation"),
            make("logic"),
            make("idea"),
            make("chair", cat="chair"),
        ],
        MockLLMClient(),
        phases=[("発散", "d", True)],
        rounds_per_phase=1,
    )
    turns_none = list(council_none.run("議題T"))
    check(len(turns_none) == len(turns), "emit 有無で turn 数が一致")
    check(
        [t.content for t in turns_none] == [t.content for t in turns],
        "emit 有無で発言内容が一致（決定的・経路非依存）",
    )
    check(
        all(t.turn_id is not None for t in turns_none),
        "emit=None でも turn_id は採番される",
    )


def _parse_sse(wire: list[str]) -> list[dict]:
    """SSE 文字列の列を {event, data} のリストにパースする（テスト用）。"""
    import json

    out = []
    for chunk in wire:
        lines = chunk.strip().splitlines()
        event = next(l.removeprefix("event: ") for l in lines if l.startswith("event: "))
        data = next(l.removeprefix("data: ") for l in lines if l.startswith("data: "))
        out.append({"event": event, "data": json.loads(data)})
    return out


def test_session_transport():
    """Step 2: バックグラウンド実行＋seqバッファ＋cursor 再接続。"""
    print("[test] session transport (background run / seq / reconnect)")

    council = service.build_council(
        ["moderator", "logic", "idea", "chair"], rounds_per_phase=1, mock=True
    )
    session = service.start_session(council, "議題BG")

    # 1. cursor 0 から tail（プロデューサ完走まで読み切る）
    wire = list(service.tail(session, cursor=0))
    session.thread.join(timeout=5)
    check(session.status == "done", f"プロデューサ完走で status=done: {session.status}")

    parsed = _parse_sse(wire)
    kinds = [e["event"] for e in parsed]
    check(kinds[0] == "start", "最初は start")
    check(kinds[-1] == "done", "最後は done")
    check(parsed[0]["data"]["session_id"] == session.id, "start に session_id が載る")
    check("error" not in kinds, "error は出ない")

    # seq は 0 から連番・単調増加
    seqs = [e["data"]["seq"] for e in parsed]
    check(seqs == list(range(len(seqs))), f"seq が 0 から連番: {seqs[:5]}...")

    # turn_start→delta*→turn_end が含まれる（Step 1 のイベント列が乗っている）
    check("turn_start" in kinds and "delta" in kinds and "turn_end" in kinds,
          "turn_start/delta/turn_end がワイヤに乗る")

    # 2. 再接続: 終了後に events が TTL で残っている間、cursor から再生できる
    cut = 3
    again = _parse_sse(list(service.tail(session, cursor=cut)))
    check([e["data"]["seq"] for e in again] == list(range(cut, len(seqs))),
          f"cursor={cut} で events[cursor:] を再生（バックログ再生）")
    check(again[0]["data"]["seq"] == cut, "再接続は指定 cursor から始まる")

    # 3. get_session / 未知 id
    check(service.get_session(session.id) is session, "get_session で取得できる")
    check(service.get_session("nope") is None, "未知 id は None（API では 404）")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_context_isolation()
    test_no_silence_and_round_robin()
    test_model_override()
    test_persona_public()
    test_sse_stream()
    test_red_team()
    test_exec_summary()
    test_streaming()
    test_session_transport()
    print()
    if _failures:
        print(f"[FAIL] {len(_failures)} 件 FAIL")
        sys.exit(1)
    print("[OK] 全テスト pass")
