# スライド作成ツール 仕様書

## 1. 概要

- **目的**: ドキュメントから AI でスライドを自動生成する CLI ツール
- **対象ユーザー**: 自分用
- **主要な価値**: NotebookLM の15枚制限を超え、背景画像生成・ルールベーステキスト配置・1枚単位リライトが可能

## 2. 技術スタック（Phase A 確定）

| コンポーネント | 技術 | モデルID / バージョン |
|--------------|------|---------------------|
| テキスト処理 | Gemini 3 Flash | `gemini-3-flash-preview` |
| 画像生成 | Nano Banana Pro | `gemini-3-pro-image-preview` |
| 画像生成（フォールバック） | Imagen 4 Fast | `imagen-4.0-fast-generate-001` |
| PPTX生成 | python-pptx | 1.0.2 |
| PDF読み込み | pdfplumber | 最新 |
| SDK | google-genai | 最新 |
| テキスト配置 | ルールベース（AI不要） | — |

## 3. 機能一覧

| ID | 機能名 | 説明 | 優先度 | 依存 |
|----|--------|------|--------|------|
| F1 | CLI基盤 | 引数解析、設定読み込み、Gemini API 接続確認 | Must | - |
| F2 | 資料読み込み | PDF/テキストファイルの読み込みとテキスト抽出 | Must | F1 |
| F3 | スライド構成生成 | Gemini 3 Flash でスライド構成 JSON を生成 | Must | F1, F2 |
| F4 | 背景画像生成 | Nano Banana Pro で各スライドの背景画像を生成 | Must | F1, F3 |
| F5 | テキスト配置 + PPTX出力 | ルールベースでテキスト配置し python-pptx で PPTX を組み立て | Must | F3, F4 |
| F6 | 1枚単位リライト | 特定スライドの再生成（構成・背景を個別に更新） | Should | F5 |

## 4. データ構造

### 入出力

- **入力**: PDF / テキストファイル（ユーザーの資料）
- **出力**: PPTX ファイル（`data/output/` に保存）
- **中間データ**: スライド構成 JSON + 背景画像ファイル（`data/output/{session_id}/` に保存）

### スライド構成 JSON スキーマ

```json
{
  "metadata": {
    "title": "プレゼンテーションタイトル",
    "total_slides": 20,
    "taste": {
      "style": "business",
      "color_tone": "dark",
      "tone": "formal"
    }
  },
  "slides": [
    {
      "slide_number": 1,
      "slide_type": "title",
      "title": "スライドタイトル",
      "subtitle": "サブタイトル（titleスライドのみ）",
      "bullet_points": ["ポイント1", "ポイント2", "ポイント3"],
      "speaker_notes": "発表者用メモ",
      "background_prompt": "Abstract dark blue gradient with subtle geometric patterns, professional, space for text"
    }
  ]
}
```

### スライドタイプ

| タイプ | 用途 | テキスト配置 |
|--------|------|------------|
| `title` | 表紙 | タイトル中央大、サブタイトル中央小 |
| `section` | セクション区切り | タイトル中央大 |
| `content` | 通常コンテンツ | タイトル上部左、箇条書き左 |
| `end` | 最終スライド | タイトル中央大 |

## 5. 外部依存

- **API**: Gemini API（`google-genai` SDK）
  - Gemini 3 Flash: テキスト処理（PDF解析・構成生成）
  - Nano Banana Pro: 画像生成
  - Imagen 4 Fast: 画像生成フォールバック
- **ライブラリ**: google-genai, python-pptx, pdfplumber, python-dotenv
- **環境変数**: `GEMINI_API_KEY`

## 6. 各機能の詳細仕様

### F1: CLI基盤 + config + Gemini API 接続

**入力**:
```bash
# 基本
python cli.py generate <input_file> [--output <output_dir>] [--style <style>] [--color <color>]

# テイスト指定
python cli.py generate report.pdf --style business --color dark

# リライト
python cli.py rewrite <session_dir> --slide 5

# 接続テスト
python cli.py test-connection
```

**処理**:
1. argparse で引数解析
2. `.env` から `GEMINI_API_KEY` を読み込み
3. `genai.Client()` で API 接続確認

**出力**: 設定済みの Client オブジェクト

**エラーケース**:
- `GEMINI_API_KEY` 未設定 → `ValueError` + 日本語エラーメッセージ
- 入力ファイル不存在 → `FileNotFoundError`
- API接続失敗 → タイムアウト30秒 + リトライ3回

**完了基準**: `python cli.py test-connection` が成功、`--help` が正常表示

### F2: 資料読み込み（document_reader）

**入力**: ファイルパス（PDF or テキスト）

**処理**:
1. ファイル拡張子で分岐:
   - `.pdf` → pdfplumber でテキスト抽出（+ Gemini 3 Flash で PDF 直接解析も可能）
   - `.txt`, `.md` → そのまま読み込み
2. テキストを返却

**出力**: 抽出テキスト（str）+ メタ情報（ページ数、ファイルサイズ）

**エラーケース**:
- 非対応ファイル形式 → `ValueError`
- PDF破損 → pdfplumber の例外をキャッチ + 日本語メッセージ
- ファイルサイズ > 50MB → 警告（Gemini API の制限）

