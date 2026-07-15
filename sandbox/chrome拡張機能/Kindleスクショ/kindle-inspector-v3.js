/**
 * Kindle Cloud Reader DOM Inspector v3
 * 画像ベース表示対応版
 * 
 * Canvas要素が見つからなかったため、画像要素とその他の表示方法を詳細調査します。
 */

(function () {
    console.log('🔍 Kindle Cloud Reader DOM Inspector v3 開始...\n');
    console.log('📌 前回の結果: Canvas=0, Images=1, Shadow DOM=28個\n');

    const results = {
        displayMethod: null,
        captureTarget: null,
        detailedAnalysis: {}
    };

    // ========================================
    // 1. 画像要素の詳細分析
    // ========================================
    console.log('🖼️ 1. 画像要素を詳細分析中...');

    function* traverseDOM(root = document.body, depth = 0, maxDepth = 10) {
        if (depth > maxDepth) return;

        for (const element of root.querySelectorAll('*')) {
            yield { element, depth, hasShadow: !!element.shadowRoot };

            if (element.shadowRoot) {
                yield* traverseDOM(element.shadowRoot, depth + 1, maxDepth);
            }
        }
    }

    const allImages = [];
    for (const { element, depth } of traverseDOM()) {
        if (element.tagName === 'IMG') {
            const rect = element.getBoundingClientRect();
            const computedStyle = window.getComputedStyle(element);

            allImages.push({
                element,
                depth,
                inShadowDOM: depth > 0,
                id: element.id,
                className: element.className,
                src: element.src,
                srcLength: element.src?.length || 0,
                isBase64: element.src?.startsWith('data:'),
                isBlob: element.src?.startsWith('blob:'),
                alt: element.alt,
                dimensions: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    naturalWidth: element.naturalWidth,
                    naturalHeight: element.naturalHeight
                },
                visible: rect.width > 0 && rect.height > 0 && computedStyle.visibility !== 'hidden',
                zIndex: computedStyle.zIndex,
                position: computedStyle.position,
                parent: {
                    tag: element.parentElement?.tagName,
                    id: element.parentElement?.id,
                    className: element.parentElement?.className
                }
            });
        }
    }

    results.detailedAnalysis.images = allImages;
    console.log(`  検出された画像: ${allImages.length}個`);

    // 表示されている画像のみフィルタ
    const visibleImages = allImages.filter(img => img.visible);
    console.log(`  表示中の画像: ${visibleImages.length}個`);

    // 最も大きい画像を特定
    const largestImage = visibleImages.sort((a, b) =>
        (b.dimensions.width * b.dimensions.height) - (a.dimensions.width * a.dimensions.height)
    )[0];

    if (largestImage) {
        console.log('\n  📍 最大の画像要素:');
        console.log('    位置:', largestImage.dimensions);
        console.log('    Shadow DOM内:', largestImage.inShadowDOM);
        console.log('    ID:', largestImage.id);
        console.log('    Class:', largestImage.className);
        console.log('    親要素:', largestImage.parent);
        console.log('    画像タイプ:', largestImage.isBase64 ? 'Base64' : largestImage.isBlob ? 'Blob' : 'URL');

        results.captureTarget = {
            type: 'image',
            element: largestImage,
            captureMethod: 'chrome.tabs.captureVisibleTab',
            area: largestImage.dimensions
        };
    }

    // ========================================
    // 2. SVG要素の検出
    // ========================================
    console.log('\n📐 2. SVG要素を検出中...');

    const allSVGs = [];
    for (const { element, depth } of traverseDOM()) {
        if (element.tagName === 'SVG' || element.tagName === 'svg') {
            const rect = element.getBoundingClientRect();
            allSVGs.push({
                depth,
                inShadowDOM: depth > 0,
                dimensions: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                visible: rect.width > 0 && rect.height > 0
            });
        }
    }

    results.detailedAnalysis.svgs = allSVGs;
    console.log(`  SVG要素: ${allSVGs.length}個`);

    // ========================================
    // 3. iframe内のコンテンツ確認
    // ========================================
    console.log('\n🖼️ 3. iframe内のコンテンツを確認中...');

    const allIframes = [];
    for (const { element, depth } of traverseDOM()) {
        if (element.tagName === 'IFRAME') {
            const rect = element.getBoundingClientRect();
            let accessible = false;
            let innerContent = null;

            try {
                const doc = element.contentDocument || element.contentWindow?.document;
                accessible = !!doc;

                if (accessible) {
                    const innerImages = doc.querySelectorAll('img');
                    const innerCanvases = doc.querySelectorAll('canvas');
                    innerContent = {
                        images: innerImages.length,
                        canvases: innerCanvases.length,
                        bodyHTML: doc.body?.innerHTML?.substring(0, 200)
                    };
                }
            } catch (e) {
                accessible = false;
            }

            allIframes.push({
                depth,
                inShadowDOM: depth > 0,
                id: element.id,
                src: element.src,
                dimensions: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                accessible,
                innerContent
            });
        }
    }

    results.detailedAnalysis.iframes = allIframes;
    console.log(`  iframe: ${allIframes.length}個`);

    allIframes.forEach((iframe, i) => {
        console.log(`    iframe #${i}:`, {
            accessible: iframe.accessible,
            content: iframe.innerContent
        });
    });

    // ========================================
    // 4. コンテナ要素の特定
    // ========================================
    console.log('\n📦 4. メインコンテナ要素を特定中...');

    // 大きな領域を持つdiv要素を探す
    const largeContainers = [];
    for (const { element, depth } of traverseDOM()) {
        if (element.tagName === 'DIV') {
            const rect = element.getBoundingClientRect();
            const area = rect.width * rect.height;

            // 画面の20%以上を占める要素
            const viewportArea = window.innerWidth * window.innerHeight;
            if (area > viewportArea * 0.2 && rect.width > 300 && rect.height > 300) {
                const computedStyle = window.getComputedStyle(element);
                largeContainers.push({
                    element,
                    depth,
                    inShadowDOM: depth > 0,
                    id: element.id,
                    className: element.className,
                    dimensions: {
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    areaPercent: Math.round((area / viewportArea) * 100),
                    backgroundColor: computedStyle.backgroundColor,
                    childCount: element.children.length
                });
            }
        }
    }

    // 面積でソート
    largeContainers.sort((a, b) => b.areaPercent - a.areaPercent);

    results.detailedAnalysis.largeContainers = largeContainers.slice(0, 5);
    console.log(`  大きなコンテナ: ${largeContainers.length}個（上位5個表示）`);

    largeContainers.slice(0, 5).forEach((container, i) => {
        console.log(`    #${i}: ${container.areaPercent}% - ${container.id || container.className}`);
    });

    // ========================================
    // 5. ページ番号要素の詳細確認
    // ========================================
    console.log('\n📖 5. ページ番号要素を詳細確認中...');

    const pageIndicators = [];
    for (const { element, depth } of traverseDOM()) {
        const text = element.textContent?.trim();
        if (text && text.length < 100) { // 短いテキストのみ
            // ページ番号パターン
            const patterns = [
                /(\d+)\s*\/\s*(\d+)/,           // "12 / 240"
                /page\s*(\d+)\s*of\s*(\d+)/i,   // "Page 12 of 240"
                /location\s*(\d+)/i,             // "Location 123"
                /(\d+)%/                         // "45%"
            ];

            for (const pattern of patterns) {
                const match = text.match(pattern);
                if (match) {
                    const rect = element.getBoundingClientRect();
                    pageIndicators.push({
                        element,
                        depth,
                        inShadowDOM: depth > 0,
                        text,
                        pattern: pattern.source,
                        match: match[0],
                        tag: element.tagName,
                        id: element.id,
                        className: element.className,
                        position: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y)
                        }
                    });
                    break;
                }
            }
        }
    }

    results.detailedAnalysis.pageIndicators = pageIndicators;
    console.log(`  ページ番号候補: ${pageIndicators.length}個`);

    pageIndicators.slice(0, 5).forEach((indicator, i) => {
        console.log(`    #${i}: "${indicator.text}" (${indicator.pattern})`);
    });

    // ========================================
    // 6. 表示方式の判定
    // ========================================
    console.log('\n🎯 6. 表示方式を判定中...');

    let displayMethod = 'unknown';
    let captureStrategy = null;

    if (largestImage && largestImage.dimensions.width > 400) {
        displayMethod = 'image-based';
        captureStrategy = {
            method: 'tab_capture',
            description: 'chrome.tabs.captureVisibleTab()で画面全体をキャプチャし、画像領域を切り抜く',
            target: largestImage.dimensions,
            note: 'Content Scriptから直接実行不可。Background Scriptと連携が必要'
        };
    } else if (allIframes.some(f => f.accessible && f.innerContent?.images > 0)) {
        displayMethod = 'iframe-based';
        const accessibleIframe = allIframes.find(f => f.accessible);
        captureStrategy = {
            method: 'iframe_capture',
            description: 'iframe内の画像を直接取得',
            target: accessibleIframe
        };
    } else if (largeContainers.length > 0) {
        displayMethod = 'container-based';
        captureStrategy = {
            method: 'tab_capture',
            description: 'chrome.tabs.captureVisibleTab()でコンテナ領域をキャプチャ',
            target: largeContainers[0].dimensions
        };
    }

    results.displayMethod = displayMethod;
    results.captureStrategy = captureStrategy;

    console.log(`  表示方式: ${displayMethod}`);
    console.log('  キャプチャ戦略:', captureStrategy);

    // ========================================
    // 7. ページめくりの詳細分析
    // ========================================
    console.log('\n🔄 7. ページめくり方法を詳細分析中...');

    // 右側の大きなクリック領域を探す
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    const rightClickAreas = [];
    for (const { element, depth } of traverseDOM()) {
        const rect = element.getBoundingClientRect();

        // 右側30%のエリアで、高さが画面の50%以上
        if (rect.x > viewportWidth * 0.7 &&
            rect.height > viewportHeight * 0.5 &&
            rect.width > 50) {

            const computedStyle = window.getComputedStyle(element);
            const isClickable = computedStyle.cursor === 'pointer' ||
                element.onclick ||
                element.tagName === 'BUTTON' ||
                element.tagName === 'A';

            rightClickAreas.push({
                element,
                depth,
                inShadowDOM: depth > 0,
                tag: element.tagName,
                id: element.id,
                className: element.className,
                dimensions: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                cursor: computedStyle.cursor,
                isClickable
            });
        }
    }

    results.detailedAnalysis.rightClickAreas = rightClickAreas;
    console.log(`  右側クリック領域: ${rightClickAreas.length}個`);

    rightClickAreas.slice(0, 3).forEach((area, i) => {
        console.log(`    #${i}: ${area.tag} - ${area.dimensions.width}x${area.dimensions.height} (clickable: ${area.isClickable})`);
    });

    // ========================================
    // 8. 実装推奨事項
    // ========================================
    console.log('\n💡 8. Chrome Extension実装推奨事項...');

    const recommendations = {
        architecture: {
            manifest: 'Manifest V3',
            permissions: ['tabs', 'activeTab', 'storage'],
            contentScript: {
                matches: ['https://read.amazon.co.jp/*', 'https://read.amazon.com/*'],
                runAt: 'document_idle'
            },
            background: {
                type: 'service_worker',
                purpose: 'chrome.tabs.captureVisibleTab()の実行'
            }
        },

        captureFlow: {
            step1: 'Content Scriptでページ読み込みを待機',
            step2: largestImage ? `画像要素の位置を取得: ${JSON.stringify(largestImage.dimensions)}` : 'コンテナ要素の位置を取得',
            step3: 'Background Scriptにメッセージ送信',
            step4: 'Background Scriptでchrome.tabs.captureVisibleTab()実行',
            step5: 'Canvas APIで必要な領域を切り抜き',
            step6: 'Base64に変換してIndexedDBに保存'
        },

        pageNavigation: {
            method: rightClickAreas.length > 0 ? 'click_right_area' : 'keyboard_arrow',
            target: rightClickAreas[0] || null,
            alternative: 'document.dispatchEvent(new KeyboardEvent("keydown", {key: "ArrowRight"}))',
            waitTime: 1500
        },

        endDetection: {
            primary: pageIndicators.length > 0 ? 'monitor_page_number' : 'compare_screenshots',
            pageIndicator: pageIndicators[0] || null,
            fallback: '連続3回同じスクリーンショットが取得されたら終了'
        },

        storage: {
            library: 'Dexie.js',
            schema: {
                screenshots: '++id, pageNumber, imageData, timestamp'
            },
            clearOnComplete: true
        }
    };

    results.recommendations = recommendations;
    console.log(recommendations);

    // ========================================
    // 9. サマリー
    // ========================================
    console.log('\n' + '='.repeat(60));
    console.log('📊 最終診断結果');
    console.log('='.repeat(60));

    console.log('\n✅ 検出結果:');
    console.log(`  - 表示方式: ${displayMethod}`);
    console.log(`  - 画像要素: ${allImages.length}個 (表示中: ${visibleImages.length}個)`);
    console.log(`  - 大きなコンテナ: ${largeContainers.length}個`);
    console.log(`  - ページ番号表示: ${pageIndicators.length}個`);
    console.log(`  - 右側クリック領域: ${rightClickAreas.length}個`);

    console.log('\n🎯 推奨実装:');
    console.log(`  1. キャプチャ方法: ${captureStrategy?.method || 'unknown'}`);
    console.log(`  2. ページめくり: ${recommendations.pageNavigation.method}`);
    console.log(`  3. 終了検出: ${recommendations.endDetection.primary}`);

    if (largestImage) {
        console.log('\n📐 撮影範囲:');
        console.log(`  x: ${largestImage.dimensions.x}`);
        console.log(`  y: ${largestImage.dimensions.y}`);
        console.log(`  width: ${largestImage.dimensions.width}`);
        console.log(`  height: ${largestImage.dimensions.height}`);
    }

    console.log('\n📋 完全な結果:');
    console.log(results);

    // グローバルに保存
    window.kindleInspectorResults = results;
    console.log('\n💾 window.kindleInspectorResults に保存しました');

    // ダウンロード関数
    window.downloadResults = function () {
        const dataStr = JSON.stringify(results, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'kindle-inspector-v3-results.json';
        link.click();
        URL.revokeObjectURL(url);
        console.log('✅ ダウンロード完了');
    };

    console.log('📥 downloadResults() でJSON出力');

    // ========================================
    // 10. テスト関数
    // ========================================

    window.testPageTurn = function () {
        console.log('🧪 ページめくりテスト...');

        if (rightClickAreas.length > 0) {
            const area = rightClickAreas[0];
            console.log(`  右側領域をクリック: ${area.tag}#${area.id}`);

            // 中央をクリック
            const centerX = area.dimensions.x + area.dimensions.width / 2;
            const centerY = area.dimensions.y + area.dimensions.height / 2;

            const clickEvent = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: centerX,
                clientY: centerY
            });

            area.element.dispatchEvent(clickEvent);
            console.log(`  ✅ クリックイベント送信: (${Math.round(centerX)}, ${Math.round(centerY)})`);
        } else {
            console.log('  矢印キーを使用...');
            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
            console.log('  ✅ ArrowRightキー送信');
        }
    };

    window.highlightCaptureArea = function () {
        console.log('🎨 撮影範囲をハイライト...');

        const target = largestImage || largeContainers[0];
        if (!target) {
            console.log('  ❌ 撮影対象が見つかりません');
            return;
        }

        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.left = target.dimensions.x + 'px';
        overlay.style.top = target.dimensions.y + 'px';
        overlay.style.width = target.dimensions.width + 'px';
        overlay.style.height = target.dimensions.height + 'px';
        overlay.style.border = '3px solid red';
        overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
        overlay.style.zIndex = '999999';
        overlay.style.pointerEvents = 'none';

        document.body.appendChild(overlay);
        console.log('  ✅ 赤い枠で表示（3秒後に消えます）');

        setTimeout(() => {
            overlay.remove();
        }, 3000);
    };

    console.log('\n🧪 テスト関数:');
    console.log('  - testPageTurn() : ページめくりを実行');
    console.log('  - highlightCaptureArea() : 撮影範囲を赤枠で表示');

    return results;

})();
