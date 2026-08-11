"""
CaptureEngine のロジックテスト

GUI も実 pyautogui も使わず、注入した fake だけで撮影ループを検証する。
中心となる FakeKindle は「キー押下でページが動き、描画には遅延がある」疑似Kindleで、
screenshotFn と pressFn の両方を提供する。固定の画像シーケンスではなくページ状態を
モデル化することで、waitForStablePage が何回ポーリングしても整合が壊れない。
"""

import os
import threading

import pytest
from PIL import Image

from capture import CaptureEngine

# --- テスト用ヘルパー ---------------------------------------------------------

AREA: tuple[int, int, int, int] = (0, 0, 20, 20)

# waitForStablePage の既定ポーリング回数（timeoutSec=5.0 / intervalSec=0.2）
MAX_POLLS = 25


def makeImage(color: str) -> Image.Image:
    """テスト用の単色画像を作る"""
    return Image.new("RGB", (20, 20), color)


def makePages(colors: list[str]) -> list[Image.Image]:
    """色名の並びからページ画像の並びを作る"""
    return [makeImage(color) for color in colors]


class FakeKindle:
    """
    ページめくりに反応する疑似Kindle

    screenshot() を screenshotFn に、press() を pressFn に渡して使う。
    renderDelay を指定すると、キー押下後その回数だけ「旧ページが写り続ける」
    描画遅延を再現する（critical-1 の再現条件）。
    """

    def __init__(
        self,
        pages: list[Image.Image],
        startIndex: int = 0,
        forwardKey: str = "right",
        renderDelay: int = 0,
        backwardStep: int = 1,
    ) -> None:
        self.pages = pages
        self.index = startIndex
        self.forwardKey = forwardKey
        self.backwardKey = "left" if forwardKey == "right" else "right"
        self.renderDelay = renderDelay
        # backwardStep>1 は「戻るキーで元の位置に戻れない本」の模擬（復帰失敗の再現）
        self.backwardStep = backwardStep

        self.displayedIndex = startIndex  # いま画面に写っているページ
        self.pendingRenders = 0  # あと何回スクショすると新ページが写るか
        self.pressedKeys: list[str] = []
        self.screenshotCount = 0

    def press(self, key: str) -> None:
        """キー押下。進む/戻るでページ位置を動かす（端では動かない）"""
        self.pressedKeys.append(key)

        if key == self.forwardKey:
            newIndex = min(self.index + 1, len(self.pages) - 1)
        elif key == self.backwardKey:
            newIndex = max(self.index - self.backwardStep, 0)
        else:
            return

        if newIndex != self.index:
            self.index = newIndex
            self.pendingRenders = self.renderDelay

    def screenshot(self, area: tuple[int, int, int, int]) -> Image.Image:
        """現在画面に写っているページを返す（描画遅延中は旧ページ）"""
        self.screenshotCount += 1

        if self.pendingRenders > 0:
            self.pendingRenders -= 1
            return self.pages[self.displayedIndex]

        self.displayedIndex = self.index
        return self.pages[self.displayedIndex]


class FakeScreen:
    """screenshotFn の代役。用意した画像シーケンスを順に返す（尽きたら最後の画像）"""

    def __init__(self, images: list[Image.Image]) -> None:
        self.images = list(images)
        self.index = 0
        self.callCount = 0

    def __call__(self, area: tuple[int, int, int, int]) -> Image.Image:
        self.callCount += 1
        if self.index < len(self.images):
            image = self.images[self.index]
            self.index += 1
        else:
            image = self.images[-1]
        return image


def noSleep(seconds: float) -> None:
    """sleepFn の代役（何もしない）"""
    return None


def makeEngine(tmpPath, screenshotFn, pressFn) -> CaptureEngine:
    """fake を注入した CaptureEngine を作る"""
    return CaptureEngine(
        tempDir=str(tmpPath),
        screenshotFn=screenshotFn,
        pressFn=pressFn,
        sleepFn=noSleep,
    )


