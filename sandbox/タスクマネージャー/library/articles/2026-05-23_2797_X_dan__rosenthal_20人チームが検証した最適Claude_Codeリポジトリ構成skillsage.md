# 20人チームが検証した最適Claude Codeリポジトリ構成（skills/agents/commands/hooks/rules）

- URL: https://x.com/dan__rosenthal/status/2058261757672538541
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-23
- いいね: 15 / RT: 9 / リプライ: 1
- 投稿者: @dan__rosenthal / フォロワー 3,205

## 投稿内容
There’s an abundance of bad advice out there on AI.

We tested 10+ folder structures across a 20-person AI-native services team.

Here's the optimal Claude Code repo layout we landed on:

1) .claude/skills/
↳ One file per skill, flat in the folder
↳ Each skill handles one task end-to-end

2) .claude/agents/
↳ For longer workflows nested inside a skill

3) .claude/commands/
↳ Slash commands that string multiple skills together

4) .claude/hooks/
↳ Controls what Claude can and can't do based on who's running it
↳ Tiered approvals by user role

5) .claude/rules/
↳ Tells Claude how to behave depending on what file it's working in

The repo root carries CLAUDE(.)md, INDEX(.)md, wiki/, clients/, raw-context/, archive/.

For non-technical GTM teams, this is the #1 reason you NEED to switch to Claude Code.

## 要約
X投稿。テーマ: claude-code。投稿者 @dan__rosenthal（フォロワー 3,205人）。いいね15・RT9。20人チームが検証した最適Claude Codeリポジトリ構成（skills/agents/commands/hooks/rules）
