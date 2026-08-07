# Scaling AI Agent Infrastructure with the MCP Stateless Updates — Google Developers Blog

- URL: https://developers.googleblog.com/scaling-ai-agent-infrastructure-with-the-mcp-stateless-updates/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-07

## 要約

GoogleがMCP 2026-07-28仕様のstateless化を自社のAIエージェントインフラに適用した経緯と知見を公式ブログで公開。

**Googleの実装背景**:
- Googleは多数のMCPサーバー（Cloud Storage, BigQuery, Calendar, Drive等）を提供
- 旧stateful仕様では各サービスにsession管理層が必要だった
- stateless化によりCloud Runへの直接デプロイが可能に

**スケールでの恩恵**:
- セッション親和性なしのhorizontal scaling
- 自動スケールアップ・ダウン（リクエストがゼロの時にコスト0）
- Cold startコスト最小化
- 複数リージョンへのデプロイが透過的に

**Googleのベストプラクティス**:
1. `tools/list`の結果をクライアント側でTTLキャッシュ（サーバーの`ttlMs`を尊重）
2. `server/discover`エンドポイントを必ず実装
3. 認証はOAuth 2.0 + OpenID Connect（MCPの新要件に準拠）
4. 観測可能性: OpenTelemetryで各ツール呼び出しをトレース

**Google MCP Serversの対応状況**:
- Google Workspace MCPサーバー群は2026-09に新仕様へ完全移行予定
- 旧仕様との後方互換期間は2027-01まで

**なぜ重要か**: Googleの公式実装事例はMCP serverの設計標準として権威がある。Claude CodeのMCPサーバー開発時の参照実装として最有力。
