# QuantaAlpha: LLM駆動アルファ因子マイニングの進化的フレームワーク（清華大・arxiv）

- URL: https://arxiv.org/abs/2602.07085
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-14

## 投稿内容
QuantaAlpha: An Evolutionary Framework for LLM-Driven Alpha Mining — arXiv:2602.07085

Framework: treats each end-to-end mining run as a "trajectory", improves factors through trajectory-level mutation and crossover operations, localizes suboptimal steps for targeted revision, recombines complementary high-reward segments.

Results vs baselines:
- vs RD-Agent: IC +0.0970, ARR +17.84%, MDD reduced
- vs AlphaAgent: IC +0.0535, ARR +12.21%, MDD reduced

Transfer results: CSI 300 → CSI 500: 160% cumulative excess return (4 years); CSI 300 → S&P 500: 137% cumulative excess return (4 years)

Team: professors/postdocs/PhDs from Tsinghua, Peking University, CAS, CMU, HKUST. GitHub available.

## 要約
清華大・北大・CAS・CMU・HKUSTの研究者チームによる2026年2月arXiv論文（GitHub公開済み）。QuantaAlphaは各マイニング実行を「軌跡（trajectory）」として扱い、軌跡レベルの突然変異とクロスオーバーで因子を改善する進化的アルファマイニングフレームワーク。既存LLMエージェントアルファマイニング（AlphaAgent・RD-Agent）と比較して: IC +0.0970・ARR +17.84%の改善（vs RD-Agent）、IC +0.0535・ARR +12.21%の改善（vs AlphaAgent）、最大ドローダウン（MDD）も削減。特に注目すべき成果: CSI 300で学習した因子がCSI 500・S&P 500に転用可能で、4年間の累積超過リターン160%・137%を記録。LLMを使った「コントローラブルなマルチラウンド検索」と「実証済み経験の再利用」が主要な技術的貢献。金融市場のノイズ・非定常性に対応するため、バックテスト結果の過学習を避ける設計が特徴。FXや株式の定量投資戦略開発に応用可能な研究成果。
