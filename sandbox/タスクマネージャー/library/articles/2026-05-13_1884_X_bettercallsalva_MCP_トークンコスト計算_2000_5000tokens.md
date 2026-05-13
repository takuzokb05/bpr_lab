# MCP サーバーごとに2,000〜5,000トークンのスキーマコストがかかる

- URL: https://x.com/bettercallsalva/status/2054663204173725848
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-13
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @bettercallsalva / フォロワー 216

## 投稿内容
@JackQian10789 @alexalbert__ This matches my budget math for Claude Code. Each MCP server adds 2-5k tokens of schema baseline before the agent does anything. For one-off scripts I write the curl/jq inline and save MCPs for workflows that actually need stateful access.

## 要約
Claude CodeにおけるMCPサーバーのトークンコストに関する実測値。各MCPサーバーがエージェントが何もアクションを起こす前にスキーマのベースラインとして2,000〜5,000トークンを消費するという定量データ。これを踏まえたコスト最適化戦略として「単発スクリプトにはcurl/jqをインラインで書き、MCPはステートフルアクセスが本当に必要なワークフローのみに限定する」という使い分けを提案。MCP採用時のコスト設計に直接使えるベンチマーク情報。
