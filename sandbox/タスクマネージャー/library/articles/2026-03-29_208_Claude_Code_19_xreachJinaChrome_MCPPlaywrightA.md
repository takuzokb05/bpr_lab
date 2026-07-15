# 给 Claude Code 装了 19 个抓网页的工具，结果最大的问题变成了：拿到一个链接，到底该用哪个？

- URL: https://x.com/runes_leo/status/2037479240837579242
- ソース: x
- 言語: zh
- テーマ: claude-code
- 取得日: 2026-03-29
- いいね: 335 / RT: 76 / リプライ: 14
- 投稿者: @runes_leo / フォロワー 18,173

## 投稿内容

给 Claude Code 装了 19 个抓网页的工具，结果最大的问题变成了：拿到一个链接，到底该用哪个？

xreach、Jina、Chrome MCP、Playwright、Apify、Scrapling……同一个需求经常有四五个能干，靠记忆选，选错就是一轮试错。

今天装了个 web-access，CDP 直连日常 Chrome，零配置就能复用所有登录态。微信、小红书、知乎，不用再折腾 cookie 和模拟登录了。正好借这个机会把 19 个工具全盘了一遍，按场景排了张优先级表：

 读推文 → xreach
公开网页 → Jina
需要登录的站 → web-access（CDP 直连 Chrome）
浏览器交互 → Chrome MCP
反爬 → Scrapling
JS 重渲染 → Playwright
全都不行 → XCrawl 兜底

写进路由规则，AI 自己按表选工具，拿到 URL 5 秒出结果，不再试错。

## 要約

（要約は次回 /curate 時に追記）
