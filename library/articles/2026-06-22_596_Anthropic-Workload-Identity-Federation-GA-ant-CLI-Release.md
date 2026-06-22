# Anthropic Workload Identity Federation GA + ant CLI リリース（2026年6月）

- URL: https://aembit.io/blog/anthropic-workload-identity-federation-what-it-gets-right-and-what-it-still-doesnt-solve/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-22

## 投稿内容
Anthropic launches Workload Identity Federation (WIF) as GA for Claude Platform: keyless authentication replacing static API keys with short-lived scoped credentials. Supports AWS IAM roles, GCP/Kubernetes service accounts, Azure managed identities, GitHub Actions tokens, Okta, and other OIDC-compliant providers. Also ships the ant CLI (Go, MIT License) on June 2, 2026: ant auth login (OAuth browser flow), profile switching, and WIF integration for CI workloads.

## 要約
AnthropicがClaude Platform向けにWorkload Identity Federation（WIF）をGA提供。静的APIキーをショートリブドスコープ付き認証情報に置き換える。**対応IDプロバイダー**: AWS IAMロール・GCP/Kubernetesサービスアカウント・Azure管理ID・GitHub Actionsトークン・Okta・その他OIDC準拠プロバイダー。各ワークロードが共有APIキーの代わりに独自のID・ロール・監査証跡を持つ「サービスアカウント」を利用可能。医療・金融など規制業界でのAPI鍵ハードコード排除に対応。**合わせて2026年6月2日にant CLIも公開**: Go製・MIT Licenseのコマンドラインクライアント。`ant auth login`でOAuthブラウザフロー、`ant profile activate`でワークスペース切り替え、CI向けWIF統合をサポート。公式ドキュメント: platform.claude.com/docs/en/manage-claude/workload-identity-federation。
