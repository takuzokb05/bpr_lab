# Claude Code Skills vs Hooks: What's the Difference and When to Use Each

- URL: https://www.mindstudio.ai/blog/claude-code-skills-vs-hooks-difference
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-08

## 投稿内容

Claude Code Skills と Hooks の動作原理の違いと使い分けを解説するガイド。Skills はYAML frontmatter付き SKILL.md ファイルで、Claude がメッセージと description を照合して自律的に読み込む。Hooks はライフサイクルポイントで自動実行されるシェルコマンドで Claude は存在を認識しない。

## 要約

Skills と Hooks は Claude Code の拡張機能だが、動作原理が根本的に異なる。Skills は Claude が description を読んで「このスキルを使うべきか」を自律判断する「引き込み型」の仕組み。一方 Hooks は PreToolUse / PostToolUse / Stop / SessionStart 等のライフサイクルポイントでシェルコマンドを自動実行する「押し付け型」の仕組みで、Claude の思考に一切影響しない。推奨使い分け：「Skills → まず導入、即効果」「Hooks → 決定論的な強制執行が必要な時（フォーマッタ・リンタ等）」「Subagents → 並列作業や文脈分離が必要な時」。実践例として、コード品質チェックを CLAUDE.md に書くのではなく Stop Hook で実行する設計が効果的。Skills が「Claude に任せる」なら Hooks は「システムが保証する」という対比で理解できる。
