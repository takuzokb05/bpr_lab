# StackQL Anthropic API Providers Update — July 2026

- URL: https://stackql.io/blog/anthropic-providers-update-july-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-20

## 要約
StackQLがAnthropicプラットフォームのプロバイダーを大幅更新。`anthropic`プロバイダー（Claude API面：messages/models/batches/files/agents/deployments/environments/sessions/skills/memory-stores/vaults の11サービス・26リソース・103オペレーション）と、新設の`anthropic_admin`プロバイダー（Admin API面）の2本立てに。これによりAnthropicのインフラをIaC（Infrastructure as Code）ツールから管理可能に。同時発表されたClaudeプラットフォーム側の変更：APIキー有効期限設定（CLアdaude Console上でカスタム期間・プリセット・無期限を選択可能、7日以上の場合は期限前にメール通知）、APIレートリミットを全モデルで統一（SonnetおよびHaikuのレートリミットをOpus水準に引き上げ、使用ティアを3段階：Start/Build/Scaleに集約）。
