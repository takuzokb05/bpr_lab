# Claude Code Hooks & MCP サーバー活用調査

調査日: 2026-02-21

---

## 1. Hooks（フック）の活用法

### 1.1 全フックイベント一覧

Claude Code は **15種類** のフックイベントをサポートしている。

| イベント | 発火タイミング | ブロック可能 |
|---------|--------------|:----------:|
| `SessionStart` | セッション開始・再開時 | No |
| `UserPromptSubmit` | ユーザーがプロンプト送信時（処理前） | Yes |
| `PreToolUse` | ツール実行前 | Yes |
| `PermissionRequest` | 許可ダイアログ表示時 | Yes |
| `PostToolUse` | ツール実行成功後 | No |
| `PostToolUseFailure` | ツール実行失敗後 | No |
| `Notification` | 通知送信時 | No |
| `SubagentStart` | サブエージェント起動時 | No |
| `SubagentStop` | サブエージェント完了時 | Yes |
| `Stop` | メインエージェント応答完了時 | Yes |
| `TeammateIdle` | チームメイトがアイドル状態になる直前 | Yes |
| `TaskCompleted` | タスク完了マーク時 | Yes |
| `ConfigChange` | 設定ファイル変更時 | Yes |
| `PreCompact` | コンテキスト圧縮前 | No |
| `SessionEnd` | セッション終了時 | No |

**ソース**: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)

### 1.2 現在のユーザー環境で使用中のフック

- `PreToolUse`: WebSearch/WebFetch の自動承認
- `Stop`: Slack通知
- `Notification`: Slack通知

### 1.3 すぐ使える実用的なフック

---

#### A. PostToolUse: 自動コードフォーマット（Prettier / Ruff）

**何ができるか**: Claude がファイルを編集・作成するたびに、自動でフォーマッタを実行する。LLM に「フォーマットして」と頼む必要がなくなり、確実にスタイル統一できる。

**具体的な設定例（Python + Ruff）**:

```json
// .claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs ruff format --quiet 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

**JavaScript/TypeScript の場合（Prettier）**:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

**メリット**: フォーマット忘れがゼロになる。コードレビュー時のスタイル指摘がなくなる。

**ソース**: [Claude Code Hooks: Complete Guide with 20+ Ready-to-Use Examples (2026)](https://aiorg.dev/blog/claude-code-hooks) / [Automate workflows with hooks](https://code.claude.com/docs/en/hooks-guide)

---

#### B. PreToolUse: 危険コマンドのブロック

**何ができるか**: `rm -rf`、`git push --force`、`.env` への書き込みなど、破壊的操作を事前に検出してブロックする。

**具体的な設定例**:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous.sh"
          }
        ]
      }
    ]
  }
}
```

**block-dangerous.sh の例**:

```bash
#!/bin/bash
COMMAND=$(jq -r '.tool_input.command')

# rm -rf をブロック
if echo "$COMMAND" | grep -q 'rm -rf'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "rm -rf コマンドはブロックされました"
    }
  }'
  exit 0
fi

# git push --force をブロック
if echo "$COMMAND" | grep -q 'git push.*--force'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "force push はブロックされました"
    }
  }'
  exit 0
fi

exit 0
```

**メリット**: LLM の判断ミスによるデータ損失を確実に防げる。

**ソース**: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)

---

#### C. PreToolUse: .env ファイルへの書き込み防止

**何ができるか**: `.env` や秘密鍵ファイルへの書き込みを防止する。

**具体的な設定例**:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "FILE=$(jq -r '.tool_input.file_path'); if echo \"$FILE\" | grep -qE '\\.(env|pem|key)$'; then echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"機密ファイルへの書き込みは禁止されています\"}}'; else exit 0; fi"
          }
        ]
      }
    ]
  }
}
```

**メリット**: 秘密情報の誤編集・漏洩を防げる。

---

#### D. PostToolUse: 非同期テスト実行

**何ができるか**: ファイル編集後にバックグラウンドでテストを実行し、結果をClaude に返す。Claude は待たずに作業を継続できる。

**具体的な設定例**:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests-async.sh",
            "async": true,
            "timeout": 300
          }
        ]
      }
    ]
  }
}
```

**run-tests-async.sh の例**:

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# テストファイルに対応するソースの変更のみ反応
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

