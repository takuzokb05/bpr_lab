# MCP 2026-07-28 RC：エンタープライズ対応で開く3つの新攻撃面

- URL: https://www.securityweek.com/new-enterprise-ready-mcp-specification-brings-new-security-challenges/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-14

## 要約
SecurityWeekがMCP 2026-07-28 RCのセキュリティリスクを実証的に解説。新たに特定された4種の攻撃面：(1)ステートトラッキング攻撃：予測可能なトラッキングIDと状態オブジェクトでワークフローハイジャック・クロステナントデータアクセス・不正クロスアクションが可能に。(2)HTTPヘッダー脆弱性：新設MCP-Method/MCP-Nameヘッダーでプロトコル混乱・デシンクロ攻撃。`x-mcp-header`でAPIキー・トークン・PII等がLB・プロキシ・ログシステムに全露出。(3)XSS：MCP Appsプロトコル拡張が従来型ストアドXSSを導入。(4)DoS via長時間タスク：Tasks extensionで単一リクエストから高コスト処理（CPU・メモリ・DB）が起動でき、送信後即時切断可能。旧バージョンは2026年7月28日で廃止指定（12ヶ月移行期間）。CVE番号なし。セキュリティ責任はプロトコルから開発者実装に移行。
