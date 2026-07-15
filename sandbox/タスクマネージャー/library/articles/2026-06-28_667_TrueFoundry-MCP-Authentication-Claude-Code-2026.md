# MCP Authentication in Claude Code 2026 Guide: OAuth・IAM・AWS・静的ヘッダー4方式

- URL: https://www.truefoundry.com/blog/mcp-authentication-in-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-28

## 投稿内容
Claude CodeでのMCPサーバー認証4方式を網羅的に解説した技術ガイド。

**方式1: 静的HTTPヘッダー（環境変数インターポレーション）**
Claude CLI起動時に${ENV_VAR}を自動的に置換する仕組み。APIキーやトークンをheaders設定に${MY_API_KEY}の形式で記述し、環境変数からセキュアに読み取る。

**方式2: AWS認証情報（継承された環境変数）**
AWS_ACCESS_KEY_ID、AWS_SECRET_ACCESS_KEY、AWS_SESSION_TOKENなどの既存環境変数を活用。追加設定不要でAWS CLIの認証情報が自動的に利用される。

**方式3: IAMロール引き受け（最小権限アクセス）**
特定タスクにのみ必要な権限を持つIAMロールを引き受けることで最小権限原則を実現。クロスアカウントアクセスにも対応。

**方式4: OAuth 2.0（インタラクティブ認証）**
`claude mcp auth [server-name]`コマンドで対話的認証を実施し、自動トークン更新機能付き。新コマンド`claude mcp login`でシェルから設定済みサーバーへの認証が可能。

**実装上の注意点（gotchas）:**
- AWS SSOセッションの期限切れ問題
- IAMポリシーの伝播遅延（変更後数分待機が必要）
- 環境変数はCLI起動前にセット必須（起動後にセットしても無効）

## 要約
Claude CodeにおけるMCPサーバー認証の4方式を実装レベルで解説。①静的HTTPヘッダー（CLI起動時${ENV_VAR}置換）、②AWS認証情報継承、③IAMロール引き受け（最小権限）、④OAuth 2.0（自動トークン更新付き）。新コマンド`claude mcp auth`と`claude mcp login`の使い方を含む。AWS SSOセッション期限・IAM伝播遅延・環境変数タイミングの実装上の落とし穴も解説。本番環境でのMCPセキュリティを確立するための実践ガイド。
