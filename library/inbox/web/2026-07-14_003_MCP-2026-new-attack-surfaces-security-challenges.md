# 新MCP仕様が開く3つの攻撃面：エンタープライズ対応が新たなセキュリティ課題を生む

- URL: https://www.securityweek.com/new-enterprise-ready-mcp-specification-brings-new-security-challenges/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-14

## 要約
SecurityWeekがMCP 2026-07-28 RCの新セキュリティリスクを解説。(1)ステートトラッキング攻撃：予測可能なIDでワークフローハイジャックやクロステナントデータアクセスが可能。(2)HTTPヘッダー脆弱性：新設MCP-Method/MCP-Nameヘッダーがプロトコル混乱攻撃を招く恐れ。x-mcp-headerでAPIキー・PII等がLB・プロキシ・ログに露出するリスク。(3)XSS：MCP Appsとして追加されたプロトコル拡張が従来型ブラウザXSS脆弱性を導入。(4)DoS：長時間タスク（Tasks extension）で単一リクエストが高コスト処理を起動可能。旧バージョンは12ヶ月移行期間あり。セキュリティ責任は開発者側に移行。
