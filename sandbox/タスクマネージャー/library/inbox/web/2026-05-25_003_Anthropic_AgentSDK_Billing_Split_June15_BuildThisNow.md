# Claude Code Billing Change June 15, 2026: Agent SDK Credit Pool Guide

- URL: https://www.buildthisnow.com/blog/guide/mechanics/claude-billing-change-june-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-25

## 要約
Anthropicが2026年6月15日施行の課金構造変更を詳解した実践ガイド。Agent SDK・`claude -p`（非インタラクティブ）・Claude Code GitHub Actions・OpenClaw等のサードパーティエージェントが、Claude購読の通常枠から**別個の月次クレジットプール**に移行する。Pro: $20、Max 5x: $100、Max 20x: $200（非繰り越し）。クレジット枯渇後は「extra usage」有効化でAPI従量課金へ。ターミナルでの対話的Claude Codeは通常購読枠のまま変更なし。影響範囲：OpenClaw・n8n・Zapier連携・GitHub Actionsで自動タスクを回している開発者は要対応。上限管理のベストプラクティスも収録。
