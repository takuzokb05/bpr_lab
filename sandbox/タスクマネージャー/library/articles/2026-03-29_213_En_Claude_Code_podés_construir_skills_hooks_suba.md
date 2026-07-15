# En Claude Code podés construir skills, hooks, subagents y MCP servers.

- URL: https://x.com/santtiagom_/status/2037625521735954850
- ソース: x
- 言語: es
- テーマ: claude-code
- 取得日: 2026-03-29
- いいね: 287 / RT: 18 / リプライ: 10
- 投稿者: @santtiagom_ / フォロワー 37,114

## 投稿内容

En Claude Code podés construir skills, hooks, subagents y MCP servers.

Pero, ¿cómo compartís todo eso con tu equipo o con la comunidad?

Con plugins.

Un plugin es una forma de empaquetar esas capacidades para que otra persona las instale y las use directamente.

¿Cómo se arma?

Es una carpeta con una estructura definida.

Tiene un archivo obligatorio:
.claude-plugin/plugin.json → define el plugin (nombre, versión y configuración)

A eso le sumás lo que quieras compartir:
- skills/<nombre>/SKILL.md
- agents/ → agentes (.md)
- hooks/hooks.json
- .mcp.json → MCP servers

Lo publicás en un marketplace (un lugar donde se distribuyen plugins). Hay uno oficial de Anthropic.

Otra persona lo instala desde Claude Code:
/plugin install <nombre-del-plugin>

Y Claude Code lee la estructura, registra las skills, activa los agentes y conecta los MCP.

Así, quien instala tu plugin pasa a tener tus skills, agentes y automatizaciones listas para usar.

## 要約

（要約は次回 /curate 時に追記）
