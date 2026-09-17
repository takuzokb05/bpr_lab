# MCP protocol receives major update: more secure and production-ready

- URL: https://itdaily.com/news/software/mcp-2026-update-specs/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-17

## 要約
2026-07-28仕様のMCPプロトコル大型アップデートを解説する記事（ITdaily.com）。

**最大の変更: ステートレス・リクエスト中心アーキテクチャ**
- ステートフル（セッション維持必須）→ ステートレス（各リクエストが情報を自己完結）
- 結果: 普通のラウンドロビン負荷分散器の後段でサーバーが動作可能に
- Mcp-Method / Mcp-Name HTTPヘッダーでゲートウェイがルーティング・認可を直接実行可能
- tools/listレスポンスをクライアントがキャッシュできるようになった

**実際の影響**:
- 以前は「スティッキーセッション+共有セッションストア+ディープパケットインスペクション」が必要だったサーバーが、シンプルなロードバランサーと Mcp-Method ヘッダーだけで運用可能に
- エンタープライズ規模でのMCP本格導入が現実的に

**その他の改善**:
- セキュリティ強化（厳格な認可制御+ローカル結果キャッシュ）
- 廃止コンポーネントは最低12ヶ月動作保証（開発者の移行猶予）
- TypeScript・Python・Go・C# SDKも同時更新（v2）

**ガバナンス**: Agentic AI Foundation（Linux Foundation傘下）がAnthropicやOpenAI・Google・Microsoft・AWSと共に管理。2024年のオープンソース化から18ヶ月の実運用フィードバックを反映した安定版。月間SDKダウンロード9,700万回超・GitHub star 86,000超。
