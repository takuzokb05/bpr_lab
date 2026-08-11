"""
Capture Module for Kindle Auto-Capture Tool

範囲指定UI（手動フォールバック用）、撮影、画像比較、キー方式のページめくり制御を担当する。
ページめくりはマウスクリックではなく矢印キー（left / right）で行う。
"""

import os
import tempfile
import threading
import time
import tkinter as tk
from tkinter import messagebox
from collections.abc import Callable

import pyautogui
from PIL import Image, ImageChops


class AreaSelector:
    """ドラッグで撮影範囲を選択する半透明オーバーレイ（手動フォールバック用）"""

    def __init__(self) -> None:
        self.selectedArea: tuple[int, int, int, int] | None = None
        self.startX: int | None = None
        self.startY: int | None = None
        self.rect: int | None = None
        self.root: tk.Tk | None = None
        # self.canvas は show() で生成する（tk.Canvas）

    def show(self) -> tuple[int, int, int, int] | None:
        """
        オーバーレイを表示して範囲選択させる

        Returns:
            Optional[Tuple[int, int, int, int]]: (x, y, width, height)。
            Escキーでキャンセルされた場合は None
        """
        self.selectedArea = None

        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')

        self.canvas = tk.Canvas(
            self.root,
            bg='black',
            highlightthickness=0,
            cursor='cross'
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        label = tk.Label(
            self.root,
            text="📖 Kindleの本文エリアをドラッグで選択してください（Escでキャンセル）",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='black'
        )
        label.place(relx=0.5, rely=0.05, anchor='center')

        self.canvas.bind('<Button-1>', self._onMouseDown)
        self.canvas.bind('<B1-Motion>', self._onMouseDrag)
        self.canvas.bind('<ButtonRelease-1>', self._onMouseUp)

        # Escでキャンセル。キーイベントを拾うためフォーカスを強制的に奪う
        self.root.bind('<Escape>', self._onCancel)
        self.root.focus_force()

        self.root.mainloop()

        return self.selectedArea

    def _onMouseDown(self, event) -> None:
        """マウス押下: 選択矩形の起点を記録する"""
        self.startX = event.x
        self.startY = event.y

        self.rect = self.canvas.create_rectangle(
            self.startX, self.startY, self.startX, self.startY,
            outline='red', width=3
        )

    def _onMouseDrag(self, event) -> None:
        """マウスドラッグ: 選択矩形を追従させる"""
        if self.rect is not None and self.startX is not None and self.startY is not None:
            self.canvas.coords(self.rect, self.startX, self.startY, event.x, event.y)

    def _onMouseUp(self, event) -> None:
        """マウス解放: 範囲を確定してオーバーレイを閉じる"""
        if self.startX is None or self.startY is None:
            return

        endX = event.x
        endY = event.y

        x = min(self.startX, endX)
        y = min(self.startY, endY)
        width = abs(endX - self.startX)
        height = abs(endY - self.startY)

        # 小さすぎる範囲は誤操作とみなして選択をやり直させる
        if width < 50 or height < 50:
            messagebox.showerror("エラー", "選択範囲が小さすぎます。もう一度選択してください。")
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = None
            return

        self.selectedArea = (x, y, width, height)
        self._closeOverlay()

    def _onCancel(self, event=None) -> None:
        """Escキー: 選択を破棄してオーバーレイを閉じる"""
        self.selectedArea = None
        self._closeOverlay()

    def _closeOverlay(self) -> None:
        """オーバーレイを破棄する（二重destroy防止）"""
        if self.root is None:
            return

        root = self.root
        self.root = None
        root.quit()
        root.destroy()

    def confirmSelection(self, area: tuple[int, int, int, int]) -> bool:
        """
        選択範囲の確認ダイアログを表示する

        Args:
            area: (x, y, width, height)

        Returns:
            bool: ユーザーが承認したら True
        """
        root = tk.Tk()
        root.withdraw()

        result = messagebox.askyesno(
            "範囲確認",
            f"この範囲で正しいですか？\n\n"
            f"位置: ({area[0]}, {area[1]})\n"
            f"サイズ: {area[2]} x {area[3]} px",
            icon='question'
        )

        root.destroy()
        return result


class ClickPositionCapture:
    """ページめくり位置を1クリックで取得するオーバーレイ（手動フォールバック用）"""

    def __init__(self) -> None:
        self.clickPosition: tuple[int, int] | None = None
        self.root: tk.Tk | None = None

    def show(self) -> tuple[int, int] | None:
        """
        オーバーレイを表示してクリック位置を1点取得する

        Returns:
            Optional[Tuple[int, int]]: (x, y) のスクリーン絶対座標。
            Escキーでキャンセルされた場合は None
        """
        self.clickPosition = None

        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')

        # 案内文は画面中央だとクリックしたい位置と重なるため上端に置く
        label = tk.Label(
            self.root,
            text="👆 「次へ」ボタン（またはページ右端）を1回クリックしてください（Escでキャンセル）",
            font=('Arial', 16, 'bold'),
            fg='yellow',
            bg='black'
        )
        label.place(relx=0.5, rely=0.05, anchor='center')

        self.root.bind('<Button-1>', self._onClick)
        self.root.bind('<Escape>', self._onCancel)
        self.root.focus_force()

        self.root.mainloop()

        return self.clickPosition

    def _onClick(self, event) -> None:
        """クリック: スクリーン絶対座標を記録して閉じる"""
        self.clickPosition = (event.x_root, event.y_root)
        self._closeOverlay()

    def _onCancel(self, event=None) -> None:
        """Escキー: 取得を破棄して閉じる"""
        self.clickPosition = None
        self._closeOverlay()

    def _closeOverlay(self) -> None:
        """オーバーレイを破棄する（二重destroy防止）"""
        if self.root is None:
            return

        root = self.root
        self.root = None
        root.quit()
        root.destroy()

    def confirmClick(self, position: tuple[int, int]) -> bool:
        """
        クリック位置の確認ダイアログを表示する

        Args:
            position: (x, y)

        Returns:
            bool: ユーザーが承認したら True
        """
        root = tk.Tk()
        root.withdraw()

        result = messagebox.askyesno(
            "クリック位置確認",
            f"このクリック位置で正しいですか？\n\n"
            f"座標: ({position[0]}, {position[1]})",
            icon='question'
        )

        root.destroy()
        return result


class CaptureEngine:
    """撮影・画像比較・キー方式の自動撮影ループを担う中核クラス"""

    def __init__(
        self,
        tempDir: str | None = None,
        screenshotFn: Callable[[tuple[int, int, int, int]], Image.Image] | None = None,
        pressFn: Callable[[str], None] | None = None,
        sleepFn: Callable[[float], None] | None = None,
    ) -> None:
        """
        Args:
            tempDir: 一時PNGの保存先。未指定なら一時ディレクトリを作る
            screenshotFn: 範囲を受け取り PIL Image を返す関数（テスト注入用）
            pressFn: キー名を受け取り押下する関数（テスト注入用）
            sleepFn: 秒数を受け取り待機する関数（テスト注入用）
        """
        self.tempDir: str = tempDir or tempfile.mkdtemp(prefix="kindle_capture_")
        os.makedirs(self.tempDir, exist_ok=True)

        self.capturedImages: list[str] = []
        self.pageCount: int = 0

        self.screenshotFn: Callable[[tuple[int, int, int, int]], Image.Image] = (
            screenshotFn or self._defaultScreenshot
        )
        self.pressFn: Callable[[str], None] = pressFn or pyautogui.press
        self.sleepFn: Callable[[float], None] = sleepFn or time.sleep

    @staticmethod
    def _defaultScreenshot(area: tuple[int, int, int, int]) -> Image.Image:
        """指定範囲を pyautogui で撮影する（既定の screenshotFn）"""
        return pyautogui.screenshot(region=area)

    def takeScreenshot(self, area: tuple[int, int, int, int]) -> tuple[str, Image.Image]:
        """
        指定範囲を撮影し、一時ディレクトリにPNG保存する

        Args:
            area: (x, y, width, height)

        Returns:
            Tuple[str, Image.Image]: (保存先パス, 撮影した画像)
        """
        image = self.screenshotFn(area)

        # 保存に成功してからカウンタとリストを進める。
        # 先に加算すると保存失敗時にページ番号が欠番になり、以降のファイル名がずれる
        nextPageNumber = self.pageCount + 1
        filename = f"page_{nextPageNumber:04d}.png"
        filepath = os.path.join(self.tempDir, filename)
        image.save(filepath)

        self.pageCount = nextPageNumber
        self.capturedImages.append(filepath)

        return filepath, image

    def compareImages(
        self,
        imgA: Image.Image,
        imgB: Image.Image,
        threshold: float = 1.0
    ) -> bool:
        """
        メモリ上の2画像が同一とみなせるかを判定する（ディスク再読込はしない）

        静止した画面のスクリーンショットはビット単位で一致するため、既定では
        完全一致だけを「同一」とする。閾値を緩めると「数文字だけ違う次ページ」を
        同一と誤判定して終端を誤検知する（旧既定の0.99は、全体の0.03%しか
        違わない2枚を同一と判定していた）。

        Args:
            imgA: 比較元の画像
            imgB: 比較先の画像
            threshold: 同一とみなすチャンネル一致率 (0.0〜1.0)。既定の 1.0 は
                完全一致のみ。1.0未満を指定した場合は、RGB各チャンネル値のうち
                差分が0だったものの割合が threshold 以上なら同一とみなす
                （ピクセル単位ではなくチャンネル単位の割合であることに注意）

        Returns:
            bool: 同一とみなせるなら True。サイズが違う場合は False
        """
        if imgA is None or imgB is None:
            return False

        if imgA.size != imgB.size:
            return False

        # チャンネル数を揃える（ヒストグラムのビン位置を固定するため）
        rgbA = imgA.convert("RGB")
        rgbB = imgB.convert("RGB")

        diff = ImageChops.difference(rgbA, rgbB)

        # 完全一致の高速判定（差分が全て0なら getbbox() は None を返す）
        if diff.getbbox() is None:
            return True

        if threshold >= 1.0:
            return False

        # 完全一致でない場合のみ、チャンネル一致率で緩く判定する
        histogram = diff.histogram()

        totalChannelValues = sum(histogram)
        if totalChannelValues == 0:
            return False

        # 差分0のビン（R/G/Bそれぞれの先頭ビン）が一致したチャンネル値の数
        identicalChannelValues = histogram[0] + histogram[256] + histogram[512]
        similarity = identicalChannelValues / totalChannelValues

        return similarity >= threshold

    def waitForStablePage(
        self,
        area: tuple[int, int, int, int],
        changedFrom: Image.Image | None = None,
        timeoutSec: float = 5.0,
        intervalSec: float = 0.2
    ) -> Image.Image:
        """
        ページめくり後、描画が完了するまで待つ（固定待機の置き換え）

        changedFrom を渡した場合、「静止していること」だけでは安定とみなさない。
        描画の遅い本ではキー押下後しばらく旧ページが写り続けるため、静止だけを
        条件にすると旧ページを安定と誤判定し、直後の撮影で同一画面が並んで
        終端検知が誤発火する（実測で8ページの本が1ページで「完了」した）。
        そこで次の2条件を両方満たしたときだけ安定とみなす:
          1. changedFrom と異なる画像になっている（＝描画が切り替わった）
          2. 直前のポーリングと同一である（＝描画が静止した）

        タイムアウトしても例外にはせず、最後に撮れた画像を返す。
        ここでの撮影はプローブなのでファイル保存も pageCount 更新も行わない。

        Args:
            area: (x, y, width, height)
            changedFrom: めくる前のページ画像。None なら静止のみで安定と判定する
            timeoutSec: 最大待機時間
            intervalSec: ポーリング間隔

        Returns:
            Image.Image: 安定したとみなした画像（タイムアウト時は最後に撮れた画像）
        """
        # キー押下直後は描画が始まってすらいないので、まず1インターバル置く
        self.sleepFn(intervalSec)

        # int() だと浮動小数点誤差で1回減る（5.0/0.2 = 24.999...）ため round で丸める
        maxPolls = max(2, round(timeoutSec / intervalSec))

        previousImage: Image.Image = self.screenshotFn(area)

        for _ in range(maxPolls - 1):
            self.sleepFn(intervalSec)
            currentImage = self.screenshotFn(area)

            isStill = self.compareImages(previousImage, currentImage)
            hasChanged = changedFrom is None or not self.compareImages(changedFrom, currentImage)

            if isStill and hasChanged:
                return currentImage

            previousImage = currentImage

        if changedFrom is not None and self.compareImages(changedFrom, previousImage):
            print("⚠️ ページの変化を検知できませんでした")
        else:
            print("⚠️ ページ描画の安定を検知できませんでした（タイムアウト）")

        return previousImage

    def detectPageTurnDirection(self, area: tuple[int, int, int, int]) -> str | None:
        """
        本の開き方向（進むキー）を判定し、あわせて1ページ目にいることを検証する

        開き方向だけを見ると、栞位置（続きから）で開かれた本でも判定が成立して
        しまい、途中ページから撮影を始める事故が起きる。そのため「前のページが
        存在しないこと」まで確認し、確認できない場合は 'ambiguous' を返して
        呼び出し側に判断を委ねる。

        判定プロトコル:
          ① 現画面 A を撮影
          ② right を押す → B = waitForStablePage(changedFrom=A)
          ③ B ≠ A（rightで動いた）:
             - left を押して復帰。復帰画像が A と一致しなければ 'ambiguous'
               （元の位置に戻せない以上、どこから撮り始めるか保証できない）
             - さらに left を押して前ページの有無を調べる
                 変化する   → 前ページが存在する＝1ページ目ではないので、
                              right で復帰して 'ambiguous'
                 変化しない → 先頭確定なので 'right'（左開き）
          ④ B == A（right無反応）で left を押すと変化する:
             right が効かない＝これ以上戻れない＝先頭とみなせるので、
             right で復帰して 'left'（右開き）。復帰に失敗したら 'ambiguous'
          ⑤ 左右どちらも無反応なら None（矢印キー非対応の本）

        プローブ撮影は pageCount / capturedImages を汚染しない。

        Args:
            area: (x, y, width, height)

        Returns:
            str | None: 'right'（左開き）/ 'left'（右開き）/
            'ambiguous'（開き方向は取れたが1ページ目である保証がない）/
            None（矢印キーに反応しない）
        """
        print("🔍 ページめくり方向を判定中...")

        # ① 現在の画面
        imageA = self.screenshotFn(area)

        # ② right で進むか試す
        self.pressFn('right')
        imageB = self.waitForStablePage(area, changedFrom=imageA)

        if not self.compareImages(imageA, imageB):
            # ③ right で変化した = 進む方向は right（左開き）
            self.pressFn('left')
            restored = self.waitForStablePage(area, changedFrom=imageB)

            if not self.compareImages(imageA, restored):
                print("⚠️ 元のページに戻せませんでした")
                return 'ambiguous'

            # 前ページの有無を確認する（変化しなければ1ページ目）
            print("   前ページの有無を確認中（変化がなければ1ページ目です）...")
            self.pressFn('left')
            probe = self.waitForStablePage(area, changedFrom=restored)

            if not self.compareImages(imageA, probe):
                print("⚠️ 前のページが存在します（1ページ目ではありません）")
                self.pressFn('right')
                self.waitForStablePage(area, changedFrom=probe)
                return 'ambiguous'

            print("✅ 左開きの本と判定しました（進む: →）")
            return 'right'

        # ④ right が無反応 → left を試す
        self.pressFn('left')
        imageC = self.waitForStablePage(area, changedFrom=imageA)

        if not self.compareImages(imageA, imageC):
            # left で進む = 右開き。right が無反応＝これ以上戻れない＝先頭とみなせる
            self.pressFn('right')
            restored = self.waitForStablePage(area, changedFrom=imageC)

            if not self.compareImages(imageA, restored):
                print("⚠️ 元のページに戻せませんでした")
                return 'ambiguous'

            print("✅ 右開きの本と判定しました（進む: ←）")
            return 'left'

        # ⑤ どちらのキーにも反応しない（キー操作非対応・フォーカス外れ等）
        print("❌ 矢印キーでページが変化しませんでした")
        return None

    def autoCapture(
        self,
        area: tuple[int, int, int, int],
        forwardKey: str,
        stopEvent: threading.Event,
        endConsecutive: int = 3
    ) -> list[str]:
        """
        自動撮影のメインループ

        直前ページとの一致が endConsecutive 回連続したら終端とみなし、
        末尾の重複 endConsecutive 枚を破棄して終了する。

        白紙ページについて: 白紙が2枚続いた程度では一致カウンタは endConsecutive に
        届かず（次のページで差分が出てカウンタがリセットされる）、本物のページとして残る。
        終了するのは「同じ画面が endConsecutive + 1 枚連続で撮れた」場合のみ。

        Args:
            area: 撮影範囲 (x, y, width, height)
            forwardKey: 進む方向のキー名（'right' または 'left'）
            stopEvent: 緊急停止用のイベント
            endConsecutive: 終端とみなす連続一致回数

        Returns:
            List[str]: 撮影した画像のパス一覧（順序どおり）
        """
        print("\n🚀 自動撮影開始!")
        print("   ⏸️  停止するにはEscキーを2秒間長押ししてください\n")

        previousImage: Image.Image | None = None
        sameCount = 0

        while not stopEvent.is_set():
            # ① 現ページを撮影
            _, currentImage = self.takeScreenshot(area)

            # ② メモリ上の直前ページと比較して終端を判定
            if previousImage is not None and self.compareImages(previousImage, currentImage):
                sameCount += 1

                if sameCount >= endConsecutive:
                    print(f"\n✅ 最終ページを検出しました（同一画面が{endConsecutive + 1}枚連続）")
                    self._discardTrailingDuplicates(endConsecutive)
                    break
            else:
                sameCount = 0

            previousImage = currentImage

            # ③ 停止要求のチェック
            if stopEvent.is_set():
                print("\n⏸️  ユーザーによって停止されました")
                break

            # ④ キーでページをめくる
            self.pressFn(forwardKey)

            # ⑤ 描画完了まで待つ（直前ページから「変化して静止する」まで待つ。
            #    静止だけを条件にすると描画途中の旧ページを次ページとして撮ってしまう）
            self.waitForStablePage(area, changedFrom=currentImage)

            # ⑥ 進捗表示
            print(f"📸 ページ {self.pageCount} を撮影")

        print(f"\n📊 撮影完了: 合計 {self.pageCount} ページ")
        return self.capturedImages

    def _discardTrailingDuplicates(self, count: int) -> None:
        """
        末尾の重複ページを count 枚、ファイル・リスト・pageCount から取り除く

        Args:
            count: 破棄する枚数
        """
        for _ in range(count):
            if not self.capturedImages:
                break

            duplicatePath = self.capturedImages.pop()
            self.pageCount -= 1

            if os.path.exists(duplicatePath):
                try:
                    os.remove(duplicatePath)
                except OSError as e:
                    print(f"⚠️ 重複ページの削除に失敗: {duplicatePath} ({e})")

    def cleanup(self) -> None:
        """
        一時ファイルを削除する

        注意: 呼ぶかどうかは呼び出し側の責務。エラー時に撮影済み画像を勝手に消さないよう、
        autoCapture の内部からは決して呼ばない。
        """
        try:
            for imagePath in self.capturedImages:
                if os.path.exists(imagePath):
                    os.remove(imagePath)

            if os.path.exists(self.tempDir):
                os.rmdir(self.tempDir)

        except OSError as e:
            print(f"⚠️ クリーンアップエラー: {e}")
