# Anthropic Claude Developer Platform 8月2026アップデート全解説

- URL: https://releasebot.io/updates/anthropic/claude-developer-platform
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-28

## 要約

Anthropic Developer PlatformのAugust 2026主要アップデート（Releasebot集計）。

**APIの重要変更**:
- **Computer Use正式GA**: `computer_toolset_20260801` として beta 終了。バッチアクション対応、ズームデフォルト有効
- **Browser Use新ツールセット**: `browser_toolset_20260801` でホストされたブラウザを操作。要素参照・フォーム入力・タブ管理・ダウンロード報告
- **Files API beta終了**: `files-api-2025-04-14` betaヘッダー不要に。有効期限制御・ページネーション追加
- **Skills API beta終了**: `skills-2025-10-02` ヘッダー不要に
- **anthropic-workspace-id レスポンスヘッダー**: APIキーが解決したワークスペースの `wrkspc_` プレフィックスIDを返す

**SDK更新（8/27）**:
- Python 1.2.0・TypeScript 0.122.0・Go 1.68.0等がfiles/skills APIのbetaヘッダーを自動削除
- `BetaSkill` → `BetaContainerSkill` にリネーム
- スキル削除が全バージョン同時削除に変更

**Admin API GA**:
- Claude Enterprise向けユーザー管理エンドポイント（メンバー・招待・グループ・カスタムロール）が正式GA
- `anthropic-beta` ヘッダー不要に
- CLI + 7 SDKで `client.beta.organization` として利用可能

**料金確定**:
- Claude Sonnet 5: 入門価格 $2/$10/Mトークン が正式定価に（9/1値上げなし）
- Claude Opus 5: $5/$25/Mトークン（Opus 4.8と同価格）、1Mコンテキスト、128k最大出力、思考モードデフォルト有効

**その他**: Managed Agentsに予算管理・アドバイザー対応・地理的推論ピン・GitHubロードスキル機能追加。Inference hooks（beta）でAIセキュリティサーバー承認ワークフロー対応。

**なぜ重要**: Computer Use・Browser Use・Skills APIがすべてbetaを卒業。本番利用の安定性が増し、FX自動取引システムへの組み込みも現実的に。
