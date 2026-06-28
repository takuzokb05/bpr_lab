# Anthropic June 2026 Release Notes: MCPトンネル・サーバーサイドフォールバックBeta

- URL: https://releasebot.io/updates/anthropic
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-28

## 投稿内容
Anthropicの2026年6月リリースノート追跡（releasebot.io）。Claude Codeユーザー向けに重要な新機能を記録。

**主要新機能:**

**MCPトンネル（リサーチプレビュー）:** プライベートネットワーク内のMCPサーバーへの到達を可能にする機能。VPN不要でファイアウォール内部のMCPサーバーにClaudeからアクセスできるようになる。

**サーバーサイドフォールバックBeta:** ヘッダー`server-side-fallback-2026-06-01`を使用することで、拒否されたリクエストを同一ラウンドトリップ内で第2モデルに自動的にリトライする機能。コスト増なしに冗長性を実現。

**Rate Limits API:** 管理者がorg・ワークスペース制限をプログラマティックにクエリできるAPI。使用量管理の自動化が可能に。

**その他のリリース:**
- 2026年6月2日以降: 出力なしの拒否（コンテンツフィルタによる完全ブロック）に課金なし
- 2026年6月9日: Fable 5・Mythos 5 GA、同日Workload Identity Federation（WIF）GA（OIDCプロバイダーでキーレス認証）
- 2026年6月15日: Claude Sonnet 4・Opus 4廃止

**WIF詳細:** 任意のOIDC準拠アイデンティティプロバイダーを使ったキーレス認証を実現。API・SDK・Claude Code全体で静的APIキー管理が不要に。

## 要約
Anthropic 2026年6月リリースノートの追跡記事。新機能: MCPトンネル（リサーチプレビュー、プライベートネットワーク内MCPサーバーへのアクセス）、サーバーサイドフォールバックBeta（拒否時の自動第2モデルリトライ）、Rate Limits API（管理者向け使用量クエリ）。6月2日以降は出力なし拒否が無課金に。Fable 5/Mythos 5 GA（6/9）、WIF GA（OIDCキーレス認証）、Claude Sonnet 4/Opus 4廃止（6/15）も記録。
