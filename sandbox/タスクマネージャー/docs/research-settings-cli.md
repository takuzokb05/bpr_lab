# Claude Code 機能調査: Settings / CLI / 隠れた便利機能

調査日: 2026-02-21

---

## 1. settings.json の活用されていない設定

### 1.1 設定ファイルの階層と優先順位

設定は以下の優先順位で適用される（上が最優先）:

| 優先度 | ファイル | 用途 |
|--------|---------|------|
| 1 | `managed-settings.json`（システム配置） | IT管理者による組織統制 |
| 2 | CLIフラグ（`--model` 等） | セッション単位の上書き |
| 3 | `.claude/settings.local.json` | 個人のプロジェクト設定（gitignore推奨） |
| 4 | `.claude/settings.json` | チーム共有のプロジェクト設定 |
| 5 | `~/.claude/settings.json` | ユーザーグローバル設定 |

**メリット**: プロジェクト固有の設定と個人設定を分離できる。チーム共有設定は `.claude/settings.json`、個人の好みは `.claude/settings.local.json` に。

ソース: [Claude Code settings - 公式ドキュメント](https://code.claude.com/docs/en/settings)

---

### 1.2 モデル設定

```json
{
  "model": "claude-sonnet-4-6",
  "availableModels": ["sonnet", "opus", "haiku"],
  "alwaysThinkingEnabled": true
}
```

| 設定 | 説明 | メリット |
|------|------|---------|
| `model` | デフォルトモデルを上書き | コスト最適化（日常はsonnet、重要時のみopus） |
| `availableModels` | 使用可能モデルを制限 | チームで統一、意図しないモデル切替を防止 |
| `alwaysThinkingEnabled` | 拡張思考を常時ON | コード品質向上。セッション毎の手動切替が不要 |

**実用ポイント**: `availableModels` を managed settings で設定すると、組織全体でモデル選択を制限可能。

ソース: [Model configuration - 公式ドキュメント](https://code.claude.com/docs/en/model-config)

---

### 1.3 UI・表示カスタマイズ

```json
{
  "language": "japanese",
  "outputStyle": "Explanatory",
  "showTurnDuration": true,
  "spinnerVerbs": {
    "mode": "append",
    "verbs": ["考え中", "分析中"]
  },
  "spinnerTipsEnabled": true,
  "terminalProgressBarEnabled": true,
  "prefersReducedMotion": false
}
```

| 設定 | 説明 | メリット |
|------|------|---------|
| `language` | 応答言語の指定 | 日本語で指示しなくても日本語で返答 |
| `outputStyle` | 出力スタイル調整 | `"Explanatory"` で説明的に、`"Concise"` で簡潔に |
| `showTurnDuration` | ターン所要時間を表示 | パフォーマンス把握に有用 |
| `spinnerVerbs` | スピナー表示のカスタマイズ | 楽しい／チーム固有のメッセージ |

ソース: [Claude Code settings - 公式ドキュメント](https://code.claude.com/docs/en/settings)

---

### 1.4 パーミッション詳細設定

```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch",
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(git log *)",
      "Bash(git diff *)",
      "Read(~/.zshrc)"
    ],
    "ask": [
      "Bash(git push *)"
    ],
    "deny": [
      "Bash(curl *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ],
    "additionalDirectories": ["../docs/"],
    "defaultMode": "acceptEdits",
    "disableBypassPermissionsMode": "disable"
  }
}
```

**パーミッションルール構文**:
- `Tool` — そのツールの全使用にマッチ
- `Tool(pattern)` — ワイルドカード (`*`) 対応のパターンマッチ
- 評価順: `deny` -> `ask` -> `allow`（最初のマッチが適用）

| 設定 | 説明 |
|------|------|
| `defaultMode` | デフォルトのパーミッションモード（`acceptEdits` 等） |
| `additionalDirectories` | 作業ディレクトリ外へのアクセス許可 |
| `disableBypassPermissionsMode` | bypass モードの無効化（セキュリティ強化） |

ソース: [Claude Code settings - 公式ドキュメント](https://code.claude.com/docs/en/settings)

---

### 1.5 サンドボックス設定

```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["git", "docker"],
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org"],
      "allowLocalBinding": true,
      "httpProxyPort": 8080
    }
  }
}
```

**メリット**: OS レベルのファイルシステム・ネットワーク隔離。サンドボックス内ではパーミッション確認なしで自由に作業可能。`--dangerously-skip-permissions` よりも安全な自律モード。

ソース: [Claude Code settings - 公式ドキュメント](https://code.claude.com/docs/en/settings)

---

### 1.6 セッション管理

```json
{
  "cleanupPeriodDays": 20
}
```

| 設定 | 説明 | メリット |
|------|------|---------|
| `cleanupPeriodDays` | N日間非アクティブなセッションを自動削除（0で即時） | ディスク節約 |

---

### 1.7 MCP サーバー管理

```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["memory", "github"],
  "disabledMcpjsonServers": ["filesystem"],
  "allowedMcpServers": [{ "serverName": "github" }],
  "deniedMcpServers": [{ "serverName": "filesystem" }]
}
```

**メリット**: MCP サーバーの有効/無効をプロジェクト設定で制御。チーム全員に同じMCPツールセットを強制可能。

---

### 1.8 プラグイン管理

```json
{
  "enabledPlugins": {
    "formatter@acme-tools": true,
    "deployer@acme-tools": true,
    "analyzer@security-plugins": false
  },
  "extraKnownMarketplaces": {
    "acme-tools": {
      "source": { "source": "github", "repo": "acme-corp/claude-plugins" }
    }
  }
}
```

---

### 1.9 帰属表示（Attribution）

```json
{
  "attribution": {
    "commit": "Co-Authored-By: Claude <noreply@anthropic.com>",
    "pr": "Generated with Claude Code"
  }
}
```

**メリット**: コミットメッセージやPRの自動帰属表示をカスタマイズ可能。

---

### 1.10 カスタムステータスライン / ファイルサジェスト

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  },
  "fileSuggestion": {
    "type": "command",
    "command": "~/.claude/file-suggestion.sh"
  },
  "plansDirectory": "./plans"
}
```

| 設定 | 説明 | メリット |
|------|------|---------|
| `statusLine` | ターミナル下部にカスタム情報を表示 | コンテキスト使用量、ブランチ名、ビルド状態等を常時表示 |
| `fileSuggestion` | ファイル候補のカスタムコマンド | @ メンション時のファイル補完を拡張 |
| `plansDirectory` | プランファイルの保存先 | プラン管理の整理 |

---

## 2. 実験的機能フラグ（環境変数）

### 2.1 現在利用可能な環境変数

| 環境変数 | 値 | 説明 |
|---------|---|------|
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | `1` | マルチエージェントチーム機能（現在使用中） |
| `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` | `1` | 全ての実験的機能を無効化（安定動作が必要な場合） |
| `CLAUDE_CODE_ENABLE_TELEMETRY` | `1` | テレメトリを有効化 |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` | `1` | バックグラウンドタスクを無効化 |
| `CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION` | `false` | プロンプトサジェスト（入力補完）を無効化 |
| `CLAUDE_CODE_TASK_LIST_ID` | `my-project` | セッション間でタスクリストを共有（`~/.claude/tasks/` に保存） |
| `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` | `1` | `--add-dir` で追加したディレクトリの CLAUDE.md もロード |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | 数値 | スキル説明のコンテキスト内文字数上限を変更（デフォルト: ウィンドウの2%） |

**設定方法**: settings.json の `env` セクションで恒久的に設定可能:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
    "CLAUDE_CODE_TASK_LIST_ID": "my-project"
  }
}
```

ソース: [Claude Code Environment Variables - Medium](https://medium.com/@dan.avila7/claude-code-environment-variables-a-complete-reference-guide-41229ef18120), [GitHub Issue #11960](https://github.com/anthropics/claude-code/issues/11960)

---

## 3. CLI オプション

### 3.1 セッション管理フラグ

| フラグ | 短縮 | 説明 | 使用例 |
|--------|------|------|--------|
| `--continue` | `-c` | 直近の会話を再開 | `claude -c` |
| `--resume` | `-r` | セッションIDまたは名前で再開 | `claude -r "auth-refactor"` |
| `--fork-session` | — | 再開時に新しいセッションIDを生成 | `claude -c --fork-session` |
| `--from-pr` | — | GitHub PRにリンクされたセッションを再開 | `claude --from-pr 123` |
| `--teleport` | — | claude.ai のWebセッションをローカルに引き継ぐ | `claude --teleport` |
| `--worktree` | `-w` | 隔離された git worktree で起動 | `claude -w feature-auth` |
| `--session-id` | — | 特定のセッションIDを使用 | `claude --session-id "UUID"` |

**使い分けガイド**:
- 日常の90%: `claude -c`（直前のセッション再開）
- 複数セッション管理: `claude -r`（選択画面）
- クロスプラットフォーム: `--teleport`

ソース: [CLI reference - 公式ドキュメント](https://code.claude.com/docs/en/cli-reference)

---

### 3.2 モデル・出力制御フラグ

| フラグ | 説明 | 使用例 |
|--------|------|--------|
| `--model` | セッションのモデルを指定 | `claude --model opus` |
| `--fallback-model` | オーバーロード時のフォールバック（printモード） | `claude -p --fallback-model sonnet "query"` |
| `--output-format` | 出力形式: `text` / `json` / `stream-json` | `claude -p "query" --output-format json` |
| `--json-schema` | JSONスキーマに基づく構造化出力 | `claude -p --json-schema '{...}' "query"` |
| `--max-budget-usd` | API費用上限 | `claude -p --max-budget-usd 5.00 "query"` |
| `--max-turns` | エージェントターン数制限 | `claude -p --max-turns 3 "query"` |
| `--verbose` | 詳細ログ出力 | `claude --verbose` |
| `--debug` | デバッグモード（カテゴリフィルタ可） | `claude --debug "api,mcp"` |

---

### 3.3 システムプロンプト制御

| フラグ | 動作 | モード |
|--------|------|--------|
| `--system-prompt` | デフォルトプロンプトを**完全置換** | Interactive + Print |
| `--system-prompt-file` | ファイルから読んで完全置換 | Print のみ |
| `--append-system-prompt` | デフォルトに**追記** | Interactive + Print |
| `--append-system-prompt-file` | ファイルから追記 | Print のみ |

**推奨**: 通常は `--append-system-prompt` を使用（Claude Codeのデフォルト機能を保持しつつ追加指示）。

---

### 3.4 パーミッション・ツール制御

| フラグ | 説明 | 使用例 |
|--------|------|--------|
| `--allowedTools` | 許可ツールを追加指定 | `"Bash(git log *)" "Read"` |
| `--disallowedTools` | 特定ツールを完全無効化 | `"Bash(git log *)" "Edit"` |
| `--tools` | 使用可能ツールを制限（`""` で全無効） | `claude --tools "Bash,Edit,Read"` |
| `--permission-mode` | パーミッションモードで起動 | `claude --permission-mode plan` |
| `--dangerously-skip-permissions` | 全パーミッション確認をスキップ | `claude --dangerously-skip-permissions` |

---

### 3.5 サブエージェント動的定義（`--agents`）

```bash
claude --agents '{
  "code-reviewer": {
    "description": "コードレビュー専門",
    "prompt": "セキュリティ・品質・ベストプラクティスに焦点を当てたレビューを行う",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  },
  "debugger": {
    "description": "デバッグ専門",
    "prompt": "エラー分析、根本原因の特定、修正案の提示を行う"
  }
}'
```

**フィールド**:
- `description`（必須）: エージェントの用途
- `prompt`（必須）: システムプロンプト
- `tools`: 使用可能ツール配列
- `model`: モデル（`sonnet` / `opus` / `haiku` / `inherit`）
- `skills`: プリロードするスキル名配列
- `mcpServers`: MCP サーバー配列
- `maxTurns`: 最大ターン数

ソース: [CLI reference - 公式ドキュメント](https://code.claude.com/docs/en/cli-reference)

---

### 3.6 パイプ入力・自動化

```bash
# ファイル内容を解析
cat error.log | claude -p "エラーの原因を分析して"

