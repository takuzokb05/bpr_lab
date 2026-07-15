# スライド作成 SKILL 調査プロジェクト

## プロジェクト概要

- **目的**: Claude がマッキンゼー / BCG 級の PPTX を生成できるようにする **SKILL.md** を設計するための調査
- **対象**: コンサルティングスライドの設計原則、LLM のスライド生成技術、プロンプト設計手法
- **主要な価値**: 調査結果を統合し、再利用可能な SKILL.md ドラフト設計仕様を導出する
- **副次目標**: Agent Teams の実践投入（7 エージェント協調）

## 調査の問い

| # | 問い | 出力ドキュメント | 担当 | 依存 |
|---|------|-----------------|------|------|
| Q1 | コンサル品質スライドの設計原則は何か？ 情報設計・視覚設計・ストーリー構成のベストプラクティス | docs/01_design_principles.md | ux-psychologist + battle-consultant | なし |
| Q2 | Claude が PPTX を生成する技術的手段と制約は何か？（python-pptx, Marp, reveal.js, XML直接生成等） | docs/02_technical_means.md | researcher-tech | なし |
| Q3 | LLM スライド生成のプロンプト / ワークフロー設計の先行事例と知見は何か？ | docs/03_prompt_workflow.md | researcher-prompt | なし |
| Q4 | Q1〜Q3 を統合し、SKILL.md ドラフトの設計仕様を構造化する | docs/04_skill_design.md | analyst | Q1〜Q3（検証済み） |

## ディレクトリ構造

```
スライド作成/
├── docs/                 # 調査ドキュメント（主成果物）
├── references/           # 参考資料
├── .claude/
│   ├── claude.md         # このファイル
│   ├── settings.json     # WebSearch/WebFetch自動承認 + Agent Teams有効化
│   ├── whiteboard.md     # エージェント間情報共有（追記のみ）
│   └── agents/           # エージェント定義（7名）
└── PLANS.md              # 進捗・意思決定の記録
```

## チーム構成（Agent Teams: 7名）

| エージェント | 役割 | agents/ 定義 |
|-------------|------|-------------|
| researcher-tech | PPTX 生成の技術的手段・ライブラリ・制約を調査 | researcher.md |
| researcher-prompt | LLM スライド生成のプロンプト設計・先行事例を調査 | researcher.md |
| ux-psychologist | 認知科学・UX の観点からスライド設計原則を導出 | ux-psychologist.md |
| battle-consultant | コンサル実務の視点で「伝わるスライド」の条件を定義 | battle-consultant.md |
| analyst | Q1〜Q3 の検証済み成果を統合し SKILL.md 設計仕様を構造化 | analyst.md |
| fact-checker | 各ドキュメント完成直後に事実検証を実施 | fact-checker.md |
| devils-advocate | 各ドキュメント検証済み直後に論理攻撃を実施 | devils-advocate.md |

## 調査ルール

### ソースと信頼性

- **全ての主張にソース（URL・出典）を必ず付ける**
- 一次ソース（公式ドキュメント・学術論文・書籍）を優先する
- 同じ情報を異なるソースでクロスチェックする
- 情報の鮮度（年度）に注意し、古いデータには明示する
- 信頼できるソース: McKinsey / BCG / Bain の公式出版物、Edward Tufte の著作、Garr Reynolds (Presentation Zen)、Nancy Duarte (slide:ology / Resonate)、学術論文（認知心理学・情報デザイン）、python-pptx 公式ドキュメント
- 除外すべきソース: 「これだけでOK」系のまとめ記事、SEO目的のアフィリエイトコンテンツ

### 分析姿勢

- 主張を無批判に受け入れない（批判的検証を徹底する）
- 具体的な数字・データを優先する（定性的な印象より定量的な根拠）
- 反例や不利なデータも公平に扱う
- **SKILL 設計の実用性**: 理論的に正しくても Claude が実行不能な指示は価値がない。常に「Claude がこの指示に従えるか？」を問う

### 品質チェック — 継続的介入モデル

