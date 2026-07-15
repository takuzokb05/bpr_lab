# Claude Code Subagents and Multi-Agent Orchestration Guide

- URL: https://hidekazu-konishi.com/entry/claude_code_subagents_and_orchestration_guide.html
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-04

## 投稿内容

Claude Code Subagents and Multi-Agent Orchestration Guide - Delegation, Parallel Fan-Out, and Custom Agent Definitions.

Subagents are separate Claude instances spawned by a main conversation to handle isolated tasks. They operate with independent context windows, preventing verbose task outputs from cluttering the parent thread. The parent receives only the conclusion, not the work that produced it.

**Three primary benefits:**
- Context preservation: verbose task details stay isolated
- Parallelization: multiple subagents run concurrently
- Least-privilege enforcement: agents can be restricted to specific tools

**Custom agent definitions:** Defined via Markdown files with YAML frontmatter in `.claude/agents/`. Tool scoping is critical: omitting the `tools` field grants *all* available tools rather than none.

**Critical operational limitation:** Subagents cannot use `AskUserQuestion`, and background subagents auto-deny prompts — so approval-gated edits fail silently when delegated.

**Best use cases:** High-volume read-only investigations (research, testing, log analysis), independent parallel tasks. Underperforms for tightly-coupled iteration, small changes, or work requiring mid-task human approval.

## 要約

Claude Code サブエージェントの設計原則と実践ガイド。独立したコンテキストウィンドウで動作する別Claudeインスタンスとして、親スレッドへの結論のみ返却という設計思想を詳解。`.claude/agents/` への YAML frontmatter 付き Markdown 配置で定義でき、ツールスコープを絞ることで最小権限を実現。最重要の落とし穴：`tools` フィールドを省略すると全ツールが付与される・バックグラウンドサブエージェントは `AskUserQuestion` を自動拒否するため承認が必要な作業を委任すると無音で失敗する。最適用途は大量の読み取り専用調査と並列タスク。フォーカルポイントを人間のレビューポジションに置くアーキテクチャを推奨。
