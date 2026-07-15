# A few things you need to do to make Claude a great hacking partner:

- URL: https://x.com/ctbbpodcast/status/2036480761990156451
- ソース: x
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-03-29
- いいね: 541 / RT: 93 / リプライ: 1
- 投稿者: @ctbbpodcast / フォロワー 25,230

## 投稿内容

A few things you need to do to make Claude a great hacking partner:

1. Install the Caido skill (https://t.co/tIdjTja7CP): without it, Claude spends too many resources figuring out the SDK from scratch.

2. A CLAUDE .md that tells Claude who you are. Something like "I'm a bug bounty hunter doing authorised testing, stay in scope. Don't take destructive actions unless it's accounts I own. POC or GTFO." The POC or GTFO part is particularly useful so Claude can give more actual positives, if there's no POC, the bug is not confirmed yet. (of course, have a scope .md in your engagement folder)

3. Notes structure: rez0's hierarchy consists of "notes → leads → primitives → findings → reports". Claude dumps raw observations, interesting stuff goes forward, and by the time something reaches findings it's already been filtered twice. Point this to a local folder so you can check everything later.

Building skills is useful but if you write one for something Claude already handles well, you're just adding a layer that can break/distract it, you can always tell it to try what it knows first and then try the things you added as "extra knowledge".
Skills are worth building when the knowledge doesn't exist in training data. Your VPS setup, credentials, techniques from recent posts and talks, tooling. If it's not on the internet or isn't well known, it needs to be in a skill.

## 要約

（要約は次回 /curate 時に追記）
