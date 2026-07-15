# Claude Code フルスタック完全解説: MCP・Skills・Subagents・Hooks の役割分担

- URL: https://alexop.dev/posts/understanding-claude-code-full-stack/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-29

## 要約
Claude Codeは「AIエージェント機能の完全なオーケストレーションフレームワーク」として位置づけられ、5層構造で機能する。CLAUDE.mdがプロジェクト記憶を管理し、MCP(Model Context Protocol)が外部ツールへのアクセスを提供、Skillsが再利用可能なワークフローを定義、Hooksが自動化トリガーを実現、Subagentsが並列処理を担う。CLAUDE.mdはエンタープライズ→ユーザー→プロジェクト→ディレクトリの階層でマージされる。Skills はディレクトリベースの拡張機能で自動実行可否をフロントマターで制御。Subagentsは独立コンテキストウィンドウを持つ専門化されたAIとして機能。Hooks は7つのライフサイクルイベントで反応。2026年以降のMCP進化で50以上のツール使用時のコンテキスト負荷が1桁削減。6プラットフォーム（CLI、VS Code、JetBrains、デスクトップ、Web、iOS）に対応する包括的な技術解説。
