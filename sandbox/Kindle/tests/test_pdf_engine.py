"""
pdf_engine / ocr モジュールのテスト
書名サニタイズ・出力パス生成・PDF変換の挙動を検証する
"""

import os
import re
from datetime import datetime

import pytest
from PIL import Image

import pdf_engine
from ocr import checkOcrAvailability
from pdf_engine import PdfEngine

# 出力ファイル名の期待形式: {書名}_{YYYYMMDD}_{HHMM}[_連番].pdf
OUTPUT_NAME_PATTERN = re.compile(r"^.+_\d{8}_\d{4}(?:_\d+)?\.pdf$")


def makeImage(path: str, size: tuple[int, int] = (60, 80)) -> str:
    """テスト用の小さなRGB画像を作る"""
    Image.new("RGB", size, color="white").save(path)
    return path


def makeEmptyFile(path: str) -> str:
    """0バイトのファイルを作る（撮影が失敗したページの再現）"""
    open(path, "wb").close()
    return path


def makeTruncatedPng(path: str, keepBytes: int = 80) -> str:
    """途中で切れた壊れたPNGを作る（保存中に中断されたページの再現）"""
    validPath = f"{path}.source.png"
    makeImage(validPath, size=(200, 200))

    with open(validPath, "rb") as f:
        data = f.read()

    os.remove(validPath)

    with open(path, "wb") as f:
        f.write(data[:keepBytes])

    return path


# --- sanitizeBookTitle ---------------------------------------------------


def test_sanitizeBookTitleKeepsJapanese():
    """日本語の書名がそのまま保持されること"""
    assert PdfEngine.sanitizeBookTitle("吾輩は猫である") == "吾輩は猫である"


def test_sanitizeBookTitleRemovesForbiddenChars():
    """Windows禁止文字が除去されること"""
    result = PdfEngine.sanitizeBookTitle('Re:ゼロ/から*始める?異世界"生活"<上>|下')

    for forbidden in '\\/:*?"<>|':
        assert forbidden not in result
    assert "ゼロ" in result


def test_sanitizeBookTitleRemovesAppSuffix():
    """アプリ名サフィックスが除去されること"""
    assert PdfEngine.sanitizeBookTitle("実践Python - Kindle") == "実践Python"
    assert PdfEngine.sanitizeBookTitle("実践Python - Kindle for PC") == "実践Python"
    assert PdfEngine.sanitizeBookTitle("実践Python - Amazon Kindle") == "実践Python"


@pytest.mark.parametrize(
    "title",
    ["はじめてのKindle", "Kindle活用術", "マンガでわかるKindle出版"],
)
def test_sanitizeBookTitleKeepsKindleInsideTitle(title):
    """区切りなしで書名の一部になっている 'Kindle' は削られないこと"""
    assert PdfEngine.sanitizeBookTitle(title) == title


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("CON", "_CON"),
        ("con", "_con"),
        ("PRN", "_PRN"),
        ("NUL", "_NUL"),
        ("COM1", "_COM1"),
        ("LPT9", "_LPT9"),
    ],
)
def test_sanitizeBookTitleGuardsReservedDeviceNames(title, expected):
    """Windows予約デバイス名には先頭に _ が付くこと"""
    assert PdfEngine.sanitizeBookTitle(title) == expected


@pytest.mark.parametrize("title", ["CONTENTS", "COM10", "コンテンツ", "AUXILIARY"])
def test_sanitizeBookTitleLeavesNonReservedNames(title):
    """予約デバイス名に似ているだけの書名は変更されないこと"""
    assert PdfEngine.sanitizeBookTitle(title) == title


@pytest.mark.parametrize("title", [None, "", "   ", "- Kindle", "///"])
def test_sanitizeBookTitleFallsBackWhenEmpty(title):
    """空・記号のみ・アプリ名のみの場合はフォールバック名になること"""
    assert PdfEngine.sanitizeBookTitle(title) == "Kindle_Export"


