# MCPアーキテクチャ完全解説—Host/Client/Serverモデル・セキュリティ注意点・300+サーバー

- URL: https://x.com/matrixprompter/status/2054107488807424162
- ソース: x
- 言語: tr
- テーマ: claude-ecosystem
- 取得日: 2026-05-13
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @matrixprompter / フォロワー 1425

## 投稿内容
MCP (Model Context Protocol) nedir?

Claude'u dış dünyaya bağlayan açık standart. Anthropic geliştirdi, OpenAI ve Google da benimsedi.

Mantığı basit: AI uygulamaları için USB-C gibi. Tek bir protokol, sayısız bağlantı. Her araç için ayrı entegrasyon yazmazsın.

Ne yapar?
Claude'u GitHub, Slack, Notion, PostgreSQL, Google Drive gibi sistemlere bağlar. "Issue ENG-4521'i çöz ve PR aç" dediğinde gerçekten yapar — kopyala yapıştır biter.

Mimari: Host (Claude) → Client → Server. Sunucular yerelde çalışır, sen yetkilendirirsin.

Dikkat: Her MCP sunucusu makinende kod çalıştırır. Rastgele repo'ları kurma, resmi olanları tercih et. Ayrıca çok sunucu = çok tool metadata = bağlam kirliliği. Proje bazlı aç, global açma.

300+ topluluk sunucusu var. Ekosistem hızla büyüyor.
#MCP #ClaudeCode #AI

## 要約
トルコ語によるMCP（Model Context Protocol）の技術的解説。Anthropicが開発しOpenAI・Googleも採用した開放標準。USB-Cの比喩でAIアプリケーション統合を説明。接続可能システム：GitHub、Slack、Notion、PostgreSQL、Google Drive。アーキテクチャはHost（Claude）→ Client → Server の3層構造で、サーバーはローカル実行・ユーザー認可式。重要なセキュリティ警告が2点：(1) 各MCPサーバーはマシン上でコードを実行するため不審なリポジトリのインストールは危険、(2) サーバー過多はtoolメタデータ増加によるコンテキスト汚染を引き起こすためプロジェクト別に限定的に使用すること。コミュニティサーバー数は300以上でエコシステムは急成長中。
