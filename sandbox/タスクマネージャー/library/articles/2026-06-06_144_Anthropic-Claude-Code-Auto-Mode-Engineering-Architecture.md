# How We Built Claude Code Auto Mode: Safer Permission-Skip Architecture

- URL: https://www.anthropic.com/engineering/claude-code-auto-mode
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-06

## 要約

AnthropicエンジニアリングブログによるClaude Code Auto Modeの設計解説（一次資料）。Auto ModeはProプラン以上で利用可能で、従来の都度パーミッション確認を「バックグラウンド安全チェック」に置き換える。ルールベースではなくモデル判断によるリスク評価を採用し、ファイル削除・git reset・外部APIコール等をリスクスコアで動的に判定。通常操作は中断なし、破壊的・疑わしい操作のみブロック＆通知。Proプランはsonnet 4.6、Enterprise/MaxはOpus 4.8でAuto Mode動作。「安全性とUXのトレードオフをどう設計したか」を詳細解説しており、採用判断・CLAUDE.md設定方針に直結する一次情報。
