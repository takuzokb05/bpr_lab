# StackQL Anthropic API Providers Update — July 2026

- URL: https://stackql.io/blog/anthropic-providers-update-july-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-20

## 投稿内容
StackQL released an update to Anthropic platform providers, including the `anthropic` provider exposing the Claude API surface with messages, models, batches, files, agents, deployments, environments, sessions, skills, memory stores, and vaults (11 services, 26 resources, 103 operations), and a new `anthropic_admin` provider for the Admin API surface. Concurrently, Anthropic added API key expiration settings in the Claude Console (presets, custom durations, or never; email reminders before expiration for keys ≥7 days), raised rate limits across the Claude API (Claude Sonnet and Claude Haiku now match Claude Opus at every usage tier), and consolidated usage tiers into three: Start, Build, and Scale.

## 要約
StackQLがAnthropicプラットフォームのIaCプロバイダーを更新。`anthropic`プロバイダー（Claude API面：11サービス・26リソース・103オペレーション）と新設の`anthropic_admin`プロバイダー（Admin API面）に。同時発表のClaudeプラットフォーム変更：APIキー有効期限設定（Claude Console上でカスタム期間・プリセット・無期限を選択、7日以上で期限前メール通知）、SonnetとHaikuのレートリミットをOpus水準に統一、使用ティアをStart/Build/Scaleの3段階に集約。エンタープライズチームによるAnthropicインフラのIaCライフサイクル管理が可能になる。開発者向けの実用的な変更で、大規模API利用の利便性が向上。
