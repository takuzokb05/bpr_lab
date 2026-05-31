"""ペルソナ・レジストリ（データ駆動）。

ペルソナ1件 = 1データ。YAML から読み込む。コードに人格を埋め込まないことで、
著名経営者・哲学者の追加を「データ追加」だけで済ませ、後続の dynamicworkflows で
「誰を・どの順で動かすか」を動的合成できるようにする。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# category の意味:
#   facilitation … 司会（オープニング/進行）。パネリストのローテーションには入れない
#   chair        … 統合役（最後に議事を1枚にまとめる議長）
#   scribe       … 書記（記録専任。speaks=False で発言ローテーション対象外）
#   thinking     … 思考スタイル系（論理 / アイデア / 共感 など）
#   founders     … 著名経営者
#   philosophers … 哲学者
_VALID_CATEGORIES = {
    "facilitation",
    "chair",
    "scribe",
    "thinking",
    "founders",
    "philosophers",
}

# カテゴリ別のアクセント色（UIUX_REVIEW_2026-05.md の彩度低めパレット）。
# persona.accent が未指定のときのフォールバックに使う。絵文字アバターの代わりに
# 「モノグラム + カテゴリ色」でペルソナを識別する。
CATEGORY_ACCENT = {
    "thinking": "#5B7C8A",
    "founders": "#8A6D3B",
    "philosophers": "#6E5B8A",
    "facilitation": "#4A4A4A",
    "chair": "#3B6E5B",
    "scribe": "#6B675F",
}
_DEFAULT_ACCENT = "#5B7C8A"


@dataclass
class Persona:
    """討論に参加する1人格。"""

    id: str
    display_name: str
    system_prompt: str
    category: str = "thinking"
    avatar: str = "🧠"
    # model=None はエンジン既定モデルを使う。collapse（均質化）対策として、
    # 思考の多様性が欲しいペルソナには個別に別モデルを割り当てられる。
    model: str | None = None
    temperature: float | None = None
    tags: list[str] = field(default_factory=list)
    # 発言ローテーションに入れるか。書記など記録専任は False。
    speaks: bool = True
    # UI 用のアクセント色（#RRGGBB）。未指定ならカテゴリ色を使う。絵文字に依らず
    # 「モノグラム + この色」でペルソナを識別する（UIUX_REVIEW 参照）。
    accent: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Persona.id は必須です")
        if not self.system_prompt.strip():
            raise ValueError(f"persona '{self.id}' の system_prompt が空です")
        if self.category not in _VALID_CATEGORIES:
            raise ValueError(
                f"persona '{self.id}' の category '{self.category}' が不正です "
                f"(有効: {sorted(_VALID_CATEGORIES)})"
            )

    @property
    def accent_color(self) -> str:
        """UI 用アクセント色。persona.accent > カテゴリ色 > 既定。"""
        return self.accent or CATEGORY_ACCENT.get(self.category, _DEFAULT_ACCENT)

    @property
    def monogram(self) -> str:
        """絵文字の代わりにアバターへ表示する1〜2文字の頭文字。

        ラテン語の複数語名はイニシャル2文字（"Steve Jobs"→"SJ"）、
        それ以外は括弧書きを除いた先頭1文字（"論理担当"→"論"）。
        """
        words = self.display_name.replace("　", " ").split()
        if len(words) >= 2 and words[0][:1].isascii() and words[1][:1].isascii():
            return (words[0][0] + words[1][0]).upper()
        base = self.display_name.split("（")[0].split("(")[0].strip()
        return base[:1] or "?"


def persona_from_dict(data: dict[str, Any]) -> Persona:
    """dict（YAML 1ファイル相当）から Persona を生成する。"""
    known = {
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
    }
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"未知のキー {sorted(unknown)} (persona '{data.get('id')}')")
    return Persona(
        id=data["id"],
        display_name=data.get("display_name", data["id"]),
        system_prompt=data["system_prompt"],
        category=data.get("category", "thinking"),
        avatar=data.get("avatar", "🧠"),
        model=data.get("model"),
        temperature=data.get("temperature"),
        tags=list(data.get("tags", [])),
        speaks=bool(data.get("speaks", True)),
        accent=data.get("accent"),
    )


def load_personas(directory: str | Path) -> list[Persona]:
    """ディレクトリ配下の *.yaml / *.yml を再帰的に読み込み、Persona のリストを返す。

    id の重複は許さない（取り違え防止）。
    """
    import yaml  # 遅延 import（テストはモックのみで動く）

    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"persona ディレクトリが見つかりません: {directory}")

    personas: list[Persona] = []
    seen: dict[str, Path] = {}
    for path in sorted(directory.rglob("*.y*ml")):
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"{path}: トップレベルは mapping である必要があります")
        persona = persona_from_dict(data)
        if persona.id in seen:
            raise ValueError(
                f"persona id '{persona.id}' が重複しています: {seen[persona.id]} と {path}"
            )
        seen[persona.id] = path
        personas.append(persona)
    return personas
