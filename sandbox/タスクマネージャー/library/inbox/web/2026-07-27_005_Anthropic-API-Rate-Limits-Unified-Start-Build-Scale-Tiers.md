# Anthropic Rate Limits Unified: Sonnet and Haiku Now Match Opus Across Start, Build, and Scale Tiers

- URL: https://chatforest.com/builders-log/anthropic-rate-limits-start-build-scale-sonnet-haiku-opus-unified-june-2026-builder-guide/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-27

## 要約
2026年6月26日にAnthropicが発表したAPIレート制限の大幅改定をビルダー向けに解説した記事。4段階だったティアを3段階（Start・Build・Scale）に再編、かつClaudeのモデル間でレート制限を統一（Sonnet・Haiku・OpusがRPM/ITPM/OTPMで同一制限に）。具体的な数値: Startティアで月上限$500、BuildでS1000、ScaleでS200,000。Tier 1でのInput tokens per minute: 旧30,000→新500,000（約16倍増）。既存ユーザーの制限引き下げは一切なし（全員が同等以上のティアに移行）。APIビルダーが直面していたエージェント・バッチジョブ・コード自動化パイプラインでのボトルネックが解消される見込み。Claude Console上でティア確認可能。7月24日にはFast mode for Opus 4.7が廃止。開発者向け実践情報として重要度高。
