# Kindle Screenshot to PDF Extension

Kindle Cloud Readerの全ページを自動撮影してPDF化するChrome拡張機能

## 特徴

- 📸 **全自動撮影** - ページめくりから保存まで完全自動化
- 💾 **IndexedDB永続化** - メモリクラッシュ対策
- 🔄 **レジューム機能** - 中断しても続きから再開可能
- 🎯 **複数ページジャンプ対策** - 1回のクリックで複数ページ進む場合も自動補正
- ⏳ **ローディング完了待機** - ページ遷移アニメーション中のスクリーンショットを防止
- 🎨 **リッチなUX** - 進捗表示、サムネイルスタック、完了時の紙吹雪
- 🌑 **Shadow DOM対応** - Kindleの複雑なDOM構造に完全対応

## インストール

### 1. 依存関係のインストール

```bash
npm install
```

### 2. ライブラリのビルド

```bash
npm run build
```

これにより、`node_modules`から必要なライブラリが`lib/`ディレクトリにコピーされます。

### 3. Chrome拡張機能として読み込み

1. Chromeで `chrome://extensions/` を開く
2. 右上の「デベロッパーモード」をONにする
3. 「パッケージ化されていない拡張機能を読み込む」をクリック
4. このディレクトリを選択

## 使い方

### 1. 撮影開始

1. Kindle Cloud Reader (https://read.amazon.co.jp/) で書籍を開く
2. 画面右上に表示される「📸 PDF保存を開始」ボタンをクリック
3. マウスドラッグで撮影範囲を指定（Kindleのページ表示エリアを選択）

### 2. 自動撮影

- 自動的に全ページが撮影されます
- 右上に進捗が表示されます
- 一時停止・キャンセルも可能

### 3. PDF生成

- 最終ページまで撮影完了後、自動的にPDF生成
- 「📥 PDFをダウンロード」ボタンでダウンロード

### 4. 中断・再開

- キャンセルした場合、次回アクセス時に「▶️ 続きから再開」ボタンが表示されます
- 撮影済みのページはスキップされます

## 技術仕様

### アーキテクチャ

```
manifest.json          # Chrome Extension設定
├── src/
│   ├── content/
│   │   └── content.js     # メインロジック
│   ├── background/
│   │   └── background.js  # スクリーンショット撮影
│   ├── storage/
│   │   └── db.js          # IndexedDB管理
│   ├── ui/
│   │   ├── overlay.js     # UI表示
│   │   └── overlay.css    # スタイル
│   └── utils/
│       ├── shadowDomHelper.js  # Shadow DOM探索
│       ├── pageDetector.js     # ページ番号検出
│       ├── pageNavigator.js    # ページめくり
│       └── loadingDetector.js  # ローディング検出
└── lib/
    ├── dexie.min.js       # IndexedDB
    ├── jspdf.min.js       # PDF生成
    └── canvas-confetti.min.js  # 紙吹雪エフェクト
```

### 主要機能

#### 複数ページジャンプ対策

一部の書籍では、1回のページ送りで複数ページ進むことがあります。
この拡張機能は自動的に検出し、目標ページまで戻ります：

```javascript
// pageNavigator.js
async function safeGoToNextPage(currentPage, waitTime = 1500) {
  // ページ送り実行
  await goToNextPage();
  
  // ページ番号をチェック
  const newPage = getCurrentPageNumber();
  
  // 複数ページジャンプを検出
  if (newPage - currentPage > 1) {
    // 目標ページまで戻る
    await handlePageJump(currentPage + 1, newPage);
  }
}
```

#### Shadow DOM対応

KindleはShadow DOMを使用しているため、通常の`querySelector`では要素を取得できません。
`shadowDomHelper.js`が再帰的に探索します：

```javascript
function* traverseDOM(root = document.body, maxDepth = 10) {
  for (const element of root.querySelectorAll('*')) {
    yield element;
    if (element.shadowRoot) {
      yield* traverseDOM(element.shadowRoot, maxDepth - 1);
    }
  }
}
```

#### ローディング完了待機

ページ遷移時のアニメーション中にスクリーンショットを撮ってしまう問題を防ぐため、
複数の方法でコンテンツの安定を確認します:

```javascript
// loadingDetector.js + content.js
async function waitForContentStable() {
  // 1. ローディングインジケーターが消えるまで待つ
  await LoadingDetector.waitForLoadingComplete(2000);
  
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

## トラブルシューティング

### ページ番号が取得できない

- Kindleの本が完全に読み込まれるまで待ってください
- 別の書籍で試してください

### 撮影範囲がずれる

- ブラウザのズーム倍率を100%にしてください
- 範囲選択時、Kindleのページ表示エリアを正確に選択してください

### PDFが生成されない

- ブラウザのストレージ容量を確認してください
- 開発者ツールのConsoleでエラーを確認してください

## 開発

### デバッグ

1. `chrome://extensions/` で拡張機能の「詳細」をクリック
2. 「バックグラウンドページを検証」でBackground Scriptのログを確認
3. Kindleページで右クリック→「検証」でContent Scriptのログを確認

### データベースのクリア

開発者ツールのConsoleで：

```javascript
window.DB.clearDatabase()
```

## ライセンス

MIT

## 作者

Created with ❤️ for Kindle lovers
