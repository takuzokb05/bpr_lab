# Anthropic Developer Platform 2026年9月更新まとめ — Admin API GA・Managed Agents Budget Controls・Fable 5.1 GA

- URL: https://releasebot.io/updates/anthropic/claude-developer-platform
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-09

## 要約
Anthropic Developer PlatformのReleasebot 2026年9月アーカイブより、主要アップデートをまとめた。

**Admin API ユーザー管理エンドポイントがベータ卒業（GA）**
Claude Enterprise（claude.ai）組織のメンバー管理・招待・グループ・カスタムロールを制御するAdmin APIエンドポイントが正式版へ移行。組織管理の自動化が本番利用可能になった。

**新レスポンスヘッダー: anthropic-workspace-id**
APIレスポンスに `anthropic-workspace-id` ヘッダーが追加され、リクエストに使用したAPIキーまたはアクセストークンが紐付くワークスペースIDを返すようになった。マルチワークスペース運用でのデバッグ・監査が容易になる。

**Claude Sonnet 5 価格正式化**
Sonnet 5の導入価格 $2/$10 per MTok が正式標準価格となり、2026年9月1日予定だった値上げは行われないことが確定。

**Claude Managed Agents: Budget Controls・Advisor Support・Geo-Pinned Inference・GitHub-Loaded Skills**
Managed Agentsセッションに4つの新機能追加：（1）Budget Controls（支出上限設定）、（2）Advisor Support（技術的ガイダンス）、（3）Geo-Pinned Inference（推論のデータ所在地指定）、（4）GitHub-Loaded Skills（GitHubリポジトリからのスキル直接ロード）。

**Fable 5.1 GA（2026年9月1日）**
Fable 5と同じ$10/$50 MTok価格でGA。キャッシュリード $0.25（Fable 5比で大幅値下げ）。Managed Agentsのエージェントモデルとしても完全サポート。

**Skills API・Files APIがMicrosoft Foundryで利用可能**
Google Cloud Vertex AIへのコンピュータ使用ツール（最新版）も近日公開予定。
