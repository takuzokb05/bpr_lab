# Hooks and MCP for Claude Code — Why This Matters（GoPenAI）

- URL: https://blog.gopenai.com/hooks-and-mcp-for-claude-code-7c535374cdf7
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-16

## 要約

Claude CodeのHooksとMCPは別システム。MCPはClaudeが到達できる外部ツールを拡張し、HooksはそのMCP callを含む全ライフサイクルイベントでClaudeの動作を制御（許可・拒否・ログ）する。Hook発火点：セッション開始・ツール使用・プロンプト送信・コンパクション。2026年プロダクション基準は「固定ソース＋制限的Hooks＋プロジェクト別サンドボックス」の3層。Skills・Hooks・Subagentsの3プリミティブがClaudeカスタマイズの全体像。安全なエージェント実装に必要な設計パターンを提示。
