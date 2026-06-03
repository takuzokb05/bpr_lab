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
    # opening1 + 発散3 + 批判3 + 収束の口火(司会)1 + 収束3 + closing1 + synthesis1 = 13
    # （summary 廃止・司会クロージング追加・収束の口火で合意を1回だけまとめる）
    check(len(turns) == 13, f"turn 数が想定どおり: {len(turns)}")
    payloads = [
        json.loads([ln for ln in t.splitlines() if ln.startswith("data: ")][0].removeprefix("data: "))
        for t in turns
    ]
    closing = [p for p in payloads if p.get("phase") == "closing"]
    check(len(closing) == 1, f"司会クロージングが1回出る: {len(closing)}")
    check(closing and closing[0]["speaker_id"] == "moderator", "クロージングは司会が行う")

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


def test_synthesis_only():
    """議事録(synthesis)が1回・議長が書く。要約3行(summary)は廃止済み。"""
    print("[test] synthesis only (summary phase removed)")
    council = service.build_council(
        ["moderator", "logic", "idea", "chair"],
        rounds_per_phase=1, mock=True,
    )
    turns = list(council.run("議題S"))
    phases = [t.phase for t in turns]
    check("summary" not in phases, "summary フェーズは廃止された")
    check(phases.count("synthesis") == 1, "synthesis は1回だけ出る")
    syn = next(t for t in turns if t.phase == "synthesis")
    check(syn.speaker_id == "chair", "議事録は議長が書く")


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
        ev_line = next((l for l in lines if l.startswith("event: ")), None)
        data_line = next((l for l in lines if l.startswith("data: ")), None)
        # heartbeat / 初回パディング（": ..." コメント）は event/data を持たない → スキップ。
        if ev_line is None or data_line is None:
            continue
        out.append(
            {
                "event": ev_line.removeprefix("event: "),
                "data": json.loads(data_line.removeprefix("data: ")),
            }
        )
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
def test_followup_injection():
    """Step 3: pull で追い質問を注入。人間ターン→司会再提示→パネリスト1周。

    - 本編フェーズの Turn 直後にだけ拾う（opening/summary/synthesis では拾わない）。
    - 複数 followup は 1 ラウンドに束ねる。
    - パネリストは list(self.panelists) 順で固定（本編ローテーション不変）。
    - pull=None で従来動作（注入なし）に一致。
    """
    print("[test] followup injection (pull: human/followup round)")

    class FakeMsg:
        """HumanMessage 互換の最小スタブ（duck typing: .text/.target）。"""

        def __init__(self, text):
            self.text = text
            self.target = None

    personas = [
        make("mod", cat="facilitation"),
        make("logic"),
        make("idea"),
        make("empathy"),
        make("chair", cat="chair"),
    ]
    panel_order = ["logic", "idea", "empathy"]  # list(panelists) の順

    # 最初の本編 Turn 直後にだけ追い質問を2件まとめて返し、以降は空（束ね・1回だけ）。
    box = {"fired": False}

    def scripted_pull():
        if not box["fired"]:
            box["fired"] = True
            return [FakeMsg("追い質問A"), FakeMsg("追い質問B")]
        return []

    council = Council(
        personas, MockLLMClient(),
        phases=[("発散", "d", True)], rounds_per_phase=1,
    )
    turns = list(council.run("議題FU", pull=scripted_pull))

    phases = [t.phase for t in turns]
    speakers = [t.speaker_id for t in turns]

    # 人間ターン2件（束ね）
    human_turns = [t for t in turns if t.speaker_id == "human"]
    check(len(human_turns) == 2, f"追い質問2件が human ターンとして注入: {len(human_turns)}")
    check(all(t.phase == "human" for t in human_turns), "human ターンの phase は human")
    check(all(t.speaker_name == "あなた" for t in human_turns), "human ターンの名前は あなた")
    check(
        [t.content for t in human_turns] == ["追い質問A", "追い質問B"],
        "human ターンの content は追い質問本文そのまま（delta=全文1チャンク相当）",
    )

    # 司会の再提示（phase=followup, speaker=mod）が human の直後・パネリスト1周の前
    followups = [t for t in turns if t.phase == "followup"]
    check(followups[0].speaker_id == "mod", "followup ラウンドは司会の再提示から始まる")
    panelist_followups = [t.speaker_id for t in followups if t.speaker_id != "mod"]
    check(
        panelist_followups == panel_order,
        f"パネリストは list(panelists) 順で1周（ローテーション不変）: {panelist_followups}",
    )

    # 注入は最初の本編 Turn 直後に1回だけ（束ね）。followup 数は司会1+パネリスト3=4。
    check(len(followups) == 1 + len(panel_order), f"followup は1ラウンドに束ねて1回だけ: {len(followups)}")

    # opening/summary/synthesis では拾わない（human/followup はそれらの直後に出ない）
    check("opening" in phases, "opening は出る")
    check("synthesis" in phases, "synthesis は出る")

    # 追い質問は最初の本編フェーズ Turn の直後（opening 直後ではない）に挿入される
    first_human_idx = speakers.index("human")
    check(phases[first_human_idx - 1] == "発散", "human 注入の直前は本編フェーズ Turn")

    # pull=None で従来動作に一致（注入なし・turn 数と内容が一致）
    council_none = Council(
        [make("mod", cat="facilitation"), make("logic"), make("idea"),
         make("empathy"), make("chair", cat="chair")],
        MockLLMClient(),
        phases=[("発散", "d", True)], rounds_per_phase=1,
    )
    turns_none = list(council_none.run("議題FU"))
    check("human" not in [t.speaker_id for t in turns_none], "pull=None なら human ターンは出ない")
    check("followup" not in [t.phase for t in turns_none], "pull=None なら followup フェーズは出ない")

    # pull が常に空を返すなら従来と完全一致
    council_empty = Council(
        [make("mod", cat="facilitation"), make("logic"), make("idea"),
         make("empathy"), make("chair", cat="chair")],
        MockLLMClient(),
        phases=[("発散", "d", True)], rounds_per_phase=1,
    )
    turns_empty = list(council_empty.run("議題FU", pull=lambda: []))
    check(
        [t.speaker_id for t in turns_empty] == [t.speaker_id for t in turns_none],
        "pull=[] は pull=None と同じ進行（従来動作）",
    )


def test_llm_status():
    """GAP3: llm_status は環境で切替・キー値を漏らさない／mock=True は常に Mock。"""
    print("[test] llm status & mock-always-mock (二重課金防止)")
    import json
    import os
    from core import MockLLMClient as _Mock

    secret = "sk-ant-SECRET-do-not-leak-1234567890"
    saved = os.environ.get("ANTHROPIC_API_KEY")
    try:
        # 1. キー未設定 → mock
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("AI_TEAMS_BYOK", None)
        st = service.llm_status()
        check(
            st["llm"] == "mock" and st["api_key_set"] is False and st["byok"] is False,
            f"キー未設定で mock: {st}",
        )
        check(
            "anthropic" in st.get("providers", []) and st.get("research_provider") == "anthropic",
            f"providers に anthropic / 検索は anthropic のみ: {st}",
        )
        check(isinstance(service.make_client(mock=False), _Mock),
              "キー未設定なら非 mock 指定でも Mock にフォールバック")

        # 2. キー設定 → anthropic（ただし値は漏らさない）
        os.environ["ANTHROPIC_API_KEY"] = secret
        st = service.llm_status()
        check(st["llm"] == "anthropic" and st["api_key_set"] is True,
              f"キー設定で anthropic: {st}")
        check(secret not in json.dumps(st, ensure_ascii=False),
              "llm_status の返り値にキー文字列が含まれない")

        # 3. mock=True はキー有無に関わらず常に Mock（二重課金禁止）
        check(isinstance(service.make_client(mock=True), _Mock),
              "mock=True はキー設定時でも必ず Mock を返す（二重課金防止）")
    finally:
        if saved is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = saved


def _setup_temp_dirs():
    """personas/presets を一時ディレクトリにコピーし、service の参照先を差し替える。

    実ディレクトリを汚さずに save/delete/category 変更を検証する。差し替え前の値を返すので
    呼び出し側が finally で戻す。
    """
    import os
    import shutil
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="aiteams_test_"))
    personas_dst = tmp / "personas"
    presets_dst = tmp / "presets"
    shutil.copytree(service.PERSONAS_DIR, personas_dst)
    # presets/builtin は同梱物。直下のユーザー領域は空で用意。
    (presets_dst / "builtin").mkdir(parents=True, exist_ok=True)
    if (service.PRESETS_BUILTIN_DIR).is_dir():
        shutil.copytree(service.PRESETS_BUILTIN_DIR, presets_dst / "builtin",
                        dirs_exist_ok=True)

    saved = (service.PERSONAS_DIR, service.PRESETS_DIR, service.PRESETS_BUILTIN_DIR)
    service.PERSONAS_DIR = personas_dst
    service.PRESETS_DIR = presets_dst
    service.PRESETS_BUILTIN_DIR = presets_dst / "builtin"
    return tmp, saved


def _restore_dirs(saved):
    service.PERSONAS_DIR, service.PRESETS_DIR, service.PRESETS_BUILTIN_DIR = saved


