# スライド作成 SKILL 調査プロジェクト

## Purpose / Big Picture

**完成物: Claude がマッキンゼー / BCG 級の PPTX を生成するための SKILL.md 設計仕様**

Claude Code の SKILL フォーマットに準拠した指示書を設計するための調査プロジェクト。コンサルティングスライドの設計原則、PPTX 生成の技術的手段、LLM プロンプト設計の先行事例を調査し、統合して SKILL.md ドラフトの設計仕様を導出する。

具体的には:
1. コンサル品質スライドの設計原則を認知科学・実務の両面から定義する
2. Claude が PPTX を生成する技術的手段と制約を調査する
3. LLM スライド生成のプロンプト・ワークフロー設計の先行事例を収集する
4. 上記を統合し、SKILL.md ドラフトの設計仕様を構造化する

**背景**: Claude はテキスト生成が主能力だが、python-pptx 等のライブラリを通じて PPTX 生成が可能。ただし「正しいコードを書ける」ことと「コンサル品質のスライドを生成できる」ことには大きな隔たりがある。この隔たりを埋める SKILL を設計するための調査が必要。

**副次目標**: Agent Teams（7エージェント協調）の実践投入。

## Progress

### Phase 1: 並列調査 ← 現在のフェーズ

- [ ] Q1: コンサル品質スライドの設計原則（ux-psychologist + battle-consultant） → docs/01_design_principles.md
- [ ] Q2: Claude の PPTX 生成技術と制約（researcher-tech） → docs/02_technical_means.md
- [ ] Q3: LLM スライド生成のプロンプト/ワークフロー設計（researcher-prompt） → docs/03_prompt_workflow.md

（各ドキュメント完成直後に fact-checker → 修正 → devils-advocate → 修正 のレビューサイクルを実施）

### Phase 2: 統合分析

- [ ] Q4: Q1〜Q3 統合 → SKILL.md ドラフト設計仕様（analyst） → docs/04_skill_design.md

（Q4 も同様に fact-checker → devils-advocate のレビューサイクルを実施）

### Phase 3: 品質検証（最終）

- [ ] devils-advocate 最終判定: 品質ゲート通過（YES 必須）

## Surprises & Discoveries

<!-- 作業中に遭遇した予期しない知見を記録する -->

## Decision Log

- 判断: Agent Teams 方式を採用（Subagent 方式ではなく）
  理由: 7エージェント起動のため、Subagent の並列2制限では不足。Agent Teams なら各テームメイトが独立インスタンスとして動作し、IPCデッドロックリスクなし。
  日付: 2026-02-26

- 判断: ux-psychologist と battle-consultant をカスタムエージェントとして新規作成
  理由: Registry にはこの2つの専門性に対応するエージェントがない。researcher に「認知科学者として振る舞え」と指示するよりも、専用エージェント定義の方が行動原則・出力フォーマットを精密に制御できる。
  日付: 2026-02-26

- 判断: fact-checker と devils-advocate を「継続的介入モデル」で運用
  理由: 最終フェーズにまとめてレビューすると、初期ドキュメントの事実誤認が後続の統合分析に波及する。各ドキュメント完成直後にレビューサイクルを回すことで、検証済みの情報のみを統合分析に投入する。
  日付: 2026-02-26

## Outcomes & Retrospective

<!-- 各Phase完了時に振り返りを記録する -->

## Context and Orientation

### ディレクトリ構造

```
スライド作成/
├── PLANS.md              # このファイル
├── docs/                 # 調査ドキュメント（主成果物）
├── references/           # 参考資料
├── .claude/
│   ├── claude.md         # プロジェクト設定
│   ├── settings.json     # WebSearch/WebFetch自動承認 + Agent Teams有効化
│   ├── whiteboard.md     # エージェント間情報共有
│   └── agents/           # エージェント定義（7名用）
│       ├── researcher.md         # researcher-tech, researcher-prompt 共用
│       ├── ux-psychologist.md    # 認知科学・UX専門（カスタム）
│       ├── battle-consultant.md  # 実戦コンサル（カスタム）
│       ├── analyst.md            # 統合分析
│       ├── fact-checker.md       # 事実検証
│       └── devils-advocate.md    # 反論・論理攻撃
└── .gitignore
```

### 用語定義

- **SKILL.md**: Claude Code の SKILL フォーマットに準拠した指示書。Claude がタスクを実行する際の行動原則・手順・出力フォーマットを定義する
- **コンサル品質**: 情報密度が高く、1枚で意思決定を支援できるスライド。McKinsey / BCG / Bain の社外公開レポートを基準とする
- **継続的介入モデル**: fact-checker と devils-advocate が各ドキュメント完成直後に即座にレビューする運用方式（最終フェーズ一括ではない）

### 関連ファイル

- `.claude/claude.md`: プロジェクトの設定・調査ルール・チーム構成
- `.claude/whiteboard.md`: エージェント間情報共有
- `.claude/agents/`: 各エージェントの定義と起動設定
