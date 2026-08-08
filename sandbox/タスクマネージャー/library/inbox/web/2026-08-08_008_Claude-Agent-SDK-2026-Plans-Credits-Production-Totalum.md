# Claude Agent SDK in 2026: Complete Guide to Plans, Credits, and Shipping to Production

- URL: https://www.totalum.app/blog/claude-agent-sdk-totalum-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-08

## 要約
Totalum BlogによるClaude Agent SDK 2026年完全ガイド。2025年9月にClaude Code SDKから改名し、Python/TypeScript対応。インストール：`pip install claude-agent-sdk` または `npm install @anthropic-ai/claude-agent-sdk`。重要な変更点：2026年6月15日より、サブスクリプションプランに月次エージェントSDKクレジットプールを分離（インタラクティブなClaude利用と別枠化）。本番運用の重要原則：①状態はPostgres/Redis/オブジェクトストレージで永続化（セッションは揮発性）②タスク/ユーザー/テナント別コストキャップの設定③全本番実行にmax_turnsを設定。SDK組み込みの使用量レポートでコストモニタリング可能。Claude Code SDKから改名された経緯と、Managed Agentsとの関係も解説。