def test_byok_make_client():
    """BYOK: リクエスト毎のキーで AnthropicClient、byok モードはサーバ env キーを来訪者に使わない。"""
    print("[test] BYOK make_client (per-request key / no server-key for visitors)")
    import os

    from core import (
        AnthropicClient as _Anthropic,
        OpenAIClient as _OpenAI,
        GeminiClient as _Gemini,
        MockLLMClient as _Mock,
    )

    saved_key = os.environ.get("ANTHROPIC_API_KEY")
    saved_byok = os.environ.get("AI_TEAMS_BYOK")
    try:
        # 1. mock=True は api_key があっても必ず Mock（二重課金防止）
        check(
            isinstance(service.make_client(mock=True, api_key="sk-ant-xxx"), _Mock),
            "mock=True は api_key 指定でも Mock",
        )
        # 2. api_key 明示 → その鍵で AnthropicClient（BYOK 本線・既定 provider）
        check(
            isinstance(service.make_client(mock=False, api_key="sk-ant-USERKEY"), _Anthropic),
            "api_key 指定（既定 provider）で AnthropicClient を返す",
        )
        # 2b. provider 指定で OpenAI / Gemini クライアントに振り分け（1セッション=1 provider）
        check(
            isinstance(service.make_client(mock=False, api_key="sk-xxx", provider="openai"), _OpenAI),
            "provider=openai で OpenAIClient",
        )
        check(
            isinstance(service.make_client(mock=False, api_key="AIza-xxx", provider="google"), _Gemini),
            "provider=google で GeminiClient",
        )
        check(
            isinstance(service.make_client(mock=False, api_key="g", provider="gemini"), _Gemini),
            "provider=gemini も google に正規化",
        )
        check(service.normalize_provider("unknown") == "anthropic", "未知 provider は anthropic に既定化")
        # 2c. mock は provider 指定でも Mock（課金しない）
        check(
            isinstance(service.make_client(mock=True, api_key="x", provider="openai"), _Mock),
            "mock=True は provider 指定でも Mock",
        )
        # 2d. build_council: 非 anthropic provider では Web 検索を強制 off（検索は anthropic のみ）
        c_oa = service.build_council(
            ["moderator", "logic", "idea", "chair"],
            rounds_per_phase=1, mock=True, provider="openai", research=True,
        )
        check(c_oa.research is False, "非 anthropic provider では research 強制 off")
        c_an = service.build_council(
            ["moderator", "logic", "idea", "chair"],
            rounds_per_phase=1, mock=True, provider="anthropic", research=True,
        )
        check(c_an.research is True, "anthropic provider では research=True が活きる")
        # 3. BYOK モード: api_key 無し＋サーバ env キー有り → サーバ鍵を使わず Mock
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-SERVERKEY"
        os.environ["AI_TEAMS_BYOK"] = "1"
        check(service.byok_mode() is True, "AI_TEAMS_BYOK=1 で byok_mode True")
        check(
            isinstance(service.make_client(mock=False, api_key=None), _Mock),
            "BYOK でキー未提供なら サーバ env キーを使わず Mock（来訪者にサーバ鍵を使わせない）",
        )
        st = service.llm_status()
        check(
            st.get("byok") is True and st.get("api_key_set") is False,
            f"BYOK の llm_status は byok:true・api_key_set:false（偵察情報を絞る）: {st}",
        )
        # 4. 非 BYOK: api_key 無し＋サーバ env キー有り → 従来どおりサーバ鍵で AnthropicClient
        os.environ.pop("AI_TEAMS_BYOK", None)
        check(
            isinstance(service.make_client(mock=False, api_key=None), _Anthropic),
            "非 BYOK は従来どおりサーバ env キーで AnthropicClient（個人運用の後方互換）",
        )
        # 5. readonly_mode は env-gated
        check(service.readonly_mode() is False, "AI_TEAMS_READONLY 未設定で readonly_mode False")
        os.environ["AI_TEAMS_READONLY"] = "1"
        check(service.readonly_mode() is True, "AI_TEAMS_READONLY=1 で readonly_mode True")
        os.environ.pop("AI_TEAMS_READONLY", None)
    finally:
        os.environ.pop("AI_TEAMS_BYOK", None)
        os.environ.pop("AI_TEAMS_READONLY", None)
        if saved_byok is not None:
            os.environ["AI_TEAMS_BYOK"] = saved_byok
        if saved_key is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = saved_key


def test_verbosity():
    """応答の長さプリセット: normalize / build_council→length_hint / max_tokens / build_context 語句。"""
    print("[test] verbosity preset (length_hint / max_tokens / context wording)")
    from core import AnthropicClient as _Anthropic

    # 1. 正規化（未指定/未知は standard）
    check(service.normalize_verbosity(None) == "standard", "未指定は standard")
    check(service.normalize_verbosity("xxx") == "standard", "未知は standard")
    check(service.normalize_verbosity("deep") == "deep", "deep はそのまま")

    # 2. build_council が length_hint を Council に渡す（mock で可）
    c_std = service.build_council(
        ["moderator", "logic", "idea", "chair"], rounds_per_phase=1, mock=True
    )
    check(c_std.length_hint == "", "standard（既定）は length_hint=''（従来＝簡潔に）")
    c_deep = service.build_council(
        ["moderator", "logic", "idea", "chair"], rounds_per_phase=1, mock=True, verbosity="deep"
    )
    check(
        c_deep.length_hint == service.VERBOSITY["deep"]["hint"],
        "deep は深掘りの length_hint を Council に渡す",
    )

    # 3. make_client に max_tokens が伝わる（real クライアントの構築のみ・無通信）
    c = service.make_client(mock=False, api_key="sk-ant-x", max_tokens=8192)
    check(
        isinstance(c, _Anthropic) and c._max_tokens == 8192,
        "max_tokens 上限がクライアントに伝わる",
    )

    # 4. build_context: length_directive が末尾ナッジの長さ語句を差し替える（空＝従来「簡潔に」）
    b = make("b")
    _s1, msg_def = build_context(transcript=[], active=b, topic="T")
    tail_def = msg_def[-1]["content"]
    check("簡潔に発言してください" in tail_def, "既定は『簡潔に発言してください』（後方互換）")
    _s2, msg_deep = build_context(transcript=[], active=b, topic="T", length_directive="じっくり丁寧に")
    tail_deep = msg_deep[-1]["content"]
    check("じっくり丁寧に発言してください" in tail_deep, "length_directive で長さ語句が差し替わる")
    check("簡潔に発言してください" not in tail_deep, "deep では『簡潔に』が外れる")


def test_custom_personas():
    """クライアント定義のカスタムペルソナ: セッション限定でレジストリに重なり、サーバ非保存。"""
    print("[test] custom personas (client-defined / session-only / non-persisted)")
    import os

    from fastapi.testclient import TestClient

    from api.main import app

    # 1. build_council でカスタムがパネリストとして編成に入る（mock）
    custom = [
        {"id": "my-x", "display_name": "自作役", "system_prompt": "あなたは自作のテスト役です。", "category": "thinking"}
    ]
    c = service.build_council(
        ["moderator", "my-x", "logic", "chair"], rounds_per_phase=1, mock=True, custom_personas=custom
    )
    check("my-x" in [p.id for p in c.panelists], "カスタムペルソナがパネリストとして編成に入る")

    # 2. 不正なカスタム（system_prompt 空）は ValueError（→400）
    try:
        service.build_council(
            ["my-y"], rounds_per_phase=1, mock=True,
            custom_personas=[{"id": "my-y", "display_name": "x", "system_prompt": "", "category": "thinking"}],
        )
        check(False, "空 system_prompt のカスタムは弾く")
    except ValueError:
        check(True, "空 system_prompt のカスタムは ValueError（→400）")

    # 3. 非保存・後方互換: 未指定なら従来編成（カスタムは残らない＝レジストリに書かない）
    c2 = service.build_council(
        ["moderator", "logic", "idea", "chair"], rounds_per_phase=1, mock=True
    )
    check("my-x" not in {p.id for p in c2.panelists}, "custom_personas 未指定なら従来編成（サーバ非保存）")
    check("my-x" not in {p.id for p in service.load_registry()}, "カスタムはレジストリ(ディスク)に残らない")

    # 4. HTTP: mock セッションにカスタム同送→200、不正 id（pattern 違反）→422
    saved_tok = os.environ.get("AI_TEAMS_API_TOKEN")
    saved_byok = os.environ.get("AI_TEAMS_BYOK")
    client = TestClient(app)
    try:
        os.environ.pop("AI_TEAMS_API_TOKEN", None)
        os.environ.pop("AI_TEAMS_BYOK", None)
        r = client.post("/sessions", json={
            "topic": "t", "persona_ids": ["logic", "my-z"], "mock": True, "interactive": False,
            "custom_personas": [{"id": "my-z", "display_name": "Z", "system_prompt": "テスト役", "category": "thinking"}],
        })
        check(r.status_code == 200, f"カスタム同送 mock セッションは 200: {r.status_code}")
        r = client.post("/sessions", json={
            "topic": "t", "persona_ids": ["logic"], "mock": True, "interactive": False,
            "custom_personas": [{"id": "Bad Id!", "display_name": "Z", "system_prompt": "x", "category": "thinking"}],
        })
        check(r.status_code == 422, f"不正 id のカスタムは 422（pattern）: {r.status_code}")
    finally:
        for k, v in (("AI_TEAMS_API_TOKEN", saved_tok), ("AI_TEAMS_BYOK", saved_byok)):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_provider_params():
    """OpenAI/Gemini のパラメータ整形: 推論モデル対応・Gemini temp 非送信・thinking 抑制。"""
    print("[test] provider params (reasoning_effort / no-temp / thinking_level)")
    from core import OpenAIClient, GeminiClient

    # OpenAI 推論モデル(gpt-5.5): temperature を送らず reasoning_effort + max_completion_tokens
    oc5 = OpenAIClient(api_key="x", model="gpt-5.5")
    p5 = oc5._params("sys", [{"role": "user", "content": "hi"}], 0.7)
    check("temperature" not in p5, "gpt-5.5 は temperature を送らない（推論モデルは既定1のみ）")
    check(p5.get("reasoning_effort") == "low", "gpt-5.5 は reasoning_effort=low（出力予算を発言に回す）")
    check("max_completion_tokens" in p5 and "max_tokens" not in p5, "max_completion_tokens を使う")

    # OpenAI 従来モデル(gpt-4o): temperature あり・reasoning_effort なし
    oc4 = OpenAIClient(api_key="x", model="gpt-4o")
    p4 = oc4._params("sys", [], 0.5)
    check(
        p4.get("temperature") == 0.5 and "reasoning_effort" not in p4,
        "gpt-4o は temperature を送り reasoning_effort は付けない",
    )

    # Gemini: temperature を送らず（Gemini 3 では非推奨）thinking_config を低めに設定
    gc = GeminiClient(api_key="x")
    cfg = gc._config("sys", 0.7)
    check(getattr(cfg, "temperature", None) is None, "Gemini は temperature を送らない（既定に従う）")
    check(getattr(cfg, "thinking_config", None) is not None, "Gemini は thinking_config を設定（出力枯れ防止）")


