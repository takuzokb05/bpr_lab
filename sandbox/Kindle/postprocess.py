"""
Post Processor for Kindle Auto-Capture Tool
撮影画像群から本文領域を検出し、全ページ共通の矩形で自動クロップする
"""

import os

from PIL import Image, ImageChops

# 隣接ページの差分で「変化あり」とみなす輝度差の閾値
# （JPEG/アンチエイリアス由来の微小なノイズを本文とみなさないための下限）
DIFF_THRESHOLD = 16


def _applyMarginAndClamp(
    bbox: tuple[int, int, int, int],
    marginPx: int,
    minWidth: int,
    minHeight: int
) -> tuple[int, int, int, int] | None:
    """
    外接矩形に余白を付け、画像境界にクランプする

    Args:
        bbox: (left, top, right, bottom) 形式の矩形
        marginPx: 外側に付ける余白 (px)
        minWidth: クランプ先の幅（全ページの最小幅）
        minHeight: クランプ先の高さ（全ページの最小高さ）

    Returns:
        Optional[Tuple[int, int, int, int]]: 余白付きの矩形。幅・高さが0以下なら None
    """
    left = max(0, bbox[0] - marginPx)
    top = max(0, bbox[1] - marginPx)
    right = min(minWidth, bbox[2] + marginPx)
    bottom = min(minHeight, bbox[3] + marginPx)

    if right <= left or bottom <= top:
        print("⚠️ 計算されたクロップ範囲が不正です（幅または高さが0以下）")
        return None

    return (left, top, right, bottom)


def computeUnionBbox(
    imagePaths: list[str],
    whiteThreshold: int = 245,
    marginPx: int = 8
) -> tuple[int, int, int, int] | None:
    """
    全ページの「本文が存在する領域」の外接矩形の和集合を計算する

    各画像をグレースケール化し、whiteThreshold 以上の画素を背景(白)とみなして
    本文画素のみの bbox を取得する。ほぼ白紙のページ（bbox が None）はスキップする。

    Args:
        imagePaths: 対象画像のパス一覧
        whiteThreshold: これ以上の輝度を背景(白)とみなす閾値 (0-255)
        marginPx: 和集合の外側に付ける余白 (px)

    Returns:
        Optional[Tuple[int, int, int, int]]:
            (left, top, right, bottom) 形式の矩形（right/bottom は排他的）。
            全ページが白紙、または有効な画像が1枚もない場合は None

    Raises:
        ValueError: whiteThreshold が 0-255 の範囲外、または marginPx が負の場合
    """
    if not 0 <= whiteThreshold <= 255:
        raise ValueError(f"whiteThreshold は 0-255 で指定してください: {whiteThreshold}")

    if marginPx < 0:
        raise ValueError(f"marginPx は 0 以上で指定してください: {marginPx}")

    unionBbox: tuple[int, int, int, int] | None = None

    # クロップ矩形は全ページで共有するため、最小サイズのページに合わせてクランプする
    minWidth: int | None = None
    minHeight: int | None = None

    blankPageCount = 0

    for imagePath in imagePaths:
        try:
            with Image.open(imagePath) as img:
                grayImage = img.convert("L")
                width, height = grayImage.size

                minWidth = width if minWidth is None else min(minWidth, width)
                minHeight = height if minHeight is None else min(minHeight, height)

                # 本文画素を 255、背景(白)を 0 にした2値マスクの外接矩形を取る
                contentMask = grayImage.point(
                    lambda pixel: 255 if pixel < whiteThreshold else 0
                )
                pageBbox = contentMask.getbbox()

        except (OSError, ValueError) as e:
            # 破損画像などは致命的ではないため、理由を出したうえでスキップする
            print(f"⚠️ 画像を読み込めませんでした（スキップ）: {imagePath} ({e})")
            continue

        if pageBbox is None:
            # ほぼ白紙のページは和集合に含めない
            blankPageCount += 1
            continue

        if unionBbox is None:
            unionBbox = pageBbox
        else:
            unionBbox = (
                min(unionBbox[0], pageBbox[0]),
                min(unionBbox[1], pageBbox[1]),
                max(unionBbox[2], pageBbox[2]),
                max(unionBbox[3], pageBbox[3]),
            )

    if unionBbox is None or minWidth is None or minHeight is None:
        print("⚠️ 本文領域を検出できませんでした（全ページが白紙、または読み込み可能な画像なし）")
        return None

    if blankPageCount > 0:
        print(f"ℹ️ 白紙とみなしたページ: {blankPageCount}件（クロップ範囲の計算から除外）")

    # 余白を付けたうえで画像境界にクランプする
    return _applyMarginAndClamp(unionBbox, marginPx, minWidth, minHeight)


