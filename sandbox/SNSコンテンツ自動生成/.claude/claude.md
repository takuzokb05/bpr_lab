# SNSコンテンツ自動生成

## プロジェクト概要

- **目的**: Grok API でツイート、Gemini API で Note 記事の下書きを自動生成する
- **対象ユーザー**: 自分（個人利用）
- **主要な価値**: 自分の文体・過去の発言スタイルを分析し、最新AI事情を取り込んだSNSコンテンツを効率的に下書き生成する

## 技術スタック

- **言語**: Python 3.9+
- **フレームワーク**: CLI（argparse）
- **データベース**: SQLite（ツイート/Note履歴・エンゲージメントデータ保存）
- **外部サービス**: Grok API (xAI), Gemini API (Google), X API (Twitter), Note（取得方法はPhase A調査後に確定）
- **パッケージ管理**: pip + requirements.txt

## ディレクトリ構造

SNSコンテンツ自動生成/
├── src/
│   ├── __init__.py
│   ├── config.py         # 設定・環境変数読み込み
│   ├── api_client.py     # 外部API連携（Grok, Gemini, X API）
│   ├── analyzer.py       # ツイート/Note文体分析・エンゲージメント分析
│   ├── generator.py      # コンテンツ生成（ツイート/Note）
│   └── db.py             # データベース操作
├── tests/
├── data/                 # SQLite DB / データファイル
├── docs/                 # Phase A: 調査ドキュメント
├── references/           # 元資料・参考文献
├── .claude/
│   ├── claude.md         # このファイル
│   ├── settings.json     # WebSearch/WebFetch自動承認
│   ├── whiteboard.md     # エージェント間情報共有（追記のみ）
│   ├── skills/           # スキル
│   └── agents/           # エージェント定義
├── .env.example
├── .gitignore
├── requirements.txt
├── PLANS.md
└── SPEC.md

## 開発ルール

### コーディング規約
- コメントは日本語で書く
- 変数名・関数名は意味が明確な英語を使用
- 型ヒントを使用する（def func(name: str) -> dict:）
- 1関数は1つの責務に絞る
- マジックナンバーは config.py に定数として定義

### Git規約
- コミットメッセージ: <type>(<scope>): <subject>
  - type: feat / fix / docs / refactor / test
  - scope: doc名（Phase A）またはモジュール名（Phase B）
  - 日本語OK
- ブランチ: feature/xxx, fix/xxx

### API連携ルール

#### 環境変数管理

config.py で環境変数を読み込み、未設定ならValueErrorを送出する。

#### リトライ・タイムアウト
- 全API呼び出しに timeout を設定する（デフォルト: 30秒）
- 一時的なエラー（5xx, Timeout）は指数バックオフでリトライ（最大3回）
- レート制限エラー（429）はRetry-Afterヘッダに従う

### データベースルール
- SQLite使用、コンテキストマネージャ（with文）必須
- パラメータ化クエリ必須（文字列結合禁止）

### セキュリティ
- APIキー・シークレットは .env に格納し .gitignore で除外
- ハードコードされた認証情報は絶対に禁止
- エラーメッセージに内部情報（パス、DB構造、APIキー）を含めない

### エラーハンドリング
- 例外を握りつぶさない（空のexcept禁止）
- 外部API呼び出しにはタイムアウトとリトライを設定
- ユーザーに見せるエラーメッセージは日本語で分かりやすく
- ログには logging モジュールを使用（print禁止）

## 調査の問い（Phase A）

| # | 問い | 出力ドキュメント | 依存 | 手法 |
|---|------|-----------------|------|------|
| Q1 | Grok API の仕様・モデル・料金 | docs/q1_grok_api.md | なし | evidence_collection |
| Q2 | X API の仕様・ツイート取得・エンゲージメント | docs/q2_x_api.md | なし | evidence_collection |
| Q3 | Note プラットフォームのデータ取得方法 | docs/q3_note_platform.md | なし | evidence_collection |
| Q4 | エンゲージメント分析手法 | docs/q4_engagement_analysis.md | なし | evidence_collection |
| Q5 | API モデル比較・選定 | docs/q5_model_comparison.md | Q1, Q2, Q3 | synthesis |

Q1〜Q4 は並列調査可能。Q5 は Q1〜Q3 の結果を統合する。

## 調査ルール

### ソースと信頼性
- 全ての主張にソース（URL・出典）を必ず付ける
- 一次ソース（公式ドキュメント・学術論文）を優先する
- 同じ情報を異なるソースでクロスチェックする
- API仕様情報は公式ドキュメントから取得

### 品質チェック
- 各ドキュメントは fact-checker で事実検証を実施
- 統合ドキュメントは devils-advocate で論理攻撃を実施
- fact-checker → 修正反映 → devils-advocate の順序を守る（並列不可）

## サブエージェントのWebSearch権限

.claude/settings.json の2層構成でWebSearch/WebFetchを自動承認する:
1. permissions.allow（静的許可）: バックグラウンドサブエージェント起動前の事前承認ステージで評価される
2. PreToolUse フック（動的許可）: ツール使用時に評価されるバックアップ

## レビューワークフロー

Phase 1: researcher (並列OK) → 各doc作成 → whiteboard.md に発見サマリーを追記
Phase 2: fact-checker (並列OK) → whiteboard.md を参照 → 事実修正を各docに反映
Phase 3: devils-advocate → 論理攻撃 → 設計修正を反映

whiteboard.md: .claude/whiteboard.md はエージェント間の情報共有ファイル。追記のみ（削除・上書き禁止）。

## Agent Teams 運用（3+ 並列実行時）

Agent Teams でテームメイトとして起動された場合、以下のルールに従う。

### テームメイトの義務

1. **作業開始時**: `.claude/whiteboard.md` を読み、ステータステーブルに自分の行を追加する
2. **各タスク完了時**: ステータステーブルの自分の行を Edit で更新する（進捗カウントと最終更新時刻）
3. **作業完了時**: ステータステーブルの状態を `✅ 完了` に更新し、ログセクションにサマリーを追記する
4. **成果物は即時書き出し**: 全タスク完了を待たず、各タスク完了時に docs/ にファイルを書き出す

### チームリードの状態確認

- `.claude/whiteboard.md` の **ステータステーブル** を Read すれば全テームメイトの現在状態が分かる
- `.claude/team-activity.log` に TaskCompleted フックが活動ログを自動記録する

## 利用可能なスキル

- .claude/skills/spec-driven-dev/SKILL.md — 仕様書駆動の段階的開発ワークフロー
- .claude/skills/code-review/SKILL.md — 多角的コードレビュー（堅牢性・効率性・セキュリティ・保守性）
- .claude/skills/error-handling-audit/SKILL.md — エラーハンドリング監査・改善

## 利用可能なエージェント

- .claude/agents/researcher.md — Web調査（バックグラウンド並列実行可能）
- .claude/agents/analyst.md — 情報分析・構造化（ツイート/Note分析）
- .claude/agents/fact-checker.md — 事実検証
- .claude/agents/devils-advocate.md — 反論・論理攻撃

全エージェントは subagent_type: general-purpose, mode: bypassPermissions で起動する。

## プロジェクト固有のルール

- 下書き生成まで: 自動投稿機能は作らない。下書きを生成し、人間が確認・編集して手動投稿する
- API使い分け: ツイート生成 → Grok API、Note記事生成 → Gemini API
- 文体の一貫性: 自分の過去の発言データを分析し、文体を模倣する
- 最新情報の取り込み: 生成時に最新のAI事情を検索して取り込む
- エンゲージメント分析: 「受けのいい文章」のパターンを分析し、生成に反映する
