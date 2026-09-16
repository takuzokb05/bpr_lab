# Claude Code Skills・Hooks・MCP 使い分け業務自動化実践レシピ（romptn Magazine）

- URL: https://romptn.com/article/105358
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-09-16

## 要約
romptn Magazineに掲載されたClaude Code 3機能（Skills/Hooks/MCP）の業務シーン別使い分けガイド。使い分けの基本原則：「Skillsは知識・手順の再利用」「Hooksは自動実行の保証」「MCPは外部システム連携」。具体的なレシピ例：①コードレビュースキル（Skills）→ /review-pr コマンドで標準化②コミット前の品質チェック（Hooks）→ PreToolUse: GitでLint自動実行③Slack通知（MCP）→ 長時間タスク完了後に自動投稿。3機能を組み合わせた業務自動化フロー（朝会議録→Skills整形→MCP投稿→Hooks確認）も紹介。初心者向けに「まずHooksから始める」学習順序も提案。
