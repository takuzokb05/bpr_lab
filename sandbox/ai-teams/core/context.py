"""コンテキスト・ビルダー（人格混線の根治）。

v2 の致命傷は「全員の発言を role=assistant で1配列に詰め、モデルに多人格ログを
自分の発言として読ませた」こと。AutoGen 方式に倣い、発言を生成するペルソナから見て:

  - 自分の過去発言 … role="assistant"（自分の声）
  - 他者の発言     … role="user" に【名前】付きで提示（外から来た入力）

とすることで、モデルが他人の人格を自分の声として継続しにくくする。
さらに毎回 system にペルソナ定義を入れ直す（長対話での fidelity decay 対策）。
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .llm_client import _env

if TYPE_CHECKING:  # 循環 import 回避（型注釈のみ）
    from .orchestrator import Turn
    from .personas import Persona

Message = dict[str, str]

# 調査ブリーフの出典リストは1件あたり数十URLに膨れ、全 researcher ターンが後続の全発言に
# 再注入されると LLM 文脈が肥大する（コスト・トークン切れ・可読性の複合悪化）。フロント表示や
# export は全件保持したいので Turn.content 自体は変えず、ここ（build_context が組む LLM 文脈の
# コピー）でだけ出典を上位 N 件に圧縮する。env AI_COUNCIL_RESEARCH_CTX_MAX_SOURCES で可変（既定 5）。
_RESEARCH_CTX_MAX_SOURCES = int(_env("RESEARCH_CTX_MAX_SOURCES", "5"))
# 「\n\n出典:\n- …」ブロックを丸ごと掴む（'出典:' 見出しは llm_client/フロントと凍結契約）。
# 「- 」行に加え空行/空白のみ行も許容して連続性を保つ（モデル生成URLに改行混入時の取りこぼし防止
# ＝対抗レビュー L1）。非"- "の本文行はマッチを切る（後続プローズを食わない）。
_RESEARCH_SOURCES_RE = re.compile(r"\n\n出典[:：]\n(?:(?:- .*|[^\S\n]*)(?:\n|$))+")


def _truncate_research_sources(content: str, max_sources: int = _RESEARCH_CTX_MAX_SOURCES) -> str:
    """調査ブリーフ content の末尾「出典:」リストを上位 max_sources 件に圧縮する（LLM 文脈用）。

    出典節が無い／件数が上限以下なら content をそのまま返す（no-op＝後方互換）。Turn.content 自体は
    変えず、build_context が messages に積むコピーにだけ適用する（フロント/export はフル保持）。
    """
    m = _RESEARCH_SOURCES_RE.search(content)
    if not m:
        return content
    head = content[: m.start()]
    lines = [ln for ln in m.group(0).strip().splitlines() if ln.startswith("- ")]
    if len(lines) <= max_sources:
        return content
    kept = "\n".join(lines[:max_sources])
    omitted = len(lines) - max_sources
    return f"{head}\n\n出典:\n{kept}\n- （他{omitted}件省略）"

# 既出に流されないための反同調ディレクティブ（collapse / echo chamber 対策）。
ANTI_CONFORMITY = (
    "安易に同意しないこと。既出の意見と異なる角度・反論・"
    "見落とされている論点を、必ず最低1つ含めること。"
)

# 調査要請ディレクティブ（research_enabled=True のときだけ末尾ナッジに足す）。
# 事実・数字が欲しいのに【資料・前提】や【調査】に無ければ「要調査: …」を1行で書かせ、
# 調査役（researcher ターン）が調べて全員に共有する。乱発を抑えるよう明示する。
RESEARCH_NUDGE = (
    "事実・数字が必要なのに【資料・前提】や【調査】に無い場合、発言の最後に"
    "『要調査: <調べたい具体的な問い>』を1行だけ書いてよい。調査役が調べて全員に共有する。"
    "乱発しないこと。"
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
    research_enabled: bool = False,
    length_directive: str = "",
    roster_note: str = "",
) -> tuple[str, list[Message]]:
    """active ペルソナが「次の1発言」を生成するための (system, messages) を組む。

    返り値の messages は必ず user で始まり user で終わる（先頭 user は Anthropic の要件、
    末尾 user は「今あなたが問われている」状態を作るため）。

    materials は全ペルソナが共有する「資料・前提」。先頭 user の【議題】に続けて
    【資料・前提】ブロックを差し込む。materials="" のときはブロックを足さず、従来と
    完全に同一の出力になる（後方互換）。

    roster_note は「この討論に同席する因縁」（対立/盟友の相手とその関係）。空でなければ
    active の system_prompt の末尾に追記し、相手を最初から意識して絡ませる。
    ""（因縁なし／相手が同席しない）のときは何も足さない＝従来と完全同一（後方互換）。
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
            # 他者の発言は user 側に、誰の発言かを明示して提示。調査(researcher)ターンは出典が
            # 肥大するので、LLM 文脈に積むコピーだけ上位 N 件に圧縮する（Turn.content 自体は不変）。
            text = turn.content
            if turn.speaker_id == "researcher" or getattr(turn, "phase", "") == "research":
                text = _truncate_research_sources(text)
            events.append(("user", f"【{turn.speaker_name}】\n{text}"))

    # 末尾の指名ナッジ（フェーズ指示・反同調・本人指名をまとめて user として注入）
    nudge: list[str] = []
    if phase_directive:
        nudge.append(phase_directive)
    if anti_conformity:
        nudge.append(ANTI_CONFORMITY)
    if research_enabled:
        # research=False では一切出さない＝従来と完全一致（後方互換）。
        nudge.append(RESEARCH_NUDGE)
    # 応答の長さ指示（プリセット由来）。空（標準）なら従来どおり "簡潔に"（後方互換）。
    length_word = length_directive or "簡潔に"
    nudge.append(
        f"あなた（{active.display_name}）の番です。上記の議論を踏まえ、"
        f"{active.display_name} として一度だけ{length_word}発言してください。"
        "他の参加者のセリフを代弁・捏造しないこと。"
        "見出しや水平線（---）で発言を機械的に飾らないこと。あなたの名前は画面に"
        "既に表示されている——冒頭に「## 〇〇担当の発言」のような見出しを付けないこと。"
        "構造化が中身を助けるとき（対比表・条件分岐・層構造など）だけ Markdown を使い、"
        "装飾のための区切り線は使わないこと。"
    )
    events.append(("user", "\n\n".join(nudge)))

    # 因縁ブロックは system 末尾に追記（セッション中ずっと効かせる）。空なら従来同一。
    system = active.system_prompt
    if roster_note:
        system = f"{system}\n\n{roster_note}"
    return system, _merge(events)
