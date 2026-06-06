# How We Built Claude Code Auto Mode: Safer Way to Skip Permissions

- URL: https://www.anthropic.com/engineering/claude-code-auto-mode
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-06

## 要約

Anthropicのエンジニアリングブログが、Claude Code Auto Modeの設計と実装を詳解した一次資料。Auto ModeはProプラン以上で利用可能で、従来の都度パーミッション確認を「バックグラウンド安全チェック」に置き換える。通常操作は中断なしで実行し、破壊的・疑わしい操作のみをブロック＆通知する仕組み。設計上の重要判断として「ルールベースではなくモデル判断によるリスク評価」を採用し、ファイル削除・git reset・外部APIコール等をリスクスコアで動的に判定。Anthropicがどのように「安全性とUX」をトレードオフしたかが明確に書かれており、Auto Mode採用判断に不可欠な一次情報。
