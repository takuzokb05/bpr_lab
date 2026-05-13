# Claude Code のプログラマティック利用がAPI従量課金へ移行する変更点

- URL: https://x.com/MIDORI_ruby7/status/2054665226872873169
- ソース: x
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-05-13
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @MIDORI_ruby7 / フォロワー 2219

## 投稿内容
・Claude Code、Coworkなどは影響なし
・Claude Agent SDK、claude -p（非インタラクティブモード）、Claude Code GitHub Actions、サードパーティ製Agent SDKアプリなど、programmatic usageもサブスクで使えていた
-> 従量課金(API料金側になる)に変更
ってことぽい

## 要約
Anthropicのサブスクリプションポリシー変更に関する重要な技術的整理。インタラクティブなClaude CodeやCoworkはサブスクのまま影響なし。一方、`claude -p`（非インタラクティブモード）、Claude Agent SDK、Claude Code GitHub Actions、サードパーティAgent SDKアプリなどのプログラマティック利用が、従来サブスクに含まれていたところからAPI従量課金へ移行する。開発者が自動化スクリプトやCI/CDパイプラインでClaude Codeを使っている場合はコスト構造が変わるため注意が必要。サブスク vs API料金の境界線を明確に整理した有益な情報。
