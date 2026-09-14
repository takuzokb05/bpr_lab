# Claude Skills Tutorial: Build Your First Skill in 10 Minutes (2026)

- URL: https://techsy.io/en/blog/claude-skills-tutorial
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-14

## 投稿内容
Hands-on tutorial for building a Claude Code skill from scratch in 10 minutes, published May 2026.

## 要約
Claude CodeのSkillを10分で作成するハンズオンチュートリアル（2026年5月公開）。SKILL.mdは2部構成：①YAMLフロントマター（trigger・description記述）＋②マークダウン指示本文。MCP vs Skills vs Hooks の判断マトリクス：外部サービス接続→MCP、再利用可能な手順ワークフロー→Skills、イベント駆動自動化→Hooks。チュートリアル実例：「daily-standup」スキル作成——Gitのコミット差分を要約してSlack投稿するワークフロー。フロントマター例：`trigger: "when I say daily standup"`と書くだけで自然言語での起動が可能。スキルの配置場所：プロジェクト用は `.claude/skills/<name>/SKILL.md`、グローバルは `~/.claude/skills/<name>/SKILL.md`。スキルとプラグインの違い（プラグインはコマンドとUI拡張、スキルはCLAUDE.md的なLLM指示）も明確化。
