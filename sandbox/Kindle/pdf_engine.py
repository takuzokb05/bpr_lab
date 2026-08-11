"""
PDF Engine for Kindle Auto-Capture Tool
Converts captured images to optimized PDF
"""

import img2pdf
import os
import re
from datetime import datetime

from PIL import Image


class PdfEngine:
    """Handles PDF generation from captured images"""

    # ファイル名に使えないWindows禁止文字
    FORBIDDEN_CHARS_PATTERN = re.compile(r'[\\/:*?"<>|]')

    # 「- Kindle」「- Kindle for PC」等のアプリ名サフィックス
    # 区切り文字（ハイフン類）は必須。区切りなしの末尾一致を許すと
    # 『はじめてのKindle』のような正当な書名まで削ってしまうため。
    APP_SUFFIX_PATTERN = re.compile(
        r'\s*[-–—―ー]\s*(?:Amazon\s+)?Kindle(?:\s+for\s+PC)?\s*$',
        re.IGNORECASE
    )

    # Windowsの予約デバイス名（このままのファイル名は作成できない）
    RESERVED_DEVICE_NAMES = (
        {"CON", "PRN", "AUX", "NUL"}
        | {f"COM{i}" for i in range(1, 10)}
        | {f"LPT{i}" for i in range(1, 10)}
    )

    # 書名の最大長（拡張子・タイムスタンプ分の余裕を残す）
    MAX_TITLE_LENGTH = 80

    # 書名が取得できない/空になった場合のフォールバック
    FALLBACK_TITLE = "Kindle_Export"

    @staticmethod
    def sanitizeBookTitle(title: str | None) -> str:
        """
        Kindleウィンドウタイトルから、安全なファイル名として使える書名を作る

        日本語はそのまま保持し、Windowsの禁止文字とアプリ名サフィックスのみ取り除く。

        Args:
            title: ウィンドウタイトル（None 可）

        Returns:
            str: ファイル名に使える書名。空になる場合は 'Kindle_Export'
        """
        if not title:
            return PdfEngine.FALLBACK_TITLE

        # Windows禁止文字と制御文字を除去
        sanitized = PdfEngine.FORBIDDEN_CHARS_PATTERN.sub("", title)
        sanitized = "".join(ch for ch in sanitized if ch.isprintable())

        # 「- Kindle for PC」「- Kindle」等のアプリ名サフィックスを（重複していても）除去
        while True:
            stripped = PdfEngine.APP_SUFFIX_PATTERN.sub("", sanitized)
            if stripped == sanitized:
                break
            sanitized = stripped

        # 連続空白を1つにまとめ、前後の空白・ハイフンを落とす
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        sanitized = sanitized.strip(" -–—_")

        # 長すぎる書名を切り詰め、末尾に残った区切り文字を再度落とす
        if len(sanitized) > PdfEngine.MAX_TITLE_LENGTH:
            sanitized = sanitized[:PdfEngine.MAX_TITLE_LENGTH]
        sanitized = sanitized.strip(" -–—_")

        # Windowsは末尾のドットを扱えない
        sanitized = sanitized.rstrip(".")

        if not sanitized:
            return PdfEngine.FALLBACK_TITLE

        # 予約デバイス名（CON, COM1 等）はそのままだとファイルを作成できない
        deviceStem = sanitized.split(".")[0].strip().upper()
        if deviceStem in PdfEngine.RESERVED_DEVICE_NAMES:
            sanitized = f"_{sanitized}"

        return sanitized

    @staticmethod
    def getOutputPath(bookTitle: str | None = None) -> str:
        """
        Generate output path for PDF in Downloads folder

        Args:
            bookTitle: Kindleウィンドウタイトル等の書名（None なら 'Kindle_Export'）

        Returns:
            str: Full path to output PDF file（既存ファイルとは衝突しないパス）
        """
        # Get user's Downloads folder
        downloadsPath = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloadsPath, exist_ok=True)

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        # Create filename
        safeTitle = PdfEngine.sanitizeBookTitle(bookTitle)
        baseName = f"{safeTitle}_{timestamp}"

        outputPath = os.path.join(downloadsPath, f"{baseName}.pdf")

        # 同名が既にある場合は _2, _3... で回避する
        suffixIndex = 2
        while os.path.exists(outputPath):
            outputPath = os.path.join(downloadsPath, f"{baseName}_{suffixIndex}.pdf")
            suffixIndex += 1

        return outputPath

    @staticmethod
    def convertToPdf(
        imagePaths: list[str],
        outputPath: str | None = None,
        bookTitle: str | None = None
    ) -> str:
        """
        Convert list of images to PDF

        Args:
            imagePaths: List of paths to image files (in order)
            outputPath: Optional custom output path. If None, uses Downloads folder
            bookTitle: 書名（outputPath 未指定時のファイル名に使う）

        Returns:
            str: Path to created PDF file

        Raises:
            ValueError: If no images provided or all images are missing
            Exception: If PDF creation fails
        """
        if not imagePaths:
            raise ValueError("画像が指定されていません")

        # 存在しない画像は警告のうえ除外する（1ファイルの欠損で全滅させない）
        validPaths = [
            imgPath for imgPath in imagePaths
            if PdfEngine.validateImages([imgPath])
        ]

        skippedCount = len(imagePaths) - len(validPaths)
        if skippedCount > 0:
            print(f"⚠️ 読み込めない画像 {skippedCount}件を除外してPDF化します")

        if not validPaths:
            raise ValueError("有効な画像が1枚もありません（すべて存在しないか、ファイルではありません）")

        # Use default path if not specified
        if outputPath is None:
            outputPath = PdfEngine.getOutputPath(bookTitle)

        try:
            print(f"📄 PDF生成中... ({len(validPaths)}ページ)")

            # Convert images to PDF
            with open(outputPath, "wb") as f:
                f.write(img2pdf.convert(validPaths))

            # Get file size
            fileSize = os.path.getsize(outputPath)
            fileSizeMb = fileSize / (1024 * 1024)

            print("✅ PDF生成完了!")
            print(f"   📁 保存先: {outputPath}")
            print(f"   📊 ファイルサイズ: {fileSizeMb:.2f} MB")
            print(f"   📖 ページ数: {len(validPaths)}")

            return outputPath

        except Exception as e:
            print(f"❌ PDF生成エラー: {e}")
            raise

    @staticmethod
    def validateImages(imagePaths: list[str]) -> bool:
        """
        Validate that all image files exist and are readable

        存在確認だけでは 0バイトファイルや途中で切れたPNGを素通しし、
        img2pdf.convert が1枚の破損でPDF全体を失敗させるため、
        実際に画像として開けるところまで確認する。

        Args:
            imagePaths: List of paths to validate

        Returns:
            bool: True if all images are valid
        """
        for imgPath in imagePaths:
            if not os.path.exists(imgPath):
                print(f"❌ 画像が見つかりません: {imgPath}")
                return False

            if not os.path.isfile(imgPath):
                print(f"❌ ファイルではありません: {imgPath}")
                return False

            try:
                # verify() は検査後に画像を使えなくするため、検査専用に開き直す
                with Image.open(imgPath) as img:
                    img.verify()
            except (OSError, ValueError, SyntaxError) as e:
                print(f"❌ 画像として読み込めません（破損の可能性）: {imgPath} ({e})")
                return False

        return True
