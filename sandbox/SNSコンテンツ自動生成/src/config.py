"""設定・環境変数読み込み"""
import os
from dotenv import load_dotenv

load_dotenv()

# API キー
GROK_API_KEY = os.getenv("GROK_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
X_API_BEARER_TOKEN = os.getenv("X_API_BEARER_TOKEN")
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

# データベース
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sns_content.db")

# API設定
API_TIMEOUT = 30  # 秒
MAX_RETRIES = 3
