"""
OCR Module for Kindle Auto-Capture Tool
画像由来のPDFにテキスト層を付与し、検索可能PDF（NotebookLM取り込み用）にする
"""

import collections
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

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

# ページ上部のうち、書名ヘッダーが載っている割合（クロップ後の画像基準）
HEADER_RATIO = 0.06

# ヘッダーから読み取った書名として認めない文字列（アプリ名だけが写った場合など）
NON_TITLE_WORDS = {"kindle", "amazon kindle", "kindle for pc"}


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


def cleanHeaderText(rawText: str) -> str | None:
    """
    ヘッダーのOCR結果を、ファイル名に使える書名候補に整形する

    日本語のOCRは文字間に空白を入れてくるため（「グロースモ デル」等）、
    日本語文字に挟まれた空白だけを詰める。英単語間の空白は語の区切りなので残す。

    Args:
        rawText: tesseract の生出力

    Returns:
        str | None: 整形後の書名候補。書名とみなせない場合は None
    """
    # 複数行が返った場合は最も長い行を採用する（短い行はノイズであることが多い）
    lines = [line.strip() for line in rawText.splitlines() if line.strip()]
    if not lines:
        return None
    text = max(lines, key=len)

    # 日本語文字に挟まれた空白のみ除去し、残りの連続空白は1つにまとめる
    text = re.sub(r"(?<=[^\x00-\x7F])[ \t]+(?=[^\x00-\x7F])", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    # 記号だけ・極端に短い結果は誤読とみなす
    if len(text) < 4:
        return None
    if not re.search(r"[0-9A-Za-z぀-ヿ一-鿿]", text):
        return None
    if text.strip().lower() in NON_TITLE_WORDS:
        return None

    return text


def extractHeaderTitle(
    imagePath: str,
    headerRatio: float = HEADER_RATIO,
    languages: str = "jpn+eng"
) -> str | None:
    """
    ページ画像の上部を切り出してOCRし、書名ヘッダーを読み取る

    新しいMicrosoft Store版Kindleはウィンドウタイトルが常に "Kindle" で書名を
    含まないため、本文ページ上部に印字されている書名ヘッダーから補う。

    Args:
        imagePath: 対象のページ画像
        headerRatio: 画像高さのうち、上から何割をヘッダーとみなすか
        languages: OCR言語指定

    Returns:
        str | None: 読み取れた書名。読み取れない場合は None
    """
    tesseractPath = _findTesseract()
    if tesseractPath is None:
        return None

    try:
        with Image.open(imagePath) as img:
            width, height = img.size
            stripHeight = max(1, int(height * headerRatio))
            headerStrip = img.crop((0, 0, width, stripHeight))
            headerStrip.load()
    except (OSError, ValueError) as e:
        print(f"⚠️ ヘッダー読み取り用の画像を開けませんでした: {imagePath} ({e})")
        return None

    stripPath = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tempFile:
            stripPath = tempFile.name
        headerStrip.save(stripPath, format="PNG")

        # --psm 7 は「1行のテキスト」前提。取れなければ段落扱い(6)で読み直す
        for pageSegMode in ("7", "6"):
            try:
                result = subprocess.run(
                    [tesseractPath, stripPath, "stdout", "-l", languages, "--psm", pageSegMode],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=60,
                )
            except (subprocess.TimeoutExpired, OSError) as e:
                print(f"⚠️ ヘッダーのOCRに失敗しました ({e})")
                return None

            if result.returncode != 0:
                continue

            title = cleanHeaderText(result.stdout or "")
            if title:
                return title

        return None

    finally:
        if stripPath and os.path.exists(stripPath):
            try:
                os.remove(stripPath)
            except OSError as e:
                print(f"⚠️ 一時ファイルを削除できませんでした: {stripPath} ({e})")


def detectBookTitleFromPages(imagePaths: list[str], sampleCount: int = 3) -> str | None:
    """
    複数ページのヘッダーをOCRし、複数ページで一致した結果だけを書名として採用する

    ヘッダーが無い本では、OCRが背景の模様を拾って 'Tie OOO Ley) hn' のような
    無意味な文字列を返す（実測）。1ページの結果をそのまま信じると、それが
    ファイル名になってしまうため、2ページ以上で同一の文字列が読めた場合のみ
    採用し、それ以外は None を返して呼び出し側の手入力に委ねる。

    表紙・前付けにはヘッダーが無いので、本文中盤（全体の 1/4〜3/4）から選ぶ。

    Args:
        imagePaths: 撮影済みページ画像のパス一覧（順序どおり）
        sampleCount: OCRするページ数

    Returns:
        str | None: 複数ページで一致した書名。確信が持てない場合は None
    """
    if not imagePaths:
        return None

    total = len(imagePaths)
    start = total // 4
    end = max(start + 1, total * 3 // 4)
    span = end - start

    indices = sorted({start + (i * span // max(1, sampleCount)) for i in range(sampleCount)})
    indices = [i for i in indices if 0 <= i < total]

    candidates = [
        title for title in (extractHeaderTitle(imagePaths[i]) for i in indices) if title
    ]

    if len(candidates) < 2:
        return None

    # 同点の場合は先に読み取れたものが採用される（Counter は挿入順を保つ）
    bestTitle, agreementCount = collections.Counter(candidates).most_common(1)[0]

    # 誤読は毎回違う文字列になるため、一致しないものは書名とみなさない
    if agreementCount < 2:
        return None

    return bestTitle
