# Claude Agent SDK 2026-06-15 課金変更：移行プレイブックと新クレジットプール詳解

- URL: https://theplanettools.ai/blog/claude-agent-sdk-billing-model-deprecation-june-15-2026-migration-playbook
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-31

## 投稿内容
Planet Tools による Claude Agent SDK の2026年6月15日課金モデル変更の移行ガイド。

## 要約
2026年6月15日より Agent SDK・claude -p の利用がサブスクリプション上限から独立したAgent SDKクレジットプール（ドル建て月次クレジット）へ移行。対象：①Claude Agent SDK、②claude -p 非インタラクティブコマンド、③Claude Code GitHub Actions統合、④Agent SDK認証のサードパーティアプリ。プラン別クレジット：Pro $20/月、Max 5x $100/月、Max 20x $200/月、Team/Enterprise要確認。超過時はfallbackなくエラー（課金設定によっては従量課金継続も可能）。移行チェックリスト：①Agent SDK利用量の月次測定、②APIキーのAgent SDK用途分離、③コスト試算・予算アラート設定。Claude Code名称からAgent SDK名称への改名も同時期（2026年3月）に実施済み。2週間以内に対応が必要な緊急トピック。
