---
name: reading
description: "本のタイトルやKindle PDFが入力されたとき、読書の知見をユーザーの文脈に落とし込んだ実践ガイドを生成し、books/に蓄積する"
user_invocable: true
---

# /reading — 読書コンパニオン（オーケストレーター）

## 概要

本のタイトル（またはKindle PDF）を入力すると、ユーザーの文脈に落とし込んだ読書ノートを生成する。内部で `/ocr-extract` と `/reading-synth` を呼び分ける。

## 入力パターン

| 入力 | 例 |
|------|---|
| 書籍タイトル | `/reading チームが機能するとはどういうことか` |
| Kindle PDF | `/reading C:\Users\takuz\Downloads\{書名}.pdf` |
| タイトル + 動機 | `/reading 組織論を学びたくて『学習する組織』を読む` |

## ルーティングロジック

```
入力にPDFパスが含まれる？
├── YES → PDFは画像ベース？
│   ├── YES → /ocr-extract → /reading-synth
│   └── NO（テキストPDF）→ テキスト直接抽出 → /reading-synth
└── NO（タイトルのみ）→ /reading-synth（WebSearchで情報収集）
```

### フロー1: Kindle PDF入力（メイン想定）

1. **ヒアリング**: 動機・知りたいこと・読み方スタイルを聞く（入力に含まれていれば省略）
2. **`/ocr-extract`**: PDF → Haiku並列OCR → テキストファイル群
3. **`/reading-synth`**: テキスト + alter-ego.md → 読書ノート生成（Opus）

### フロー2: タイトルのみ入力

1. **ヒアリング**: 同上
2. **`/reading-synth`**: WebSearchで情報収集 + alter-ego.md → 読書ノート生成

## ルール

- PDFが渡されたら必ず `/ocr-extract` を先に実行する（Opusで直読みしない）
- ヒアリング結果は `/reading-synth` にそのまま引き渡す
- 各サブスキルのルール・Gotchasはそれぞれの SKILL.md に従う

## Gotchas

- PyMuPDF未インストール時は `/ocr-extract` が失敗する → `pip install pymupdf` を案内
- PDFが500ページ超 → ヒアリング時にページ範囲を聞く（「全部読みますか？重要な章だけにしますか？」）
- 既存の読書ノートがある場合 → `/reading-synth` が追記モードで動作する
