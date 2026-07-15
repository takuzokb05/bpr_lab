/**
 * Content Script - Main
 * Kindleページに注入されるメインスクリプト
 */

console.log('[KindleScreenshot] Content Script読み込み');

// 状態管理
const state = {
    isCapturing: false,
    isPaused: false,
    isLoopRunning: false,
    direction: 'ltr',
    sessionId: null,
    captureArea: null,
    currentPage: 0,
    totalPages: 0,
    retryCount: 0,
    maxRetries: 3
};
window.screenshotState = state;

/**
 * 初期化
 */
async function initialize() {
    try {
        console.log('[KindleScreenshot] 初期化開始');

        // グローバルにリセット関数を公開（デバッグ用）
        window.forceResetKindleScreenshot = async () => {
            if (confirm('全ての撮影データと設定を消去して再起動しますか？')) {
                await window.DB.deleteEverything();
            }
        };

        await waitForKindleReady();

        // 起動時に未完了のセッションがあればクリーンアップ（引継ぎを廃止し、常に新規とする）
        const incompleteSession = await window.DB.getIncompleteSession();
        if (incompleteSession) {
            console.log('[KindleScreenshot] 未完了セッションをクリーンアップします');
            await window.DB.deleteSession(incompleteSession.id);
        }

        removeControlButtons();
        showStartButton();

        window.addEventListener('kindle-screenshot-pause', handlePause);
        window.addEventListener('kindle-screenshot-cancel', handleCancel);

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && state.isCapturing) {
                e.preventDefault();
                handlePause();
            }
            // Shift + Alt + R でリセット
            if (e.shiftKey && e.altKey && e.key === 'R') {
                window.forceResetKindleScreenshot();
            }
        });
    } catch (e) {
        console.error('[KindleScreenshot] 初期化エラー:', e);
        // エラーが発生しても最低限ボタンは出す
        showStartButton();
    }
}

/**
 * Kindleの準備完了を待機
 */
async function waitForKindleReady() {
    let attempts = 0;
    while (attempts < 10) {
        if (window.PageDetector.getCurrentPageNumber()) return;
        await window.PageDetector.sleep(1000);
        attempts++;
    }
}

function showStartButton() {
    removeControlButtons();
    const btn = document.createElement('button');
    btn.id = 'kindle-screenshot-start-btn';
    btn.className = 'kindle-screenshot-main-btn';
    btn.textContent = '📸 新規PDF保存';
    btn.onclick = handleStart;
    document.body.appendChild(btn);
}


function removeControlButtons() {
    document.querySelectorAll('.kindle-screenshot-main-btn').forEach(b => b.remove());
}

async function handleStart() {
    try {
        removeControlButtons();
        let area = window.PageDetector.detectBookArea();
        let confirmed = false;

        if (area) {
            window.UIOverlay.hideForCapture();
            await window.PageDetector.sleep(50);
            const testImg = await captureCurrentPage(area);
            window.UIOverlay.showAfterCapture();

            const res = await window.UIOverlay.showConfirmArea(testImg, area.suggestedDirection);
            if (res.confirmed) {
                state.direction = res.direction;
                confirmed = true;
            }
        }

        if (!confirmed) {
            area = await window.UIOverlay.showRangeSelector();
            if (!area) { showStartButton(); return; }

            window.UIOverlay.hideForCapture();
            await window.PageDetector.sleep(50);
            const testImg = await captureCurrentPage(area);
            window.UIOverlay.showAfterCapture();

            const res = await window.UIOverlay.showConfirmArea(testImg, window.PageDetector.estimateDirection());
            if (res.confirmed) {
                state.direction = res.direction;
                confirmed = true;
            } else {
                showStartButton(); return;
            }
        }

        const pageInfo = window.PageDetector.getCurrentPageNumber();
        const sessionId = await window.DB.createSession(document.title || 'Kindle Book', area);

        await window.DB.updateSession(sessionId, {
            direction: state.direction,
            totalPages: pageInfo?.total || 999,
            currentPage: pageInfo?.current || 1
        });

        state.sessionId = sessionId;
        state.captureArea = area;
        state.currentPage = pageInfo?.current || 1;
        state.totalPages = pageInfo?.total || 999;
        state.isCapturing = true;

        await startCapture();
    } catch (e) {
        console.error(e);
        showStartButton();
    }
}


/**
 * コンテンツが安定するまで待機
 */
