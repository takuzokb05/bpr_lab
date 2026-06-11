# TradingAgentsセットアップ完全チュートリアル：Docker+Python+LangGraphで動かすマルチエージェントLLM取引

- URL: https://byteiota.com/tradingagents-tutorial-multi-agent-llm-trading-setup/
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-11

## 要約
TradingAgentsのDocker・Pythonを使った実際のセットアップ手順を中心とした実践チュートリアル。

**アーキテクチャ**：7つの専門エージェントがLangGraphのグラフ上で協働。基本アナリスト（財務評価）・センチメントアナリスト（ニュース集約）・テクニカルアナリスト（価格パターン）・強気/弱気研究者（両視点の議論）・トレーダー（最終判断）・リスク管理（ポジションリスク審査）。

**セットアップ方法**：Docker（`docker compose run --rm tradingagents`）またはPython仮想環境。環境変数でAPIキー設定（OpenAI/Claude/Gemini等9プロバイダ対応）。

**v0.2.4の新機能（2026年4月）**：永続的な意思決定ログ（エージェントが過去取引から学習可能）、Azureエンタープライズ対応、Docker正式サポート。

**パフォーマンス**：AAPL・GOOGL・AMZNバックテストで年間24.9%リターン・シャープレシオ5.60。ただし実運用との乖離（取引コスト・スリッページ・市場レジーム変化）に注意。

**設計思想**：複数視点による議論がバイアス軽減と信頼性向上に寄与。各エージェントのreasoning logが可視化されるため意思決定プロセスが追跡可能。