def test_local_provider():
    """内製（local）: base_url で OpenAI 互換へ・検索設定・force_local・research_providers。"""
    print("[test] local provider (self-hosted / open-frontier via base_url)")
    import os

    from core import OpenAIClient as _OpenAI, MockLLMClient as _Mock

    keys = (
        "AI_TEAMS_LOCAL_BASE_URL",
        "AI_TEAMS_LOCAL_MODEL",
        "AI_TEAMS_LOCAL_API_KEY",
        "AI_TEAMS_LOCAL_SEARCH",
        "AI_TEAMS_FORCE_LOCAL",
        "AI_TEAMS_BYOK",
        "AI_TEAMS_LOCAL_REASONING",
    )
    saved = {k: os.environ.get(k) for k in keys}
    try:
        for k in keys:
            os.environ.pop(k, None)

        # 正規化
        check(service.normalize_provider("local") == "local", "provider=local は local")
        check(service.normalize_provider("ollama") == "local", "ollama は local に正規化")

        # base_url 未設定 → 内製は無効・make_client は Mock（落とさない）
        check(service.local_enabled() is False, "base_url 未設定で local 無効")
        check(
            isinstance(service.make_client(mock=False, provider="local"), _Mock),
            "local だが base_url 未設定なら Mock",
        )
        check(service.research_providers() == ["anthropic"], "既定 research_providers は anthropic のみ")
        check(service.force_local() is False, "force_local 未設定で False")

        # base_url 設定 → OpenAIClient（local モード）
        os.environ["AI_TEAMS_LOCAL_BASE_URL"] = "http://127.0.0.1:11434/v1"
        os.environ["AI_TEAMS_LOCAL_MODEL"] = "qwen3:14b"
        os.environ["AI_TEAMS_LOCAL_API_KEY"] = "test-key"
        check(service.local_enabled() is True, "base_url 設定で local 有効")
        c = service.make_client(mock=False, provider="local", max_tokens=1234)
        check(isinstance(c, _OpenAI), "local + base_url で OpenAIClient")
        check(
            c._local is True and c._base_url == "http://127.0.0.1:11434/v1",
            "base_url を保持・local モード",
        )
        check(c._model == "qwen3:14b", "AI_TEAMS_LOCAL_MODEL を使う")
        # local の _params は max_tokens + temperature（max_completion_tokens は使わない）
        p = c._params("sys", [{"role": "user", "content": "hi"}], 0.6)
        check("max_tokens" in p and "max_completion_tokens" not in p, "local は max_tokens を使う")
        check(p.get("temperature") == 0.6, "local は temperature が効く（per-persona）")
        check(
            p.get("extra_body", {}).get("reasoning", {}).get("effort") == "low",
            "local は reasoning=low を既定で送る（思考が出力枠を食う空ターン化を抑制）",
        )
        # 検索未設定 → web_research は未対応（ネットワークは叩かない）
        check(c._search_mode == "", "検索未設定なら search_mode 空")
        check("Anthropic" in c.web_research("x"), "検索未設定の local は web_research 未対応を返す")

        # 検索設定（openrouter）
        os.environ["AI_TEAMS_LOCAL_SEARCH"] = "openrouter"
        check(service.local_search_enabled() is True, "AI_TEAMS_LOCAL_SEARCH=openrouter で検索有効")
        check("local" in service.research_providers(), "検索設定済みで research_providers に local")
        c2 = service.make_client(mock=False, provider="local")
        check(c2._search_mode == "openrouter", "make_client が search_mode を渡す")
        cc = service.build_council(
            ["moderator", "logic", "idea", "chair"], mock=True, provider="local", research=True
        )
        check(cc.research is True, "検索設定済みの local では research=True が活きる")
        os.environ.pop("AI_TEAMS_LOCAL_SEARCH", None)
        cc2 = service.build_council(
            ["moderator", "logic", "idea", "chair"], mock=True, provider="local", research=True
        )
        check(cc2.research is False, "検索未設定の local では research 強制 off")

        # 討論モード（エンジン・プリセット・許可制でモデル＋verbosity）
        check(
            (service.resolve_preset("quick") or {}).get("model") == "deepseek/deepseek-v4-flash",
            "preset quick=Flash に解決",
        )
        check(service.resolve_preset("unknown") is None, "未知 preset は None（許可制）")
        cm = service.make_client(mock=False, provider="local", model="deepseek/deepseek-v4-flash")
        check(cm._model == "deepseek/deepseek-v4-flash", "make_client が model 上書きを使う")
        stp = service.llm_status()
        check(
            any(p.get("id") == "quick" for p in stp.get("presets", []))
            and stp.get("default_preset") == "standard",
            f"llm_status に presets と default_preset(standard): {stp.get('presets')}",
        )

        # force_local
        os.environ["AI_TEAMS_FORCE_LOCAL"] = "1"
        check(service.force_local() is True, "FORCE_LOCAL=1 + base_url で force_local True")
        st = service.llm_status()
        check(
            st.get("local") is True and st.get("force_local") is True,
            f"llm_status に local/force_local: {st}",
        )
        check("local" in st.get("providers", []), "providers に local")

        # base_url を消すと force_local は False（誤設定で落とさない）
        os.environ.pop("AI_TEAMS_LOCAL_BASE_URL", None)
        check(service.force_local() is False, "base_url 無しなら force_local False（誤設定耐性）")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_synthesis_max_tokens():
    """議事録(synthesis)は専用の大きめ max_tokens で生成し、途中打ち切りを防ぐ。"""
    print("[test] synthesis max_tokens (議事録は専用の大きめ上限で打ち切り防止)")

    c = service.build_council(
        ["moderator", "logic", "idea", "chair"],
        rounds_per_phase=1, mock=True, verbosity="standard",
    )
    check(c.synthesis_max_tokens >= 8192, f"synthesis_max_tokens は 8192 以上: {c.synthesis_max_tokens}")
    # 非ストリーム run（emit=None）で全 mock 呼び出しを記録 → 最後が synthesize。
    list(c.run("テスト議題"))
    calls = c.client.calls  # MockLLMClient
    check(len(calls) >= 2, f"複数発言が生成された: {len(calls)}")
    body_mts = [call.get("max_tokens") for call in calls[:-1]]
    synth_mt = calls[-1].get("max_tokens")
    check(all(mt is None for mt in body_mts), f"本編発言は max_tokens 上書きなし(None): {set(body_mts)}")
    check(
        synth_mt == c.synthesis_max_tokens,
        f"議事録は専用 max_tokens({c.synthesis_max_tokens})を渡す: {synth_mt}",
    )
    # deep でも本編1発言の2倍のヘッドルームが付く（最も長文化しやすいモードの保護）。
    cd = service.build_council(["moderator", "logic", "idea", "chair"], mock=True, verbosity="deep")
    check(cd.synthesis_max_tokens >= 16384, f"deep の議事録は 16384 以上: {cd.synthesis_max_tokens}")

    # stream 経路（emit set）でも synthesis だけ大きい上限になることを固定する（回帰検出）。
    c2 = service.build_council(
        ["moderator", "logic", "idea", "chair"], rounds_per_phase=1, mock=True, verbosity="standard"
    )
    list(c2.run("テスト議題2", emit=lambda e: None))
    calls2 = c2.client.calls
    check(all(call.get("max_tokens") is None for call in calls2[:-1]), "stream: 本編は上書きなし(None)")
    check(
        calls2[-1].get("max_tokens") == c2.synthesis_max_tokens,
        f"stream: 議事録は専用 max_tokens を渡す: {calls2[-1].get('max_tokens')}",
    )


