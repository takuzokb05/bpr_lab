# Release v1.0.0 — anthropics/anthropic-sdk-python (GitHub)

- URL: https://github.com/anthropics/anthropic-sdk-python/releases/tag/v1.0.0
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-12

## 投稿内容
Official release notes for Anthropic Python SDK v1.0.0 (August 20, 2026). Core change: HTTP layer moves from httpx to httpx2, a maintained API-compatible fork. Call httpx2.alias_httpx() at startup if tracing or mocking libraries patch httpx. Drops Python < 3.10. Removes: legacy Text Completions API, temperature/top_p/top_k on Messages methods, tool runner's client-side compaction_control. Personal keys and service account keys added in Claude Console for workspace-scoped access. Computer use and browser use toolsets brought to Google Cloud for several Claude models. SDK behavior for files and skills updated, BetaSkill renamed to BetaContainerSkill.

## 要約
Anthropic Python SDK v1.0.0公式リリースノート（2026-08-20）。コア変更: HTTPクライアントhttpx→httpx2。廃止: Python 3.10未満、Text Completions API、Messages APIのtemperature/top_p/top_k、tool runnerのclient-side compaction_control。新機能: Claude Consoleでパーソナルキー・サービスアカウントキーのワークスペーススコープ管理、コンピューターユース/ブラウザユースのGoogle Cloud対応。BetaSkill→BetaContainerSkillに改名。ファイルとスキルのSDK動作更新。httpxをパッチするライブラリにはhttpx2.alias_httpx()での互換対応が必要。
