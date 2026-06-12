# Claude Fable 5 完全ガイド — API・ベンチマーク・価格・実装例 (TrueFoundry)

- URL: https://www.truefoundry.com/blog/claude-fable-5-api-benchmarks-pricing-how-to-use-it
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-12

## 要約
TrueFoundryによるClaude Fable 5の実装向け完全ガイド。モデルID: claude-fable-5-20260609。主要仕様: 1Mコンテキスト・128k最大出力・アダプティブシンキング常時オン。ベンチマーク詳細: SWE-Bench Pro 80.3%（GPT-5.5: 58.6%）・HumanEval 96.2%・MMLU 91.8%・GPQA Diamond 78.4%・Vision benchmark 91.5%。価格: API $10/$50 per million input/output tokens。コスト最適化: プロンプトキャッシュ活用で最大60〜70%削減可能。AWS Bedrock（anthropic.claude-fable-5-20260609-v1:0）・Google Vertex AI対応済み。Python実装例・ストリーミング設定・システムプロンプト最適化パターンを掲載。Pro/Maxユーザーは6/9-22の無料期間に積極的に評価推奨。Fable 5とOpus 4.8の使い分け基準: コーディング・長時間エージェントタスクはFable 5、コスト重視はOpus 4.8。
