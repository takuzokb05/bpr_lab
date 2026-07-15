"""アプリケーション設定"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# アプリ基本情報
APP_NAME = "スライド作成ツール"
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "output"

# Gemini API設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY が設定されていません。.envファイルを確認してください。")

# モデル設定
MODEL_TEXT = "gemini-3-flash-preview"
MODEL_IMAGE = "gemini-3-pro-image-preview"
MODEL_IMAGE_FALLBACK = "imagen-4.0-fast-generate-001"

# テキスト処理の thinking レベル（minimal/low/medium/high）
THINKING_LEVEL = "low"

# 画像生成設定
IMAGE_ASPECT_RATIO = "16:9"
IMAGE_RESOLUTION = "1K"

# スライド設定（インチ）
SLIDE_WIDTH_INCHES = 13.333
SLIDE_HEIGHT_INCHES = 7.5

# デフォルトテイスト
DEFAULT_STYLE = "business"
DEFAULT_COLOR_TONE = "dark"
DEFAULT_TONE = "formal"

# デフォルトフォント
DEFAULT_FONT = "メイリオ"

# API設定
API_TIMEOUT = 30
API_MAX_RETRIES = 3

# ファイルサイズ制限（バイト）
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