# 構造化出力でスクリプト連携
claude -p "APIエンドポイント一覧" --output-format json

# ストリーミングJSON
claude -p "ログを分析" --output-format stream-json

# Git エイリアス
git config --global alias.ai \
  '!claude -p "変更内容から簡潔なコミットメッセージを生成" --input-format diff < /dev/stdin'

# ファンアウトパターン（大量ファイル処理）
for file in $(cat files.txt); do
  claude -p "Migrate $file from React to Vue." \
    --allowedTools "Edit,Bash(git commit *)"
done
```

ソース: [Best Practices - 公式ドキュメント](https://code.claude.com/docs/en/best-practices)

---

### 3.7 その他のCLIフラグ

| フラグ | 説明 |
|--------|------|
| `--add-dir` | 追加ワーキングディレクトリ |
| `--agent` | 特定エージェントでセッション開始 |
| `--chrome` / `--no-chrome` | Chrome ブラウザ統合の有効/無効 |
| `--init` / `--init-only` | 初期化フック実行 |
| `--mcp-config` | MCP設定ファイルの読み込み |
| `--remote` | claude.ai上でWebセッション作成 |
| `--teammate-mode` | チームメイト表示方法（`auto` / `in-process` / `tmux`） |
| `--plugin-dir` | プラグインディレクトリの追加 |
| `--no-session-persistence` | セッション保存を無効化 |
| `--disable-slash-commands` | スキル・スラッシュコマンドを無効化 |
| `--setting-sources` | 設定ソースの選択（`user,project,local`） |

---

## 4. スラッシュコマンド完全リスト

### 4.1 組み込みコマンド

| コマンド | 説明 | 実用ポイント |
|---------|------|------------|
| `/clear` | 会話履歴をクリア | **タスク切替時に必須。コンテキスト汚染防止** |
| `/compact [指示]` | 会話を圧縮（指示でフォーカス指定可能） | `/compact APIの変更に焦点を当てて` |
| `/config` | 設定インターフェース | GUIでの設定変更 |
| `/context` | コンテキスト使用量をカラーグリッドで可視化 | **定期的にチェック推奨** |
| `/cost` | トークン使用統計 | セッションのコスト確認 |
| `/copy` | 直前のアシスタント応答をクリップボードにコピー | 出力の共有に便利 |
| `/debug [説明]` | セッションデバッグログを読んでトラブルシュート | 問題発生時に |
| `/desktop` | CLIセッションをDesktopアプリに引き継ぎ | macOS / Windows |
| `/doctor` | インストール状態のヘルスチェック | 設定の問題診断 |
| `/exit` | REPL終了 | — |
| `/export [filename]` | 会話をファイルまたはクリップボードにエクスポート | 会話の保存・共有 |
| `/help` | ヘルプ表示 | — |
| `/init` | CLAUDE.md を自動生成 | **新プロジェクトで最初に実行** |
| `/mcp` | MCP サーバー管理・OAuth認証 | — |
| `/memory` | CLAUDE.md ファイルの編集 | — |
| `/model` | モデル選択・切替（Opus 4.6では左右矢印でエフォートレベル調整） | **即座に反映** |
| `/permissions` | パーミッション表示・更新 | — |
| `/plan` | プランモードに直接入る | `Shift+Tab` でも切替可能 |
| `/rename <name>` | セッションに名前を付ける | `claude -r` で探しやすくなる |
| `/resume [session]` | セッション再開 | IDまたは名前で指定 |
| `/rewind` | 会話・コードを以前の状態に巻き戻し or サマリー | `Esc+Esc` でも起動可 |
| `/stats` | 日次利用状況、セッション履歴、ストリーク、モデル使用を可視化 | — |
| `/status` | バージョン、モデル、アカウント、接続状態 | — |
| `/statusline` | ステータスラインUIの設定 | — |
| `/tasks` | バックグラウンドタスクの一覧・管理 | — |
| `/teleport` | claude.ai のリモートセッションを再開 | — |
| `/theme` | カラーテーマ変更 | — |
| `/todos` | TODO一覧 | — |
| `/usage` | プラン利用制限・レートリミット状態 | サブスクリプション用 |
| `/vim` | Vimモード有効化 | — |
| `/keybindings` | キーバインド設定ファイルを開く | — |
| `/terminal-setup` | ターミナル設定（Shift+Enter等のバインディング） | — |

ソース: [Interactive mode - 公式ドキュメント](https://code.claude.com/docs/en/interactive-mode)

---

## 5. キーボードショートカット

### 5.1 一般操作

| ショートカット | 説明 | 備考 |
|--------------|------|------|
| `Ctrl+C` | 現在の入力/生成をキャンセル | 予約済み、再バインド不可 |
| `Ctrl+D` | セッション終了 | 予約済み、再バインド不可 |
| `Ctrl+F` | 全バックグラウンドエージェントを停止 | 3秒以内に2回押しで確認 |
| `Ctrl+G` | デフォルトテキストエディタで開く | プロンプト編集やカスタム応答に |
| `Ctrl+L` | ターミナル画面クリア | 会話履歴は保持 |
| `Ctrl+O` | 詳細出力の切替 | ツール使用・実行の詳細表示 |
| `Ctrl+R` | コマンド履歴の逆方向検索 | インタラクティブ検索 |
| `Ctrl+V` / `Alt+V`(Win) | クリップボードから画像貼り付け | スクリーンショット投入に |
| `Ctrl+B` | 実行中タスクをバックグラウンドに | tmuxユーザーは2回押し |
| `Ctrl+T` | タスクリスト表示の切替 | 最大10タスク表示 |
| `Esc` | 生成を停止 | コンテキストは保持 |
| `Esc + Esc` | 巻き戻し/サマリーメニュー | コード・会話の復元 |
| `Shift+Tab` / `Alt+M` | パーミッションモード切替 | Auto-Accept / Plan / Normal |
| `Alt+P`(Win) / `Option+P`(Mac) | モデル切替 | プロンプトをクリアせずに |
| `Alt+T`(Win) / `Option+T`(Mac) | 拡張思考の切替 | `/terminal-setup` 実行後に使用可能 |

### 5.2 テキスト編集

| ショートカット | 説明 |
|--------------|------|
| `Ctrl+K` | 行末まで削除 |
| `Ctrl+U` | 行全体を削除 |
| `Ctrl+Y` | 削除したテキストを貼り付け |
| `Alt+Y`（`Ctrl+Y` の後） | 貼り付け履歴を循環 |
| `Alt+B` | 1単語後方に移動 |
| `Alt+F` | 1単語前方に移動 |

### 5.3 マルチライン入力

| 方法 | ショートカット | 対応環境 |
|------|-------------|---------|
| バックスラッシュ | `\` + `Enter` | 全ターミナル |
| Option+Enter | `Option+Enter` | macOSデフォルト |
| Shift+Enter | `Shift+Enter` | iTerm2, WezTerm, Ghostty, Kitty |
| Ctrl+J | `Ctrl+J` | 全ターミナル |
| ペースト | 直接ペースト | コードブロック・ログに |

### 5.4 クイック入力

| 入力 | 説明 |
|------|------|
| `/` | スラッシュコマンド/スキル起動 |
| `!` | Bash直接実行モード（Claude解釈なし） |
| `@` | ファイルパスオートコンプリート |

### 5.5 キーバインドのカスタマイズ

`~/.claude/keybindings.json` で全ショートカットをカスタマイズ可能:

```json
{
  "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
  "bindings": [
    {
      "context": "Chat",
      "bindings": {
        "ctrl+e": "chat:externalEditor",
        "ctrl+u": null
      }
    }
  ]
}
```

変更は自動検出され、再起動不要で反映。`/doctor` で警告確認可能。

ソース: [Customize keyboard shortcuts - 公式ドキュメント](https://code.claude.com/docs/en/keybindings), [Interactive mode - 公式ドキュメント](https://code.claude.com/docs/en/interactive-mode)

---

## 6. コンテキスト管理のベストプラクティス

### 6.1 核心原則

> **Claude のコンテキストウィンドウは最も重要なリソース。コンテキストが埋まるとパフォーマンスが劣化する。**

### 6.2 `/compact` の効果的な使い方

```
/compact                           # 自動要約
/compact APIの変更に焦点を当てて      # フォーカス指定
/compact 修正済みファイル一覧とテストコマンドを保持  # 保持指定
```

- **自動コンパクション**: コンテキスト上限に近づくと自動発動。コードパターン・ファイル状態・重要な決定が保持される
- **手動コンパクション**: `/compact <指示>` でフォーカスを指定可能
- **部分サマリー**: `Esc+Esc` / `/rewind` から特定メッセージ以降のみをサマリー化

**CLAUDE.md でのコンパクション制御**:
```markdown
コンパクション時は、修正済みファイルの完全リストとテストコマンドを常に保持すること
```

### 6.3 `/clear` の使い分け

| タイミング | 推奨 |
|-----------|------|
| 無関係なタスクへの切替 | `/clear` |
| 2回以上の修正指示が失敗 | `/clear` + より良い初期プロンプト |
| 長時間の調査後の実装開始 | `/clear`（調査結果はメモに残す） |
| 同一タスクの継続 | クリア不要 |

### 6.4 サブエージェントによるコンテキスト保護

```
サブエージェントを使って認証システムのトークンリフレッシュの仕組みを調査して。
既存のOAuthユーティリティも確認して。
```

**効果**: サブエージェントは独立したコンテキストウィンドウで動作し、サマリーのみを返す。メインコンテキストの消費を最小限に抑える。

### 6.5 コンテキスト使用量の監視

```
/context    # カラーグリッドで可視化
```

フレッシュセッション・モノレポでのベースラインコスト: 約20kトークン（10%）。残りが作業に使用可能。

### 6.6 CLAUDE.md のベストプラクティス

**含めるべきもの**:
- Claude が推測できない Bash コマンド
- デフォルトと異なるコードスタイル規則
- テスト手順・テストランナー
- リポジトリの慣例（ブランチ命名、PR規約）
- アーキテクチャ決定
- 環境固有の注意事項
- よくある落とし穴

**含めるべきでないもの**:
- コードを読めば分かること
- 標準的な言語規約（Claudeは既知）
- 詳細なAPIドキュメント（リンクで十分）
- 頻繁に変わる情報
- 長い説明やチュートリアル
- ファイル毎の説明
- 「きれいなコードを書く」等の自明な指示

**Progressive Disclosure**: 全情報を事前に与えるのではなく、情報の**見つけ方**を教える:
```markdown
API設計の規約については @docs/api-conventions.md を参照
テスト手順は @docs/testing.md を参照
```

**重要度の強調**: `IMPORTANT` や `YOU MUST` で遵守率を向上させる。

ソース: [Best Practices - 公式ドキュメント](https://code.claude.com/docs/en/best-practices)

---

## 7. Hooks 設定

### 7.1 フックの種類

| フック | タイミング | 主な用途 |
|--------|----------|---------|
| `PreToolUse` | ツール実行前 | バリデーション、ブロック |
| `PostToolUse` | ツール成功後 | フォーマッター、リンター実行 |
| `PostToolUseFailure` | ツール失敗後 | エラー処理 |
| `Notification` | 通知送信時 | カスタム通知 |
| `Stop` | 応答完了時 | 自動アクション |
| `SubagentStop` | サブエージェント完了時 | 後処理 |
| `TaskCompleted` | タスク完了時 | 完了通知 |
| `UserPromptSubmit` | ユーザー入力送信時 | 入力バリデーション |
| `PermissionRequest` | パーミッション要求時 | 自動承認/拒否 |

### 7.2 実用的な設定例

**ファイル編集後にPrettierを自動実行**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "npx prettier --write \"$FILE_PATH\""
      }
    ]
  }
}
```

