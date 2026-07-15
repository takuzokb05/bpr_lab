# SNSコンテンツ自動生成

このドキュメントは Living Document（生きた文書）である。
作業の進捗、発見事項、設計判断をリアルタイムで更新し続けること。
新しい Claude Code セッションでは、このファイルを最初に読み、現在地を把握してから作業を再開する。

## Purpose / Big Picture

**完成物: SNSコンテンツ自動生成エージェント**

Grok API でツイート、Gemini API で Note 記事の下書きを自動生成するCLIツール。
自分の過去の発言スタイルとエンゲージメント分析に基づき、最新AI事情を取り込んだコンテンツを生成する。

具体的には:
1. X API で自分の過去ツイートとエンゲージメントデータを取得・分析
2. Note の過去記事を取得・分析（方法はPhase Aで調査）
3. 「受けのいい文章」のパターンを抽出
4. 最新のAI事情を検索して取り込み
5. 自分の文体を模倣したツイート（Grok API）/ Note記事（Gemini API）の下書きを生成
6. 人間が確認・編集して手動投稿

**背景**: SNS発信を効率化したい。自分の文体やトーンを維持しつつ、最新情報を取り込んだ質の高いコンテンツを素早く下書きしたい。

## Progress

### Phase A: 技術調査 ← 現在のフェーズ

- [ ] Q1: Grok API の仕様・モデル・料金調査
- [ ] Q2: X API の仕様・ツイート取得・エンゲージメント調査
- [ ] Q3: Note プラットフォームのデータ取得方法調査
- [ ] Q4: エンゲージメント分析手法の調査
- [ ] Q5: API モデル比較・選定（Q1〜Q3統合）
- [ ] fact-checker による事実検証
- [ ] devils-advocate による設計レビュー

### Phase B: 実装

- [ ] F1: CLI基盤 + config + API接続
- [ ] F2: X API ツイート履歴取得 + データ保存
- [ ] F3: 自分のツイート/Note 文体分析（エンゲージメント込み）
- [ ] F4: 最新AI事情の情報収集パイプライン
- [ ] F5: ツイート下書き生成（Grok API）
- [ ] F6: Note記事下書き生成（Gemini API）
- [ ] F7: 出力フォーマット + レビュー用プレビュー

## Surprises & Discoveries

## Decision Log

## Outcomes & Retrospective

## Context and Orientation

### ディレクトリ構造

SNSコンテンツ自動生成/
├── PLANS.md
├── SPEC.md
├── .claude/
│   ├── claude.md
│   ├── settings.json
│   ├── whiteboard.md
│   ├── skills/
│   └── agents/
├── docs/
├── references/
├── src/
├── tests/
└── data/

### 用語定義

- エンゲージメント: ツイートへの反応（いいね、RT、リプライ、インプレッション）の総称
- スキ: Note プラットフォームでの「いいね」相当の反応
- 文体分析: テキストの特徴（語彙、文長、トーン、構造パターン）の定量的分析
- 下書き生成: AI が生成したコンテンツを人間が確認・編集する前の状態

### 関連ファイル

- .claude/claude.md: プロジェクト設定
- docs/: 調査ドキュメント（Phase A成果物）
- SPEC.md: 実装仕様書
- .env.example: 環境変数の一覧

### 既知の制約

- X API の無料枠は制限が厳しい（Phase A Q2 で詳細調査）
- Note に公式APIがない可能性がある（Phase A Q3 で代替手段調査）
- 自動投稿は行わない（下書き生成まで）
