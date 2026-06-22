# Anthropic Workload Identity Federation: Keyless Auth GA for Claude Platform

- URL: https://aembit.io/blog/anthropic-workload-identity-federation-what-it-gets-right-and-what-it-still-doesnt-solve/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-22

## 要約
AnthropicがClaude Platform向けにWorkload Identity Federation（WIF）をGA提供。静的APIキーをショートリブドスコープ付き認証情報に置き換える。**対応IDプロバイダー**: AWS IAMロール、GCP/Kubernetesサービスアカウント、Azure管理ID、GitHub Actionsトークン、Okta、その他OIDC準拠プロバイダー。各ワークロードが共有APIキーの代わりに独自のID・ロール・監査証跡を持つ「サービスアカウント」を導入。Claude Console上で段階的セットアップUIが用意され、認証テストコマンドで設定を即確認可能。本番CIや医療・金融などの規制業界でのAPI鍵ハードコード排除を実現。合わせて2026年6月2日には**ant CLI**（Go製、MIT License）も公開：`ant auth login`でOAuthフロー経由ブラウザ認証、プロファイル切り替え機能（複数ワークスペース管理）、CI向けWIF統合をサポート。Anthropic公式ドキュメント: platform.claude.com/docs/en/manage-claude/workload-identity-federation。
