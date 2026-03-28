# MCP's Biggest Growing Pains for Production Use (The New Stack)

- URL: https://thenewstack.io/model-context-protocol-roadmap-2026/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-03-28

## 要約

MCPを本番環境で使う際の技術的課題を詳細分析した記事（2026年）。
- **セッション状態とスケーリング**: MCP 1.0はステートフルセッション前提のため水平スケールが困難→Streamable HTTPで解決予定
- **Capability Discovery不足**: サーバーに接続してみるまで何ができるか不明→`.well-known`エンドポイントで解決予定
- **Enterprise Governance**: 監査証跡・アクセス制御・認証が標準化されていない→Enterprise Extensionsで対応
- 現時点での回避策（キャッシュ・サイドカーパターン・プロキシ）も詳述

MCPの採用を検討している組織が直面する現実的な問題と、2026年の仕様進化による解決タイムラインが分かる。
