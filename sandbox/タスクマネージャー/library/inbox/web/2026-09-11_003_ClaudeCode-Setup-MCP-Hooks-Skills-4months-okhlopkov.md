# My Claude Code Setup After 4 Months of Daily Use (MCP, Hooks, Skills)

- URL: https://okhlopkov.com/claude-code-setup-mcp-hooks-skills-2026/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-11

## 要約
4ヶ月のClaude Code日常利用を経た実践者によるセットアップ全公開。ポイント：① MCP設定：GitHub MCP（PR/Issue操作）・Filesystem MCP・Postgres MCP（スキーマ参照）をメイン利用、設定は `~/.claude/settings.json` のグローバルに置き特定プロジェクトで上書き ② Hooks：`PreToolUse` で危険なシェルコマンド（rm -rf等）を遮断、`PostToolUse` でファイル変更後に自動lint実行 ③ Skills：デプロイスキル・コードレビュースキル・DBマイグレーションスキルの3本柱で繰り返し作業をテンプレート化 ④ CLAUDE.md：コンテキスト管理の核、150行以内でアーキテクチャ・禁止事項・頻出コマンドを記述 ⑤ Plan Modeの活用：実装前に `/plan` で設計レビューをClaude任せにすることでリグレッション削減 ⑥ Subagentsのworktree活用：gitのworktree機能と組み合わせて並列開発 ⑦ 「最も効いたのはHooksによる自動lint」「スキルは5本以上になると管理コストが上がる」などの実体験知見を含む。
