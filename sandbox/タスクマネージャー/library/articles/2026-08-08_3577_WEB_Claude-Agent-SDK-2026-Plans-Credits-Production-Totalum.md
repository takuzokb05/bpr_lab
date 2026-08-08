# Claude Agent SDK in 2026: Complete Guide to Plans, Credits, and Shipping to Production

- URL: https://www.totalum.app/blog/claude-agent-sdk-totalum-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-08

## 投稿内容
Claude Agent SDK (renamed from Claude Code SDK in Sep 2025) ships in Python and TypeScript. Install: `pip install claude-agent-sdk` or `npm install @anthropic-ai/claude-agent-sdk`. As of June 15, 2026: subscription plans get a dedicated monthly Agent SDK credit pool separate from interactive Claude usage. Production patterns: durable state in Postgres/Redis/object storage (session is ephemeral); per-task/user/tenant cost caps in the agent harness; max_turns on every production run; built-in usage reporting for cost monitoring.

## 要約
Claude Agent SDK（2025年9月にClaude Code SDKから改名）の2026年完全ガイド。Python/TypeScript対応、pip/npmでインストール。2026年6月15日より月次エージェントSDKクレジットプールをインタラクティブ利用から分離。本番原則：状態永続化（Postgres/Redis）、コストキャップのハーネス実装、max_turns設定、SDK組み込み使用量レポート。Managed AgentsとSDKの関係も解説。
