# Claude Code実戦Tips: 初日から知っておきたかった教訓（プランモード・コンテキスト・検証）

- URL: https://marmelab.com/blog/2026/04/24/claude-code-tips-i-wish-id-had-from-day-one.html
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-28

## 投稿内容
Claude Code Tips I Wish I'd Had From Day One (marmelab, April 2026). Planning fixes the core problem by collapsing ambiguous decisions into a reviewed spec. Without "don't implement yet," Claude skips revision and starts writing code immediately. One developer spent two hours on a 12-step spec and recovered an estimated 6 to 10 hours of implementation time. Every file Claude reads, every command output, every message — it all eats into your context window. When it fills up, Claude starts "forgetting" earlier instructions.

## 要約
marmelab（フランス技術会社）によるClaude Code実践ティップス記事（2026年4月24日）。6つの主要教訓：①プランモード活用（"dont implement yet"を明示し、12ステップ仕様書作成2時間→実装時間6-10時間節約。スコープ明確な小タスクはプランモード不要）、②コンテキストウィンドウ管理（全ファイル読み込み・コマンド出力・会話がウィンドウを消費→サブエージェントでリサーチ分離・新タスクで新セッション開始）、③MCP接続でNotion/Figma/DB等の外部ツール連携拡張、④Hooks＝例外なく実行が必要なアクション向け・CLAUDE.md＝助言的指示（役割の明確な分担）、⑤必ずコード外で検証（テスト・スクリーンショット。検証できないものはリリースしない）、⑥コンテキスト圧迫の予防的管理（早めのコンパクション活用）。日本語でのClaude Code初期設定の参考として有用。