def test_sanitizeBookTitleTruncatesTo80Chars():
    """80文字を超える書名が切り詰められること"""
    longTitle = "あ" * 120

    result = PdfEngine.sanitizeBookTitle(longTitle)

    assert len(result) == 80
    assert result == "あ" * 80


def test_sanitizeBookTitleCollapsesWhitespace():
    """連続空白が1つにまとめられ、前後が整形されること"""
    assert PdfEngine.sanitizeBookTitle("  実践   Python 入門  ") == "実践 Python 入門"


# --- getOutputPath -------------------------------------------------------


def _useTempHome(tmp_path, monkeypatch) -> str:
    """ホームディレクトリを tmp_path に差し替え、Downloads のパスを返す"""
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HOMEPATH", str(tmp_path))
    monkeypatch.delenv("HOMEDRIVE", raising=False)
    return os.path.join(str(tmp_path), "Downloads")


def _freezeTimestamp(monkeypatch) -> None:
    """タイムスタンプを固定し、分をまたぐことによるテストの揺らぎを防ぐ"""

    class FixedDatetime:
        @staticmethod
        def now() -> datetime:
            return datetime(2026, 8, 11, 16, 6)

    monkeypatch.setattr(pdf_engine, "datetime", FixedDatetime)


def test_getOutputPathFormat(tmp_path, monkeypatch):
    """Downloads配下に {書名}_{YYYYMMDD_HHMM}.pdf が生成されること"""
    downloadsPath = _useTempHome(tmp_path, monkeypatch)
    _freezeTimestamp(monkeypatch)

    outputPath = PdfEngine.getOutputPath("実践Python - Kindle")

    assert os.path.dirname(outputPath) == downloadsPath
    assert os.path.basename(outputPath) == "実践Python_20260811_1606.pdf"
    assert OUTPUT_NAME_PATTERN.match(os.path.basename(outputPath))


def test_getOutputPathUsesFallbackWithoutTitle(tmp_path, monkeypatch):
    """書名未指定なら Kindle_Export がベース名になること"""
    _useTempHome(tmp_path, monkeypatch)
    _freezeTimestamp(monkeypatch)

    outputPath = PdfEngine.getOutputPath()

    assert os.path.basename(outputPath).startswith("Kindle_Export_")
    assert OUTPUT_NAME_PATTERN.match(os.path.basename(outputPath))


def test_getOutputPathAvoidsCollision(tmp_path, monkeypatch):
    """同名ファイルが存在する場合に _2, _3 が付くこと"""
    _useTempHome(tmp_path, monkeypatch)
    _freezeTimestamp(monkeypatch)

    firstPath = PdfEngine.getOutputPath("テスト書名")
    open(firstPath, "wb").close()

    secondPath = PdfEngine.getOutputPath("テスト書名")
    assert os.path.basename(secondPath) == "テスト書名_20260811_1606_2.pdf"
    open(secondPath, "wb").close()

    thirdPath = PdfEngine.getOutputPath("テスト書名")
    assert os.path.basename(thirdPath) == "テスト書名_20260811_1606_3.pdf"


# --- validateImages ------------------------------------------------------


def test_validateImagesAcceptsValidImage(tmp_path):
    """正常な画像は有効と判定されること"""
    assert PdfEngine.validateImages([makeImage(str(tmp_path / "page_0001.png"))]) is True


def test_validateImagesRejectsEmptyFile(tmp_path):
    """0バイトのファイルが不正と判定されること"""
    assert PdfEngine.validateImages([makeEmptyFile(str(tmp_path / "empty.png"))]) is False


def test_validateImagesRejectsTruncatedPng(tmp_path):
    """途中で切れたPNGが不正と判定されること"""
    assert PdfEngine.validateImages([makeTruncatedPng(str(tmp_path / "broken.png"))]) is False


