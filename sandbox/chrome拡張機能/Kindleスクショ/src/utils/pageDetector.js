/**
 * Page Detector
 * ページ番号の検出と最終ページ判定
 */

/**
 * 現在のページ番号を取得
 * @returns {{current: number, total: number, text: string}|null}
 */
function getCurrentPageNumber() {
    const patterns = [
        /(\d+)\s*\/\s*(\d+)/,
        /page\s*(\d+)\s*of\s*(\d+)/i,
        /location\s*(\d+)/i,
        /(\d+)%/
    ];

    // 最適化: テキストを保持している可能性が高い「末端に近い要素」だけを抽出
    const textElements = window.ShadowDOMHelper.findByCriteria(el => {
        // 子要素が多い要素（親コンテナなど）で textContent を呼ぶと
        // 配下の全テキストを連結するため非常に重い。これを避ける。
        if (el.children && el.children.length > 3) return false;

        const text = el.textContent?.trim();
        return text && text.length > 0 && text.length < 50;
    });

    // 最も下にある要素を優先（通常、ページ番号はフッターにあるため）
    const sortedElements = textElements.sort((a, b) => {
        const rectA = a.element.getBoundingClientRect();
        const rectB = b.element.getBoundingClientRect();
        return rectB.y - rectA.y;
    });

    for (const { element } of sortedElements) {
        const text = element.textContent.trim();
        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match) {
                const isLocation = pattern.source.includes('location');
                const isPercent = pattern.source.includes('%');
                return {
                    current: parseInt(match[1]),
                    total: match[2] ? parseInt(match[2]) : (isPercent ? 100 : null),
                    text: match[0],
                    isLocation,
                    isPercent
                };
            }
        }
    }
    return null;
}

/**
 * ページ番号が変化したか確認
 * @param {number} previousPage - 前回のページ番号
 * @param {number} timeout - タイムアウト（ミリ秒）
 * @returns {Promise<{changed: boolean, newPage: number|null, jumpedPages: number}>}
 */
async function waitForPageChange(previousPage, timeout = 3000) {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
        const pageInfo = getCurrentPageNumber();

        if (pageInfo && pageInfo.current !== previousPage) {
            const jumpedPages = pageInfo.current - previousPage;

            return {
                changed: true,
                newPage: pageInfo.current,
                jumpedPages: jumpedPages,
                pageInfo: pageInfo
            };
        }

        await sleep(100);
    }

    return {
        changed: false,
        newPage: null,
        jumpedPages: 0
    };
}

/**
 * 最終ページかどうか判定
 * @returns {boolean}
 */
function isLastPage() {
    const pageInfo = getCurrentPageNumber();
    if (!pageInfo) return false;

    // 現在のページが総ページ数以上なら最後
    if (pageInfo.total && pageInfo.current >= pageInfo.total) {
        return true;
    }

    return isNextButtonDisabled();
}

/**
 * 次ページボタンが無効化されているか確認
 * @returns {boolean}
 */
function isNextButtonDisabled() {
    // 進行方向を確認
    const isRTL = window.screenshotState?.direction === 'rtl';
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // 次ページに進むためのクリックエリアを探す（LTRなら右、RTLなら左）
    const nextPageAreas = window.ShadowDOMHelper.findByCriteria(el => {
        const rect = el.getBoundingClientRect();
        if (isRTL) {
            return rect.x < viewportWidth * 0.5 &&
                (rect.x + rect.width) < viewportWidth * 0.5 &&
                rect.height > viewportHeight * 0.5 &&
                rect.width > 50 &&
                rect.width < viewportWidth * 0.8;
        } else {
            return rect.x > viewportWidth * 0.5 &&
                rect.height > viewportHeight * 0.5 &&
                rect.width > 50 &&
                rect.width < viewportWidth * 0.8;
        }
    });

    if (nextPageAreas.length === 0) {
        const pageInfo = getCurrentPageNumber();
        if (pageInfo && pageInfo.total && (pageInfo.current > pageInfo.total * 0.9)) {
            return true;
        }
        return false;
    }

    nextPageAreas.sort((a, b) => {
        const rectA = a.element.getBoundingClientRect();
        const rectB = b.element.getBoundingClientRect();
        return isRTL ? (rectA.x - rectB.x) : (rectB.x - rectA.x);
    });

    const area = nextPageAreas[0].element;
    const style = window.getComputedStyle(area);

    return area.disabled ||
        area.getAttribute('aria-disabled') === 'true' ||
        style.pointerEvents === 'none' ||
        style.display === 'none' ||
        style.visibility === 'hidden' ||
        parseFloat(style.opacity) < 0.1;
}

