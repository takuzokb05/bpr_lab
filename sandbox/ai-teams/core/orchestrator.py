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
from typing import Iterator, Sequence

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


# (フェーズ名, 指示, 反同調を効かせるか) のデフォルト進行。
DEFAULT_PHASES: list[tuple[str, str, bool]] = [
    (
        "発散",
        "【発散フェーズ】既出の案に乗らず、新しい角度・対案・突飛な視点を出してください。"
        "幅を広げるのが目的で、深掘りや合意はまだ早い。",
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
    ) -> None:
        self.client = client
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.phases = phases if phases is not None else DEFAULT_PHASES
        self.rounds_per_phase = rounds_per_phase

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

    # -- 内部ヘルパ --------------------------------------------------------
    def _call(self, persona: Persona, system: str, messages: list[dict[str, str]]) -> str:
        model = persona.model or self.default_model
        temperature = (
            persona.temperature if persona.temperature is not None else self.default_temperature
        )
        return self.client.generate(
            system=system, messages=messages, model=model, temperature=temperature
        )

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
    ) -> Turn:
        system, messages = build_context(
            transcript=transcript,
            active=persona,
            topic=topic,
            phase_directive=phase_directive,
            anti_conformity=anti_conformity,
        )
        content = self._call(persona, system, messages)
        return Turn(persona.id, persona.display_name, content, phase, round_no)

    # -- 公開 API ----------------------------------------------------------
    def run(self, topic: str) -> Iterator[Turn]:
        """討論を進行し、確定した Turn を1件ずつ yield する。"""
        transcript: list[Turn] = []

        # 1. 司会オープニング（任意）
        if self.moderator is not None:
            turn = self._speak(
                self.moderator,
                transcript,
                topic,
                phase="opening",
                round_no=0,
                phase_directive=(
                    "【オープニング】議題を一言で整理し、論点を提示して討論の口火を切ってください。"
                    "結論は出さないこと。"
                ),
                anti_conformity=False,
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
                    )
                    transcript.append(turn)
                    yield turn

        # 3. 議長による統合（chairman パターン）。chair が無ければ司会が兼任。
        synthesizer = self.chair or self.moderator
        if synthesizer is not None:
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
            )
            transcript.append(turn)
            yield turn