本プロジェクトでは fact-checker と devils-advocate が**各ドキュメント完成直後に即座に介入**する。最終フェーズにまとめて実施するのではなく、各成果物が生成されるたびにレビューサイクルを回す。

```
ドキュメント完成 → fact-checker 検証 → 修正反映 → devils-advocate 攻撃 → 修正反映 → 検証済みドキュメント
```

この順序を各 Q1〜Q3 ドキュメントごとに実施する。Q4（統合）は検証済み Q1〜Q3 のみを入力とする。Q4 自体も同じレビューサイクルを通す。

## サブエージェントのWebSearch権限

`.claude/settings.json` の2層構成でWebSearch/WebFetchを自動承認する:

1. **`permissions.allow`**（静的許可）: バックグラウンドサブエージェント起動前の事前承認ステージで評価される
2. **`PreToolUse` フック**（動的許可）: ツール使用時に評価されるバックアップ

## レビューワークフロー（継続的介入）

```
Phase 1: 並列調査
  ├── Q1: ux-psychologist + battle-consultant → docs/01
  ├── Q2: researcher-tech → docs/02
  └── Q3: researcher-prompt → docs/03
  （各ドキュメント完成直後に↓を実行）
  └── fact-checker → 修正 → devils-advocate → 修正 → 検証済み

Phase 2: 統合分析（検証済みドキュメントのみを入力）
  └── Q4: analyst → docs/04
  └── fact-checker → 修正 → devils-advocate → 修正 → 検証済み
```

**whiteboard.md**: `.claude/whiteboard.md` はエージェント間の情報共有ファイル。各エージェントが作業開始時に読み、完了時にサマリーを追記する。追記のみ（削除・上書き禁止）。

## Agent Teams 運用

Agent Teams でテームメイトとして起動された場合、以下のルールに従う。

### テームメイトの義務

1. **作業開始時**: `.claude/whiteboard.md` を読み、ステータステーブルに自分の行を追加する
2. **各タスク完了時**: ステータステーブルの自分の行を Edit で更新する（進捗カウントと最終更新時刻）
3. **作業完了時**: ステータステーブルの状態を `✅ 完了` に更新し、ログセクションにサマリーを追記する
4. **成果物は即時書き出し**: 全タスク完了を待たず、各タスク完了時に docs/ にファイルを書き出す

### チームリードの状態確認

- `.claude/whiteboard.md` の **ステータステーブル** を Read すれば全テームメイトの現在状態が分かる
- `.claude/team-activity.log` に TaskCompleted フックが活動ログを自動記録する

## Git規約

- コミットメッセージ: `<type>(<scope>): <subject>`
  - type: docs / fix / refactor
  - scope: doc名（01, 02等）
  - 日本語OK

## 利用可能なエージェント

- agents/researcher.md — Web調査（researcher-tech, researcher-prompt の2名が共有）
- agents/ux-psychologist.md — 認知科学・UXの観点からスライド設計原則を導出（カスタムエージェント）
- agents/battle-consultant.md — コンサル実務の視点で辛口フィードバック（カスタムエージェント）
- agents/analyst.md — 検証済みドキュメントの統合・SKILL設計仕様の構造化
- agents/fact-checker.md — 事実検証（各ドキュメント完成直後に介入）
- agents/devils-advocate.md — 反論・論理攻撃（fact-checker検証後に介入）

**重要**: 各エージェントは `subagent_type: general-purpose`, `mode: bypassPermissions` で起動する。`Explore` タイプでは Write/Edit が使えず出力が空になる。

## プロジェクト固有のルール

- これは**ツール開発プロジェクトではない**。成果物は SKILL.md の設計仕様であり、Python コードではない
- 「コンサル品質」の定義: 情報密度が高く、1枚で意思決定を支援できるスライド（McKinsey, BCG, Bain の社外公開レポートを基準とする）
- Claude の現在の能力制約（テキスト生成が主、画像生成は限定的）を前提に設計する
- SKILL.md は Claude Code の SKILL フォーマット（skills-registry 準拠）に適合させる
