# Claude Code Nested Subagents: 4-Day Evolution — v2.1.217→219 深度3復活

- URL: https://dev.classmethod.jp/en/articles/20260722-cc-updates-v2-1-217/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-28

## 投稿内容
Between July 21-24, 2026, Claude Code underwent a rapid four-day evolution on nested subagents. v2.1.172 (June 10): nested subagents allowed up to depth 5. v2.1.217 (July 21): concurrent subagent cap set to 20, nested subagent spawning disabled entirely. v2.1.219 (July 24): nesting reinstated at default depth 3. Configuration: CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH (override depth limit), CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS (default 20). Anthropic cited cost explosions and overload as reasons for restrictions, then found depth 3 sufficient for virtually all real use cases. Additional v2.1.217 changes: subagent tool calls no longer appear in parent's approval queue (UX improvement), subagent token usage explicitly separated from parent budget.

## 要約
2026年7月21〜24日にClaude Codeのサブエージェント制御が急展開。v2.1.172（6/10）で深度5のネスト許可→v2.1.217（7/21）で同時実行上限20・ネスト完全禁止→v2.1.219（7/24）でデフォルト深度3で再実装。設定変数：CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH・CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS（デフォルト20）。Anthropicはコスト爆発・過負荷への対応としてガードレールを導入。深度3で実用上のほぼ全ユースケースに対応可能と説明。追加変更：サブエージェントのツール呼び出しが親の承認キューから除外（UX改善）、トークン使用量が親予算から分離。
