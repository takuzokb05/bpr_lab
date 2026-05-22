# Claude CodeがAPIキー不要に：Workload Identity Federation新認証導入（XenoSpectrum）

- URL: https://xenospectrum.com/claude-api-workload-identity-federation/
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-05-22

## 要約
2026年5月4日発表：AnthropicがWIF（Workload Identity Federation）サポートを導入。静的APIキーをCIパイプラインや本番環境に保存する必要がなくなる重要なセキュリティ改善。対応IdP：AWS IAM・Google Cloud・Microsoft Azure・GitHub Actions・Kubernetes・Okta。仕組み：各IdPの短命トークンをAnthropicが検証して一時的なAPI認証を発行。メリット：秘密鍵の漏洩リスク排除・定期ローテーション不要・既存IAMポリシーとの統合。エンタープライズ向けClaude Code導入障壁が大幅に低下する重要な公式機能追加。