**特定ディレクトリへの書き込みをブロック**:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "python ~/.claude/hooks/block-migrations.py"
      }
    ]
  }
}
```

**LLMベースのプロンプトフック**（`type: "prompt"`）: AIを使ってアクションの許可/ブロックを判定。

ソース: [Hooks reference - 公式ドキュメント](https://code.claude.com/docs/en/hooks), [Claude Code Hooks - DataCamp](https://www.datacamp.com/tutorial/claude-code-hooks)

---

## 8. 隠れた便利機能

### 8.1 `!` Bash モード

プロンプト先頭に `!` を付けると、Claudeの解釈なしで直接シェルコマンドを実行。出力は会話コンテキストに追加される:
```
! npm test
! git status
! ls -la
```
Tabキーで過去の `!` コマンドからオートコンプリート。

### 8.2 `@` ファイルメンション

ファイルパスを `@` で参照すると、Claudeが応答前にファイルを読み込む。ファイルの場所を説明する必要がない。

### 8.3 拡張思考トリガー

スキルやプロンプト内に `"ultrathink"` というキーワードを含めると、最大の思考バジェット（31,999トークン）が発動。複雑な推論タスクに有効。

### 8.4 プロンプトサジェスト

Claudeの応答後、グレーアウトされた次のアクション候補が表示される。Tabで受け入れ、Enterで受け入れて送信。プロンプトキャッシュを再利用するため追加コストは最小限。

### 8.5 PR レビューステータス表示

開いているPRがあるブランチで作業中、フッターにPRリンクが表示（`PR #446`）。色付きアンダーラインでレビュー状態を表示:
- 緑: 承認済み
- 黄: レビュー待ち
- 赤: 変更要求
- 灰: ドラフト
- 紫: マージ済み

