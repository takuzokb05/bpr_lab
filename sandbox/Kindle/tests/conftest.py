"""
pytest 共通設定

tests/ 配下からプロジェクトルートの capture.py 等を import できるようにする。
"""

import sys
from pathlib import Path

# プロジェクトルート（tests/ の1つ上）を import パスに追加する
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
