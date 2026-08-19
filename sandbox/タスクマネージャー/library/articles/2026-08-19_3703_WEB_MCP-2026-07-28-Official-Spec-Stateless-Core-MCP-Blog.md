# The 2026-07-28 MCP Specification - Official Release: Stateless Core & Enterprise Auth

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-19

## 投稿内容
MCP公式ブログによるv2026-07-28仕様の発表（TS/Python/Go/C# SDK同時更新）。

## 要約
MCP史上最大の改訂。主要変更5点: (1)ステートレスプロトコルコア（最大変更）- initialize/initializedハンドシェイクとMcp-Session-Idヘッダを廃止、全リクエストが自己記述的に→平易なラウンドロビンLBで任意インスタンスにルーティング可能、(2)Roots/Sampling/Loggingを非推奨（12ヶ月は動作継続）、(3)Enterprise Managed AuthorizationエクステンションがStableに昇格（組織が全MCPサーバーの認可を一元管理、ユーザーはシングルログインで全サービスアクセス）、(4)オプショナルなdiscoveryコール対応、(5)コアトランスポートモデル全面書き直し。エージェントインフラのスケーリングが大幅容易化。
