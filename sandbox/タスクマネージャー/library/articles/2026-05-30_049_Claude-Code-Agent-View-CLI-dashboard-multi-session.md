# Claude Code Agent View: 複数エージェントセッションを一元管理するCLIダッシュボード

- URL: https://claude.com/blog/agent-view-in-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-30

## 投稿内容
Agent view in Claude Code — Anthropic Blog, May 11, 2026. Claude Code now ships "agent view," a single CLI dashboard for managing multiple parallel agent sessions. Run `claude agents` or press left arrow from any session to open the view. Each row shows the session state (waiting/running/done), last response content, and when you last interacted. Reply inline when an agent awaits input. Launch new background sessions with `/bg` or `claude --bg`. Available as Research Preview on Pro, Max, Team, Enterprise, and Claude API plans. Eliminates the need for multiple terminal tabs or tmux grids for parallel agent workflows.

## 要約
Anthropicが2026年5月11日に「Agent View」を研究プレビューとして公開。Claude Codeで複数の並列エージェントセッションを単一CLIダッシュボードで一元管理できる新機能。`claude agents`コマンドで起動し、各セッションの待機状態・実行状況・最終レスポンス内容を一覧表示。入力待ちセッションへのインライン返信、`/bg`・`claude --bg`でのバックグラウンドセッション新規起動が可能。対応プランはPro・Max・Team・Enterprise・Claude API。Dynamic Workflowsと組み合わせた1,000並列サブエージェント運用を現実的にする重要UX改善。左矢印キーで任意セッションからAgent Viewに遷移でき、tmuxグリッドやタブ管理が不要になる。公式ブログによる一次情報。
