/**
 * Background Service Worker
 * スクリーンショット撮影とメッセージ処理
 */

console.log('[Background] Service Worker起動');

// メッセージリスナー
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('[Background] メッセージ受信:', request.action);

    if (request.action === 'captureArea') {
        handleCaptureArea(request, sender, sendResponse);
        return true; // 非同期レスポンス
    }

    if (request.action === 'ping') {
        sendResponse({ status: 'ok' });
        return false;
    }
});

/**
 * 指定領域をキャプチャ
 * @param {Object} request - {action, area: {x, y, width, height}}
 * @param {Object} sender
 * @param {Function} sendResponse
 */
async function handleCaptureArea(request, sender, sendResponse) {
    try {
        const tabId = sender.tab.id;
        const area = request.area;

        console.log('[Background] キャプチャ開始:', area);

        // タブ全体をキャプチャ
        chrome.tabs.captureVisibleTab(null, { format: 'png' }, async (dataUrl) => {
            if (chrome.runtime.lastError) {
                console.error('[Background] キャプチャエラー:', chrome.runtime.lastError);
                sendResponse({
                    success: false,
                    error: chrome.runtime.lastError.message
                });
                return;
            }

            try {
                // 指定領域を切り抜き
                const croppedImage = await cropImage(dataUrl, area, request.viewport);

                console.log('[Background] キャプチャ成功');
                sendResponse({
                    success: true,
                    imageData: croppedImage
                });
            } catch (error) {
                console.error('[Background] 切り抜きエラー:', error);
                sendResponse({
                    success: false,
                    error: error.message
                });
            }
        });
    } catch (error) {
        console.error('[Background] 処理エラー:', error);
        sendResponse({
            success: false,
            error: error.message
        });
    }
}

/**
 * 画像を切り抜き
 * @param {string} dataUrl - 元画像のData URL
 * @param {Object} area - {x, y, width, height}
 * @param {Object} viewport - {width, height, devicePixelRatio}
 * @returns {Promise<string>} 切り抜いた画像のData URL
 */
async function cropImage(dataUrl, area, viewport) {
    try {
        console.log('[Background] cropImage 開始:', { area, viewport });

        // Data URLをBlobに変換
        const response = await fetch(dataUrl);
        const blob = await response.blob();

        // ImageBitmapを作成
        const imageBitmap = await createImageBitmap(blob);

        // 実際のDPRを計算（キャプチャ画像サイズ / ContentScriptの窓幅）
        const viewportWidth = viewport?.width || 1280;
        const dpr = imageBitmap.width / viewportWidth;

        console.log('[Background] DPR算出結果:', {
            bitmapWidth: imageBitmap.width,
            viewportWidth: viewportWidth,
            dpr: dpr
        });
        console.log('[Background] 切り抜き計算:', {
            sourceX: area.x * dpr,
            sourceY: area.y * dpr,
            sourceWidth: area.width * dpr,
            sourceHeight: area.height * dpr,
            destWidth: area.width,
            destHeight: area.height
        });

        // OffscreenCanvasで切り抜き（出力サイズは元の選択サイズ）
        const canvas = new OffscreenCanvas(area.width, area.height);
        const ctx = canvas.getContext('2d');

        // 高品質設定
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        // 指定領域を切り抜き（ソース座標はDPR倍、出力は元サイズ）
        ctx.drawImage(
            imageBitmap,
            area.x * dpr,      // ソースX（DPR倍）
            area.y * dpr,      // ソースY（DPR倍）
            area.width * dpr,  // ソース幅（DPR倍）
            area.height * dpr, // ソース高さ（DPR倍）
            0,                 // 描画先X
            0,                 // 描画先Y
            area.width,        // 描画先幅（元サイズ）
            area.height        // 描画先高さ（元サイズ）
        );

        console.log('[Background] Canvas描画完了');

        // Blobに変換
        const croppedBlob = await canvas.convertToBlob({ type: 'image/png' });

        // Data URLに変換
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                console.log('[Background] cropImage 完了');
                resolve(reader.result);
            };
            reader.onerror = () => reject(new Error('Blob読み込みエラー'));
            reader.readAsDataURL(croppedBlob);
        });

    } catch (error) {
        console.error('[Background] cropImage エラー:', error);
        throw error;
    }
}

/**
 * 拡張機能インストール時の処理
 */
chrome.runtime.onInstalled.addListener((details) => {
    console.log('[Background] 拡張機能インストール:', details.reason);

    if (details.reason === 'install') {
        console.log('[Background] 初回インストール');
    } else if (details.reason === 'update') {
        console.log('[Background] アップデート:', details.previousVersion, '→', chrome.runtime.getManifest().version);
    }
});
