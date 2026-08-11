"""
OCR Module for Kindle Auto-Capture Tool
画像由来のPDFにテキスト層を付与し、検索可能PDF（NotebookLM取り込み用）にする
"""

import importlib.util
import os
import shutil
import subprocess
import sys

# 不足しているものがあった際に案内する導入手順（日本語）
# Ghostscript は --output-type pdf 指定で不要のため導入手順に含めない（実測確認済み）
INSTALL_GUIDE = (
    "【導入手順】\n"
    "  1. OCRエンジン本体: pip install ocrmypdf\n"
    "  2. Tesseract OCR: winget install UB-Mannheim.TesseractOCR\n"
    "     ※ winget導入では eng/jpn の言語データが同梱される（2026-08時点で実測確認済み）\n"
    "  ※ インストール後はターミナルを開き直して PATH を反映させてください"
)

# winget既定のインストール先（PATH未反映の端末向けフォールバック）
DEFAULT_TESSERACT_DIR = r"C:\Program Files\Tesseract-OCR"


def _findTesseract() -> str | None:
    """tesseract実行ファイルを探す。PATHになければ既定インストール先も見る"""
    found = shutil.which("tesseract")
    if found:
        return found
    defaultExe = os.path.join(DEFAULT_TESSERACT_DIR, "tesseract.exe")
    if os.path.isfile(defaultExe):
        # ocrmypdf のサブプロセスからも見えるよう PATH に足しておく
        os.environ["PATH"] = DEFAULT_TESSERACT_DIR + os.pathsep + os.environ.get("PATH", "")
        return defaultExe
    return None


def checkOcrAvailability() -> tuple[bool, str]:
    """
    OCR実行環境（ocrmypdf / tesseract / 日本語言語データ）の可用性を確認する

    Returns:
        Tuple[bool, str]: (利用可能か, 日本語の説明メッセージ)
            利用不可の場合、メッセージには不足内容と導入手順が含まれる
    """
    # ① Python パッケージ ocrmypdf
    if importlib.util.find_spec("ocrmypdf") is None:
        return (
            False,
            "OCRライブラリ ocrmypdf がインストールされていません。\n" + INSTALL_GUIDE,
        )

    # ② tesseract 実行ファイル（PATH → 既定インストール先の順で探す）
    tesseractPath = _findTesseract()
    if tesseractPath is None:
        return (
            False,
            "Tesseract OCR 本体が見つかりません（PATH が通っていない可能性があります）。\n"
            + INSTALL_GUIDE,
        )

    # ③ 日本語言語データ (jpn)
    try:
        result = subprocess.run(
            [tesseractPath, "--list-langs"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return (
            False,
            f"Tesseract の言語一覧取得がタイムアウトしました: {tesseractPath}\n" + INSTALL_GUIDE,
        )
    except OSError as e:
        return (
            False,
            f"Tesseract を実行できませんでした: {tesseractPath} ({e})\n" + INSTALL_GUIDE,
        )

    # tesseract のバージョンによって一覧が stdout / stderr のどちらにも出るため両方を見る
    langOutput = f"{result.stdout or ''}\n{result.stderr or ''}"
    availableLangs = [line.strip() for line in langOutput.splitlines() if line.strip()]

    if result.returncode != 0:
        return (
            False,
            f"Tesseract の言語一覧取得に失敗しました (終了コード {result.returncode}): "
            f"{langOutput.strip()}\n" + INSTALL_GUIDE,
        )

    if "jpn" not in availableLangs:
        return (
            False,
            "Tesseract に日本語言語データ (jpn) がインストールされていません。\n"
            f"  検出された言語: {', '.join(availableLangs) or '(なし)'}\n" + INSTALL_GUIDE,
        )

    return (True, f"OCR実行環境は利用可能です (tesseract: {tesseractPath}, 日本語データ: あり)")


def runOcr(
    inputPdf: str,
    outputPdf: str,
    languages: str = "jpn+eng",
    timeoutSec: int = 1800
) -> bool:
    """
    ocrmypdf を実行して、PDFに検索可能なテキスト層を付与する

    Args:
        inputPdf: 入力PDF（画像のみのPDF）のパス
        outputPdf: 出力PDF（テキスト層付き）のパス
        languages: OCR言語指定（ocrmypdf の -l に渡す）
        timeoutSec: 実行タイムアウト（秒）

    Returns:
        bool: 成功したら True。失敗時は理由をprintしたうえで False
    """
    if not os.path.exists(inputPdf):
        print(f"❌ OCR対象のPDFが見つかりません: {inputPdf}")
        return False

    # checkOcrAvailability を経由せず単独で呼ばれても動くよう、ここでも探索する
    # （_findTesseract は既定インストール先を見つけた場合に PATH へ追加する副作用があり、
    #   これが無いと ocrmypdf のサブプロセスが tesseract を見つけられない）
    if _findTesseract() is None:
        print("❌ Tesseract OCR 本体が見つかりません（PATH が通っていない可能性があります）。")
        print(INSTALL_GUIDE)
        return False

    # --output-type pdf: PDF/A変換を行わない（Ghostscript不要になる・実測確認済み）
    # --optimize 0: pngquant等の外部最適化ツールを呼ばない（Windowsで未導入のため）
    command: list[str] = [
        sys.executable,
        "-m",
        "ocrmypdf",
        "-l",
        languages,
        "--output-type",
        "pdf",
        "--optimize",
        "0",
        inputPdf,
        outputPdf,
    ]

    print(f"🔍 OCR処理中... (言語: {languages}) ※ ページ数によっては数分かかります")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeoutSec,
        )
    except subprocess.TimeoutExpired:
        print(f"❌ OCR処理がタイムアウトしました ({timeoutSec}秒)。ページ数が多い場合は timeoutSec を延ばしてください。")
        return False
    except OSError as e:
        print(f"❌ OCRプロセスを起動できませんでした: {e}")
        return False

    if result.returncode != 0:
        print(f"❌ OCR処理に失敗しました (終了コード {result.returncode})")

        # 例外は握りつぶさず、原因追跡に必要な stderr の要点を出す
        errorLines = [line for line in (result.stderr or "").splitlines() if line.strip()]
        if errorLines:
            print("   --- ocrmypdf のエラー出力（末尾）---")
            for line in errorLines[-10:]:
                print(f"   {line}")
        else:
            print("   （エラー出力はありませんでした）")

        print("   ヒント: checkOcrAvailability() で実行環境を確認してください")
        return False

    if not os.path.exists(outputPdf):
        print(f"❌ OCRは正常終了しましたが、出力PDFが生成されていません: {outputPdf}")
        return False

    fileSizeMb = os.path.getsize(outputPdf) / (1024 * 1024)
    print("✅ OCR完了! (テキスト検索可能なPDF)")
    print(f"   📁 保存先: {outputPdf}")
    print(f"   📊 ファイルサイズ: {fileSizeMb:.2f} MB")

    return True
