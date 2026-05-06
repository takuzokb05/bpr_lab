# I see a lot of people trying to build AI Tools into QGIS or to get AI to control

- URL: https://twitter.com/lawrencejessej/status/2052129877189329348
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-06
- いいね: 0 / RT: 0 / リプライ: 1
- 投稿者: @lawrencejessej / フォロワー 1007

## 投稿内容
I see a lot of people trying to build AI Tools into QGIS or to get AI to control QGIS through an MCP server. Trying to get AI to use QGIS the way you're used to, but I think that is overthinking it a bit.

What I've come to learn is the agents like Claude Code or Codex are really good at using the command line. It was a bit tricky for me to understand at first because I've never used command line. I don't know what is possible, I didn't know what --flags were, how to ask for help etc. But that is the world agents are built in. Give them a terminal and a well-documented tool, and they will just go. They don't need a cursor. They don't need a window. They need a command, an input, and an output.

Part of why this works so well is something that doesn't get talked about much: CLI tools are light on context. When an MCP server loads up, it pushes its entire schema into the agent's working memory upfront, every tool, every parameter, whether the agent needs them or not. A CLI tool doesn't do that. The agent can just ask qgis_process --help, get a list of what's available, pick the one it needs, ask for the specific syntax, and go. It discovers capability on demand instead of loading everything at once. That's not just more efficient, it's actually how good agent-native tools are supposed to work.

And QGIS? QGIS is actually excellent at this. It has a full Python API, a headless processing framework, and a massive library of algorithms you can call directly from the command line via qgis_process. You can reproject, clip, rasterize, calculate indices, run terrain analysis, all without ever opening the GUI. The GUI is great for humans. The CLI is great for agents.

QGIS headless fits this conversation perfectly. You don't need to build a bridge. You don't even need to know the commands. You just have to ask your agent to try use qgis_process / qgis headless and make notes on how to make it work more smoothly next time.

The future of a lot of software isn't "the AI controls the GUI." It's "we don't need the GUI." Headless operation isn't a workaround, it's a feature. The agent reads your data, runs the tool, writes the output, checks if it worked, and iterates. No screen required.

I think the bigger concept here is to stop trying to adapt agents to human workflows, and start embracing what agents are actually good at. They love structured inputs. They love documented CLI tools. They love iteration loops where pass/fail is unambiguous. I think it is more important to think about how your current workflows should be updated to work with agents. How are your files being saved, organized, etc? What parts do you need to do? How can your agents work parallel to you?

For me I still prefer to try use agents to kick of deterministic workflows / python scripts, because I know the outputs are true and can be verified. But its such an interesting time to be playing with these tools.

## 要約
QGIS + AI活用の実践知見：MCPサーバーでGISツールを制御するより、Pythonスクリプトを書かせてQGISのPythonコンソールから実行させる方がClaude Code/Codexには向いていると指摘。エージェントにとってのツール制御のベストアーキテクチャについての洞察。
