# Claude Code Cross-Session Messaging: ListAgents & SendMessage Official Docs

- URL: https://code.claude.com/docs/en/cross-session-messaging
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-29

## 要約
v2.1.224（2026-08-07）から追加されたClaude Codeのクロスセッションメッセージング機能の公式ドキュメント。
- 異なるターミナル/worktreeで動く複数Claudeインスタンスが互いにメッセージを送受信できる
- `ListAgents`で到達可能なセッションを発見、`SendMessage`でテキスト送信
- メッセージはテキストのみ（会話履歴やファイルは含まない）
- macOS/Linux対応（WSL2含む）、v2.1.234以降でWindows(Native)対応
- セキュリティ：OSユーザー単位でinboxソケットを制限、他ユーザーのセッションからアクセス不可
- Auto modeでは`SendMessage`がディスパッチ前にパーミッションクラシファイアで評価される
- 管理者はorg単位でインバウンドメッセージ拒否・`SendMessage`/`ListAgents`を無効化可能
- `/list-agents`（`/peers`でも可）コマンドで現在のセッション一覧を確認
- 用途例：一方のセッションでの変更が別セッションに影響する場合の自動通知、並列開発でのブロック解除
- 一方のセッションは別セッションのパーミッション設定を変更・承認することは不可
