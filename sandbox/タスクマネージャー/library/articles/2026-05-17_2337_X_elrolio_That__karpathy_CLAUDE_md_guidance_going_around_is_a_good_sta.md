# That @karpathy CLAUDE.md guidance going around is a good starting point.  But pr

- URL: https://x.com/elrolio/status/2056115938865590698
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-17
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @elrolio / フォロワー 1519

## 投稿内容
That @karpathy CLAUDE.md guidance going around is a good starting point.

But prose instructions are the weakest enforcement layer you can build.

I run Claude Code as my daily work environment for marketing strategy, competitive intel, content production — not code.

There are layers beyond prose, and each one catches what the last one can't:

Prose rules — You write "think before acting" in your CLAUDE.md and the model reads it. Sometimes follows it, sometimes doesn't. You find out when the output is wrong.

Hooks — A rule that intercepts the behavior before it happens. I kept re-explaining "don't spawn Explore subagents" until I wrote a hook that blocks it at the system level. The model doesn't decide whether to comply — it can't.

Skills — Codified workflows with enforced sequence. My editing pipeline runs de-LLMification → clarity → voice validation in that order, every time, because the skill defines it.

Agent architecture — Specialized agents with scoped tools. My competitive intelligence agent has web scraping access. My editing agents don't. You can't touch what your tools don't reach.

Success criteria — This is Karpathy's best insight, buried in his post. Don't tell the model what to do — tell it what done looks like. "Complete when it has 3 sourced alternatives with evidence tiers and data within 90 days." The model loops until it gets there.

Start with the CLAUDE.md. Then look at which rules you keep re-explaining — those are your first hooks. The layers build from there.
---

Three graphics showing my real applications:
1. Strategic Theater — "don't use strategic theater language"
- Bad: "compelling strategic opportunity with transformative potential"
- Good: "$2.4B market, growing 18% YoY, 3.2% penetration"

2. Evidence Tiers — "don't present speculation as fact"
- Bad: "Our analysis shows this market could reach $8B by 2028"
- Good: "Gartner estimates $8B (Projected). We've measured $1.2B in our segment."

3. Context First — "check what we already know before responding"
- Bad: "Let me create a new competitive analysis from scratch"
- Good: "Found 3 prior analyses in vault. Building on the March assessment."

## 要約
CLAUDE.mdを非コード用途で活用する実践知見
