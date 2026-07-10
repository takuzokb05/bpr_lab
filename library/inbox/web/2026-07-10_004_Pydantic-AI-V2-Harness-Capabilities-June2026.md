# Pydantic AI V2リリース：Capabilities Primitive + Harness（2026年6月23日）

- URL: https://pydantic.dev/articles/pydantic-ai-v2
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-07-10

## 要約
Pydantic AI V2（2026年6月23日、7ベータ版を経て正式リリース）。アーキテクチャ刷新の核心：「capability」という統一プリミティブを導入。1つのcapabilityにエージェントのツール・指示・ライフサイクルフック・モデル設定をまとめて束ねる。コアは軽量（ループ・プロバイダー・capability/hooks API・基礎的capability）に保ち、memory・guardrails・サンドボックスコード実行・ファイルアクセス等の追加機能は別パッケージ「Harness」に分離。Capabilityはシリアライズ可能かつLLM書き込み可能で、エージェントが自身の改良を提案できる可能性。オプショナルプロバイダー依存でインストールサイズ削減。Logfire observability統合（instrumentationがcapabilityとして実装）。v1からの移行は非推奨警告を先にクリアすれば破壊的変更は最小限。Pydantic自身のリポジトリ全体でこのフレームワーク上のヘッドレスコーディングエージェントをドッグフーディング中。
