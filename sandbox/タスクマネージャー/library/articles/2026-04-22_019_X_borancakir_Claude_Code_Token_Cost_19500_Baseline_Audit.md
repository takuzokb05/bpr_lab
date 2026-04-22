# Claude Codeセッション開始時に19,500トークン消費の内訳 — Redditで926セッション監査報告

- URL: https://x.com/borancakir/status/2046314459015025079
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-22
- いいね: 1 / RT: 0 / リプライ: 0
- 投稿者: @borancakir / フォロワー 1,141

## 投稿内容
Checked /cost at the start of my session this morning.

19,500 tokens before a single line of work.

Someone on Reddit audited 926 Claude Code sessions last week and found 45K at baseline.

Here is where it goes:

1) Every MCP server you have connected dumps its full tool definitions into context at session start, whether you call those tools or not.

2) CLAUDE.md loads in full on top of that, regardless of what the task actually needs.

3) Claude's own system tools take another 10-13k before you have typed a thing.

Two things that actually move it: 

Disable MCP servers you are not using for the current task + keep CLAUDE.md under 600 tokens.

Run /cost before you start your next session... it is the cheapest audit you will do this week.

## 要約
@borancakir（フォロワー1,141）による2026-04-20の投稿。Claude Codeセッション開始前に19,500トークンが自動消費されるという実測値。Redditでの926セッション監査では平均45Kトークンが開始時に消費されていたことも判明。内訳：①接続中の全MCPサーバーのツール定義がセッション開始時に全投入（使用有無関係なし）、②CLAUDE.mdの全文が読み込まれる（タスク無関係）、③Claudeのシステムツール自体で10〜13K。具体的な対策：未使用MCPサーバーの無効化、CLAUDE.md 600トークン以下に維持。/costコマンドでの事前確認を推奨。定量データ付きの実践的なコスト最適化知見。
