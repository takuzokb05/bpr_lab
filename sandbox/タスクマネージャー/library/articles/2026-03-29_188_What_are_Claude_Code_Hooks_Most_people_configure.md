# What are Claude Code Hooks?

- URL: https://x.com/akshay_pachaar/status/2037523396876173783
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-29
- いいね: 754 / RT: 115 / リプライ: 31
- 投稿者: @akshay_pachaar / フォロワー 261,619

## 投稿内容

What are Claude Code Hooks?

Most people configure Claude Code with 𝗖𝗟𝗔𝗨𝗗𝗘.𝗺𝗱 and call it a day.

But that's a mistake.

𝗖𝗟𝗔𝗨𝗗𝗘.𝗺𝗱 is just a suggestion. 𝗛𝗼𝗼𝗸𝘀 are a guarantee.

Claude follows 𝗖𝗟𝗔𝗨𝗗𝗘.𝗺𝗱 most of the time, not all of the time. It might forget to run your linter. It might execute a command you'd never approve. It might declare "done" while tests are still failing.

Hooks fix this by making critical behaviors deterministic.

Here's the idea.

Every tool call Claude makes passes through a lifecycle. Before the tool runs, after it finishes, when Claude is about to stop. You attach shell scripts to these lifecycle events, and they fire automatically. Not most of the time. Every time.

The image below shows exactly how this works.

Claude generates a tool call. Before it executes, the 𝗣𝗿𝗲𝗧𝗼𝗼𝗹𝗨𝘀𝗲 hook intercepts it. Your bash firewall script checks the command against dangerous patterns. If it matches 𝗿𝗺 -𝗿𝗳 / or a force-push to main, 𝗲𝘅𝗶𝘁 𝗰𝗼𝗱𝗲 𝟮 blocks the call entirely and sends the error back to Claude for self-correction. If it's safe, 𝗲𝘅𝗶𝘁 𝗰𝗼𝗱𝗲 𝟬 lets it through.

The tool runs. After it finishes, the 𝗣𝗼𝘀𝘁𝗧𝗼𝗼𝗹𝗨𝘀𝗲 hook kicks in. A one-liner runs 𝗣𝗿𝗲𝘁𝘁𝗶𝗲𝗿 on the file Claude just wrote. Clean output, every time, without Claude needing to remember.

But that's just the mechanical part. The real power is in what you enforce.

A 𝗦𝘁𝗼𝗽 hook that runs 𝗻𝗽𝗺 𝘁𝗲𝘀𝘁 and blocks Claude from finishing until the suite is green. A 𝗦𝗲𝘀𝘀𝗶𝗼𝗻𝗦𝘁𝗮𝗿𝘁 hook that injects the current git branch into context automatically. A 𝗡𝗼𝘁𝗶𝗳𝗶𝗰𝗮𝘁𝗶𝗼𝗻 hook that pings your desktop when Claude needs attention.

The exit code behavior is worth understanding before you write your first hook

𝗘𝘅𝗶𝘁 𝟬 means success. 𝗘𝘅𝗶𝘁 𝟭 means error but non-blocking, execution continues normally. Only 𝗲𝘅𝗶𝘁 𝗰𝗼𝗱𝗲 𝟮 actually blocks and feeds your error message to Claude. Using 𝗲𝘅𝗶𝘁 𝟭 for security hooks is the most common mistake. It logs a warning and does absolutely nothing to stop the action.

The entire configuration lives in 𝘀𝗲𝘁𝘁𝗶𝗻𝗴𝘀.𝗷𝘀𝗼𝗻 under a 𝗵𝗼𝗼𝗸𝘀 key. Each hook gets a matcher regex to target specific tools and a shell command to run. Commit it to git and your whole team gets the same guardrails.

A 𝗖𝗟𝗔𝗨𝗗𝗘.𝗺𝗱 that says "always run 𝗣𝗿𝗲𝘁𝘁𝗶𝗲𝗿" is a hope. A 𝗣𝗼𝘀𝘁𝗧𝗼𝗼𝗹𝗨𝘀𝗲 hook that runs 𝗣𝗿𝗲𝘁𝘁𝗶𝗲𝗿 is a fact.

Suggestions scale with trust. Hooks scale with certainty.

The article below is a complete guide to 𝗖𝗟𝗔𝗨𝗗𝗘.𝗺𝗱, hooks, skills, agents, and permissions, and how to set them up properly.

## 要約

（要約は次回 /curate 時に追記）
