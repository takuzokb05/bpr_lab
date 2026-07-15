/**
 * Kindle Cloud Reader DOM Inspector v2
 * Shadow DOM対応版
 * 
 * このスクリプトをKindle Cloud Readerのページでブラウザコンソールに貼り付けて実行してください。
 * Shadow DOMの内部まで探索し、Kindleの構造を完全に解析します。
 */

(function () {
    console.log('🔍 Kindle Cloud Reader DOM Inspector v2 (Shadow DOM対応) 開始...\n');

    const results = {
        pageInfo: {},
        navigation: {},
        content: {},
        ui: {},
        shadowDomDetails: [],
        issues: []
    };

    // ========================================
    // Shadow DOM探索ヘルパー
    // ========================================

    function* traverseDOM(root = document.body, depth = 0, maxDepth = 10) {
        if (depth > maxDepth) return;

        for (const element of root.querySelectorAll('*')) {
            yield { element, depth, hasShadow: !!element.shadowRoot };

            // Shadow DOMがある場合は内部も探索
            if (element.shadowRoot) {
                yield* traverseDOM(element.shadowRoot, depth + 1, maxDepth);
            }
        }
    }

    function findInShadowDOM(selector, root = document) {
        const results = [];

        // 通常のDOM検索
        const normalResults = root.querySelectorAll(selector);
        results.push(...normalResults);

        // Shadow DOM内を探索
        for (const { element } of traverseDOM(root)) {
            if (element.shadowRoot) {
                const shadowResults = element.shadowRoot.querySelectorAll(selector);
                results.push(...shadowResults);
            }
        }

        return results;
    }

    function findByCriteria(criteria, root = document) {
        const results = [];

        for (const { element, depth } of traverseDOM(root)) {
            if (criteria(element)) {
                results.push({ element, depth });
            }
        }

        return results;
    }

    // ========================================
    // 1. Shadow DOMの詳細分析
    // ========================================
    console.log('🌑 1. Shadow DOMを詳細分析中...');

    const shadowHosts = Array.from(document.querySelectorAll('*'))
        .filter(el => el.shadowRoot);

    shadowHosts.forEach((host, index) => {
        const shadowRoot = host.shadowRoot;
        const children = shadowRoot.querySelectorAll('*');

        const detail = {
            index,
            hostTag: host.tagName,
            hostId: host.id,
            hostClasses: Array.from(host.classList),
            childCount: children.length,
            childTags: [...new Set(Array.from(children).map(c => c.tagName))],
            hasCanvas: shadowRoot.querySelector('canvas') !== null,
            hasIframe: shadowRoot.querySelector('iframe') !== null,
            hasImage: shadowRoot.querySelector('img') !== null,
            hasButton: shadowRoot.querySelector('button') !== null
        };

        results.shadowDomDetails.push(detail);
        console.log(`  Shadow #${index}:`, detail);
    });

    // ========================================
    // 2. コンテンツエリアの再探索（Shadow DOM内含む）
    // ========================================
    console.log('\n📄 2. コンテンツエリアを再探索中（Shadow DOM内含む）...');

    // Canvas要素を探す（Kindleは画像をCanvasで表示することが多い）
    const canvases = findByCriteria(el => el.tagName === 'CANVAS');

    results.content.canvases = canvases.map(({ element, depth }) => {
        const rect = element.getBoundingClientRect();
        return {
            depth,
            inShadowDOM: depth > 0,
            id: element.id,
            dimensions: {
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            },
            visible: rect.width > 0 && rect.height > 0,
            context: element.getContext ? '2d-capable' : 'unknown'
        };
    });

    console.log(`  Canvas要素: ${results.content.canvases.length}個検出`);
    results.content.canvases.forEach(c => console.log('   ', c));

    // 画像要素も探す
    const images = findByCriteria(el => el.tagName === 'IMG');

    results.content.images = images.slice(0, 10).map(({ element, depth }) => {
        const rect = element.getBoundingClientRect();
        return {
            depth,
            inShadowDOM: depth > 0,
            src: element.src?.substring(0, 100),
            dimensions: {
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }
        };
    });

    console.log(`  画像要素: ${results.content.images.length}個検出（最大10個表示）`);

    // ========================================
    // 3. ナビゲーションボタンの再探索
    // ========================================
    console.log('\n🔄 3. ナビゲーションボタンを再探索中...');

    // クリック可能な領域を探す
    const clickableAreas = findByCriteria(el => {
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return (
            (el.tagName === 'BUTTON' ||
                el.tagName === 'A' ||
                el.onclick ||
                style.cursor === 'pointer') &&
            rect.width > 20 &&
            rect.height > 20
        );
    });

    results.navigation.clickableAreas = clickableAreas.slice(0, 20).map(({ element, depth }) => {
        const rect = element.getBoundingClientRect();
        return {
            depth,
            inShadowDOM: depth > 0,
            tag: element.tagName,
            id: element.id,
            ariaLabel: element.getAttribute('aria-label'),
            text: element.textContent?.trim().substring(0, 50),
            position: {
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }
        };
    });

    console.log(`  クリック可能エリア: ${results.navigation.clickableAreas.length}個検出`);

    // 右側と左側のクリック領域を特定
    const viewportWidth = window.innerWidth;
    const rightClickAreas = results.navigation.clickableAreas.filter(
        area => area.position.x > viewportWidth * 0.7
    );
    const leftClickAreas = results.navigation.clickableAreas.filter(
        area => area.position.x < viewportWidth * 0.3
    );

    console.log(`  右側クリック領域（次ページ候補）: ${rightClickAreas.length}個`);
    console.log(`  左側クリック領域（前ページ候補）: ${leftClickAreas.length}個`);

    // ========================================
    // 4. ページ番号表示の再探索
    // ========================================
    console.log('\n📖 4. ページ番号表示を再探索中...');

    const textElements = findByCriteria(el => {
        const text = el.textContent?.trim();
        return text && (
            /\d+\s*\/\s*\d+/.test(text) || // "12 / 240" 形式
            /page\s*\d+/i.test(text) ||     // "Page 12" 形式
            /location\s*\d+/i.test(text)    // "Location 123" 形式
        );
    });

    results.pageInfo.indicators = textElements.map(({ element, depth }) => ({
        depth,
        inShadowDOM: depth > 0,
        text: element.textContent?.trim(),
        tag: element.tagName,
        ariaLabel: element.getAttribute('aria-label')
    }));

    console.log('  ページ番号表示:', results.pageInfo.indicators);

    // ========================================
    // 5. イベントリスナーの検出
    // ========================================
    console.log('\n👂 5. イベントリスナーを検出中...');

    // キーボードイベントリスナー
    const hasKeyListeners = {
        document: !!document.onkeydown || !!document.onkeyup,
        body: !!document.body.onkeydown || !!document.body.onkeyup
    };

    results.navigation.keyboardSupport = hasKeyListeners;
    console.log('  キーボードサポート:', hasKeyListeners);

    // タッチイベントリスナー
    const hasTouchListeners = {
        document: !!document.ontouchstart || !!document.ontouchend,
        body: !!document.body.ontouchstart || !!document.body.ontouchend
    };

    results.navigation.touchSupport = hasTouchListeners;
    console.log('  タッチサポート:', hasTouchListeners);

    // ========================================
    // 6. 推奨される撮影範囲の再計算
    // ========================================
    console.log('\n📐 6. 推奨撮影範囲を再計算中...');

    // 最も大きいCanvas要素を撮影対象とする
    const largestCanvas = results.content.canvases
        .filter(c => c.visible)
        .sort((a, b) => (b.dimensions.width * b.dimensions.height) - (a.dimensions.width * a.dimensions.height))[0];

    if (largestCanvas) {
        results.content.recommendedCaptureArea = {
            x: largestCanvas.dimensions.x,
            y: largestCanvas.dimensions.y,
            width: largestCanvas.dimensions.width,
            height: largestCanvas.dimensions.height,
            note: '最大のCanvas要素（Kindleのページ表示）',
            inShadowDOM: largestCanvas.inShadowDOM
        };
        console.log('  ✅ 推奨範囲:', results.content.recommendedCaptureArea);
    } else {
        results.issues.push('❌ 撮影可能なCanvas要素が見つかりませんでした');
        console.log('  ❌ Canvas要素が見つかりません');
    }

    // ========================================
    // 7. ページめくり方法の推奨
    // ========================================
    console.log('\n💡 7. ページめくり方法を分析中...');

    const pageTurnMethods = [];

    // 方法1: 右側クリック
    if (rightClickAreas.length > 0) {
        pageTurnMethods.push({
            method: 'click_right_area',
            priority: 1,
            description: '画面右側のクリック可能エリアをクリック',
            target: rightClickAreas[0]
        });
    }

    // 方法2: キーボード（矢印キー）
    if (hasKeyListeners.document || hasKeyListeners.body) {
        pageTurnMethods.push({
            method: 'keyboard_arrow',
            priority: 2,
            description: '右矢印キー（ArrowRight）を送信',
            keyCode: 'ArrowRight'
        });
    }

    // 方法3: 特定のボタン要素
    const nextButtons = results.navigation.clickableAreas.filter(
        area => area.ariaLabel?.toLowerCase().includes('next') ||
            area.text?.toLowerCase().includes('next')
    );

    if (nextButtons.length > 0) {
        pageTurnMethods.push({
            method: 'click_next_button',
            priority: 3,
            description: '「Next」ボタンをクリック',
            target: nextButtons[0]
        });
    }

    results.navigation.pageTurnMethods = pageTurnMethods;
    console.log('  利用可能なページめくり方法:', pageTurnMethods);

    // ========================================
    // 8. 最終ページ検出方法
    // ========================================
    console.log('\n🏁 8. 最終ページ検出方法を分析中...');

    const endDetectionMethods = [];

    // 方法1: ページ番号の監視
    if (results.pageInfo.indicators.length > 0) {
        endDetectionMethods.push({
            method: 'page_number_monitoring',
            description: 'ページ番号が変化しなくなったら終了',
            element: results.pageInfo.indicators[0]
        });
    }

    // 方法2: Canvas内容の比較
    if (largestCanvas) {
        endDetectionMethods.push({
            method: 'canvas_content_comparison',
            description: 'Canvas内容のハッシュ値を比較し、変化がなければ終了'
        });
    }

    // 方法3: クリック領域の状態変化
    endDetectionMethods.push({
        method: 'clickable_area_state',
        description: '次ページ領域がクリック不可になったら終了'
    });

    results.navigation.endDetectionMethods = endDetectionMethods;
    console.log('  最終ページ検出方法:', endDetectionMethods);

    // ========================================
    // 9. Chrome Extension実装のヒント
    // ========================================
    console.log('\n🔧 9. Chrome Extension実装のヒント...');

    const implementationHints = {
        contentScript: {
            shadowDomAccess: 'Shadow DOMにアクセスするため、element.shadowRootを使用する必要があります',
            captureMethod: largestCanvas ? 'chrome.tabs.captureVisibleTab() を使用してCanvas領域をキャプチャ' : 'Canvas要素が見つからないため、別の方法を検討',
            injection: 'UIボタンは通常のDOMに注入可能（Shadow DOM外）'
        },
        pageNavigation: {
            recommended: pageTurnMethods[0]?.method || 'unknown',
            fallback: pageTurnMethods[1]?.method || 'manual',
            waitTime: '1.5秒（ページ読み込み待機）'
        },
        endDetection: {
            primary: endDetectionMethods[0]?.method || 'unknown',
            secondary: endDetectionMethods[1]?.method || 'manual'
        }
    };

    results.implementationHints = implementationHints;
    console.log(implementationHints);

    // ========================================
    // 10. 結果のサマリー
    // ========================================
    console.log('\n' + '='.repeat(60));
    console.log('📊 診断結果サマリー v2');
    console.log('='.repeat(60));

    console.log('\n✅ 検出された要素:');
    console.log(`  - Shadow DOM: ${results.shadowDomDetails.length}個`);
    console.log(`  - Canvas要素: ${results.content.canvases.length}個`);
    console.log(`  - 画像要素: ${results.content.images.length}個`);
    console.log(`  - クリック可能エリア: ${results.navigation.clickableAreas.length}個`);
    console.log(`  - ページ番号表示: ${results.pageInfo.indicators.length}個`);

    if (results.issues.length > 0) {
        console.log('\n⚠️ 注意事項:');
        results.issues.forEach(issue => console.log(`  ${issue}`));
    }

    console.log('\n💡 推奨実装アプローチ:');

    if (largestCanvas) {
        const area = results.content.recommendedCaptureArea;
        console.log(`  ✓ 撮影範囲: x=${area.x}, y=${area.y}, w=${area.width}, h=${area.height}`);
        console.log(`    (Shadow DOM内: ${area.inShadowDOM ? 'はい' : 'いいえ'})`);
    }

    if (pageTurnMethods.length > 0) {
        console.log(`  ✓ ページめくり: ${pageTurnMethods[0].description}`);
    }

    if (endDetectionMethods.length > 0) {
        console.log(`  ✓ 最終ページ検出: ${endDetectionMethods[0].description}`);
    }

    console.log('\n📋 完全な結果オブジェクト:');
    console.log(results);

    // グローバルに保存
    window.kindleInspectorResults = results;
    console.log('\n💾 結果は window.kindleInspectorResults に保存されました');

    // ダウンロード関数
    window.downloadResults = function () {
        const dataStr = JSON.stringify(results, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'kindle-inspector-v2-results.json';
        link.click();
        URL.revokeObjectURL(url);
        console.log('✅ ダウンロードを開始しました');
    };

    console.log('\n📥 結果をJSONでダウンロード: downloadResults()');

    // ========================================
    // 11. インタラクティブテスト関数
    // ========================================

    // ページめくりテスト
    window.testPageTurn = function () {
        console.log('🧪 ページめくりテスト開始...');

        if (pageTurnMethods.length === 0) {
            console.log('❌ ページめくり方法が見つかりません');
            return;
        }

        const method = pageTurnMethods[0];
        console.log(`  方法: ${method.description}`);

        if (method.method === 'click_right_area' && method.target) {
            console.log('  右側エリアをクリックします...');
            // 実際のクリックはシミュレーション
            console.log('  ⚠️ 実際のクリックは手動で確認してください');
        } else if (method.method === 'keyboard_arrow') {
            console.log('  右矢印キーを送信します...');
            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
            console.log('  ✅ キーイベントを送信しました');
        }
    };

    // Canvas内容取得テスト
    window.testCanvasCapture = function () {
        console.log('🧪 Canvas撮影テスト開始...');

        if (!largestCanvas) {
            console.log('❌ Canvas要素が見つかりません');
            return;
        }

        console.log('  Canvas要素を検出しました');
        console.log('  ⚠️ 実際の撮影はchrome.tabs.captureVisibleTab()を使用してください');
        console.log('  （Content Scriptからは直接実行できません）');
    };

    console.log('\n🧪 テスト関数:');
    console.log('  - testPageTurn() : ページめくりをテスト');
    console.log('  - testCanvasCapture() : Canvas撮影をテスト');

    return results;

})();
