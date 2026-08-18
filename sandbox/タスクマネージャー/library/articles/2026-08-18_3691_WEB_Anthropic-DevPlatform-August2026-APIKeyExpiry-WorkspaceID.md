# Anthropic Developer Platform August 2026: APIキー有効期限・ワークスペースID・メモリAPI安定化

- URL: https://releasebot.io/updates/anthropic/claude-developer-platform
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-18

## 要約

Anthropic Developer Platformの2026年8月アップデート群。開発者向け運用・セキュリティ機能が充実した。

### 主要アップデート

**APIキー有効期限設定（新機能）**
Claude ConsoleでAPIキー作成時に有効期限を設定可能になった。7日以上のライフタイムを持つキーは期限前にメール通知が届く。セキュリティポリシー強化・コンプライアンス対応に有効。

**anthropic-workspace-idレスポンスヘッダー**
APIレスポンスに使用されたワークスペースIDが含まれるようになった。マルチワークスペース環境でのデバッグ・課金追跡・アクセス制御検証が容易に。

**agent-memory-2026-07-22 betaヘッダー**
メモリリスティングがサーバー定義の安定順序を返すように。SDKがデフォルトで新メモリストアヘッダーを送信するようになった。エージェントの永続メモリ機能が本格化。

**Claude Sonnet 5 価格永久固定（重要）**
9月1日からの$3/$15/MTok値上げ予定がキャンセルされ、現行の$2/$10が恒久価格に確定。量成長戦略への明確な転換。

これらの変更により、Anthropic APIを本番運用で使用している開発者は特にAPIキー有効期限設定とワークスペースID追跡の実装を検討すべき。
