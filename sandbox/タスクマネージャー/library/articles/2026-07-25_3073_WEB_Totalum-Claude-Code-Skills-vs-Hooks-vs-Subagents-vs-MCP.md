# Claude Code Skills 2026: Complete Guide vs Hooks, Subagents, and MCP

- URL: https://www.totalum.app/blog/claude-code-skills-totalum
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-25

## 投稿内容

TotalumによるClaude Code Skillsの完全ガイド。Skills vs Hooks vs Subagents vs MCPの使い分けを詳解。

## 要約

- Skills・Hooks・Subagents・MCPの4拡張手段の違いと使い分けを体系的に解説
- Skillsはメタデータのみ常時ロードされるため、多数のスキルを共存させながらコンテキスト消費を抑えられる
- 「Skills = 知識パック（on-demand instruction sets）」「Hooks = 決定論的な自動化」「Subagents = 委任境界」「MCP = 外部ツール・データ統合」という明確な役割分担
- Pluginsの概念: Skills + Subagents + MCP設定 + Hooksをひとつのインストール可能なパッケージに束ねたもの
- 2026年時点でのMCP公式レジストリには9,400以上のサーバーが登録されており、Claude Code・Cursor・Windsurf・VS Codeなど主要IDEで利用可能
- 実際のプロジェクトへの適用決定木（decision tree）形式で解説されており、どの手段を選ぶかの判断基準が明確
- Totalumはこれらの拡張機能を統合管理するプラットフォームとして2026年に登場したツール
