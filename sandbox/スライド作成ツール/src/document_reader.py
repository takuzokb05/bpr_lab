"""資料読み込み（PDF/テキスト）"""
import os
from pathlib import Path

import pdfplumber

from src.config import MAX_FILE_SIZE

# 対応ファイル拡張子
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def read_document(file_path: Path) -> dict:
    """
    ファイルを読み込み、テキストとメタ情報を返す。

    Returns:
        {"text": str, "pages": int, "file_size": int, "file_name": str}
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"非対応のファイル形式です: {ext}\n"
            f"対応形式: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(
            f"ファイルサイズが大きすぎます: {file_size / 1024 / 1024:.1f}MB "
            f"(上限: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB)"
        )

    if ext == ".pdf":
        return _read_pdf(file_path, file_size)
    else:
        return _read_text(file_path, file_size)


def _read_pdf(file_path: Path, file_size: int) -> dict:
    """PDF からテキストを抽出"""
    try:
        text_parts = []
        page_count = 0
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        text = "\n\n".join(text_parts)
        if not text.strip():
            raise ValueError(
                f"PDFからテキストを抽出できませんでした: {file_path}\n"
                "スキャンPDFの場合はOCR処理が必要です。"
            )

        return {
            "text": text,
            "pages": page_count,
            "file_size": file_size,
            "file_name": file_path.name,
        }
    except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as e:
        raise ValueError(f"PDFファイルが破損しているか、形式が不正です: {e}") from e


def _read_text(file_path: Path, file_size: int) -> dict:
    """テキスト/Markdownファイルを読み込み"""
    text = file_path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"ファイルが空です: {file_path}")

    return {
        "text": text,
        "pages": 1,
        "file_size": file_size,
        "file_name": file_path.name,
    }
