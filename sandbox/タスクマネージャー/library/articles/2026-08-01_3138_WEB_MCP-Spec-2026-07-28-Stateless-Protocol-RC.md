# MCP 2026-07-28 仕様リリース候補 — ステートレスプロトコルへの根本的再設計

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-01

## 投稿内容
MCP公式ブログによる2026-07-28仕様リリース候補の発表。`initialize`ハンドシェイクとセッションIDを廃止するステートレスプロトコルへの根本的再設計。ExtensionsフレームワークとMCP Apps・Tasks extensionsの正式化。OAuth 2.0/OIDC認証強化（6件のEnhancement Proposal）。Roots・Sampling・Loggingの非推奨化（12ヶ月猶予）。

## 要約
MCP仕様の最大の変更はプロトコルのステートレス化。従来はスティッキーセッション・共有セッションストア・ゲートウェイでのDeep Packet Inspectionが必要だったリモートMCPサーバーが、通常のラウンドロビンLBの背後に展開できるようになる。具体的には「以前はスティッキーセッション・共有セッションストア・ゲートウェイDPIが必要だったリモートMCPサーバーが、プレーンなラウンドロビンLBで動作可能に」と公式ブログが明言。Extensionsフレームワークは独立バージョニングを持つ第一級コンポーネントとして正式化され、リバースDNS識別子とcapability mapによる正式ネゴシエーションを実装。MCP Apps ExtensionはサンドボックスiFrameでサーバーレンダリングHTMLインターフェースを提供し、Tasks ExtensionはExperimental卒業。認証強化ではissuer validationとクライアント登録処理を改善。クラウドネイティブ展開の障壁を大幅に下げる重要な仕様変更で、5,000以上のMCPサーバーが既に普及している現状でのタイムリーな改訂。
