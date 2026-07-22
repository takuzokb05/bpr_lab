# How Datadog built a "universal machine tool" for Claude Code — Anthropic Blog

- URL: https://claude.com/blog/how-datadog-built-a-universal-machine-tool-for-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-22

## 投稿内容
Anthropic official blog (July 21, 2026) on Datadog's "Temper" — a deterministic kernel built on top of Claude Code. Rather than AI agents generating application code directly, they produce formal specifications that Temper verifies and executes. This solves the growing bottleneck between fast agent-generated code and verified, production-ready software. Temper enforces three contracts per capability: (1) Behavior contract: states, transitions, preconditions, safety properties. (2) Data contract: entity types and APIs in machine-readable form. (3) Authorization: default-deny, scope-based approval with human hot-loading. Specifications pass four independent verification layers: symbolic reasoning, exhaustive state exploration, deterministic simulation with fault injection, and randomized property testing (~1,000 action sequences). Full verification cascade completes in under one second for small specs. The proven specification is the same artifact that runs in production — eliminating drift between verified and deployed code. Quote from Datadog VP Engineering Sesh Nalla: "Agents can produce code faster than any team can review by hand, but they can make mistakes."

## 要約
Anthropic公式ブログ（7月21日）。DatadogがClaude Code上に構築した決定論的カーネル「Temper」の事例紹介。エージェントがアプリコードを直接生成する代わりに形式仕様を生成し、Temperが3つの契約（振る舞い・データ・認可）を強制した上で4層独立検証（シンボリック推論・網羅的状態探索・決定論シミュレーション・ランダムプロパティテスト）を実施。小規模仕様の全検証が1秒以内で完了。検証済みアーティファクトをそのまま本番実行するためドリフトなし。エージェントの高速コード生成と本番品質保証を両立した重要ユースケース。
