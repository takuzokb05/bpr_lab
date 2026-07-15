# MCP 2026-07-28 Spec: What Changed, What Breaks — Migration Guide

- URL: https://stacktr.ee/blog/mcp-2026-spec-changes
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-06

## 投稿内容
MCP 2026-07-28 RC の破壊的変更と移行ガイド。ステートレス化によりinitialize/initializedハンドシェイクとMcp-Session-Idヘッダが廃止。全リクエストにMcp-Method・Mcp-Nameヘッダが必須。Roots・Sampling・Loggingが非推奨（12ヶ月後削除）。Multi Round-Trip Requests（SEP-2322）でサーバー起点samplingを代替。ttlMs/cacheScopeによるキャッシュ制御（SEP-2549）追加。ロードバランサ対応が容易になる一方、既存サーバーのセッション管理ロジック全廃が必要。Tier 1 SDKは10週以内対応が求められる。

## 要約
MCP 2026-07-28 RC の破壊的変更を網羅した開発者向けマイグレーションガイド。プロトコルがステートレス化され、initialize/initialized ハンドシェイクと Mcp-Session-Id ヘッダが廃止。全リクエストに Mcp-Method・Mcp-Name ヘッダが必須となる。Roots・Sampling・Logging の3プリミティブが Deprecated 指定され、12ヶ月後に削除予定。Multi Round-Trip Requests（SEP-2322）でサーバー起点の sampling を代替。ttlMs/cacheScope によるキャッシュ制御（SEP-2549）も追加。ロードバランサ対応が容易になる一方、既存サーバーはセッション管理ロジックを全廃する必要があり移行コストが大きい。
