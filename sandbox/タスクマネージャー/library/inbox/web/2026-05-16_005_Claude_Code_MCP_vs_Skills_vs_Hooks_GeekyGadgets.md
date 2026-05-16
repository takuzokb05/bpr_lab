# Claude Code MCP vs Skills vs Hooks: What You Need to Know

- URL: https://www.geeky-gadgets.com/claude-code-mcp-plugins-explained/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-16

## 要約
Geeky Gadgetsによる3つの拡張機能の違いを明確に整理した解説記事。MCPは外部システム接続（DB・API・Slack等）でJSON-RPC通信、Skillsは繰り返しワークフローをMarkdownで定義するスラッシュコマンド化の仕組み、Hooksはイベント駆動型でコード実行を保証する仕組み（Skillsと違いモデルが無視できない）。使い分けの指針：新しいデータソース接続→MCP、繰り返しプロセス→Skills、品質保証・セキュリティチェック→Hooks。Pluginはこれら全てをまとめるコンテナ。記事末にフローチャート形式の選択ガイドがあり実務で即使える。Hooksは「guarantee execution」という点でSkillsより強力だが設定コストが高い。
