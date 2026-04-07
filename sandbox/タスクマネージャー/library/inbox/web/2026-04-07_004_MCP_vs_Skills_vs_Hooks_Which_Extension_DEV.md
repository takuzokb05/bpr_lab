# MCP vs Skills vs Hooks in Claude Code: Which Extension Do You Need?

- URL: https://dev.to/bruce_he/mcp-vs-skills-vs-hooks-in-claude-code-which-extension-do-you-need-3b8i
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-07

## 要約
Claude Codeの3つの拡張機構の使い分けを整理した比較記事。Hooks（ボトムレイヤー：ライフサイクルイベント自動化、「常に起きなければならないこと」）、Skills（ミドルレイヤー：再利用可能なドメイン知識・ワークフロー）、MCP（外部ツール接続、Figma・GitHub・Postgres等）という3層モデルを提示。CLAUDE.mdとの関係も整理：CLAUDE.md＝常時ロードされる広域ルール、Skills＝オンデマンドな専門知識。重要な設計ガイドライン：「何かが必ず起きなければならないなら→Hook、何かを覚えさせるなら→CLAUDE.md、ドメイン固有のワークフローなら→Skill、外部サービスが必要なら→MCP」。Claude Code拡張システムの全体像を短くまとめた一次情報として価値が高い。
