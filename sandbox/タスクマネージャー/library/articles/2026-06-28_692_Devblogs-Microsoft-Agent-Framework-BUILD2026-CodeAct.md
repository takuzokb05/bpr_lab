# Microsoft Agent Framework BUILD 2026: CodeAct・Hosted Agents・52.4%レイテンシ改善

- URL: https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce/
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-06-28

## 投稿内容
BUILD 2026（2026年6月3日発表）でMicrosoft Agent Framework（2026年4月3日GA）の主要追加機能を発表した記事（Microsoft DevBlogs）。

**主要新機能:**

**① Agent Harness（本番対応パターン）:**
- 自動コンテキストコンパクション（コンテキスト圧縮）
- 組み込みシステム命令（ユーザーカスタマイズ可能なベースプロンプト）
- ファイルメモリ（セッション間の永続的なファイルシステム状態）
- タスク追跡（進捗管理の組み込み）
- OpenTelemetry統合（分散トレーシング・メトリクス・ログ）

**② Foundry Hosted Agents（ゼロスケーリングデプロイ）:**
- ゼロスケーリング対応のクラウドデプロイメント
- 永続ファイルシステム状態（セッション間でのデータ保持）
- セッション別VM分離（セキュリティ・安定性）
- 使用時のみ課金（アイドル時はゼロコスト）

**③ CodeAct（最重要新機能）:**
複数のツール呼び出しを単一のPythonプログラムに統合し、Hyperlight マイクロVM内で実行する新アーキテクチャ。

**定量的成果（代表的なワークロードでの測定値）:**
- レイテンシ改善: **52.4%削減**
- トークン削減: **63.9%削減**

これは複数の独立したツール呼び出しをバッチ化することで、LLMとツール実行間のラウンドトリップ数を大幅に削減できることによる。

**④ 追加発表:**
- GitHub Copilot SDK統合
- Handoff Orchestration Pattern（マルチエージェントトポロジー向け引き継ぎパターン）

## 要約
Microsoft Agent Framework BUILD 2026（2026年6月3日）新機能発表。①Agent Harness: 自動コンパクション・組み込みシステム命令・ファイルメモリ・タスク追跡・OpenTelemetry統合。②Foundry Hosted Agents: ゼロスケーリングクラウドデプロイ（永続FS・セッション別VM分離）。③CodeAct: 複数ツール呼び出しを単一Pythonプログラム化+Hyperlight マイクロVM実行で代表ワークロードにてレイテンシ52.4%削減・トークン63.9%削減を実現。④GitHub Copilot SDK統合・Handoff Orchestrationパターン追加。
