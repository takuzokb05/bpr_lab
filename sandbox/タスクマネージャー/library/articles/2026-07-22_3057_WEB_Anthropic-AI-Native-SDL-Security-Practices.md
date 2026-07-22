# How Anthropic secures its AI-native software development lifecycle — Anthropic Blog

- URL: https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-22

## 投稿内容
Anthropic's Deputy CISO Jason Clinton publicly details security practices for a development lifecycle where Claude authors ~80% of merged code (published July 21, 2026). Five SDLC stages: (1) Planning — automated Claude Opus-powered PSR analyzes design docs against MITRE ATT&CK; low-risk projects can self-approve. (2) Code generation — security guidance in CLAUDE.md files and org-wide skills; /security-review command integrated into Claude Code; security guidance plugin provides real-time suggestions; developers work on remote VMs with restricted egress allowlisting. (3) Testing/CI — multiple specialized review agents with narrow focus areas, each writing proofs validating findings before posting comments; risk-tiered codebase; SAST combined with agentic scanning. (4) Deployment — continuous AI-powered DAST in staging; external pentesting for major launches; bug bounty and red teaming. (5) Monitoring — single-purpose alert triage agent with limited permissions; separate agents as checks on each other via shared channels; all agent actions routed to SIEM for auditability. Governance: every approval logged with signals and reasoning.

## 要約
Anthropic Deputy CISO Jason Clintonが、Claudeがコードの~80%を生成する環境でのAIネイティブSDLCセキュリティ実践を公開（7月21日）。5段階：①計画：Claude Opus駆動のPSRがMITRE ATT&CKで設計書を自動分析②コード生成：CLAUDE.md＋スキルにセキュリティガイダンス埋め込み、/security-reviewコマンド、egress制限リモートVM③テスト：複数専門エージェントがPoV（脆弱性証明）を書いてからコメント投稿、SAST＋エージェントスキャン併用④デプロイ：ステージングでのAIパワードDASTと外部ペンテスト⑤モニタリング：単一目的アラートエージェント、全承認をSIEMに記録。Claudeコード生成80%環境での実際のセキュリティ知見として価値が高い。
