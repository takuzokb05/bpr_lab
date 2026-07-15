# How to build with subagents in Claude Code

- URL: https://x.com/KashKysh/status/2037607602067050873
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-29
- いいね: 76 / RT: 7 / リプライ: 15
- 投稿者: @KashKysh / フォロワー 67,329

## 投稿内容

How to build with subagents in Claude Code

90% of Claude Code users are sleeping on this feature, even though it works better than almost any prompt

imagine you need to build a product made up of 10 parts, subagents can handle each of them separately

What are subagents?

these are specialized AI assistants that handle specific types of tasks

each subagent runs in its own context window, with a custom system prompt and specific tool access

basically, once it's set up, when Claude hits a task that fits a subagent, it just delegates it, and the subagent handles everything autonomously and returns the result

How to create your own subagent?

run the /agents command in a Claude Code session (v1.0.60+), choose the scope, then configure:

→ model
→ name
→ description
→ tools
→ system prompt

the system prompt file is located at: .claude/agents/your-agent.md

How to invoke a subagent?

you don't really need a command anymore, just ask Claude in your prompt to use a subagent

or it will do it automatically, which makes the whole building process way easier

if you're a builder working on a complex product, it's basically a must-have to split responsibilities across subagents

and if you need multiple agents working in parallel and interacting with each other, you can go even further and use agent teams

this is a must-have feature for anyone building with Claude Code

and I'll put together more resources you should check out if you want to break into the top 5% of Claude Code users

## 要約

（要約は次回 /curate 時に追記）
