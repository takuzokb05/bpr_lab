# Claude Code の指示をどこに書くか — 7つの指示面とコンテキスト負債の設計

- URL: https://zenn.dev/suwash/articles/claude-code-steering-surfaces_20260622
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-07-06

## 投稿内容
Claude Code における指示記述場所（Steering Surface）を7種類に分類。CLAUDE.md / SKILL.md / hooks / MCP ツール説明 / インラインコメント / セッション内プロンプト / 環境変数の7面を用途・ライフタイム・コスト観点で比較。コンテキスト負債（不要な指示が溜まって指示精度が下がる問題）の設計回避策を論じる。CLAUDE.mdが200行超で遵守率が下がるという定量的根拠も引用。どの指示をどこに置くかの判断フレームワークとして実務に直結する内容。2026年6月22日公開。

## 要約
Claude Code の7つの指示記述場所（Steering Surface）を分類・比較した上級技術記事。CLAUDE.md・SKILL.md・hooks・MCP ツール説明・インラインコメント・セッション内プロンプト・環境変数の用途・ライフタイム・コストを整理。コンテキスト負債（不要指示蓄積による精度低下）の設計回避策を論じ、CLAUDE.md が200行超で遵守率が落ちる定量根拠も引用。どの指示をどこに置くかの判断フレームワークを提供する実践的記事。Claude Code 本格活用者必読。
