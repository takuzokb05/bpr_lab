# CLAUDE.md Best Practices Ultimate Guide 2026 — 10必須セクション・3層構造・削除基準

- URL: https://amitray.com/best-practices-for-claude-md/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-02

## 投稿内容
amitray.comによるCLAUDE.md設計の決定版ガイド（2026年）。P-002・P-015提案の実装に直接対応する内容。

**3層構造（推奨）**
- **Layer 1**: CLAUDE.md本体 → 必須情報のみ（500語以内）
- **Layer 2**: `.claude/rules/` → トピック別分離（`@.claude/rules/fx-trading.md`等でインポート）
- **Layer 3**: Skills → 専門知識・手順書

**CLAUDE.mdに含める10項目**
1. プロジェクト概要（1-2文）
2. 技術スタック・バージョン
3. エントリーポイント
4. ビルド/テスト/lintコマンド
5. 命名規則
6. コーディングスタイル
7. 禁止事項（絶対にやらないこと）
8. 環境変数
9. 外部依存
10. よくある落とし穴

**削除基準**
「削除してもClaudeが間違えないなら削除」— ブロートしたCLAUDE.mdは重要ルールの遵守率を低下させる。

**@インポート構文**
```
@.claude/rules/fx-trading.md
@.claude/rules/coding-style.md
```

**チーム運用**
CLAUDE.mdをgitでチーム管理すると時間とともに改善される。CLAUDE.local.mdで個人設定を分離。

## 要約
amitray.comによるCLAUDE.md設計の決定版ガイド（2026年）。3層構造（CLAUDE.md→.claude/rules/→Skills）、10必須セクション、500語以内の削除基準を包括的に解説。
@インポート構文（`@.claude/rules/fx-trading.md`等）でトピック別ファイルに分散管理する設計パターンが有用。
削除基準「削除してもClaudeが間違えないなら削除」は過剰なCLAUDE.mdが重要ルール遵守率を低下させる問題への実践的対処法。
チームでgit管理することでCLAUDE.mdが改善される仕組みと、CLAUDE.local.mdによる個人設定分離も解説。
P-002（CLAUDE.md整備）・P-015（3層構造への移行）の実装参考として最も直接的に活用できる記事。
