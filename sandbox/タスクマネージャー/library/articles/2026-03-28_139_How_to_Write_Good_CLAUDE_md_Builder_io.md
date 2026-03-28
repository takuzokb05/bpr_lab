# How to Write a Good CLAUDE.md File (Builder.io)

- URL: https://www.builder.io/blog/claude-md-guide
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-28

## 要約

CLAUDE.mdの効果的な書き方について、フロンティアLLMの実験結果に基づいた実践ガイド。
- **150〜200命令の上限**: それを超えると全命令の遵守率が一様に低下するという実測データ
- **Progressive Disclosureパターン**: CLAUDE.mdには情報の場所を書き、詳細はSkillsや`.claude/rules/`に委譲
- 悪い例：「Reactを使え」→ 良い例：「技術スタックは`TECH_STACK.md`を参照せよ」
- CLAUDE.mdを「常に読まれる設定ファイル」ではなく「コンテキスト効率を最大化するインデックス」として設計する考え方

実際の良い例・悪い例を対比した具体的なBefore/Afterが含まれており、CLAUDE.md改善に直結する内容。
