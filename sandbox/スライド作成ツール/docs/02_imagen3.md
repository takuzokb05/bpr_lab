# Q2: Imagen の画像生成制約・出力形式・背景プロンプト手法

## 重要な発見: Imagen 3 は廃止済み → Imagen 4 へ移行

> **Imagen 3 は既にシャットダウン済み**。現在利用可能なのは **Imagen 4** ファミリーのみ。
> プロジェクトの PLANS.md / SPEC.md の記述は Imagen 4 に更新が必要。
>
> ソース: [Imagen - Gemini API](https://ai.google.dev/gemini-api/docs/imagen)

## 1. Imagen 4 ファミリー

| モデル | モデルID | 価格/画像 | 用途 |
|--------|---------|----------|------|
| **Imagen 4 Fast** | `imagen-4.0-fast-generate-001` | $0.02 | 高速・大量生成 |
| **Imagen 4 Standard** | `imagen-4.0-generate-001` | $0.04 | バランス型 |
| **Imagen 4 Ultra** | `imagen-4.0-ultra-generate-001` | $0.06 | 高品質 |

> **推奨: Imagen 4 Fast**（$0.02/枚）— スライド背景には十分な品質で最安
>
> ソース: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

## 1b. Nano Banana ファミリー（Gemini ベース画像生成）

| モデル | モデルID | 解像度 | 特徴 |
|--------|---------|--------|------|
| Nano Banana | `gemini-2.5-flash-image` | 1K | 高速、$0.039/画像 |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | **1K〜4K** | **高品質テキスト描画、thinking推論、最大14参照画像** |

> **推奨変更: Nano Banana Pro を採用**（Gemini 3 Pro Image）
> - 4K 出力対応でスライド背景に最適な高解像度
> - テキスト描画の精度が高く、多言語対応
> - thinking モードで複雑な指示にも対応
> - 対応アスペクト比: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, **16:9**, 21:9
> - フォールバック: Imagen 4 Fast（$0.02/枚）
>
> ソース: [Nano Banana Image Generation](https://ai.google.dev/gemini-api/docs/image-generation)、[Nano Banana Pro](https://blog.google/technology/ai/nano-banana-pro/)

## 2. 画像生成の仕様

### アスペクト比

| アスペクト比 | 用途 | スライド向け |
|-------------|------|------------|
| 1:1 | 正方形（デフォルト） | - |
| 4:3 | フルスクリーン | 4:3 スライド用 |
| 3:4 | 縦長 | - |
| **16:9** | **ワイドスクリーン** | **標準スライド用 ← 推奨** |
| 9:16 | 縦長ワイド | - |

### 解像度

- **1K**（デフォルト）: 16:9 の場合おそらく 1920×1080 相当
- **2K**: Standard / Ultra モデルで対応

### 出力形式

- 画像はバイト列として返却される
- `image.show()` で表示、またはバイト列をファイルに保存

### 1リクエストあたりの画像数

- **1〜4枚** を指定可能

### SynthID ウォーターマーク

- 全生成画像に **SynthID**（不可視の電子透かし）が付与される
- 視覚的には影響なし

> ソース: [Imagen - Gemini API](https://ai.google.dev/gemini-api/docs/imagen)

## 3. コンテンツポリシー

### personGeneration パラメータ

| 値 | 動作 |
|----|------|
| `"dont_allow"` | 人物画像をブロック |
| `"allow_adult"` | 大人のみ許可（デフォルト） |
| `"allow_all"` | 全年齢許可（EU/UK/CH/MENA では制限あり） |

- スライド背景用途では `"dont_allow"` が安全

## 4. google-genai SDK でのコード例

### 基本的な画像生成

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_images(
    model='imagen-4.0-fast-generate-001',
    prompt='Abstract dark blue gradient background with subtle geometric patterns, professional business style',
    config=types.GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="16:9",
        person_generation="dont_allow",
    )
)

# 画像の保存
for i, generated_image in enumerate(response.generated_images):
    with open(f"background_{i}.png", "wb") as f:
        f.write(generated_image.image.image_bytes)
```

### スライド背景に適したプロンプト例

```python
# テイスト別のプロンプトテンプレート
prompts = {
    "business_dark": "Abstract dark gradient background with subtle geometric lines, professional corporate style, deep blue and navy tones, minimal, clean, space for text overlay",
    "business_light": "Clean white and light gray abstract background with soft geometric shapes, professional minimalist style, bright and airy, space for text",
    "creative": "Vibrant colorful abstract watercolor background, flowing gradients of purple and teal, artistic and modern, plenty of negative space for text",
    "academic": "Subtle off-white textured paper background with faint grid lines, scholarly and clean, warm neutral tones",
}
```

### 背景画像生成のポイント

1. **「space for text overlay」を必ず含める** — テキストを重ねるスペースを確保
2. **抽象的・パターン系を指定** — 具体的なオブジェクトは避ける
3. **色調をテイストに合わせる** — ダーク背景なら白文字、ライト背景なら黒文字
4. **16:9 アスペクト比を指定** — スライドのデフォルトサイズに合致

## 5. コスト概算

| シナリオ | 枚数 | モデル | コスト |
|----------|------|--------|--------|
| 20枚スライド | 20 | Imagen 4 Fast | **$0.40**（約60円） |
| 20枚スライド | 20 | Imagen 4 Standard | $0.80（約120円） |
| 50枚スライド | 50 | Imagen 4 Fast | $1.00（約150円） |

> **注意**: 無料枠は存在しない。全ての使用が課金対象。ただし Google AI Studio 上では無料テスト可能。
>
> ソース: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)

## 6. 代替手段との比較

| サービス | 価格/画像 | 16:9対応 | API統合 | メリット |
|----------|----------|----------|---------|---------|
| **Imagen 4 Fast** | $0.02 | ○ | Gemini API 一本化 | **最安・API統合が楽** |
| DALL-E 3 | $0.04〜$0.08 | ○ | OpenAI API 別途必要 | 品質高いが高コスト |
| Stable Diffusion | 無料（自前運用） | ○ | セルフホスト必要 | 無料だがインフラ必要 |

**結論**: Gemini API キーを既に持っているため、Imagen 4 Fast が最適。追加のAPIキー不要、コスト最安。

## 7. 情報の信頼性評価

- **一次ソース（公式）**: 3件
  - [Imagen - Gemini API](https://ai.google.dev/gemini-api/docs/imagen)
  - [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
  - [Imagen 4 GA Announcement](https://developers.googleblog.com/announcing-imagen-4-fast-and-imagen-4-family-generally-available-in-the-gemini-api/)
- **二次ソース**: 2件
  - [DataCamp: Imagen 3 Guide](https://www.datacamp.com/tutorial/imagen-3)（旧版情報含む、注意）
  - [LaoZhang: Cheap Gemini Image API](https://blog.laozhang.ai/en/posts/cheap-gemini-image-api)
- **注意**: Imagen 3 → 4 の移行が最近のため、ネット上には Imagen 3 の古い情報が多い。公式ドキュメントを優先すること
