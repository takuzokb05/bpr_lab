/**
 * Content Script 検証コード
 * 
 * Kindleページのコンソールで実行してください
 */

console.log('='.repeat(60));
console.log('Content Script → Background Script 通信検証');
console.log('='.repeat(60));

// 1. 基本チェック
console.log('\n1. 基本機能チェック:');
console.log('  - chrome.runtime:', typeof chrome.runtime);
console.log('  - chrome.runtime.sendMessage:', typeof chrome.runtime.sendMessage);
console.log('  - chrome.runtime.id:', chrome.runtime.id);

// 2. Pingテスト
async function testPing() {
    console.log('\n2. Pingテスト:');

    return new Promise((resolve) => {
        chrome.runtime.sendMessage({ action: 'ping' }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('  ❌ エラー:', chrome.runtime.lastError.message);
                console.error('  - 原因: Background Scriptが起動していない可能性');
                resolve(false);
            } else {
                console.log('  ✅ 成功:', response);
                resolve(true);
            }
        });
    });
}

// 3. キャプチャテスト
async function testCaptureRequest() {
    console.log('\n3. キャプチャリクエストテスト:');

    const testArea = {
        x: 100,
        y: 100,
        width: 400,
        height: 300
    };

    console.log('  - テスト領域:', testArea);

    return new Promise((resolve) => {
        const startTime = Date.now();

        chrome.runtime.sendMessage({
            action: 'captureArea',
            area: testArea
        }, (response) => {
            const elapsed = Date.now() - startTime;

            if (chrome.runtime.lastError) {
                console.error('  ❌ エラー:', chrome.runtime.lastError.message);
                console.error('  - 経過時間:', elapsed, 'ms');
                resolve(false);
            } else if (!response) {
                console.error('  ❌ 応答なし');
                console.error('  - 経過時間:', elapsed, 'ms');
                console.error('  - 原因: Background ScriptのsendResponseが呼ばれていない');
                resolve(false);
            } else if (response.success) {
                console.log('  ✅ 成功');
                console.log('  - 経過時間:', elapsed, 'ms');
                console.log('  - 画像サイズ:', response.imageData.length, 'bytes');
                resolve(true);
            } else {
                console.error('  ❌ 失敗:', response.error);
                console.error('  - 経過時間:', elapsed, 'ms');
                resolve(false);
            }
        });

        // タイムアウト検出
        setTimeout(() => {
            console.warn('  ⚠️ 5秒経過しても応答なし');
        }, 5000);
    });
}

// 4. Background Scriptの状態確認
async function checkBackgroundScript() {
    console.log('\n4. Background Script状態確認:');

    try {
        const views = chrome.extension.getViews({ type: 'background' });
        console.log('  - Background View数:', views.length);

        if (views.length === 0) {
            console.error('  ❌ Background Scriptが起動していません');
            console.log('  - 対処法:');
            console.log('    1. chrome://extensions/ を開く');
            console.log('    2. 拡張機能をリロード');
            console.log('    3. "service worker" リンクをクリックして確認');
        } else {
            console.log('  ✅ Background Scriptは起動しています');
        }
    } catch (error) {
        console.error('  ❌ エラー:', error.message);
    }
}

// 5. 全テスト実行
async function runAllTests() {
    console.log('\n' + '='.repeat(60));
    console.log('全テスト実行');
    console.log('='.repeat(60));

    await checkBackgroundScript();

    const pingOk = await testPing();
    if (!pingOk) {
        console.error('\n❌ Pingテスト失敗。以降のテストをスキップします。');
        return;
    }

    await testCaptureRequest();

    console.log('\n' + '='.repeat(60));
    console.log('テスト完了');
    console.log('='.repeat(60));
}

// グローバルに公開
window.verifyBackgroundConnection = {
    testPing,
    testCaptureRequest,
    checkBackgroundScript,
    runAllTests
};

console.log('\n使用方法:');
console.log('  verifyBackgroundConnection.runAllTests() : 全テスト実行');
console.log('  verifyBackgroundConnection.testPing() : Pingのみ');
console.log('  verifyBackgroundConnection.testCaptureRequest() : キャプチャのみ');
console.log('='.repeat(60));

// 自動実行
console.log('\n自動テスト開始...\n');
runAllTests();
