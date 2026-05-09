# Hermes Agent v0.13.0: 耐久性マルチエージェント基盤・8つのP0修正

- URL: https://x.com/WesRoth/status/2053112757600596090
- ソース: x
- 言語: en
- テーマ: ai-news
- 取得日: 2026-05-09
- いいね: 55 / RT: 7 / リプライ: 4
- 投稿者: @WesRoth / フォロワー 35,221

## 投稿内容
Nous Research has released Hermes Agent v0.13.0, dubbed "The Tenacity Release," which is heavily focused on ensuring the AI agent finishes the tasks it starts.

The update introduces a durable multi-agent collaboration board. This allows users to drop tasks onto the board, where multiple Hermes workers can pick them up, hand them off, and close them out, supported by features like heartbeats, zombie detection, and per-task retry budgets.

A new /goal command (also referred to as the Ralph loop) locks the agent onto a specific target across multiple conversation turns, preventing it from forgetting the user's original request.

The release closes eight major security vulnerabilities (P0s), turns data redaction on by default, and introduces a pluggable architecture that allows third-party model providers to be added as plugins. 

It also features improved state persistence with Checkpoints v2 and a gateway that auto-resumes interrupted sessions.

## 要約
Hermes Agent v0.13.0: 耐久性マルチエージェント基盤・8つのP0修正。投稿者@WesRoth（フォロワー35,221）による具体的な技術情報。
