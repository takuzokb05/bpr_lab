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

# 因縁（relationships）の関係種別。rival=対立 / ally=盟友 / mentor=あなたが師 / student=あなたが弟子。
_VALID_REL_TYPES = {"rival", "ally", "mentor", "student"}

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
    # ピッカー表示用の一行説明（「この人はどんな人か」）。選ぶときに一目で分かる短文を持たせる
    # （system_prompt 全文とは別物）。空なら UI は説明を出さない＝後方互換。
    description: str = ""
    # レガシー絵文字フィールド（後方互換でのみ受理・保持）。UI は描画に使わず
    # モノグラム＋カテゴリ色で識別する（UIUX_REVIEW: 絵文字全廃）。既定は空。
    avatar: str = ""
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
    # 偉人同士の因縁（対立/盟友/師弟）。各要素 = {"to": <相手 id>, "type": <関係種別>,
    # "note": <あなた視点の一言>}。同じ討論に相手が同席するとき、その関係を system に注入して
    # 「最初から相手を意識して絡む」ようにする＋ピッカーで対立相手をサジェストする。空＝従来同一。
    relationships: list[dict] = field(default_factory=list)

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
        for r in self.relationships:
            if not isinstance(r, dict) or not r.get("to"):
                raise ValueError(f"persona '{self.id}' の relationships に 'to' が無い要素があります")
            if r.get("type") not in _VALID_REL_TYPES:
                raise ValueError(
                    f"persona '{self.id}' の relationship type '{r.get('type')}' が不正です "
                    f"(有効: {sorted(_VALID_REL_TYPES)})"
                )
            # note は任意だが、文字列以外は注入時の .strip() で落ちるため弾く（防御）。
            if r.get("note") is not None and not isinstance(r.get("note"), str):
                raise ValueError(f"persona '{self.id}' の relationship note は文字列で指定してください")

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
        "description",
        "avatar",
        "model",
        "temperature",
        "tags",
        "speaks",
        "accent",
        "relationships",
    }
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"未知のキー {sorted(unknown)} (persona '{data.get('id')}')")
    # relationships は要素 dict のリスト。単一 dict を誤って書いた場合は [dict] に正規化し、
    # それ以外の非リスト（mapping 直書き等）は list() がキー名の並びになって誤検証されるため明示的に弾く。
    rels = data.get("relationships", [])
    if isinstance(rels, dict):
        rels = [rels]
    elif not isinstance(rels, list):
        raise ValueError(
            f"persona '{data.get('id')}' の relationships はリストで指定してください "
            f"(実際の型: {type(rels).__name__})"
        )
    return Persona(
        id=data["id"],
        display_name=data.get("display_name", data["id"]),
        system_prompt=data["system_prompt"],
        category=data.get("category", "thinking"),
        # None（PersonaUpsert の未指定）も空文字に正規化し、dataclass の str 不変条件を保つ。
        description=data.get("description") or "",
        avatar=data.get("avatar", ""),
        model=data.get("model"),
        temperature=data.get("temperature"),
        tags=list(data.get("tags", [])),
        speaks=bool(data.get("speaks", True)),
        accent=data.get("accent"),
        relationships=list(rels),
    )


def load_personas_with_paths(directory: str | Path) -> list[tuple[Persona, Path]]:
    """ディレクトリ配下の *.yaml / *.yml を再帰的に読み込み、(Persona, Path) の列を返す。

    id の重複は許さない（取り違え防止）。save_persona は id→実パスの対応で旧ファイルを
    unlink するため、ファイル名から id を推測せずこの実パスを使う（jobs.yaml の
    id=steve_jobs のような不一致があるため）。

    戻り値・例外・sorted 順・id 重複検出は load_personas と完全に同じ挙動（薄いラッパが
    Persona だけを取り出せるよう、ここに本体ロジックを集約する）。
    """
    import yaml  # 遅延 import（テストはモックのみで動く）

    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"persona ディレクトリが見つかりません: {directory}")

    pairs: list[tuple[Persona, Path]] = []
    seen: dict[str, Path] = {}
    for path in sorted(directory.rglob("*.y*ml")):
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"{path}: トップレベルは mapping である必要があります")
        # 1件の不正で全体ロードを落とす挙動は維持しつつ、原因ファイルの path を必ず示す
        # （現状は persona id だけで、どの YAML が壊れているか特定が困難なため）。
        try:
            persona = persona_from_dict(data)
        except (ValueError, KeyError) as e:
            raise ValueError(f"{path}: persona の読み込みに失敗しました: {e}") from e
        if persona.id in seen:
            raise ValueError(
                f"persona id '{persona.id}' が重複しています: {seen[persona.id]} と {path}"
            )
        seen[persona.id] = path
        pairs.append((persona, path))
    return pairs


def load_personas(directory: str | Path) -> list[Persona]:
    """ディレクトリ配下の *.yaml / *.yml を再帰的に読み込み、Persona のリストを返す。

    id の重複は許さない（取り違え防止）。実体は load_personas_with_paths（後方互換のため
    Persona だけを取り出す薄いラッパ）。
    """
    return [persona for persona, _path in load_personas_with_paths(directory)]
