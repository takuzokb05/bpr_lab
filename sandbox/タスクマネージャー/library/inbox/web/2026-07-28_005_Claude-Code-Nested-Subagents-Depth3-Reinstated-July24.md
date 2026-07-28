# Claude Code v2.1.217/219 Major Updates: Nested Sub-Agent Limits 4-Day Evolution

- URL: https://dev.classmethod.jp/en/articles/20260722-cc-updates-v2-1-217/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-28

## 要約
2026年7月21〜24日に起きたClaude Codeサブエージェント制御の急展開を解説。v2.1.172（6月10日）でネストサブエージェント最大深度5を実装後、v2.1.217（7月21日）で同時実行上限20・ネスト完全禁止に。4日後のv2.1.219（7月24日）でデフォルト深度3で再実装。設定変数：CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH（深度上限変更）、CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS（デフォルト20）。Anthropicは過負荷・予期しないコスト爆発を防ぐガードレールとして制限を導入した旨を説明。その他v2.1.217の変更：サブエージェントのツール使用が親エージェントの承認キュー表示対象から除外（UX改善）、サブエージェントのToken使用が親エージェント予算から明示的に分離。実運用上は深度3制限でほぼすべてのユースケースに対応可能とAnthropicは述べている。
