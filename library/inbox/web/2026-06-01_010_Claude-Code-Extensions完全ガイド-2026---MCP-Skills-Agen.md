# Claude Code Extensions完全ガイド 2026 — MCP・Skills・Agents・Hooks の違い

- URL: https://www.morphllm.com/claude-code-extensions
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-01

## 要約
morphllm.com がClaude Code拡張機能の4要素（MCP・Skills・Custom Agents・Hooks）を体系的に解説。
MCP servers: 外部ツール・APIへの接続（GitHub・Slack・PostgreSQL・Stripe等200以上）。
Skills: カスタムワークフローの教示とスラッシュコマンド登録（.md形式、トークン節約可能）。
Custom Agents: 独自のコンテキストでタスクを分離・委任。
Hooks: ライフサイクルイベント（pre-commit、post-tool call等）でシェルスクリプトを自動実行。
意思決定ルール: 毎ターン必要→CLAUDE.md、たまに使う手順→skill、自動実行→hook、メインコンテキストを埋める→subagent。
Pluginsはこれら複数をパッケージした配布単位として位置付けられている。
