# MCP vs Skills vs Hooks in Claude Code: Which Extension Do You Need?

- URL: https://dev.to/bruce_he/mcp-vs-skills-vs-hooks-in-claude-code-which-extension-do-you-need-3b8i
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-07

## 要約

Claude Codeの3拡張機構の使い分けを3層モデルで整理：
- **Hooks（ボトムレイヤー）**: ライフサイクルイベント自動化。「常に起きなければならないこと」（フォーマット・lint・セキュリティチェック）。決定論的・100%実行保証
- **Skills（ミドルレイヤー）**: 再利用可能なドメイン知識・ワークフロー。オンデマンドロードでCLAUDE.mdを肥大化させない
- **MCP（外部ツール接続）**: Figma・GitHub・Postgres等への連携。外部サービスが必要な時のみ

CLAUDE.mdとの関係も整理：CLAUDE.md＝常時ロードの広域ルール、Skills＝必要時のみの専門知識。

設計判断フロー：「何かが必ず起きなければ→Hook、記憶させる→CLAUDE.md、ドメイン固有ワークフロー→Skill、外部サービス必要→MCP」。Claude Code拡張システム全体像を短く把握できる。
