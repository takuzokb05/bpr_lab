# Claude Code Function Hooks: Preview Behind a Flag

- URL: https://claudefa.st/blog/tools/hooks/function-hooks
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-11

## 要約
Claude Codeに新機能「Function Hooks」がフラグ付きプレビューとして登場。既存のLifecycle Hooks（ツール呼び出し前後・セッション開始/終了などのイベント）とは異なり、Function Hooksは特定の関数・ツール呼び出しに直接フックできる。従来のHooksが「いつ実行するか」を制御するのに対し、Function Hooksは「どの関数が呼ばれたとき」を細粒度で制御可能。用途例：特定MCPツールの実行前に追加バリデーション、外部APIコールの前後にログ記録、ファイル操作前の確認ダイアログなど。セキュリティ面でシンリンク経由のファイルアクセス問題（スキル/エージェント/フック内の宣言済みコンポーネントパスがシンリンクの場合、スキル外のファイルを読めるバグ）の修正も同時に実施済み。開発者は `~/.claude/settings.json` の `experimental` フラグで有効化可能。
