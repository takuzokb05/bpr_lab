# Claude Code Hooks vs Settings の違い：イベントベースvsデフォルト設定

- URL: https://x.com/dan_mwita8/status/2057567112131170385
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-21
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @dan_mwita8 / フォロワー 128

## 投稿内容

Claude Code hooks and settings overlap confusingly. The rule is that hooks fire on events (PreToolUse, Stop) while settings allow/deny tools. If you want a behavior to happen every time, it's a hook ,if you want to gate a tool, it's settings.

## 要約

Claude CodeのHooksはイベント（PreToolUse, Stop等）で発火するシェルコマンド。Settingsはデフォルトのデフォルト設定値。混同しがちだが役割が異なる：Hooksは決定論的な処理、Settingsは起動時の挙動を制御。ドキュメントで不明確な点を整理した技術解説。
