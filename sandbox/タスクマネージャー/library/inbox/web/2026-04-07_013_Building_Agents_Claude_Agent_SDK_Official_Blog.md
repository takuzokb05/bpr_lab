# Building agents with the Claude Agent SDK

- URL: https://claude.com/blog/building-agents-with-the-claude-agent-sdk
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-04-07

## 要約
Anthropic公式ブログによるClaude Agent SDK紹介記事。Claude Codeを動かすのと同じツール・エージェントループ・コンテキスト管理をPython/TypeScriptから直接使えるSDK。エージェントループ4ステップ：①コンテキスト収集、②アクション実行、③作業検証、④繰り返し。async forループがClaude の思考→ツール呼び出し→結果観察→次の判断を自動オーケストレーション。Claude Code SDKからClaude Agent SDKへの名称変更（より広い用途へのシグナル）の背景も説明。コードレビューエージェント（コードベース分析→バグ/セキュリティ問題発見→構造化フィードバック）のサンプル実装付き。Anthropic公式の一次情報として信頼性が高い。
