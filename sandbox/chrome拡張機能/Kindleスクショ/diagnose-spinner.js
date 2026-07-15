/**
 * Kindleのローディングスピナー診断スクリプト
 * コンソールで実行してスピナー要素を特定する
 */

console.log('=== Kindle Spinner Diagnostic ===');

// 1. よくあるスピナー関連のクラス名やID
const commonSpinnerSelectors = [
    '[class*="spinner"]',
    '[class*="loading"]',
    '[class*="loader"]',
    '[id*="spinner"]',
    '[id*="loading"]',
    '[id*="loader"]',
    '[aria-busy="true"]',
    '[aria-live="polite"]',
    '[role="progressbar"]',
    '[class*="progress"]'
];

console.log('1. 通常のDOM内でスピナー要素を検索:');
commonSpinnerSelectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    if (elements.length > 0) {
        console.log(`  ✓ 見つかりました: ${selector}`, elements);
        elements.forEach(el => {
            console.log('    - 要素:', el);
            console.log('    - 表示状態:', window.getComputedStyle(el).display);
            console.log('    - 可視性:', window.getComputedStyle(el).visibility);
            console.log('    - opacity:', window.getComputedStyle(el).opacity);
        });
    }
});

// 2. Shadow DOM内を検索
console.log('\n2. Shadow DOM内でスピナー要素を検索:');
function findInShadowDOM(root, depth = 0) {
    if (depth > 5) return; // 深さ制限

    const indent = '  '.repeat(depth);

    if (root.shadowRoot) {
        console.log(`${indent}Shadow Root found in:`, root);
        commonSpinnerSelectors.forEach(selector => {
            const elements = root.shadowRoot.querySelectorAll(selector);
            if (elements.length > 0) {
                console.log(`${indent}  ✓ ${selector}:`, elements);
            }
        });

        // Shadow Root内の子要素も再帰的に探索
        root.shadowRoot.querySelectorAll('*').forEach(child => {
            findInShadowDOM(child, depth + 1);
        });
    }

    // 通常の子要素も探索
    if (root.children) {
        Array.from(root.children).forEach(child => {
            findInShadowDOM(child, depth + 1);
        });
    }
}

findInShadowDOM(document.body);

// 3. アニメーション中の要素を検出
console.log('\n3. アニメーション中の要素を検出:');
const allElements = document.querySelectorAll('*');
const animatingElements = [];
allElements.forEach(el => {
    const style = window.getComputedStyle(el);
    if (style.animation !== 'none' || style.transition !== 'none') {
        animatingElements.push({
            element: el,
            animation: style.animation,
            transition: style.transition
        });
    }
});
if (animatingElements.length > 0) {
    console.log('  アニメーション中の要素:', animatingElements);
}

// 4. 監視用の関数を提供
console.log('\n4. リアルタイム監視を開始します...');
console.log('   ページをめくってスピナーが表示されるタイミングを確認してください。');

let lastSpinnerState = null;
const monitorInterval = setInterval(() => {
    let spinnerFound = false;
    let spinnerInfo = [];

    // 通常のDOMをチェック
    commonSpinnerSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            const style = window.getComputedStyle(el);
            if (style.display !== 'none' && style.visibility !== 'hidden' && parseFloat(style.opacity) > 0) {
                spinnerFound = true;
                spinnerInfo.push({
                    selector,
                    element: el,
                    className: el.className,
                    id: el.id
                });
            }
        });
    });

    // 状態が変わった時だけログ出力
    const currentState = spinnerFound ? 'VISIBLE' : 'HIDDEN';
    if (currentState !== lastSpinnerState) {
        if (spinnerFound) {
            console.log('🔄 スピナー検出!', spinnerInfo);
        } else {
            console.log('✅ スピナー消失');
        }
        lastSpinnerState = currentState;
    }
}, 100);

// 10秒後に監視を停止
setTimeout(() => {
    clearInterval(monitorInterval);
    console.log('\n監視を停止しました。');
    console.log('スピナーが検出された場合、上記の情報を使って待機処理を実装できます。');
}, 10000);

console.log('\n=== 診断スクリプト実行中 ===');
console.log('今すぐページをめくってください！');
