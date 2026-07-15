## Q2: X API（Twitter API）の仕様・ツイート取得調査

### 主要な発見

1. **X API v2 の料金プラン（2026年2月時点）**
   - 要点: 4つのプランが存在。Free は実質「書き込み専用」でツイート読み取り不可
   - データ:
     | プラン | 月額 | 読み取り上限 | 書き込み上限 | API バージョン |
     |--------|------|------------|------------|--------------|
     | Free | $0 | 0件/月 | 1,500件/月 | v2 のみ |
     | Basic | $200 | 15,000件/月 | 50,000件/月 | v1.1 & v2 |
     | Pro | $5,000 | 1,000,000件/月 | 300,000件/月 | v1.1 & v2 |
     | Enterprise | $42,000+ | 50M+件/月 | 要相談 | 全バージョン |
   - 注意: 2025年12月から Pay-Per-Use（従量課金）のパイロットプログラムが閉鎖ベータで開始。クレジットベースの柔軟な課金が可能になる見込み
   - ソース: [X/Twitter API Pricing 2026](https://getlate.dev/blog/twitter-api-pricing)

2. **自分の過去ツイートを取得する方法**
   - エンドポイント: `GET /2/users/:id/tweets`（ユーザータイムライン）
   - 取得可能範囲: 直近3,200件のツイート（リツイート、リプライ、引用ツイート含む）
   - 主要パラメータ:
     - `start_time` / `end_time`: 期間指定（ISO 8601形式）
     - `max_results`: 1回あたり最大100件
     - `tweet.fields`: `created_at,public_metrics,non_public_metrics` 等を指定
     - `pagination_token`: ページネーション用
   - 認証: OAuth 1.0a User Context / OAuth 2.0 Authorization Code with PKCE / OAuth 2.0 App-Only
   - レート制限: 180リクエスト/15分（ユーザー単位）
   - ソース: [Timelines introduction | X Developer Platform](https://developer.x.com/en/docs/x-api/tweets/timelines/introduction)

3. **エンゲージメントデータの取得方法**
   - 4種類のメトリクスが存在:
     | メトリクス種別 | 認証 | 対象 | 制限 | 主なフィールド |
     |--------------|------|------|------|--------------|
     | public_metrics | Bearer Token（誰でも） | 全ての公開ツイート | なし | retweet_count, quote_count, like_count, reply_count, impression_count |
     | non_public_metrics | ユーザー認証 | 自分のツイートのみ | 過去30日 | url_link_clicks, user_profile_clicks, impression_count |
     | organic_metrics | ユーザー認証 | 自分のツイートのみ | 過去30日 | 非プロモーション由来の全メトリクス |
     | promoted_metrics | ユーザー認証 | プロモーションツイートのみ | 過去30日 | 広告由来のメトリクス |
   - 動画メトリクス（non_public_metrics 内）: `playback_0_count`, `playback_25_count`, `playback_50_count`, `playback_75_count`, `playback_100_count`
   - 重要: `impression_count` は public_metrics にも含まれるが、non_public_metrics の方がより詳細
   - ソース: [Metrics | X API](https://docs.x.com/x-api/fundamentals/metrics)

4. **レート制限（プランごと）**
   - Free: エンドポイントごとに24時間ウィンドウで制限（非常に厳しい）
   - Basic/Pro: 15分ウィンドウで制限（頻繁にリセットされるため実用的）
   - ユーザータイムライン: 180リクエスト/15分
   - 月間制限: Free=読み取り0件、Basic=15,000件、Pro=1,000,000件
   - 超過時: HTTP 429 エラー
   - ソース: [X API Rate Limits](https://docs.x.com/x-api/fundamentals/rate-limits)

5. **Python での実装方法（tweepy）**
   - ライブラリ: `tweepy`（v4.14.0が最新安定版）
   - インストール: `pip install tweepy`
   - 実装例:
     ```python
     import tweepy

     # OAuth 2.0 で認証（自分のツイート + エンゲージメント取得に必要）
     client = tweepy.Client(
         bearer_token="YOUR_BEARER_TOKEN",
         consumer_key="YOUR_CONSUMER_KEY",
         consumer_secret="YOUR_CONSUMER_SECRET",
         access_token="YOUR_ACCESS_TOKEN",
         access_token_secret="YOUR_ACCESS_TOKEN_SECRET"
     )

     # 自分のツイートを取得（エンゲージメントデータ付き）
     user_id = "YOUR_USER_ID"
     tweets = client.get_users_tweets(
         id=user_id,
         max_results=100,
         tweet_fields=[
             "created_at",
             "public_metrics",
             "non_public_metrics",
             "organic_metrics"
         ]
     )

     for tweet in tweets.data:
         print(f"テキスト: {tweet.text}")
         print(f"いいね: {tweet.public_metrics['like_count']}")
         print(f"RT: {tweet.public_metrics['retweet_count']}")
         print(f"インプレッション: {tweet.public_metrics['impression_count']}")
     ```
   - 注意: `non_public_metrics` と `organic_metrics` は自分のツイートのみ、かつ過去30日以内
   - ソース: [Client - tweepy 4.14.0 documentation](https://docs.tweepy.org/en/stable/client.html)

### SNSコンテンツ生成プロジェクトへの影響

- **推奨プラン**: Basic ($200/月) で開始。月15,000件読み取り = 過去ツイートの初回取得 + 定期的な分析に十分
- **コスト懸念**: Free プランではツイート読み取りが不可能なため、最低 Basic ($200/月) が必要
- **代替案**: Pay-Per-Use パイロットが一般開放されれば、利用量の少ない個人プロジェクトにはより安価になる可能性
- **制約**: non_public_metrics（詳細なインプレッション等）は過去30日以内のツイートのみ。長期分析には public_metrics を使用する必要あり

### 情報の信頼性評価
- 一次ソース（公式ドキュメント）: 4件
- 二次ソース（メディア・比較サイト）: 3件

### ソース一覧
1. [About the X API](https://docs.x.com/x-api/getting-started/about-x-api) - 公式ドキュメント
2. [Metrics | X API](https://docs.x.com/x-api/fundamentals/metrics) - 公式ドキュメント
3. [X API Rate Limits](https://docs.x.com/x-api/fundamentals/rate-limits) - 公式ドキュメント
4. [Client - tweepy documentation](https://docs.tweepy.org/en/stable/client.html) - 公式ライブラリドキュメント
5. [X/Twitter API Pricing 2026](https://getlate.dev/blog/twitter-api-pricing) - 価格比較記事
6. [X API Pricing Tiers | Jesus Iniesta](https://jesusiniesta.es/blog/x-api-pricing-tiers-what-you-actually-get) - 解説記事
7. [X API Pricing 2025 | twitterapi.io](https://twitterapi.io/blog/twitter-api-pricing-2025) - 価格情報
