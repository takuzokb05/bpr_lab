# Claude Code Best Practices for Agentic Coding 2026 — OpenHands

- URL: https://www.openhands.dev/blog/claude-code-best-practices-agentic-coding
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-29

## 投稿内容

OpenHands (Jul 02, 2026): "10 Claude Code Best Practices for Agentic Coding"

The workflow Anthropic recommends is explore, then plan, then code. Claude Code works best when it has a clear context, disciplined planning, and structure built around it before execution begins.

Key practices:
1. Use plan mode (Shift+Tab) before any edit — Anthropic internal testing found unguided attempts succeed ~33% of the time
2. Keep CLAUDE.md under 200 lines — all 18 frontier models tested lose accuracy as input grows, some dropping from 95% to 60% past a threshold
3. Use block-level HTML comments for notes to humans (stripped before hitting context = zero tokens)
4. Decision framework: Hooks/permissions for enforced rules; Skills for contextual knowledge; Subagents for delegation boundaries; CLAUDE.md for always-on project guidance
5. Run parallel agents in git worktrees for noisy research tasks
6. Use verification loops to kill hallucinations
7. Treat Claude Code like a skilled contractor: clear scope, verification criteria, bounded tools, persistent memory via CLAUDE.md
8. Add a team Makefile to standardize workflows for all team members

## 要約
OpenHandsが2026年7月に公開した10のベストプラクティス。「探索→計画→コーディング」ワークフローが要。CLAUDE.mdは200行以内必須（超過するとモデル精度が95%→60%に低下する実測値あり）。Shift+TabでのPlanモード活用、gitワークツリーでの並列エージェント実行、ツール選択の設計原則（Hooks=強制ルール、Skills=文脈知識、Subagents=委任境界）を明確化。チームMakefileで全員が1コマンドで実行できる環境を構築することを推奨。
