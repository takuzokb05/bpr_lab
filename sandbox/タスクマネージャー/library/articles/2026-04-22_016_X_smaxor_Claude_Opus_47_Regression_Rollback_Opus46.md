# Claude Opus 4.7でタスクが10分→90分に悪化 — 本番ビルドをOpus 4.6へ全戻しした理由

- URL: https://x.com/smaxor/status/2045971525409661307
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-22
- いいね: 1 / RT: 0 / リプライ: 0
- 投稿者: @smaxor / フォロワー 10,358

## 投稿内容
I just mass-reverted every Claude Code project back to Opus 4.6.

Here's why.

I've been running Opus 4.7 for the past few days across multiple production builds. Lead routing platform. Case Cleanse. Real software that ships to real clients.

And something was off.

Tasks that Opus 4.6 would knock out in 10 to 15 minutes were taking over an hour. Sometimes 90 minutes. Same prompts. Same project structure. Same everything.

It would eventually finish. But the output was worse.

More hallucinated file paths. More circular refactoring that went nowhere. More "let me restructure this for you" when nobody asked for a restructure.

I'm not a casual user. I've pushed billions of tokens through Claude Code building full production platforms. Hundreds of sessions. I know what good output looks like from this tool because I've been living inside it every single day.

So I rolled back to Opus 4.6 with the 1 million token context window.

First task after the revert? Done in 12 minutes. Clean code. No detours.

Here's how to do it yourself if you're running into the same issues.

The quick way is to just type /model inside any Claude Code session and select claude-opus-4-6 from the list.

But if you want it locked in across all your projects, add it to your settings.json:

{ "model": "claude-opus-4-6-1m" }
Important detail here. If you just set it to claude-opus-4-6 you're going to get the default 200k context window. That works fine for smaller tasks but if you're running complex multi-file builds you want the full million tokens. The 1M model string is claude-opus-4-6-1m. That "max" in the model name is what unlocks the extended context. Don't skip it.

## 要約
@smaxor（フォロワー10,358、複数の本番プラットフォームを構築する実務者）による2026-04-19の投稿。Claude Opus 4.7でOpus 4.6比でタスク完了時間が10〜15分→1時間以上（最大90分）に悪化し、全プロジェクトをOpus 4.6に戻した事例。具体的な症状：ファイルパスのハルシネーション増加・不要なリファクタリング提案・循環的な作業ループ。ロールバック後は12分で完了。settings.jsonへの`"model": "claude-opus-4-6-1m"`設定方法を具体的に説明。重要な詳細：`claude-opus-4-6`のみだとデフォルト200Kコンテキストになるため、1Mコンテキストは`claude-opus-4-6-1m`を指定する必要あり。モデル選択をインフラ選択と同等に扱う実践知見。
