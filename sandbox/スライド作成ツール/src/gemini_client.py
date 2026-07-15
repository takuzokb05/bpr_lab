"""Gemini API クライアント"""
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, MODEL_TEXT, MODEL_IMAGE, THINKING_LEVEL


def create_client() -> genai.Client:
    """Gemini API クライアントを作成"""
    return genai.Client(api_key=GEMINI_API_KEY)


def test_connection(client: genai.Client) -> bool:
    """API接続テスト。成功なら True を返す"""
    try:
        response = client.models.generate_content(
            model=MODEL_TEXT,
            contents="Hello",
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
                max_output_tokens=10,
            ),
        )
        return response.text is not None
    except Exception as e:
        raise ConnectionError(f"Gemini API への接続に失敗しました: {e}") from e