async function waitForContentStable() {
    // 過剰な待機処理を除去し、単純な時間待機に戻します
    // これにより「一生ページ更新しない」問題を解消します

    window.UIOverlay.hideForCapture();
    await window.PageDetector.sleep(500); // 固定待機のみにする
    window.UIOverlay.showAfterCapture();

    return true;
}

/**
 * 撮影ループ
 */
async function startCapture() {
    if (state.isLoopRunning) return;
    state.isLoopRunning = true;

    try {
        console.log('[KindleScreenshot] 撮影ループ開始');
        window.UIOverlay.showProgress(0, state.totalPages);

        let lastImageData = null;
        let capturedCount = 0;
        let stuckCount = 0;
        let samePageNumCount = 0; // 同じページ番号に留まっている回数
        let lastPageNum = -1;

        // すでに撮影済みのメタデータを取得（現在の状態を確認）
        const metadata = await window.DB.getScreenshotMetadata(state.sessionId);
        capturedCount = metadata.length;

        while (state.isCapturing && !state.isPaused) {
            // 1. 現在のページ情報を取得
            const currentPageInfo = window.PageDetector.getCurrentPageNumber();
            const currentNum = currentPageInfo?.current || 0;

            // ページ番号の変化を追跡
            if (currentNum === lastPageNum && currentNum !== 0) {
                samePageNumCount++;
            } else {
                samePageNumCount = 0;
                lastPageNum = currentNum;
            }

            // 2. 撮影して内容を確認
            // 撮影前にUIを隠す
            window.UIOverlay.hideForCapture();
            await window.PageDetector.sleep(50); // 反映待ち

            const currentImg = await captureCurrentPage();

            // 撮影後にUIを戻す
            window.UIOverlay.showAfterCapture();

            if (currentImg && currentImg !== lastImageData) {
                // 成功！内容が更新された
                capturedCount++;
                const pageNum = currentNum || 0;

                await window.DB.saveScreenshot(state.sessionId, pageNum, currentImg);
                lastImageData = currentImg;
                stuckCount = 0;

                window.UIOverlay.addThumbnail(currentImg);
                window.UIOverlay.showProgress(capturedCount, state.totalPages);

                console.log(`[KindleScreenshot] ページ保存: ${pageNum} (累計: ${capturedCount}枚)`);
                await window.DB.updateSession(state.sessionId, { currentPage: pageNum });
            } else {
                // 内容が変わっていない
                stuckCount++;
                console.log(`[KindleScreenshot] 内容に変化なし (stuckCount: ${stuckCount})`);
            }

            // 3. 次のページへ移動を試みる
            const beforePageNum = currentNum;
            await window.PageNavigator.goToNextPage('auto');

            // 4. ページ遷移を待機
            let pageNumChanged = false;
            for (let i = 0; i < 15; i++) {
                await window.PageDetector.sleep(100);
                const afterPageInfo = window.PageDetector.getCurrentPageNumber();
                if (afterPageInfo && afterPageInfo.current !== beforePageNum) {
                    pageNumChanged = true;
                    break;
                }
            }

            // 5. 遷移後の安定待ち（短縮）
            if (pageNumChanged) {
                await window.PageDetector.sleep(800);
            } else {
                await window.PageDetector.sleep(500);
            }

            // 6. 終了判定
            const isFinal = window.PageDetector.isLastPage();

            // 最終ページ番号であり、かつ遷移が発生していない場合
            if (isFinal && (!pageNumChanged || samePageNumCount >= 3)) {
                if (stuckCount >= 1 || samePageNumCount >= 3) {
                    console.log('[KindleScreenshot] 終端での無限ループ防止のため停止します');
                    await handleComplete();
                    return;
                }
            }

            // 通常の停滞判定
            if (stuckCount >= 3 && !pageNumChanged) {
                if (isFinal || stuckCount >= 5) {
                    console.log('[KindleScreenshot] 変化が停止したため終了します');
                    await handleComplete();
                    return;
                }
            }
        }
    } catch (e) {
        console.error('[KindleScreenshot] 撮影ループエラー:', e);
    } finally {
        state.isLoopRunning = false;
    }
}

async function captureCurrentPage(customArea) {
    const area = customArea || state.captureArea;
    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
            action: 'captureArea',
            area,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight,
                devicePixelRatio: window.devicePixelRatio
            }
        }, (res) => {
            if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
            else if (res && res.success) resolve(res.imageData);
            else reject(new Error('Capture failed'));
        });
    });
}

