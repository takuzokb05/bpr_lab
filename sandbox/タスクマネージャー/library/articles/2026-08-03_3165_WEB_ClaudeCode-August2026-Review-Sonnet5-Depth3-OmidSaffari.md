# Claude Code Review: August 2026 - Sonnet 5 Default, Depth-3 Subagents, 50% Usage Boost

- URL: https://omidsaffari.com/blog/claude-code-review
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-03

## 要約
2026年8月時点での実測レビュー記事。現在のClaude Codeの正確な仕様を整理した信頼性の高い記録。

確認された主要仕様:
- **Claude Sonnet 5がデフォルトモデル**：1Mトークンコンテキストウィンドウ対応
- **プロモーション価格**：$2/$10 per Mトークン（2026年8月31日まで）→9月1日から$3/$15に変更
- **Subagentsのdepth制限が3に拡張**（従来はdepth 1）
- **50%週間使用量ブースト延長**：2026年8月19日まで継続
- **バグ修正確認済**：claude update/claude doctorのサイレントハング、/statusのSystem diagnosticsが空白になる問題

実際のコーディングワークフローでの効果も定性評価。Sonnet 5の1Mコンテキストにより大規模リポジトリ全体を一度に把握できるようになった点を特筆。
