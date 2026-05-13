# .claudeフォルダはプロジェクトの「OS」：CLAUDE.md・hooks・skillsの深掘り

- URL: https://x.com/meunclefarm/status/2054667738745110879
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-13
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @meunclefarm / フォロワー 687

## 投稿内容
This is one of the most valuable deep dives I've seen on Claude Code. The .claude folder really is the "operating system" for how Claude behaves in a project, and most people are only scratching the surface.
What stood out most:
•  The clear separation between project-level (team-committed) and global ~/.claude/ (personal) configs — this is huge for teams.
•  Using rules/ with path-scoped YAML frontmatter instead of bloating CLAUDE.md.
•  The power of hooks for deterministic control (especially PreToolUse as a security gate and Stop hooks for quality enforcement).
•  Skills and Agents as the next-level packaging for reusable workflows.
Treating CLAUDE.md like institutional memory instead of just prompt text is a game-changer. This post just leveled up how I'll configure every new project from now on.
Thank you for the incredibly thorough breakdown, Akshay — bookmarking and sharing this with the team. 🔥

## 要約
.claudeフォルダの設計思想を「プロジェクトのOS」と表現した深掘り解説への反応。具体的に紹介される4つのポイントが重要：①プロジェクトレベル（チームコミット）とグローバル~/.claude/（個人）の明確な分離、②CLAUDE.mdを膨らませる代わりにrules/ディレクトリにパススコープYAMLフロントマターを使う手法、③PreToolUseをセキュリティゲートとして・Stop hooksを品質管理に使うhooksの決定論的制御、④再利用可能ワークフローのパッケージングとしてのSkillsとAgents。CLAUDE.mdを「プロンプトテキスト」ではなく「組織の制度記憶（institutional memory）」として扱う視点が特に有益。