def test_persona_service_crud():
    """ペルソナ service: 保存/詳細/category 変更 unlink/旧パス unlink を id→path で。"""
    print("[test] persona service CRUD (save/detail/category-move unlink)")
    import shutil

    tmp, saved = _setup_temp_dirs()
    try:
        # 1. persona_detail は system_prompt を含み、accent は生値
        from core import Persona
        p = Persona(id="x", display_name="X", system_prompt="P", category="thinking")
        det = service.persona_detail(p)
        check(det["system_prompt"] == "P", "persona_detail は system_prompt を含む")
        check(det["accent"] is None, "accent 未指定は生値 None（カテゴリ色で潰さない）")

        # 2. 新規作成
        data = {
            "id": "newbie", "display_name": "新人", "system_prompt": "がんばる",
            "category": "thinking",
        }
        service.save_persona(data, expect_id=None)
        path = service.PERSONAS_DIR / "thinking" / "newbie.yaml"
        check(path.exists(), "新規ペルソナが personas/{category}/{id}.yaml に保存される")

        # 3. id 衝突 → ValueError("...exists")
        try:
            service.save_persona(data, expect_id=None)
            check(False, "id 衝突は ValueError を投げる")
        except ValueError as e:
            check("exists" in str(e), f"id 衝突メッセージに exists: {e}")

        # 4. category 変更で旧パスを unlink（id→path で旧ファイルを消す）
        moved = dict(data, category="founders")
        service.save_persona(moved, expect_id="newbie")
        new_path = service.PERSONAS_DIR / "founders" / "newbie.yaml"
        check(new_path.exists(), "category 変更後の新パスに保存される")
        check(not path.exists(), "category 変更で旧パスが unlink される")

        # 5. 書き出しキーは known のみ・safe_dump（日本語そのまま・id 推測しない）
        import yaml
        with new_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        check(set(raw) <= set(service._PERSONA_WRITE_KEYS), "書き出しキーは known セットのみ")
        check(raw["display_name"] == "新人", "allow_unicode で日本語が化けない")

        # 6. jobs.yaml の id=steve_jobs（ファイル名と不一致）でも detail が引ける
        det2 = service.get_persona_detail("steve_jobs")
        check(det2["id"] == "steve_jobs", "ファイル名 jobs.yaml でも id=steve_jobs で引ける")

        # 7. 未知 id の更新は KeyError（404）
        try:
            service.save_persona(dict(data, id="ghost"), expect_id="ghost")
            check(False, "未知 id 更新は KeyError")
        except KeyError:
            check(True, "未知 id 更新は KeyError（404 にマップ）")

        # 8. 削除
        service.delete_persona("newbie")
        check(not new_path.exists(), "delete_persona で実ファイルが消える")
    finally:
        _restore_dirs(saved)
        shutil.rmtree(tmp, ignore_errors=True)


def test_preset_service():
    """プリセット service: builtin 判定・読取専用・未知 persona 検証・CRUD。"""
    print("[test] preset service (builtin read-only / unknown persona / CRUD)")
    import shutil

    tmp, saved = _setup_temp_dirs()
    try:
        presets = service.load_presets()
        ids = {p["id"] for p in presets}
        check("startup_meeting" in ids and "philosophy_cafe" in ids,
              "同梱プリセット2件が読める")

        sm = service.get_preset("startup_meeting")
        check(sm["builtin"] is True, "builtin プリセットは builtin:true")
        check(
            sm["persona_ids"] == ["moderator", "steve_jobs", "idea", "logic", "chair"],
            f"startup_meeting の persona_ids は実 id（steve_jobs）: {sm['persona_ids']}",
        )

        # builtin の更新は read-only 409
        try:
            service.save_preset(dict(sm, name="改変"), create=False)
            check(False, "builtin 更新は ValueError")
        except ValueError as e:
            check("read-only" in str(e), f"builtin は読取専用: {e}")
        # builtin の削除も read-only
        try:
            service.delete_preset("startup_meeting")
            check(False, "builtin 削除は ValueError")
        except ValueError as e:
            check("read-only" in str(e), f"builtin 削除は読取専用: {e}")

        # ユーザープリセット新規作成
        up = {
            "id": "my_team", "name": "マイチーム",
            "persona_ids": ["moderator", "logic", "idea", "chair"],
            "rounds_per_phase": 1, "red_team": True,
        }
        created = service.save_preset(up, create=True)
        check(created["builtin"] is False, "ユーザープリセットは builtin:false")
        check((service.PRESETS_DIR / "my_team.yaml").exists(),
              "ユーザープリセットは presets/ 直下に保存（builtin/ ではない）")

        # 同 id 作成は exists 409
        try:
            service.save_preset(up, create=True)
            check(False, "id 衝突は ValueError")
        except ValueError as e:
            check("exists" in str(e), f"preset id 衝突に exists: {e}")

        # 未知 persona は valid:false（ValueError "unknown persona ids: [...]"）
        try:
            service.save_preset(
                dict(up, id="bad", persona_ids=["moderator", "no_such_persona"]),
                create=True,
            )
            check(False, "未知 persona は ValueError")
        except ValueError as e:
            check("unknown persona ids" in str(e), f"未知 persona メッセージ: {e}")

        # ユーザープリセット更新・削除
        service.save_preset(dict(up, name="改名チーム"), create=False)
        check(service.get_preset("my_team")["name"] == "改名チーム", "ユーザープリセット更新")
        service.delete_preset("my_team")
        check("my_team" not in {p["id"] for p in service.load_presets()},
              "ユーザープリセット削除")

        # 未知 id 取得・削除は KeyError
        try:
            service.get_preset("nope")
            check(False, "未知 preset 取得は KeyError")
        except KeyError:
            check(True, "未知 preset 取得は KeyError（404）")
    finally:
        _restore_dirs(saved)
        shutil.rmtree(tmp, ignore_errors=True)


def test_http_api():
    """HTTP 層: 例外→ステータスコード写像・パストラバーサル拒否・/health の形。"""
    print("[test] HTTP API (status mapping / path traversal / health)")
    import shutil

    from fastapi.testclient import TestClient

    from api.main import app

    tmp, saved = _setup_temp_dirs()
    client = TestClient(app)
    try:
        # /health: 形 + キー値非露出
        r = client.get("/health")
        check(r.status_code == 200, "/health 200")
        body = r.json()
        check({"status", "llm", "api_key_set"} <= set(body), "/health に status/llm/api_key_set")
        check(isinstance(body["api_key_set"], bool), "api_key_set は bool")
        check("ANTHROPIC_API_KEY" not in r.text, "/health にキー名/値を含めない")

        # ペルソナ CRUD のステータス写像
        new_p = {"id": "tester", "display_name": "テスター", "system_prompt": "P", "category": "thinking"}
        r = client.post("/personas", json=new_p)
        check(r.status_code == 201, f"POST /personas 201: {r.status_code}")
        check("system_prompt" in r.json(), "persona_detail は system_prompt を含む")
        check(not r.json().get("avatar"), "新規ペルソナに絵文字 avatar を焼き込まない")
        r = client.post("/personas", json=new_p)
        check(r.status_code == 409, f"重複 POST /personas は 409: {r.status_code}")
        r = client.post("/personas", json={**new_p, "id": "bad", "category": "nope"})
        check(r.status_code == 422, f"不正 category は 422(Literal): {r.status_code}")
        r = client.post("/personas", json={**new_p, "id": "bad", "system_prompt": ""})
        check(r.status_code == 422, f"空 system_prompt は 422: {r.status_code}")
        r = client.get("/personas/tester")
        check(r.status_code == 200, "GET /personas/{id} 200")
        r = client.get("/personas/ghost")
        check(r.status_code == 404, f"未知 persona は 404: {r.status_code}")
        r = client.delete("/personas/tester")
        check(r.status_code == 204, f"DELETE /personas 204: {r.status_code}")
        r = client.delete("/personas/tester")
        check(r.status_code == 404, f"二重 DELETE は 404: {r.status_code}")

        # パストラバーサル: id の charset 制限で入口 422（PERSONAS_DIR 外に書かせない）
        r = client.post("/personas", json={**new_p, "id": "../evil"})
        check(r.status_code == 422, f"../ を含む persona id は 422: {r.status_code}")
        check(not (service.PERSONAS_DIR.parent / "evil.yaml").exists(), "ディレクトリ外にファイルが作られない")

        # プリセット CRUD のステータス写像
        r = client.get("/presets")
        check(r.status_code == 200 and len(r.json()) >= 2, "GET /presets に builtin 2件")
        r = client.put("/presets/startup_meeting", json={
            "id": "startup_meeting", "name": "改変",
            "persona_ids": ["moderator", "logic", "idea", "chair"],
        })
        check(r.status_code == 409, f"builtin プリセット更新は 409: {r.status_code}")
        r = client.delete("/presets/startup_meeting")
        check(r.status_code == 409, f"builtin プリセット削除は 409: {r.status_code}")
        r = client.post("/presets", json={
            "id": "mine", "name": "マイ",
            "persona_ids": ["moderator", "logic", "idea", "chair"],
        })
        check(r.status_code == 201, f"POST /presets 201: {r.status_code}")
        r = client.post("/presets", json={
            "id": "mine", "name": "重複",
            "persona_ids": ["moderator", "logic"],
        })
        check(r.status_code == 409, f"preset id 衝突は 409: {r.status_code}")
        r = client.post("/presets", json={
            "id": "badp", "name": "未知",
            "persona_ids": ["moderator", "no_such_persona"],
        })
        check(r.status_code == 400, f"未知 persona を含むプリセットは 400: {r.status_code}")
        r = client.post("/presets", json={
            "id": "../evilp", "name": "x", "persona_ids": ["moderator"],
        })
        check(r.status_code == 422, f"../ を含む preset id は 422: {r.status_code}")
        r = client.delete("/presets/mine")
        check(r.status_code == 204, f"ユーザープリセット削除は 204: {r.status_code}")
        r = client.get("/presets/nope")
        check(r.status_code == 404, f"未知 preset 取得は 404: {r.status_code}")

        # 追い質問エンドポイント: body 検証は session 存在に関わらず Pydantic が先に走る
        r = client.post("/sessions/nope/messages", json={"kind": "followup", "text": "hi"})
        check(r.status_code == 404, f"未知 session への追い質問は 404: {r.status_code}")
        r = client.post("/sessions/x/messages", json={"kind": "intervention", "text": "hi"})
        check(r.status_code == 422, f"不正 kind は 422(Literal): {r.status_code}")
        r = client.post("/sessions/x/messages", json={"text": ""})
        check(r.status_code == 422, f"空 text は 422: {r.status_code}")
        r = client.delete("/sessions/nope")
        check(r.status_code == 404, f"未知 session の停止は 404: {r.status_code}")
    finally:
        _restore_dirs(saved)
        shutil.rmtree(tmp, ignore_errors=True)


