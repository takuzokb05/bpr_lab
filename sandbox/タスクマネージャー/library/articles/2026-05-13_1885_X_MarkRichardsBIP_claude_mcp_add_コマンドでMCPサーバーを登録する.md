# `claude mcp add` コマンドによるMCPサーバー登録の実際の手順

- URL: https://x.com/MarkRichardsBIP/status/2054661267726729521
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-13
- いいね: 0 / RT: 0 / リプライ: 1
- 投稿者: @MarkRichardsBIP / フォロワー 1734

## 投稿内容
Step 5 — tell Claude Code where the MCP server lives.

claude mcp add hyperliquid /usr/local/bin/hyperliquid-mcp --scope user

claude mcp list

Green check next to hyperliquid? You're plugged in.

## 要約
Claude CodeへのMCPサーバー登録手順のチュートリアルの一部（Step 5）。`claude mcp add <name> <path> --scope user`というコマンド構文でユーザースコープのMCPサーバーを追加し、`claude mcp list`で緑チェックが表示されれば接続完了という確認方法を解説。`--scope user`フラグによりユーザーレベル（グローバル）でMCPサーバーを登録する点が具体的。Hyperliquid MCPを例に使ったDeFi/取引用途のClaude Code拡張チュートリアルの文脈。MCPサーバーの追加・確認のCLIワークフローを示す実践的なリファレンス。
