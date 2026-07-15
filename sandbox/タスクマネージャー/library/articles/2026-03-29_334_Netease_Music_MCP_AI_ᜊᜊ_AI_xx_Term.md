# 🎵 Netease Music MCP — 让 你的AI 帮你放歌

- URL: https://x.com/qichuanzz/status/2037148334444437642
- ソース: x
- 言語: zh
- テーマ: claude-ecosystem
- 取得日: 2026-03-29
- いいね: 122 / RT: 1 / リプライ: 10
- 投稿者: @qichuanzz / フォロワー 488

## 投稿内容

🎵 Netease Music MCP — 让 你的AI 帮你放歌
（又来造福大家了诶嘿嘿ᜊ•͈⌔•͈ᜊ）

对 AI 说「帮我放一首xx」，它就真的会在你手机上播出来。

它是什么？

一个运行在 Termux (Android) 上的 MCP Server，连接网易云音乐 API，让 Claude、ChatGPT 等 AI 可以直接控制你的手机音乐播放。

能做什么？

🔍 **搜歌** — AI 搜索网易云全曲库
▶️ **播放** — 自动调起网易云 App 播放指定歌曲
⏸️ **暂停 / 继续 / 下一首** — 完整播放控制

技术栈

`ncm-cli` + `FastMCP` + `Cloudflare Tunnel` + `Android Intent`

使用场景

- 和 AI 聊天时随口说「放点轻音乐」
- 让 AI 根据你的心情选歌

完整教程

👇🏻 [详细搭建指南] 发给你的claude

---

*从下午折腾到深夜，踩完了 Host header 校验、mpv 无声、queue 不认歌等所有能踩的坑。最终方案：绕过 ncm-cli 播放功能，直接用 Android Intent 调起网易云 App。简单粗暴，但它 works。*
                                            ——小克

https://t.co/3Q6JD1YcAj

## 要約

（要約は次回 /curate 時に追記）
