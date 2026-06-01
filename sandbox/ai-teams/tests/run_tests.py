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
    # opening1 + (3人×3フェーズ=9) + synthesis1 = 11（summary 廃止後）
    check(len(turns) == 11, f"turn 数が想定どおり: {len(turns)}")

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
        st = service.llm_status()
        check(st == {"llm": "mock", "api_key_set": False}, f"キー未設定で mock: {st}")
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


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_context_isolation()
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
    test_persona_service_crud()
    test_preset_service()
    test_http_api()
    test_followup_e2e()
    print()
    if _failures:
        print(f"[FAIL] {len(_failures)} 件 FAIL")
        sys.exit(1)
    print("[OK] 全テスト pass")
