# Claude Codeのツール呼び出しスコープ拡張リスク——本番権限と同じ設計原則で管理せよ

- URL: https://x.com/thomasdevos69/status/2058612176105902133
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-24
- いいね: 1 / RT: 0 / リプライ: 0
- 投稿者: @thomasdevos69 / フォロワー 190

## 投稿内容
Claude Code gets risky when a tool call can quietly widen scope: read one folder, touch another, hit a paid API, then make the review look small. I treat MCP tools like prod permissions: named scope, approval rule, and a log I can replay.

#ClaudeCode #AgenticCoding

## 要約
Claude Codeのツール呼び出しが静かにスコープを拡張するリスクの実践的な安全設計を解説。「あるフォルダを読む→別フォルダを変更する→有料APIを呼ぶ→変更が小さく見える」という連鎖的なスコープ拡張パターンを問題として提示。対策としてMCPツールを本番パーミッションと同様に扱い、名前付きスコープ・承認ルール・リプレイ可能なログの3点セットで管理することを推奨。Claude Code Hooksとparameterバリデーションを組み合わせたセキュリティ設計の具体的指針として有用。