RESULT=$(python -m pytest tests/ --tb=short 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "{\"systemMessage\": \"テスト全件PASS ($FILE_PATH 編集後)\"}"
else
  echo "{\"systemMessage\": \"テスト失敗 ($FILE_PATH 編集後): $RESULT\"}"
fi
```

**メリット**: 編集のたびにテスト結果がフィードバックされ、壊れたコードの早期発見ができる。`async: true` で作業をブロックしない。

**ソース**: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)

---

#### E. Stop: 品質ゲート（プロンプトベース）

**何ができるか**: Claude が作業完了を宣言する前に、LLM が「本当に完了か」を評価する。不十分なら作業を継続させる。

**具体的な設定例**:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "以下のコンテキストを確認し、全てのタスクが完了しているか判定してください: $ARGUMENTS\n\n判定基準:\n1. ユーザーが依頼した全項目が実装されているか\n2. エラーが残っていないか\n3. テストが必要な場合、実行されたか\n\nJSON形式で回答: {\"ok\": true} で完了を許可、{\"ok\": false, \"reason\": \"理由\"} で作業継続を指示。",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**メリット**: 作業の中途半端な完了を防げる。テスト実行忘れなどを検知。

**注意**: `stop_hook_active` を確認しないと無限ループの危険がある。プロンプトフックは Haiku モデルで実行されるためコストは低い。

**ソース**: [Claude Code: Part 8 - Hooks for Automated Quality Checks](https://www.letanure.dev/blog/2025-08-06--claude-code-part-8-hooks-automated-quality-checks) / [Claude Code — Use Hooks to Enforce End-of-Turn Quality Gates](https://blog.devgenius.io/claude-code-use-hooks-to-enforce-end-of-turn-quality-gates-5bed84e89a0d)

---

#### F. TaskCompleted: チームメイトの品質チェック

**何ができるか**: Agent Teams でチームメイトがタスク完了を宣言する前に、テストやlintを実行して品質を保証する。

**具体的な設定例**:

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/verify-task.sh"
          }
        ]
      }
    ]
  }
}
```

**verify-task.sh の例**:

```bash
#!/bin/bash
INPUT=$(cat)
TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task_subject')

# テスト実行
if ! python -m pytest tests/ --tb=short 2>&1; then
  echo "テストが失敗しています。修正してからタスクを完了してください: $TASK_SUBJECT" >&2
  exit 2
fi

exit 0
```

**メリット**: exit 2 でタスク完了をブロックし、修正を強制できる。

**ソース**: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)

---

#### G. SessionStart: 開発コンテキストの自動読み込み

**何ができるか**: セッション開始時に Git の状態、最近の変更、環境変数などを自動的にコンテキストに追加する。

