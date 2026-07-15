# Claude Code HooksとSkillsで「社内展開チェック」を自動化した実装事例（JA）

- URL: https://zenn.dev/nexta_/articles/962f0448a37d7a
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-06-17

## 要約
Zenn実践事例記事。PostToolUse hookとSkillsを組み合わせて社内展開前チェック（セキュリティポリシー適合・OSS依存ライセンス・機密情報スキャン）を自動実行するシステム実装。SKILL.mdのfrontmatterにhooksを直書きして単一ファイルで管理する具体的yaml構文付き。効果：従来の手動レビュー工程を70%自動化し、PR提出から承認までのサイクルタイムを削減。サブエージェントとの連携（チェック用サブエージェントを別権限で起動）パターンも解説。GitHubリポジトリへのスキルファイル共有で組織横断の標準化を実現した経験談。
