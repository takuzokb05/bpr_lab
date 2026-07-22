# How Anthropic secures its AI-native software development lifecycle — Anthropic Blog

- URL: https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-22

## 要約
Anthropic Deputy CISO Jason Clintonが、Claudeがマージコードの約80%を生成する環境でのSDLCセキュリティ実践を公開（7月21日）。5段階：①計画：Claude Opus駆動のPSR（Project Security Review）がMITRE ATT&CKフレームワークに基づいて設計書を自動分析。②コード生成：CLAUDE.mdとスキルにセキュリティガイダンスを埋め込み、/security-reviewコマンドとセキュリティプラグインを実装。開発者はegressホワイトリスト制限付きリモートVMで作業。③テスト/CI：複数の専門エージェントがRAGで文脈を取得し、PoV（proof of vulnerability）を書いてからコメント投稿。リスクTier別自動化レベル。④デプロイ：ステージング環境での継続的AIパワードDAST。⑤モニタリング：単一目的アラートトリアージエージェント、エージェント間チェックを相互制御。全承認はSIEMへ記録。
