# ローディングスピナー対策の実装

## 問題

ページ遷移時のローディングアニメーション(くるくる回るスピナー)が表示されている最中にスクリーンショットを撮ってしまう問題がありました。

## 実装した対策

### 1. コンテンツ安定待機機能 (`waitForContentStable`)

**場所**: `src/content/content.js`

ページ遷移後に以下の2段階でコンテンツの安定を確認します:

#### ステップ1: ローディングインジケーター検出
- `LoadingDetector.waitForLoadingComplete()` を使用
- よくあるローディング関連のセレクター(`[class*="spinner"]`, `[class*="loading"]`など)を監視
- Shadow DOM内も再帰的に探索
- 最大2秒間待機

#### ステップ2: 画像比較による安定性確認
- 300msごとに連続でスクリーンショットを撮影
- 前回のキャプチャと比較して同一であることを確認
- 最大5回試行(合計1.5秒)
- 2回連続で同じ画像 = コンテンツが安定したと判断

```javascript
async function waitForContentStable() {
    // 1. ローディングインジケーターが消えるまで待つ
    if (window.LoadingDetector) {
        await window.LoadingDetector.waitForLoadingComplete(2000, 100);
    }
    
    // 2. 連続キャプチャで画像の安定性を確認
    let previousCapture = await captureCurrentPage();
    for (let i = 0; i < 5; i++) {
        await sleep(300);
        const currentCapture = await captureCurrentPage();
        if (currentCapture === previousCapture) {
            return true; // 安定
        }
        previousCapture = currentCapture;
    }
}
```

### 2. ローディング検出ユーティリティ (`loadingDetector.js`)

**場所**: `src/utils/loadingDetector.js`

汎用的なローディング検出機能を提供:

- `isLoading()`: 現在ローディング中かチェック
- `waitForLoadingComplete()`: ローディング完了まで待機

通常のDOMとShadow DOM両方に対応。

### 3. Kindleのfonts.jsonエラー抑制 (`errorSuppressor.js`)

**場所**: `src/utils/errorSuppressor.js`

**問題**: Kindle Cloud Readerが存在しない `fonts.json` を繰り返しリクエストし、大量の404エラーが発生していました。これがパフォーマンスに悪影響を与えていた可能性があります。

**対策**: `fetch` をインターセプトして、`fonts.json` へのリクエストを検出し、空のJSONレスポンスを返すことでエラーを抑制します。

```javascript
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const url = args[0];
    if (typeof url === 'string' && url.includes('fonts.json')) {
        // 空のレスポンスを返してエラーを防ぐ
        return Promise.resolve(new Response('{}', {
            status: 200,
            statusText: 'OK',
            headers: { 'Content-Type': 'application/json' }
        }));
    }
    return originalFetch.apply(this, args);
};
```

### 4. ページ遷移後の待機時間調整

**場所**: `src/content/content.js` の `startCapture()` 関数

- ページ番号が変わった場合: 800ms待機 + `waitForContentStable()`
- ページ番号が変わらなかった場合: 1000ms待機

```javascript
if (pageNumChanged) {
    await window.PageDetector.sleep(800);
    await waitForContentStable(); // 追加の安定確認
} else {
    await window.PageDetector.sleep(1000);
}
```

## 効果

1. **ローディング中のスクリーンショット防止**: スピナーが表示されている状態でのキャプチャを回避
2. **コンテンツの完全な読み込み確認**: 画像比較により、実際にコンテンツが安定したことを確認
3. **パフォーマンス改善**: Kindleのfonts.jsonエラーを抑制し、無駄なリトライを削減
4. **信頼性向上**: より確実に正しいページをキャプチャ

## テスト方法

1. Chrome拡張機能を再読み込み
2. Kindle Cloud Readerで書籍を開く
3. 「📸 新規PDF保存」を開始
4. 開発者ツールのConsoleで以下を確認:
   - `[ErrorSuppressor] fonts.jsonリクエストをブロックしました` が表示される
   - `[LoadingDetector] ローディング完了` が表示される
   - `[KindleScreenshot] コンテンツ安定確認 (X回目で一致)` が表示される
   - fonts.json関連の404エラーが表示されない

## トラブルシューティング

### まだローディング中にキャプチャされる場合

1. `waitForContentStable()` の `maxAttempts` を増やす(現在5回)
2. `checkInterval` を長くする(現在300ms)
3. `LoadingDetector.waitForLoadingComplete()` のタイムアウトを延長(現在2000ms)

### パフォーマンスが遅い場合

1. `waitForContentStable()` の試行回数を減らす
2. 画像比較の代わりに固定待機時間を使用
3. ローディング検出のチェック間隔を長くする

## 関連ファイル

- `src/content/content.js` - メインロジック、`waitForContentStable()` 実装
- `src/utils/loadingDetector.js` - ローディング検出ユーティリティ
- `src/utils/errorSuppressor.js` - Kindleエラー抑制
- `manifest.json` - スクリプト読み込み順序の設定