**完了基準**: PDF/テキストファイルからテキスト抽出成功、テスト3件以上

### F3: スライド構成生成（slide_planner）

**入力**: 抽出テキスト + テイスト設定（style, color_tone, tone）

**処理**:
1. Gemini 3 Flash に PDF/テキストとテイスト情報を渡す
2. `response_schema` でスライド構成 JSON を強制出力
3. thinking_level は `"low"` を使用（構成生成は高度な推論不要、速度優先）
4. JSON をパース・バリデーション

**出力**: スライド構成 dict（Section 4 のスキーマに準拠）

**プロンプト**:
```
あなたはプレゼンテーション設計の専門家です。
以下の資料を読み、スライド構成を作成してください。

【要件】
- スライド枚数: 資料の内容量に応じて適切に（制限なし）
- 最初のスライドは slide_type: "title"
- 最後のスライドは slide_type: "end"
- セクションの切り替え時は slide_type: "section"
- それ以外は slide_type: "content"
- 各スライドの bullet_points は 3〜5 項目
- background_prompt は英語で、テイスト設定に合わせた抽象的背景画像の説明

【テイスト】
- スタイル: {style}
- 色調: {color_tone}
- トーン: {tone}
```

**エラーケース**:
- JSON パース失敗 → リトライ1回
- API タイムアウト → 指数バックオフ（最大3回）
- レート制限（429） → Retry-After に従う

**完了基準**: テイスト3パターンで構成 JSON を正常生成、スキーマバリデーション通過

### F4: 背景画像生成（image_generator）

**入力**: スライド構成 JSON（各スライドの `background_prompt`）

**処理**:
1. 各スライドの `background_prompt` を Nano Banana Pro に渡す
2. 16:9 アスペクト比、1K 解像度で生成
3. 生成画像を `data/output/{session_id}/images/slide_{n}.png` に保存
4. エラー時は Imagen 4 Fast にフォールバック

**Nano Banana Pro 呼び出し**:
```python
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=background_prompt,
    config=types.GenerateContentConfig(
        response_modalities=["image"],
    )
)
```

**Imagen 4 Fast フォールバック**:
```python
response = client.models.generate_images(
    model='imagen-4.0-fast-generate-001',
    prompt=background_prompt,
    config=types.GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="16:9",
        person_generation="dont_allow",
    )
)
```

**エラーケース**:
- コンテンツフィルターでブロック → プロンプトを簡略化してリトライ
- Nano Banana Pro 失敗 → Imagen 4 Fast にフォールバック
- 全画像生成失敗 → 単色背景で継続（画像なしスライド）

**完了基準**: 5枚以上の背景画像を正常生成・保存

### F5: テキスト配置 + PPTX出力（text_layout + pptx_builder）

**入力**: スライド構成 JSON + 背景画像ファイル群

**処理**:
1. `Presentation()` を作成（16:9: 13.333 × 7.5 インチ）
2. 各スライドについて:
   a. 空白レイアウト（`slide_layouts[6]`）でスライド追加
   b. 背景画像を `add_picture()` でフルサイズ配置 → XML操作で最背面
   c. 半透明オーバーレイ（黒、alpha 40%）を追加
   d. `slide_type` に応じたレイアウトテンプレートでテキスト配置
3. PPTX を `data/output/{session_id}/presentation.pptx` に保存

**レイアウトテンプレート（座標定義）**:

| タイプ | タイトル位置 | コンテンツ位置 |
|--------|------------|--------------|
| `title` | 中央、Y=2.5in、W=10in、FontSize=44pt | サブタイトル: 中央、Y=4in、FontSize=24pt |
| `section` | 中央、Y=3in、W=10in、FontSize=40pt | — |
| `content` | 左上、X=0.8in、Y=0.4in、W=11in、FontSize=32pt | 箇条書き: X=1in、Y=1.5in、W=10in、FontSize=20pt |
| `end` | 中央、Y=3in、W=10in、FontSize=36pt | — |

**フォント**: `"メイリオ"`（Windows標準、日本語対応）
**テキスト色**: 白（ダーク背景想定）、テイストに応じて切替

**エラーケース**:
- 背景画像ファイル不存在 → 単色背景で代替
- PPTX 保存失敗 → ディレクトリ自動作成

**完了基準**: 背景画像付き・テキスト配置済みの PPTX が正常に出力され、PowerPoint で開ける

### F6: 1枚単位リライト

**入力**: セッションディレクトリ + スライド番号

**処理**:
1. セッションの構成 JSON を読み込み
2. 指定スライドの構成を Gemini 3 Flash で再生成
3. 背景画像を Nano Banana Pro で再生成
4. PPTX を再構築（該当スライドのみ差し替え）

**CLI**:
```bash
python cli.py rewrite data/output/session_20260221/ --slide 5
```

**エラーケース**:
- セッションディレクトリ不存在 → `FileNotFoundError`
- スライド番号が範囲外 → `ValueError`

**完了基準**: 指定スライドのみ再生成され、他のスライドは変更なし

## 7. 実装順序

```
F1（CLI基盤）→ F2（資料読み込み）→ F3（構成生成）→ F4（画像生成）→ F5（PPTX出力）→ F6（リライト）
```

各機能は独立してテスト可能な単位で実装する。
