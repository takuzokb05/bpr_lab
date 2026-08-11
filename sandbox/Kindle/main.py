"""
Kindle Auto-Capture to PDF Tool - メインコントローラー

新フロー(v2):
  本を1ページ目で開く → Enter
    → 書名をウィンドウタイトルから取得
    → 開き方向を自動判定(→/←プローブ)
    → クライアント領域を全画面撮影ループ(3連続同一で終端検知)
    → 自動クロップ → PDF化 → OCR(テキスト層付与) → Downloads/{書名}_{日時}.pdf
  → 次の本へ(連続モード)

フォールバック:
  --manual-turn : キーでめくれない本向け。クリック位置を指定してクリックでめくる
  --manual-area : 自動クロップを使わず、ドラッグで撮影範囲を指定する
  --no-ocr      : OCRをスキップして画像のみのPDFを出力する
"""

import argparse
import ctypes
import os
import shutil
import sys
import threading
import time

import pyautogui
from pynput import keyboard

from capture import AreaSelector, CaptureEngine, ClickPositionCapture
from ocr import checkOcrAvailability, runOcr
from pdf_engine import PdfEngine
from postprocess import computeChangingBbox, computeUnionBbox, cropImages
from window_manager import WindowManager


class EmergencyStopListener:
    """Escキー長押しによる緊急停止の監視"""

    def __init__(self, stopEvent: threading.Event, holdDuration: float = 2.0):
        self.stopEvent = stopEvent
        self.holdDuration = holdDuration
        self.escPressed = False
        self.pressStartTime: float | None = None
        self.listener: keyboard.Listener | None = None

    def start(self) -> None:
        """監視を開始する"""
        self.listener = keyboard.Listener(on_press=self._onPress, on_release=self._onRelease)
        self.listener.start()
        print("[停止] 緊急停止: Escキーを2秒間長押しで停止します")

    def stop(self) -> None:
        """監視を終了する"""
        if self.listener:
            self.listener.stop()

    def _onPress(self, key) -> None:
        if key == keyboard.Key.esc and not self.escPressed:
            self.escPressed = True
            self.pressStartTime = time.time()
            threading.Thread(target=self._monitorHold, daemon=True).start()

    def _onRelease(self, key) -> None:
        if key == keyboard.Key.esc:
            self.escPressed = False
            self.pressStartTime = None

    def _monitorHold(self) -> None:
        while self.escPressed:
            if self.pressStartTime and time.time() - self.pressStartTime >= self.holdDuration:
                print("\n[停止] 緊急停止が発動されました!")
                self.stopEvent.set()
                break
            time.sleep(0.1)


def setupDpiAwareness() -> None:
    """
    高DPI環境での座標ずれを防ぐ(150%スケーリング等)

    注意: pyautogui が import 時に SetProcessDPIAware() を呼ぶため、この時点で
    プロセスは既に SYSTEM_AWARE になっている。SetProcessDpiAwareness(2) は
    E_ACCESSDENIED を「戻り値で」返す(例外は出ない)ので、戻り値ではなく
    GetProcessDpiAwareness の実測値で未設定(=0)のときだけ警告する。
    """
    try:
        shcore = ctypes.windll.shcore
        shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_DPI_AWARE(設定済みならE_ACCESSDENIEDが返るだけ)
        awareness = ctypes.c_int(-1)
        shcore.GetProcessDpiAwareness(None, ctypes.byref(awareness))
        if awareness.value == 0:
            print("[警告] プロセスがDPI非認識です。画面スケーリング環境では座標がずれる可能性があります")
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            print("[警告] DPI認識の設定に失敗しました。画面スケーリング環境では座標がずれる可能性があります")


def isWithinPrimaryMonitor(area: tuple[int, int, int, int]) -> bool:
    """
    範囲がプライマリモニタ内に収まっているか確認する

    pyautogui.screenshot はプライマリモニタしか撮影できず、範囲外は例外なく
    黒画像になる(サイレント失敗)ため、事前に明示的に検知する。
    """
    x, y, width, height = area
    primaryWidth = ctypes.windll.user32.GetSystemMetrics(0)
    primaryHeight = ctypes.windll.user32.GetSystemMetrics(1)
    return x >= 0 and y >= 0 and x + width <= primaryWidth and y + height <= primaryHeight


