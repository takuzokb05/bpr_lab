# MCPのOAuth範囲の限定性とconfused deputy攻撃リスク

- URL: https://x.com/torresmateo/status/2054658596323860943
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-13
- いいね: 2 / RT: 0 / リプライ: 1
- 投稿者: @torresmateo / フォロワー 733

## 投稿内容
@nbarbettini MCP's OAuth section is narrowly scoped. it secures the connection between the client (Cursor, Claude Code) and a remote MCP server. that's it.

forward a Google token through the server and you've collapsed two security realms into one. confused deputy. privilege escalation.

## 要約
MCPのOAuthセキュリティモデルの重要な限界を指摘したセキュリティ分析。MCPのOAuthはクライアント（Cursor、Claude Code）とリモートMCPサーバー間の接続のみを保護するにとどまり、そこで止まるという狭いスコープ。問題のシナリオ：GoogleトークンをMCPサーバー経由で転送すると、2つの異なるセキュリティ境界（MCPのOAuth認証済み接続と、Googleの認証済みトークン）が1つに統合される。これにより「confused deputy」攻撃（ある権限を持つエージェントが別の文脈で権限を悪用される攻撃）と権限昇格のリスクが生まれる。Claude Codeでリモートに認証するMCPサーバーを設計・使用する際のセキュリティ注意事項として重要。
