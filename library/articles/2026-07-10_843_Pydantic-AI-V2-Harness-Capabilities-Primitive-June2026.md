# Pydantic AI V2：Capabilities Primitive + Harness設計（2026年6月23日正式リリース）

- URL: https://pydantic.dev/articles/pydantic-ai-v2
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-07-10

## 投稿内容

Pydantic AI V2が2026年6月23日に7ベータ版を経て正式リリース。AIエージェントフレームワークのアーキテクチャを根本から再設計した。

**Capability：統一プリミティブ**
V2の核心はcapabilityという単一の合成可能なユニット。エージェントのツール・指示・ライフサイクルフック・モデル設定をすべて1つのプリミティブにまとめる。拡張思考・コード実行サンドボックス・ウェブ検索・動的ツール探索等の機能がそれぞれcapabilityとして実装される。Capabilityはシリアライズ可能かつLLM書き込み可能で、エージェントが自身の改良を提案できる可能性を持つ。

**Harnessとの分離設計**
コアは軽量に保つ方針：アジェンティックループ・プロバイダー・capability/hooks API・基礎的capabilityのみをコアに収録。メモリ・ガードレール・ファイルアクセス・コードモード等の追加機能は別パッケージ「Pydantic AI Harness」に分離し、コアの安定性を保ちながら高速に機能追加可能にした。コミュニティ提供capabilityもHarnessで承認・リンク提供。

**技術的改善点**
- capabilityは遅延ツールローディングをサポート
- サーバーサイドメッセージコンパクション
- メッセージキューによるミッドラン制御
- オプショナルプロバイダー依存によるインストールサイズ削減
- Logfire observabilityをcapabilityとして統合

**ドッグフーディング**
Pydantic自身がPydantic AI V2をベースにしたヘッドレスコーディングエージェントを自社全リポジトリに適用中。6月はHarnessの大量新capability追加と並行して実施。

**移行について**
v1からの移行は非推奨警告を先にクリアすれば破壊的変更は最小限。アップグレードガイドは公式ドキュメントに記載。

## 要約
Pydantic AI V2（2026年6月23日、正式GA）はAIエージェントフレームワークの根本再設計。ツール・フック・指示・モデル設定をまとめる「capability」という統一プリミティブと、コアと拡張機能を分離する「Harness」設計が2大柱。Claude Agent SDK・LangGraph・Microsoft Agent Framework 1.0と並ぶ主要エージェントSDKとして位置づけられる。Capabilityのシリアライズ可能性とLLM書き込み可能性は将来の自己改善エージェントを見据えた設計。コア軽量化・Harness分離で拡張の自由度と安定性を両立。Pydantic自身がドッグフーディングしている信頼性あり。Claude Codeとの比較において「capabilityとskillの概念的類似」が興味深い。
