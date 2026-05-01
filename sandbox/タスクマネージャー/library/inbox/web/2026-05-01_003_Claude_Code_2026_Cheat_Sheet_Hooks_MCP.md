# Claude Code 2026 Complete Cheat Sheet: Slash Commands, MCP, Hooks & Shortcuts

- URL: https://techbytes.app/posts/claude-code-2026-cheat-sheet-hooks-mcp-commands/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-01

## 要約
2026年版Claude Code全機能チートシート。主要内容：(1) `/doctor`（診断）、`/cost`（トークン内訳表示）、`/plan`（実行前承認モード）、`/memory`（永続コンテキスト管理）の必須スラッシュコマンド。(2) MCP設定：クラウドツールは`--transport http`、ローカルは`--transport stdio`（SSEは廃止予定）。(3) Hooksは`settings.json`のJSON定義で`PreToolUse`・`PostToolUse`・新規追加の`FileChanged`/`CwdChanged`イベントを設定。(4) `opusplan`エイリアスでプランニングはOpus・実行はSonnetという組み合わせ。(5) ショートカット：`Alt+P`でモデル切替、`Alt+T`で拡張思考、`Alt+O`でFastモード、`Shift+Tab`でPermissionモードサイクル。(6) `settings.json`で`defaultMode: "plan"`と`deny`ルール設定によるセーフティ強化。コマンドリファレンス形式で実用性が高い。
