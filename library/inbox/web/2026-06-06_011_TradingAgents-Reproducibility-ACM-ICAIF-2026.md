# Reproducibility in the TradingAgents Framework — ACM ICAIF 2026

- URL: https://dl.acm.org/doi/10.1145/3800973.3801029
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-06

## 要約

ACM 2026 International Conference on Artificial Intelligence and Fintechで発表されたTradingAgentsフレームワークの再現性検証論文。UCLA+MITオリジナル論文の結果を独立チームが再現実験し、バックテスト条件（データリーク・未来情報混入・ルックアヘッドバイアス）が再現性に与える影響を定量評価。arxiv.org/pdf/2601.13770（Look-Ahead-Bench）と合わせて読む必要がある研究で、「LLM取引エージェントの過去パフォーマンスが現実に再現可能か」という実用上の核心問題に取り組む。結論として一部戦略は再現可能だが、センチメント分析精度がLLMバージョンに強く依存するため本番移行前の慎重な検証が必要。FX自動取引でTradingAgentsを採用する際のリスク評価に直接関連する学術知見。
