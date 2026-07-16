# Hooks and MCP for Claude Code — Why This Matters

- URL: https://blog.gopenai.com/hooks-and-mcp-for-claude-code-7c535374cdf7
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-16

## 要約

GoPenAI（2026年6月）のMedium記事。Claude CodeのHooks機能とMCPの違いと連携を解説。MCPはClaudeが到達できる外部ツールを拡張し、HooksはClaudeがそのツールで何をできるか（許可・拒否・ログ）を制御する。MCP callsを含む全てのライフサイクルイベント（セッション開始・ツール使用・プロンプト送信・コンパクション）をHooksでインターセプト可能。2026年のプロダクション基準は「固定ソース＋制限的Hooks＋プロジェクト別サンドボックス」の3層。HooksとMCPを組み合わせることで、エージェントの動作を安全かつ監査可能にする実装パターンを紹介。Skills・Hooks・Subagentsの3つのプリミティブがClaudeカスタマイズの全体像。
