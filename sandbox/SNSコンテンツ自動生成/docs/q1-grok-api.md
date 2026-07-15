## Q1: Grok API の仕様・モデル・料金調査

### 主要な発見

1. **OpenAI SDK互換のAPIインターフェース**
   - 要点: xAI の Grok API は OpenAI SDK と互換性があり、`base_url` を `https://api.x.ai/v1` に変更するだけで既存の OpenAI コードを流用可能
   - データ: 公式 Python SDK (`pip install xai-sdk`) と OpenAI SDK の両方が利用可能
   - 補足: Anthropic SDK 互換は完全に非推奨（deprecated）
   - ソース: [Getting Started | xAI](https://docs.x.ai/developers/quickstart)

2. **利用可能なモデル一覧と特徴**
   - テキスト生成（推論あり）:
     | モデル | 入力 ($/1M tokens) | 出力 ($/1M tokens) | キャッシュ入力 | コンテキスト |
     |--------|-------------------|-------------------|--------------|-------------|
     | grok-4-1-fast-reasoning | $0.20 | $0.50 | $0.05 | 2M |
     | grok-4-fast-reasoning | $0.20 | $0.50 | $0.05 | 2M |
     | grok-4-0709 | $3.00 | $15.00 | $0.75 | 256K |
     | grok-3-mini | $0.30 | $0.50 | $0.07 | 131K |
     | grok-code-fast-1 | $0.20 | $1.50 | $0.02 | 256K |
   - テキスト生成（推論なし）:
     | モデル | 入力 ($/1M tokens) | 出力 ($/1M tokens) | キャッシュ入力 | コンテキスト |
     |--------|-------------------|-------------------|--------------|-------------|
     | grok-4-1-fast-non-reasoning | $0.20 | $0.50 | $0.05 | 2M |
     | grok-4-fast-non-reasoning | $0.20 | $0.50 | $0.05 | 2M |
     | grok-3 | $3.00 | $15.00 | $0.75 | 131K |
   - 補足: grok-4-1-fast が最新かつ最安（2026年2月時点）
   - ソース: [Models and Pricing | xAI](https://docs.x.ai/developers/models)

3. **料金体系**
   - 要点: 従量課金制。無料枠は無いが、新規登録時に $25 のプロモーションクレジットあり
   - データ: データ共有プログラムに参加すると月額 $150 の無料クレジット追加（ただし事前に $5 以上の API 利用が条件）
   - 想定コスト: 軽量利用（個人プロジェクト）で月 $5〜30、中規模で $30〜150
   - Batch API で50%割引（非同期処理）
   - ソース: [xAI Grok API Pricing 2026](https://www.aifreeapi.com/en/posts/xai-grok-api-pricing)

4. **レート制限**
   - 要点: モデル・ティアごとに RPM（リクエスト/分）と TPM（トークン/分）が設定
   - データ: grok-4-fast 系は 480 RPM / 4M TPM（参考値）
   - 確認方法: xAI Console（console.x.ai）で自チームの制限を確認可能
   - 制限超過時: HTTP 429 エラー。上限引き上げは support@x.ai に連絡
   - ソース: [Consumption and Rate Limits | xAI](https://docs.x.ai/docs/key-information/consumption-and-rate-limits)

5. **Python SDK の使い方**
   - 公式 SDK:
     ```python
     pip install xai-sdk
     ```
     ```python
     import os
     from xai_sdk import Client
     from xai_sdk.chat import user, system

     client = Client(api_key=os.getenv("XAI_API_KEY"), timeout=3600)
     chat = client.chat.create(model="grok-4-1-fast-reasoning")
     chat.append(system("あなたは優秀なアシスタントです。"))
     chat.append(user("ツイートを生成してください"))
     response = chat.sample()
     print(response.content)
     ```
   - OpenAI SDK 互換:
     ```python
     pip install openai
     ```
     ```python
     import os
     from openai import OpenAI

     client = OpenAI(
         api_key=os.getenv("XAI_API_KEY"),
         base_url="https://api.x.ai/v1",
     )
     completion = client.responses.create(
         model="grok-4-1-fast-reasoning",
         input=[
             {"role": "system", "content": "あなたは優秀なアシスタントです。"},
             {"role": "user", "content": "ツイートを生成してください"},
         ],
     )
     print(completion.output[0].content)
     ```
   - ソース: [The Hitchhiker's Guide to Grok | xAI](https://docs.x.ai/docs/tutorial)

### SNSコンテンツ生成への適性評価

- **ツイート生成（短文）**: grok-4-1-fast-non-reasoning が最適。低コスト ($0.20/$0.50) で高速。推論不要なタスクに最適化
- **長文記事生成**: grok-4-1-fast-reasoning がコスパ良好。2M コンテキストで長文にも対応
- **コスト見積り**: ツイート100件/日（各500トークン出力想定）= 月約 $0.75 と非常に安価

### 情報の信頼性評価
- 一次ソース（公式ドキュメント）: 4件
- 二次ソース（メディア・比較サイト）: 2件

### ソース一覧
1. [Models and Pricing | xAI](https://docs.x.ai/developers/models) - 公式ドキュメント
2. [Getting Started | xAI](https://docs.x.ai/developers/quickstart) - 公式ドキュメント
3. [Consumption and Rate Limits | xAI](https://docs.x.ai/docs/key-information/consumption-and-rate-limits) - 公式ドキュメント
4. [The Hitchhiker's Guide to Grok | xAI](https://docs.x.ai/docs/tutorial) - 公式チュートリアル
5. [AI API Pricing Comparison 2026 | IntuitionLabs](https://intuitionlabs.ai/articles/ai-api-pricing-comparison-grok-gemini-openai-claude) - 比較サイト
6. [xAI Grok API Pricing 2026](https://www.aifreeapi.com/en/posts/xai-grok-api-pricing) - 料金ガイド
