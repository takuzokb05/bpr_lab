# Claude Code 自動化・リモート実行 調査レポート

調査日: 2026-03-28

## 1. Claude Code Web版 (claude.ai/code) の現状

### 概要
Claude Code Web版はブラウザ上でClaude Codeを実行できる環境。ローカルセットアップ不要で、長時間タスクを投げて後で確認できる。

### 主な機能
- **クラウド実行**: Anthropicのインフラ上でコード実行（ローカルマシン不要）
- **GitHub連携**: リポジトリのクローン→変更→PR作成まで自動
- **スケジュールタスク**: cron的な定期実行（最小間隔1時間）
- **MCP Connectors**: Slack、Linear、Google Drive等の外部サービス接続
- **環境設定**: ネットワークアクセス制限、環境変数、セットアップスクリプト
- **PR作成**: 変更はデフォルトで `claude/` プレフィックスのブランチに限定

### 制約
- **ローカルファイルアクセス不可**: 毎回GitHubからfresh clone
- **最小実行間隔**: 1時間（Desktop版は1分から可能）
- **ブランチ制限**: デフォルトで `claude/` プレフィックスのみpush可能（解除可能）
- **対応プラン**: Pro, Max, Team, Enterprise（Freeは不可）

### リモートコントロール（2026年2月〜）
ローカルのCLIセッションをclaude.ai/codeやiOS/Androidアプリから遠隔操作可能。コードはローカルに残り、チャットメッセージのみ暗号化されて中継される。

---

## 2. スケジューリング機能の比較

### 3つの方式

| 項目 | Cloud (Web) | Desktop | /loop (CLI) |
|------|:-----------:|:-------:|:-----------:|
| 実行場所 | Anthropicクラウド | ローカルマシン | ローカルマシン |
| マシン起動必須 | No | Yes | Yes |
| セッション維持必須 | No | No | Yes |
| 再起動後の永続性 | Yes | Yes | No |
| ローカルファイルアクセス | No (fresh clone) | Yes | Yes |
| MCP | Connectors設定 | 設定ファイル+Connectors | セッション継承 |
| 最小間隔 | 1時間 | 1分 | 1分 |

### Cloud スケジュールタスクの作成方法

1. **Web UI**: claude.ai/code/scheduled → 「New scheduled task」
2. **Desktop**: Schedule ページ → 「New task」→「New remote task」
3. **CLI**: `/schedule` コマンド（会話形式でセットアップ）

### /schedule コマンド（CLIからCloud task作成）
```
/schedule daily PR review at 9am
/schedule list
/schedule update
/schedule run
```

### RemoteTrigger API
CLIからCloud scheduled taskをプログラマティックに操作可能:
- `list`: 全トリガー一覧
- `get`: 特定トリガーの詳細
- `create`: 新規作成
- `update`: 更新
- `run`: 即時実行

### /loop（セッション内ポーリング）
```
/loop 5m check if the deployment finished
/loop 20m /review-pr 1234
```
- セッション終了で消滅（3日で自動期限切れ）
- Catch-up実行なし（ビジー中のmissは1回だけ発火）

### CronCreate ツール（セッション内スケジューリング）
- 5フィールドcron式（ローカルタイムゾーン）
- `durable: true` で `.claude/scheduled_tasks.json` に永続化可能
- `recurring: false` で1回限りのリマインダー
- セッション内最大50タスク

---

## 3. GitHub Actions 連携

### 公式Action
- リポジトリ: `anthropics/claude-code-action`
- マーケットプレイス: Claude Code Action Official

### セットアップ
```bash
# CLI からワンコマンドセットアップ
claude
/install-github-app
```

### 認証方式
| 方式 | 必要な Secret |
|------|---------------|
| Anthropic API 直接 | `ANTHROPIC_API_KEY` |
| AWS Bedrock | `AWS_ROLE_TO_ASSUME` (OIDC) |
| Google Vertex AI | `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT` |

### 基本ワークフロー例
```yaml
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
jobs:
  claude:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### 定期実行（cron trigger）
```yaml
name: Daily Report
on:
  schedule:
    - cron: "0 9 * * *"
jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: "Generate a summary of yesterday's commits and open issues"
          claude_args: "--model opus"
```

### Agent SDK（プログラマティック実行）
```bash
# CLI（旧headlessモード）
claude -p "Find and fix the bug in auth.py" --allowedTools "Read,Edit,Bash"

# bare モード（CI向け、設定ファイル無視で高速起動）
claude --bare -p "Summarize this file" --allowedTools "Read"

# JSON出力
claude -p "Summarize this project" --output-format json