function handlePause() {
    state.isPaused = !state.isPaused;
    const btn = document.querySelector('.kindle-screenshot-btn-pause');
    if (btn) btn.textContent = state.isPaused ? '▶️ 再開' : '⏸ 一時停止';
    if (!state.isPaused) startCapture();
}

async function handleCancel() {
    if (state.sessionId) {
        await window.DB.deleteSession(state.sessionId);
    }
    state.isCapturing = false;
    state.sessionId = null;
    window.UIOverlay.hideAll();
    showStartButton();
}

async function handleComplete() {
    state.isCapturing = false;
    window.UIOverlay.hideProgress();
    await window.DB.completeSession(state.sessionId);
    const prog = await window.DB.getProgress(state.sessionId);
    window.UIOverlay.hideAll();
    await window.UIOverlay.showCompletion(prog.captured, generatePDF);
}

async function generatePDF() {
    try {
        console.log('[KindleScreenshot] PDF生成開始');
        // 撮影順（DBのID）を絶対基準としてソートするためのメタデータを取得
        // 全画像を一度に読み込むとメモリ不足でクラッシュするため
        const metadata = await window.DB.getScreenshotMetadata(state.sessionId);
        if (metadata.length === 0) {
            alert('撮影データがありません');
            return;
        }

        metadata.sort((a, b) => (a.id || 0) - (b.id || 0));

        const { jsPDF } = window.jspdf;

        // 最初の1枚だけ取得してPDFのサイズを決定
        const firstShot = await window.DB.db.screenshots.get(metadata[0].id);
        const firstImg = await loadImage(firstShot.imageData);

        const pdf = new jsPDF({
            orientation: firstImg.width > firstImg.height ? 'l' : 'p',
            unit: 'px',
            format: [firstImg.width, firstImg.height],
            compress: true
        });

        for (let i = 0; i < metadata.length; i++) {
            // 1枚ずつDBから読み込む（メモリ節約）
            const shot = await window.DB.db.screenshots.get(metadata[i].id);
            const img = await loadImage(shot.imageData);

            // --- 軽量化設定 ---
            const maxWidth = 1600; // 必要十分な解像度
            let tw = img.width;
            let th = img.height;

            if (img.width > maxWidth) {
                tw = maxWidth;
                th = (img.height * maxWidth) / img.width;
            }

            // Canvasを使用して再圧縮
            const canvas = new OffscreenCanvas(tw, th);
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, tw, th);

            const blob = await canvas.convertToBlob({ type: 'image/jpeg', quality: 0.75 });
            const data = await new Promise(r => {
                const reader = new FileReader();
                reader.onloadend = () => r(reader.result);
                reader.readAsDataURL(blob);
            });

            if (i > 0) {
                pdf.addPage([tw, th]);
            } else {
                // 1ページ目の場合は既存のページをリサイズ（jsPDFの制約上、内部プロパティ操作が必要だが
                // シンプルに1ページ目もaddImageの引数で合わせる）
            }

            pdf.addImage(data, 'JPEG', 0, 0, tw, th, undefined, 'FAST');

            if (i % 10 === 0) {
                console.log(`[KindleScreenshot] PDF生成中: ${i + 1}/${metadata.length}`);
            }
        }

        // 重要: pdf.save() は内部で巨大な文字列を生成しようとしてエラーになるため、
        // Blobとして出力し、URL.createObjectURL を使ってダウンロードする。
        const blob = pdf.output('blob');
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');

        const session = await window.DB.db.sessions.get(state.sessionId);
        const title = (session?.bookTitle || 'Kindle').replace(/[^\w\s-]/g, '').substring(0, 50);

        link.href = url;
        link.download = `${title}-${Date.now()}.pdf`;
        link.click();

        // メモリ解放
        setTimeout(() => URL.revokeObjectURL(url), 10000);

        console.log('[KindleScreenshot] PDF生成完了');
        await window.DB.deleteSession(state.sessionId);
        showStartButton();
    } catch (e) {
        console.error('[KindleScreenshot] PDF生成エラー:', e);
        alert('PDF生成中にエラーが発生しました。\n' + e.message + '\n\nブラウザのメモリが不足している可能性があります。');
    }
}

function loadImage(url) {
    return new Promise((res, rej) => {
        const img = new Image();
        img.onload = () => res(img);
        img.onerror = rej;
        img.src = url;
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}
