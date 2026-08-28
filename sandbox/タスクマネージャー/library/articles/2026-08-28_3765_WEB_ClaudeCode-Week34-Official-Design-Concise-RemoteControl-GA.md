# Claude Code Week 34 (Aug 17–21): /design・Concise出力スタイル・Remote Control GA

- URL: https://code.claude.com/docs/en/whats-new/2026-w34
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-28

## 投稿内容
Official Claude Code Week 34 changelog covering v2.1.234 → v2.1.239 (August 17–21, 2026). Three headline features:

1. **/design (research preview)**: Run `/design <brief>` to get a published canvas of editable UI artboards. Built on Artifacts infrastructure. Available on Pro, Max, Team, Enterprise. Requires v2.1.233+. Pick an artboard, tweak it, then have Claude implement it—all without leaving the session.

2. **Concise output style (v2.1.237)**: New built-in output style. Claude leads with the result and skips preamble and narration, while doing the work as thoroughly as in Default. Enable via `/config` → Output style or `"outputStyle": "Concise"` in settings.json.

3. **Remote Control GA (mobile)**: `claude remote-control` now shows the machine as a device card in the Claude mobile app's Code tab. Tap to pick a directory and start a session from your phone. Remote Control is out of research preview.

Additional wins: auto-continue after usage limit reset, spellcheck (aspell/hunspell/ispell), GitLab MR badge in footer, effort level change from phone applies immediately, `/permissions` and `/add-dir` work during active turns, `/goal` 30-minute check-in, own prompts render Markdown, `ANTHROPIC_DEFAULT_MODEL` env var, `notify_when_idle` cross-session messaging, Windows native SendMessage/ListAgents, self-hosted runner `--defer-shutdown-max-min` and `--proxy-authorization-command`.

## 要約
Claude Code公式Week 34ログ（v2.1.234-239）。3本の主要機能が揃い踏み。①/design（research preview）：`/design <brief>`でUIのartboardを複数案生成→公開リンクを返す→選択→実装まで1セッション内で完結。Artifacts基盤で動作、Pro以上対応、v2.1.233必須。②Concise出力スタイル（v2.1.237）：結果先頭表示でpreamble排除。/config または settings.json `"outputStyle":"Concise"` で有効化。エラー・セキュリティ警告は常に全文表示。③Remote Control正式GA：スマホのCodeタブにマシンが「デバイスカード」として表示、タップでディレクトリ選択→セッション開始。他：使用量制限リセット後の自動継続、スペルチェック、GitLab MRバッジ、ANTHROPIC_DEFAULT_MODEL環境変数、Windows native SendMessage/ListAgents等。3本すべてが実務ワークフロー短縮に直結する高インパクト変更。
