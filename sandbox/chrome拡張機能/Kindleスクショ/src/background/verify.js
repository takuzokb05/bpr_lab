/**
 * Background Script 検証コード
 * 
 * chrome://extensions/ で「Kindle Screenshot to PDF」の
 * 「service worker」リンクをクリックして、このコンソールを確認してください
 */

console.log('='.repeat(60));
console.log('Background Script 検証開始');
console.log('='.repeat(60));

// 1. 基本的な機能チェック
console.log('\n1. 基本機能チェック:');
console.log('  - chrome.runtime:', typeof chrome.runtime);
console.log('  - chrome.tabs:', typeof chrome.tabs);
console.log('  - Image:', typeof Image);
console.log('  - OffscreenCanvas:', typeof OffscreenCanvas);
console.log('  - FileReader:', typeof FileReader);

// 2. メッセージリスナーの確認
console.log('\n2. メッセージリスナー登録確認:');
console.log('  - リスナー数:', chrome.runtime.onMessage.hasListeners() ? '登録済み' : '未登録');

// 3. テストメッセージ送信機能
window.testBackgroundScript = function () {
    console.log('\n3. テストメッセージ送信:');

    chrome.runtime.sendMessage({ action: 'ping' }, (response) => {
        if (chrome.runtime.lastError) {
            console.error('  ❌ エラー:', chrome.runtime.lastError.message);
        } else {
            console.log('  ✅ 応答:', response);
        }
    });
};

// 4. キャプチャテスト
window.testCapture = async function () {
    console.log('\n4. キャプチャテスト:');

    try {
        // アクティブタブを取得
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs.length === 0) {
            console.error('  ❌ アクティブタブが見つかりません');
            return;
        }

        console.log('  - アクティブタブID:', tabs[0].id);

        // キャプチャ実行
        chrome.tabs.captureVisibleTab(null, { format: 'png' }, (dataUrl) => {
            if (chrome.runtime.lastError) {
                console.error('  ❌ キャプチャエラー:', chrome.runtime.lastError.message);
            } else {
                console.log('  ✅ キャプチャ成功');
                console.log('  - データサイズ:', dataUrl.length, 'bytes');
                console.log('  - プレフィックス:', dataUrl.substring(0, 30));
            }
        });
    } catch (error) {
        console.error('  ❌ エラー:', error.message);
    }
};

console.log('\n使用方法:');
console.log('  - testBackgroundScript() : Pingテスト');
console.log('  - testCapture() : キャプチャテスト');
console.log('='.repeat(60));
