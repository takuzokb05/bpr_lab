/**
 * ページ送り診断スクリプト
 * Kindleページのコンソールで実行してください
 */

console.log('='.repeat(60));
console.log('ページ送り診断');
console.log('='.repeat(60));

// 1. 右側クリック領域の検出
function testFindRightArea() {
    console.log('\n1. 右側クリック領域の検出:');

    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    console.log('  - ビューポート:', viewportWidth, 'x', viewportHeight);
    console.log('  - 検索範囲: x >', viewportWidth * 0.7);

    const rightAreas = window.ShadowDOMHelper.findByCriteria(el => {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);

        const isRight = rect.x > viewportWidth * 0.7;
        const isTall = rect.height > viewportHeight * 0.5;
        const isWide = rect.width > 50;
        const isClickable = style.pointerEvents !== 'none';

        if (isRight && isTall && isWide && isClickable) {
            console.log('  ✅ 候補発見:', {
                element: el.tagName,
                class: el.className,
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                pointerEvents: style.pointerEvents
            });
        }

        return isRight && isTall && isWide && isClickable;
    });

    console.log('  - 見つかった領域:', rightAreas.length, '個');

    if (rightAreas.length > 0) {
        const area = rightAreas[0].element;
        area.style.outline = '3px solid red';
        console.log('  ✅ 最初の領域を赤枠で表示しました');
        return area;
    } else {
        console.error('  ❌ 右側クリック領域が見つかりません');
        return null;
    }
}

// 2. クリックテスト
function testClick(element) {
    console.log('\n2. クリックテスト:');

    if (!element) {
        console.error('  ❌ 要素がありません');
        return;
    }

    const rect = element.getBoundingClientRect();
    const centerX = rect.x + rect.width / 2;
    const centerY = rect.y + rect.height / 2;

    console.log('  - クリック位置:', Math.round(centerX), ',', Math.round(centerY));

    const clickEvent = new MouseEvent('click', {
        view: window,
        bubbles: true,
        cancelable: true,
        clientX: centerX,
        clientY: centerY
    });

    element.dispatchEvent(clickEvent);
    console.log('  ✅ クリックイベント発火');
}

// 3. キーボードイベントテスト
function testKeyboard() {
    console.log('\n3. キーボードイベントテスト:');

    const event = new KeyboardEvent('keydown', {
        key: 'ArrowRight',
        code: 'ArrowRight',
        keyCode: 39,
        bubbles: true,
        cancelable: true
    });

    document.dispatchEvent(event);
    console.log('  ✅ ArrowRightキーイベント発火');
}

// 4. ページ番号の変化を監視
async function monitorPageChange(duration = 3000) {
    console.log('\n4. ページ番号変化の監視:');

    const startPage = window.PageDetector.getCurrentPageNumber();
    console.log('  - 開始ページ:', startPage?.current);

    const startTime = Date.now();
    let changed = false;

    while (Date.now() - startTime < duration) {
        await window.PageDetector.sleep(100);
        const currentPage = window.PageDetector.getCurrentPageNumber();

        if (currentPage && currentPage.current !== startPage?.current) {
            console.log('  ✅ ページ変化検出:', startPage?.current, '→', currentPage.current);
            changed = true;
            break;
        }
    }

    if (!changed) {
        console.error('  ❌', duration, 'ms経過してもページが変わりませんでした');
    }

    return changed;
}

// 5. 全テスト実行
async function runPageNavigationTest() {
    console.log('\n' + '='.repeat(60));
    console.log('全テスト実行');
    console.log('='.repeat(60));

    // 右側領域を探す
    const rightArea = testFindRightArea();

    if (rightArea) {
        // クリックテスト
        testClick(rightArea);

        // ページ変化を監視
        const changed = await monitorPageChange(2000);

        if (!changed) {
            console.log('\n別の方法を試します...');
            testKeyboard();
            await monitorPageChange(2000);
        }
    } else {
        console.log('\nキーボードイベントを試します...');
        testKeyboard();
        await monitorPageChange(2000);
    }

    console.log('\n' + '='.repeat(60));
    console.log('テスト完了');
    console.log('='.repeat(60));
}

// グローバルに公開
window.pageNavTest = {
    testFindRightArea,
    testClick,
    testKeyboard,
    monitorPageChange,
    runPageNavigationTest
};

console.log('\n使用方法:');
console.log('  pageNavTest.runPageNavigationTest() : 全テスト実行');
console.log('  pageNavTest.testFindRightArea() : 右側領域を探す');
console.log('='.repeat(60));

// 自動実行
console.log('\n自動テスト開始...\n');
runPageNavigationTest();
