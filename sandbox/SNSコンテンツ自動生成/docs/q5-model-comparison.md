## Q5: APIモデル比較・選定

### モデル料金比較（2026年2月時点）

| モデル | 入力 ($/1M tokens) | 出力 ($/1M tokens) | コンテキスト | 特徴 |
|--------|-------------------|-------------------|------------|------|
| **grok-4-1-fast** | $0.20 | $0.50 | 2M | 最安。高速。日本語性能は未知数 |
| **grok-3** | $3.00 | $15.00 | 131K | xAIフラグシップ。X連携強い |
| **grok-3-mini** | $0.30 | $0.50 | 131K | コスパ良。軽量タスク向け |
| **Gemini 2.5 Pro** | $1.25 | $10.00 | 2M | Google製。日本語学習データ豊富 |
| **Gemini 2.5 Flash** | $0.15 | $0.60 | 1M | 最安クラス。高速 |
| **GPT-4o** | $5.00 | $15.00 | 128K | OpenAI。日本語安定 |
| **Claude Sonnet 4.5** | $3.00 | $15.00 | 200K | Anthropic。高品質だがコスト高 |

ソース: [xAI公式 Models & Pricing](https://docs.x.ai/developers/models), [AI API Pricing Comparison 2026](https://intuitionlabs.ai/articles/ai-api-pricing-comparison-grok-gemini-openai-claude)

### 用途別の適性

#### ツイート生成（短文 140〜280文字）

| 評価軸 | Grok | Gemini | GPT-4o |
|--------|------|--------|--------|
| 短文の切れ味 | ◎（ウィットに富む、X文化に最適化） | ○（論理的・正確だがやや固い） | ○（バランス型） |
| リアルタイム情報 | ◎（X データに直接アクセス） | △（検索連携あるが即時性劣る） | △ |
| 日本語の自然さ | △〜○（情報少、要検証） | ○（学習データ豊富） | ◎（日本語実績豊富） |
| コスト（30本/月） | ◎（grok-4-1-fast: 推定 $0.01未満） | ◎（Flash: 推定 $0.01未満） | △（$0.05程度） |

#### Note記事生成（長文 2000〜5000文字）

| 評価軸 | Grok | Gemini | GPT-4o |
|--------|------|--------|--------|
| 長文の構成力 | ○ | ◎（2Mコンテキスト、長文得意） | ○ |
| 日本語文章の品質 | △〜○（要検証） | ○〜◎ | ◎ |
| コスト（4本/月） | ○（grok-3: 推定 $0.30） | ○（Pro: 推定 $0.20） | △（推定 $1.00） |

### 月間コスト試算

想定使用量: ツイート30本（各500トークン入出力）+ Note記事4本（各3000トークン入出力）

| 構成 | ツイート | Note記事 | 月間推定コスト |
|------|---------|---------|--------------|
| **推奨A: Grok + Gemini** | grok-4-1-fast ($0.20/$0.50) | Gemini 2.5 Pro ($1.25/$10) | **約 $0.15** |
| 推奨B: 全部Grok | grok-4-1-fast | grok-3 | 約 $0.25 |
| 推奨C: 全部Gemini | Gemini Flash | Gemini Pro | 約 $0.12 |
| 参考: 全部GPT-4o | GPT-4o | GPT-4o | 約 $1.20 |

### 推奨構成

**ツイート生成: grok-4-1-fast**
- 理由: 最安（$0.20/$0.50 per 1M）、X文化に最適化されたウィットのある文体、リアルタイムトレンド把握
- リスク: 日本語の自然さは要検証。初期テストで品質が低ければ Gemini Flash に切り替え

**Note記事生成: Gemini 2.5 Pro**
- 理由: 長文構成力が高い、2Mコンテキストで大量の参考資料を投入可能、日本語学習データが豊富（Google検索データ由来）
- リスク: 文体が固くなりがち。プロンプトで文体指定が必要

**代替案: 両方とも Gemini（Flash + Pro）**
- 理由: 単一ベンダーで管理が楽。最安。ただしGrokのX連携メリットを捨てることになる

### 主要な発見

1. **コストは全構成で月$1.5以下** — API料金は実質無視できるレベル。X API の料金（Basic $200/月）の方が圧倒的に高い
   - ソース: [xAI Models & Pricing](https://docs.x.ai/developers/models)

2. **GrokはX連携に強い** — リアルタイムのX データアクセスが差別化ポイント。ツイート生成には最適
   - ソース: [Grok vs Gemini Comparison 2026](https://www.demandsage.com/grok-vs-gemini/)

3. **Geminiは長文・多言語に強い** — 2Mコンテキスト + Google翻訳由来の日本語データで品質が高い
   - ソース: [Grok vs ChatGPT vs Gemini Comparison](https://screenapp.io/blog/grok-vs-chatgpt-vs-gemini)

4. **xAI新規登録で$25無料クレジット** — 月$150のデータ共有プログラムもあり、個人利用なら実質無料
   - ソース: [xAI API Pricing Guide](https://www.aifreeapi.com/en/posts/xai-grok-api-pricing)

5. **日本語生成品質の直接比較データは不足** — ベンチマークが英語中心。実機テストが必須
   - ソース: [Grok Review 2026](https://hackceleration.com/grok-review/)

### 情報の信頼性評価

- 一次ソース（公式）: 2件（xAI公式ドキュメント、Google AI公式）
- 二次ソース（比較レビュー・メディア）: 6件
- 注意: 料金は変動が激しいため、実装時に再確認が必要

### ソース一覧

1. [xAI Models & Pricing](https://docs.x.ai/developers/models) - 公式
2. [AI API Pricing Comparison 2026](https://intuitionlabs.ai/articles/ai-api-pricing-comparison-grok-gemini-openai-claude) - 比較レビュー
3. [Grok vs Gemini Comparison 2026](https://www.demandsage.com/grok-vs-gemini/) - メディア
4. [Grok vs ChatGPT vs Gemini](https://screenapp.io/blog/grok-vs-chatgpt-vs-gemini) - メディア
5. [xAI Grok API Pricing Guide](https://www.aifreeapi.com/en/posts/xai-grok-api-pricing) - ガイド
6. [Grok Review 2026](https://hackceleration.com/grok-review/) - レビュー
7. [xAI API Pricing (pricepertoken)](https://pricepertoken.com/pricing-page/provider/xai) - 料金比較
8. [Grok 3 API Pricing](https://pricepertoken.com/pricing-page/model/xai-grok-3) - 料金詳細
