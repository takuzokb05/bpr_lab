# GitHub: steipete/claude-code-mcp - Claude Code as MCP Server

- URL: https://github.com/steipete/claude-code-mcp
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-04

## 要約
Peter Steinberger（steipete）氏によるClaude Code自体をMCPサーバーとして公開するプロジェクト。「Agent in your Agent」というコンセプトで、Claude CodeのCodebase探索・ファイル編集・シェル実行などの能力を他のAIエージェントやMCPクライアントから呼び出し可能にする。これにより既存のMCPクライアント（Claude Desktop等）がClaude Codeのエージェント機能を直接利用できる。実装はClaude Code CLIをワンショットモードで呼び出すシンプルな設計で、サブエージェントとしての委任ユースケース（コード生成・バグ修正・テスト作成）に特化。マルチエージェントアーキテクチャにおけるClaude Codeの活用パターンとして参考価値が高い。
