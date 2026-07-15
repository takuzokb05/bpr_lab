# 食トレンド分析MCPサーバー自作事例: FastMCP+Databricks Apps+Unity Catalog（エブリー）

- URL: https://tech.every.tv/entry/2026/05/26/115508
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-05-29

## 投稿内容
Claudeで食トレンドを分析できるMCPを自作した（every Tech Blog, 2026-05-26）。株式会社エブリー（デリッシュキッチン運営）がデリッシュリサーチのデータをClaude APIから自然言語で問い合わせるMCPサーバーを構築。技術スタック: Python 3.11 + FastMCP + Databricks Appsホスティング + Unity Catalogデータアクセス + OpenTelemetry監視。装備した11種類ツール: キーワード検索数推移・ランキング・物価相関分析など。表記ゆれ・言い換えを代表語に自動正規化。Databricks Apps Resource宣言20個上限に当たり手動GRANTへ切り替えが必要（実運用上の注意点）。ツール呼び出し履歴をUnity Catalogに蓄積し利用状況・エラー率を継続追跡。社内リリース後: ダッシュボードでは対応困難な切り口分析・Web検索との組み合わせ・商材提案資料作成など多様な活用が生まれた。

## 要約
エブリー社（デリッシュキッチン）の開発チームが独自ドメインデータ（食トレンド検索ログ）をClaude APIから自然言語で問い合わせるカスタムMCPサーバーを構築した実践事例（2026年5月26日公開）。FastMCP + Databricks Apps + Unity Catalogの技術スタックで11種類のツールを実装。表記ゆれ自動正規化・OpenTelemetry監視・ツール呼び出し履歴蓄積など本番品質の実装詳細を公開。実装上のハマりポイントとしてDatabricks Apps Resource宣言の20個上限も記録。社内展開後に「ダッシュボードでは対応困難な切り口分析」等の新しい活用が自発的に生まれた点が重要。カスタムドメインデータをMCP経由でLLMに接続するパターンの参考事例として高い価値を持つ。
