---
name: ocr-extract
description: "Kindle PDF（画像ベース）をAgent Teams並列OCRでテキスト化する。読書以外にも汎用的に使える"
user_invocable: true
---

# /ocr-extract — PDF並列OCRテキスト化

## 概要

画像ベースのPDF（Kindle スクショ等）を、Haikuサブエージェントの並列処理でテキスト化する。トークンコストはOpus直読みの約1/15。

## 入力パターン

| 入力 | 例 |
|------|---|
| PDFパス | `/ocr-extract C:\Users\takuz\Downloads\本.pdf` |
| PDFパス + ページ範囲 | `/ocr-extract 本.pdf 117-232` |

## コアプロセス

### Step 1: PDF検査

1. PyMuPDF（fitz）でPDFを開く
2. ページ数を取得
3. テキストレイヤーの有無を確認（数ページ `get_text()` してみる）
   - テキストが取れる → 「テキストPDFです。OCR不要かもしれません。続行しますか？」と確認
   - テキストが取れない → 画像PDFと判断、OCR続行
4. **縦書き/横書き判定**: 最初の2-3ページをReadツールで目視確認する
   - 縦書き → サブエージェントへのプロンプトに「縦書き日本語です。右から左、上から下に読んでください」を追加 + dpiを200に上げる
   - 横書き → 通常のプロンプト + dpi=150

### Step 2: 画像化

1. 出力ディレクトリを作成: `library/books/{ベース名}_ocr_tmp/`
2. 指定ページ範囲（デフォルト: 全ページ）をPNGに変換
   - `page.get_pixmap(dpi=150)` で十分な品質
   - ファイル名: `page_XXX.png`（3桁ゼロ埋め）

```python
import fitz
doc = fitz.open(pdf_path)
for i in range(start, end):
    page = doc[i]
    pix = page.get_pixmap(dpi=150)
    pix.save(f'{out_dir}/page_{i+1:03d}.png')
```

### Step 3: バッチ分割

- 20ページ/バッチで分割
- バッチ数を計算: `ceil(total_pages / 20)`

### Step 4: Agent Teams 並列OCR

**6チームメイト以下の場合**: Agent tool で `model: "haiku"` を指定し、`run_in_background: true` で全バッチ同時起動。

**7チームメイト以上の場合**: 6並列 × 複数ウェーブで処理。

各エージェントへのプロンプト:

```
あなたはOCRリーダーです。以下の画像ファイルを順番に読み取り、テキストを正確に抽出してください。

対象ファイル: {out_dir} にある page_{start}.png から page_{end}.png まで

手順:
1. 各PNGファイルをReadツールで読み取る
2. 画像に表示されている日本語テキストを正確に抽出する
3. 全ページのテキストを結合して、以下のファイルに保存する:
   {out_dir}/batch_{n}_p{start}-{end}.txt

出力ルール:
- ページ区切りは「--- page XXX ---」で入れる
- 見出し・箇条書き・図表はマークダウンで再現
- 読み取れない文字は [不明] とする
- 余計な説明は不要。テキスト抽出のみに集中する
```

エージェント設定:
- `model: "haiku"`
- `mode: "bypassPermissions"`
- `run_in_background: true`

### Step 5: 結果確認

1. 全バッチ完了を待つ
2. `batch_*.txt` の存在と空でないことを確認
3. 失敗バッチがあれば再実行

### Step 6: 結果報告

ユーザーに以下を報告:
- 処理ページ数
- バッチ数・並列数
- 合計トークン消費（概算）
- 出力ファイルの場所

## 出力

```
library/books/{ベース名}_ocr_tmp/
├── page_001.png ... page_NNN.png   # 画像（中間生成物）
├── batch_1_p001-020.txt            # バッチ別テキスト
├── batch_2_p021-040.txt
└── ...
```

## ルール

- テキストPDFの場合はOCRせず `get_text()` で抽出するか確認する
- 画像ファイルは中間生成物。ノート完成後に削除を提案する
- OCRの品質は完璧でなくてよい（後段のreading-synthが文脈で補完する）
- 縦書きPDFは精度が落ちる旨をユーザーに伝える

## Gotchas

- PyMuPDF（fitz）が未インストール → `pip install pymupdf` を案内
- 500ページ超のPDFは画像化だけで数分かかる → 先にページ範囲を聞く
- Agent Teams並列はIPCの制約で稀にデッドロックする → タイムアウト（5分）後に未完了バッチを再実行
- Haiku の縦書き日本語OCR精度は横書きより低い → [不明] が多い場合はユーザーに伝える
