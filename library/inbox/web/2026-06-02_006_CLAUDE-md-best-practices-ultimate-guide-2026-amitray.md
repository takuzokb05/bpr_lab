# CLAUDE.md Best Practices: Ultimate Guide 2026 (amitray.com)

- URL: https://amitray.com/best-practices-for-claude-md/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-02

## 要約
amitray.comによるCLAUDE.md設計の決定版ガイド（2026年）。
3層構造の推奨：Layer 1（CLAUDE.md本体）に必須情報のみ・Layer 2（.claude/rules/）にトピック別分離・Layer 3（Skills）に専門知識。
必須含有コンテンツ10項目：プロジェクト概要、技術スタック・バージョン、エントリーポイント、ビルド/テスト/lintコマンド、命名規則、コーディングスタイル、禁止事項、環境変数、外部依存、よくある落とし穴。
削除基準: 「削除してもClaudeが間違えないなら削除」の原則。500語以内を厳守。
CLAUDE.mdの@インポート構文を使い、`@.claude/rules/fx-trading.md`等でトピック別ファイルを参照する設計を推奨。
チームでgit管理することでCLAUDE.mdが改善される仕組みが説明されており、P-002・P-015提案の実装参考として有用。
