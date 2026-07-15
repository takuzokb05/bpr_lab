# Claude Codeフルスタック解説: MCP・Skills・Subagents・Hooksの役割分担

- URL: https://alexop.dev/posts/understanding-claude-code-full-stack/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-29

## 投稿内容
Claude Code is not just a coding tool — it is a complete orchestration framework for AI agent functionality. It is built around five layers: CLAUDE.md for project memory, MCP (Model Context Protocol) for external tool access, Skills for reusable workflows, Hooks for automation triggers, and Subagents for parallel processing. CLAUDE.md is merged hierarchically (enterprise → user → project → directory). Skills are directory-based extensions with frontmatter controlling auto-execution. Subagents operate with independent context windows as specialized AI personalities. Hooks react across 7 lifecycle extension events. MCP evolution in 2026 reduced context load for 50+ tool use by an order of magnitude. Available across 6 platforms: CLI, VS Code, JetBrains, desktop app, web, and iOS.

## 要約
Claude Codeは「AIエージェント機能の完全なオーケストレーションフレームワーク」として5層構造で機能する技術解説記事。CLAUDE.mdはエンタープライズ→ユーザー→プロジェクト→ディレクトリの階層でマージされプロジェクト記憶を管理。MCPが外部ツールへのアクセスを提供し、Skillsがディレクトリベースで再利用可能なワークフローを定義（フロントマターで自動実行制御）。Subagentsは独立コンテキストウィンドウを持つ専門化されたAIとして並列処理を担い、Hooksが7つのライフサイクルイベントで自動化を実現。2026年のMCP進化で50以上のツール使用時のコンテキスト負荷が1桁削減。CLI・VS Code・JetBrains・デスクトップ・Web・iOSの6プラットフォーム対応。各レイヤーの責任範囲を明確に整理した包括的技術解説として、Claude Codeアーキテクチャ理解の基礎資料となる。
