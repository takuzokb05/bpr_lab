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
    # 司会1 + パネリスト3 + 議長1 = 5（1フェーズ×1ラウンド）。デフォルト3フェーズなので
    # ここではフェーズ既定のまま: opening1 + (3人×3フェーズ) + synthesis1 = 11
    check(len(turns) == 11, f"turn 数が想定どおり: {len(turns)}")

    # data 行の JSON 検証（最初の turn）
    data_line = [ln for ln in turns[0].splitlines() if ln.startswith("data: ")][0]
    payload = json.loads(data_line.removeprefix("data: "))
    for key in ("speaker_id", "speaker_name", "content", "phase", "round"):
        check(key in payload, f"turn payload に {key} が含まれる")
    check(payload["speaker_id"] == "moderator", "先頭 turn は司会")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_context_isolation()
    test_no_silence_and_round_robin()
    test_model_override()
    test_persona_public()
    test_sse_stream()
    print()
    if _failures:
        print(f"❌ {len(_failures)} 件 FAIL")
        sys.exit(1)
    print("✅ 全テスト pass")
