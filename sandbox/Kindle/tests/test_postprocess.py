"""
postprocess モジュールのテスト
本文領域の外接矩形計算とクロップの挙動を検証する
"""

import os
import stat
from collections.abc import Sequence

import pytest
from PIL import Image, ImageDraw

import postprocess
from postprocess import computeChangingBbox, computeUnionBbox, cropImages

# テスト用ページのサイズ
PAGE_SIZE = (200, 300)

# 全ページに常時表示される固定UI（Kindleのヘッダー・進捗バーを模したもの）
FIXED_UI_RECT = (0, 0, 199, 20)


def makePage(
    path: str,
    rects: Sequence[tuple[int, int, int, int]],
    size: tuple[int, int] = PAGE_SIZE
) -> str:
    """
    白背景に黒矩形を描いたテスト用ページ画像を作る

    Args:
        path: 保存先パス
        rects: 黒で塗る矩形 (x0, y0, x1, y1) の一覧（座標は両端含む）
        size: 画像サイズ

    Returns:
        str: 保存したパス
    """
    image = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(image)

    for rect in rects:
        draw.rectangle(list(rect), fill="black")

    image.save(path)
    return path


def makePageWithFixedUi(
    path: str,
    bodyRects: Sequence[tuple[int, int, int, int]]
) -> str:
    """固定UI（ヘッダー帯）付きのページ画像を作る"""
    return makePage(path, [FIXED_UI_RECT, *bodyRects])


# --- computeChangingBbox -------------------------------------------------


def test_computeChangingBboxExcludesFixedUi(tmp_path):
    """全ページ共通の固定UIが除外され、変化する本文領域だけが返ること"""
    page1 = makePageWithFixedUi(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])
    page2 = makePageWithFixedUi(str(tmp_path / "page_0002.png"), [(30, 100, 60, 200)])

    changingBbox = computeChangingBbox([page1, page2], marginPx=8)

    # 変化するのは本文2箇所のみ。生の差分bboxは (30, 60, 81, 201) で、そこに余白8px
    assert changingBbox == (22, 52, 89, 209)

    # 対照: computeUnionBbox は固定UIを本文とみなすため、上端が0まで広がってしまう
    unionBbox = computeUnionBbox([page1, page2], marginPx=8)
    assert unionBbox is not None
    assert unionBbox[1] == 0
    assert changingBbox[1] > unionBbox[1]


def test_computeChangingBboxSamplesFirstAndLastPage(tmp_path):
    """サンプリングで先頭と末尾のページが必ず比較されること"""
    pages = [
        makePageWithFixedUi(str(tmp_path / f"page_{i:04d}.png"), [(50, 60, 80, 90)])
        for i in range(4)
    ]
    # 末尾ページだけ本文が追加で変化する
    pages.append(
        makePageWithFixedUi(
            str(tmp_path / "page_0004.png"), [(50, 60, 80, 90), (100, 200, 150, 250)]
        )
    )

    changingBbox = computeChangingBbox(pages, sampleCount=2, marginPx=8)

    # 先頭と末尾の差分は追加された本文のみ。生の差分bboxは (100, 200, 151, 251)
    assert changingBbox == (92, 192, 159, 259)


def test_computeChangingBboxReturnsNoneForSinglePage(tmp_path):
    """画像が2枚未満なら None を返すこと"""
    page = makePageWithFixedUi(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])

    assert computeChangingBbox([page]) is None
    assert computeChangingBbox([]) is None


def test_computeChangingBboxReturnsNoneWhenAllPagesIdentical(tmp_path):
    """全ページが同一（差分なし）なら None を返すこと"""
    pages = [
        makePageWithFixedUi(str(tmp_path / f"page_{i:04d}.png"), [(50, 60, 80, 90)])
        for i in range(3)
    ]

    assert computeChangingBbox(pages) is None


def test_computeChangingBboxClampsMarginToImageBounds(tmp_path):
    """余白が画像境界を越えないようクランプされること"""
    # 一方のページだけ本文がある＝本文領域全体が「変化する領域」になる
    page1 = makePageWithFixedUi(str(tmp_path / "page_0001.png"), [(5, 30, 195, 295)])
    page2 = makePageWithFixedUi(str(tmp_path / "page_0002.png"), [])

    changingBbox = computeChangingBbox([page1, page2], marginPx=50)

    assert changingBbox == (0, 0, PAGE_SIZE[0], PAGE_SIZE[1])


def test_computeChangingBboxSkipsUnreadableFile(tmp_path):
    """読み込めないファイルが混ざっても、残りのページから差分を計算できること"""
    brokenPath = tmp_path / "broken.png"
    brokenPath.write_bytes(b"not an image")

    page1 = makePageWithFixedUi(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])
    page2 = makePageWithFixedUi(str(tmp_path / "page_0002.png"), [(30, 100, 60, 200)])

    changingBbox = computeChangingBbox([str(brokenPath), page1, page2], marginPx=8)

    assert changingBbox == (22, 52, 89, 209)


def test_computeChangingBboxRejectsInvalidSampleCount(tmp_path):
    """sampleCount が2未満なら ValueError を送出すること"""
    page1 = makePageWithFixedUi(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])
    page2 = makePageWithFixedUi(str(tmp_path / "page_0002.png"), [(30, 100, 60, 200)])

    with pytest.raises(ValueError):
        computeChangingBbox([page1, page2], sampleCount=1)


# --- computeUnionBbox ----------------------------------------------------


def test_computeUnionBboxTakesUnionOfPages(tmp_path):
    """2ページ分の本文領域の和集合が計算されること"""
    page1 = makePage(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])
    page2 = makePage(str(tmp_path / "page_0002.png"), [(30, 100, 60, 200)])

    bbox = computeUnionBbox([page1, page2], marginPx=8)

    # 描画は両端を含むため、生の外接矩形は (30, 60, 81, 201)。そこに余白8pxを付ける
    assert bbox == (22, 52, 89, 209)