**具体的な設定例**:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"現在のブランチ: $(git branch --show-current 2>/dev/null || echo 'N/A')\\n最近のコミット:\\n$(git log --oneline -5 2>/dev/null || echo 'N/A')\""
          }
        ]
      }
    ]
  }
}
```

**メリット**: 毎回「git status を見て」と言わなくても、Claude が現在の開発状況を把握した状態で作業を開始できる。

**ソース**: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)

---

### 1.4 フックの3種類のタイプ

| タイプ | 説明 | 用途 |
|--------|------|------|
| `command` | シェルコマンドを実行 | フォーマッタ、lint、ファイルチェック |
| `prompt` | LLM に単発の判定を依頼 | 品質ゲート、内容チェック |
| `agent` | サブエージェントを起動して多段階検証 | テスト実行確認、複雑な条件検証 |

**注意**: `prompt` と `agent` タイプは `Stop` と `SubagentStop` 等で利用可能。`async` は `command` タイプのみ対応。

### 1.5 フックの設定場所

| ファイル | スコープ | 共有可能 |
|---------|---------|:-------:|
| `~/.claude/settings.json` | 全プロジェクト | No |
| `.claude/settings.json` | 単一プロジェクト | Yes（Git） |
| `.claude/settings.local.json` | 単一プロジェクト | No |
| プラグインの `hooks/hooks.json` | プラグイン有効時 | Yes |
| スキル/エージェントの frontmatter | コンポーネント有効時 | Yes |

---

## 2. MCP サーバーの活用法

### 2.1 MCP とは

MCP（Model Context Protocol）は AI とツール連携のオープンスタンダード。Claude Code に外部ツール、DB、API を接続できる。

**ソース**: [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)

### 2.2 すぐ使える実用的な MCP サーバー

---

#### A. GitHub MCP サーバー

**何ができるか**: PR の作成・レビュー、Issue 管理、リポジトリ操作を Claude Code 内で直接実行。

**具体的な設定例**:

```bash
# Windows の場合
claude mcp add --transport http github https://api.githubcopilot.com/mcp/
```

認証が必要なので、追加後に Claude Code 内で `/mcp` コマンドを実行してブラウザ認証する。

**使用例**:
- 「PR #456 をレビューして改善を提案して」
- 「発見したバグの Issue を作成して」
- 「自分にアサインされた全 PR を見せて」

**メリット**: ターミナルとブラウザの行き来が不要。`gh` CLI より自然言語で操作できる。

**ソース**: [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp) / [Top 10 Essential MCP Servers for Claude Code](https://apidog.com/blog/top-10-mcp-servers-for-claude-code/)

---

#### B. Context7 — 最新ドキュメント参照

**何ができるか**: ライブラリ・フレームワークの最新ドキュメントとコード例を、バージョン指定で直接コンテキストに注入する。Claude の学習データが古くても、最新 API を正確に使える。

**具体的な設定例**:

```bash
# Windows の場合
claude mcp add --transport stdio context7 -- cmd /c npx -y @upstash/context7-mcp@latest
```

**使用例**:
- 「Context7 で Next.js 15 のルーティング方法を調べて」
- 「pandas 2.2 の新しい API を確認して」

**メリット**: 古い API や存在しない関数を使うハルシネーションを大幅に削減。

**ソース**: [Context7 GitHub](https://github.com/upstash/context7) / [Best MCP Servers for Claude Code](https://mcpcat.io/guides/best-mcp-servers-for-claude-code/)

---

#### C. Sentry — エラーモニタリング

**何ができるか**: 本番環境のエラーを Claude Code 内で直接確認・分析。スタックトレースの解析やエラー傾向の調査が可能。

**具体的な設定例**:

```bash
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
# その後 /mcp コマンドで OAuth 認証
```

**使用例**:
- 「過去24時間で最も多いエラーは？」
- 「エラー ID abc123 のスタックトレースを見せて」
- 「どのデプロイでこの新しいエラーが発生した？」

**メリット**: エラー調査 → コード修正をワンストップで完結。

**ソース**: [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)

---

#### D. PostgreSQL / データベース接続

**何ができるか**: 自然言語でデータベースにクエリを実行。テーブルスキーマの確認や分析クエリも可能。

**具体的な設定例**:

```bash
# Windows の場合
claude mcp add --transport stdio db -- cmd /c npx -y @bytebase/dbhub --dsn "postgresql://readonly:pass@localhost:5432/mydb"
```

**使用例**:
- 「今月の売上合計は？」
- 「orders テーブルのスキーマを見せて」
- 「90日以上購入のない顧客を検索」

**メリット**: SQL を手書きせずにデータ分析。読み取り専用ユーザーで接続すれば安全。

**ソース**: [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)

---

#### E. Notion MCP サーバー

**何ができるか**: Notion のページ・データベースに直接アクセス。ドキュメント参照、タスク管理、ナレッジベース検索が可能。

**具体的な設定例**:

```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
# その後 /mcp コマンドで OAuth 認証
```

**使用例**:
- 「Notion の設計ドキュメントを参照して実装して」
- 「今週のタスク一覧を見せて」

**メリット**: 設計ドキュメントと実装を直結。コンテキストスイッチ削減。

**ソース**: [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)

---

#### F. Playwright — ブラウザ自動化

**何ができるか**: ブラウザを自動操作してテスト実行、スクリーンショット取得、E2Eテスト。

**具体的な設定例**:

```bash
# Windows の場合
claude mcp add --transport stdio playwright -- cmd /c npx -y @playwright/mcp@latest
```

**使用例**:
- 「ログインフローが動作するかテストして」
- 「チェックアウトページのスクリーンショットを取って」

**メリット**: UI テストの自動化を自然言語で指示できる。

**ソース**: [Best MCP Servers for Claude Code](https://mcpcat.io/guides/best-mcp-servers-for-claude-code/)

---

### 2.3 MCP サーバーの管理コマンド

```bash
# サーバー追加（HTTP）
claude mcp add --transport http <名前> <URL>

# サーバー追加（stdio, Windows）
claude mcp add --transport stdio <名前> -- cmd /c npx -y <パッケージ名>