def test_followup_e2e():
    """追い質問 end-to-end: post_message → 背景 _produce → _drain → 人間ターン注入。"""
    print("[test] followup e2e (post_message -> background drain -> inject)")
    import threading

    from core import Council, MockLLMClient

    # オープニング生成中にブロックして、その間に post_message できるようにする
    # （mock は瞬時に完走するので、投函タイミングを決定論化する）。
    gate = threading.Event()

    class GatedMock(MockLLMClient):
        def __init__(self):
            super().__init__()
            self._first = True

        def generate_stream(self, **kw):
            if self._first:
                self._first = False
                gate.wait(timeout=10)  # 最初の発言（オープニング）で待つ
            yield from super().generate_stream(**kw)

    personas = [
        make("mod", cat="facilitation"),
        make("logic"),
        make("idea"),
        make("chair", cat="chair"),
    ]
    council = Council(personas, GatedMock(), phases=[("発散", "d", True)], rounds_per_phase=1)
    sess = service.start_session(council, "議題E2E")
    try:
        # オープリングでブロック中に追い質問を投函 → 最初の本編 Turn 直後に drain される
        service.post_message(sess, service.HumanMessage(text="追い質問E2E"))
        gate.set()  # 解放
        sess.thread.join(timeout=10)
        check(sess.status == "done", f"プロデューサ完走: {sess.status}")

        events = sess.events
        human_starts = [
            e for e in events
            if e["event"] == "turn_start" and e["data"].get("speaker_id") == "human"
        ]
        check(len(human_starts) == 1, f"人間ターンが1件注入される: {len(human_starts)}")
        hid = human_starts[0]["data"]["turn_id"]
        human_text = "".join(
            e["data"]["text"] for e in events
            if e["event"] == "delta" and e["data"].get("turn_id") == hid
        )
        check(human_text == "追い質問E2E", f"人間ターンの本文が一致: {human_text}")
        check(human_starts[0]["data"]["phase"] == "human", "人間ターンの phase は human")
        # 司会再提示 + パネリスト応答が followup フェーズで続く
        followups = [
            e for e in events
            if e["event"] == "turn_start" and e["data"].get("phase") == "followup"
        ]
        check(len(followups) >= 1, f"followup ターンが続く（司会/パネリスト）: {len(followups)}")
        # 全イベントに seq/ts が載る（再接続再生の一貫性）
        check(all("seq" in e and "ts" in e for e in events), "全イベントに seq と ts")
    finally:
        sess.cancelled = True
        gate.set()


def test_floor_open_pause():
    """(A) interactive=True: 本編後に status=="paused" になり paused イベントが出る。"""
    print("[test] floor-open pause (interactive: deliberate -> paused)")
    import time

    from core import Council, MockLLMClient

    personas = [
        make("mod", cat="facilitation"),
        make("logic"),
        make("idea"),
        make("chair", cat="chair"),
    ]
    council = Council(personas, MockLLMClient(), phases=[("発散", "d", True)], rounds_per_phase=1)
    sess = service.start_session(council, "議題FLOOR", interactive=True)
    try:
        # 本編完走後、floor-open に入って paused になるのを待つ（mock は瞬時）。
        deadline = time.time() + 5
        while sess.status != "paused" and time.time() < deadline:
            time.sleep(0.02)
        check(sess.status == "paused", f"本編後に status=paused になる: {sess.status}")

        events = sess.events
        kinds = [e["event"] for e in events]
        check("paused" in kinds, "paused イベントが出る")
        paused_ev = next(e for e in events if e["event"] == "paused")
        check(paused_ev["data"].get("phase") == "floor_open", "paused の phase は floor_open")
        check("seq" in paused_ev and "ts" in paused_ev, "paused イベントに seq/ts が載る")

        # 自動 synthesis していない（締めるまで議事録は出ない）。
        check(
            "synthesis" not in [e["data"].get("phase") for e in events if e["event"] == "turn_start"],
            "floor-open では自動 synthesis しない（締めるまで議事録は出ない）",
        )
        # opening+本編は出ている。
        phases = [e["data"].get("phase") for e in events if e["event"] == "turn_start"]
        check("opening" in phases and "発散" in phases, "opening と本編フェーズは出ている")
        # まだ done になっていない。
        check("done" not in kinds, "floor-open ではまだ done になっていない")
    finally:
        sess.cancelled = True
        service.finish_floor(sess)
        if sess.thread is not None:
            sess.thread.join(timeout=5)


def test_floor_open_close_then_finish():
    """(B) close で synthesis が出て再び paused、finish で done になる。"""
    print("[test] floor-open close (synthesis) then finish (done)")
    import threading
    import time

    from core import Council, MockLLMClient

    def wait_until(pred, timeout=5):
        deadline = time.time() + timeout
        while not pred() and time.time() < deadline:
            time.sleep(0.02)
        return pred()

    def synthesis_count(sess):
        return sum(
            1 for e in sess.events
            if e["event"] == "turn_start" and e["data"].get("phase") == "synthesis"
        )

    def paused_count(sess):
        return sum(1 for e in sess.events if e["event"] == "paused")

    personas = [
        make("mod", cat="facilitation"),
        make("logic"),
        make("idea"),
        make("chair", cat="chair"),
    ]
    council = Council(personas, MockLLMClient(), phases=[("発散", "d", True)], rounds_per_phase=1)
    sess = service.start_session(council, "議題CLOSE", interactive=True)
    try:
        # 1. 最初の floor-open（本編後）まで待つ
        check(wait_until(lambda: paused_count(sess) >= 1), "本編後に paused になる")

        # 2. close を post（threading で投函）→ synthesis が出て再び paused（paused が2回目に）
        before = len(sess.events)
        threading.Thread(target=service.close_floor, args=(sess,), daemon=True).start()
        # synthesis ターンが現れ、かつ paused イベントが2回目（再び floor-open）になるのを待つ
        check(
            wait_until(lambda: synthesis_count(sess) == 1 and paused_count(sess) >= 2),
            "close 後に synthesis を回して再び paused に戻る",
        )

        syn_starts = [
            e for e in sess.events
            if e["event"] == "turn_start" and e["data"].get("phase") == "synthesis"
        ]
        check(len(syn_starts) == 1, f"close で synthesis ターンが1件出る: {len(syn_starts)}")
        check(syn_starts[0]["data"]["speaker_id"] == "chair", "議事録は議長(chair)が書く")
        # close 後にイベントが増えている（synthesis + paused 再掲）
        check(len(sess.events) > before, "close でイベントが増える")
        # 締めた後も議場は開いたまま（paused）＝深掘り継続可能
        check(wait_until(lambda: sess.status == "paused"), "締めた後も議場は開いたまま（paused）")

        # 3. finish を post → done になり paused が閉じる
        threading.Thread(target=service.finish_floor, args=(sess,), daemon=True).start()
        check(wait_until(lambda: sess.status == "done"), "finish 後に done になる")
        check(sess.events[-1]["event"] == "done", "最後のイベントは done")
        if sess.thread is not None:
            sess.thread.join(timeout=5)
        check(not sess.thread.is_alive(), "プロデューサスレッドが終了する")
    finally:
        sess.cancelled = True
        service.finish_floor(sess)
        if sess.thread is not None:
            sess.thread.join(timeout=5)


