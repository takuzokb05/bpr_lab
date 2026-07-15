# Build an AI Agent with Claude Agent SDK — SerpApi Tutorial 2026 + June 15 課金解説

- URL: https://serpapi.com/blog/build-an-ai-agent-with-claude-agent-sdk/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-01

## 要約
SerpApi による Claude Agent SDK を使ったAIエージェント構築チュートリアル（2026年版）。Claude Codeと同一エージェントループをPython/TypeScriptライブラリとして提供する設計思想から解説。
主要インターフェース: `query()` 非同期ジェネレータ（プロンプト→型付きメッセージストリーム返却）。組み込みツール: ファイル読み書き・コマンド実行・コード理解・Web検索・Web取得が即利用可能（手動tool実装不要）。
Sessions機能でマルチターン会話の状態管理、MCPサーバーへのファーストクラスサポートも提供。
6月15日以降の課金変更についても解説: Agent SDK利用はサブスクリプション枠外の月次クレジットプールから課金。Pro $20・Max 5x $100・Max 20x $200/月。
SerpApi自体をMCPサーバーとして利用した実践例を含む、Web調査エージェントの完全実装例を提供。
