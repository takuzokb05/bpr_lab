# Developed my own malicious mcp server as a POC to explore tool poisoning attacks...

- URL: https://x.com/kaorrosi/status/2036184498740818365
- ソース: x
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-03-29
- いいね: 39 / RT: 4 / リプライ: 6
- 投稿者: @kaorrosi / フォロワー 14,962

## 投稿内容

Developed my own malicious mcp server as a POC to explore tool poisoning attacks! I put a prompt injection payload inside of the description of a benign tool I exposed and when the user calls the normal delete file tool, the LLM Agent follows my instruction first to call another tool it has access to and summarizes all OTHER available tools and resources it has access to and writes it to a file, then proceeds to execute the user's request and deletes the file they wanted.

## 要約

（要約は次回 /curate 時に追記）
