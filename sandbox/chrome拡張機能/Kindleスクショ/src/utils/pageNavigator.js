/**
 * Page Navigator
 * ページめくりと複数ページジャンプの対策
 */

/**
 * 座標指定で要素をクリック
 * @param {Element} element 
 */
function clickElement(element) {
    if (!element) return;
    const rect = element.getBoundingClientRect();
    const centerX = rect.x + rect.width / 2;
    const centerY = rect.y + rect.height / 2;

    const clickOptions = {
        view: window,
        bubbles: true,
        cancelable: true,
        clientX: centerX,
        clientY: centerY
    };

    // mousedown -> mouseup -> click の順で発火（Kindleの内部状態を確実に動かすため）
    element.dispatchEvent(new MouseEvent('mousedown', clickOptions));
    element.dispatchEvent(new MouseEvent('mouseup', clickOptions));
    element.dispatchEvent(new MouseEvent('click', clickOptions));
}

/**
 * キーボードイベントを送信
 * @param {string} key 
 */
function sendKeyboardEvent(key) {
    const keyCode = key === 'ArrowRight' ? 39 : 37;
    const eventParams = {
        key: key,
        code: key,
        keyCode: keyCode,
        which: keyCode,
        bubbles: true,
        cancelable: true,
        view: window
    };

    // keydown と keyup をセットで送る
    document.dispatchEvent(new KeyboardEvent('keydown', eventParams));
    setTimeout(() => {
        document.dispatchEvent(new KeyboardEvent('keyup', eventParams));
    }, 50);
}

/**
 * 次ページへ移動（低レベル操作）
 * @param {string} method - 'click' | 'keyboard' | 'auto'
 */
async function goToNextPage(method = 'auto') {
    const direction = window.screenshotState?.direction || 'ltr';
    const isRTL = direction === 'rtl';

    if (method === 'click' || method === 'auto') {
        const targetArea = isRTL ? findLeftClickArea() : findRightClickArea();
        if (targetArea) {
            console.log('[PageNavigator] ターゲット領域をクリックします');
            clickElement(targetArea);
            if (method === 'click') return true;
        }
    }

    if (method === 'keyboard' || method === 'auto') {
        const key = isRTL ? 'ArrowLeft' : 'ArrowRight';
        console.log(`[PageNavigator] キーボードイベント送信: ${key}`);
        sendKeyboardEvent(key);
        return true;
    }

    return false;
}

/**
 * 前ページへ移動
 */
async function goToPreviousPage() {
    const direction = window.screenshotState?.direction || 'ltr';
    const isRTL = direction === 'rtl';

    const targetArea = isRTL ? findRightClickArea() : findLeftClickArea();
    if (targetArea) {
        clickElement(targetArea);
    } else {
        const key = isRTL ? 'ArrowRight' : 'ArrowLeft';
        sendKeyboardEvent(key);
    }
    return true;
}

/**
 * 右側のクリック領域を探す (画面の右30%)
 */
function findRightClickArea() {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    const rightAreas = window.ShadowDOMHelper.findByCriteria(el => {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        // 右側30%のエリアで、高さが画面の半分以上
        return rect.x > viewportWidth * 0.7 &&
            rect.height > viewportHeight * 0.5 &&
            rect.width > 30 &&
            style.pointerEvents !== 'none' &&
            style.display !== 'none';
    });

    if (rightAreas.length > 0) {
        // 重なり順（depth）が深いもの＝より表面に近いものを優先
        rightAreas.sort((a, b) => (b.depth - a.depth) || (b.element.getBoundingClientRect().x - a.element.getBoundingClientRect().x));
        return rightAreas[0].element;
    }
    return null;
}

/**
 * 左側のクリック領域を探す (画面の左30%)
 */
function findLeftClickArea() {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    const leftAreas = window.ShadowDOMHelper.findByCriteria(el => {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        // 左側30%のエリアで、高さが画面の半分以上
        return rect.x < viewportWidth * 0.3 &&
            (rect.x + rect.width) < viewportWidth * 0.4 &&
            rect.height > viewportHeight * 0.5 &&
            rect.width > 30 &&
            style.pointerEvents !== 'none' &&
            style.display !== 'none';
    });

    if (leftAreas.length > 0) {
        leftAreas.sort((a, b) => (b.depth - a.depth) || (a.element.getBoundingClientRect().x - b.element.getBoundingClientRect().x));
        return leftAreas[0].element;
    }
    return null;
}

/**
 * 安全に次ページへ移動
 * 1. まずクリックを試す
 * 2. 変わらなければキーボードを試す
 * @param {number} waitTime - 合計待機時間（ミリ秒）
 */
async function safeGoToNextPage(waitTime = 2500) {
    const beforePageNum = window.PageDetector.getCurrentPageNumber()?.current;
    console.log('[PageNavigator] safeGoToNextPage 開始: 現在=', beforePageNum);

    // 1段目: クリックを試行
    await goToNextPage('click');

    // 変化を確認（半分程度の時間をかける）
    const firstWait = 1200;
    const startTime = Date.now();

    while (Date.now() - startTime < firstWait) {
        const afterPageNum = window.PageDetector.getCurrentPageNumber()?.current;
        if (afterPageNum !== undefined && afterPageNum !== null && afterPageNum !== beforePageNum) {
            console.log('[PageNavigator] クリックでページ変更成功:', beforePageNum, '→', afterPageNum);
            return { success: true, newPage: afterPageNum };
        }
        await window.PageDetector.sleep(200);
    }

    // 2段目: キーボード入力を試行
    console.log('[PageNavigator] クリックで変化がないためキーボードを試行します (Fallback)');
    await goToNextPage('keyboard');

    while (Date.now() - startTime < waitTime) {
        const afterPageNum = window.PageDetector.getCurrentPageNumber()?.current;
        if (afterPageNum !== undefined && afterPageNum !== null && afterPageNum !== beforePageNum) {
            console.log('[PageNavigator] キーボードでページ変更成功:', beforePageNum, '→', afterPageNum);
            return { success: true, newPage: afterPageNum };
        }
        await window.PageDetector.sleep(200);
    }

    const finalPageNum = window.PageDetector.getCurrentPageNumber()?.current || beforePageNum;
    console.warn('[PageNavigator] ページ変更なし (タイムアウト)');
    return { success: false, newPage: finalPageNum };
}

// グローバルに公開
window.PageNavigator = {
    goToNextPage,
    goToPreviousPage,
    findRightClickArea,
    findLeftClickArea,
    safeGoToNextPage
};
