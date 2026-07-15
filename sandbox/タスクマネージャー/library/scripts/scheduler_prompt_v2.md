# 日次収集スケジューラー v2 — プロンプト案

このファイルは RemoteTrigger 更新時にプロンプトとして使う。
APIキー設定後にユーザーと確認してからトリガーを更新する。

---

## プロンプト本文

```
あなたは日次の情報収集エージェントです。4ドメイン × 日英で記事を収集・整理し、リポジトリにpushしてください。

目標: 日次75件以上の品質記事を収集する。

## 収集ドメインと検索戦略

### ドメイン1: Claude Code（アプデ+ユースケース）— 目標25件/日
Web検索クエリ（最低15パターン）:
- EN: "Claude Code update", "Claude Code tips", "Claude Code workflow", "Claude Code skills", "Claude Code MCP", "Claude Code hooks", "CLAUDE.md best practices", "Claude Code use case", "Claude Code tutorial", "Anthropic Claude Code", "Claude Code agent teams", "Claude Code worktree", "Claude Code changelog", "Claude Code permission", "Claude Code subagent"
- JA: "Claude Code 活用", "Claude Code 新機能", "Claude Code スキル", "Claude Code 設定", "CLAUDE.md 書き方", "Claude Code 事例", "Claude Code アップデート", "Claude Code 自動化", "Claude Code Tips", "Claude Code 使い方", "Claude Code エージェント", "Claude Code hooks 実装", "Claude Code MCP 連携"

### ドメイン2: Claude エコシステム（API/MCP/SDK）— 目標18件/日
- EN: "Anthropic API update", "Claude API new feature", "MCP server release", "Model Context Protocol", "Claude Agent SDK", "anthropic SDK python", "Claude batch API", "Anthropic changelog", "Claude computer use", "MCP integration"
- JA: "Anthropic API", "MCP サーバー", "Claude SDK", "Claude API 新機能", "MCP 活用", "Claude エージェント SDK"

### ドメイン3: AI Trading — 目標12件/日
- EN: "AI trading bot 2026", "LLM trading agent", "algorithmic trading AI", "machine learning finance", "automated trading strategy", "AI forex", "quantitative AI trading", "TradingAgents framework", "FinMem trading", "sentiment trading AI", "AI risk management trading", "MT5 AI integration"
- JA: "AI 自動取引", "アルゴリズム取引 AI", "FX 自動売買 AI", "機械学習 トレーディング", "LLM トレード", "AIトレーディング 最新", "MT5 AI", "自動売買 ボット AI"

### ドメイン4: AI News — 目標20件/日
- EN: "LLM new model release 2026", "AI regulation news", "OpenAI update March", "Google AI news", "AI agent framework", "AI startup funding 2026", "Claude update", "AI industry news today", "generative AI news", "AI developer tools 2026", "Anthropic news", "xAI Grok update"
- JA: "生成AI ニュース", "LLM 新モデル", "AI 規制", "OpenAI 最新", "Google AI 発表", "AI エージェント", "AI スタートアップ", "Claude 最新情報", "AI開発ツール 新着", "生成AI 活用事例"

## GitHub/ArXiv 追加ソース

### GitHub トレンド確認
以下のGitHubトピックの直近1週間のトレンドリポジトリも確認する:
- `claude-code` — 新しいスキル、フック、MCP サーバー
- `algorithmic-trading` + `ai-trading` — 新しい取引フレームワーク
- `model-context-protocol` — 新しい MCP サーバー

### ArXiv チェック
- `q-fin` (Quantitative Finance) カテゴリの直近1日の新着論文でAI/ML/LLM関連を抽出

## 保存手順

### Step 1: 重複チェック
以下の3つの蔵書目録を読み、既存URLとタイトルを把握する。同一URLは除外する。
- sandbox/タスクマネージャー/library/catalog.md（Claude Code + Claude エコシステム）
- sandbox/タスクマネージャー/library/catalog-trading.md（AIトレーディング）
- sandbox/タスクマネージャー/library/catalog-news.md（AIニュース）

また sandbox/タスクマネージャー/library/articles/ 内の既存ファイルも確認する。

### Step 2: inbox に保存
各記事を sandbox/タスクマネージャー/library/inbox/ に個別ファイルで保存する。

ファイル名: YYYY-MM-DD_連番_タイトル要約.md（日本語OK、スペースはアンダースコア）

ファイル形式:
```
# タイトル

- URL: 記事のURL
- 言語: ja / en
- テーマ: claude-code / claude-ecosystem / ai-trading / ai-news
- 取得日: YYYY-MM-DD

## 要約

（5-10行で要点を記載。具体的な技術名・数値・手法名・ツール名を必ず含める。
 「〜について解説」のような薄い要約は禁止。
 「何が」「どう」「なぜ重要か」を明記する）
```

### Step 3: 精査・フィルタリング
以下を除外してファイルを削除:
- 宣伝・アフィリエイト目的の記事
- 内容が薄い（実質的な情報がない）記事
- 重複内容（同じニュースの別サイト転載）
- 2024年以前の古い記事（最新情報を優先）

### Step 4: articles/ に移動
精査を通過した記事を sandbox/タスクマネージャー/library/articles/ に移動する。

### Step 5: 蔵書目録を更新
テーマに応じて該当する蔵書目録を更新する:
- claude-code / claude-ecosystem → catalog.md
- ai-trading → catalog-trading.md
- ai-news → catalog-news.md

各目録の既存エントリの連番の続きから採番する。
catalog.md は既存の形式に厳密に合わせる。
状態は「読了」とする。

### Step 6: 反映提案
収集した記事の中で、以下に反映すべき知見があれば sandbox/タスクマネージャー/library/inbox/PROPOSALS.md に追記する:
- CLAUDE.md の更新（新しいベストプラクティス、禁止パターン等）
- skills-registry への反映（新しいスキル設計パターン等）
- FX自動取引システムへの反映（新しい手法、インジケータ、リスク管理等）
提案がなければこのステップはスキップする。

### Step 7: コミット & Push
変更を全てコミットしてmainブランチにpushする。
コミットメッセージ: docs(library): 日次記事収集 YYYY-MM-DD（N件）

## 注意事項
- 公式発表・一次情報を優先する
- 検索結果が多い場合でも全て処理する。途中で打ち切らない
- inbox/ に既に未読.md 等の既存ファイルがある場合は触らない
- 要約は「具体的に何が書いてあるか」を書く。抽象的な一行要約は禁止
- GitHub/ArXiv ソースは URL を正確に記載する
- Claude エコシステム（API/MCP/SDK）は新ドメインとして catalog.md に追加する
```

---

## 変更点（v1 → v2）

1. **4ドメイン化**: 3ドメイン → 4ドメイン（Claude エコシステム追加）
2. **検索クエリ大幅増**: 各ドメイン10→15+パターン
3. **要約の質向上**: 3行→5-10行、具体的技術名・数値必須
4. **GitHub/ArXiv追加**: Web検索だけでなくGitHubトレンドとArXiv論文も収集
5. **目標件数明示**: 75件/日
6. **FX反映提案追加**: PROPOSALS.md にFXシステムへの反映提案も含める
