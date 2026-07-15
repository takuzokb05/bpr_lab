"""
Test PDF conversion with Poppler
"""

from pdf_processor import PDFProcessor, POPPLER_PATH

print("Poppler設定確認:")
print(f"Popplerパス: {POPPLER_PATH}")
print(f"存在確認: {POPPLER_PATH.exists()}")

if POPPLER_PATH.exists():
    print("✓ Popplerが見つかりました！")
    print("\nPDF変換の準備ができています。")
    print("\n使用方法:")
    print("  python main.py --input <your_pdf_file>.pdf")
else:
    print("❌ Popplerが見つかりません。")
    print(f"期待されるパス: {POPPLER_PATH}")
