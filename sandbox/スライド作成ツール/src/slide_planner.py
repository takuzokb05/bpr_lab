"""スライド構成生成（Gemini 3 Flash）"""
import json
from pathlib import Path

from google import genai
from google.genai import types

from src.config import MODEL_TEXT, THINKING_LEVEL


# スライド構成の JSON スキーマ
SLIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "total_slides": {"type": "integer"},
            },
            "required": ["title", "total_slides"],
        },
        "slides": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "slide_number": {"type": "integer"},
                    "slide_type": {
                        "type": "string",
                        "enum": ["title", "section", "content", "end"],
                    },
                    "title": {"type": "string"},
                    "subtitle": {"type": "string"},
                    "bullet_points": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "speaker_notes": {"type": "string"},
                    "background_prompt": {"type": "string"},
                },
                "required": [
                    "slide_number", "slide_type", "title",
                    "bullet_points", "background_prompt",
                ],
            },
        },
    },
    "required": ["metadata", "slides"],
}


def _build_prompt(taste: dict) -> str:
    """スライド構成生成用のプロンプトを構築"""
    return f"""あなたはプレゼンテーション設計の専門家です。
以下の資料を読み、スライド構成を作成してください。

【要件】
- スライド枚数: 資料の内容量に応じて適切に（制限なし）
- 最初のスライドは slide_type: "title"
- 最後のスライドは slide_type: "end"
- セクションの切り替え時は slide_type: "section"
- それ以外は slide_type: "content"
- 各 content スライドの bullet_points は 3〜5 項目
- title/section/end スライドの bullet_points は空配列 []
- speaker_notes は日本語で発表者向けメモ
- background_prompt は英語で、テイスト設定に合わせた抽象的背景画像の説明。
  必ず "space for text overlay" を含め、具体的なオブジェクトは避ける

【テイスト】
- スタイル: {taste.get('style', 'business')}
- 色調: {taste.get('color_tone', 'dark')}
- トーン: {taste.get('tone', 'formal')}

資料の内容:
"""


def generate_slide_plan(
    client: genai.Client,
    text: str,
    taste: dict,
    input_path: Path | None = None,
) -> dict:
    """
    Gemini 3 Flash でスライド構成 JSON を生成する。

    Args:
        client: Gemini API クライアント
        text: 資料のテキスト
        taste: テイスト設定 {"style", "color_tone", "tone"}
        input_path: 元ファイルパス（PDF直接渡し用、オプション）

    Returns:
        スライド構成 dict
    """
    prompt = _build_prompt(taste)

    # PDF の場合は直接ファイルを渡す（視覚情報も活用）
    if input_path and input_path.suffix.lower() == ".pdf":
        contents = [
            types.Part.from_bytes(
                data=input_path.read_bytes(),
                mime_type="application/pdf",
            ),
            prompt,
        ]
    else:
        contents = prompt + text

    response = client.models.generate_content(
        model=MODEL_TEXT,
        contents=contents,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
            response_mime_type="application/json",
            response_schema=SLIDE_SCHEMA,
        ),
    )

    plan = json.loads(response.text)

    # テイスト情報をメタデータに付与
    plan["metadata"]["taste"] = taste

    return plan


def regenerate_single_slide(
    client: genai.Client,
    plan: dict,
    slide_number: int,
) -> dict:
    """指定スライドの構成を再生成する（F6 リライト用）"""
    slide = None
    for s in plan["slides"]:
        if s["slide_number"] == slide_number:
            slide = s
            break

    if slide is None:
        raise ValueError(f"スライド #{slide_number} が見つかりません")

    taste = plan["metadata"].get("taste", {})
    prompt = f"""以下のスライドの内容を別の切り口で書き直してください。
元のスライドタイプ・テイストは維持してください。

【元のスライド】
{json.dumps(slide, ensure_ascii=False, indent=2)}

【テイスト】
- スタイル: {taste.get('style', 'business')}
- 色調: {taste.get('color_tone', 'dark')}
- トーン: {taste.get('tone', 'formal')}
"""

    # 単一スライドのスキーマ
    single_schema = SLIDE_SCHEMA["properties"]["slides"]["items"]

    response = client.models.generate_content(
        model=MODEL_TEXT,
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL),
            response_mime_type="application/json",
            response_schema=single_schema,
        ),
    )

    return json.loads(response.text)
