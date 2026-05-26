# How to vibe code games using agent skills  Set up Claude Cod...

- URL: https://x.com/alphabatcher/status/2059380037359432077
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-26
- いいね: 3 / RT: 0 / リプライ: 2
- 投稿者: @alphabatcher / フォロワー 51952

## 投稿内容
How to vibe code games using agent skills

Set up Claude Code + Nexus like this:

> install Claude Code: `npm install -g @anthropic-ai/claude-code`
> open your Unity / Unreal / Godot project
> run `claude`
> create `CLAUDE.md` in the project root
> start Nexus Router v0.5.0+
> enable Anthropic protocol in `nexus.toml`
> set `ANTHROPIC_BASE_URL=http://localhost:6000/llm/anthropic`
> set `ANTHROPIC_MODEL=anthropic/claude-sonnet-4-5`
> run `claude mcp add nexus http://localhost:6000/mcp --transport http`
> confirm with `claude mcp list`

In `CLAUDE.md`, write:

> Engine
> Language
> Genre
> Current build
> Active task
> Coding conventions
> File structure
> Movement-controller patterns
> Files Claude cannot touch

First prompt:

> Build a double-jump mechanic
> second jump has 70% of first jump power
> add a particle burst at peak of second jump
> use the existing movement-controller patterns
> do not edit locked files from `CLAUDE.md`
> run the relevant tests after

After it works, tune:

> coyote time
> input buffer
> jump curve
> second-jump force
> particle timing
> landing audio
> camera shake
> controller feel

## 要約
How to vibe code games using agent skills

Set up Claude Code + Nexus like this:

> install Claude Code: `npm install -g @anthropic-ai/claude-code`
> open your Unity / Unreal / Godot project
> run `claude`
> create `CLAUDE.md` in the project root
> start Nexus Router v0.5.0+
> enable Anthropic proto...
