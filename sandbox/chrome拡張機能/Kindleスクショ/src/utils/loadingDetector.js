/**
 * Loading Detector
 * Kindleのローディング状態を検出
 */

/**
 * ローディングインジケーターが表示されているかチェック
 * @returns {boolean} ローディング中ならtrue
 */
function isLoading() {
    // 1. よくあるローディング関連のセレクター
    const loadingSelectors = [
        '[class*="spinner"]',
        '[class*="loading"]',
        '[class*="loader"]',
        '[id*="spinner"]',
        '[id*="loading"]',
        '[aria-busy="true"]',
        '[role="progressbar"]'
    ];

    // 通常のDOMをチェック
    for (const selector of loadingSelectors) {
        const elements = document.querySelectorAll(selector);
        for (const el of elements) {
            const style = window.getComputedStyle(el);
            if (style.display !== 'none' &&
                style.visibility !== 'hidden' &&
                parseFloat(style.opacity) > 0) {
                console.log('[LoadingDetector] ローディング要素検出:', selector, el);
                return true;
            }
        }
    }

    // Shadow DOM内をチェック
    const shadowHosts = window.ShadowDOMHelper?.findAllShadowHosts?.() || [];
    for (const host of shadowHosts) {
        if (!host.shadowRoot) continue;

        for (const selector of loadingSelectors) {
            const elements = host.shadowRoot.querySelectorAll(selector);
            for (const el of elements) {
                const style = window.getComputedStyle(el);
                if (style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    parseFloat(style.opacity) > 0) {
                    console.log('[LoadingDetector] Shadow DOM内でローディング要素検出:', selector, el);
                    return true;
                }
            }
        }
    }

    return false;
}

/**
 * ローディングが完了するまで待機
 * @param {number} timeout - 最大待機時間（ミリ秒）
 * @param {number} checkInterval - チェック間隔（ミリ秒）
 * @returns {Promise<boolean>} ローディングが完了したらtrue、タイムアウトならfalse
 */
async function waitForLoadingComplete(timeout = 3000, checkInterval = 100) {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
        if (!isLoading()) {
            console.log('[LoadingDetector] ローディング完了');
            return true;
        }
        await window.PageDetector.sleep(checkInterval);
    }

    console.warn('[LoadingDetector] ローディング完了待機がタイムアウト');
    return false;
}

// グローバルに公開
window.LoadingDetector = {
    isLoading,
    waitForLoadingComplete
};