def makeKindleEngine(tmpPath, kindle: FakeKindle, stopEvent=None, stopAfter: int = 0):
    """FakeKindle を screenshotFn/pressFn の両方に繋いだ CaptureEngine を作る"""

    def press(key: str) -> None:
        kindle.press(key)
        # 指定回数押されたら緊急停止がかかる状況を模す
        if stopEvent is not None and stopAfter and len(kindle.pressedKeys) >= stopAfter:
            stopEvent.set()

    return makeEngine(tmpPath, kindle.screenshot, press)


@pytest.fixture
def engine(tmp_path):
    """compareImages など、画面を使わないメソッドの検証用エンジン"""
    return makeEngine(tmp_path, FakeScreen([makeImage("white")]), lambda key: None)


# --- compareImages ------------------------------------------------------------

def testCompareImagesReturnsTrueForIdenticalImages(engine):
    """同一内容の画像は一致と判定される"""
    assert engine.compareImages(makeImage("white"), makeImage("white")) is True


def testCompareImagesReturnsFalseForDifferentImages(engine):
    """内容が異なる画像は不一致と判定される"""
    assert engine.compareImages(makeImage("white"), makeImage("black")) is False


def testCompareImagesReturnsFalseForDifferentSizes(engine):
    """サイズが異なる画像は（内容によらず）不一致と判定される"""
    small = Image.new("RGB", (10, 10), "white")
    large = Image.new("RGB", (20, 20), "white")

    assert engine.compareImages(small, large) is False


def testCompareImagesRejectsTinyDifference(engine):
    """
    全体の0.03%しか違わない2枚を「同一」と判定しない（high-2の回帰）

    旧既定 threshold=0.99 はこの差分を同一と誤判定し、
    「数文字だけ違う次ページ」で終端を誤検知しうる状態だった。
    """
    base = Image.new("RGB", (100, 100), "white")
    modified = base.copy()
    # 10000px 中 3px だけ変更 = 0.03%
    for x in range(3):
        modified.putpixel((x, 0), (0, 0, 0))

    assert engine.compareImages(base, modified) is False
    # 閾値を明示的に緩めた場合のみ「同一」に倒れる（緩和はオプトイン）
    assert engine.compareImages(base, modified, threshold=0.99) is True


# --- waitForStablePage --------------------------------------------------------

def testWaitForStablePageIgnoresStillOldPage(tmp_path):
    """
    静止していても changedFrom と同じなら安定とみなさない（critical-1の回帰）

    キー押下後しばらく旧ページが写り続ける本で、旧ページを「安定」と誤判定すると
    終端検知が誤発火する。新ページが出て静止するまで待つこと。
    """
    oldPage = makeImage("white")
    newPage = makeImage("blue")

    # 旧ページが3回写ってから新ページに切り替わる
    screen = FakeScreen([oldPage, oldPage, oldPage, newPage, newPage])
    engine = makeEngine(tmp_path, screen, lambda key: None)

    result = engine.waitForStablePage(AREA, changedFrom=oldPage)

    assert result.tobytes() == newPage.tobytes()


def testWaitForStablePageReturnsLastImageWhenNeverChanges(tmp_path):
    """changedFrom が最後まで変化しない場合、例外にせず最後の画像を返して打ち切る"""
    stuckPage = makeImage("white")

    screen = FakeScreen([stuckPage])  # 何回撮っても同じ画面
    engine = makeEngine(tmp_path, screen, lambda key: None)

    result = engine.waitForStablePage(AREA, changedFrom=stuckPage)

    assert result.tobytes() == stuckPage.tobytes()
    # ポーリング上限で必ず止まる（無限ループしない）
    assert screen.callCount == MAX_POLLS


