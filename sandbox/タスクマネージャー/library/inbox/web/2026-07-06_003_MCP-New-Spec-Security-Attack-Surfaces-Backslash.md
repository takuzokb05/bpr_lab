# New MCP Spec Opens Three New Attack Surfaces — Security Review

- URL: https://www.backslash.security/blog/new-mcp-spec-opens-new-attack-surfaces
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-06

## 要約
セキュリティ企業 Backslash が MCP 2026-07-28 RC の新たな攻撃面を分析。ステートレス化で生じる3つのリスク：(1) リクエストごとの _meta インジェクション（クライアント情報偽装）、(2) MCP Apps の iframe サンドボックス回避、(3) Multi Round-Trip Requests でのサーバー起点 payload 改ざん。従来のセッション固定型では検知できたなりすましが困難になる可能性。MCP ゲートウェイでの署名検証・入力バリデーション強化を推奨。AI エージェント導入を検討するセキュリティチームが読むべき一次分析記事。定量的なCVSS等は未掲載だが脅威モデルが具体的。
