# Claude Agent SDK・claude -p等のprogrammatic usageが6/15からAPI従量課金に移行

- URL: https://x.com/MIDORI_ruby7/status/2054665226872873169
- ソース: x
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-05-13
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @MIDORI_ruby7 / フォロワー 2219

## 投稿内容
・Claude Code、Coworkなどは影響なし
・Claude Agent SDK、claude -p（非インタラクティブモード）、Claude Code GitHub Actions、サードパーティ製Agent SDKアプリなど、programmatic usageもサブスクで使えていた
-> 従量課金(API料金側になる)に変更
ってことぽい

## 要約
Anthropicの課金体系変更の技術的内訳を整理した投稿。影響なし対象：Claude Code（インタラクティブ利用）、Cowork。課金変更対象（サブスク→API従量課金）：Claude Agent SDK、claude -p（非インタラクティブモード）、Claude Code GitHub Actions、サードパーティ製Agent SDKアプリ。要するにprogrammatic usage（自動化・エージェント用途）がサブスクリプション対象外となりAPI料金に移行するという整理。Claude CodeのCLI利用とAPIプログラム利用の境界が明確化された。6/15実施予定のこの変更は、エージェント開発者・CI/CD自動化ユーザーに直接影響する重要な課金構造の変化。
