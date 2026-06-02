# Best Claude Code Plugins 2026: 11本テスト・真に使えた4本 — Context7・rtk・Playwright・GitHub

- URL: https://buildtolaunch.substack.com/p/best-claude-code-plugins-tested-review
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-02

## 投稿内容
Build to LaunchサブスタックによるClaude Codeプラグイン11本の実際テストレビュー（2026年）。

**真に使えた4本（推奨）**
1. **Context7** — ライブラリドキュメントをバージョン固定で提供。古いAPIへの参照ミスを防ぐ。コンテキスト汚染が少ない
2. **rtk** — CLIツール出力をLLMコンテキストに入る前にフィルタリング・圧縮。トークン節約
3. **Playwright Plugin** — ブラウザ自動化テストとの統合。UIテスト・スクレイピング・E2Eテストに直接使用可能
4. **GitHub Plugin** — PR・Issue・Actions・Releases に直接アクセス。`mcp__github__`ツール群の上位互換

**除外した7本の理由**
- 機能重複（MCP serverと重複する機能）
- コンテキスト消費が大きい（他のタスクに使えるコンテキストが減少）
- 動作不安定（2026年5月時点でbugあり）
- 既存ワークフローとの競合

**重要なインサイト**
プラグインは多ければ良いわけではない。各プラグインはコンテキストを消費し、複雑さを増す。「少数の精選ツール + 明確なCLAUDE.md」が最も効果的。

**コスト評価**
Context7: 追加コンテキスト最小・精度向上最大 → 最高ROI
rtk: コンテキスト圧縮により全体コスト削減効果あり

## 要約
Build to LaunchによるClaude Codeプラグイン11本の実用テストレビュー。真に使える4本：①Context7（ライブラリドキュメントのバージョン固定参照・古いAPI参照ミス防止）、②rtk（CLI出力圧縮・トークン節約）、③Playwright Plugin（ブラウザ自動化テスト統合）、④GitHub Plugin（PR/Issue/Actions直接アクセス）。
除外理由も公開：機能重複・コンテキスト過剰消費・動作不安定・ワークフロー競合。
「プラグインは多ければ良いわけではなく、コンテキスト汚染のリスクがある」という実践知見が特に価値が高い。
Context7が最高ROI（追加コンテキスト最小・精度向上最大）と評価。rtkはコンテキスト圧縮で全体コスト削減効果あり。
本プロジェクトの日次収集エージェントやFX自動取引にプラグインを導入する際の選定基準として直接活用可能。
