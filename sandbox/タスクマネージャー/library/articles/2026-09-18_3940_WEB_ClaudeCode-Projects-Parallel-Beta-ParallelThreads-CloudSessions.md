# Claude Code Projects Major Relaunch: Parallel Cloud Sessions & Shared Memory Beta

- URL: https://www.itechpost.com/articles/237367/20260918/claude-code-projects-gets-major-relaunch-managing-parallel-ai-agents-cloud.htm
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-18

## 投稿内容
Anthropic rebuilt Claude Code Projects from the ground up. The new beta (September 17, 2026) lets a single project coordinate parallel threads—each a full Claude Code cloud session—while sharing memory and a project library. Threads keep running after you close your laptop. A coordinator model (e.g. Opus 5) splits a goal into subtasks and dispatches them to worker threads, each configurable with its own model and thinking-effort level. Daily limit: 200 new threads across all projects. Currently limited to Pro/Max users who have used cloud sessions and have no existing projects; others can join a waitlist.

Additional coverage: https://www.marktechpost.com/2026/09/17/anthropic-launches-claude-code-projects-in-beta-parallel-cloud-sessions-that-keep-running-after-you-close-your-laptop/

## 要約
Anthropicが2026年9月17日にClaude Code Projectsを大幅リニューアルしベータ公開。コーディネーターが目標をパラレルスレッドに分割し、各スレッドはフルClaude Codeクラウドセッションとして並行稼働する。ラップトップを閉じてもスレッドは継続実行し結果を会話へ報告。コーディネーターとワーカーでモデル・思考レベルを独立設定可能（例: coordinator=Opus 5, workers=Sonnet 5）。共有メモリ＋プロジェクトライブラリで複数リポジトリをまたぐ長期作業を管理。1日最大200スレッド制限、各スレッドがフルセッションのため使用量消費に注意。Pro/Max既存クラウドセッションユーザー優先でウェイトリストあり。ローカル並列作業の限界（コンテキスト・手動調整）を解消する本格的なマルチエージェント実行基盤として注目度高い。
