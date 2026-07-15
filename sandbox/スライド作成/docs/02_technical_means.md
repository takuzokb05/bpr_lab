# Q2: Claude の PPTX 生成技術と制約

## 主要な発見

### 1. python-pptx（Python ライブラリ）

- **要点**: Python で PPTX を読み書きする最も成熟したライブラリ。テンプレートの読み込み・既存ファイル編集・新規作成の全てに対応する。API が PowerPoint の UI 構造を忠実に反映しており、学習コストが低い
- **バージョン**: 1.0.0（安定版）
- **主要機能**:
  - **スライドマスター / レイアウト操作**: テンプレートのスライドマスターを通じてフォント・背景・プレースホルダーを継承。レイアウトごとにカスタマイズ可能。プレースホルダーは `idx` 値でアクセスし、位置・サイズ・書式が親から継承される
  - **テキスト操作**: Run 単位でフォント（書体・サイズ・色・太字・斜体・下線）を制御。段落レベルでアラインメント・インデント・箇条書き設定。テキストフレームで縦位置・マージン・自動フィット制御
  - **テーブル**: `add_table()` またはプレースホルダー経由で作成。セル結合（`cell.merge()`）対応。ただしセルにはテキストのみ格納可能（画像・図形・入れ子テーブルは不可）。セル罫線・行高・列幅の API は未整備
  - **チャート**: 棒グラフ、折れ線、円、散布図、バブル、ドーナツ、レーダー、面グラフに対応。データラベル・凡例・軸カスタマイズ可能。**3D チャートは非対応。マルチプロットチャートの新規作成は不可**（既存の読み取りは可）
  - **図形**: オートシェイプ、フリーフォーム描画（線分の連続で構成）対応
  - **画像**: PNG/JPG/EMF 挿入対応。**SVG は非対応**（PIL 依存の制約）
  - **SmartArt**: **非対応**（Issue #83 で要望あり、未実装）
- **制約まとめ**:
  - SVG 画像挿入不可
  - SmartArt 操作不可
  - 3D チャート作成不可
  - マルチプロットチャート新規作成不可
  - テーブルセル罫線の詳細スタイリング API が未整備
  - テーブルセルにはテキストのみ（画像不可）
