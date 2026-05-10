# This Chinese guy built agents in Claude Code for cold ema...

- URL: https://x.com/jn_jackk/status/2053580406335947147
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-10
- いいね: 1 / RT: 0 / リプライ: 0
- 投稿者: @jn_jackk / フォロワー 9,621

## 投稿内容
This Chinese guy built agents in Claude Code for cold email campaigns and single-handedly serves 38 B2B businesses a month, taking $3000 from each.

He built a system of 7 agents on Claude Sonnet 4.6 that scrapes LinkedIn and Apollo in narrow verticals, finds B2B companies with broken pipelines, and over 1 weekend takes each one to a finished sample campaign with a personalized Loom and cold message.

No VA, no sales team, no SDR. Just him, a MacBook, an iPhone, and 1 API key.

And traditional cold email agencies keep teams of 9 people on salary for the same order flow, while his expenses are only tokens and subscriptions to Smartlead, Higgsfield, and Calendly.

7 agents work through 1 orchestrator on Claude Code Router. Usage is about 3.4 million tokens a day, the average API bill is about $540 a month.

All 7 go through MCP servers and write shared state to the file system, without shared state in memory and without race conditions, and 1 of them lives right in the iPhone and picks up positive replies from the subway, a taxi, or on walks.

And here is the system prompt he put into the orchestrator before launch:
"You are the orchestrator of a solo agency that sells done-for-you cold email campaigns to B2B businesses. You delegate read-only tasks to 6 sub-agents and own all writes.

sub-agents:

// Scout (sweeps LinkedIn, Apollo, and job boards in selected verticals: 4+ years in business, actively hiring SDRs or BDRs, no outbound footprint or last campaign from 2023, but solid revenue signals)

// Diagnoser (for each lead writes a 50-word pipeline diagnosis, hero angle, tone matched to the vertical, and a cold message under 70 words)

// Builder (generates a sample 5-step sequence + 50 verified prospects in Smartlead through MCP only for the top 4 leads per day, with the sharpest diagnoses and the biggest pipeline gap)

// Filmer (pulls 6 screenshots of the campaign mockup and through Higgsfield renders a 45-second personalized Loom-style walkthrough with the prospect's logo on screen)

// Pitcher (sends a personalized cold message through the right channel for the vertical: email to SaaS founders, LinkedIn to consultancies and M&A shops, SMS to logistics ops leads, IG DM to ecom brands)

// Checker (runs every message through evals for personalization, absence of AI markers and buzzwords before sending)

// Mobile (lives in the iPhone, handles positive replies in real time, books Zoom calls in Calendly through MCP while the owner is on the go).
You never let 2 sub-agents touch 1 lead. You stop and request approval from the human only when a deal exceeds $4,000 or the reply rate in a vertical for the day drops below 11%."

Meaning the system knows what it is and within what boundaries it is allowed to act.

It knows it is supposed to find leads on its own.

It knows it is supposed to take each one to a sample campaign, Loom, and cold message without intervention.

It knows the human only steps in when a deal goes above $4,000 or the reply rate stops converging.

→ The system runs 24 hours a day

→ Scout sweeps about 240 B2B companies across LinkedIn and Apollo per day and leaves 32 new leads in the queue

→ Diagnoser outputs 32 structured diagnoses + briefs + cold messages per day

→ Builder assembles 3 to 4 finished sample campaigns in Smartlead for the sharpest leads

→ Filmer renders a 45-second personalized Loom in Higgsfield for each one

→ Pitcher sends 32 personalized messages per day across 4 channels with a reply rate of about 16%

→ Checker runs every message through evals before sending
And only when a deal breaks $4,000 or the reply rate for the day drops below 11% does the orchestrator wake the owner.

And when the owner at that moment is sitting in the subway or a taxi, the Mobile agent in his iPhone picks up 1 move on its own: replies to a fresh positive reply from a SaaS founder, books a Zoom through Calendly synced to the local time of the client, and puts the lead back in the queue.

The owner only has to tap "approve" and in just 10 minutes join the call.

Here is what the system writes in his log during 1 of the Saturdays:

"scout report: 244 B2B companies checked across SaaS, healthtech, and logistics, 38 actively hiring SDRs, 21 with no outbound footprint, 7 publicly complaining about pipeline on LinkedIn. passing top 32 to diagnoser."

"pitcher: 32 cold messages sent across 4 channels, 16 replies, 6 positive, 4 Zoom calls booked for Sunday. passing to closer."

"builder: sample campaign for Ridgeway Logistics built in Instantly, 3-step sequence, 50 verified prospects, consultative tone. URL placed at /Users/dev/cold-stack/clients/ridgeway/v1. filmer launching Higgsfield."

"eval flag: deal with Halcyon Capital Partners at $4,200 exceeds the approved limit of $4,000. sending for manual review."

He has no server of his own and no separate backend.

Just a local file sandbox at /Users/dev/cold-stack, an MCP router, 1 API key to Claude, and the same key forwarded to Claude Code on his iPhone.

Out of everything I have seen this year, this is the cleanest one-person agency for selling cold email to B2B businesses: $540 a month on the API, about $19,000 into the account, and between them 7 prompts, 1 file system, and 1 phone in the pocket.

## 要約
This Chinese guy built agents in Claude Code for cold email campaigns and single-handedly serves 38 B2B businesses a month, taking $3000 from each.

He built a system of 7 agents on Claude Sonnet 4.6 that scrapes LinkedIn and Apollo in narrow verticals, finds B2B companies with broken pipelines, and over 1 weekend takes each one to a finished sample campaign with a personalized Loom and cold message.

No VA, no sales team, no SDR. Just him, a MacBook, an iPhone, and 1 API key.

And traditional c
