"""
PDF Engine for Kindle Auto-Capture Tool
Converts captured images to optimized PDF
"""

import img2pdf
import os
import re
import shutil
import tempfile
from datetime import datetime

from PIL import Image

# PDFに埋め込む画像のJPEG品質。
# NotebookLM等の取り込み先は1ソース200MBが上限で、PNGのままだと約290画面で超過する
# （実測: 174画面で120MB = 0.69MB/画面）。q80ならサイズは約54%に減り、
# 図中の小さな文字も判読できることを実測で確認済み。
JPEG_QUALITY = 80


class PdfEngine:
    """Handles PDF generation from captured images"""

    # ファイル名に使えないWindows禁止文字
    FORBIDDEN_CHARS_PATTERN = re.compile(r'[\\/:*?"<>|]')

    # 書名を含まない汎用ウィンドウタイトル（新Store版Kindleは常に "Kindle" を返す）
    GENERIC_WINDOW_TITLES = {"kindle", "amazon kindle", "kindle for pc"}

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
    def isGenericWindowTitle(title: str | None) -> bool:
        """
        ウィンドウタイトルが書名を含まない汎用名か判定する

        旧Kindle for PCは「書名 - Kindle」だったが、新しいMicrosoft Store版は
        常に "Kindle" を返すため、これを書名として採用してはいけない。

        Args:
            title: ウィンドウタイトル（None 可）

        Returns:
            bool: 書名として使えない汎用名なら True
        """
        if not title:
            return True

        normalized = re.sub(r"\s+", " ", title).strip().lower()
        return normalized in PdfEngine.GENERIC_WINDOW_TITLES

    @staticmethod
    def _stageAsJpeg(imagePaths: list[str], stagingDir: str, quality: int) -> list[str]:
        """
        PDF埋め込み用に、画像をJPEGへ変換した一時ファイル群を作る

        1枚の変換失敗で撮影分を失わないよう、失敗したページは元の画像パスを
        そのまま使う（PDFは生成できるが、そのページだけ元サイズのまま残る）。

        Args:
            imagePaths: 変換元の画像パス一覧
            stagingDir: 変換後ファイルの置き場（呼び出し側が後始末する）
            quality: JPEG品質 (1-95)

        Returns:
            list[str]: img2pdf に渡すパス一覧（順序は入力どおり）
        """
        stagedPaths: list[str] = []
        failedCount = 0

        for index, imagePath in enumerate(imagePaths):
            jpegPath = os.path.join(stagingDir, f"page_{index:04d}.jpg")
            try:
                with Image.open(imagePath) as img:
                    # JPEGはアルファチャンネルを扱えないためRGBに落とす
                    rgbImage = img.convert("RGB")
                    rgbImage.load()

                rgbImage.save(jpegPath, format="JPEG", quality=quality, optimize=True)
                stagedPaths.append(jpegPath)

            except (OSError, ValueError) as e:
                print(f"⚠️ JPEG変換に失敗しました（元画像のまま埋め込みます）: "
                      f"{os.path.basename(imagePath)} ({e})")
                stagedPaths.append(imagePath)
                failedCount += 1

        if failedCount:
            print(f"⚠️ JPEG変換に失敗したページ: {failedCount}件")

        return stagedPaths

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
        bookTitle: str | None = None,
        jpegQuality: int | None = JPEG_QUALITY
    ) -> str:
        """
        Convert list of images to PDF

        Args:
            imagePaths: List of paths to image files (in order)
            outputPath: Optional custom output path. If None, uses Downloads folder
            bookTitle: 書名（outputPath 未指定時のファイル名に使う）
            jpegQuality: 埋め込み時のJPEG品質。None なら元画像（PNG）のまま埋め込む

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

        # JPEG化は一時ディレクトリで行い、撮影済みのPNGには手を触れない
        # （失敗時に元画像から作り直せるようにするため）
        stagingDir: str | None = None

        try:
            print(f"📄 PDF生成中... ({len(validPaths)}ページ)")

            if jpegQuality is None:
                embedPaths = validPaths
            else:
                print(f"🗜️ 画像をJPEG(q{jpegQuality})に変換しています...")
                stagingDir = tempfile.mkdtemp(prefix="kindle_jpeg_")
                embedPaths = PdfEngine._stageAsJpeg(validPaths, stagingDir, jpegQuality)

            # Convert images to PDF
            with open(outputPath, "wb") as f:
                f.write(img2pdf.convert(embedPaths))

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

        finally:
            # 中間JPEGはPDFに書き出した時点で不要（元のPNGは呼び出し側が管理する）
            if stagingDir and os.path.isdir(stagingDir):
                shutil.rmtree(stagingDir, ignore_errors=True)

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
