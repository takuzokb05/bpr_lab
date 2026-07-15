# Claude Code Auto Mode isn't just "enable it and walk away"

- URL: https://x.com/dani_avila7/status/2037727415074423175
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-29
- いいね: 92 / RT: 8 / リプライ: 13
- 投稿者: @dani_avila7 / フォロワー 27,092

## 投稿内容

Claude Code Auto Mode isn't just "enable it and walk away"

Bookmark this for later! 

Auto mode puts a classifier between Claude and your system. Before each tool call runs, it reviews the action and decides: safe to proceed, or block it and confirm

The problem is it ships with no knowledge of your stack, so it can't tell your repos, domains, and cloud services apart from untrusted external targets. It blocks them

That's what autoMode.environment fixes. You're telling the classifier what infrastructure is yours, try this:

- Run "claude auto-mode defaults" to see the built-in rules
- Feed that output to Claude and let it read what's already there and create the environment
- Edit settings.json with the environment Claude proposes
- Run "claude auto-mode config" to verify the effective config
- Run "claude auto-mode critique" to catch rules that are ambiguous, redundant, or likely to cause false positives

This is the environment config I got working for https://t.co/pEjytZiAFd
Auto mode has been running clean ever since 👇

## 要約

（要約は次回 /curate 時に追記）
