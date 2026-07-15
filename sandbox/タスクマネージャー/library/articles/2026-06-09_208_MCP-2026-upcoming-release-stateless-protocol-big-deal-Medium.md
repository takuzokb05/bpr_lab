# MCP's Upcoming 2026 Release Is a Big Deal — ステートレス化でエンタープライズ展開を変える

- URL: https://medium.com/@balajibal/mcps-upcoming-2026-release-is-a-big-deal-1d15990f121f
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-09

## 投稿内容
Balaji BalによるMCP 2026-07-28 Release Candidateの重要性解説記事。公式仕様（blog.modelcontextprotocol.io）の外から見た実用インパクト分析。

最大の変更：プロトコルのステートレス化。
- 旧仕様：スティッキーセッション・共有セッションストア・ゲートウェイでのディープパケットインスペクションが必要。
- 新仕様：ラウンドロビンロードバランサーが使用可能。Mcp-Methodヘッダーでルーティングができるため、ボディ検査不要。

追加変更：
- Streamable HTTPにMcp-Method/Mcp-Nameヘッダーを必須化（ゲートウェイ・ロードバランサー・レートリミットをオペレーション単位で制御可能）
- List/リソース読み取り結果にttlMsとcacheScopeを追加（HTTP Cache-Controlモデルに準拠）
- W3C Trace Context（traceparent/tracestate/baggage）標準化で分散トレース相関が容易に
- SDK Tier 1は10週間以内に対応義務

7月28日が最終仕様リリース予定。拡張フレームワーク・Tasks・MCP Apps・OAuth強化も包含。

## 要約
MCP 2026-07-28 RC のステートレス化が企業向け展開を大幅に簡素化するという視点からの解説。スティッキーセッション不要→普通のロードバランサーで動作可能という変化は、エンタープライズ本番採用の最大の障壁を取り除く。Tier 1 SDKの対応デッドラインと合わせて注目すべきエコシステムの転換点。
