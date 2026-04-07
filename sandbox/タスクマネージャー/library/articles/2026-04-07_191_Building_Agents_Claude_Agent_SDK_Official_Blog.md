# Building agents with the Claude Agent SDK（Anthropic公式ブログ）

- URL: https://claude.com/blog/building-agents-with-the-claude-agent-sdk
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-04-07

## 要約

Anthropic公式ブログによるClaude Agent SDK紹介。Claude Codeを動かすのと同じツール・エージェントループ・コンテキスト管理をPython/TypeScriptから直接プログラムできる：
- **エージェントループ4ステップ**: ①コンテキスト収集→②アクション実行→③作業検証→④繰り返し
- async forループがClaude の思考→ツール呼び出し→結果観察→次判断を自動オーケストレーション
- SDK自動処理：ツール実行・コンテキスト管理・リトライ
- **名称変更の意図**: "Claude Code SDK"→"Claude Agent SDK"で「コーディング以外のエージェント用途」へのブランディング転換
- コードレビューエージェント実装サンプル付き（コードベース分析→バグ/セキュリティ発見→構造化フィードバック）

Anthropic公式の一次情報として信頼性が最高。
