# How to Make Claude Code Skills Activate Reliably (Scott Spence)

- URL: https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-28

## 要約

スキルの自動発動（autonomousトリガー）が標準では約50%の成功率に留まる問題を解決する実践ガイド。
- **描写的description**: 「いつ」「何をするか」を過度に具体的に書くことで自動認識率が向上（50%→80-84%）
- **トリガーキーワードの明示**: descriptionに「when user asks about X」「triggered by Y」などの明示的トリガー文言を含める
- `disable-model-invocation: true` をスクリプト専用スキルに設定してコンテキスト消費ゼロにする方法
- 失敗パターン分析：抽象的なdescription、スコープが広すぎるスキル名

スキル設計において最も実践的な問題（発動しない）への直接的な解決策を提供。