### 8.6 Git Worktree による並列セッション

```bash
claude -w feature-auth    # 隔離されたworktreeで起動
```

各セッションが独立したworktreeで動作。並列開発・実験に最適。

### 8.7 インタビューパターン

```
[簡潔な説明] を作りたい。AskUserQuestion ツールを使って詳細にインタビューして。

技術実装、UI/UX、エッジケース、懸念点、トレードオフについて質問して。
自明な質問は避け、見落としがちな難しい部分を掘り下げて。

全てカバーしたら SPEC.md に完全な仕様書を書いて。
```

仕様完成後、フレッシュセッションで実装を開始するのが推奨パターン。

### 8.8 Writer/Reviewer パターン

| セッション A（Writer） | セッション B（Reviewer） |
|----------------------|------------------------|
| `APIのレートリミッターを実装` | — |
| — | `@src/middleware/rateLimiter.ts のレートリミッター実装をレビュー。エッジケース、レース条件、既存ミドルウェアとの整合性を確認` |
| `レビューフィードバック: [B の出力]。指摘を修正して` | — |

### 8.9 Ctrl+G エディタ連携

プロンプト入力中に `Ctrl+G` を押すとデフォルトテキストエディタ（`$EDITOR`）が開く。複雑なプロンプトの編集、長文の入力、プランの直接編集に便利。

