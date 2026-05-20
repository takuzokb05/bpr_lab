# Anthropic acaba de resolver el problema que frenaba a las empresas grandes con I

- URL: https://x.com/teKa088/status/2056718296393691606
- ソース: x
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-20
- いいね: 2219 / RT: 161 / リプライ: 33
- 投稿者: @teKa088 / フォロワー 9369

## 投稿内容
Anthropic acaba de resolver el problema que frenaba a las empresas grandes con IA agéntica:

Antes: tu agente necesitaba acceso a tu MCP server → tenías que exponerlo a internet público → área legal decía no

Ahora: MCP tunnel crea un canal seguro vía tunnel .anthropic.com → el agente llega a tu servidor interno sin que salga nada a la red pública

Tu firewall, tus políticas, tu perimeter. El agente opera adentro.

Self-hosted sandboxes (beta pública) + MCP tunnels (research preview) = Claude Managed Agents corre en tu infraestructura

## 要約
AnthropicのMCPトンネルの技術解説：tunnel.anthropic.com経由でエンタープライズのファイアウォール内部からMCP接続を実現
