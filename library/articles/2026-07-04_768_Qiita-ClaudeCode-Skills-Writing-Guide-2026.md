# 【2026年最新】Claude Code Skills の書き方完全ガイド ─ 自作 Skill で業務が別物になる

- URL: https://qiita.com/kawabe0201/items/e1a7dfbd7f363001f66e
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-07-04

## 投稿内容

著者：川辺煌士（@kawabe0201）。Claude Code Skills の設計・実装ガイド。

**Skillとは：**
再利用可能な「手順書とトリガー条件」を frontmatter 付き Markdown ファイルとして管理する仕組み。`~/.claude/skills/`（グローバル）または `.claude/skills/`（プロジェクト専用）に配置。

**frontmatter仕様：**
必須要素は `name` と `description`。特に「description の書き方が Skill の起動率を決める」という原則が強調されており、具体的で1〜2文の説明が重要。

**実践例3件：**
1. **commit Skill**：Conventional Commits 形式でのコミット自動化
2. **review-pr Skill**：GitHub PR の徹底レビュー自動化
3. **deploy Skill**：本番環境デプロイの安全自動化

**description作成の5原則：**
1. 具体的な動詞で開始
2. 対象を明示
3. 副次効果を記載
4. トリガー条件を明確化
5. 1〜2文に収める

**設計哲学：** 「Skill は単なるスニペット置き場ではなく、起動条件まで含めた再利用可能な手順書」として設計することで開発体験が大きく変わる。

## 要約

Claude Code Skills（SKILL.md）の実践的設計ガイド。description の品質が Skill の自動起動率を左右するという重要な知見を提供。具体的な動詞・対象・副次効果・トリガー条件を1〜2文に凝縮する5原則が実用的。コミット・PRレビュー・デプロイという開発ライフサイクル全体をカバーする3つの実例を含む。既存の Skills 記事が概念説明に留まることが多い中、起動率向上のためのdescription設計という実践的視点が独自性。Qiita での公開により日本語圏の Claude Code 利用者へのアクセスが高い。
