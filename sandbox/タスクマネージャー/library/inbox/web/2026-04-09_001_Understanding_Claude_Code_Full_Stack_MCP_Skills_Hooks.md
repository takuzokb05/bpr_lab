# Understanding Claude Code's Full Stack: MCP, Skills, Subagents, and Hooks Explained

- URL: https://alexop.dev/posts/understanding-claude-code-full-stack/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-09

## 要約
Claude Codeの拡張システム全体を体系的に解説した技術記事。MCPサーバー・Skills・Subagents・Hooksの4レイヤーがどのように連携するかをアーキテクチャ視点で説明。Hooks（底層：ライフサイクルイベント自動化）、MCP（中層：外部ツール接続）、Skills（上層：再利用可能ワークフロー）の三層構造を明確化。サブエージェントはメインエージェントから独立したコンテキストウィンドウで動作し、フォーク型並列実行を可能にする点を解説。実務では「2〜3 MCPサーバー + 数個のカスタムSkill」が最も費用対効果が高いと結論。各レイヤーの使い分け判断フローを図示しており、Claude Codeエコシステム全体の理解に役立つ一次情報。
