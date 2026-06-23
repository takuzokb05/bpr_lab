# Claude Agent SDK: Agent Loops, Tool Calls, and Multi-Step Workflows

- URL: https://www.augmentcode.com/guides/claude-agent-sdk-agent-loops-tool-calls
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-23

## 要約
Augment CodeによるClaude Agent SDKの実践ガイド。エージェントループの仕組み（ユーザー入力→Claude応答→ツール呼び出し→結果フィードバック→再応答）を図解とコードで解説。ツール定義の書き方、ストリーミング応答の扱い、セッション継続（--resume）、コンテキスト圧縮の自動処理を網羅。マルチステップワークフローでは各ステップをサブエージェントに委任し、メインコンテキストを汚染しない設計を推奨。エラーハンドリングとリトライロジックの実装例あり。Python SDKでの具体的なコードスニペットが豊富で、ファイルシステム操作・Web検索・コード実行のツール実装パターンを示す。エージェントループの停止条件（stop_reason: end_turn / tool_use / max_tokens）の取り扱いも解説。
