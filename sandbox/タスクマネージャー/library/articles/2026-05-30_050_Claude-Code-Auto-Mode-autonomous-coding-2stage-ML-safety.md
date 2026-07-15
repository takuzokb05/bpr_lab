# Claude Code Auto Mode: 2段階ML分類器で自律コーディング・人間承認ゲートを排除

- URL: https://www.infoq.com/news/2026/05/anthropic-claude-code-auto-mode/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-30

## 投稿内容
Inside Claude Code Auto Mode: Anthropic's Autonomous Coding System with Human Approval Gates — InfoQ, May 2026. Auto mode replaces human "approve/deny" permission prompts with an ML classifier evaluating every tool call in real time. Architecture: Input Layer (file reads, shell results, web responses undergo inspection before entering context — malicious content triggers warnings), Execution Layer (two-stage classification: fast initial filter + deeper analysis for uncertain/risky actions). Subagent workflows get outbound validation pre-execution and return checks post-completion to detect prompt injection. Safe operations run automatically; ambiguous/dangerous ones find safer paths or escalate. Spinner turns red when a permission check is triggered. Auto mode available on Pro plan (May 2026), supports Sonnet 4.6.

## 要約
Claude CodeのAuto ModeをInfoQが技術的に詳解。従来の都度承認プロンプトをML分類器に置き換え、毎ツール呼び出しをリアルタイム評価する自律コーディング機能。2層アーキテクチャ：入力層（悪意あるコンテンツを文脈組み込み前にブロック）と実行層（高速フィルタ→詳細分析の2段階分類）。安全と判定されれば自動実行、曖昧・危険ならより安全なパスを探索または人間に確認。サブエージェントワークフロー向けには送出前バリデーションと完了後チェックでプロンプトインジェクションを防御。Proプランで2026年5月中旬から展開、Sonnet 4.6をサポート。「コーヒーブレイクで本当に離席できる」水準の自律度を実現しつつ、センシティブな操作は人間承認を保持するバランス設計。
