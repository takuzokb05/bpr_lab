"""コンテキスト・ビルダー（人格混線の根治）。

v2 の致命傷は「全員の発言を role=assistant で1配列に詰め、モデルに多人格ログを
自分の発言として読ませた」こと。AutoGen 方式に倣い、発言を生成するペルソナから見て:

  - 自分の過去発言 … role="assistant"（自分の声）
  - 他者の発言     … role="user" に【名前】付きで提示（外から来た入力）

とすることで、モデルが他人の人格を自分の声として継続しにくくする。
さらに毎回 system にペルソナ定義を入れ直す（長対話での fidelity decay 対策）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # 循環 import 回避（型注釈のみ）
    from .orchestrator import Turn
    from .personas import Persona

Message = dict[str, str]

# 既出に流されないための反同調ディレクティブ（collapse / echo chamber 対策）。
ANTI_CONFORMITY = (
    "安易に同意しないこと。既出の意見と異なる角度・反論・"
    "見落とされている論点を、必ず最低1つ含めること。"
)


def _merge(events: list[tuple[str, str]]) -> list[Message]:
    """連続する同一 role を1メッセージに結合する（Anthropic の role 交互制約に適合）。"""
    merged: list[list[str]] = []
    for role, text in events:
        if merged and merged[-1][0] == role:
            merged[-1][1] = merged[-1][1] + "\n\n" + text
        else:
            merged.append([role, text])
    return [{"role": r, "content": c} for r, c in merged]


def build_context(
    *,
    transcript: list["Turn"],
    active: "Persona",
    topic: str,
    phase_directive: str = "",
    anti_conformity: bool = True,
    materials: str = "",
) -> tuple[str, list[Message]]:
    """active ペルソナが「次の1発言」を生成するための (system, messages) を組む。

    返り値の messages は必ず user で始まり user で終わる（先頭 user は Anthropic の要件、
    末尾 user は「今あなたが問われている」状態を作るため）。

    materials は全ペルソナが共有する「資料・前提」。先頭 user の【議題】に続けて
    【資料・前提】ブロックを差し込む。materials="" のときはブロックを足さず、従来と
    完全に同一の出力になる（後方互換）。
    """
    head = f"【議題】\n{topic}"
    if materials:
        head += f"\n\n【資料・前提】\n{materials}"
    events: list[tuple[str, str]] = [("user", head)]

    for turn in transcript:
        if turn.speaker_id == active.id:
            # 自分の発言は素の assistant（名前ラベルを付けない＝自分の声として認識させる）
            events.append(("assistant", turn.content))
        else:
            # 他者の発言は user 側に、誰の発言かを明示して提示
            events.append(("user", f"【{turn.speaker_name}】\n{turn.content}"))

    # 末尾の指名ナッジ（フェーズ指示・反同調・本人指名をまとめて user として注入）
    nudge: list[str] = []
    if phase_directive:
        nudge.append(phase_directive)
    if anti_conformity:
        nudge.append(ANTI_CONFORMITY)
    nudge.append(
        f"あなた（{active.display_name}）の番です。上記の議論を踏まえ、"
        f"{active.display_name} として一度だけ簡潔に発言してください。"
        "他の参加者のセリフを代弁・捏造しないこと。"
        "見出しや水平線（---）で発言を機械的に飾らないこと。あなたの名前は画面に"
        "既に表示されている——冒頭に「## 〇〇担当の発言」のような見出しを付けないこと。"
        "構造化が中身を助けるとき（対比表・条件分岐・層構造など）だけ Markdown を使い、"
        "装飾のための区切り線は使わないこと。"
    )
    events.append(("user", "\n\n".join(nudge)))

    return active.system_prompt, _merge(events)