def test_computeUnionBboxIgnoresBlankPages(tmp_path):
    """ほぼ白紙のページが和集合に影響しないこと"""
    blankPage = makePage(str(tmp_path / "page_0001.png"), [])
    contentPage = makePage(str(tmp_path / "page_0002.png"), [(50, 60, 80, 90)])

    bboxWithBlank = computeUnionBbox([blankPage, contentPage], marginPx=8)
    bboxWithoutBlank = computeUnionBbox([contentPage], marginPx=8)

    assert bboxWithBlank == bboxWithoutBlank
    assert bboxWithBlank == (42, 52, 89, 99)


def test_computeUnionBboxReturnsNoneWhenAllBlank(tmp_path):
    """全ページ白紙なら None を返すこと"""
    pages: list[str] = [
        makePage(str(tmp_path / "page_0001.png"), []),
        makePage(str(tmp_path / "page_0002.png"), []),
    ]

    assert computeUnionBbox(pages) is None


def test_computeUnionBboxClampsMarginToImageBounds(tmp_path):
    """余白が画像境界を越えないようクランプされること"""
    page = makePage(str(tmp_path / "page_0001.png"), [(5, 5, 195, 295)])

    bbox = computeUnionBbox([page], marginPx=50)

    assert bbox == (0, 0, PAGE_SIZE[0], PAGE_SIZE[1])


def test_computeUnionBboxSkipsUnreadableFile(tmp_path):
    """読み込めないファイルが混ざっても、残りのページから矩形を計算できること"""
    brokenPath = tmp_path / "broken.png"
    brokenPath.write_bytes(b"not an image")

    page = makePage(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])

    bbox = computeUnionBbox([str(brokenPath), page], marginPx=8)

    assert bbox == (42, 52, 89, 99)


def test_computeUnionBboxRejectsInvalidThreshold(tmp_path):
    """閾値が範囲外なら ValueError を送出すること"""
    page = makePage(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])

    with pytest.raises(ValueError):
        computeUnionBbox([page], whiteThreshold=300)


def test_cropImagesOverwritesInPlace(tmp_path):
    """全画像が指定矩形でクロップされ、同じパスに上書き保存されること"""
    pages = [
        makePage(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)]),
        makePage(str(tmp_path / "page_0002.png"), [(30, 100, 60, 200)]),
    ]

    bbox: tuple[int, int, int, int] = (20, 40, 120, 240)
    cropImages(pages, bbox)

    for page in pages:
        with Image.open(page) as img:
            assert img.size == (100, 200)


def test_cropImagesRejectsEmptyBbox(tmp_path):
    """幅・高さが0以下の矩形は ValueError になること"""
    page = makePage(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])

    with pytest.raises(ValueError):
        cropImages([page], (100, 100, 100, 200))


def test_cropImagesLeavesNoTempFileOnSuccess(tmp_path):
    """成功時に一時ファイルが残らないこと"""
    page = makePage(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])

    cropImages([page], (20, 40, 120, 240))

    assert not os.path.exists(f"{page}.cropping.tmp")
    assert [p.name for p in tmp_path.iterdir()] == ["page_0001.png"]


def test_cropImagesKeepsOriginalWhenReplaceFails(tmp_path, monkeypatch):
    """置き換えに失敗しても元画像が破壊されないこと（原子的置換の検証）"""
    page = makePage(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])
    originalBytes = (tmp_path / "page_0001.png").read_bytes()

    def failingReplace(src: str, dst: str) -> None:
        raise OSError("差し替えに失敗（テスト用の擬似障害）")

    monkeypatch.setattr(postprocess.os, "replace", failingReplace)

    # 1枚の失敗で例外を投げず、警告して継続する
    cropImages([page], (20, 40, 120, 240))

    assert (tmp_path / "page_0001.png").read_bytes() == originalBytes
    with Image.open(page) as img:
        assert img.size == PAGE_SIZE

    # 中途半端な一時ファイルを残さない
    assert not os.path.exists(f"{page}.cropping.tmp")


@pytest.mark.skipif(os.name != "nt", reason="読み取り専用ファイルの上書き拒否はWindows固有の挙動")
def test_cropImagesKeepsOriginalWhenDestinationIsReadOnly(tmp_path):
    """書き込み先が読み取り専用でも元画像が破壊されないこと"""
    page = makePage(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)])
    originalBytes = (tmp_path / "page_0001.png").read_bytes()

    os.chmod(page, stat.S_IREAD)
    try:
        cropImages([page], (20, 40, 120, 240))

        assert (tmp_path / "page_0001.png").read_bytes() == originalBytes
        assert not os.path.exists(f"{page}.cropping.tmp")
    finally:
        # tmp_path の後始末ができるよう書き込み権限を戻す
        os.chmod(page, stat.S_IWRITE | stat.S_IREAD)


def test_computeUnionBboxThenCropRoundTrip(tmp_path):
    """計算した矩形でクロップすると、全ページが同じサイズに揃うこと"""
    pages = [
        makePage(str(tmp_path / "page_0001.png"), [(50, 60, 80, 90)]),
        makePage(str(tmp_path / "page_0002.png"), [(30, 100, 60, 200)]),
    ]

    bbox: tuple[int, int, int, int] | None = computeUnionBbox(pages)
    assert bbox is not None

    cropImages(pages, bbox)

    expectedSize = (bbox[2] - bbox[0], bbox[3] - bbox[1])
    for page in pages:
        with Image.open(page) as img:
            assert img.size == expectedSize
