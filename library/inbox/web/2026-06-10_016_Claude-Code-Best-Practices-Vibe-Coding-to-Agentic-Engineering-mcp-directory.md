# Claude Code Best Practices: From Vibe Coding to Agentic Engineering (2026)

- URL: https://mcp.directory/blog/claude-code-best-practices
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-10

## 要約
mcp.directoryが公開したClaude Codeベストプラクティスガイド（2026年版）。「Vibe Coding」から「Agentic Engineering」への移行をテーマに、5層アーキテクチャ（CLAUDE.md・MCP servers・skills・hooks・subagents）を解説。Hooksは「決定論的に毎回実行すべき処理」に使い、CLAUDE.mdは「毎ターン真であるべき命令」に限定するという明確な使い分け指針を示す。Skillsは「時々だけ必要な手順」に、subagentsは「メインコンテキストを汚染したくないリサーチや作業」に使うという設計パターンを提示。CLAUDE.md内のルールはstable（安定したルール）のみ残し、pathsにglob指定して関連ファイルのみ読み込む分割管理を推奨。実践的なHook設定例（PreToolUse/PostToolUse/UserPromptSubmit）も含む。
