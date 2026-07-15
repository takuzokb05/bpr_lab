# Q3: LLM スライド生成のプロンプト/ワークフロー設計

## 主要な発見

### 1. 既存ツール/サービスの設計思想

#### Gamma AI

- 要点: カードベースの「レスポンシブレイアウト」を採用し、固定スライドではなく垂直スクロール型のナラティブフローを重視。20以上のAIモデルを統合し、テキスト・画像・レイアウト・デザイン要素を自動生成する。2025年9月に「Gamma Agent」（Gamma 3.0）を導入し、Web検索・コンテンツ書き換え・デザインフィードバック・複雑な編集を自然言語で会話的に実行可能にした
- 設計原則: プロンプトの「文脈と目的」を理解し、アウトライン→全スライド→ビジュアルを一気通貫で生成。RAG統合により、AIが生成する編集や画像提案の関連性と自然さを向上
- SKILL設計への示唆: 「プロンプトの意図理解→構造化→生成」の3段パイプラインは参考になるが、Gammaの独自フォーマット（カード型）はPPTX生成とは異なるアプローチ
- ソース: [Gamma AI App Review 2026](https://www.gamsgo.com/blog/gamma-app-review), [Introducing Gamma 3.0](https://gamma.app/insights/introducing-gamma-3-0)

#### Beautiful.ai

- 要点: 「自動レイアウトルール」に基づく構造化されたスライドベースのプレゼンテーション。間隔・整列・デザインクリーンアップを自動化し、ブランド一貫性を保持
- 設計原則: レイアウト制約をシステムレベルで強制（ユーザーが自由に配置を崩せない）。これにより「常にプロフェッショナルな見た目」を保証
- SKILL設計への示唆: レイアウト制約のシステム的強制は、CLIツールでは難しいが、テンプレート+制約条件としてプロンプトに組み込むことは可能
- ソース: [Beautiful.ai vs Gamma 2026](https://www.beautiful.ai/compare/gamma-alternative)

#### SlidesGPT / Plus AI / その他

- 要点: 大半のツールはテキストプロンプト→完成スライドの「1ショット生成」を基本とし、アウトラインプレビュー→生成→反復修正のフローを採用。Microsoft CopilotはPowerPointネイティブ統合
- ソース: [Best AI Presentation Makers 2026](https://plusai.com/blog/best-ai-presentation-makers)

---

### 2. スライド生成に特化したプロンプト設計パターン

#### パターン A: ロールベースプロンプティング

- 要点: 「シニアプレゼンテーションデザイナー」等の役割を付与し、スタイル制約（ジャーゴンフリー、12語以下のバレットポイント）と対象聴衆を明示する
- 具体例: `"Act as a Senior presentation designer. Goal: create concise slide decks. Style: jargon-free, bullet points fewer than 12 words. Audience: [target]"`
- 効果: ロール設定により、LLMの出力トーン・情報密度・専門用語レベルが安定する
- ソース: [ChatGPT Prompts for Presentations - SlideModel](https://slidemodel.com/chatgpt-powerpoint-maker-prompt/)

#### パターン B: 構造化出力指定（JSON/XMLスキーマ）

- 要点: LLMにスライド構造をJSON/XMLで出力させ、それをレンダラーに渡す方式。各スライドのタイトル・本文・ビジュアル指示を構造化データとして扱う
- 具体例: アウトラインをJSONで出力 → 各スライドのコンテンツをJSONで生成 → python-pptx等でレンダリング
- 効果: 生成内容とレイアウトの関心を分離でき、品質制御が容易になる
- SKILL設計への示唆: Claude Code の SKILL では JSON マニフェスト → python-pptx ビルダー の2段構成が有効
- ソース: [PPTX CLI tool](https://github.com/tomleelong/PPTX), [claude-office-skills](https://github.com/tfriedel/claude-office-skills)

#### パターン C: コンテンツストラテジスト思考

- 要点: 「レイアウトを先に定義し、それから埋める」というアンカリング手法。構造・フロー・読者の期待をコントロールする
- 効果: スライドごとの情報密度が均一化し、ストーリーの流れが改善
- ソース: [Prompt Engineering Guide](https://www.promptingguide.ai/)

#### パターン D: Claude 固有 — XML タグによる構造化

- 要点: Claudeは `<instructions>`, `<context>`, `<input>`, `<example>` 等のXMLタグで複雑なプロンプトを明確に解析できる。スライド生成では、入力テキスト・スタイル指示・アウトライン・各スライドの制約をタグで分離することで誤解釈を低減
- 具体例: `<slide_style>`, `<outline>`, `<slide n="1">`, `<content_constraint>` 等
- ソース: [Anthropic Claude Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [Use XML Tags](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags)

---

### 3. ワークフロー設計: 1ショット vs 段階的生成

#### 学術的エビデンス: 段階的生成が圧倒的に優位

**DocPres（2024, EMNLP）** — 5段階パイプライン:
1. **Document Overview**: 階層的要約（セクション→サブセクション→コンテンツ）
2. **Outline Generation**: Chain-of-Thought プロンプティングで「重要トピックを良いフローで短いタイトルに」
3. **Slide-to-Section Mapping**: ステップバイステップ推論でスライドタイトルと文書セクションを対応付け（90%一致率）
4. **Content Generation**: 前のスライドをコンテキストに含め、一貫性を保持しながらスライドごとに生成
5. **Image Extraction**: CLIPエンベディングのコサイン類似度で図を選択

**結果**: 人間評価で DocPres は平均 3.2/5（利用可能性）vs 直接GPT生成の 1.2/5。「良い初稿として使える」評価。単一プロンプトの GPT-Flat, GPT-COT, GPT-Cons はプロンプト戦略を変えても同程度（~2.3/5 可読性）にとどまり、段階的分解の優位性を実証

- ソース: [Enhancing Presentation Slide Generation by LLMs with a Multi-Staged End-to-End Approach](https://arxiv.org/html/2406.06556v1)

**PPTAgent（2025, arXiv）** — 参照スライドベースの編集型パイプライン:
1. **Stage I: 参照分析** — 既存プレゼンテーションをクラスタリング（視覚埋め込み、閾値0.65）し、機能カテゴリ（構造スライド vs コンテンツスライド）に分類。コンテンツスキーマを抽出
2. **Stage II: アウトライン→編集** — どの参照スライドを使うか指定するアウトラインを生成。その後、各スライドについて参照をベースにコードアクション（`replace_span`, `del_span`, `clone_paragraph`, `replace_image`, `del_image`）で反復編集
3. **PPTEval**: 3次元評価（Content, Design, Coherence）。GPT-4oによる1-5スコア、人間評価との相関 r=0.71

**重要な知見**:
- HTML レンダリングで LLM の理解を助けると成功率 95% → 74.6%（なし）
- アウトラインありの一貫性スコア: 4.48 vs 3.36（なし）
- 参照スライドの品質に依存するという脆弱性あり
- **「アーキテクチャ設計はモデルサイズよりも大きなインパクトを持つ」**（GPT-4o-mini + RAG > GPT-4o 単体）

- ソース: [PPTAgent: Generating and Evaluating Presentations Beyond Text-to-Slides](https://arxiv.org/html/2501.03936v3)

#### 1ショット生成の限界

- 直接LLMにプレゼンテーション全体を生成させると、情報の網羅性・論理フロー・スライド間の一貫性が低下
- コンテキスト長の制約で、長い入力文書の処理に劣化が発生
- 「段階的に複雑なタスクを小さなサブタスクに分解する利点」が実証済み（DocPres論文）
- ソース: 上記 DocPres, PPTAgent 論文

#### SKILL設計への推奨ワークフロー

```
Step 1: 意図解析 — ユーザー入力から目的・聴衆・トーンを抽出
Step 2: アウトライン生成 — スライドタイトルと各スライドの役割を決定（CoT推論）
Step 3: コンテンツ生成 — スライドごとに前のスライドをコンテキストに含め逐次生成
Step 4: レイアウト適用 — テンプレート/制約に基づきレイアウトを決定
Step 5: 自己検証 — 生成結果をレビューし、修正が必要な箇所を特定
Step 6: 最終出力 — python-pptx 等でレンダリング
```

---

### 4. Claude 固有のベストプラクティス

#### System Prompt 設計

- **ロール付与**: 「You are a professional presentation designer specializing in McKinsey-style consulting slides.」のように具体的なロールを設定。Claude はシステムプロンプトに対する応答性が高い（Claude 4.5/4.6 では以前のモデルより敏感）
- **XML タグ活用**: `<slide_brief>`, `<style_guide>`, `<content_source>` 等でプロンプトの各部分を明確に分離
- **Few-shot Examples**: `<example>` タグ内に理想的なスライド出力の例を3-5個提示。エッジケースを含む多様な例が推奨
- ソース: [Anthropic Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)

#### Prompt Chaining（段階的API呼び出し）

- Claude の最新モデルはアダプティブシンキングとサブエージェントオーケストレーションにより、多くのマルチステップ推論を内部的に処理可能
- ただし、中間出力の検査やパイプライン構造の強制が必要な場合は、明示的なプロンプトチェーンが有効
- **最も一般的なチェーンパターン**: ドラフト生成 → 基準に基づくレビュー → フィードバックに基づく洗練（各ステップが別API呼び出し）
- ソース: [Chain Complex Prompts - Anthropic Docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts)

#### Structured Output（構造化出力）

- Claude は JSON, YAML, Markdown, テーブル等の構造化出力を確実に処理可能
- Structured Outputs 機能により、レスポンスを指定スキーマに制約可能
- スライド生成では: 各スライドの内容を JSON スキーマ（タイトル, 本文, ビジュアル指示, レイアウトタイプ）で出力させ、レンダラーに渡すのが最も信頼性が高い
- ソース: [Anthropic Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)

#### Artifacts / React コンポーネント

- Claude.ai の Artifacts 機能では、React コンポーネントとしてスライドのプレビューを生成し、リアルタイムでフィードバックを得ることが可能
- 「Frontend Slides」スキル: HTML/CSS でアニメーション付きWebプレゼンテーションを生成（キーボード操作・スワイプ・プログレスバー対応）
- **注意**: Artifacts は Claude.ai 専用。Claude Code の SKILL ではコード実行（python-pptx）が主経路
- ソース: [Every Way to Make Slides with Claude in 2026](https://www.the-ai-corner.com/p/every-way-to-make-slides-with-claude), [frontend-slides](https://github.com/zarazhangrui/frontend-slides)

#### Claude Code Agent Skills（SKILL.md フォーマット）

- SKILL.md の2部構成: YAMLフロントマター（起動条件）+ Markdownコンテンツ（実行指示）
- **Progressive Disclosure**: 必要な情報を段階的に開示。SKILL.md は500行以下に抑え、詳細な参照資料は別ファイルに分離
- **claude-office-skills** の PPTX ワークフロー:
  1. テンプレート分析（markitdown でテキスト抽出）
  2. ビジュアル検証（サムネイルグリッド生成）
  3. スライド並び替え（インデックスベース）
  4. テキストインベントリ（全テキスト要素をJSONに抽出）
  5. コンテンツ投入（フォーマット付き置換JSONを生成）
  6. 最終組み立て + 検証
- ソース: [Claude Code Skills](https://code.claude.com/docs/en/skills), [claude-office-skills](https://github.com/tfriedel/claude-office-skills), [Anthropic Skills Design](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

---

### 5. 品質制御手法

#### Self-Refine（自己洗練）パターン

- 要点: 同じLLMが「生成→フィードバック→洗練」を反復する手法。追加学習データ・強化学習不要
- 効果: 7つの多様なタスクで、1ショット生成より人間評価・自動メトリクスの両方で改善
- スライド生成への適用: アウトライン生成後に「このアウトラインの論理フロー・情報網羅性を評価せよ」→ フィードバックに基づき修正 → 各スライドでも同様に適用
- ソース: [Self-Refine: Iterative Refinement with Self-Feedback (NeurIPS 2023)](https://arxiv.org/abs/2303.17651)

#### Textual-to-Visual Iterative Self-Verification

- 要点: テキスト形式（JSON）のレイアウトを画像に変換し、LLMベースの Reviewer + Refiner で反復修正。JSONベースの自己修正だけでは効果がなく、ビジュアル変換により劇的に改善
- 定量結果:
  - Alignment: 2.0（ベースライン）→ 2.1（JSON修正のみ）→ 3.0（ビジュアル変換）
  - Logical Flow: 3.0 → 3.8（参照品質 3.7 に匹敵）
- SKILL設計への示唆: python-pptx でスライドを生成 → サムネイル画像化 → Claude に画像を見せてレビュー → 修正 という「視覚的フィードバックループ」が有効
- ソース: [Textual-to-Visual Iterative Self-Verification for Slide Generation](https://arxiv.org/html/2502.15412)

#### PPTEval: 3次元評価フレームワーク

- **Content**: テキストの簡潔さ、文法的正確性、画像の関連性
- **Design**: 色の調和、視覚要素、レイアウトの可読性、要素の重なりなし
- **Coherence**: 段階的な構造展開、必須の文脈情報の含有
- GPT-4o をジャッジとして使用、1-5スケール。人間評価との Pearson 相関 0.71
- ソース: [PPTAgent](https://arxiv.org/html/2501.03936v3)

#### SlideBot: 認知負荷理論に基づく品質保証

- **Cognitive Load Theory (CLT)**: 内因的負荷を序論スキャフォールディングで削減、外因的負荷を冗長排除で最小化、発生的負荷をスキーマ構築で強化
- **Cognitive Theory of Multimedia Learning (CTML)**: シグナリング（太字キーワード）、一貫性（関連情報のみ）、空間的近接（テキストと図を隣接配置）
- **結果**: SlideBot は Microsoft Copilot を全次元で大幅上回り（信頼性 +2.42pt、概念的正確性 +0.86pt）。直接プロンプティングベースラインにも全勝
- ソース: [SlideBot: A Multi-Agent Framework](https://arxiv.org/html/2511.09804v1)

---

### 6. 失敗パターンと対策

#### 失敗パターン A: テキスト過多 / 情報密度の暴走

- 症状: 1スライドに大量のテキスト、バレットポイントの深いネスト、読めないフォントサイズ
- 原因: LLMの「網羅性バイアス」。プロンプトで制約しないと情報を詰め込む傾向
- 対策: プロンプトに明示的な制約（「1スライド最大5バレットポイント、各12語以内」「Key Message を1行で」）。スライドごとに文字数カウントの自動チェック
- ソース: [Common AI Presentation Mistakes - SlidesAI](https://www.slidesai.io/blog/common-ai-presentation-mistakes)

#### 失敗パターン B: サイレントレイアウト崩壊

- 症状: 編集時は正常に見えるが、エクスポート後やプレゼン時にテキストが切れる・重なる
- 原因: フォントレンダリング差異、コードブロックの折り返し、画面サイズの違い。LLM生成物には「これは間違っている」という明確なシグナルがない
- 対策: 「ビジュアル検証」を必ず組み込む。サムネイルグリッド生成 → 人間またはLLMによる目視チェック。CI/自動パイプラインへのオーバーフローチェッカー組み込み
- ソース: [The Silent Layout Bug in AI-Generated Slides](https://dev.to/rivi_mizuiro_147c9219f6d5/the-silent-layout-bug-in-ai-generated-slides-2oml)

#### 失敗パターン C: 統計データのハルシネーション

- 症状: もっともらしいが虚偽の統計・数値がスライドに含まれる
- 具体例: 銀行クライアント向け Copilot 生成スライドで「欧州フィンテック資金調達が43%増加」と記載 → 実際は12%
- 対策: RAG（検索拡張生成）の活用、全ての数値データにソースを要求するプロンプト設計、fact-checker エージェントによる検証
- ソース: [AI Presentation Maker is Failing You](https://medium.com/@abhimansbhat18/your-ai-presentation-maker-is-failing-you-heres-how-to-fix-it-eb44869c3bed)

#### 失敗パターン D: レイアウトの単調性 / AIスロップ

- 症状: 全スライドが同じレイアウト、同じ配色、同じフォント。「AI感」が強い
- 原因: LLMの「分布の中心」への収束傾向
- 対策: テンプレートバリエーションの明示的な指定、スライドタイプごとの異なるレイアウト指示（タイトル、データ、比較、引用等）、Claudeの場合は `<frontend_aesthetics>` プロンプトパターンで「AIスロップ」回避を指示
- ソース: [Anthropic Prompting Best Practices - Frontend Design](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)

#### 失敗パターン E: JSON/XMLの構文エラー

- 症状: 構造化出力が不正な JSON/XML となり、レンダラーがクラッシュ
- 対策: Claude の Structured Outputs 機能でスキーマを強制。バリデーション→リトライループ。PPTAgentの手法（最大2回の自己修正反復）が参考になる
- ソース: [5 Steps to Handle LLM Output Failures](https://latitude.so/blog/5-steps-to-handle-llm-output-failures)

#### 失敗パターン F: コンテキスト長の壁

- 症状: 長い入力文書でプレゼンテーション全体を一括生成すると後半のスライドの品質が低下
- 対策: DocPres方式の階層的要約→スライドごとのセクションマッピング。「文書全体をコンテキストに入れるのではなく、各スライドに関連するセクションのみを渡す」
- ソース: [DocPres](https://arxiv.org/html/2406.06556v1)

---

## マルチエージェント設計パターン

### SlideBot のマルチエージェント設計（教育スライド生成）

5つの専門エージェント + 中央のモデレータで構成:

| エージェント | 責務 |
|-------------|------|
| Moderator | 全エージェントの調整、フィードバックループ管理、スライドプラン構築 |
| Retriever | 外部ソースから情報収集、引用付き構造化サマリーを返却 |
| Code Generator | スライドプランを LaTeX Beamer コードに変換 + コンパイル検証ループ |
| Enhancer | インストラクターコメント挿入、ビジュアルマクロ（パイプライン、数式、擬似コード等） |

- **結果**: Microsoft Copilot を全次元で大幅に上回り、「アーキテクチャ設計はモデルサイズよりも大きな影響を持つ」ことを実証
- ソース: [SlideBot](https://arxiv.org/html/2511.09804v1)

### Auto-Slides: インタラクティブなマルチエージェントシステム

- 研究プレゼンテーションの作成・カスタマイズに特化したインタラクティブシステム
- ソース: [Auto-Slides](https://arxiv.org/abs/2509.11062)

### SlideGen: 科学スライド生成のための協調マルチモーダルエージェント

- 科学論文からスライドを生成する協調型マルチモーダルエージェント
- ソース: [SlideGen](https://arxiv.org/pdf/2512.04529)

---

## SKILL.md 設計への統合的示唆

### 推奨アーキテクチャ

学術研究と実装事例から導出される、SKILL.md に組み込むべき設計要素:

1. **段階的生成パイプライン**: 1ショットではなく、意図解析→アウトライン→コンテンツ→レイアウト→検証の多段構成
2. **構造化中間表現**: 各段階の出力をJSON/XMLスキーマで定義し、段階間のインターフェースを明確化
3. **Self-Refine ループ**: アウトライン生成後とスライド生成後にそれぞれ自己レビューステップを挿入
4. **ビジュアル検証**: サムネイル生成→視覚的レビューで「サイレントレイアウト崩壊」を検出
5. **テンプレート活用**: ゼロから生成するのではなく、既存テンプレートの編集アプローチが品質・一貫性を向上
6. **明示的制約**: 文字数制限、バレットポイント数制限、レイアウトタイプ指定をプロンプトに組み込む
7. **認知負荷理論の反映**: CLT/CTMLに基づくスライド構成原則をプロンプトに埋め込む（Q1成果と連携）

### Claude Code SKILL として実装する場合の構成案

```
SKILL.md (エントリポイント、500行以内)
├── Step 1: 意図解析 — XML タグでユーザー入力を解析
├── Step 2: アウトライン生成 — CoT + Self-Refine
├── Step 3: コンテンツ生成 — スライドごとに前スライドをコンテキストに
├── Step 4: JSON マニフェスト生成 — 各スライドの構造化データ
├── Step 5: python-pptx レンダリング — テンプレートベースの組み立て
└── Step 6: 検証 — サムネイル生成 + 視覚的チェック

resources/
├── slide_schema.json  — スライドの JSON スキーマ定義
├── style_guide.md     — コンサル品質の基準・制約
├── examples/          — 理想的な出力例（few-shot 用）
└── templates/         — PPTX テンプレート
```

---

## 情報の信頼性評価

- 一次ソース（公式ドキュメント・学術論文・リポジトリ）: 12件
  - Anthropic 公式ドキュメント (3), arXiv 学術論文 (5: DocPres, PPTAgent, Self-Refine, SlideBot, Textual-to-Visual), GitHub リポジトリ (4: claude-office-skills, PPTX, frontend-slides, slidev-overflow-checker)
- 二次ソース（テックメディア・ブログ等）: 8件
  - AI比較レビュー (3), Medium技術記事 (2), DEV Community (1), 製品レビュー (2)
- 注意が必要な情報:
  - Gamma, Beautiful.ai 等の製品比較はマーケティングバイアスの可能性あり。機能記述は公式サイトから取得したが、内部アーキテクチャの詳細は非公開
  - SlideBot の評価は参加者数が限定的（学生28名、専門家11名）

---

## ソース一覧

1. [PPTAgent: Generating and Evaluating Presentations Beyond Text-to-Slides (arXiv, 2025)](https://arxiv.org/html/2501.03936v3) - 学術論文
2. [Enhancing Presentation Slide Generation by LLMs with a Multi-Staged End-to-End Approach (arXiv/EMNLP, 2024)](https://arxiv.org/html/2406.06556v1) - 学術論文
3. [Textual-to-Visual Iterative Self-Verification for Slide Generation (arXiv, 2025)](https://arxiv.org/html/2502.15412) - 学術論文
4. [SlideBot: A Multi-Agent Framework for Generating Informative, Reliable, Multi-Modal Presentations (arXiv, 2025)](https://arxiv.org/html/2511.09804v1) - 学術論文
5. [Self-Refine: Iterative Refinement with Self-Feedback (NeurIPS, 2023)](https://arxiv.org/abs/2303.17651) - 学術論文
6. [Anthropic Claude Prompting Best Practices (公式ドキュメント)](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) - 公式
7. [Anthropic Chain Complex Prompts (公式ドキュメント)](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts) - 公式
8. [Claude Code Skills (公式ドキュメント)](https://code.claude.com/docs/en/skills) - 公式
9. [claude-office-skills (GitHub)](https://github.com/tfriedel/claude-office-skills) - OSS
10. [PPTX CLI (GitHub)](https://github.com/tomleelong/PPTX) - OSS
11. [frontend-slides (GitHub)](https://github.com/zarazhangrui/frontend-slides) - OSS
12. [slidev-overflow-checker (GitHub)](https://github.com/mizuirorivi/slidev-overflow-checker) - OSS
13. [Gamma AI App Review 2026](https://www.gamsgo.com/blog/gamma-app-review) - メディアレビュー
14. [Introducing Gamma 3.0](https://gamma.app/insights/introducing-gamma-3-0) - 製品公式
15. [Beautiful.ai vs Gamma 2026](https://www.beautiful.ai/compare/gamma-alternative) - 製品比較
16. [Best AI Presentation Makers 2026 - Plus AI](https://plusai.com/blog/best-ai-presentation-makers) - メディアレビュー
17. [ChatGPT Prompts for Presentations - SlideModel](https://slidemodel.com/chatgpt-powerpoint-maker-prompt/) - メディア
18. [Common AI Presentation Mistakes - SlidesAI](https://www.slidesai.io/blog/common-ai-presentation-mistakes) - メディア
19. [The Silent Layout Bug in AI-Generated Slides - DEV Community](https://dev.to/rivi_mizuiro_147c9219f6d5/the-silent-layout-bug-in-ai-generated-slides-2oml) - メディア
20. [Auto-Slides (arXiv, 2025)](https://arxiv.org/abs/2509.11062) - 学術論文
