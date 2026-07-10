# Google Cloud：50以上のフルマネージドMCPサーバーがGA（2026年5月）

- URL: https://cloud.google.com/blog/ja/products/ai-machine-learning/google-managed-mcp-servers-are-available-for-everyone
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-07-10

## 投稿内容

Google Cloudが2026年5月21日のGoogle Cloud Next '26で、50以上のフルマネージドModel Context Protocol（MCP）サーバーを全ユーザー向けにGA（一般提供）およびプレビューで公開した。

**対応サービスカテゴリ**
- インフラ・運用：GKE・Cloud Run・GCE（ライフサイクル管理）、Cloud Logging & Monitoring（自己修復システム）、Google Security Operations（脅威調査）、Android Management API、Network Management API
- データ・分析：Spanner・AlloyDB・Cloud SQL・Firestore・Bigtable（運用データ）、BigQuery・Apache Spark（大規模データ処理）、Pub/Sub・Apache Kafka（リアルタイムアラート）、Cloud Storage・Knowledge Catalog
- サービス・アプリ：Developer Knowledge API、Google Maps Grounding Lite、Workspace API群（Gmail・Drive・Calendar・Chat・People API）、Google Pay & Wallet API、Customer Experience Agent Studio

**エンタープライズセキュリティ**
- Cloud IAM denyポリシーによる細粒度アクセス制御
- Model ArmorによるプロンプトインジェクションとデータExfiltration防止のインライン統合
- OTelトレーシングとCloud Audit Logsによる完全な可観測性

**高い相互運用性**
- Gemini CLI・Claude・ChatGPT・VS Code・LangChain・Agent Development Kit（ADK）・CrewAIすべてで動作確認済み
- MCPプロトコルプリミティブとしてresourcesとpromptsをサポート

**Agent Registry**
エージェント・MCPサーバー・ツールを統合的に検索・管理できるディレクトリサービス。

**実例：Insta360**
GCPエージェントエコシステムを使用して、ユーザーが自然言語入力でクラウド上の動画編集を完了できるAI動画編集エージェントを構築。

## 要約
Google Cloudが2026年5月21日のGoogle Cloud Next '26でフルマネージドMCPサーバー50以上をGA公開。GKE・BigQuery・Gmail・Cloud SQL等の主要GCPサービスをMCPプロトコルで直接AI接続可能にした。Cloud IAM・Model Armor・OTelトレーシングによるエンタープライズグレードのセキュリティと可観測性を標準装備。Claude・ChatGPT・Gemini CLI・LangChain等主要AI/フレームワーク全て対応。Agent Registryが統合ディレクトリとして機能し、OpenAI・Google・Microsoft・AnthropicがMCPを採用した業界標準化の流れを加速する重要リリース。Claude CodeユーザーはMCPサーバーとしてGCPサービスをコスト効率的に接続可能になった。