def test_validateImagesRejectsMissingFile(tmp_path):
    """存在しないパスが不正と判定されること"""
    assert PdfEngine.validateImages([str(tmp_path / "missing.png")]) is False


def test_validateImagesRejectsDirectory(tmp_path):
    """ディレクトリが不正と判定されること"""
    assert PdfEngine.validateImages([str(tmp_path)]) is False


# --- convertToPdf --------------------------------------------------------


def test_convertToPdfCreatesFile(tmp_path):
    """画像2枚から実際にPDFが生成されること"""
    images = [
        makeImage(str(tmp_path / "page_0001.png")),
        makeImage(str(tmp_path / "page_0002.png")),
    ]
    outputPath = str(tmp_path / "out.pdf")

    result = PdfEngine.convertToPdf(images, outputPath=outputPath)

    assert result == outputPath
    assert os.path.exists(outputPath)
    assert os.path.getsize(outputPath) > 0


def test_convertToPdfSkipsMissingImages(tmp_path):
    """欠損パスが混ざっていても、残りの画像で変換が成功すること"""
    images = [
        makeImage(str(tmp_path / "page_0001.png")),
        str(tmp_path / "missing.png"),
        makeImage(str(tmp_path / "page_0003.png")),
    ]
    outputPath = str(tmp_path / "out.pdf")

    PdfEngine.convertToPdf(images, outputPath=outputPath)

    assert os.path.getsize(outputPath) > 0


def test_convertToPdfSkipsCorruptedImages(tmp_path):
    """0バイト・破損PNGを除外し、正常な画像だけでPDF化できること"""
    images = [
        makeImage(str(tmp_path / "page_0001.png")),
        makeEmptyFile(str(tmp_path / "page_0002.png")),
        makeTruncatedPng(str(tmp_path / "page_0003.png")),
        makeImage(str(tmp_path / "page_0004.png")),
    ]
    outputPath = str(tmp_path / "out.pdf")

    PdfEngine.convertToPdf(images, outputPath=outputPath)

    assert os.path.getsize(outputPath) > 0


def test_convertToPdfRaisesWhenAllImagesCorrupted(tmp_path):
    """全画像が破損している場合は ValueError になること"""
    images = [
        makeEmptyFile(str(tmp_path / "page_0001.png")),
        makeTruncatedPng(str(tmp_path / "page_0002.png")),
    ]

    with pytest.raises(ValueError):
        PdfEngine.convertToPdf(images, outputPath=str(tmp_path / "out.pdf"))


def test_convertToPdfRaisesWhenAllMissing(tmp_path):
    """有効な画像が1枚もない場合は ValueError になること"""
    images = [str(tmp_path / "missing1.png"), str(tmp_path / "missing2.png")]

    with pytest.raises(ValueError):
        PdfEngine.convertToPdf(images, outputPath=str(tmp_path / "out.pdf"))


def test_convertToPdfRaisesOnEmptyList(tmp_path):
    """画像リストが空なら ValueError になること"""
    with pytest.raises(ValueError):
        PdfEngine.convertToPdf([], outputPath=str(tmp_path / "out.pdf"))


def test_convertToPdfUsesBookTitleForDefaultPath(tmp_path, monkeypatch):
    """outputPath 未指定なら書名付きのDownloadsパスへ保存されること"""
    _useTempHome(tmp_path, monkeypatch)
    _freezeTimestamp(monkeypatch)

    images = [makeImage(str(tmp_path / "page_0001.png"))]

    result = PdfEngine.convertToPdf(images, bookTitle="実践Python - Kindle")

    assert os.path.basename(result) == "実践Python_20260811_1606.pdf"
    assert os.path.exists(result)


# --- ocr -----------------------------------------------------------------


def test_checkOcrAvailabilityReturnsTupleShape():
    """環境依存の実行は行わず、戻り値の形だけを確認する"""
    isAvailable, message = checkOcrAvailability()

    assert isinstance(isAvailable, bool)
    assert isinstance(message, str)
    assert message
