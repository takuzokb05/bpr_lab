# Anthropic Python SDK v1.0: What Breaks and How to Migrate (DigitalApplied)

- URL: https://www.digitalapplied.com/blog/anthropic-python-sdk-v1-breaking-change-migration
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-12

## 投稿内容
Comprehensive migration guide for Anthropic Python SDK v1.0.0 (released August 20, 2026). Breaking changes: 1) HTTP client moves from httpx to httpx2 (API-compatible, maintained fork) — use httpx2.alias_httpx() at startup for tracing/mocking libraries that patch httpx. 2) Python 3.10 minimum required. 3) Legacy Text Completions API removed. 4) temperature, top_p, top_k parameters removed from Messages methods. 5) Tool runner's client-side compaction_control removed. OpenTelemetry: update from HTTPXClientInstrumentor to HTTPX2ClientInstrumentor. Full migration guide with before-and-after code snippets available at Anthropic docs.

## 要約
Anthropic Python SDK v1.0.0（2026-08-20リリース）のブレイキングチェンジと移行ガイド（DigitalApplied）。主要変更5点: ①HTTPクライアントhttpx→httpx2（APIは互換性あり、トレース/モック系ライブラリにはhttpx2.alias_httpx()を起動時呼び出しで対応）②Python 3.10未満のサポート廃止③legacy Text Completions API削除④Messagesメソッドのtemperature/top_p/top_kパラメータ削除⑤tool runnerのclient-side compaction_control削除。OpenTelemetry利用者はHTTPX2ClientInstrumentorへの更新が必須。サイレントに観測性スタックが壊れるリスクがあるためv1.0へのアップグレードは計画的なマイグレーションが必要。