# 会話の継続
session_id=$(claude -p "Start a review" --output-format json | jq -r '.session_id')
claude -p "Continue that review" --resume "$session_id"
```

Python/TypeScript SDKも利用可能（`claude -p` のラッパー）。

---

## 4. 自動化手段の全体像

### claude.aiのCode機能を自動実行する方法

| 方式 | 実現可能性 | 備考 |
|------|:---------:|------|
| Cloud Scheduled Tasks | **可能** | Web UIまたは`/schedule`で作成。最小1時間間隔 |
| RemoteTrigger API | **可能** | CLIからAPI直叩きでCRUD+即時実行 |
| GitHub Actions + claude-code-action | **可能** | cron triggerで定期実行 |
| Agent SDK (CLI `claude -p`) | **可能** | 外部cron/Task Schedulerと組合せ |
| Agent SDK (Python/TypeScript) | **可能** | アプリに組み込み |
| Webhook/API直接呼び出し | **不可** | claude.aiのCode機能にWebhook APIは存在しない |

### 重要な制約
- Max/Proサブスクリプションの課金はプログラマティック呼び出しに使えない（API Keyのみ）
- Cloud Scheduled Tasksはサブスク課金（Pro/Max/Team/Enterprise）
- GitHub Actions版はAPI Key課金（トークン従量）

---

## 5. コスト比較

### API トークン単価

| モデル | Input | Output | Batch Input | Batch Output |
|--------|------:|-------:|------------:|-------------:|
| Opus 4.6 | $5/MTok | $25/MTok | $2.50/MTok | $12.50/MTok |
| Sonnet 4.6 | $3/MTok | $15/MTok | $1.50/MTok | $7.50/MTok |
| Haiku 4.5 | $1/MTok | $5/MTok | $0.50/MTok | $2.50/MTok |

Prompt Caching: Cache Hit = 基本入力単価の0.1倍

### サブスクリプション

| プラン | 月額 | 用途 |
|--------|-----:|------|
| Pro | $20 | Claude Code Web/Desktop/CLI。定期タスク利用可能 |
| Max 5x | $100 | Pro の5倍使用量 |
| Max 20x | $200 | Pro の20倍使用量 |
| Team | $25〜$150/user | 組織向け |

### 方式別コスト試算（「定期情報収集→リポジトリ反映」想定）

**想定タスク**: 毎日1回、Web検索で情報収集→記事要約→リポジトリにコミット
- 推定トークン: 入力 100K〜200K, 出力 20K〜50K / 回

| 方式 | 月間コスト（概算） | 備考 |
|------|------------------:|------|
| **Cloud Scheduled Task (Pro)** | **$20/月（定額）** | Pro契約に含まれる。制限に達するとスロットル |
| **Cloud Scheduled Task (Max 5x)** | **$100/月（定額）** | 大量実行向け |
| **GitHub Actions + API** | **$5〜15/月** | API従量 + GitHub Actions分。Sonnet使用時 |
| **GitHub Actions + API (Opus)** | **$10〜30/月** | Opus使用時 |
| **ローカルcron + CLI (`claude -p`)** | **$5〜15/月** | API従量のみ。ただしPC常時起動が必要 |
| **Agent SDK (Python) + VPS** | **$5〜15/月 + VPS** | API従量 + VPS費用 |

---

## 6. 「定期的な情報収集→リポジトリ反映」の最適解

### 推奨: Cloud Scheduled Tasks（Pro契約 + Web UI）

**理由**:
1. **マシン依存なし** — Anthropicクラウドで実行。PCオフでも動く
2. **YAML不要** — 自然言語プロンプトだけで定義可能
3. **GitHub連携済み** — リポジトリのclone→変更→PR作成が組み込み
4. **MCP Connectors** — Slack通知等の外部連携も可能
5. **定額課金** — Pro $20/月でスケジュールタスク利用可能
6. **管理が簡単** — Web UIで作成・編集・一時停止・履歴確認

**制約**:
- 最小間隔1時間（日次タスクなら十分）
- ローカルファイル不要のタスクに限定（GitHubリポジトリベース）
- library/ 等のローカル資産は参照不可（GitHubにpushされている必要あり）

### 代替案: GitHub Actions + claude-code-action

**向いているケース**:
- API従量課金で厳密にコスト管理したい
- 既存のCI/CDパイプラインに組み込みたい
- モデルを自由に選択したい（Sonnetでコスト最適化等）
- Bedrock/Vertex経由で利用したい

### 現環境（ローカルPC + タスクマネージャー）への適用

現在の library/ や skills-registry/ はローカル資産のため、Cloud Scheduled Tasksから直接アクセスできない。以下の対応が必要:

1. **library/ をGitHubリポジトリに含める** → Cloud Scheduled Taskで直接操作可能
2. **または**: ローカルPC起動中に Desktop Scheduled Task を使う
3. **または**: GitHub Actions + API で定期実行し、PRとして反映

---

## Sources

- [Run prompts on a schedule - Claude Code Docs](https://code.claude.com/docs/en/scheduled-tasks)
- [Schedule tasks on the web - Claude Code Docs](https://code.claude.com/docs/en/web-scheduled-tasks)
- [Claude Code GitHub Actions - Claude Code Docs](https://code.claude.com/docs/en/github-actions)
- [Run Claude Code programmatically - Claude Code Docs](https://code.claude.com/docs/en/headless)
- [Pricing - Claude API Docs](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude Code Web Guide](https://www.getaiperks.com/en/articles/claude-code-web)
- [anthropics/claude-code-action (GitHub)](https://github.com/anthropics/claude-code-action)
- [Claude Codeのスケジュールタスクの実例 (DevelopersIO)](https://dev.classmethod.jp/articles/claude-code-scheduled-tasks-github-triage/)
- [Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Plans & Pricing](https://claude.com/pricing)
