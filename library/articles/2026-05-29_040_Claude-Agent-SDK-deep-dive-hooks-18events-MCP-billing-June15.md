# Claude Agent SDK深掘り: 18フックイベント・MCP統合・6月15日課金変更の全解説

- URL: https://jidonglab.com/blog/claude-agent-sdk-deep-dive-en/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-29

## 投稿内容
Claude Agent SDK Deep Dive: What It Means to Use Claude Code as a Library (Jidong Lab). The Agent SDK is the same harness that powers Claude Code, exposed as a library. Python: `pip install claude-agent-sdk`; TypeScript: `npm install @anthropic-ai/claude-agent-sdk`. Built-in tools eliminate boilerplate for file system and shell access. 18 hook events provide lifecycle control to intercept nearly every point of agent execution. Deepest MCP integration of any framework — Playwright, Slack, GitHub, and hundreds of other servers connect with a single configuration line. June 15, 2026: Agent SDK usage splits into a separate credit pool (Pro: $20/month equivalent; Max 20x: $200/month equivalent). Claude Sonnet 4 and Opus 4 (20250514 versions) retire June 15 — migrate to Sonnet 4.6 / Opus 4.7. Managed Agents webhooks, multiagent orchestration, and self-hosted sandboxes available on Claude Platform on AWS.

## 要約
Claude Agent SDKの技術的深掘り解説。SDKはClaude Codeを動かすのと同一ハーネスをライブラリとして公開したもので、Python/TypeScriptで利用可能。18フックイベントによるライフサイクル制御が全フレームワーク中最も深いMCP統合と並ぶ特徴。Playwright・Slack・GitHub等のMCPサーバーが1行設定で接続可能。2026年6月15日の重要変更点: Agent SDK利用は別クレジットプールに分離（Pro: 月$20相当、Max 20x: 月$200相当追加）。Claude Sonnet 4/Opus 4（20250514版）が6月15日にリタイアしSonnet 4.6・Opus 4.7への移行が必要。Managed AgentsのWebhooks・マルチエージェントオーケストレーション・セルフホストサンドボックスもAWS上のClaude Platformで利用可能。課金変更の実務的インパクトを含む必読記事。
