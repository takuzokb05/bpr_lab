# 🚨Breaking: The guy who created Claude Code (@bcherny) just revealed how his team...

- URL: https://x.com/Suryanshti777/status/2037558286137143591
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-29
- いいね: 877 / RT: 142 / リプライ: 49
- 投稿者: @Suryanshti777 / フォロワー 29,157

## 投稿内容

🚨Breaking: The guy who created Claude Code (@bcherny) just revealed how his team actually trains their AI.

One file: CLAUDE.md

You place it at the root of your project.

Inside it:

past mistakes

conventions

rules

Claude reads it every session.

The result?

The agent improves over time without you touching the code.

Every bug that gets fixed becomes a permanent rule.

Boris Cherny uses this internally at Anthropic every day.

Here’s the template he shared — ready to copy, paste, and adapt.

CLAUDE.md Template

1. Plan Mode Default

Enter plan mode for any non-trivial task (3+ steps or architectural decisions)

If something goes wrong, STOP and re-plan immediately — don’t keep pushing

Use plan mode for verification steps, not just building

Write detailed specs upfront to reduce ambiguity

2. Subagent Strategy

Use subagents frequently to keep the main context window clean

Offload research, exploration, and parallel analysis to subagents

For complex problems, throw more compute via subagents

Assign one task per subagent for focused execution

3. Self-Improvement Loop

After any correction from the user, update tasks/lessons.md with the pattern

Write rules for yourself to prevent repeating the same mistake

Ruthlessly iterate on these lessons until the mistake rate drops

Review lessons at the start of each session

4. Verification Before Done

Never mark a task complete without proving it works

Diff behavior between main and your changes when relevant

Ask yourself: “Would a staff engineer approve this?”

Run tests, check logs, and demonstrate correctness

5. Demand Elegance (Balanced)

For non-trivial changes, ask: “Is there a more elegant solution?”

If a fix feels hacky, ask:
“Knowing everything I know now, implement the elegant solution.”

Skip this for simple fixes — don’t over-engineer

Challenge your own work before presenting it

6. Autonomous Bug Fixing

When given a bug report: just fix it

Use logs, errors, and failing tests to diagnose

Require zero context switching from the user

Fix failing CI tests automatically

Task Management

1. Plan First – Write the plan in tasks/todo.md with checkable items

2. Verify Plan – Confirm the plan before implementation

3. Track Progress – Mark items complete as you go

4. Explain Changes – Provide a high-level summary at each step

5. Document Results – Add a review section to tasks/todo.md

6. Capture Lessons – Update tasks/lessons.md after corrections

Core Principles

Simplicity First
Make every change as simple as possible and minimize code impact.

No Laziness
Find root causes. Avoid temporary fixes. Maintain senior-level engineering standards.

## 要約

（要約は次回 /curate 時に追記）
