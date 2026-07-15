# Kindle DOM Inspector 使用方法

## 目的
このスクリプトは、Kindle Cloud Readerのページ構造を解析し、Chrome拡張機能の実装に必要な要素を特定するための診断ツールです。

## 使用手順

### 1. Kindle Cloud Readerを開く
1. ブラウザで https://read.amazon.co.jp/ にアクセス
2. 任意の書籍を開く
3. 本文が表示されている状態にする

### 2. スクリプトを実行
1. ブラウザの開発者ツールを開く（F12キー）
2. Consoleタブを選択
3. `kindle-inspector.js` の内容をコピー
4. コンソールに貼り付けて Enter キーを押す

### 3. 結果を確認

スクリプトは以下の情報を自動的に検出します：

#### 📖 ページ情報
- ページ番号の表示エリア
- 現在のページ位置を示す要素

#### 🔄 ナビゲーション
- 次ページボタンの候補
- 前ページボタンの候補
- ボタンの状態（有効/無効）

#### 📄 コンテンツエリア
- 本文が表示されている領域
- 推奨される撮影範囲（座標とサイズ）

#### 🎨 UI要素
- メニューバー
- ツールバー
- ボタン注入に適した場所

#### 🖼️ 特殊要素
- iframe の有無
- Shadow DOM の使用状況
- アクセス制約の確認

### 4. 結果のエクスポート

コンソールに以下のコマンドを入力すると、結果をJSONファイルとしてダウンロードできます：

```javascript
downloadResults()
```

## 出力例

```javascript
{
  "pageInfo": {
    "indicators": [
      {
        "selector": "#kindleReader_pageTurn",
        "text": "12 / 240",
        "ariaLabel": "Page 12 of 240"
      }
    ]
  },
  "navigation": {
    "nextButton": [
      {
        "selector": "#kindleReader_pageTurnAreaRight",
        "disabled": false,
        "clickable": true
      }
    ]
  },
  "content": {
    "recommendedCaptureArea": {
      "x": 100,
      "y": 50,
      "width": 800,
      "height": 1200
    }
  }
}
```

## トラブルシューティング

### エラーが出る場合
- Kindleの本が正しく開いているか確認
- ページが完全に読み込まれるまで待つ
- 別の書籍で試す（書籍によってUIが異なる場合があります）

### 要素が検出されない場合
- Kindleのバージョンが異なる可能性があります
- ブラウザの拡張機能が干渉している可能性があります
- プライベートモードで試してみてください

## 次のステップ

このスクリプトで取得した情報を元に、以下を実装します：

1. **Content Script**: 検出されたボタンやコンテンツエリアにアクセス
2. **Screenshot Logic**: 推奨撮影範囲を使用してキャプチャ
3. **Page Navigation**: 次ページボタンのクリック処理
4. **End Detection**: 最終ページの判定ロジック

## 注意事項

- このスクリプトは診断専用で、実際のスクリーンショット機能は含まれていません
- Kindleのページ構造は予告なく変更される可能性があります
- 取得した情報は拡張機能の実装時に参照してください
