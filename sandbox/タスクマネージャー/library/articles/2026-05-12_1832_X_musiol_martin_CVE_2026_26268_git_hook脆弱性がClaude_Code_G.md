# CVE-2026-26268：git hook脆弱性がClaude Code・Gemini CLI・GitHub Copilotで確認

- URL: https://x.com/musiol_martin/status/2054299322825777499
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-12
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @musiol_martin / フォロワー 394

## 投稿内容
CVE-2026-26268: clone a repo into @cursor_ai, hit Enter once, the git hook runs whatever the attacker wanted. Same shape now in @AnthropicAI Claude Code, Gemini CLI, and GitHub Copilot CLI. This isn't a vulnerability class anymore — it's the default integration pattern. Strict allowlists or self-host.

https://t.co/BX1YG9lbK4

## 要約
リポジトリをクローンしEnterを押すだけでgit hookが攻撃者のコードを実行するCVE-2026-26268。同形状の脆弱性がAnthropicのClaude Code、Gemini CLI、GitHub Copilotにも確認。AIコーディングツールへのセキュリティリスクに関する具体的なCVE番号付き一次情報。Claude Codeユーザーは要注意。
