# Q3: python-pptx のレイアウト機能とテキスト配置の自由度

## 1. 基本情報

- **現在のバージョン**: 1.0.2（2024年8月7日リリース）
- **ライセンス**: MIT
- **メンテナンス**: アクティブ（GitHub: [scanny/python-pptx](https://github.com/scanny/python-pptx)）
- **インストール**: `pip install python-pptx`
- **依存**: lxml, Pillow, XlsxWriter

> ソース: [python-pptx Documentation](https://python-pptx.readthedocs.io/en/latest/)

## 2. スライドの基本操作

### プレゼンテーションの作成・保存

```python
from pptx import Presentation

prs = Presentation()
# デフォルトは 10×7.5 インチ（4:3）
prs.save('output.pptx')
```

### スライドサイズの設定（16:9）

```python
from pptx.util import Inches, Emu

prs = Presentation()
# 16:9 = 13.333 × 7.5 インチ
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
```

> ソース: [Presentations API](https://python-pptx.readthedocs.io/en/latest/api/presentation.html)

### スライドの追加

```python
# レイアウト一覧（デフォルトテーマ）
# 0: タイトルスライド
# 1: タイトルとコンテンツ
# 5: タイトルのみ
# 6: 空白

blank_layout = prs.slide_layouts[6]
slide = prs.slides.add_slide(blank_layout)
```

> ソース: [Working with Slides](https://python-pptx.readthedocs.io/en/latest/user/slides.html)

## 3. 背景画像の設定

### 重要な制約

**python-pptx には背景画像を直接設定する API がない。**

`slide.background.fill` は固体色・グラデーション・パターンのみ対応し、画像背景は非サポート。

> ソース: [Issue #496](https://github.com/scanny/python-pptx/issues/496)、[Slide Background Analysis](https://python-pptx.readthedocs.io/en/latest/dev/analysis/sld-background.html)

### ワークアラウンド: フルサイズ画像を最背面に配置

```python
from pptx import Presentation
from pptx.util import Inches, Emu

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白レイアウト

# 画像をスライド全体に配置（位置: 左上 0,0、サイズ: スライド全体）
pic = slide.shapes.add_picture(
    'background.png',
    left=0,
    top=0,
    width=prs.slide_width,
    height=prs.slide_height
)

# 最背面に移動（XMLレベルの操作）
slide.shapes._spTree.remove(pic._element)
slide.shapes._spTree.insert(2, pic._element)  # index 2 = 背景の直後
```

### 半透明オーバーレイの追加（テキスト可読性向上）

```python
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
import copy

# 半透明の矩形を追加
overlay = slide.shapes.add_shape(
    1,  # MSO_SHAPE.RECTANGLE
    left=0,
    top=0,
    width=prs.slide_width,
    height=prs.slide_height
)
overlay.fill.solid()
overlay.fill.fore_color.rgb = RGBColor(0, 0, 0)  # 黒

# 透明度の設定（XMLレベル）
# alpha = 40000 → 40% 不透明（60% 透明）
solidFill = overlay.fill._fill
srgbClr = solidFill.find(qn('a:srgbClr'))
if srgbClr is not None:
    alpha = srgbClr.makeelement(qn('a:alpha'), {'val': '40000'})
    srgbClr.append(alpha)

overlay.line.fill.background()  # 枠線を消す
```

> **注意**: 半透明の設定は python-pptx の公式 API では直接サポートされていない。XML レベルの操作が必要。

## 4. テキスト配置の自由度

### テキストボックスの作成（自由配置）

```python
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

txBox = slide.shapes.add_textbox(
    left=Inches(1),
    top=Inches(1),
    width=Inches(10),
    height=Inches(1.5)
)
tf = txBox.text_frame
tf.word_wrap = True  # テキスト折り返し

p = tf.paragraphs[0]
p.text = "スライドタイトル"
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = RGBColor(255, 255, 255)  # 白
p.alignment = PP_ALIGN.LEFT
```

### フォント設定の自由度

| 設定項目 | API | 例 |
|----------|-----|-----|
| フォント名 | `p.font.name` | `"メイリオ"` |
| サイズ | `p.font.size` | `Pt(24)` |
| 太字 | `p.font.bold` | `True` |
| イタリック | `p.font.italic` | `True` |
| 色 | `p.font.color.rgb` | `RGBColor(255,255,255)` |
| 下線 | `p.font.underline` | `True` |

### テキスト配置

| 配置 | 定数 |
|------|------|
| 左揃え | `PP_ALIGN.LEFT` |
| 中央揃え | `PP_ALIGN.CENTER` |
| 右揃え | `PP_ALIGN.RIGHT` |
| 両端揃え | `PP_ALIGN.JUSTIFY` |

### 行間・段落間隔

```python
from pptx.util import Pt

p = tf.paragraphs[0]
p.space_before = Pt(6)   # 段落前の間隔
p.space_after = Pt(6)    # 段落後の間隔
p.line_spacing = Pt(24)  # 行間（固定値）
# または
p.line_spacing = 1.5     # 行間（倍率）
```

### 箇条書き（ビュレット）

```python
from pptx.util import Inches, Pt

tf = txBox.text_frame
tf.word_wrap = True

# 1行目
p = tf.paragraphs[0]
p.text = "最初のポイント"
p.level = 0  # インデントレベル

# 2行目以降は add_paragraph
p2 = tf.add_paragraph()
p2.text = "2つ目のポイント"
p2.level = 0

p3 = tf.add_paragraph()
p3.text = "サブポイント"
p3.level = 1  # インデント
```

> ソース: [Getting Started](https://python-pptx.readthedocs.io/en/latest/user/quickstart.html)、[Working with Placeholders](https://python-pptx.readthedocs.io/en/latest/user/placeholders-using.html)

## 5. 図形・要素の操作

### 図形の追加

```python
from pptx.enum.shapes import MSO_SHAPE

shape = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE,
    left=Inches(1),
    top=Inches(2),
    width=Inches(4),
    height=Inches(2)
)
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(0, 120, 215)
```

### z-order（重なり順序）の制御

python-pptx の公式 API には z-order 変更メソッドがない。XML レベルで `_spTree` 内の要素順序を操作する必要がある（前述の背景画像の例を参照）。

## 6. テンプレート活用

```python
# 既存テンプレートの読み込み
prs = Presentation('template.pptx')

# テンプレートのレイアウトを使用
layout = prs.slide_layouts[0]
slide = prs.slides.add_slide(layout)
```

テンプレートからスライドマスターのフォント・色・レイアウトを継承可能。

## 7. 制限事項・注意点

### できないこと

| 機能 | 対応状況 |
|------|---------|
| アニメーション | ✕ 非サポート |
| トランジション（画面遷移） | ✕ 非サポート |
| 背景画像（API レベル） | ✕ ワークアラウンド必要 |
| 半透明（API レベル） | ✕ XML 操作必要 |
| 影・グロー効果 | △ XML 操作で可能だが複雑 |
| 動画埋め込み | ✕ 非サポート |
| グラフ（高度なもの） | △ 基本的なグラフのみ |

### 日本語フォントの注意

- フォント名は **正確に指定**（例: `"メイリオ"`, `"游ゴシック"`, `"Noto Sans JP"`）
- python-pptx は **フォントを埋め込まない**。閲覧環境にフォントがインストールされていない場合、代替フォントで表示される
- 安全な選択: `"メイリオ"`（Windows標準）、`"游ゴシック"`（Windows/Mac共通）

### ファイルサイズの注意

- 背景画像を全スライドに入れるとファイルサイズが大きくなる
- **推奨**: 画像は事前に適切なサイズに圧縮する（1920×1080, JPEG 品質80%程度）

## 8. 本プロジェクトでの実装方針（提案）

```
1. 空白レイアウト (slide_layouts[6]) をベースにする
2. 背景画像: add_picture() でフルサイズ配置 → XML操作で最背面
3. 半透明オーバーレイ: add_shape() + XML alpha 設定
4. テキスト: add_textbox() で自由配置
5. 16:9 (13.333 × 7.5 インチ) 固定
```

この方針であれば、python-pptx の制約内で高品質なスライドが生成可能。

## 9. 情報の信頼性評価

- **一次ソース（公式）**: 5件
  - [python-pptx Documentation](https://python-pptx.readthedocs.io/en/latest/)
  - [Getting Started](https://python-pptx.readthedocs.io/en/latest/user/quickstart.html)
  - [Slide Background Analysis](https://python-pptx.readthedocs.io/en/latest/dev/analysis/sld-background.html)
  - [Issue #496](https://github.com/scanny/python-pptx/issues/496)
  - [Issue #366](https://github.com/scanny/python-pptx/issues/366)
- **二次ソース**: 2件
  - [SlideModel: Create Presentation in Python](https://slidemodel.com/how-to-create-presentation-in-python/)
  - [CodeFriends: Images on Slide](https://www.codefriends.net/courses/automation-intro-basics/chapter-2/python-pptx-images)
- **注意**: 半透明オーバーレイや z-order 操作は非公式のワークアラウンド。python-pptx のバージョンアップで動作が変わる可能性あり
