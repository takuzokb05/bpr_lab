# Anthropic Python SDK v1.0: What Breaks and How to Migrate (DigitalApplied)

- URL: https://www.digitalapplied.com/blog/anthropic-python-sdk-v1-breaking-change-migration
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-12

## 要約
Anthropic Python SDK v1.0.0（2026-08-20リリース）のブレイキングチェンジと移行ガイド。主要変更点: ①HTTPクライアントをhttpx→httpx2に移行（APIは互換性あり、トレース/モック系ライブラリにはhttpx2.alias_httpx()で対応）②Python 3.10未満のサポート廃止③legacy Text Completions API削除④Messagesメソッドのtemperature/top_p/top_kパラメータ削除⑤tool runnerのclient-side compaction_control削除。OpenTelemetryはHTTPX2ClientInstrumentorへの更新が必要。実際のコード例と移行ステップを詳述。
