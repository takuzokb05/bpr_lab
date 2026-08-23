# Anthropic Python SDK v1.0.0 リリース：httpx2移行・Breaking Changes

- URL: https://github.com/anthropics/anthropic-sdk-python/releases
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-23

## 要約

Anthropic Python SDK v1.0.0が2026年8月20日（木）にリリース。主要変更：HTTPレイヤーをhttpxからhttpx2（API互換メンテナンスフォーク）に移行。Breaking Changes：Python 3.10+必須（3.9以下サポート終了）、非推奨だったText Completions APIを削除、Messagesメソッドのtemperature/top_p/top_kパラメータを削除、asyncクライアントの`.with_raw_response`結果に`await response.parse()`が必要に。新機能：Files API・Skills API GA、コンピュータ使用ツール・ブラウザ使用ツールセット追加、マネージドエージェントのウェブ検索設定とself-hostedサンドボックスメモリ対応。Claude Code v2.1.239に`/claude-api upgrade`コマンドが追加されており、0.x→1.x移行を半自動化できる。MIGRATION.mdで全変更のBefore/After解説あり。