def testWaitForStablePageWithoutChangedFromUsesStillnessOnly(tmp_path):
    """changedFrom 省略時は従来どおり「2回連続同一」だけで安定と判定する"""
    page = makeImage("white")

    screen = FakeScreen([page])
    engine = makeEngine(tmp_path, screen, lambda key: None)

    result = engine.waitForStablePage(AREA)

    assert result.tobytes() == page.tobytes()
    assert screen.callCount == 2


# --- detectPageTurnDirection --------------------------------------------------

def testDetectPageTurnDirectionFindsLeftBoundBook(tmp_path):
    """左開き（→で進む本）を1ページ目で判定すると 'right' を返す"""
    kindle = FakeKindle(makePages(["white", "blue", "red"]), startIndex=0, forwardKey="right")
    engine = makeKindleEngine(tmp_path, kindle)

    direction = engine.detectPageTurnDirection(AREA)

    assert direction == "right"
    # right(進む) → left(復帰) → left(前ページ確認・先頭なので動かない)
    assert kindle.pressedKeys == ["right", "left", "left"]
    assert kindle.index == 0  # 1ページ目に戻っている
    # プローブ撮影は保存もカウントもしない
    assert engine.pageCount == 0
    assert engine.capturedImages == []
    assert os.listdir(tmp_path) == []


def testDetectPageTurnDirectionFindsRightBoundBook(tmp_path):
    """右開き（←で進む本）を1ページ目で判定すると 'left' を返す"""
    kindle = FakeKindle(makePages(["white", "blue", "red"]), startIndex=0, forwardKey="left")
    engine = makeKindleEngine(tmp_path, kindle)

    direction = engine.detectPageTurnDirection(AREA)

    assert direction == "left"
    # right(無反応=戻れない=先頭確定) → left(進む) → right(復帰)
    assert kindle.pressedKeys == ["right", "left", "right"]
    assert kindle.index == 0
    assert engine.pageCount == 0


def testDetectPageTurnDirectionReturnsNoneWhenKeysDoNothing(tmp_path):
    """左右どちらのキーにも反応しなければ None を返す"""
    kindle = FakeKindle(makePages(["white"]), startIndex=0)  # 1ページしかない=どちらも動かない
    engine = makeKindleEngine(tmp_path, kindle)

    direction = engine.detectPageTurnDirection(AREA)

    assert direction is None
    assert kindle.pressedKeys == ["right", "left"]
    assert engine.pageCount == 0


def testDetectPageTurnDirectionReturnsAmbiguousWhenRestoreFails(tmp_path):
    """
    元のページに戻せない本では 'ambiguous' を返す（critical-3の回帰）

    backwardStep=2 で「←が2ページ戻る」本を模し、復帰に失敗する状況を作る。
    """
    kindle = FakeKindle(
        makePages(["white", "blue", "red", "green"]),
        startIndex=1,
        forwardKey="right",
        backwardStep=2,
    )
    engine = makeKindleEngine(tmp_path, kindle)

    direction = engine.detectPageTurnDirection(AREA)

    assert direction == "ambiguous"
    assert kindle.pressedKeys == ["right", "left"]


def testDetectPageTurnDirectionReturnsAmbiguousWhenNotOnFirstPage(tmp_path):
    """
    栞位置（途中ページ）で開かれている本では 'ambiguous' を返す（critical-3の回帰）

    開き方向自体は判定できるが、前ページが存在するので撮影開始位置を保証できない。
    """
    kindle = FakeKindle(makePages(["white", "blue", "red"]), startIndex=1, forwardKey="right")
    engine = makeKindleEngine(tmp_path, kindle)

    direction = engine.detectPageTurnDirection(AREA)

    assert direction == "ambiguous"
    # right(進む) → left(復帰) → left(前ページへ=先頭でないと判明) → right(復帰)
    assert kindle.pressedKeys == ["right", "left", "left", "right"]
    assert kindle.index == 1  # 呼び出し前の位置に戻している


