# Claude Code Compliance API 拡張：Cowork+Claude CodeのセッションをEnterpriseが一括取得可能（公式ベータ）

- URL: https://claude.com/blog/compliance-api-cowork-and-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-12

## 投稿内容
AnthropicがCompliance APIの適用範囲をCowork（デスクトップ/Web/モバイル）とClaude Code（CLI/デスクトップ）に拡張すると発表。Claude Enterprise顧客向けのベータ機能として提供開始。セキュリティ・コンプライアンスチームは、既存のCompliance APIインターフェースを通じて両製品のセッション内容とメタデータを一括取得できる。

**取得可能データ（セッションコンテンツ）：**
- プロンプト・レスポンス
- ツール呼び出し内容
- スキル・アーティファクトの転写テキスト

**取得可能データ（メタデータ）：**
- 検証済みユーザーID・メールアドレス
- 組織ID
- セッションID・メッセージID
- タイムスタンプ

eDiscoveryや内部監査対応に活用可能。2026年8月時点でベータ、Claude Enterpriseプランのみ対応。

## 要約
Claude Code v2.1.224（2026年8月7日）に続くAnthropicのエンタープライズ強化策第2弾。Compliance APIがCoworkとClaude Codeのセッションデータ取得に対応したことで、金融・医療・法律など規制産業での利用が現実的になった。これまでCompliance APIはClaude Chatのみ対象だったが、今回の拡張でコーディングエージェントの使用記録も一元管理できる。自社セルフホストランナー（v2.1.224追加）と組み合わせることで、「自社インフラで実行＋監査ログ取得」という完全なエンタープライズ要件を満たすことが可能になった点が重要。Claude CodeとCoworkが同一APIで管理できる統合性も評価ポイント。
