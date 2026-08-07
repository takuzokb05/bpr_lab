# NVIDIA's NOOA Makes an Agent One Python Class — The New Stack

- URL: https://thenewstack.io/nvidia-nooa-agent-framework/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-07

## 要約

NVIDIAが2026-07-27にリリースしたオープンソースエージェントフレームワーク「NOOA（NVIDIA Object-Oriented Agents）」の技術解説。

**NOOAのコアコンセプト**:
- エージェントを単一のPythonクラスとして表現する
- 「エージェント = クラス」という抽象化により、テスト・トレース・監査・ガバナンスが容易になる
- model-agnostic: OpenAI, Anthropic, Google, Mistral, Ollamaなど主要LLM全対応

**技術的特徴**:
- Python-based, 単一クラス継承で新エージェントを定義
- ハーネスがモデルとの統合を改善し、エージェント動作をtest/trace/audit/governしやすくする
- 研究プレビューとして提供中（GitHub上でコードとベンチマーク公開）
- `agent.run(task)` → 戻り値 → 次エージェントへ渡す、のシンプルなAPI

**Open Secure AI Alliance**:
- NVIDIAを含む37組織が「Open Secure AI Alliance」を設立（2026-07）
- AIエージェントのセキュリティ技術・ツールをOSSで開発・共有する目的
- メンバー: Anthropic, Google, Microsoft, AWS等業界主要企業

**NemoClaw（GTC Taipei 2026発表）**:
- NOOAと別軸でNVIDIAが発表したエージェントオーケストレーションフレームワーク
- NemoClaw + NOOA = NVIDIAのフルスタックエージェント基盤

**なぜ重要か**: NOOA採用で単一LLMへの依存を回避しながら、テスト容易なエージェント設計が可能。エージェント移行コストの最小化に貢献。
