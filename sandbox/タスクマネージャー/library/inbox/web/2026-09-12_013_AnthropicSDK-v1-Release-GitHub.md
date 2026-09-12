# Release v1.0.0 - anthropics/anthropic-sdk-python (GitHub)

- URL: https://github.com/anthropics/anthropic-sdk-python/releases/tag/v1.0.0
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-12

## 要約
Anthropic Python SDK v1.0.0公式リリースノート（2026-08-20）。破壊的変更: ①HTTPクライアントhttpx→httpx2（メンテナンス継続中のAPIcompatibleフォーク）②Python 3.10未満サポート廃止③legacy Text Completions API削除④Messagesメソッドのtemperature/top_p/top_kパラメータ削除⑤tool runnerのclient-side compaction_control削除。互換性対応: httpxをパッチするトレース/モックライブラリには`httpx2.alias_httpx()`を起動時に呼び出す。OpenTelemetry: contrib packageに新HTTPX2ClientInstrumentorが追加されたため更新が必要。v1移行ガイド（全変更点・before/afterスニペット）が別途公開。
