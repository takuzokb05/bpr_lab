# Executive Summary
Web版Kindleの自動スクショ・PDF化ツールをChrome拡張機能として実装する。
最大の特徴は、 IndexedDBを活用したメモリ保護と、ブラウザクラッシュからの復帰を可能にする「レジューム機能」。
ユーザーが撮影範囲を一度指定すれば、あとは全自動でページめくりと保存を実行する。

# Prompt Contract: Kindle Screenshot to PDF Extension

## Goal
- Web版Kindleリーダー（Cloud Reader）の画面から、指定された領域を自動で全ページ撮影し、IndexedDBに一時保存する。
- 全ページの撮影完了後、保存された画像を1枚のPDFに結合してダウンロードする。
- メモリ制限によるクラッシュ対策として、一括処理ではなくページ単位の永続化を行う。

## Rules
- Framework: Chrome Extension Manifest v3
- Storage: IndexedDB (Dexie.js推奨) を使用し、Base64画像をページ番号をキーに保存。
- Recovery: 拡張機能の再読み込み時、IndexedDBに未完了のデータがある場合は「続きから再開」ボタンを表示すること。
- PDF Library: jsPDF (クライアントサイドで完結させること)
- Naming: camelCase
- Security: Content Security Policy (CSP) に準拠。外部サーバーへの画像アップロードは厳禁。

## Implementation Flow
1. **Button Injection**: Kindle Cloud Readerのメニューバー（id="top-nav"等）に「PDF保存を開始」ボタンを注入する。
2. **Range Selection**: ボタン押下後、ユーザーがマウスドラッグで撮影範囲（x, y, width, height）を指定する透過オーバーレイを表示する。
3. **Loop Process**:
    - 指定秒数（Default: 1.5s）待機。
    - Chrome Tab Capture APIで指定領域をキャプチャ。
    - IndexedDBへ画像を保存。
    - DOM操作（Next Page Buttonのクリック）で次ページへ。
    - 最終ページ（Next Page Buttonが非活性またはページ番号不変）まで繰り返す。
4. **Finalize**: IndexedDBから全画像を取得し、jsPDFで結合・ダウンロード。IndexedDBをクリアする。

## UX Specs
- **Target Size**: 注入するボタンサイズは最小44x44pxを確保すること。
- **Status Visibility**: 実行中は画面右上に「撮影中: 12/240ページ」のような進捗インジケータを最前面で表示。
- **Celebration**: 保存完了時、Canvas-confetti等を用いた紙吹雪アニメーションと労いのマイクロコピーを表示。
- **Error Handling**: ページめくりに失敗した場合、3回までリトライし、それでもダメな場合は「手動でページをめくって再試行」のトーストを表示。

## Examples
- Input: { range: {x: 100, y: 50, w: 800, h: 1200}, totalPages: null }
- Expected Output: output.pdf (A4 or Image size based PDF)