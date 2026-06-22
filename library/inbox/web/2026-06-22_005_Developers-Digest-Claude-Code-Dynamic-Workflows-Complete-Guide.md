# Claude Code Dynamic Workflows: The Complete Guide

- URL: https://www.developersdigest.tech/blog/claude-code-dynamic-workflows-guide
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-22

## 要約
Developers DigestによるClaude Code Dynamic Workflows完全ガイド。複雑なソフトウェアエンジニアリングタスクを大量AIエージェントで並列処理するClaude Code固有機能の技術解説。**起動方法**: ①「Create a workflow」と直接依頼 ②`/config`でultracodeモードをオン（effort=xhigh、自動適用判断）。**プラン**: Max/Team/Enterprise/API版は自動有効、Proは`/config`から手動有効化。**仕組み**: Claudeが動的にオーケストレーションスクリプトを生成 → 数十〜数百の並列サブエージェント起動 → 結果集約 → 検証 → 最終出力提示。用途: コードベース規模のマイグレーション、大規模リファクタリング、多ファイル横断テスト生成。レート制限: 全プランで倍増済み（SpaceXコロッサス提携後）。Auto modeとの組み合わせで、Bedrock/Vertex/Foundry上でもOpus 4.7/4.8対応済み。既存の5段階ネストサブエージェント制限に注意。
