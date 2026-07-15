"""
Poppler自動検出とPATH設定ヘルパー
"""

import os
from pathlib import Path

print("Popplerを検索中...")

# よくある場所を検索
search_paths = [
    Path(r"C:\Program Files\poppler"),
    Path(r"C:\poppler"),
    Path.home() / "Downloads",
    Path.home() / "Desktop",
    Path(r"C:\Users") / os.getenv("USERNAME", "") / "Downloads",
]

found_paths = []

for search_path in search_paths:
    if search_path.exists():
        # popplerフォルダを再帰的に検索
        for item in search_path.rglob("poppler*"):
            if item.is_dir():
                # binフォルダを探す
                bin_path = item / "Library" / "bin"
                if not bin_path.exists():
                    bin_path = item / "bin"
                
                if bin_path.exists() and (bin_path / "pdftoppm.exe").exists():
                    found_paths.append(str(bin_path))

if found_paths:
    print("\n✓ Popplerが見つかりました！\n")
    for i, path in enumerate(found_paths, 1):
        print(f"{i}. {path}")
    
    print("\n" + "="*60)
    print("以下のコマンドをPowerShellで実行してください:")
    print("="*60)
    print(f'$env:Path += ";{found_paths[0]}"')
    print("="*60)
    
    print("\nまたは、pdf_processor.pyで直接パスを指定することもできます。")
else:
    print("\n❌ Popplerが見つかりませんでした。")
    print("\n解凍したPopplerフォルダの場所を教えてください。")
    print("例: C:\\Users\\takuz\\Downloads\\poppler-24.08.0")
