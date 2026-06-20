# CLAUDE.md と AGENTS.md のベストプラクティス比較（Izanami）

- URL: https://izanami.dev/post/47b08b5a-6e1c-4fb0-8342-06b8e627450a
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-06-20

## 要約
Izanami による CLAUDE.md と AGENTS.md の書き方ベストプラクティス比較記事（2026年）。CLAUDE.md は Claude Code 専用、AGENTS.md は OpenAI Codex・Gemini CLI・Claude Code 等の複数エージェント共通フォーマット。使い分け基準：単一エージェント環境は CLAUDE.md、マルチエージェント環境では AGENTS.md を推奨。共通の記述すべき内容：テックスタック・エントリーポイント・命名規則・build/test/lint コマンド・禁止事項。「やってはいけないこと」の明示が最も効果的で、300行以内・WHY/WHAT/HOW の3要素を簡潔に書くのがベストプラクティス。AGENTS.md の普及に伴いマルチエージェント環境での設定ファイル統一が進む傾向を紹介。プロジェクトスケール別のテンプレート例付き。
