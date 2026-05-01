# Flowise の深刻な脆弱性：Anthropic MCP アダプタ経由でのコマンド実行の恐れ

- URL: https://iototsecnews.jp/2026/04/20/critical-vulnerability-in-flowise-allows-remote-command-execution-via-mcp-adapters/
- ソース: x
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-05-01
- いいね: 1 / RT: 1 / リプライ: 0
- 投稿者: @iototsecnews / フォロワー 484

## 投稿内容
Flowise の深刻な脆弱性：Anthropic MCP アダプタ経由でのコマンド実行の恐れ
https://t.co/MUWHfgyVM5
今回の問題は、AI エージェント同士を繋ぐ標準規格である MCP (Model Context Protocol) の設計そのものに原因があります。一般的なプログラムの書き間違いではなく、SDK の作り方という深層にリスクが潜んでいるため、開発者が気づかないうちに脆弱性を引き継いでしまう点が非常に特殊です。この設計上の判断により、本来は安全なはずの環境でも、攻撃者にコマンド実行を許す恐れがあります。現時点において、LiteLLM／LangChain／Flowise などのフレームワークに影響が及んでおり、すでに 10 件以上の CVE が発行されています。ご利用のチームは、ご注意ください。
#Anthropic #Flowise #MCP #Vulnerability

## 要約
フォロワー484の@iototsecnewsによる投稿。 Flowise の深刻な脆弱性：Anthropic MCP アダプタ経由でのコマンド実行の恐れ

今回の問題は、AI エージェント同士を繋ぐ標準規格である MCP (Model Context Protocol) の設計そのものに原因があります。一般的なプログラムの書き間違いではなく、SDK の作り方という深層にリスクが潜んでいるため、開発者が気づかないうちに脆弱性を引き継いでしまう点が非常に特殊です。この設計上の判断により、本来は安全なはずの環境でも、攻撃者にコマンド実行を許す恐れがあります。... 参照URL: https://iototsecnews.jp/2026/04/20/critical-vulnerability-in-flowise-allows-remote-command-execution-via-mcp-adapters/
