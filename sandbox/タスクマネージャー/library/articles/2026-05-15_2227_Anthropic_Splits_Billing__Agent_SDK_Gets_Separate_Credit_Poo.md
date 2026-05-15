# Anthropic Splits Billing: Agent SDK Gets Separate Credit Pools June 15 2026

- URL: https://thenewstack.io/anthropic-agent-sdk-credits/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-15

## 要約
2026年6月15日からのClaude Agent SDK課金変更を詳報（The New Stack）。
これまではPro/Maxのインタラクティブ枠からAgent SDK利用分も消費されていたが分離。
新クレジット枠：Pro $20/月、Max 5x $100/月、Max 20x $200/月（毎月リセット・繰越なし）。
対象：Agent SDK・claude -pコマンド・Claude Code GitHub Actions・サードパーティSDKアプリ。
同日Sonnet 4 + Opus 4がAPIから引退、Sonnet 4.6/Opus 4.7が新デフォルト。
開発者への影響：Agent SDK経由の大量呼び出しが本番利用しやすくなる反面、消費追跡が必要。
移行プレイブックとしては claude mcp list で依存を確認し、クレジット残量モニタリング設定を推奨。
