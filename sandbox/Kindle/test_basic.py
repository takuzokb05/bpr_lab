"""
導入確認用スモークテスト: 依存パッケージと全モジュールがimportできるかだけを確認する
(ロジックの検証は tests/ の pytest スイートが担当)
"""

import importlib
import sys


def main() -> int:
    """依存と自作モジュールのimport可否を順に確認する"""
    # リダイレクト時のcp932でも落ちないようUTF-8を明示する
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

    targets = [
        # 依存パッケージ
        "pyautogui",
        "PIL",
        "img2pdf",
        "pynput",
        "pygetwindow",
        "ocrmypdf",
        # 自作モジュール
        "window_manager",
        "capture",
        "postprocess",
        "ocr",
        "pdf_engine",
        "main",
    ]

    failed: list[str] = []
    for name in targets:
        try:
            importlib.import_module(name)
            print(f"  OK  {name}")
        except Exception as e:
            print(f"  NG  {name}: {e}")
            failed.append(name)

    if failed:
        print(f"\nNG: import失敗 {len(failed)}件: {', '.join(failed)}")
        print("pip install -r requirements.txt を実行してください")
        return 1

    print("\nOK: 全モジュールのimportに成功しました。python main.py で起動できます")
    return 0


if __name__ == "__main__":
    sys.exit(main())
