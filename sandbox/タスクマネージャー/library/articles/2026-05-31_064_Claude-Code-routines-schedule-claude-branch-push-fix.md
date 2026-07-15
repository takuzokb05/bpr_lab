# Claude Code Routines: /schedule が claude/ ブランチにプッシュする問題と修正

- URL: https://israynotarray.com/en/ai/2026/05/25/claude-code-routines-schedule-and-branch-push-fix/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-31

## 投稿内容
IsRayNotArray による Claude Code Routines の実運用ハマりポイントと修正ガイド。

## 要約
2026年4月14日リサーチプレビュー開始のClaude Code Routinesで、/scheduleトリガーを設定するとPRがmainではなくclaude/プレフィックスブランチにプッシュされる既知の挙動を解説。CLAUDE.mdにbranch設定を明示的に記述する回避策と、Routine定義ファイルのbranch属性によるターゲットブランチ指定方法を実例付きで説明。Routinesは定期実行（hourly/daily/weekday/weekly）・HTTP POST API・GitHubイベントの3トリガーをサポート。対象はPro/Max/Team/Enterprise全プラン。claude.ai/code/routinesまたは/scheduleコマンドで設定可能。日常的なRoutines利用で必ず遭遇する問題のため参照価値高い。
