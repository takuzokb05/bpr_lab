# ChatGPT（生成AI）の売買判断を定期的に連携して自動的にFX取引を行うEAの開発

- URL: https://note.com/sayama_ocha/n/nb22d3c2cbaa2
- ソース: web
- 言語: ja
- テーマ: ai-trading
- 取得日: 2026-04-18

## 要約
Note掲載のsayama_ocha氏による実装記事。ChatGPT APIをMT5のEAと連携してFX自動売買を実現する具体的な実装手順。アーキテクチャ：MT5 EA（MQL5）がChatGPT APIを定期呼び出し→JSON形式で売買判断を受取→自動注文執行。技術的ポイント：APIキー管理・JSON Parse・エラーハンドリング・レート制限対策。使用モデル：ChatGPT-5（GPT-4o等）。結果と考察：AIの判断精度はプロンプト設計に依存、バックテスト不可のため実運用リスクあり。日本語圏でのLLM×MT5統合の実践事例として希少。コードの一部を公開しており再現性が高い。
