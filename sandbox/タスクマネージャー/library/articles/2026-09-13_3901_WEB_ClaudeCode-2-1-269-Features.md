# Claude Code 2.1.269: plugin eval, /output-style, Bash diff

- URL: https://aicatchup.com/news/claude-code-weekly-limits-permanent-25-percent-september-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-13

## 要約
Claude Code 2.1.269（2026-09-11）の新機能3点: (1) `claude plugin eval`コマンド——プラグインのevalスイートをClaude Code本体に対してスコアリング実行しJSON+HTMLレポートを出力。CI連携でプラグイン品質を定量評価できる (2) `/output-style [name]`スラッシュコマンド——セッション中にMarkdown/JSON/Plain等の出力スタイルをその場で切り替え可能 (3) Bashツール結果にファイル変更のdiffを追加——Bashがファイル編集を行った場合、その差分がツール結果に含まれ変更の透明性が向上。注意: git読み取り専用コマンドが長時間セッション後に不必要に権限確認を求めるリグレッションあり（2.1.270で修正予定）。
