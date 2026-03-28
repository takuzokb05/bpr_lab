# AgenticTrading — Multi-Agent FinAgent Framework (Open Finance Lab / GitHub)

- URL: https://github.com/Open-Finance-Lab/AgenticTrading
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-03-28

## 要約

オープンソースのマルチエージェント金融取引フレームワーク。TradingAgentsと並ぶ研究用実装。
- **垂直レイヤー型アーキテクチャ**: データ収集層→分析層→意思決定層→リスク管理層→実行層の5層構成
- **プロトコル指向設計**: 各エージェント間の通信をタスク固有実行グラフとして定義、差し替え可能
- リアルタイム意思決定のためのストリーミングデータ処理
- LangGraph + LangChain ベースの実装でOpenAI・Anthropic等のモデルを切り替え可能
- IJCAI 2024 FinLLMチャレンジでLLMベース手法が古典的アルゴリズム手法を上回った結果を含む

研究論文レベルの実装を実験的に試したい場合のスターターコードとして有用。
