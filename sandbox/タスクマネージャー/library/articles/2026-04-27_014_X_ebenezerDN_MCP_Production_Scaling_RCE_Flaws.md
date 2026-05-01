# Anthropic、MCP本番エージェント向け拡張 — プログレッシブ探索・RCE脆弱性の懸念も

- URL: https://twitter.com/ebenezerDN/status/2047112686773641254
- ソース: x
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-04-27
- いいね: 5 / RT: 0 / リプライ: 0
- 投稿者: @ebenezerDN / フォロワー 12,387

## 投稿内容
Anthropic is scaling the Model Context Protocol (MCP) for production agents, moving beyond local tool-use to a standardized layer for enterprise discovery. New features include progressive discovery and programmable server-side tool definitions.

https://getaibook.com/news/anthropic-pushes-mcp-for-production-agents-despite-rce-flaws/

## 要約
AnthropicがMCPを本番エージェント用途に本格スケールしているという報告。ローカルツール利用を超えてエンタープライズ向けの標準的なディスカバリーレイヤーへ。新機能としてプログレッシブ探索（Progressive Discovery）とプログラマブルなサーバーサイドツール定義が追加された。タイトルに「despite RCE flaws」とある通り、セキュリティ脆弱性（Remote Code Execution）の懸念が並行している状況でのスケール。参照記事URL：https://getaibook.com/news/anthropic-pushes-mcp-for-production-agents-despite-rce-flaws/。本番環境でMCPを使用するエージェント開発者は、RCE脆弱性のリスクを認識した上での設計が必要。リモートMCPサーバーの正式サポート（@asu_hagi投稿）と合わせて読むべき情報。
