# Claude Code Aug 29 Update: Linux 75MB化・restricted mode・token detail

- URL: https://explainx.ai/blog/claude-code-weekly-update-faster-startup-token-visibility-august-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-30

## 投稿内容

Claude Code's Aug 29, 2026 update includes CLI that starts before the sandbox loads, Linux download drops to ~75 MB, and /cost, /usage, and /tasks get new token detail. A new --restricted mode removes the built-in tools that run commands or code and WebFetch, keeps file tools inside the working directory, and refuses bypassPermissions. An Auto mode tab was added to the /permissions interface that surfaces the default rule set and lets you append your own allow/deny rules through the UI. Claude Code 2.1.245 fixes a critical startup crash affecting Linux users on the latest glibc versions.

## 要約

2026年8月29日リリースのClaude Code最新アップデート詳解。主要変更点5点：
1. **Linuxバイナリ75MB化**: zstd圧縮採用により~340MBから~75MB（約4.5倍削減）。CIダウンロード時間・デプロイ速度が大幅改善
2. **高速起動**: CLIがサンドボックスロード前に起動開始する設計変更で体感速度向上
3. **/cost・/usage・/tasksにトークン詳細表示**: セッション/タスク単位のトークン消費量の可視化を強化
4. **--restricted mode**: Bash実行・WebFetchツールを削除、ファイルツールをworking dir内に限定、bypassPermissionsを拒否するセキュリティ強化モード。信頼できないコードベース閲覧・レビュー用途に最適
5. **/permissionsにAuto modeタブ**: デフォルトルールセット表示とUI操作によるallow/denyルール追記が可能に
v2.1.245はLinux最新glibcでの起動クラッシュを修正。