def test_run_backward_compat():
    """(C) run() 後方互換: emit/pull=None で従来と同一 turn 列（opening+本編+synthesis）。

    deliberate→synthesize の合成が、抽出前の単一 run() と同じ turn 列を出すことを保証する。
    deliberate+synthesize を手で繋いだ列とも一致する（合成の等価性）。
    """
    print("[test] run() backward compat (deliberate+synthesize == run)")
    from itertools import count

    from core import Council, MockLLMClient

    def build():
        return Council(
            [
                make("mod", cat="facilitation"),
                make("logic"),
                make("idea"),
                make("empathy"),
                make("chair", cat="chair"),
            ],
            MockLLMClient(),
            phases=[("発散", "d", True), ("批判", "c", True)],
            rounds_per_phase=1,
        )

    # 1. run() の出力
    run_turns = list(build().run("議題BC"))
    run_sig = [(t.speaker_id, t.phase, t.round, t.turn_id, t.content) for t in run_turns]

    # 2. deliberate + synthesize を手で繋いだ出力（ids/transcript を共有）
    council = build()
    transcript: list = []
    ids = count()
    composed = list(council.deliberate("議題BC", transcript, ids=ids))
    composed += list(council.synthesize("議題BC", transcript, ids=ids))
    comp_sig = [(t.speaker_id, t.phase, t.round, t.turn_id, t.content) for t in composed]

    check(run_sig == comp_sig, "run() == deliberate()+synthesize()（合成の等価性）")

    # 3. 構造: opening が先頭、synthesis が末尾1回、turn_id は 0 から連番
    check(run_turns[0].phase == "opening", "先頭は opening")
    check(run_turns[-1].phase == "synthesis", "末尾は synthesis")
    check([t.phase for t in run_turns].count("synthesis") == 1, "synthesis は1回だけ")
    check(
        [t.turn_id for t in run_turns] == list(range(len(run_turns))),
        "turn_id は 0 から連番（deliberate→synthesize で継続採番）",
    )
    # 本編フェーズが両方出ている（発散・批判 各3パネリスト）
    phases = [t.phase for t in run_turns]
    check(phases.count("発散") == 3 and phases.count("批判") == 3, "本編は各フェーズ3人ずつ発言")


# ---------------------------------------------------------------------------
def test_materials_in_context():
    """(A) build_context に materials を渡すと先頭 user に【資料・前提】が入る。

    materials="" のときは従来と完全同一（test_context_isolation を壊さない）。
    """
    print("[test] materials grounding in build_context (資料接地)")
    a, b, c = make("a"), make("b"), make("c")
    transcript = [
        Turn("a", "A", "a-said", "発散", 0),
        Turn("b", "B", "b-said", "発散", 0),
        Turn("c", "C", "c-said", "発散", 0),
    ]

    # 1. materials 付き: 先頭 user に【資料・前提】が【議題】に続いて入る
    system, messages = build_context(
        transcript=transcript, active=b, topic="T", materials="売上 100 億円・粗利率 30%"
    )
    head = messages[0]["content"]
    check(messages[0]["role"] == "user", "先頭メッセージは user（Anthropic 要件）")
    check("【議題】" in head, "先頭 user に【議題】が入る")
    check("【資料・前提】" in head, "先頭 user に【資料・前提】が入る")
    check("売上 100 億円・粗利率 30%" in head, "materials 本文が先頭 user に載る")
    # 【議題】が【資料・前提】より前にある（順序）
    check(
        head.index("【議題】") < head.index("【資料・前提】"),
        "【議題】の後に【資料・前提】が続く",
    )

    # 2. materials="" は従来と完全同一（既定値・明示空の両方）
    sys_default, msg_default = build_context(transcript=transcript, active=b, topic="T")
    sys_empty, msg_empty = build_context(
        transcript=transcript, active=b, topic="T", materials=""
    )
    check(
        [m["content"] for m in msg_default] == [m["content"] for m in msg_empty],
        "materials='' は materials 未指定（従来）と完全一致",
    )
    check("【資料・前提】" not in msg_empty[0]["content"], "materials='' でブロックを足さない")
    # 空 transcript なら先頭 user は【議題】のみ（資料ブロックを足さないことを純粋に確認）。
    _sys, msg_bare = build_context(transcript=[], active=b, topic="T", materials="")
    check(
        msg_bare[0]["content"].startswith("【議題】\nT"),
        "materials='' の先頭 user は【議題】で始まる（資料ブロック無し）",
    )
    check("【資料・前提】" not in msg_bare[0]["content"], "空 transcript+materials='' で資料ブロックを足さない")


def test_intake_questions():
    """(B) generate_intake_questions(mock) が 2〜4 個の質問 list を返す。"""
    print("[test] generate_intake_questions (主訴確認・mock 定型)")

    qs = service.generate_intake_questions("新規事業をやるべきか", mock=True)
    check(isinstance(qs, list), "list を返す")
    check(all(isinstance(q, str) for q in qs), "各要素は str")
    check(2 <= len(qs) <= 4, f"質問数は 2〜4 個: {len(qs)}")
    check(all(q.strip() for q in qs), "空の質問を含まない")

    # materials 付きでも 2〜4 個（mock は定型・決定的）
    qs2 = service.generate_intake_questions(
        "新規事業をやるべきか", materials="予算 500 万円・3 名体制", mock=True
    )
    check(2 <= len(qs2) <= 4, f"materials 付きでも 2〜4 個: {len(qs2)}")

    # パーサ単体: 番号・箇条書き記号を剥がし、空行を捨て、最大 4 件に切る
    parsed = service._parse_intake_questions(
        "1. 主訴は何ですか\n- 制約はありますか\n\n３．既に試したことは？\n* 良い結論とは\n5) 余分な5件目"
    )
    check(len(parsed) == 4, f"最大 4 件に切り詰める: {len(parsed)}")
    check(parsed[0] == "主訴は何ですか", f"先頭番号 '1.' を剥がす: {parsed[0]}")
    check(parsed[1] == "制約はありますか", f"箇条書き '- ' を剥がす: {parsed[1]}")
    check(parsed[2] == "既に試したことは？", f"全角番号 '３．' を剥がす: {parsed[2]}")


def test_materials_propagation_e2e():
    """(C) build_council(materials=…) で Council.materials が伝播し _speak 経由で資料が載る。"""
    print("[test] materials propagation (build_council -> Council -> _speak)")
    from core import Council, MockLLMClient

    # 1. Council.materials に保持され、_speak 経由でパネリストの messages に資料が載る
    material_text = "前提: 競合 A 社のシェアは 40%"
    personas = [
        make("mod", cat="facilitation"),
        make("logic"),
        make("idea"),
        make("chair", cat="chair"),
    ]
    client = MockLLMClient()
    council = Council(
        personas, client, phases=[("発散", "d", True)], rounds_per_phase=1,
        materials=material_text,
    )
    check(council.materials == material_text, "Council.materials に伝播する")
    list(council.run("議題M"))  # mock で1ターン回す
    # 全 LLM 呼び出しの先頭 user に資料が載っている（パネリスト・司会・議長すべて）
    seen = False
    for call in client.calls:
        first_user = next((m["content"] for m in call["messages"] if m["role"] == "user"), "")
        if material_text in first_user and "【資料・前提】" in first_user:
            seen = True
    check(seen, "_speak 経由でパネリストの messages 先頭 user に資料が載る")

    # 2. build_council(materials=…) で Council に届く（service 経由）
    council2 = service.build_council(
        ["moderator", "logic", "idea", "chair"],
        rounds_per_phase=1, mock=True, materials="サービス層からの資料",
    )
    check(council2.materials == "サービス層からの資料", "build_council(materials=…) が Council に届く")

    # 3. materials 既定（未指定）なら Council.materials は ""（後方互換）
    council3 = service.build_council(
        ["moderator", "logic", "idea", "chair"], rounds_per_phase=1, mock=True
    )
    check(council3.materials == "", "build_council の materials 既定は ''（後方互換）")


# ---------------------------------------------------------------------------
def test_web_research_mock():
    """(1) web_research(Mock) が canned 文字列を返す（LLM/検索を呼ばない・無料）。"""
    print("[test] web_research mock canned (検索せず決定的)")
    c = MockLLMClient()
    brief = c.web_research("USD/JPY の 2026 年見通し")
    check(
        brief == "（モック調査結果: USD/JPY の 2026 年見通し ／出典なし・検証用）",
        f"Mock web_research は canned を返す: {brief}",
    )
    # web_research は generate を呼ばない（calls に記録されない＝検索/LLM 非発火）。
    check(len(c.calls) == 0, "web_research(Mock) は generate を呼ばない（calls 空・無料）")

    # service.run_research は client.web_research の薄いラッパ
    brief2 = service.run_research(c, "X についての統計")
    check(
        brief2 == "（モック調査結果: X についての統計 ／出典なし・検証用）",
        f"run_research は web_research をそのまま返す: {brief2}",
    )


