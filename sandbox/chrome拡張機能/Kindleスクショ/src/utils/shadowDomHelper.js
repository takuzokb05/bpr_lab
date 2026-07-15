/**
 * Shadow DOM Helper
 * Shadow DOM内の要素を効率的に検索するためのユーティリティ
 */

/**
 * DOMツリーを再帰的に探索（Shadow DOM含む）
 * querySelectorAll('*') を使わないことで負荷を最小限に抑える
 * @param {Element} root - 探索開始要素
 * @param {number} depth - 現在の深さ
 * @param {number} maxDepth - 最大探索深度
 */
function* traverseDOM(root, depth = 0, maxDepth = 15) {
    if (!root || depth > maxDepth) return;

    // 現在の要素を返す
    yield { element: root, depth, hasShadow: !!root.shadowRoot };

    // Shadow DOMがある場合は内部を優先的に探索
    if (root.shadowRoot) {
        let shadowChild = root.shadowRoot.firstElementChild;
        while (shadowChild) {
            yield* traverseDOM(shadowChild, depth + 1, maxDepth);
            shadowChild = shadowChild.nextElementSibling;
        }
    }

    // 通常の子要素を探索
    let child = root.firstElementChild;
    while (child) {
        yield* traverseDOM(child, depth + 1, maxDepth);
        child = child.nextElementSibling;
    }
}

/**
 * 条件関数に一致する要素を検索
 * @param {Function} criteria - 判定関数 (element) => boolean
 * @param {Element} root - 探索開始要素
 * @returns {Array<{element: Element, depth: number}>}
 */
function findByCriteria(criteria, root = document.body) {
    const results = [];
    const generator = traverseDOM(root);

    for (const item of generator) {
        try {
            if (criteria(item.element)) {
                results.push(item);
            }
        } catch (e) {
            // アクセス拒否など
        }
    }

    return results;
}

/**
 * セレクタに一致する要素をShadow DOM内も含めて検索
 * @param {string} selector - CSSセレクタ
 * @param {Element} root - 探索開始要素
 * @returns {Array<Element>} 見つかった要素の配列
 */
function findInShadowDOM(selector, root = document.body) {
    return findByCriteria(el => el.matches && el.matches(selector), root)
        .map(item => item.element);
}

/**
 * テキスト内容で要素を検索
 * @param {RegExp|string} pattern - 検索パターン
 * @param {Element} root - 探索開始要素
 * @returns {Array<Element>}
 */
function findByText(pattern, root = document.body) {
    const regex = pattern instanceof RegExp ? pattern : new RegExp(pattern);

    return findByCriteria(el => {
        // 子要素が多すぎる要素は、textContent取得が重いのでスキップ（最適化）
        if (el.children.length > 5) return false;

        const text = el.textContent?.trim();
        return text && regex.test(text);
    }, root).map(({ element }) => element);
}

// グローバルに公開
window.ShadowDOMHelper = {
    traverseDOM,
    findInShadowDOM,
    findByCriteria,
    findByText
};
