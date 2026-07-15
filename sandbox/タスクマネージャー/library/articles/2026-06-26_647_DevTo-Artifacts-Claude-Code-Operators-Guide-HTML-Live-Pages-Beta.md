# Artifacts in Claude Code: The Operator's Guide — Live HTML Pages・Org-Only Share・Team Plan

- URL: https://dev.to/max_quimby/artifacts-in-claude-code-the-operators-guide-4fb0
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-26

## 投稿内容
Dev.to article by Max Quimby: "Artifacts in Claude Code: The Operator's Guide" — covering beta rollout, architecture, configuration, and security model for the Artifacts feature launched June 18, 2026.

## 要約
Claude Code Artifacts（2026年6月18日ベータ・組織限定）の運用ガイド。**Artifactsとは**: セッションコンテキストからClaude Codeが生成するself-contained HTMLページ。静的エクスポートではなく、セッション進行に伴いリアルタイム更新されるliveページ。プライベートURLで組織内のみ公開（外部公開不可）。**有効なユースケース**: PRウォークスルー・インシデントページ・依存関係ダッシュボード・マイグレーションチェックリスト・テスト結果サマリー等、ターミナル出力のままでは読みにくい情報のビジュアル化に最適。**プラン要件**: Team planでデフォルトON、Enterprise planでは管理者が設定変更可能、Pro/Maxでは利用不可。**セキュリティモデル**: ArtifactのURLはAnthropicサーバー上に存在するが組織外からはアクセス不可。バージョン履歴ベータ（Team/Enterprise限定）でArtifactの変遷を追跡可能。**設定キー**: `artifacts.enabled` / `artifacts.orgSharing` / `artifacts.versionHistory`。運用担当者向けの権限設定・監査ログの取り方も含む実務ガイド。
