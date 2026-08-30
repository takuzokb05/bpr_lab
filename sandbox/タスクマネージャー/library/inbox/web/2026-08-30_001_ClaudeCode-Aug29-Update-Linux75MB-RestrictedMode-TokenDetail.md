# Claude Code Aug 29 Update: Linux 75MB化・restricted mode・token detail

- URL: https://explainx.ai/blog/claude-code-weekly-update-faster-startup-token-visibility-august-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-30

## 要約

2026年8月29日リリースのClaude Code最新アップデート詳解。Linuxバイナリが従来~340MBから~75MB（4.5倍削減）に縮小、zstd圧縮採用でCIダウンロード時間が大幅短縮。CLI起動がサンドボックスロード前に完了するよう改善され体感速度向上。/cost・/usage・/tasksコマンドにトークン詳細表示を追加。新--restricted modeはBash実行・WebFetchツールを削除し、ファイルツールをworking dir内に限定・bypassPermissionsを拒否するセキュリティ強化モード。/permissionsインターフェースにAuto modeタブ追加でallow/denyルールをUI操作可能に。v2.1.245はLinux最新glibc起動クラッシュを修正。
