# Claude Code 週次アップデートまとめ（2026/08/02週）

- URL: https://qiita.com/saitoko/items/a95cbb5888835be0f7fd
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-08-03

## 要約
2026年8月2日週のClaude Code更新をv2.1.213〜v2.1.220にわたりまとめたQiita記事（GitHub CHANGELOG.md・npm registryを一次情報として参照）。

主なハイライト:
- **Opus 5が新デフォルトOpusモデルとして追加**（1Mコンテキスト対応・価格はOpus 4.8と同額）
- **/verify・/code-review・/deep-researchの自律実行（Auto Mode）が段階的廃止**→ユーザー明示起動に移行
- **/code-reviewはバックグラウンドサブエージェントとして再設計**（レビュー結果が会話を埋め尽くさなくなった）
- **dynamic workflowsのデフォルトサイズがmedium（15エージェント以下）に変更**
- Opus 4.7がfast modeから削除
- claude update・claude doctorのサイレントハング修正
- モデルピッカーUIのバグ修正

Claude Codeが自律実行から「ユーザーが明示的にトリガーするもの」へ設計思想が移行している重要な変更点を記録。
