# Claude Codeステータスライン再実装: 5h/7d使用制限カウントダウン+Stopフック音

- URL: https://x.com/did0f/status/2051386342928531725
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-04
- いいね: 0 / RT: 1 / リプライ: 0
- 投稿者: @did0f / フォロワー 1560

## 投稿内容
The default Claude Code statusline shows the model and the cwd. That's it.

I rebuilt it: context bar, git branch, 5h + 7d rate-limit countdowns, session length. Plus a Stop hook for an "answer ready" chime.

Full bash script + the bell trick I got wrong on the first try 👇😄

## 要約
@did0f（フォロワー1560）がデフォルトの「モデル名+CWD」表示に不満を感じ、statuslineを完全再実装。追加した機能: コンテキストバー、gitブランチ表示、5時間および7日間のレートリミットカウントダウン、セッション時間表示、さらにStopフックを使った「回答準備完了」通知チャイム。フルのbashスクリプトとベルトリック手法を公開。Claude Codeの運用可視化ツールとして実用的なカスタマイズ例。
