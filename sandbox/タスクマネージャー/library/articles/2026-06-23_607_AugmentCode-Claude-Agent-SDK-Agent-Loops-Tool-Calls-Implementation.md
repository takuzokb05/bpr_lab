# Claude Agent SDK: Agent Loops, Tool Calls, and Multi-Step Workflows

- URL: https://www.augmentcode.com/guides/claude-agent-sdk-agent-loops-tool-calls
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-23

## 要約
Augment CodeによるClaude Agent SDKの実装ガイド。エージェントループ（入力→Claude応答→ツール呼び出し→結果フィードバック→再応答）をコード付きで解説。ツール定義・ストリーミング応答・セッション継続（--resume）・コンテキスト圧縮の自動処理を網羅。マルチステップワークフローはサブエージェントに委任しメインコンテキストを保護する設計を推奨。Python SDKの具体コードスニペット（ファイルシステム操作・Web検索・コード実行）が豊富。エラーハンドリングとリトライロジックの実装例あり。stop_reason（end_turn / tool_use / max_tokens）の取り扱い方も明示。実装者向けの一次情報として参照価値が高い。
