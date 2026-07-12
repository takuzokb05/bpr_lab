# 【Claude Code】skill.md とは？書き方の最短ルートと運用で気をつけること

- URL: https://www.playpark.co.jp/blog/skill-md-guide
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-07-12

## 要約
合同会社playparkによるClaude Code SKILL.md実践ガイド。SKILL.mdの基本構造（frontmatter + 本文）、descriptionフィールドの重要性、配置場所（.claude/skills/スキル名/SKILL.md）を解説。

**核心的な設計原則**:
- Claude Codeはセッション起動時に全SKILL.mdのdescriptionのみを読み込んで一覧化し、ユーザー発話との意味的マッチングに使用
- descriptionは「このスキルを呼ぶべき状況」を自然文で記述する（検索クエリとして機能）
- 本体（本文）は使用時のみ読み込まれるため、長くても初期トークンコストはゼロ

**実践的なポイント**:
- frontmatterは最低限`description`だけで動作する
- スキル名（ディレクトリ名）はClaude Codeに表示される識別子になるため、意味が伝わる名前を選ぶ
- 運用上の注意：descriptionが曖昧だと誤トリガーや未トリガーが発生する

**配置の仕組み**:
- プロジェクト固有: `.claude/skills/スキル名/SKILL.md`
- 全プロジェクト共通: `~/.claude/skills/スキル名/SKILL.md`

初めてスキルを作る実践者向けの最短ルート解説。既存の_844（Techsy Skills Tutorial）や_852（Syusodo Skills推奨）と相補的な視点（運用上の落とし穴を重視）で価値あり。
