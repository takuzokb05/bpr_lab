# Anthropic API Rate Limits Unified: Start/Build/Scale 3-Tier System (June 2026)

- URL: https://chatforest.com/builders-log/anthropic-rate-limits-start-build-scale-sonnet-haiku-opus-unified-june-2026-builder-guide/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-27

## 投稿内容
Builder-focused guide to Anthropic's June 26, 2026 API rate limit overhaul: 4 tiers simplified to 3 (Start/Build/Scale), all models now have equal limits.

## 要約
2026年6月26日にAnthropicが発表したAPIレート制限の大幅改定をビルダー向けに解説。4段階→3段階（Start・Build・Scale）に再編、かつ全モデル間でレート制限を統一（Sonnet・Haiku・OpusがRPM/ITPM/OTPMで同一制限に）。具体的数値: Startで月上限$500、Build $1,000、Scale $200,000。Tier 1でのInput tokens/minute: 旧30,000→新500,000（約16倍増）。既存ユーザーの制限引き下げなし（全員が同等以上のティアへ移行）。APIビルダーが直面していたエージェント・バッチジョブ・コード自動化パイプラインでのボトルネックが解消される見込み。Claude Console上でティア確認可能。関連: 7月24日にFast mode for Opus 4.7廃止（`claude-opus-4-7`+`speed: "fast"`はエラー返却）、中間会話ツール変更がFable 5・Mythos 5・Opus 4.8・Opus 5でベータ提供開始。開発者向け実践情報として重要度高。
