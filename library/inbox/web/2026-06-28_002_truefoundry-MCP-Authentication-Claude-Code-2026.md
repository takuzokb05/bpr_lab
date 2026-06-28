# MCP Authentication in Claude Code 2026 Guide

- URL: https://www.truefoundry.com/blog/mcp-authentication-in-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-28

## 要約
Claude CodeでのMCPサーバー認証4方式を解説。①静的HTTPヘッダー（環境変数インターポレーション: CLI起動時に${ENV_VAR}を置換）、②AWS認証情報（AWS_ACCESS_KEY_IDなど継承された環境変数）、③IAMロール引き受け（最小権限アクセス）、④OAuth 2.0（`claude mcp auth [server-name]`インタラクティブコマンドで自動トークン更新）。新コマンド`claude mcp login`でシェルからサーバー認証が可能。実装上の注意点：AWS SSOセッションの期限切れ、IAMポリシーの伝播遅延、環境変数はCLI起動前にセット必須。