- **ソース**:
  - [python-pptx 公式ドキュメント - Slides](https://python-pptx.readthedocs.io/en/latest/user/slides.html)
  - [python-pptx 公式ドキュメント - Charts](https://python-pptx.readthedocs.io/en/latest/user/charts.html)
  - [python-pptx 公式ドキュメント - Placeholders](https://python-pptx.readthedocs.io/en/latest/user/placeholders-using.html)
  - [python-pptx 公式ドキュメント - Tables](https://python-pptx.readthedocs.io/en/latest/user/table.html)
  - [python-pptx 公式ドキュメント - Text](https://python-pptx.readthedocs.io/en/latest/user/text.html)
  - [python-pptx GitHub - SmartArt Issue #83](https://github.com/scanny/python-pptx/issues/83)
  - [python-pptx GitHub - SVG Issue #394](https://github.com/scanny/python-pptx/issues/394)

### 2. PptxGenJS（Node.js ライブラリ）

- **要点**: JavaScript/Node.js で PPTX を**新規作成**する主要ライブラリ。Anthropic 公式 PPTX スキルが採用している生成エンジン。ブラウザ・Node.js 双方で動作し、テキスト・テーブル・図形・画像・チャートの全主要オブジェクトに対応
- **主要機能**:
  - テキスト、テーブル、図形、画像、チャートの全スライドオブジェクトを生成可能
  - カスタムスライドマスター定義（一貫したブランディング）
  - ブラウザ・Node.js・React・Electron 等のマルチ環境対応
- **重大な制約**: **既存 .pptx ファイルの読み込み・編集が不可能**。座標・サイズを全てコードで指定する必要がある
- **Anthropic 公式採用**: Anthropic の Agent Skills（`skills/pptx/SKILL.md`）はスクラッチからの PPTX 生成に PptxGenJS を使用。テンプレート編集には別途 XML 直接操作を使用
- **ソース**:
  - [PptxGenJS GitHub](https://github.com/gitbrent/PptxGenJS)
  - [PptxGenJS 公式サイト](https://gitbrent.github.io/PptxGenJS/)
  - [Anthropic Skills - PPTX SKILL.md](https://github.com/anthropics/skills/blob/main/skills/pptx/SKILL.md)

### 3. Marp（Markdown → スライド変換）

- **要点**: Markdown で記述し、HTML/PDF/PPTX に変換するエコシステム。VS Code 拡張・CLI 両方で利用可能。テーマは CSS でカスタマイズ可能
- **出力形式**: HTML, PDF, PPTX, PNG, JPEG, TXT
- **テーマ**: 3つの組み込みテーマ（default, gaia, uncover）。カスタム CSS テーマ作成可能。`--theme` オプションまたは VS Code 設定で切り替え
- **PPTX 出力の実態**:
  - **通常 PPTX**: スライドが**事前レンダリング画像**として埋め込まれる。テキスト編集不可。表示品質はほぼ 100% 再現
  - **編集可能 PPTX（実験的）**: `--pptx-editable` オプションで有効化。ただし **再現性が大幅に低下**。複雑なスタイルではエラーや不完全な出力が発生。発表者ノート非対応。Marp 公式は「外観維持が重要な場合は推奨しない」と明記
  - 編集可能 PPTX には LibreOffice Impress + 互換ブラウザのインストールが必要
- **制約まとめ**:
  - 通常 PPTX は画像ベースのためテキスト編集不可（コンサルスライドの要件「編集可能性」を満たさない）
  - 編集可能 PPTX は実験的で品質が不安定
  - チャート・テーブル・SmartArt 等の PowerPoint ネイティブオブジェクトは生成不可
- **ソース**:
  - [Marp 公式サイト](https://marp.app/)
  - [Marp CLI GitHub](https://github.com/marp-team/marp-cli)
  - [Marp PPTX 編集不可の FAQ](https://github.com/orgs/marp-team/discussions/82)
  - [Marp CLI PPTX editable Issue #298](https://github.com/marp-team/marp-cli/issues/298)

### 4. reveal.js（HTML ベースのスライド生成）

- **要点**: HTML/CSS/JavaScript でスライドを構築するプレゼンテーションフレームワーク。プログラマティックな生成に適しているが、PPTX 出力はネイティブ非対応
- **出力形式**: HTML（ブラウザ表示）、PDF（Chrome 印刷経由）
- **PPTX エクスポート**: **ネイティブ非対応**。PDF → LibreOffice 変換のワークアラウンドのみ
- **PDF 生成**: Chrome/Chromium の印刷機能、または DeckTape CLI ツールで変換
- **LLM との親和性**: LLM 比較研究（Nicolas Brosse, 2025）によると、Quarto/reveal.js は LLM のテキスト生成能力と高い親和性を示し、「コードファースト」フォーマットとして推奨。LLM が直接 Markdown/HTML を生成できるため、API 呼び出しの複雑さを回避
- **制約まとめ**:
  - PPTX 直接出力不可（クライアントが PPTX を要求する場合に致命的）
  - PowerPoint ネイティブオブジェクト（チャート・テーブル等）を生成不可
  - PDF 変換は Chrome 依存
- **ソース**:
  - [reveal.js 公式サイト](https://revealjs.com/)
  - [reveal.js PDF Export](https://revealjs.com/pdf-export/)
  - [reveal.js GitHub - PPTX Export Issue #1702](https://github.com/hakimel/reveal.js/issues/1702)
  - [LLM Slides Format Comparison (Nicolas Brosse)](https://nbrosse.github.io/posts/llm-slides/llm-slides.html)

### 5. Office Open XML（OOXML）直接生成

- **要点**: PPTX は ZIP 圧縮された XML ファイル群（OOXML 規格）。理論上は XML を直接生成すれば完全な制御が可能だが、仕様書が数千ページに及び実用的ではない
- **構造**: `_rels/` （関係定義）、`ppt/presentation.xml`（メイン）、`ppt/slides/slideN.xml`（各スライド）、`ppt/slideMasters/`（マスター）、`ppt/slideLayouts/`（レイアウト）で構成
- **Anthropic 公式スキルの活用**: テンプレート**編集**時に限り XML 直接操作を使用。`unpack.py` で ZIP を展開 → XML を編集 → 再パック。新規作成には使用しない
- **Python ライブラリ**: python-opc（低レベル OPC 操作）、lxml（XML 解析）等があるが、いずれも高レベル抽象化は不十分
- **制約まとめ**:
  - OOXML 仕様が膨大（数千ページ）で、直接記述は非現実的
  - LLM に XML を直接生成させるアプローチは「非効率的で現在の LLM 能力を見落としている」と評価される
  - テンプレート編集の補助的手段としては有効
- **ソース**:
  - [OOXML PPTX 構造解説](http://www.officeopenxml.com/anatomyofOOXML-pptx.php)
  - [PPTX ファイルの構造解析 (SlideModel)](https://slidemodel.com/anatomy-of-a-pptx-file/)
  - [Microsoft Learn - PresentationML 構造](https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document)

### 6. Anthropic 公式 Agent Skills（PPTX スキル）

- **要点**: Anthropic が公式に提供する PPTX 生成スキル。Claude.ai（Pro/Max/Team/Enterprise）で利用可能。Claude Code でもスキルとして読み込み可能
- **アーキテクチャ**（2つのワークフロー）:
  - **新規作成**: PptxGenJS（Node.js）でスライドをプログラム生成
  - **テンプレート編集**: XML 直接操作（unpack → 編集 → pack）
  - **テキスト抽出**: markitdown ライブラリ
  - **品質検証**: LibreOffice で PDF 変換 → Poppler で画像化 → 視覚検査
- **設計ガイドライン**（SKILL.md 記載）:
  - カラーパレット: 10 種類のキュレーション済みパレット
  - タイポグラフィ: 8 種類のフォントペアリング推奨
  - レイアウト: 2カラム、アイコン+テキスト行、グリッド等
  - 「タイトル下のアクセントライン禁止」（AI 生成スライドの特徴的ハルマーク）
- **品質保証プロセス**: 生成 → PDF 変換 → 画像化 → 視覚検査 → 修正 → 再検証のループを**最低1回**実施
- **制約**:
  - ファイルサイズ上限 30MB
  - レイアウト忠実度 100% は保証されない（人間のデザインレビュー必須）
  - テンプレート再現時の色味・配置ずれが発生しやすい
  - コンテキスト長の制約（トークン上限）でスライド数に実質的制限
  - 実用的には数十〜100 枚程度まで
- **ソース**:
  - [Anthropic Skills GitHub](https://github.com/anthropics/skills)
  - [Anthropic Skills - PPTX SKILL.md](https://github.com/anthropics/skills/blob/main/skills/pptx/SKILL.md)
  - [Anthropic Agent Skills ドキュメント](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
  - [Claude PPTX スキル実践ガイド (SmartScope)](https://smartscope.blog/en/generative-ai/claude/claude-pptx-skill-practical-guide/)

### 7. Claude の根本的制約

- **要点**: Claude はテキスト生成が主能力。コード（Python/JavaScript）を生成・実行する形でのみ PPTX を生成できる。画像生成は限定的（テキストベースの図形・チャートは可能だが、写真やイラストの生成はできない）
- **具体的制約**:
  - **直接的なバイナリ出力不可**: PPTX ファイルを直接生成することはできない。必ずコード生成 → コード実行のパイプラインが必要
  - **画像素材の限界**: 写真・イラスト・アイコン等の画像素材は外部から提供する必要がある。Claude が生成できるのはコードで描画可能な図形・チャートのみ
  - **レイアウト精度**: ピクセル単位のレイアウト調整はコード上の数値指定に依存。視覚的フィードバックなしでの座標指定は試行錯誤が必要
  - **コンテキスト長制約**: 長大なスライドデッキの全内容を一度にコンテキストに収めることが難しい
  - **テンプレート解析の難しさ**: 既存テンプレートの構造解析は可能だが、色味・配置の完全再現は困難
- **ソース**:
  - [Claude ファイル作成・編集ドキュメント](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)
  - [Claude in PowerPoint](https://support.claude.com/en/articles/13521390-use-claude-in-powerpoint)

---

## LLM スライド生成における手段の比較

Nicolas Brosse (2025) の実証研究を基に、Gemini Pro 2.5 での実測結果を含めた比較。

| 評価軸 | python-pptx | PptxGenJS | Marp | reveal.js / Quarto | OOXML 直接 |
|--------|-------------|-----------|------|-------------------|-----------|
| **PPTX 出力** | ネイティブ | ネイティブ | 対応（画像/実験的） | 非対応 | ネイティブ（理論上） |
| **既存テンプレート編集** | 対応 | **非対応** | 非対応 | 非対応 | 対応 |
| **チャート生成** | 対応（2D のみ） | 対応 | 非対応 | 非対応 | 対応（理論上） |
| **テーブル生成** | 対応（制約あり） | 対応 | Markdown テーブル | HTML テーブル | 対応（理論上） |
| **SmartArt** | 非対応 | 非対応 | 非対応 | 非対応 | 対応（理論上） |
| **SVG 画像** | 非対応 | 対応 | CSS 経由 | HTML ネイティブ | 対応（理論上） |
| **LLM 生成信頼性** | 中〜高 | 中〜高 | 高 | 高 | 低 |
| **LLM コード冗長性** | 中 | 中 | 低 | 低 | 極めて高 |
| **学習コスト** | 低 | 低 | 極めて低 | 低 | 極めて高 |
| **成熟度** | 高（v1.0.0） | 高 | 中 | 高 | - |
| **Anthropic 公式採用** | 非採用 | **新規作成に採用** | 非採用 | 非採用 | **テンプレート編集に採用** |

## SKILL.md で採用すべき手段の推奨

### 推奨アーキテクチャ: ハイブリッド方式（Anthropic 公式スキル準拠）

Anthropic 公式 PPTX スキルのアーキテクチャを基盤とし、以下の組み合わせを推奨する。

#### 主要手段

| ユースケース | 推奨手段 | 理由 |
|-------------|---------|------|
| **新規作成（スクラッチ）** | **PptxGenJS** | Anthropic 公式採用。チャート・テーブル・図形の全オブジェクトに対応。Claude Code の Bash ツールで `node` 実行可能 |
| **テンプレート編集** | **XML 直接操作**（unpack → edit → pack） | 既存テンプレートのレイアウト・スタイルを保持しつつコンテンツ差し替えが可能。Anthropic 公式スキルと同じアプローチ |
| **テキスト抽出・分析** | **markitdown** | 既存 PPTX の内容把握に使用 |
| **品質検証** | **LibreOffice + Poppler** | PDF 変換 → 画像化 → 視覚検査のパイプライン |

#### python-pptx を主要手段に選ばない理由

python-pptx は機能的に優秀だが、Anthropic 公式スキルが PptxGenJS を選択している事実は重要な判断材料。公式スキルとの互換性・将来の改善恩恵を考慮すると、PptxGenJS ベースが合理的。ただし、**テンプレート読み込み・編集が必要な場合**は python-pptx が PptxGenJS より優位（PptxGenJS は既存ファイルを読めない）。

#### Marp / reveal.js を選ばない理由

- Marp: PPTX 出力が画像ベースまたは実験的。編集可能な PPTX を安定的に生成できない
- reveal.js: PPTX 出力がネイティブ非対応。HTML ベースのプレゼンには最適だが、「PPTX ファイルを納品する」要件を満たせない

#### 補助的にコードファースト手段を活用する場面

reveal.js / Quarto は LLM との親和性が最も高い（テキストベースで直接生成可能）。PPTX が不要なケース（社内プレゼン、Web 公開等）では有力な選択肢として SKILL.md のオプショナル出力フォーマットに含めることを検討してもよい。

### 実装上の注意点

1. **画像素材は外部提供前提**: Claude は写真・イラストを生成できない。テンプレートに組み込むか、ストック画像 URL を指定する設計が必要
2. **品質検証ループは必須**: Anthropic 公式スキルが「最低1回の修正-再検証サイクル」を義務化している。SKILL.md にも同様のプロセスを組み込むべき
3. **レイアウト忠実度の期待値管理**: 100% 忠実な再現は不可能。人間の最終デザインレビューを前提とした設計が現実的
4. **テンプレート戦略**: スクラッチ生成よりテンプレートベースの方が品質安定。「構造優先のテンプレート設計」（明確な指標配置）が推奨される

---

## 情報の信頼性評価

- 一次ソース（公式ドキュメント・リポジトリ）: 12件
  - python-pptx 公式ドキュメント（6ページ）
  - PptxGenJS GitHub
  - Marp 公式サイト + GitHub（3件）
  - reveal.js 公式サイト + GitHub（2件）
  - Anthropic 公式 Skills GitHub + ドキュメント（3件）
  - Microsoft Learn（OOXML）
- 二次ソース（技術ブログ・比較研究）: 4件
  - Nicolas Brosse の LLM スライドフォーマット比較研究
  - SmartScope の Claude PPTX 実践ガイド
  - SlideModel の PPTX 構造解説
  - officeopenxml.com の PPTX 構造解説
- 注意が必要な情報:
  - Claude PPTX スキルの「数十〜100枚」は運用ガイダンスであり公式保証ではない
  - Marp の編集可能 PPTX は「実験的」ステータスであり、将来改善される可能性がある
  - PptxGenJS の Anthropic 採用は 2025年10月時点の情報であり、将来変更の可能性あり

## ソース一覧

1. [python-pptx 公式ドキュメント](https://python-pptx.readthedocs.io/en/latest/) - 公式
2. [python-pptx GitHub](https://github.com/scanny/python-pptx) - 公式
3. [PptxGenJS GitHub](https://github.com/gitbrent/PptxGenJS) - 公式
4. [PptxGenJS 公式サイト](https://gitbrent.github.io/PptxGenJS/) - 公式
5. [Marp 公式サイト](https://marp.app/) - 公式
6. [Marp CLI GitHub](https://github.com/marp-team/marp-cli) - 公式
7. [reveal.js 公式サイト](https://revealjs.com/) - 公式
8. [reveal.js GitHub](https://github.com/hakimel/reveal.js) - 公式
9. [Anthropic Skills GitHub](https://github.com/anthropics/skills) - 公式
10. [Anthropic Agent Skills ドキュメント](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) - 公式
11. [Microsoft Learn - PresentationML 構造](https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document) - 公式
12. [OOXML PPTX 構造 (officeopenxml.com)](http://www.officeopenxml.com/anatomyofOOXML-pptx.php) - 技術リファレンス
13. [LLM Slides Format Comparison (Nicolas Brosse, 2025)](https://nbrosse.github.io/posts/llm-slides/llm-slides.html) - 技術ブログ（実証研究）
14. [Claude PPTX スキル実践ガイド (SmartScope)](https://smartscope.blog/en/generative-ai/claude/claude-pptx-skill-practical-guide/) - 技術ブログ
15. [PPTX ファイル構造解析 (SlideModel)](https://slidemodel.com/anatomy-of-a-pptx-file/) - 技術ブログ
16. [Claude in PowerPoint ヘルプ](https://support.claude.com/en/articles/13521390-use-claude-in-powerpoint) - 公式
17. [tfriedel/claude-office-skills GitHub](https://github.com/tfriedel/claude-office-skills) - コミュニティ
18. [Marp PPTX 編集不可の FAQ](https://github.com/orgs/marp-team/discussions/82) - 公式
