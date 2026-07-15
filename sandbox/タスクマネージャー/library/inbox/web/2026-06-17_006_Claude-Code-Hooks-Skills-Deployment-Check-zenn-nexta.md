# Claude CodeのHooksとSkillsで社内展開チェックを自動化した

- URL: https://zenn.dev/nexta_/articles/962f0448a37d7a
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-06-17

## 要約
Zenn実践記事。Claude CodeのHooks（PostToolUse）とSkillsを組み合わせて「社内展開していいか」を自動チェックするシステムの実装事例。コード変更後に自動でセキュリティポリシー適合確認・依存パッケージライセンスチェック・機密情報スキャンを実行するフック設計。SKILL.mdにhooks frontmatterを直書きする方法を具体的なyaml付きで解説。従来の手動レビューを70%自動化、開発サイクル短縮の定量効果も報告。
