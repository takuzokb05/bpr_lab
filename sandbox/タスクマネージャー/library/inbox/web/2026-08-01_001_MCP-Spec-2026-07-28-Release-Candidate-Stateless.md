# MCP 2026-07-28 Specification Release Candidate — Stateless Protocol Architecture

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-01

## 要約
MCP仕様の2026-07-28リリース候補が公開。最大の変更は**プロトコルのステートレス化**：`initialize` ハンドシェイクとセッションIDを廃止し、どのサーバーインスタンスにでもリクエストをルーティング可能に。これにより通常のラウンドロビンLBの背後にMCPサーバーを展開でき、スティッキーセッションや共有セッションストアが不要になる。他の主要変更：（1）独立バージョニングを持つExtensionsフレームワーク（MCP Apps・Tasks extensions正式化）、（2）OAuth 2.0/OIDCに対応する認証強化（6件のEnhancement Proposal）、（3）Roots・Sampling・Loggingの12ヶ月猶予付き非推奨化。最終仕様は2026-07-28に公開予定。クラウドネイティブデプロイメントへの移行を大幅に容易にする重要な仕様変更。