# --- autoCapture --------------------------------------------------------------

def testAutoCaptureRemovesExactlyThreeTrailingDuplicates(tmp_path):
    """終端検知時、末尾の重複3枚だけが除去され最終ページは1枚残る"""
    kindle = FakeKindle(makePages(["white", "blue", "red"]))
    engine = makeKindleEngine(tmp_path, kindle)

    result = engine.autoCapture(AREA, "right", threading.Event(), endConsecutive=3)

    assert len(result) == 3
    assert engine.pageCount == 3
    assert result == engine.capturedImages
    # ファイル側も3枚だけ残っている
    assert sorted(os.listdir(tmp_path)) == ["page_0001.png", "page_0002.png", "page_0003.png"]
    for path in result:
        assert os.path.exists(path)


def testAutoCaptureKeepsConsecutiveBlankPages(tmp_path):
    """白紙が3枚続いても終端とはみなさず、本物のページとして残す"""
    # white / 白紙3枚 / red の5ページ
    kindle = FakeKindle(makePages(["white", "black", "black", "black", "red"]))
    engine = makeKindleEngine(tmp_path, kindle)

    result = engine.autoCapture(AREA, "right", threading.Event(), endConsecutive=3)

    assert len(result) == 5
    assert engine.pageCount == 5


def testAutoCaptureCapturesEveryPageOnSlowRenderingBook(tmp_path):
    """
    描画が遅い本でも全ページ撮れる（critical-1の回帰）

    キー押下後2回のポーリング分は旧ページが写る本。旧実装は旧ページを安定と
    誤判定して同一画面を撮り続け、8ページの本が1ページで「完了」していた。
    """
    pages = makePages(["white", "blue", "red", "green", "yellow", "purple", "orange", "gray"])
    kindle = FakeKindle(pages, renderDelay=2)
    engine = makeKindleEngine(tmp_path, kindle)

    result = engine.autoCapture(AREA, "right", threading.Event(), endConsecutive=3)

    assert len(result) == len(pages)
    assert engine.pageCount == len(pages)


def testAutoCaptureStopsOnStopEvent(tmp_path):
    """stopEvent がセットされたらループを中断し、撮影済み画像は保持する"""
    kindle = FakeKindle(makePages(["white", "blue", "red", "green"]))
    stopEvent = threading.Event()
    # 2回目のキー押下で緊急停止がかかる
    engine = makeKindleEngine(tmp_path, kindle, stopEvent=stopEvent, stopAfter=2)

    result = engine.autoCapture(AREA, "right", stopEvent, endConsecutive=3)

    assert stopEvent.is_set()
    assert len(result) == 2
    assert engine.pageCount == 2
    # 中断時は重複除去を行わないので撮影済みファイルはそのまま残る
    assert sorted(os.listdir(tmp_path)) == ["page_0001.png", "page_0002.png"]


def testAutoCaptureUsesForwardKey(tmp_path):
    """指定した forwardKey だけが押される（右開きの本では 'left'）"""
    kindle = FakeKindle(makePages(["white", "blue"]), forwardKey="left")
    engine = makeKindleEngine(tmp_path, kindle)

    engine.autoCapture(AREA, "left", threading.Event(), endConsecutive=3)

    assert set(kindle.pressedKeys) == {"left"}


# --- takeScreenshot -----------------------------------------------------------

def testTakeScreenshotDoesNotAdvanceCountOnSaveFailure(tmp_path):
    """保存に失敗したらページ番号を進めない（欠番防止）"""

    class UnsavableImage:
        """save() が必ず失敗する疑似画像"""

        def save(self, path: str) -> None:
            raise OSError("disk full")

    engine = makeEngine(tmp_path, lambda area: UnsavableImage(), lambda key: None)

    with pytest.raises(OSError):
        engine.takeScreenshot(AREA)

    assert engine.pageCount == 0
    assert engine.capturedImages == []