def test_research_turn_emit():
    """(2) Council(research=True)+emit_research_turn で researcher ターンが emit され transcript に乗る。"""
    print("[test] emit_research_turn (speaker_id=researcher / phase=research)")
    from core import Council, MockLLMClient

    personas = [
        make("mod", cat="facilitation"),
        make("logic"),
        make("idea"),
        make("chair", cat="chair"),
    ]
    council = Council(
        personas, MockLLMClient(), phases=[("発散", "d", True)], rounds_per_phase=1,
        research=True,
    )
    check(council.research is True, "Council.research=True が伝播する")

    transcript: list = []
    events: list[dict] = []
    rt = council.emit_research_turn(
        transcript, "調査結果ブリーフ本文", emit=events.append, turn_id=42
    )

    # Turn の形
    check(rt.speaker_id == "researcher", "Turn.speaker_id は researcher")
    check(rt.speaker_name == "調査", "Turn.speaker_name は 調査")
    check(rt.phase == "research", "Turn.phase は research")
    check(rt.round == 0, "Turn.round は 0")
    check(rt.turn_id == 42, "Turn.turn_id は渡した値")
    check(rt.content == "調査結果ブリーフ本文", "Turn.content はブリーフ本文")

    # transcript に append される
    check(transcript == [rt], "emit_research_turn は transcript に Turn を積む")

    # emit イベント: turn_start → delta（全文1チャンク）。turn_end は呼び出し側が出すのでここでは出ない。
    types = [e["type"] for e in events]
    check(types == ["turn_start", "delta"], f"turn_start→delta を emit（turn_end は出さない）: {types}")
    ts = events[0]
    check(ts["speaker_id"] == "researcher" and ts["phase"] == "research", "turn_start に researcher/research")
    check(ts["turn_id"] == 42, "turn_start の turn_id は渡した値")
    check(events[1]["text"] == "調査結果ブリーフ本文", "delta は全文1チャンク")

    # emit=None でも transcript には積まれる（Turn を返す）
    transcript2: list = []
    rt2 = council.emit_research_turn(transcript2, "別ブリーフ", emit=None, turn_id=7)
    check(transcript2 == [rt2], "emit=None でも transcript に積む")

    # 検索前先出し: emit_research_start は turn_start だけを流す（本文未着＝UI「調べています…」）。
    ev2: list[dict] = []
    council.emit_research_start(ev2.append, turn_id=99, query="日本の出生率")
    check([e["type"] for e in ev2] == ["turn_start"], "emit_research_start は turn_start のみ")
    check(ev2[0]["speaker_id"] == "researcher" and ev2[0]["turn_id"] == 99, "turn_start は researcher/該当id")
    check(ev2[0]["query"] == "日本の出生率", "turn_start に検索クエリが載る（UI のリアルタイム表示用）")
    # 検索後: emit_start=False なら turn_start を出さず delta のみ（先出し済みのため）。
    tr3: list = []
    ev3: list[dict] = []
    council.emit_research_turn(tr3, "あとからの本文", emit=ev3.append, turn_id=99, emit_start=False)
    check([e["type"] for e in ev3] == ["delta"], "emit_start=False は delta のみ（turn_start 二重防止）")
    check(ev3[0]["text"] == "あとからの本文", "delta に本文が載る")


def test_extract_research_queries():
    """(3) _extract_research_queries が「要調査: X」を抽出（半角/全角コロン両対応）。"""
    print("[test] _extract_research_queries (要調査マーカー抽出)")

    # 半角コロン
    qs = service._extract_research_queries("本文です。\n要調査: 日本の出生率の推移")
    check(qs == ["日本の出生率の推移"], f"半角コロンを抽出: {qs}")

    # 全角コロン
    qs2 = service._extract_research_queries("要調査：競合A社の市場シェア")
    check(qs2 == ["競合A社の市場シェア"], f"全角コロンを抽出: {qs2}")

    # 複数行・余分な空白・空マーカーを除去
    qs3 = service._extract_research_queries(
        "前段\n要調査:  EV 充電インフラの普及率  \nつなぎ\n要調査：再エネ比率\n要調査:   "
    )
    check(
        qs3 == ["EV 充電インフラの普及率", "再エネ比率"],
        f"複数抽出・trim・空除去: {qs3}",
    )

    # マーカーが無ければ空
    check(service._extract_research_queries("ただの発言") == [], "マーカー無しは空 list")
    check(service._extract_research_queries("") == [], "空文字は空 list")

    # 箇条書き/強調/番号/行内（行頭限定をやめた強化分）。モデルの多様な書き方を取りこぼさない。
    check(
        service._extract_research_queries("- 要調査: 半導体の国産化率") == ["半導体の国産化率"],
        "箇条書き(- )の要調査を抽出",
    )
    check(
        service._extract_research_queries("**要調査:** 円相場の推移") == ["円相場の推移"],
        "強調(**要調査:**)を抽出",
    )
    check(
        service._extract_research_queries("1. 要調査： 生成AIの市場規模") == ["生成AIの市場規模"],
        "番号付き(1. )の要調査を抽出",
    )
    check(
        service._extract_research_queries("結論として確認が要る。要調査: 法改正の施行日")
        == ["法改正の施行日"],
        "行内(文中)の要調査を抽出",
    )


def test_research_disabled_backward_compat():
    """(4) research=False で build_context に要調査指示が出ず、従来と一致する。"""
    print("[test] research=False backward compat (要調査指示を出さない)")
    from core.context import RESEARCH_NUDGE

    a, b, c = make("a"), make("b"), make("c")
    transcript = [
        Turn("a", "A", "a-said", "発散", 0),
        Turn("b", "B", "b-said", "発散", 0),
        Turn("c", "C", "c-said", "発散", 0),
    ]

    # research_enabled 既定（False）: 要調査ナッジが出ない＝従来と完全一致
    sys_off, msg_off = build_context(transcript=transcript, active=b, topic="T")
    all_user_off = "\n".join(m["content"] for m in msg_off if m["role"] == "user")
    check(RESEARCH_NUDGE not in all_user_off, "research_enabled=False で要調査指示を出さない")

    # 明示 False も既定と完全一致（後方互換）
    sys_expl, msg_expl = build_context(
        transcript=transcript, active=b, topic="T", research_enabled=False
    )
    check(
        [m["content"] for m in msg_off] == [m["content"] for m in msg_expl],
        "research_enabled 既定 == 明示 False（従来一致）",
    )

    # research_enabled=True のときだけナッジが入る
    sys_on, msg_on = build_context(
        transcript=transcript, active=b, topic="T", research_enabled=True
    )
    all_user_on = "\n".join(m["content"] for m in msg_on if m["role"] == "user")
    check(RESEARCH_NUDGE in all_user_on, "research_enabled=True で要調査指示が入る")

    # Council.research=False のとき _speak が要調査指示を出さない（既定と同じ発言列）
    from core import Council, MockLLMClient

    def build(research):
        return Council(
            [make("mod", cat="facilitation"), make("logic"), make("idea"),
             make("chair", cat="chair")],
            MockLLMClient(),
            phases=[("発散", "d", True)], rounds_per_phase=1,
            research=research,
        )

    off = build(False)
    list(off.run("議題NR"))
    off_clean = all(
        RESEARCH_NUDGE not in "\n".join(m["content"] for m in call["messages"])
        for call in off.client.calls
    )
    check(off_clean, "research=False の Council は全 LLM 呼び出しに要調査指示を含めない")

    on = build(True)
    list(on.run("議題NR"))
    on_seen = any(
        RESEARCH_NUDGE in "\n".join(m["content"] for m in call["messages"])
        for call in on.client.calls
    )
    check(on_seen, "research=True の Council は LLM 呼び出しに要調査指示を含める")

    # build_council の research 既定は False（後方互換）
    council_default = service.build_council(
        ["moderator", "logic", "idea", "chair"], rounds_per_phase=1, mock=True
    )
    check(council_default.research is False, "build_council の research 既定は False（後方互換）")
    council_on = service.build_council(
        ["moderator", "logic", "idea", "chair"], rounds_per_phase=1, mock=True, research=True
    )
    check(council_on.research is True, "build_council(research=True) が Council に届く")


