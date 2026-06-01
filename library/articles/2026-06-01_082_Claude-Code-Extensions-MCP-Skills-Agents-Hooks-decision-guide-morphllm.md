# Claude Code Extensions 完全ガイド 2026 — MCP・Skills・Agents・Hooks の使い分け

- URL: https://www.morphllm.com/claude-code-extensions
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-01

## 要約
morphllm.com がClaude Code拡張機能の4要素を体系的に解説し、意思決定ルールを提供。
4要素の役割: ①MCP servers=外部ツール・API接続（GitHub・Slack・PostgreSQL・Stripe等200以上）、②Skills=カスタムワークフロー教示とスラッシュコマンド登録（.md形式・コンテキスト節約）、③Custom Agents=独自コンテキストでのタスク分離委任、④Hooks=ライフサイクルイベント自動スクリプト実行（pre-commit・post-tool call等）。
意思決定ルール: 毎ターン必要→CLAUDE.md、たまに使う手順→skill、自動実行→hook、メインコンテキストを埋める→subagent。
5層構成の全体アーキテクチャ: CLAUDE.md（プロジェクトルール）→MCP→skills→hooks→subagents。
Plugins = 複数要素（MCP+skills+subagents+hooks）をパッケージした配布単位として位置付け。
