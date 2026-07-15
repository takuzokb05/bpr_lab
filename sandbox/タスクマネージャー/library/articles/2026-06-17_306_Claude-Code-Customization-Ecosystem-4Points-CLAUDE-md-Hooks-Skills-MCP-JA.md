# Claude Codeカスタマイズ生態系：CLAUDE.md・Hooks・Skills・MCP 4拡張点の設計戦略（JA）

- URL: https://zenn.dev/76hata/articles/claude-code-customization-ecosystem
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-06-17

## 要約
ZennのClaude Code設計論記事。4つの拡張点（CLAUDE.md=コンテキスト永続化、Hooks=決定論的実行、Skills=手順パッケージ化、MCP=外部ツール接続）をシステマティックに整理。実装知見：カスタムコマンド（.claude/commands/deploy.md）とSkills（.claude/skills/deploy/SKILL.md）は両方とも/deployを生成して等価に機能。プロジェクト別.claude配置でチーム間の設定分離が可能。.mcp.jsonをリポジトリに含めることでチーム標準MCP設定を共有。「CLAUDE.mdはAgentに世界の見え方を教える場所であり、自己紹介の場所ではない」という設計哲学が核心。
