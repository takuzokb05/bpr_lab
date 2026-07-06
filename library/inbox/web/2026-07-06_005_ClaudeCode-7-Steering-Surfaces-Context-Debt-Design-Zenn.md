# Claude Code の指示をどこに書くか — 7つの指示面とコンテキスト負債の設計

- URL: https://zenn.dev/suwash/articles/claude-code-steering-surfaces_20260622
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-07-06

## 要約
Claude Code における指示記述場所（Steering Surface）を7種類に分類して整理した技術記事。CLAUDE.md / SKILL.md / hooks / MCP ツール説明 / インラインコメント / セッション内プロンプト / 環境変数の7面を用途・ライフタイム・コスト観点で比較。コンテキスト負債（不要な指示が溜まって指示精度が下がる問題）の設計回避策を論じる。長いCLAUDE.mdが200行超で遵守率が下がるという定量的根拠も引用。どの指示をどこに置くかの判断フレームワークとして実務に直結する内容。2026年6月22日公開。Claude Code を本格活用している開発者向けの上級記事。
