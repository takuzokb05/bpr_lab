/**
 * Error Suppressor
 * Kindle Cloud Readerの既知のエラーを抑制してパフォーマンスを改善
 */

(function () {
    'use strict';

    // fonts.json 404エラーを抑制
    const originalFetch = window.fetch;
    window.fetch = function (...args) {
        const url = args[0];

        // fonts.jsonへのリクエストを検出
        if (typeof url === 'string' && url.includes('fonts.json')) {
            console.log('[ErrorSuppressor] fonts.jsonリクエストをブロックしました（Kindle側のバグ回避）');
            // 空のレスポンスを返す
            return Promise.resolve(new Response('{}', {
                status: 200,
                statusText: 'OK',
                headers: { 'Content-Type': 'application/json' }
            }));
        }

        return originalFetch.apply(this, args);
    };

    console.log('[ErrorSuppressor] Kindle fonts.jsonエラー抑制を有効化');
})();