def askYesNo(prompt: str) -> bool:
    """コンソールでy/n確認"""
    while True:
        answer = input(f"{prompt} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False


def captureOneBook(
    windowManager: WindowManager,
    args: argparse.Namespace,
    stopEvent: threading.Event,
    ocrAvailable: bool,
) -> bool:
    """
    1冊分の撮影〜PDF出力を実行する

    Returns:
        bool: 続行可能ならTrue(次の本へ)、緊急停止・致命的失敗ならFalse
    """
    # 連続処理中にKindleが再起動されているとhwndが死ぬため、毎冊で有効性を確認する
    if not windowManager.isWindowValid() and not windowManager.findKindleWindow():
        print("[エラー] Kindleウィンドウを再検出できませんでした。Kindle for PCの起動を確認してください")
        return False

    if not windowManager.activateWindow():
        print("[エラー] Kindleウィンドウをアクティブ化できませんでした")
        return False
    time.sleep(1.0)

    bookTitle = windowManager.getWindowTitle()
    print(f"[書名] {bookTitle}")

    # 撮影範囲の決定
    if args.manual_area:
        selector = AreaSelector()
        area = selector.show()
        if area is None:
            print("[中断] 範囲選択がキャンセルされました")
            return True
        if not selector.confirmSelection(area):
            print("[中断] 範囲が確定されませんでした。もう一度 Enter からやり直してください")
            return True
        windowManager.activateWindow()
        time.sleep(0.5)
    else:
        area = windowManager.getClientRect()
        if area is None:
            print("[エラー] ウィンドウのクライアント領域を取得できませんでした")
            return False

    # pyautoguiの撮影はプライマリモニタ限定(範囲外は黒画像のサイレント失敗になる)
    if not isWithinPrimaryMonitor(area):
        print("[エラー] Kindleウィンドウがプライマリモニタからはみ出しています。メインモニタ内に収めて再実行してください")
        return True

    # ページめくり方式の決定
    if args.manual_turn:
        clickCapture = ClickPositionCapture()
        clickPos = clickCapture.show()
        if clickPos is None:
            print("[中断] クリック位置の指定がキャンセルされました")
            return True
        if not clickCapture.confirmClick(clickPos):
            print("[中断] クリック位置が確定されませんでした。もう一度 Enter からやり直してください")
            return True
        windowManager.activateWindow()
        time.sleep(0.5)
        # pressFnをクリックに差し替えてキー名は無視する
        engine = CaptureEngine(pressFn=lambda _key: pyautogui.click(clickPos[0], clickPos[1]))
        forwardKey = "right"  # ダミー(pressFnが無視する)
        print(f"[設定] クリック位置 {clickPos} でページをめくります")
    else:
        engine = CaptureEngine()
        print("[判定] 開き方向を自動判定しています...")
        detected = engine.detectPageTurnDirection(area)
        if detected is None:
            print("[エラー] 矢印キーでページをめくれない本のようです。--manual-turn オプションで再実行してください")
            engine.cleanup()
            return True
        if detected == "ambiguous":
            print("[エラー] 本が1ページ目で開かれていない可能性があります(前のページが存在するようです)。")
            print("        Kindleで【1ページ目(表紙)】を表示してから、もう一度 Enter してください")
            engine.cleanup()
            return True
        forwardKey = detected
        openingStyle = "左開き(横書き)" if forwardKey == "right" else "右開き(縦書き)"
        print(f"[判定] {openingStyle} と判定しました(進むキー: {forwardKey})")

    # 撮影ループ
    print("\n[開始] 自動撮影を開始します(停止はEsc長押し)")
    try:
        images = engine.autoCapture(area, forwardKey, stopEvent)
    except Exception:
        print(f"[保全] 撮影済み画像は削除せず残しています: {engine.tempDir}")
        raise

    interrupted = stopEvent.is_set()
    if interrupted:
        if not images:
            engine.cleanup()
            return False
        if not askYesNo("途中までの撮影分をPDF化しますか?"):
            # 「PDF化しない」と「画像も捨てる」は別の意思決定。数十分の撮影結果を守る
            print(f"[保全] 撮影済み画像は削除せず残しています: {engine.tempDir}")
            return False

    if not images:
        print("[警告] 撮影された画像がありません")
        engine.cleanup()
        return True

    # ページ数の下限チェック: めくり失敗(フォーカス外れ等)で数枚しか撮れていない場合、
    # 数百ページの本が数ページのPDFとして「完了」してしまう事故を防ぐ
    if not interrupted and len(images) <= 3:
        print(f"[警告] 撮影できたのが {len(images)} ページだけです。ページめくりが効いていない可能性があります")
        print("        (Kindleウィンドウにフォーカスが当たっていない/キー非対応の本など)")
        if not askYesNo("このままPDF化しますか?"):
            engine.cleanup()
            return True

    # 後処理: 自動クロップ(手動範囲指定時はそのまま)
    try:
        if not args.manual_area:
            # ページ間で変化する領域=本文(固定UIを除外)。検出できなければ非白画素方式で代替
            bbox = computeChangingBbox(images) or computeUnionBbox(images)
            if bbox:
                cropImages(images, bbox)
                print(f"[後処理] 余白を自動クロップしました: {bbox}")

        # PDF化 → OCR
        rawPdf = os.path.join(engine.tempDir, "raw.pdf")
        PdfEngine.convertToPdf(images, outputPath=rawPdf)
        finalPath = PdfEngine.getOutputPath(bookTitle)

        if ocrAvailable and not args.no_ocr:
            print("[OCR] テキスト層を付与しています(ページ数によっては数分かかります)...")
            if not runOcr(rawPdf, finalPath):
                print("[警告] OCRに失敗したため、画像のみのPDFを保存します")
                shutil.copyfile(rawPdf, finalPath)
        else:
            shutil.copyfile(rawPdf, finalPath)

        print(f"\n[完了] PDFを保存しました: {finalPath} ({len(images)}ページ)")
    except Exception:
        print(f"[保全] 撮影済み画像は削除せず残しています: {engine.tempDir}")
        raise

    # 成功時のみ一時ファイルを掃除する(失敗時は上のexceptで保全)
    # PDFは既に保存済みなので、ここでの掃除失敗を「本の処理失敗」に格上げしない
    try:
        # cleanup()はtempDirをrmdirするため、先にraw.pdfを消しておく必要がある
        if os.path.exists(rawPdf):
            os.remove(rawPdf)
        engine.cleanup()
    except OSError as e:
        print(f"[警告] 一時ファイルの掃除に失敗しました(PDFは保存済み): {e}")
    return not interrupted


def main() -> int:
    """エントリポイント: Kindle検出 → 連続撮影ループ"""
    parser = argparse.ArgumentParser(description="Kindle Auto-Capture to PDF Tool")
    parser.add_argument("--manual-turn", action="store_true", help="クリックでページをめくる(キー非対応本向け)")
    parser.add_argument("--manual-area", action="store_true", help="撮影範囲をドラッグで手動指定する")
    parser.add_argument("--no-ocr", action="store_true", help="OCRをスキップする")

    # リダイレクト時のcp932でも日本語/絵文字printで落ちないようUTF-8を明示する
    # (--help も日本語のため parse_args より前に行う)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("Kindle Auto-Capture to PDF Tool v2")
    print("=" * 60)

    setupDpiAwareness()

    windowManager = WindowManager()
    if not windowManager.findKindleWindow():
        print("\n[エラー] Kindle for PCが見つかりません。起動してから再実行してください")
        input("\nEnterキーを押して終了...")
        return 1

    ocrAvailable, ocrReason = checkOcrAvailability()
    if ocrAvailable:
        print("[OCR] OCR環境: 利用可能(検索可能PDFを出力します)")
    else:
        print(f"[OCR] OCR環境: 利用不可(画像のみのPDFを出力します)\n{ocrReason}")

    stopEvent = threading.Event()
    emergencyStop = EmergencyStopListener(stopEvent)
    emergencyStop.start()

    try:
        while True:
            answer = input("\n撮影する本を【1ページ目】で開いて Enter (qで終了): ").strip().lower()
            if answer == "q":
                break
            stopEvent.clear()
            try:
                if not captureOneBook(windowManager, args, stopEvent, ocrAvailable):
                    break
            except Exception as e:
                print(f"\n[エラー] 処理中にエラーが発生しました: {e}")
                if not askYesNo("次の本に進みますか?"):
                    break
    finally:
        emergencyStop.stop()

    print("\n終了します")
    return 0


if __name__ == "__main__":
    sys.exit(main())
