# Claude Code April 2026 Update: /powerup, MCP 500K, Session Stability

- URL: https://daily1bite.com/en/blog/ai-tutorial/claude-code-april-2026-update
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-07

## 要約

Claude Code v2.1.89〜v2.1.92（2026年4月）の4大変更を解説：
- **/powerup** (v2.1.90、4月1日): インターミナルインタラクティブ学習。10レッスン各3〜10分、アニメーションデモ付き。コンテキスト管理・Hooks・MCP・サブエージェント・/loop等をカバー
- **MCP 500K**: MCPサーバーの結果ストレージ上限を500Kキャラクタへ拡大（大量データ取得が可能に）
- **defer permission**: PreToolUseフックに「defer」第3選択肢追加。allow/denyに加え「外部シグナル待機」が可能になり、外部承認ワークフロー構築が現実的に
- **/cost拡張**: モデル別・キャッシュヒット別コスト内訳（Proサブスクリプション向け）

特に「defer」は Hooks設計の拡張として重要。/release-notesがインタラクティブ版ピッカーに変更。
