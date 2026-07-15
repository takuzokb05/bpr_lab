/**
 * Loading Logic Test
 * ローディング判定ロジックの単体テスト
 */

// --- Mock Environment ---
class MockElement {
    constructor(tagName, classes = '', id = '') {
        this.tagName = tagName;
        this.className = classes;
        this.id = id;
        this.style = { display: 'block', visibility: 'visible', opacity: '1' };
    }

    // getComputedStyle用
    get computedStyle() {
        return this.style;
    }
}

// 簡易DOM Mock
const document = {
    elements: [],

    // テスト用に要素を追加
    _add(el) { this.elements.push(el); },
    // テスト用に全クリア
    _clear() { this.elements = []; },

    querySelectorAll(selector) {
        // 簡易的なセレクタ判定
        return this.elements.filter(el => {
            if (selector.includes('.')) {
                return el.className.includes(selector.replace('.', ''));
            }
            if (selector.includes('#')) {
                return el.id === (selector.replace('#', ''));
            }
            if (selector.includes('class*="spinner"')) {
                return el.className.includes('spinner');
            }
            return false;
        });
    }
};

const window = {
    getComputedStyle(el) { return el.computedStyle; },

    ShadowDOMHelper: {
        findAllShadowHosts: () => [] // 今回はShadow DOMまではテストしない
    },

    PageDetector: {
        sleep: (ms) => new Promise(r => setTimeout(r, 10)) // テスト用に待機時間を短縮
    }
};

// --- Target Logic (Source Code Copy for Testing) ---

// src/utils/loadingDetector.js のロジック部分
function isLoading() {
    const loadingSelectors = [
        '[class*="spinner"]',
        '.loading-spinner'
    ];

    for (const selector of loadingSelectors) {
        const elements = document.querySelectorAll(selector);
        for (const el of elements) {
            const style = window.getComputedStyle(el);
            if (style.display !== 'none' &&
                style.visibility !== 'hidden' &&
                parseFloat(style.opacity) > 0) {
                return true;
            }
        }
    }
    return false;
}

async function waitForLoadingComplete(timeout = 2000) {
    const startTime = Date.now();
    // テスト用：最大5回チェック
    let checks = 0;

    while (Date.now() - startTime < timeout && checks < 20) {
        if (!isLoading()) {
            return true;
        }
        await window.PageDetector.sleep(100);
        checks++;
    }
    return false;
}

// src/content/content.js の waitForContentStable ロジック部分
async function waitForContentStable() {
    // スピナーチェック
    if (isLoading()) {
        console.log('  [Logic] Spinner detected. Waiting...');
        const result = await waitForLoadingComplete(1000); // テスト用に短く
        return result ? 'Stable (After Wait)' : 'Timeout';
    }

    return 'Stable (Immediate)';
}


// --- Tests ---

async function runTests() {
    console.log('=== Testing Loading Logic ===\n');

    // Test 1: 正常時（スピナーなし）
    console.log('Test 1: Normal Case (No Spinner)');
    document._clear();

    const start1 = Date.now();
    const result1 = await waitForContentStable();
    const time1 = Date.now() - start1;

    if (result1 === 'Stable (Immediate)' && time1 < 50) {
        console.log('  ✅ PASS: Returns immediately (Time: ' + time1 + 'ms)');
    } else {
        console.error('  ❌ FAIL: Did not return immediately. Result:', result1, 'Time:', time1);
    }
    console.log('');


    // Test 2: ローディング中（スピナーあり -> 消える）
    console.log('Test 2: Loading Case (Spinner disappears)');
    document._clear();
    const spinner = new MockElement('DIV', 'loading-spinner');
    document._add(spinner);

    // 50ms後にスピナーを消すシミュレーション (テスト環境のsleepは10msなので5ループくらい)
    setTimeout(() => {
        console.log('  [Sim] Removing spinner...');
        document._clear();
    }, 50);

    const start2 = Date.now();
    const result2 = await waitForContentStable();

    if (result2 === 'Stable (After Wait)') {
        console.log('  ✅ PASS: Waited and confirmed stability');
    } else {
        console.error('  ❌ FAIL: Unexpected result:', result2);
    }
    console.log('');


    // Test 3: 無限ロード（スピナー消えない -> タイムアウト）
    console.log('Test 3: Infinite Loading Case (Timeout)');
    document._clear();
    document._add(new MockElement('DIV', 'loading-spinner')); // 消さない

    const start3 = Date.now();
    const result3 = await waitForContentStable();

    if (result3 === 'Timeout') {
        console.log('  ✅ PASS: Timed out correctly (Safety check)');
    } else {
        console.error('  ❌ FAIL: Did not timeout. Result:', result3);
    }
}

runTests();