def computeChangingBbox(
    imagePaths: list[str],
    sampleCount: int = 10,
    marginPx: int = 8
) -> tuple[int, int, int, int] | None:
    """
    ページ間で「変化する領域」の外接矩形を計算する（本文領域の検出）

    computeUnionBbox は非白画素をすべて本文とみなすため、Kindleのヘッダーや
    進捗バーのような常時表示UIが必ず矩形に含まれ、クロップがほぼ効かなくなる。
    本関数は等間隔にサンプリングしたページの隣接ペア差分を取り、
    「ページごとに変化する領域＝本文」だけを抽出する（固定UIは差分0で除外される）。

    Args:
        imagePaths: 対象画像のパス一覧
        sampleCount: サンプリングする最大ページ数
        marginPx: 外接矩形の外側に付ける余白 (px)

    Returns:
        Optional[Tuple[int, int, int, int]]:
            (left, top, right, bottom) 形式の矩形（right/bottom は排他的）。
            画像が2枚未満、読み込める画像が2枚未満、または全ペアで差分がない場合は None

    Raises:
        ValueError: sampleCount が2未満、または marginPx が負の場合
    """
    if sampleCount < 2:
        raise ValueError(f"sampleCount は 2 以上で指定してください: {sampleCount}")

    if marginPx < 0:
        raise ValueError(f"marginPx は 0 以上で指定してください: {marginPx}")

    if len(imagePaths) < 2:
        print("⚠️ 差分による本文検出には2ページ以上必要です")
        return None

    # 等間隔に最大 sampleCount ページを選ぶ（先頭と末尾は必ず含む）
    sampleTotal = min(sampleCount, len(imagePaths))
    lastIndex = len(imagePaths) - 1
    sampleIndices = sorted({
        round(i * lastIndex / (sampleTotal - 1)) for i in range(sampleTotal)
    })

    # 差分計算のため、サンプルはグレースケール化してメモリに載せる
    sampleImages: list[Image.Image] = []
    minWidth: int | None = None
    minHeight: int | None = None

    for index in sampleIndices:
        imagePath = imagePaths[index]
        try:
            with Image.open(imagePath) as img:
                grayImage = img.convert("L")
        except (OSError, ValueError) as e:
            print(f"⚠️ 画像を読み込めませんでした（スキップ）: {imagePath} ({e})")
            continue

        width, height = grayImage.size
        minWidth = width if minWidth is None else min(minWidth, width)
        minHeight = height if minHeight is None else min(minHeight, height)
        sampleImages.append(grayImage)

    if len(sampleImages) < 2 or minWidth is None or minHeight is None:
        print("⚠️ 差分を取れるサンプル画像が2枚未満です")
        return None

    changingBbox: tuple[int, int, int, int] | None = None

    # 隣接ペアを走査する（末尾がずれる前提のため strict=False）
    for previousImage, currentImage in zip(sampleImages, sampleImages[1:], strict=False):
        # サイズ差があると difference が失敗するため、共通領域に揃えてから比較する
        commonBox = (0, 0, minWidth, minHeight)
        diffImage = ImageChops.difference(
            previousImage.crop(commonBox), currentImage.crop(commonBox)
        )

        # 微小なノイズを無視し、明確に変化した画素のみを残す
        changedMask = diffImage.point(lambda pixel: 255 if pixel > DIFF_THRESHOLD else 0)
        pairBbox = changedMask.getbbox()

        if pairBbox is None:
            # このペアは完全に同一（固定UIのみのページ等）
            continue

        if changingBbox is None:
            changingBbox = pairBbox
        else:
            changingBbox = (
                min(changingBbox[0], pairBbox[0]),
                min(changingBbox[1], pairBbox[1]),
                max(changingBbox[2], pairBbox[2]),
                max(changingBbox[3], pairBbox[3]),
            )

    if changingBbox is None:
        print("⚠️ ページ間で変化する領域を検出できませんでした（全サンプルが同一）")
        return None

    print(f"🔎 本文領域を検出しました（サンプル {len(sampleImages)}ページの差分）")

    return _applyMarginAndClamp(changingBbox, marginPx, minWidth, minHeight)


def cropImages(imagePaths: list[str], bbox: tuple[int, int, int, int]) -> None:
    """
    全画像を指定の矩形でクロップし、同じパスへ上書き保存する

    書き込みは「一時ファイルへ保存 → os.replace で原子的に差し替え」で行う。
    元パスへ直接 save すると、途中で失敗したときに元画像を破壊してしまうため。

    Args:
        imagePaths: 対象画像のパス一覧
        bbox: (left, top, right, bottom) 形式の矩形（right/bottom は排他的）

    Raises:
        ValueError: bbox の幅または高さが0以下の場合
    """
    left, top, right, bottom = bbox

    if right <= left or bottom <= top:
        raise ValueError(f"クロップ範囲が不正です: {bbox}")

    croppedCount = 0
    failedCount = 0

    print(f"✂️ 自動クロップ中... ({len(imagePaths)}ページ / 範囲 {right - left}x{bottom - top} px)")

    for imagePath in imagePaths:
        # 一時ファイルは同一ディレクトリに置く（os.replace は同一ボリューム内でのみ原子的）
        tempPath = f"{imagePath}.cropping.tmp"

        try:
            with Image.open(imagePath) as img:
                # 拡張子のない一時ファイルへ保存するため、元の形式を控えておく
                sourceFormat = img.format
                croppedImage = img.crop(bbox)
                # with を抜ける前に画素を読み込んでおく（元ファイルを閉じた後に保存するため）
                croppedImage.load()

            croppedImage.save(tempPath, format=sourceFormat or "PNG")
            os.replace(tempPath, imagePath)
            croppedCount += 1

        except (OSError, ValueError) as e:
            # 1枚の失敗で全体を止めず、件数を集計して最後に報告する
            print(f"⚠️ クロップに失敗しました（元画像を維持）: {os.path.basename(imagePath)} ({e})")
            failedCount += 1

            # 中途半端な一時ファイルを残さない
            if os.path.exists(tempPath):
                try:
                    os.remove(tempPath)
                except OSError as cleanupError:
                    print(f"⚠️ 一時ファイルを削除できませんでした: {tempPath} ({cleanupError})")

    print(f"✅ クロップ完了: {croppedCount}ページ" + (f" / 失敗 {failedCount}ページ" if failedCount else ""))
