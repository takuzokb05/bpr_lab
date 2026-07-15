/**
 * スクリーンショット範囲テストスクリプト
 * Kindleページのコンソールで実行してください
 */

console.log('='.repeat(60));
console.log('スクリーンショット範囲テスト');
console.log('='.repeat(60));

// デバイス情報
console.log('\n📱 デバイス情報:');
console.log('  - devicePixelRatio:', window.devicePixelRatio);
console.log('  - innerWidth:', window.innerWidth);
console.log('  - innerHeight:', window.innerHeight);
console.log('  - screen.width:', screen.width);
console.log('  - screen.height:', screen.height);

// テスト用の範囲選択
async function testCaptureArea() {
    console.log('\n📸 範囲選択テスト開始...');

    try {
        // 範囲選択UIを表示
        const area = await window.UIOverlay.showRangeSelector();

        console.log('\n✅ 選択された範囲:', area);
        console.log('  - x:', area.x);
        console.log('  - y:', area.y);
        console.log('  - width:', area.width);
        console.log('  - height:', area.height);

        // 実際にキャプチャをテスト
        console.log('\n📸 キャプチャテスト実行中...');

        const response = await new Promise((resolve) => {
            chrome.runtime.sendMessage({
                action: 'captureArea',
                area: area
            }, resolve);
        });

        if (response && response.success) {
            console.log('✅ キャプチャ成功');
            console.log('  - 画像サイズ:', response.imageData.length, 'bytes');

            // 画像を表示
            const img = new Image();
            img.src = response.imageData;
            img.onload = () => {
                console.log('  - 画像の実際のサイズ:', img.width, 'x', img.height);
                console.log('  - 期待サイズ:', area.width, 'x', area.height);

                if (img.width !== area.width || img.height !== area.height) {
                    console.warn('⚠️ サイズが一致しません！');
                    console.warn('  - 倍率:', img.width / area.width, 'x', img.height / area.height);
                }

                // 画像をページに表示
                img.style.position = 'fixed';
                img.style.top = '10px';
                img.style.left = '10px';
                img.style.border = '3px solid red';
                img.style.zIndex = '999999';
                document.body.appendChild(img);

                console.log('✅ キャプチャ画像を画面左上に表示しました（赤枠）');
                console.log('   クリックして削除できます');

                img.addEventListener('click', () => {
                    img.remove();
                    console.log('画像を削除しました');
                });
            };
        } else {
            console.error('❌ キャプチャ失敗:', response?.error);
        }

    } catch (error) {
        console.error('❌ エラー:', error);
    }
}

// 選択範囲を視覚化
function visualizeArea(area) {
    // 既存のオーバーレイを削除
    document.querySelectorAll('.test-area-overlay').forEach(el => el.remove());

    const overlay = document.createElement('div');
    overlay.className = 'test-area-overlay';
    overlay.style.position = 'fixed';
    overlay.style.left = area.x + 'px';
    overlay.style.top = area.y + 'px';
    overlay.style.width = area.width + 'px';
    overlay.style.height = area.height + 'px';
    overlay.style.border = '3px solid lime';
    overlay.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';
    overlay.style.zIndex = '999998';
    overlay.style.pointerEvents = 'none';

    document.body.appendChild(overlay);

    console.log('✅ 選択範囲を緑枠で表示しました');

    setTimeout(() => {
        overlay.remove();
        console.log('緑枠を削除しました');
    }, 5000);
}

// 手動テスト用
window.captureTest = {
    testCaptureArea,
    visualizeArea,

    // 簡易テスト（固定範囲）
    quickTest: async function () {
        const testArea = {
            x: 100,
            y: 100,
            width: 400,
            height: 300
        };

        console.log('\n🚀 クイックテスト: 固定範囲', testArea);

        visualizeArea(testArea);

        const response = await new Promise((resolve) => {
            chrome.runtime.sendMessage({
                action: 'captureArea',
                area: testArea
            }, resolve);
        });

        if (response && response.success) {
            const img = new Image();
            img.src = response.imageData;
            img.onload = () => {
                console.log('✅ キャプチャ成功');
                console.log('  - 期待サイズ:', testArea.width, 'x', testArea.height);
                console.log('  - 実際サイズ:', img.width, 'x', img.height);
                console.log('  - DPR:', window.devicePixelRatio);
                console.log('  - 倍率:', img.width / testArea.width);

                img.style.position = 'fixed';
                img.style.top = '10px';
                img.style.left = '10px';
                img.style.border = '3px solid red';
                img.style.zIndex = '999999';
                document.body.appendChild(img);

                img.addEventListener('click', () => img.remove());
            };
        }
    }
};

console.log('\n使用方法:');
console.log('  captureTest.testCaptureArea() : 範囲選択してキャプチャテスト');
console.log('  captureTest.quickTest() : 固定範囲でクイックテスト');
console.log('='.repeat(60));