def test_api_auth_token():
    """デプロイ用最小認証（env-gated）: token 未設定で従来動作・設定時は Bearer 必須。

    - AI_TEAMS_API_TOKEN 未設定 → 認証無効（全エンドポイントが従来どおり通る）。
    - 設定あり → Bearer 無し/不一致は 401、正しい Bearer は通る。
      ただし /health は無認証 200、OPTIONS（CORS プリフライト）は常に通る。
    """
    print("[test] api auth token (env-gated minimal auth)")
    import os

    from fastapi.testclient import TestClient

    from api.main import app

    saved = os.environ.get("AI_TEAMS_API_TOKEN")
    client = TestClient(app)
    try:
        # 1. token 未設定 → 認証無効（従来どおり全エンドポイントが動く）
        os.environ.pop("AI_TEAMS_API_TOKEN", None)
        r = client.get("/health")
        check(r.status_code == 200, f"token 未設定で /health 200: {r.status_code}")
        r = client.get("/personas")
        check(r.status_code == 200, f"token 未設定で GET /personas 200: {r.status_code}")
        # POST /sessions（mock）は token 未設定なら 200 で SSE を返す
        r = client.post(
            "/sessions",
            json={
                "topic": "認証テスト議題",
                "persona_ids": ["moderator", "logic", "idea", "chair"],
                "mock": True,
                "interactive": False,
            },
        )
        check(r.status_code == 200, f"token 未設定で POST /sessions 200: {r.status_code}")

        # 2. token 設定 → Bearer 必須
        token = "deploy-secret-token-xyz"
        os.environ["AI_TEAMS_API_TOKEN"] = token

        # Bearer 無しの GET /personas は 401
        r = client.get("/personas")
        check(r.status_code == 401, f"token 設定・Bearer 無しの GET /personas は 401: {r.status_code}")
        check(r.json() == {"detail": "unauthorized"}, f"401 body は unauthorized: {r.json()}")

        # Bearer 無しの POST /sessions も 401（ボディ検証より前に弾く）
        r = client.post(
            "/sessions",
            json={
                "topic": "認証テスト議題",
                "persona_ids": ["moderator", "logic", "idea", "chair"],
                "mock": True,
                "interactive": False,
            },
        )
        check(r.status_code == 401, f"token 設定・Bearer 無しの POST /sessions は 401: {r.status_code}")

        # 誤った token は 401
        r = client.get("/personas", headers={"Authorization": "Bearer wrong-token"})
        check(r.status_code == 401, f"誤 Bearer は 401: {r.status_code}")

        # 正しい Bearer は通る
        r = client.get("/personas", headers={"Authorization": f"Bearer {token}"})
        check(r.status_code == 200, f"正しい Bearer の GET /personas は 200: {r.status_code}")
        r = client.post(
            "/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "topic": "認証テスト議題",
                "persona_ids": ["moderator", "logic", "idea", "chair"],
                "mock": True,
                "interactive": False,
            },
        )
        check(r.status_code == 200, f"正しい Bearer の POST /sessions は 200: {r.status_code}")

        # 3. /health は token 設定時も無認証で 200（稼働確認のため除外）
        r = client.get("/health")
        check(r.status_code == 200, f"token 設定でも /health は無認証 200: {r.status_code}")

        # 4. OPTIONS（CORS プリフライト）は token 設定時も通る（401 にしない）
        r = client.options(
            "/personas",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        check(r.status_code != 401, f"OPTIONS プリフライトは 401 にしない: {r.status_code}")
    finally:
        if saved is None:
            os.environ.pop("AI_TEAMS_API_TOKEN", None)
        else:
            os.environ["AI_TEAMS_API_TOKEN"] = saved


def test_byok_http_guards():
    """HTTP: BYOK で実LLM要求にキー必須(400)、mock は不要(200)、readonly で CRUD 403。"""
    print("[test] BYOK http guards (400 no-key / 200 mock / 403 readonly)")
    import os

    from fastapi.testclient import TestClient

    from api.main import app

    saved_byok = os.environ.get("AI_TEAMS_BYOK")
    saved_ro = os.environ.get("AI_TEAMS_READONLY")
    saved_tok = os.environ.get("AI_TEAMS_API_TOKEN")
    client = TestClient(app)
    sess = {
        "topic": "BYOK議題",
        "persona_ids": ["moderator", "logic", "idea", "chair"],
        "interactive": False,
    }
    try:
        os.environ.pop("AI_TEAMS_API_TOKEN", None)  # 認証は別テスト。ここは BYOK 挙動に集中
        os.environ["AI_TEAMS_BYOK"] = "1"
        # 実 LLM（mock:false）＋キー未提供 → 400
        r = client.post("/sessions", json={**sess, "mock": False})
        check(r.status_code == 400, f"BYOK・実LLM・キー無しは 400: {r.status_code}")
        # mock:true はキー不要で 200（プレビュー）
        r = client.post("/sessions", json={**sess, "mock": True})
        check(r.status_code == 200, f"BYOK でも mock:true は 200: {r.status_code}")
        # intake も同様（mock:false・キー無し → 400）
        r = client.post("/intake", json={"topic": "x", "mock": False})
        check(r.status_code == 400, f"BYOK・intake・キー無しは 400: {r.status_code}")
        # readonly: 編成の書込は 403
        os.environ["AI_TEAMS_READONLY"] = "1"
        r = client.post(
            "/personas",
            json={"id": "ro", "display_name": "RO", "system_prompt": "p", "category": "thinking"},
        )
        check(r.status_code == 403, f"readonly で POST /personas は 403: {r.status_code}")
    finally:
        for k, v in (
            ("AI_TEAMS_BYOK", saved_byok),
            ("AI_TEAMS_READONLY", saved_ro),
            ("AI_TEAMS_API_TOKEN", saved_tok),
        ):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_cors_allowed_origins_env():
    """CORS allow_origins が env AI_TEAMS_ALLOWED_ORIGINS（カンマ区切り）で可変。

    未設定なら既定 ["http://localhost:3000"]（後方互換）。
    """
    print("[test] cors allowed origins (env-configurable)")
    import os

    from api.main import _allowed_origins

    saved = os.environ.get("AI_TEAMS_ALLOWED_ORIGINS")
    try:
        # 1. 未設定 → 既定
        os.environ.pop("AI_TEAMS_ALLOWED_ORIGINS", None)
        check(
            _allowed_origins() == ["http://localhost:3000"],
            f"env 未設定で既定 localhost:3000: {_allowed_origins()}",
        )

        # 2. カンマ区切りで複数 origin（空白 trim・空要素除去）
        os.environ["AI_TEAMS_ALLOWED_ORIGINS"] = "https://app.example.com, https://admin.example.com ,"
        check(
            _allowed_origins() == ["https://app.example.com", "https://admin.example.com"],
            f"カンマ区切りを trim して list 化: {_allowed_origins()}",
        )

        # 3. 空文字なら既定にフォールバック
        os.environ["AI_TEAMS_ALLOWED_ORIGINS"] = "   "
        check(
            _allowed_origins() == ["http://localhost:3000"],
            f"空白のみは既定にフォールバック: {_allowed_origins()}",
        )
    finally:
        if saved is None:
            os.environ.pop("AI_TEAMS_ALLOWED_ORIGINS", None)
        else:
            os.environ["AI_TEAMS_ALLOWED_ORIGINS"] = saved


# ---------------------------------------------------------------------------
def test_relationships():
    """偉人の因縁: 相手が同席する討論でだけ system に因縁ブロックを注入する。"""
    print("[test] relationships (因縁の文脈注入)")
    from core import Council, MockLLMClient, Persona, build_context

    a = Persona(id="a", display_name="アルファ", system_prompt="A です。",
                relationships=[{"to": "b", "type": "rival", "note": "宿敵"}])
    b = Persona(id="b", display_name="ベータ", system_prompt="B です。")
    c = Persona(id="c", display_name="ガンマ", system_prompt="C です。")
    mod = Persona(id="mod", display_name="司会", system_prompt="進行", category="facilitation")
    chair = Persona(id="chair", display_name="議長", system_prompt="まとめ", category="chair")

    # 1. 相手(b)同席 → a に因縁文が立つ。因縁を持たない b には立たない。
    co = Council([mod, a, b, chair], MockLLMClient(),
                 phases=[("発散", "d", True)], rounds_per_phase=1)
    check("a" in co._roster_notes, "相手同席で a に因縁文が立つ")
    check("ベータ" in co._roster_notes["a"], "因縁文に相手の表示名が入る")
    check("宿敵" in co._roster_notes["a"], "因縁文に note が入る")
    check("b" not in co._roster_notes, "因縁を持たない b には立たない")

    # 2. 相手(b)不在 → 注入しない（無関係な討論では従来同一）。
    solo = Council([mod, a, c, chair], MockLLMClient(),
                   phases=[("発散", "d", True)], rounds_per_phase=1)
    check("a" not in solo._roster_notes, "相手不在なら因縁を注入しない")

    # 3. build_context: roster_note を渡すと system 末尾に付く。空なら system 不変（後方互換）。
    sys_with, _ = build_context(transcript=[], active=a, topic="T", roster_note="【因縁】X")
    check(sys_with.endswith("【因縁】X"), "roster_note が system 末尾に付く")
    sys_without, _ = build_context(transcript=[], active=a, topic="T")
    check(sys_without == a.system_prompt, "roster_note 無しは system 不変（後方互換）")

    # 4. 不正な relationship は弾く（type 不正 / to 欠落）。
    try:
        Persona(id="x", display_name="X", system_prompt="x",
                relationships=[{"to": "b", "type": "foe"}])
        check(False, "不正な relationship type を弾く")
    except ValueError:
        check(True, "不正な relationship type を弾く")


def test_persona_upsert_relationships():
    """編集保存で因縁が消えない回帰: PersonaUpsert が relationships を model_dump に通す。"""
    print("[test] PersonaUpsert relationships round-trip (因縁の編集保存)")
    from api.main import PersonaUpsert

    u = PersonaUpsert(
        id="x",
        display_name="X",
        system_prompt="x",
        category="thinking",
        relationships=[{"to": "rival_y", "type": "rival", "note": "宿敵"}],
    )
    d = u.model_dump()
    check("relationships" in d, "model_dump に relationships が含まれる（extra=ignore で消えない）")
    check(len(d["relationships"]) == 1, "relationships が1件保持される")
    check(d["relationships"][0]["to"] == "rival_y", "relationship の to が往復する")
    check(d["relationships"][0]["type"] == "rival", "relationship の type が往復する")
    # 不正な type は弾く（Literal 検証）
    try:
        PersonaUpsert(
            id="x", display_name="X", system_prompt="x", category="thinking",
            relationships=[{"to": "y", "type": "foe"}],
        )
        check(False, "不正な relationship type を弾く")
    except Exception:
        check(True, "不正な relationship type を弾く")


if __name__ == "__main__":
    test_context_isolation()
    test_relationships()
    test_persona_upsert_relationships()
    test_no_silence_and_round_robin()
    test_model_override()
    test_persona_public()
    test_sse_stream()
    test_red_team()
    test_synthesis_only()
    test_streaming()
    test_session_transport()
    test_followup_injection()
    test_llm_status()
    test_byok_make_client()
    test_verbosity()
    test_provider_params()
    test_local_provider()
    test_synthesis_max_tokens()
    test_custom_personas()
    test_persona_service_crud()
    test_preset_service()
    test_http_api()
    test_followup_e2e()
    test_floor_open_pause()
    test_floor_open_close_then_finish()
    test_run_backward_compat()
    test_materials_in_context()
    test_intake_questions()
    test_materials_propagation_e2e()
    test_web_research_mock()
    test_research_turn_emit()
    test_extract_research_queries()
    test_research_disabled_backward_compat()
    test_api_auth_token()
    test_byok_http_guards()
    test_cors_allowed_origins_env()
    print()
    if _failures:
        print(f"[FAIL] {len(_failures)} 件 FAIL")
        sys.exit(1)
    print("[OK] 全テスト pass")
