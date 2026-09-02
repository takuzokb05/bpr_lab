# My Claude Code Setup After 4 Months of Daily Use (2026)

- URL: https://okhlopkov.com/claude-code-setup-mcp-hooks-skills-2026/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-02

## 要約
4ヶ月間のClaude Code日常利用で構築した実践セットアップガイド。推奨構成：
- セットアップ方針: まず小さく始め、native installer→短いCLAUDE.md→1 MCPサーバー→1 deterministic hook→1 skill
- Hooks: PreToolUse/PostToolUseで決定論的ガードレール実装（src/外への書き込みブロック等）
- MCP: 必要最小限のスコープで接続（Playwright、GitHub、ファイルシステム）
- Skills: 繰り返しワークフローのみスキル化、description具体化が重要
- CLAUDE.md: 200行以内、「常時知るべき知識」のみ記載
- コスト管理: /compact・/clear・/rewindの使い分けでコンテキスト効率化
- 実際の生産性向上: コードレビュー・テスト作成・ドキュメント生成で特に効果大
