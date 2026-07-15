"""
Prompt templates for OCR processing with Gemini API
"""

# Layer 1: Static Context - Editor role and formatting rules
CONTEXT_LAYER = """あなたはシニア校正エディターです。PDFページの画像からテキストを抽出し、構造化されたMarkdownとして出力してください。

## 構造化ルール:
- 数式は LaTeX 形式で記述してください（例: $E = mc^2$, $$\\int_0^\\infty e^{-x} dx$$）
- 脚注は [^1] 形式で記述してください
- 図表は以下の形式で記述してください:
  > [図X: 説明文]
  > [表X: 説明文]
- 見出しは適切な階層（#, ##, ###）で記述してください
- 箇条書きは - または 1. 2. 3. の形式で記述してください
- 文脈に合わせた自然な日本語校正を抽出と同時に実行してください

## 品質基準:
- OCRエラーを修正し、読みやすい日本語に校正してください
- 元のレイアウトと論理構造を維持してください
- 段落の区切りを適切に保ってください
"""

# Layer 2: Dynamic Task Template
TASK_LAYER_TEMPLATE = """
## 処理対象:
- ページ範囲: {start_page}ページ目から{end_page}ページ目まで
- 出力対象: {output_start}ページ目から{output_end}ページ目まで

## 継続性情報:
{continuity_info}

## 指示:
提供された画像から、ページ{output_start}から{output_end}までの内容をMarkdown形式で出力してください。
前後のページは文脈理解のために提供されていますが、出力には含めないでください。
"""

# Layer 3: Few-Shot Examples
FEW_SHOT_EXAMPLES = """
## 出力例:

### 例1: テキストと数式
```markdown
# 第1章 微分積分の基礎

微分の定義は以下の通りです:

$$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$

この式は、関数 $f(x)$ の点 $x$ における変化率を表しています[^1]。

[^1]: ニュートンとライプニッツによって独立に発見されました。
```

### 例2: 図表を含む場合
```markdown
## 実験結果

以下の図は、温度と反応速度の関係を示しています。

> [図3.1: 温度と反応速度の関係グラフ]

実験データを表にまとめると以下のようになります:

> [表3.1: 実験データ一覧]
> | 温度(℃) | 反応速度(mol/s) |
> | --- | --- |
> | 20 | 0.05 |
> | 40 | 0.12 |
> | 60 | 0.28 |
```

### 例3: 箇条書き
```markdown
## 注意事項

実験を行う際は、以下の点に注意してください:

- 保護メガネを着用すること
- 換気を十分に行うこと
- 薬品の取り扱いは慎重に行うこと
```
"""

def build_prompt(start_page: int, end_page: int, output_start: int, output_end: int, 
                 last_tail_text: str = "", current_chapter: str = "") -> str:
    """
    Build complete 3-layer prompt for OCR processing
    
    Args:
        start_page: First page in the input range (including overlap)
        end_page: Last page in the input range (including overlap)
        output_start: First page to output
        output_end: Last page to output
        last_tail_text: Last 3 lines from previous batch for continuity
        current_chapter: Current chapter name for context
    
    Returns:
        Complete prompt string
    """
    # Build continuity information
    continuity_parts = []
    if last_tail_text:
        continuity_parts.append(f"前回の末尾は以下の通りです:\n```\n{last_tail_text}\n```\nこれに自然に続くように記述してください。")
    if current_chapter:
        continuity_parts.append(f"現在の章: {current_chapter}")
    
    continuity_info = "\n".join(continuity_parts) if continuity_parts else "これは文書の最初の部分です。"
    
    # Combine all layers
    task_layer = TASK_LAYER_TEMPLATE.format(
        start_page=start_page,
        end_page=end_page,
        output_start=output_start,
        output_end=output_end,
        continuity_info=continuity_info
    )
    
    return f"{CONTEXT_LAYER}\n{task_layer}\n{FEW_SHOT_EXAMPLES}"


def extract_chapter_from_text(text: str) -> str:
    """
    Extract chapter name from text using pattern matching
    
    Args:
        text: Markdown text to search
    
    Returns:
        Chapter name if found, empty string otherwise
    """
    import re
    
    # Pattern for Japanese chapter headings
    patterns = [
        r'^#\s+第?([0-9一二三四五六七八九十百]+)[章編部][\s:：]*(.*?)$',
        r'^#\s+(Chapter|CHAPTER)\s+(\d+)[\s:：]*(.*?)$',
    ]
    
    for line in text.split('\n'):
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                return line.strip().lstrip('#').strip()
    
    return ""


def extract_last_lines(text: str, num_lines: int = 3) -> str:
    """
    Extract last N non-empty lines from text
    
    Args:
        text: Text to extract from
        num_lines: Number of lines to extract (default: 3)
    
    Returns:
        Last N lines joined with newlines
    """
    lines = [line for line in text.split('\n') if line.strip()]
    return '\n'.join(lines[-num_lines:]) if lines else ""
