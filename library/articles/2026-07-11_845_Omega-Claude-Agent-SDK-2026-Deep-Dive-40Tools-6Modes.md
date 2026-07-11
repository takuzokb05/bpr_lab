# Claude Agent SDK 2026 Deep Dive: 40ツール・30+フックイベント・6パーミッションモード

- URL: https://o-mega.ai/articles/claude-agent-sdk-the-2026-deep-dive
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-11

## 要約
Claude Agent SDKの2026年版技術詳細解説。APIラッパーではなく**サブプロセスモデル**が核心：`claude`バイナリをOS別プロセスとして起動しJSON-RPC via stdin/outで通信、アプリクラッシュでもエージェント状態が保持される。

**2026年新機能**:
- 40の統合ツール / 30以上のフックイベント
- Remote Routines: クラウドスケジューリング・GitHub event/HTTPトリガー（ローカルセッション不要）
- Agent Teams: 共有タスクリストでピアエージェント協調（`SendMessage`で直接通信）

**6段階パーミッションモード**:
| モード | 挙動 |
|--------|------|
| `default` | 読み込み自動承認、編集時プロンプト |
| `acceptEdits` | 一般ファイル操作を自動承認 |
| `plan` | 読み取り専用探索 |
| `auto` | AIが安全性を評価してから実行 |
| `dontAsk` | 明示allowlist外は自動拒否 |
| `bypassPermissions` | 全自動承認（`rm -rf /`と`~`を除く） |

マッチャー構文例：`Bash(npm run *)` / `Read(~/secrets/**)` / `WebFetch(domain:example.com)`

**CLAUDE.md階層**: managed policy → user → project → local override（サブディレクトリ単位でオンデマンドロード）

**セッション永続化**: `~/.claude/projects/<project-path>/`にJSONLトランスクリプトを保存、セッションIDで再開可能。

Pythonコード例：`ClaudeAgentOptions`で`allowed_tools`・`effort`・`max_budget_usd`・`can_use_tool`ラムダを指定する本番パターン。MCP接続はstdio/HTTP経由でツールが`mcp__<server>__<tool>`名前空間で出現。