ソース: [Best Practices - 公式ドキュメント](https://code.claude.com/docs/en/best-practices), [Interactive mode - 公式ドキュメント](https://code.claude.com/docs/en/interactive-mode)

---

## 9. すぐ適用できる推奨設定（ユーザー環境向け）

### 9.1 `~/.claude/settings.json` に追加推奨

```json
{
  "permissions": {
    "allow": ["WebSearch", "WebFetch"]
  },
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "language": "japanese",
  "showTurnDuration": true,
  "alwaysThinkingEnabled": true
}
```

**追加のポイント**:
- `language`: 毎回日本語で指示しなくてもよくなる
- `showTurnDuration`: 応答時間の把握
- `alwaysThinkingEnabled`: 品質向上（特にopusとの組合せ）

### 9.2 プロジェクト別 `.claude/settings.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(python -m pytest *)",
      "Bash(npm run *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)"
    ]
  }
}
```

### 9.3 よく使うCLIコマンド

```bash
# セッション管理
claude -c                    # 直前のセッション再開
claude -r "session-name"     # 名前付きセッション再開
claude --model opus          # Opusで起動

# 自動化
claude -p "query" --output-format json    # スクリプト連携
claude -p --max-budget-usd 3.00 "query"   # コスト制限付き
cat file.log | claude -p "分析して"         # パイプ入力

