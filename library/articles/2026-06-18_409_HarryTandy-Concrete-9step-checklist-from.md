# Concrete 9-step checklist from Google Cloud AI Director Addy Osmani for turnin

- URL: https://x.com/HarryTandy/status/2066970581229031432
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-18
- いいね: 6 / RT: 3 / リプライ: 3
- 投稿者: @HarryTandy / フォロワー 23,616

## 投稿内容

Addy Osmani, Google Cloud AI Director:

"The harness is the environment one single agent runs inside"

9-step checklist for turning default Claude Code into repeatable work:

1. Start with the 4 surfaces
- model
- tools
- permissions
- context

2. Write the project facts
- this repo uses `pnpm`
- where tests live
- what files are dangerous

3. Cut `CLAUDE.md` down
If it reads like a tutorial, make it a Skill

4. Add safe approvals
Read, grep, test, lint
Cheap actions should not stop every run

5. Deny the bad exits
- secrets
- force pushes
- destructive shell commands
- production writes

6. Split maker and checker
Main agent edits
Reviewer subagent inspects the diff and runs the app

7. Turn repeated work into Skills
- one workflow
- one `SKILL.md`
- one clear trigger

8. Use hooks for rules the model must obey
Exit code 2 blocks the action before charm can enter the room

9. Write memory at the end
- failed command
- accepted fix
- next file to inspect

The rule:

> context tells Claude where it is
> permissions decide what it can touch
> hooks stop the dumb move
> reviewer checks the artifact
> memory makes tomorrow less repetitive

Default Claude Code is fine for a one-off fix

Repeated work needs a runtime with receipts

## 要約

Concrete 9-step checklist from Google Cloud AI Director Addy Osmani for turning default Claude Code into repeatable work, covering model/tools/permissions/context surfaces。
投稿者 @HarryTandy（フォロワー23,616人）によるclaude-code関連情報。
投稿内容の要点: Addy Osmani, Google Cloud AI Director:
