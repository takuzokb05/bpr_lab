# Claude Code Agent View: 複数エージェントセッションを一元管理するCLIダッシュボード

- URL: https://claude.com/blog/agent-view-in-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-30

## 要約
Anthropicが2026年5月11日にClaude Codeの新機能「Agent View」を研究プレビューとして公開した。従来は複数のターミナルタブやtmuxグリッドで個別に管理していた複数エージェントセッションを、単一CLIダッシュボードで一元監視・操作できる。`claude agents`コマンドで起動し、各セッションの待機状態・実行状況・最終レスポンス内容を一覧表示。入力待ちのセッションにはインラインで返信可能。`/bg`コマンドや`claude --bg`でバックグラウンドセッションを新規起動できる。対応プランはPro・Max・Team・Enterprise・Claude API。Dynamic Workflowsと組み合わせた並列エージェント運用で大規模タスクの効率が大幅向上。左矢印キーで任意セッションからAgent Viewに遷移できる。