# 一覧表示
claude mcp list

# 詳細確認
claude mcp get <名前>

# 削除
claude mcp remove <名前>

# Claude Desktop からインポート
claude mcp add-from-claude-desktop

# 認証（Claude Code 内）
/mcp
```

### 2.4 MCP サーバーのスコープ

| スコープ | 保存先 | 用途 |
|---------|--------|------|
| `local`（デフォルト） | `~/.claude.json` | 個人の現プロジェクト用 |
| `project` | `.mcp.json`（Git管理） | チーム共有 |
| `user` | `~/.claude.json` | 個人の全プロジェクト用 |

```bash
# プロジェクト共有（.mcp.json に保存）
claude mcp add --transport http github --scope project https://api.githubcopilot.com/mcp/

# 全プロジェクトで使用
claude mcp add --transport http github --scope user https://api.githubcopilot.com/mcp/
```

### 2.5 Windows 固有の注意事項

Windows（WSL でない）環境では、`npx` を使う stdio サーバーは `cmd /c` ラッパーが必要:

```bash
# 正しい
claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package

# 間違い（"Connection closed" エラーになる）
claude mcp add --transport stdio my-server -- npx -y @some/package
```

---

## 3. ユーザー環境への推奨アクション

### 3.1 優先度: 高（すぐ導入可能）

| 推奨 | 種別 | 理由 |
|------|------|------|
| PostToolUse: Ruff 自動フォーマット | Hook | Python プロジェクト多数。コード品質が自動で保たれる |
| PreToolUse: .env 書き込みブロック | Hook | APIキー管理ポリシーの強制。既存ルールの自動化 |
| Context7 MCP サーバー | MCP | 最新ドキュメント参照でハルシネーション削減 |

### 3.2 優先度: 中（検討推奨）

| 推奨 | 種別 | 理由 |
|------|------|------|
| GitHub MCP サーバー | MCP | PR/Issue 管理の効率化。現在 `gh` CLI で対応可能だが自然言語操作が便利 |
| PostToolUse: 非同期テスト実行 | Hook | 編集のたびに自動テスト。品質向上 |
| TaskCompleted: テスト必須ゲート | Hook | Agent Teams でチームメイトの品質保証 |

### 3.3 優先度: 低（将来検討）

| 推奨 | 種別 | 理由 |
|------|------|------|
| Stop: プロンプトベース品質ゲート | Hook | 便利だが無限ループリスクあり。慎重に設定 |
| Sentry MCP サーバー | MCP | 本番運用開始後に有用 |
| PostgreSQL MCP サーバー | MCP | DB を使うプロジェクトで有用 |

---

## ソース一覧

- [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks) — 公式フックリファレンス（全15イベントの詳細）
- [Automate workflows with hooks - Claude Code Docs](https://code.claude.com/docs/en/hooks-guide) — 公式フックガイド
- [Connect Claude Code to tools via MCP - Claude Code Docs](https://code.claude.com/docs/en/mcp) — 公式MCPガイド
- [Claude Code Hooks: Complete Guide with 20+ Ready-to-Use Examples (2026)](https://aiorg.dev/blog/claude-code-hooks) — 20以上の実用例
- [Claude Code Hooks Complete Guide (February 2026 Edition)](https://smartscope.blog/en/generative-ai/claude/claude-code-hooks-guide/) — 2026年2月版ガイド
- [Claude Code: Part 8 - Hooks for Automated Quality Checks](https://www.letanure.dev/blog/2025-08-06--claude-code-part-8-hooks-automated-quality-checks) — 品質チェック自動化
- [Claude Code — Use Hooks to Enforce End-of-Turn Quality Gates](https://blog.devgenius.io/claude-code-use-hooks-to-enforce-end-of-turn-quality-gates-5bed84e89a0d) — Stop フック品質ゲート
- [Top 10 Essential MCP Servers for Claude Code (2026)](https://apidog.com/blog/top-10-mcp-servers-for-claude-code/) — MCP サーバー TOP10
- [Best MCP Servers for Claude Code](https://mcpcat.io/guides/best-mcp-servers-for-claude-code/) — MCP サーバーガイド
- [Context7 GitHub](https://github.com/upstash/context7) — Context7 公式リポジトリ
- [GitHub - disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) — フック実践集
- [Claude Code hooks blog - Anthropic](https://claude.com/blog/how-to-configure-hooks) — Anthropic 公式ブログ
