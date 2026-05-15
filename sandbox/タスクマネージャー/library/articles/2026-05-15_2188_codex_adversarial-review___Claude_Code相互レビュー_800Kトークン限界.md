# codex adversarial-review + Claude Code相互レビュー 800Kトークン限界

- URL: https://x.com/msrktt/status/2055392951962948068
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-15
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @msrktt / フォロワー 522

## 投稿内容
I ran /codex:adversarial-review, and Claude Code would keep making some mistakes. I realized it was due to the 800K token context.. I cleared but now I have codex fix it and CC review it again before running.

## 要約
@msrktt による実践ワークフロー報告（522F）。
/codex:adversarial-reviewスキルとClaude Codeを組み合わせた相互レビューアーキテクチャ。
手順: まずClaude Codeに実装させ、Codexがadversarial reviewを行い再修正する循環。
800Kトークンコンテキスト上限でエラーが発生、クリア後にCodexで修正→CCが再レビューの流れで解決。
大規模コードベースでのコンテキスト管理の実践的な課題と解決パターン。
