"""討論オーケストレーター（UI 非依存・ジェネレータ）。

設計の柱（根拠は ../RESEARCH_2026-05_orchestration.md）:
  - 発言順は LLM ではなく **コードのラウンドロビン** が決める → 沈黙エージェントを構造的に排除
  - 各発言は `build_context` で **コンテキスト分離** → 人格混線を排除
  - 反同調プロンプト＋ペルソナ毎ターン再注入 → 均質化 / fidelity decay を抑制
  - 司会オープニング → 発散 → 批判 → 収束 → 議長統合（chairman）の構造化進行
  - run() は Turn を1件ずつ yield する純粋なジェネレータ（UI は描画に専念できる）
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Callable, Iterator, Sequence

# 追い質問ラウンドで各パネリストに前置きする指示。本編ローテーションを乱さないよう、
# 順序を list(self.panelists) で固定し（scheduler.order() は使わない）、まずこの質問に
# 答えてから本編に戻る、という流れを作る。
FOLLOWUP_DIRECTIVE = (
    "【追い質問対応】司会が今読み上げた人間からの追い質問に、"
    "まずあなたの立場から要点を絞って答えてください"
    "（目安: 最も強い論点1〜2つ。過度な箇条書きや見出しで水増ししない）。"
    "その上で、これまでの議論とのつながりを一言添えること。"
)

from .context import build_context
from .llm_client import DEFAULT_MODEL, LLMClient
from .personas import Persona


@dataclass
class Turn:
    """確定した1発言。"""

    speaker_id: str
    speaker_name: str
    content: str
    phase: str
    round: int
    # ストリーミング/再接続用の単調増加 ID。run() が採番する（非ストリーム経路でも付与）。
    turn_id: int | None = None


# emit に流すイベント（turn_start / delta）。turn_end は呼び出し側が出す（設計 v2）。
Emit = Callable[[dict], None]

# 未処理の人間メッセージ（追い質問など）を drain して返すコールバック。
# 返り値は .text / .target を持つオブジェクトの列（api.service.HumanMessage を import せず
# duck typing で扱う＝core を API 層に依存させない）。pull=None なら従来動作（注入なし）。
Pull = Callable[[], list]


# Red Team（反対役）への追加指示。指名されたパネリストの発言時に毎ターン注入する。
# 同調バイアス対策（研究: 討論を放置すると同調で精度が下がる）として、最低1名の
# 反論を構造的に保証する。
RED_TEAM_DIRECTIVE = (
    "【あなたの特命: Red Team（反対役）】"
    "あなたはこの討論で意図的に反対の立場を取る担当です。"
    "多数派や心地よい結論に流されず、最も強い反証・最悪のシナリオ・"
    "見落とされている前提を必ず1つ提示してください。"
    "全員が賛成していても、あえて穴を探すのがあなたの責務です。"
)

# 収束フェーズ専用の Red Team 特命。反対役は降りないが、穴を突いて終わらず
# 「塞ぐ最小条件（これを満たすなら進めてよい）」まで示させ、意思決定を前に進める。
RED_TEAM_CONVERGE_DIRECTIVE = (
    "【あなたの特命: Red Team（収束）】"
    "最後まで反対役を降りる必要はありません。ただし収束フェーズでは、"
    "最も強い反証を1つ突いた上で、その反証を踏まえてもなお実行に値する"
    "『条件付きの一手』（これを満たすなら進めてよい、という具体的な前提条件）を"
    "必ず1つ提示してください。穴を指摘して終わるのではなく、穴を塞ぐ最小条件を示すこと。"
)


# (フェーズ名, 指示, 反同調を効かせるか) のデフォルト進行。
DEFAULT_PHASES: list[tuple[str, str, bool]] = [
    (
        "発散",
        "【発散フェーズ】既出の案に乗らず、新しい角度・対案・突飛な視点を出してください。"
        "幅を広げるのが目的で、深掘りや合意はまだ早い。突飛でよいが、各案に"
        "「これが成立する前提」または「これが崩れる条件」を一言添え、後続の批判フェーズが"
        "噛めるフックを残すこと。",
        True,
    ),
    (
        "批判",
        "【批判フェーズ】新しい案を出すのは止め、既出の案の致命的欠陥・リスク・矛盾を"
        "具体的に突いてください（Devil's Advocate）。",
        True,
    ),
    (
        "収束",
        "【収束フェーズ】批判に耐えた案を統合し、具体的なアクションに落としてください。",
        False,
    ),
]


class RoundRobinScheduler:
    """ラウンドロビン。各ラウンドで全パネリストがちょうど1回発言する＝沈黙が起きない。

    ラウンドごとに開始位置を1つ回し、毎回同じ人が口火を切らないようにする。
    """

    def __init__(self, panelists: Sequence[Persona]) -> None:
        self._panelists = list(panelists)
        self._round_index = 0

    def order(self) -> list[Persona]:
        n = len(self._panelists)
        if n == 0:
            return []
        start = self._round_index % n
        self._round_index += 1
        return self._panelists[start:] + self._panelists[:start]


class Council:
    """討論セッション1回分のオーケストレーター。"""

    def __init__(
        self,
        personas: Sequence[Persona],
        client: LLMClient,
        *,
        default_model: str = DEFAULT_MODEL,
        default_temperature: float = 0.7,
        phases: list[tuple[str, str, bool]] | None = None,
        rounds_per_phase: int = 1,
        red_team: bool = True,
        red_team_id: str | None = None,
        materials: str = "",
        research: bool = False,
    ) -> None:
        self.client = client
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.phases = phases if phases is not None else DEFAULT_PHASES
        self.rounds_per_phase = rounds_per_phase
        # 全ペルソナが共有する「資料・前提」。セッション中は不変（構築時に確定）。
        # _speak が build_context に渡す。"" のとき従来と完全同一（ブロックを足さない）。
        self.materials = materials
        # Web 検索（調査役）を有効にするか。True のとき各ペルソナの末尾ナッジに
        # 「要調査: …」を書いてよい指示を足し、producer がそのマーカーを拾って調査役が
        # 調べ、researcher ターンとして全員に共有する。False では一切何もしない（後方互換）。
        self.research = research

        personas = list(personas)
        # 役割ごとに振り分ける
        self.moderator = next((p for p in personas if p.category == "facilitation"), None)
        self.chair = next((p for p in personas if p.category == "chair"), None)
        # パネリスト = 発言する人のうち、司会・議長・書記（speaks=False）を除いた面々
        self.panelists = [
            p
            for p in personas
            if p.speaks and p.category not in ("facilitation", "chair", "scribe")
        ]
        if not self.panelists:
            raise ValueError("パネリストが0人です。thinking/founders/philosophers のペルソナが必要です。")
        self.scheduler = RoundRobinScheduler(self.panelists)

        # red_team_id の妥当性はフラグと独立に検証する（red_team=False でも不正 id は
        # サイレント無視せず弾く＝同一入力で挙動が割れない）。
        if red_team_id is not None and not any(p.id == red_team_id for p in self.panelists):
            raise ValueError(f"red_team_id '{red_team_id}' はパネリストにいません")
        # Red Team（反対役）の選定。明示指定が無ければ先頭パネリストを充てる。
        # 1人しかいない討論では反対役を立てない（全員反対では討論にならない）。
        self.red_team_id: str | None = None
        if red_team and len(self.panelists) >= 2:
            self.red_team_id = red_team_id if red_team_id is not None else self.panelists[0].id

    # -- 内部ヘルパ --------------------------------------------------------
    def _resolve(self, persona: Persona) -> tuple[str, float]:
        """ペルソナ指定があればそれを、無ければエンジン既定の (model, temperature)。"""
        model = persona.model or self.default_model
        temperature = (
            persona.temperature if persona.temperature is not None else self.default_temperature
        )
        return model, temperature

    def _speak(
        self,
        persona: Persona,
        transcript: list[Turn],
        topic: str,
        phase: str,
        round_no: int,
        *,
        phase_directive: str,
        anti_conformity: bool,
        emit: Emit | None = None,
        turn_id: int | None = None,
    ) -> Turn:
        # Red Team に指名されたパネリストには、毎ターン反対役の特命を上乗せする。
        # 収束フェーズだけは「穴突き＋塞ぐ最小条件」版に切替える（phase 名は DEFAULT_PHASES と一致）。
        if persona.id == self.red_team_id:
            rt = RED_TEAM_CONVERGE_DIRECTIVE if phase == "収束" else RED_TEAM_DIRECTIVE
            phase_directive = f"{phase_directive}\n\n{rt}"
        system, messages = build_context(
            transcript=transcript,
            active=persona,
            topic=topic,
            phase_directive=phase_directive,
            anti_conformity=anti_conformity,
            materials=self.materials,
            research_enabled=self.research,
        )
        model, temperature = self._resolve(persona)

        if emit is None:
            # 後方互換: 一括生成して Turn だけを返す（既存テストはこの経路）。
            content = self.client.generate(
                system=system, messages=messages, model=model, temperature=temperature
            )
        else:
            # ストリーミング経路: turn_start → delta* を emit しつつ全文を蓄積。
            # turn_end は呼び出し側（API 層）が yield 後に出す（設計 v2）。
            emit(
                {
                    "type": "turn_start",
                    "turn_id": turn_id,
                    "speaker_id": persona.id,
                    "speaker_name": persona.display_name,
                    "phase": phase,
                    "round": round_no,
                }
            )
            parts: list[str] = []
            for chunk in self.client.generate_stream(
                system=system, messages=messages, model=model, temperature=temperature
            ):
                parts.append(chunk)
                emit({"type": "delta", "turn_id": turn_id, "text": chunk})
            content = "".join(parts).strip()
        return Turn(persona.id, persona.display_name, content, phase, round_no, turn_id=turn_id)

    def _emit_simple_turn(
        self,
        *,
        speaker_id: str,
        speaker_name: str,
        content: str,
        phase: str,
        round_no: int,
        emit: Emit | None,
        turn_id: int,
    ) -> Turn:
        """LLM を呼ばずに、与えられた本文をそのまま1ターンとして流す。

        人間ターン（追い質問のエコー）に使う。emit があれば turn_start → delta（全文を
        1チャンク）を流す。turn_end は呼び出し側（_produce）が出すので、ここでは出さない
        （二重防止）。Turn を返す（呼び出し側が transcript に積む）。
        """
        if emit is not None:
            emit(
                {
                    "type": "turn_start",
                    "turn_id": turn_id,
                    "speaker_id": speaker_id,
                    "speaker_name": speaker_name,
                    "phase": phase,
                    "round": round_no,
                }
            )
            emit({"type": "delta", "turn_id": turn_id, "text": content})
        return Turn(speaker_id, speaker_name, content, phase, round_no, turn_id=turn_id)

    def emit_research_turn(
        self,
        transcript: list[Turn],
        brief: str,
        *,
        emit: Emit | None,
        turn_id: int,
    ) -> Turn:
        """調査役（researcher）の調査結果ブリーフを1ターンとして流し、transcript に積む。

        LLM は呼ばない（brief は呼び出し側＝producer が run_research で取得済み）。
        emit があれば turn_start{speaker_id:"researcher", speaker_name:"調査",
        phase:"research", round:0} → delta{text:brief（全文1チャンク）} を流す。
        turn_end は呼び出し側（_produce）が出す（_emit_simple_turn と同形・二重防止）。
        新しい SSE イベント型は増やさず、調査を1人の話者のターンとして討論に乗せる
        ことで全員が共有する。Turn は transcript に append してから返す。
        """
        if emit is not None:
            emit(
                {
                    "type": "turn_start",
                    "turn_id": turn_id,
                    "speaker_id": "researcher",
                    "speaker_name": "調査",
                    "phase": "research",
                    "round": 0,
                }
            )
            emit({"type": "delta", "turn_id": turn_id, "text": brief})
        turn = Turn("researcher", "調査", brief, "research", 0, turn_id=turn_id)
        transcript.append(turn)
        return turn

    def deepen(
        self,
        topic: str,
        transcript: list[Turn],
        msgs: Sequence,
        *,
        emit: Emit | None = None,
        ids: "count[int]",
    ) -> Iterator[Turn]:
        """人間ターン(msgs)→司会再提示→パネリスト1周の「深掘り1周」を yield する公開メソッド。

        本編中の追い質問注入（_drain_and_inject）と floor-open 中の deepen で共有する。
        msgs は .text を持つオブジェクトの列（duck typing）。空なら何もしない。
          (a) 各追い質問を「人間ターン」として transcript に積み yield（LLM 不使用）。
          (b) 司会在席時のみ、司会が再提示する followup ターンを生成・yield。
          (c) list(self.panelists) を **本編とは独立に1周** し、followup directive 前置きで
              各パネリストに答えさせる（順序固定でローテーションを乱さない）。Red Team 指名者
              には _speak が自動で反対役の特命を上乗せする。
        複数の追い質問は 1 ラウンドに束ねて処理する（(a) で全件積んでから (b)(c) は1回）。
        turn_id は呼び出し側が所有する ids=count() を共有して継続採番する。
        round_no は人間入力起点の深掘りなので 0 固定（本編ラウンドとは独立）。
        """
        msgs = list(msgs)
        if not msgs:
            return
        round_no = 0

        # (a) 人間ターン（追い質問のエコー）を順に積む。
        for msg in msgs:
            text = getattr(msg, "text", "") or ""
            human = self._emit_simple_turn(
                speaker_id="human",
                speaker_name="あなた",
                content=text,
                phase="human",
                round_no=round_no,
                emit=emit,
                turn_id=next(ids),
            )
            transcript.append(human)
            yield human

        # (b) 司会が在席していれば、追い質問を討論に投げ直す（再提示）。
        if self.moderator is not None:
            questions = "\n".join(f"- {getattr(m, 'text', '') or ''}" for m in msgs)
            mod_turn = self._speak(
                self.moderator,
                transcript,
                topic,
                phase="followup",
                round_no=round_no,
                phase_directive=(
                    "【追い質問の取り次ぎ】視聴者（人間）から次の追い質問が入りました。"
                    "パネリストに分かるよう簡潔に取り次ぎ、これに答えるよう促してください。"
                    "あなた自身が答えてしまわないこと。論点を増やさず、質問をそのまま簡潔に"
                    "取り次ぐこと（自分で論点を3つに展開しない）。\n" + questions
                ),
                anti_conformity=False,
                emit=emit,
                turn_id=next(ids),
            )
            transcript.append(mod_turn)
            yield mod_turn

        # (c) パネリスト全員が1周して追い質問に答える（順序固定＝本編ローテーション不変）。
        for persona in list(self.panelists):
            turn = self._speak(
                persona,
                transcript,
                topic,
                phase="followup",
                round_no=round_no,
                phase_directive=FOLLOWUP_DIRECTIVE,
                anti_conformity=False,
                emit=emit,
                turn_id=next(ids),
            )
            transcript.append(turn)
            yield turn

    def _drain_and_inject(
        self,
        transcript: list[Turn],
        topic: str,
        *,
        emit: Emit | None,
        ids: "count[int]",
        pull: Pull | None,
    ) -> Iterator[Turn]:
        """本編フェーズの各 Turn 直後に呼ばれ、溜まった追い質問を注入する薄いラッパ。

        pull=None なら何もしない（従来動作＝既存テストはこの経路）。pull() が空なら
        即 return。来ていたら deepen() に委譲する（人間ターン→司会再提示→パネリスト1周）。
        """
        if pull is None:
            return
        msgs = pull()
        if not msgs:
            return
        yield from self.deepen(topic, transcript, msgs, emit=emit, ids=ids)

    # -- 公開 API ----------------------------------------------------------
    def deliberate(
        self,
        topic: str,
        transcript: list[Turn],
        *,
        emit: Emit | None = None,
        pull: Pull | None = None,
        ids: "count[int]",
    ) -> Iterator[Turn]:
        """opening＋本編フェーズ（発散/批判/収束）を進行し Turn を yield する。synthesis はやらない。

        transcript と ids（採番カウンタ）は呼び出し側が所有・共有する（floor-open ループで
        deepen/synthesize と transcript・採番を継続させるため）。

        emit を渡すと各発言を turn_start → delta* のイベント列として流す（ストリーミング経路）。
        emit=None なら一括生成し Turn だけを yield する（後方互換）。

        pull を渡すと、本編フェーズの各 Turn 直後に追い質問を drain して注入する
        （人間ターン → 司会再提示 → パネリスト1周）。pull=None なら従来動作（注入なし）。
        opening では拾わない。
        """
        # 1. 司会オープニング（任意）
        if self.moderator is not None:
            turn = self._speak(
                self.moderator,
                transcript,
                topic,
                phase="opening",
                round_no=0,
                phase_directive=(
                    "【オープニング】議題を一言で整理し、論点を2〜3つ提示して討論の口火を切って"
                    "ください。結論は出さず、最後に特定の立場の人へ発言を促すこと。"
                ),
                anti_conformity=False,
                emit=emit,
                turn_id=next(ids),
            )
            transcript.append(turn)
            yield turn

        # 2. フェーズ進行（各ラウンドでラウンドロビン＝全員必ず発言）
        for phase_name, directive, anti in self.phases:
            for round_no in range(self.rounds_per_phase):
                for persona in self.scheduler.order():
                    turn = self._speak(
                        persona,
                        transcript,
                        topic,
                        phase=phase_name,
                        round_no=round_no,
                        phase_directive=directive,
                        anti_conformity=anti,
                        emit=emit,
                        turn_id=next(ids),
                    )
                    transcript.append(turn)
                    yield turn
                    # 本編フェーズの各 Turn 直後にだけ追い質問を拾う（pull=None なら no-op）。
                    yield from self._drain_and_inject(
                        transcript, topic, emit=emit, ids=ids, pull=pull
                    )

    def synthesize(
        self,
        topic: str,
        transcript: list[Turn],
        *,
        emit: Emit | None = None,
        ids: "count[int]",
    ) -> Iterator[Turn]:
        """議長による統合（議事録）ターンを1つ yield する。chair が無ければ司会が兼任。

        かつて 3行エグゼクティブサマリ(summary フェーズ)を別に出していたが、実 LLM が
        3行指示を守らず議事録と重複した上、短すぎて読まれないため廃止。議事録1枚に集約する。
        synthesizer（chair も moderator も）が居なければ何も yield しない。
        transcript と ids は呼び出し側が所有・共有する。
        """
        synthesizer = self.chair or self.moderator
        if synthesizer is None:
            return
        # 議事録（合意/対立/リスク/アクション）。
        turn = self._speak(
            synthesizer,
            transcript,
            topic,
            phase="synthesis",
            round_no=0,
            phase_directive=(
                "【統合】これまでの議論を、合意点 / 対立が残った点 / 主要リスク / "
                "ネクストアクション の4見出しで簡潔に1枚にまとめてください。"
                "新しい意見は足さず、出た議論だけを統合すること。"
            ),
            anti_conformity=False,
            emit=emit,
            turn_id=next(ids),
        )
        transcript.append(turn)
        yield turn

    def run(self, topic: str, *, emit: Emit | None = None, pull: Pull | None = None) -> Iterator[Turn]:
        """討論を進行し、確定した Turn を1件ずつ yield する（後方互換の自動完走経路）。

        deliberate（opening+本編）→ synthesize（議事録）の合成。ids=count() と transcript=[]
        をこの中で所有するので、従来と完全に同一の出力（opening+本編+synthesis）になる。

        emit を渡すと各発言を turn_start → delta* のイベント列として流す（ストリーミング経路）。
        emit=None なら従来どおり一括生成し Turn だけを yield する。turn_id は両経路で採番する。

        pull を渡すと本編フェーズの各 Turn 直後に追い質問を drain して注入する。pull=None なら
        従来動作（注入なし）。opening/synthesis では拾わない。
        """
        transcript: list[Turn] = []
        ids = count()  # turn_id の採番（単調増加。deliberate→synthesize で継続）
        yield from self.deliberate(topic, transcript, emit=emit, pull=pull, ids=ids)
        yield from self.synthesize(topic, transcript, emit=emit, ids=ids)
