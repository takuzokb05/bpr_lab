# 【2026年最新】Claude Code Skills の書き方完全ガイド

- URL: https://qiita.com/kawabe0201/items/e1a7dfbd7f363001f66e
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-07-04

## 要約
Claude Code Skills の設計・実装ガイド（川辺煌士著）。Skillは再利用可能な「手順書+トリガー条件」をfrontmatter付きMarkdownで管理する仕組み。配置先は `~/.claude/skills/`（グローバル）または `.claude/skills/`（プロジェクト専用）。必須frontmatterは `name` と `description`。「description の書き方がSkillの起動率を決める」という原則を強調、具体的動詞で始め1〜2文に収めることを推奨。実践例3件：commit Skill（Conventional Commits形式での自動化）・review-pr Skill（GitHub PR徹底レビュー）・deploy Skill（本番環境デプロイの安全自動化）。description作成5原則：具体的な動詞で開始・対象を明示・副次効果を記載・トリガー条件を明確化・1〜2文に収める。「Skillは単なるスニペット置き場ではなく起動条件まで含めた再利用可能な手順書」という設計哲学を提唱。
