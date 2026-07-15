# Q1: Gemini API のドキュメント解析能力とプロンプト設計

## 1. モデルラインナップ（2026年2月時点）

### 主要モデル

| モデル | 用途 | 入力（/1M tokens） | 出力（/1M tokens） | 備考 |
|--------|------|-------------------|-------------------|------|
| **Gemini 3 Flash** | Pro級知能 × Flash速度 | 無料枠あり（有料: $0.50） | 無料枠あり（有料: $3.00） | **← 採用: メイン処理用** |
| Gemini 2.5 Flash | 低レイテンシ・大量処理 | 無料枠あり（有料: $0.30） | 無料枠あり（有料: $2.50） | **2026/6/17 廃止予定** |
| Gemini 2.5 Pro | 高度な推論・複雑タスク | $1.25〜$2.50 | $10.00〜$15.00 | コスト過剰 |
| Gemini 2.0 Flash | 旧世代 | 無料枠あり | 無料枠あり | **2026/6/1 廃止予定** |

> **重要**: Gemini 2.0 系は 2026/6/1、Gemini 2.5 Flash は 2026/6/17 に廃止予定（[公式廃止スケジュール](https://ai.google.dev/gemini-api/docs/deprecations)）。**本プロジェクトでは Gemini 3 Flash を採用**する。
>
> Gemini 3 Flash の特徴: 1M トークンコンテキスト、64K 出力、構造化出力+ツール併用対応、thinking レベル設定可能（minimal/low/medium/high）。
> 2.5 Flash 比で同等タスクのトークン消費が30%削減（公式発表）。
>
> ソース: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

### 無料枠のレート制限（概算）

| モデル | RPM | RPD | TPM |
|--------|-----|-----|-----|
| Gemini 2.5 Pro | 5 | 100 | 250,000 |
| Gemini 2.5 Flash | 10 | 250 | 250,000 |
| Gemini 2.5 Flash-Lite | 15 | 1,000 | 250,000 |

> ソース: [Gemini API Free Tier Rate Limits](https://www.aifreeapi.com/en/posts/gemini-api-free-tier-rate-limits)、[Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)

## 2. ドキュメント入力機能

### PDF 処理能力

- **対応**: PDF ファイルの直接処理が可能
- **制限**: 最大 **50MB** または **1,000ページ**
- **トークン消費**: 1ページあたり約 **258 トークン**（画像として処理）
- **重要**: ドキュメントビジョンが本質的に理解できるのは **PDF のみ**。TXT/HTML/XML 等は平文テキストとして抽出されるため、図表・レイアウトは失われる

> ソース: [Document Understanding](https://ai.google.dev/gemini-api/docs/document-processing)

### ファイルアップロード方法

2つの方法がある:

1. **インライン（小さいファイル向け）**: バイト列を直接渡す
2. **File API（大きいファイル向け）**: アップロード → URI取得 → プロンプトに渡す

## 3. google-genai Python SDK

### インストール

```bash
pip install google-genai
```

### 基本的なテキスト生成

```python
from google import genai

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="スライドの構成案を作成してください"
)
print(response.text)
```

### PDF ファイルの解析（インライン）

```python
from google import genai
from google.genai import types
import pathlib

client = genai.Client(api_key="YOUR_API_KEY")
filepath = pathlib.Path('document.pdf')

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        types.Part.from_bytes(
            data=filepath.read_bytes(),
            mime_type='application/pdf',
        ),
        "この資料の内容をスライド構成に変換してください"
    ]
)
print(response.text)
```

### PDF ファイルの解析（File API — 大容量向け）

```python
from google import genai
import pathlib

client = genai.Client(api_key="YOUR_API_KEY")
file_path = pathlib.Path('large_document.pdf')

# アップロード
uploaded_file = client.files.upload(file=file_path)

# 解析
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[uploaded_file, "この資料をスライド構成に変換してください"]
)
print(response.text)
```

> ソース: [Document Understanding](https://ai.google.dev/gemini-api/docs/document-processing)、[Google Gen AI SDK](https://googleapis.github.io/python-genai/)

### 構造化出力（JSON モード）

`response_schema` を指定することで、JSON 形式の構造化出力を強制できる:

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[uploaded_file, "この資料をスライド構成に変換してください"],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema={
            "type": "object",
            "properties": {
                "slides": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "slide_number": {"type": "integer"},
                            "title": {"type": "string"},
                            "bullet_points": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "speaker_notes": {"type": "string"},
                            "background_prompt": {"type": "string"}
                        },
                        "required": ["slide_number", "title", "bullet_points"]
                    }
                }
            }
        }
    )
)
```

> ソース: [Structured Output](https://ai.google.dev/gemini-api/docs/structured-output)（リンク先は Document Understanding ページから参照）

## 4. スライド構成生成のプロンプト設計

### 推奨プロンプト構造

```
あなたはプレゼンテーション設計の専門家です。

以下の資料を読み、プレゼンテーションスライドの構成を作成してください。

【要件】
- スライド枚数: 資料の内容量に応じて適切に（制限なし）
- 各スライドには以下を含める:
  - タイトル（簡潔に）
  - 箇条書き（3〜5項目）
  - スピーカーノート（発表者用メモ）
  - 背景画像のプロンプト（スライド内容に合った抽象的・ビジュアル的な画像の説明）

【テイスト】
- スタイル: {ビジネス / カジュアル / アカデミック}
- 色調: {ダーク / ライト / カラフル}
- トーン: {フォーマル / 親しみやすい}

JSON形式で出力してください。
```

### テイスト制御のポイント

- プロンプト内で「テイスト」セクションを設け、スタイル・色調・トーンを指定
- 背景画像プロンプトにもテイスト情報を反映させる（例: 「ダークトーンの抽象的なビジネス背景」）
- `response_schema` で構造を強制し、出力のばらつきを防ぐ

## 5. コスト概算

### スライド20枚の資料を処理する場合

| 工程 | モデル | トークン数 | コスト（無料枠） | コスト（有料） |
|------|--------|-----------|----------------|--------------|
| PDF解析（30ページ） | 3 Flash | ~8,000 入力 | 無料 | ~$0.002 |
| 構成生成 | 3 Flash | ~3,000 出力 | 無料 | ~$0.008 |
| リライト（1枚） | 3 Flash | ~500 | 無料 | ~$0.001 |

**結論: 無料枠で十分運用可能**（Gemini 3 Flash の無料枠レート制限内）

## 6. 情報の信頼性評価

- **一次ソース（公式）**: 5件
  - [Document Understanding](https://ai.google.dev/gemini-api/docs/document-processing)
  - [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
  - [Models](https://ai.google.dev/gemini-api/docs/models)
  - [Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
  - [Google Gen AI SDK](https://googleapis.github.io/python-genai/)
- **二次ソース**: 2件
  - [aifreeapi.com Rate Limits Guide](https://www.aifreeapi.com/en/posts/gemini-api-free-tier-rate-limits)
  - [Philipp Schmid: PDFs to Insights](https://www.philschmid.de/gemini-pdf-to-data)
- **注意**: レート制限の具体的数値はTier・時期により変動する。Google AI Studio で最新値を確認すべき
