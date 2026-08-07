# Stateless MCP Is Here: What the 2026-07-28 Spec Changes and How to Host a Fleet on One Bun Process

- URL: https://www.developersdigest.tech/blog/stateless-mcp-2026-spec-bun-fleet
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-07

## 要約

MCP 2026-07-28仕様のstateless化に伴い、複数MCPサーバーをBun単一プロセスで運用する実装パターンを解説。

**MCP stateless化の変更点まとめ**:
- `initialize`/`initialized`ハンドシェイク廃止
- `Mcp-Session-Id`ヘッダー廃止
- 各リクエストが`_meta`でprotocol version・client info・capabilitiesを自己申告
- 結果: ラウンドロビンLBやサーバーレス・エッジへのデプロイが可能に

**Bunを使った複数サーバーフリート化の手法**:
- 従来: MCPサーバー1個 = プロセス1個 = メモリ・コスト増
- 新手法: Bunの単一プロセス内でsub-routerとして複数MCPサーバーを動作させる
- `Mcp-Method`ヘッダーでルーティング
- メモリ共有・Cold start不要でエッジデプロイに最適

**実装コード骨格**（TypeScript/Bun）:
```typescript
const server = Bun.serve({ fetch: router }) // 1プロセスで複数MCPを捌く
```

**移行戦略**:
1. 隠れたセッション状態をインベントリ化
2. `server/discover`を追加
3. リスト結果を決定論的・キャッシュ対応に
4. 少なくとも12ヶ月は旧パスを維持

**なぜ重要か**: Claude Codeのローカルおよびサーバー側MCPインフラの簡素化・コスト削減に直結。
