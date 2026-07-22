# How Datadog built a "universal machine tool" for Claude Code — Anthropic Blog

- URL: https://claude.com/blog/how-datadog-built-a-universal-machine-tool-for-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-22

## 要約
Anthropic公式ブログ（7月21日）。DatadogがClaude Code向けに「Temper」と呼ぶ決定論的カーネルを構築した事例紹介。エージェントがアプリコードを直接生成するのではなく、Temperが検証・実行する形式仕様を生成することで品質を担保。3つの契約（振る舞い仕様・データコントラクト・認可）を強制し、4層独立検証（シンボリック推論・網羅的状態探索・決定論シミュレーション・ランダムプロパティテスト）をすべて通過。小規模仕様の全検証カスケードが1秒以内で完了。エージェントは仕様が証明された同一アーティファクトを本番で動かすため、ドリフトが発生しない。高速生成と高い安全性保証の両立を実現した重要事例。
