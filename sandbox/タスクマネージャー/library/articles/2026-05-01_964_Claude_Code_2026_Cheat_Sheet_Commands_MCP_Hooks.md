# Claude Code 2026 完全チートシート: Slash Commands・MCP・Hooks・Shortcuts

- URL: https://techbytes.app/posts/claude-code-2026-cheat-sheet-hooks-mcp-commands/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-01

## 要約
2026年版Claude Code全機能チートシート。主要情報：(1) 必須スラッシュコマンド—`/doctor`（診断）、`/cost`（トークン内訳）、`/plan`（実行前承認モード）、`/memory`（永続コンテキスト管理）。(2) MCP設定—クラウドツールは`--transport http`、ローカルは`--transport stdio`（SSEは廃止予定）。(3) フック設定—`settings.json`のJSON定義で`PreToolUse`・`PostToolUse`・新規`FileChanged`/`CwdChanged`イベントをポーリングなしで自動化。(4) モデル切り替え—`opusplan`エイリアスでプランニングをOpus・実行をSonnetに分離。(5) キーボードショートカット—`Alt+P`モデル切替、`Alt+T`拡張思考、`Alt+O`Fastモード、`Shift+Tab`Permissionモードサイクル。(6) セーフティ—`settings.json`に`defaultMode: "plan"`と`deny`ルール(`Bash(rm -rf *)`)を設定。コマンドリファレンスとして実用性高い。
