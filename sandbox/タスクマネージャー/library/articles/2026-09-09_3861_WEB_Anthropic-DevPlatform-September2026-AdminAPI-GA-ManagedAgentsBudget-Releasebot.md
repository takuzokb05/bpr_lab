# Anthropic Developer Platform 2026年9月アップデート — Admin API GA・Managed Agents Budget Controls・Fable 5.1

- URL: https://releasebot.io/updates/anthropic/claude-developer-platform
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-09

## 要約
Anthropic Developer Platform の2026年9月主要アップデートまとめ：

**Admin API ユーザー管理エンドポイントがベータ卒業（GA）**
Claude Enterprise（claude.ai）組織のメンバー管理・招待・グループ・カスタムロールを制御するAdmin APIエンドポイントが正式版移行。組織管理の自動化が本番利用可能に。

**新レスポンスヘッダー: anthropic-workspace-id**
APIレスポンスに `anthropic-workspace-id` ヘッダーが追加され、使用したAPIキー/トークンが紐付くワークスペースIDを返すようになった。マルチワークスペース運用でのデバッグ・監査が容易に。

**Claude Sonnet 5 価格正式化 — 値上げなし**
Sonnet 5の導入価格 $2/$10 per MTok が正式標準価格として確定。2026年9月1日予定だった値上げは行われず。

**Claude Managed Agents 新機能4つ**
Budget Controls（支出上限）・Advisor Support・Geo-Pinned Inference（データ所在地指定）・GitHub-Loaded Skills（GitHubリポジトリからスキル直接ロード）を追加。

**Fable 5.1 GA（2026年9月1日）**
Fable 5と同価格（$10/$50 MTok）でGA。キャッシュリード $0.25（Fable 5比で大幅値下げ）。Managed Agentsのエージェントモデルとしても完全サポート。

**Skills API・Files API が Microsoft Foundry で利用可能**
Google Cloud Vertex AI へのコンピュータ使用ツール（最新版）も近日公開予定。
