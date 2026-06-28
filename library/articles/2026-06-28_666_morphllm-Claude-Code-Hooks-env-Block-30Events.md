# Claude Code Hooks (2026): .envブロック・30イベント・終了コードセマンティクス

- URL: https://www.morphllm.com/claude-code-hooks
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-28

## 投稿内容
Claude Code hooksの詳細技術リファレンス記事。30のhookイベント、5種のハンドラータイプ（command/http/mcp_tool/prompt/agent）、および全フックが受け取るJSON入力構造（session_id, transcript_path, cwd, hook_event_name、イベント固有フィールドtool_input.file_pathやtool_input.commandを含む）を網羅。

終了コードセマンティクスの重要な解説: 0はstdout JSONを成功としてパース、2は対応イベントでアクションをブロックしstderrをClaudeにフィードバック、その他のコードはすべてノンブロッキングとなる。この「2のみブロック」という仕様は重要な実装上の注意点であり、Unixの慣例（1=エラー）に慣れた開発者が誤ってexit 1を使ってブロックしようとしても、実際にはブロックされないというよくある失敗パターンを指摘している。

特集: PreToolUseフックを使って.envファイルへのアクセスをブロックする実装例。パーミッションルールや.gitignoreでは防げない、インデックス経由やsystem-reminderインジェクション経由のアクセスも防止できる決定論的な方法として説明。本番パターン: 正規表現によるPreToolUseでの危険コマンドブロック、PostToolUseでの自動フォーマット、ツール呼び出し間のコスト・使用量ロギング。

## 要約
Claude Code hooksの包括的技術リファレンス。30イベント・5ハンドラータイプ・JSONインプット構造を解説。最重要ポイント：終了コード2のみがアクションをブロック（exit 1は非ブロッキング）。PreToolUseフックで.envファイルをブロックする決定論的なセキュリティ実装例を特集。パーミッションルールや.gitignoreでは防げないインデックス経由のアクセスも確実に防止できる。本番事例としてdangerous command regex blocking・自動フォーマット・コストロギングパターンを掲載。
