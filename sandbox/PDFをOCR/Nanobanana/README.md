# Gemini 3 Pro Image (Nano Banana Pro) API 実行環境

Google の最新画像生成モデル **Gemini 3 Pro Image** (別名: **Nano Banana Pro**) を使用した画像生成API実行環境です。

## 📋 概要

- **モデル**: `gemini-3-pro-image-preview`
- **リリース日**: 2025年11月20日
- **対応解像度**: 1K, 2K, 4K
- **対応アスペクト比**: 1:1, 3:2, 2:3, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9

## 🚀 セットアップ

### 1. 依存パッケージのインストール

```powershell
cd c:\Users\takuz\プロジェクト\bpr_lab\sandbox\PDFをOCR\Nanobanana
pip install -r requirements.txt
```

### 2. APIキーの確認

同一フォルダに `API_KEY.txt` が存在することを確認してください。
このファイルには Google AI Studio で取得した Gemini API キーが記載されている必要があります。

### 3. 動作確認

```powershell
python config.py
```

利用可能なモデルリストが表示されれば成功です。

## 📁 ファイル構成

```
Nanobanana/
├── config.py              # API設定モジュール
├── image_generator.py     # 画像生成クラス
├── requirements.txt       # 依存パッケージ
├── README.md             # このファイル
├── examples/             # サンプルスクリプト
│   ├── basic_generation.py      # 基本的な画像生成
│   ├── advanced_generation.py   # 高度な設定での生成
│   └── batch_generation.py      # バッチ生成
└── output/               # 生成画像の保存先
```

## 💡 使用方法

### 基本的な使用例

```python
from config import initialize_gemini
from image_generator import ImageGenerator

# API初期化
initialize_gemini()

# ImageGenerator インスタンス作成
generator = ImageGenerator()

# 画像生成
images = generator.generate_image(
    prompt="A beautiful sunset over the ocean",
    aspect_ratio="16:9",
    resolution="2K",
    num_images=1
)
```

### サンプルスクリプトの実行

#### 基本的な画像生成
```powershell
python examples/basic_generation.py
```

#### 高度な設定での画像生成
```powershell
python examples/advanced_generation.py
```

#### バッチ生成
```powershell
python examples/batch_generation.py
```

## 🎨 主要機能

### 1. テキストから画像生成 (Text-to-Image)

```python
images = generator.generate_image(
    prompt="Your creative prompt here",
    aspect_ratio="1:1",      # アスペクト比
    resolution="2K",          # 解像度
    num_images=1,            # 生成枚数
    save=True,               # 自動保存
    filename_prefix="my_image"
)
```

### 2. 画像から画像生成 (Image-to-Image)

```python
images = generator.generate_from_image(
    prompt="Edit this image to add...",
    input_image_path="path/to/input.jpg",
    aspect_ratio="16:9",
    resolution="2K"
)
```

### 3. サポートされている設定

**アスペクト比:**
- `1:1` - 正方形
- `16:9` - ワイドスクリーン (横長)
- `9:16` - 縦長 (スマホ壁紙向け)
- `4:3`, `3:4`, `3:2`, `2:3`, `4:5`, `5:4`

**解像度:**
- `1K` - 標準品質
- `2K` - 高品質 (推奨)
- `4K` - 最高品質

## 🔧 トラブルシューティング

### API_KEY.txt が見つからない

```
FileNotFoundError: API_KEY.txt が見つかりません
```

**解決方法**: 親フォルダ (`PDFをOCR`) に `API_KEY.txt` を配置してください。

### モデルが見つからない

```
Model not found: gemini-3-pro-image-preview
```

**解決方法**: 
1. APIキーが有効か確認
2. `python config.py` でモデルリストを確認
3. 利用可能な画像生成モデルを確認

### 画像が生成されない

**考えられる原因**:
- プロンプトが不適切 (公序良俗に反する内容など)
- APIクォータ超過
- ネットワーク接続の問題

**解決方法**: エラーメッセージを確認し、プロンプトを調整してください。

## 📝 注意事項

- 生成された画像には Google の SynthID 電子透かしが含まれます
- 公人や不適切なコンテンツの生成は制限されています
- API使用には料金が発生する場合があります (Gemini API: $0.03/画像)

## 🔗 参考リンク

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Imagen 3 Release Notes](https://blog.google/technology/ai/google-imagen-3/)

## 📄 ライセンス

このプロジェクトは Google Gemini API の利用規約に従います。
