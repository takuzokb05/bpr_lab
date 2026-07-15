# 🚨BREAKING: Someone built an entire AI trading firm and open-sourced it.

- URL: https://x.com/mhdfaran/status/2036037106913714463
- ソース: x
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-03-29
- いいね: 206 / RT: 39 / リプライ: 10
- 投稿者: @mhdfaran / フォロワー 78,864

## 投稿内容

🚨BREAKING: Someone built an entire AI trading firm and open-sourced it.

A full team of AI agents working together exactly like a real Wall Street firm.

It's called TradingAgents. Here's how it works:

The Analyst Team reads the market:
→ Fundamentals Analyst — reads company financials, finds red flags
→ Sentiment Analyst — scans social media for market mood
→ News Analyst — monitors global news and macro events
→ Technical Analyst — reads MACD, RSI, price patterns

Then the Researchers debate:
→ A bull agent argues for the trade
→ A bear agent argues against it
→ They go back and forth until one side wins

Then the Trader decides.
Then Risk Management approves or kills it.
Then the Portfolio Manager signs off.
Every trade goes through 6 layers of AI review before it executes.

Works with Claude, GPT, Gemini, Grok, and local models via Ollama.

Three lines to run your first analysis:
ta = TradingAgentsGraph(config=DEFAULT_CONFIG.copy())
_, decision = ta.propagate("NVDA", "2026-01-15")
print(decision)

29.9K stars. Backed by a published research paper.
Free & open source.

link in comment

## 要約

（要約は次回 /curate 時に追記）