# コンテキスト管理
/context                     # 使用量確認
/compact APIの変更に集中       # フォーカス指定で圧縮
/clear                       # タスク間でリセット
```

---

## ソース一覧

- [Claude Code settings - 公式ドキュメント](https://code.claude.com/docs/en/settings)
- [CLI reference - 公式ドキュメント](https://code.claude.com/docs/en/cli-reference)
- [Interactive mode - 公式ドキュメント](https://code.claude.com/docs/en/interactive-mode)
- [Customize keyboard shortcuts - 公式ドキュメント](https://code.claude.com/docs/en/keybindings)
- [Best Practices - 公式ドキュメント](https://code.claude.com/docs/en/best-practices)
- [Slash commands / Skills - 公式ドキュメント](https://code.claude.com/docs/en/slash-commands)
- [Model configuration - 公式ドキュメント](https://code.claude.com/docs/en/model-config)
- [Hooks reference - 公式ドキュメント](https://code.claude.com/docs/en/hooks)
- [Claude Code Environment Variables - Medium](https://medium.com/@dan.avila7/claude-code-environment-variables-a-complete-reference-guide-41229ef18120)
- [A developer's guide to settings.json - eesel.ai](https://www.eesel.ai/blog/settings-json-claude-code)
- [Claude Code Hooks - DataCamp](https://www.datacamp.com/tutorial/claude-code-hooks)
- [Hidden Claude Code Commands - petegypps.uk](https://www.petegypps.uk/blog/claude-code-hidden-commands-complete-guide-secret-features)
- [Shipyard Claude Code CLI Cheatsheet](https://shipyard.build/blog/claude-code-cheat-sheet/)
- [GitHub Issue #11960 - CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS](https://github.com/anthropics/claude-code/issues/11960)
