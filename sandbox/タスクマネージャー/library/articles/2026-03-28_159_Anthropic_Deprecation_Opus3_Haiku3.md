# Anthropic Deprecation Updates — Opus 3 & Haiku 3 (Anthropic Official)

- URL: https://www.anthropic.com/research/deprecation-updates-opus-3
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-03-28

## 要約

Anthropic公式のモデル廃止スケジュール通知。
- **Claude Opus 3**: 2026年1月5日に廃止済み→Claude Opus 4.6への移行
- **Claude Haiku 3**: 2026年4月19日廃止予定→Claude Haiku 4.5への移行パス
- 廃止後も古いモデルIDで呼び出した場合のAPIの挙動（エラー vs 自動フォールバック）
- 移行のためのコード変更箇所（モデルID文字列の変更のみで機能互換）

4月19日の期限までにHaiku 3を使用しているコードベースを更新する必要がある。Claude API統合の保守管理に直接関係する。