/**
 * ページ番号の連続性をチェック
 * @param {number} expectedPage - 期待されるページ番号
 * @param {number} actualPage - 実際のページ番号
 * @returns {{isSequential: boolean, skippedPages: number}}
 */
function checkPageSequence(expectedPage, actualPage) {
    const diff = actualPage - expectedPage;

    return {
        isSequential: diff === 1,
        skippedPages: diff > 1 ? diff - 1 : 0,
        jumpedBack: diff < 0
    };
}

/**
 * スリープ関数
 * @param {number} ms - ミリ秒
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 本が表示されている領域を自動検知
 * @returns {{x: number, y: number, width: number, height: number, method: string}|null}
 */
function detectBookArea() {
    console.log('[PageDetector] 撮影範囲の自動検知を開始します...');
    const candidates = [];
    const viewportArea = window.innerWidth * window.innerHeight;

    // 探索開始
    for (const { element } of window.ShadowDOMHelper.traverseDOM(document.body)) {
        // 画像、Canvas、または背景画像を持つDIVを対象にする
        const isImage = element.tagName === 'IMG';
        const isCanvas = element.tagName === 'CANVAS';
        const isDiv = element.tagName === 'DIV';

        if (!isImage && !isCanvas && !isDiv) continue;

        const rect = element.getBoundingClientRect();

        // 画面外の要素は除外
        if (rect.width === 0 || rect.height === 0 || rect.bottom < 0 || rect.top > window.innerHeight) continue;

        const area = rect.width * rect.height;
        // 緩和: 画面の10%以上、かつ200x200以上のサイズ
        const isLargeEnough = rect.width > 200 && rect.height > 200 && area > (viewportArea * 0.1);

        if (isLargeEnough) {
            // DIVの場合は背景画像があるか、特定のクラスを持つか確認
            if (isDiv) {
                const style = window.getComputedStyle(element);
                const hasBgImg = style.backgroundImage && style.backgroundImage !== 'none';
                const isPageContainer = element.className && // クラス名チェック（文字列の場合のみ）
                    typeof element.className === 'string' &&
                    (element.className.includes('page') || element.className.includes('canvas'));

                if (!hasBgImg && !isPageContainer) continue;
            }

            candidates.push({
                element,
                rect: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                area,
                type: element.tagName
            });
        }
    }

    if (candidates.length > 0) {
        // 面積が大きい順にソート
        candidates.sort((a, b) => b.area - a.area);

        // 最大の要素を採用（ただし、画面全体すぎるものは除外したいが、Kindleは全画面に近いので許容）
        const best = candidates[0];
        console.log(`[PageDetector] 候補検出: ${candidates.length}件, 採用:`, best);

        let suggestedDirection = estimateDirection();

        return {
            ...best.rect,
            method: 'auto',
            suggestedDirection
        };
    }

    console.warn('[PageDetector] 自動検出できませんでした。候補が見つかりません。');
    return null;
}

/**
 * 本の綴じ方向を推測
 * @returns {string} 'ltr' or 'rtl'
 */
function estimateDirection() {
    const isRTL = window.ShadowDOMHelper.findByCriteria(el => {
        const rect = el.getBoundingClientRect();
        return rect.x < 50 && rect.height > window.innerHeight * 0.5;
    }).length > 0;

    return isRTL ? 'rtl' : 'ltr';
}

// グローバルに公開
window.PageDetector = {
    getCurrentPageNumber,
    waitForPageChange,
    isLastPage,
    isNextButtonDisabled,
    checkPageSequence,
    detectBookArea,
    estimateDirection,
    sleep
};
