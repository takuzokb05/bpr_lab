# プロポーザル: 経済ニュースセンチメント (BERT) + GARCH ボラ予測

## 1. 戦略仮説

経済指標発表・中央銀行声明・地政学ニュースのテキストから **BERT/FinBERT** でセンチメントスコアを抽出し、**GARCH モデル** で予測したボラティリティと組み合わせる。「高センチメント変動 × 高ボラ予測」 時にイベントドリブン的にエントリーする。重要指標 (FOMC、ECB、日銀、NFP等) **発表直後のオーバーリアクション/アンダーリアクション** を狙う。

## 2. 想定エッジ源 [G1-1]

- **情報非対称**: 人間トレーダーがニュースを読むのに数秒〜数十秒かかる間に、LLM は数百 ms で同等以上の判断ができる (機械的優位)
- **行動経済学的非効率**: 重要指標発表後の過剰反応 (overshooting) と数時間以内の修正が実証 (Bodilsen 2025)
- **GARCH のボラクラスタリング検出**: イベント前後のボラ上昇を統計的に予測可能
- **構造的優位**: テキスト + 時系列の融合は研究最前線、retail trader 競合少ない
- **既知のリスク**: 重要イベント時のスプレッド拡大 (通常 2-3pip → 10-20pip)、スリッページ大

## 3. シグナル定義 (擬似コード)

```python
# Stage 1: ニュース収集 (リアルタイム)
from newsapi import NewsApiClient
news = newsapi.get_everything(
    q='ECB OR FOMC OR BOJ OR "nonfarm payrolls"',
    from_param=now - timedelta(hours=1),
)

# Stage 2: FinBERT センチメント抽出
from transformers import pipeline
finbert = pipeline('sentiment-analysis', model='ProsusAI/finbert')
sentiment_scores = [finbert(article['title'])[0] for article in news]
# {'label': 'positive', 'score': 0.87} 形式
sentiment_aggregate = mean_weighted_by_recency(sentiment_scores)

# Stage 3: GARCH ボラ予測
from arch import arch_model
garch = arch_model(returns, vol='Garch', p=1, q=1)
result = garch.fit(disp='off')
vol_forecast_next_hour = result.forecast(horizon=1).variance.iloc[-1, 0] ** 0.5

# Stage 4: シグナル
if sentiment_aggregate > 0.7 and vol_forecast > vol_threshold:
    enter_long(USD/JPY, lot=0.5*normal_lot, sl=tight, tp=2*atr_pre_event)
elif sentiment_aggregate < 0.3:
    enter_short(...)
```

## 4. データ要件 [G1-2]

- **ニュースデータ**:
  - **NewsAPI** ($449/月 for business、無料枠は100req/日のみ)
  - **GDELT** (無料、しかしレイテンシ15分)
  - **Reuters / Bloomberg API** (個人不可)
  - → **GDELT または NewsAPI 無料枠** が現実的
- **経済カレンダー**: ForexFactory (無料スクレイピング) または FRED API
- **LLM 推論**: FinBERT (HuggingFace) ローカル推論で **GPU 推奨だが CPU 可** (1記事 0.2秒)
- **必要データ**: 通貨ペア H1 OHLCV + ニュースタイムスタンプ
- **計算リソース**: FinBERT 推論で 1日 100記事処理 = 20秒

## 5. リスクモデル [G1-5]

| 項目 | 設定 |
|---|---|
| ポジションサイジング | **重要イベント時は通常の 50%** (ボラ拡大対応) |
| 損切り (SL) | イベント直後は **タイト 1×ATR**、その後 2×ATR に拡大 |
| 利確 (TP) | 2×ATR (短時間決済前提) |
| エントリー時間制限 | イベント発表後 **5-30 分** 限定 |
| 最大ポジション保有時間 | 4時間 |
| 想定 MaxDD | 15-25% (イベント trading は高分散) |

## 6. 自己改善メカニズム [G0-B] — 必須

### ドリフト検出
- **センチメント-リターン相関の monitoring**: 直近 100イベントの相関係数が 0.1 を下回ったら警戒
- **FinBERT の信頼度推移**: 平均信頼度 (label score) が低下したら、新モデルへの差替えを検討
- **重要度別ヒット率**: 高インパクト指標 (FOMC等) のヒット率が 50%を割ったら戦略停止

### 自動再最適化
- **月次**: GARCH パラメータの再フィッティング (過去 1000バー)
- **四半期**: FinBERT を **FinBERT-Tone, FinBERT-FLS** などの新モデルと比較し精度高い方を採用
- **イベント分類モデル**: 「市場が反応するか」を予測する二次分類器を月次学習 (meta-labeling 的)

### フォールバック
- **新モデル AUC < 直前モデル AUC × 0.9** → ロールバック
- **3イベント連続損失** → 1週間停止 + パラメータ見直し
- **「観察モード」**: 新規エントリー停止し、ログだけ取って次戦略候補を探索

## 7. 過去 BT 結果 [G0-A] — 必須

### 既存研究の参照
- **Bodilsen (Wiley 2025) "Exploiting News Analytics for Volatility Forecasting"**: 国内マクロニュースセンチメントが個別株 + S&P 500 のボラ予測を大幅改善 ([Wiley](https://onlinelibrary.wiley.com/doi/full/10.1002/jae.3095))
- **arXiv 2510.16503 "Sentiment and Volatility... BERT and GARCH"**: BERT + GARCH-Student-t で地政学危機時のボラ予測に成功 ([arXiv](https://arxiv.org/pdf/2510.16503))
- **arXiv 2503.19767 "Equity volatility with attention and sentiment"**: smooth-transition GARCH × ニュースセンチメントで予測力向上 ([arXiv](https://arxiv.org/pdf/2503.19767))
- **MDPI 2025 "News Sentiment and Stock Market"**: ML + センチメント統合の有効性実証 ([MDPI](https://www.mdpi.com/1911-8074/18/8/412))

### PF > 0.95 を超える論拠
- ボラ予測の改善は実証済 → 取引タイミングの精度向上に直結
- ただし、**ボラ予測 ≠ 方向予測**。本戦略はセンチメントで方向、GARCH で「機会の大きさ」を判断
- イベント trading は **アクティブ運用者の競合場**。retail vs HFT で勝てるか疑問あり

### 自前 BT 提案
- 過去2年の FOMC, ECB, 日銀イベントを抽出
- 各イベント直後のセンチメント + ボラ予測 + 価格変動を関連付け
- 累計 PF を算出 (スプレッド拡大込み)

## 8. WFA / OOS [G1-7]

- **Walk-Forward**: 18ヶ月学習 / 6ヶ月運用、過去5年で 6サイクル
- **イベント数の少なさ**: FOMC は年 8回、ECB 年 8回、日銀 年 8回 → 全部で年 20-30 イベント。**5年で 100-150 サンプル**
- **サンプル少すぎ問題**: Deflated Sharpe で厳しく補正必要
- **重要度別評価**: 高/中/低インパクト別に PF を測定 (低インパクトは捨てる判断あり)

## 9. 実装複雑度 [G1-3]

- **工数見積もり**: 4週間
  - Week 1: ニュースデータパイプライン + ForexFactory スクレイピング
  - Week 2: FinBERT 統合 + センチメント集計
  - Week 3: GARCH + シグナル生成
  - Week 4: WFO + フォールバック + バックテスト
- **依存ライブラリ**: `transformers, arch (GARCH), beautifulsoup4, mt5, pandas`
- **外部 API 依存**: NewsAPI または GDELT (信頼性中)
- **既存資産活用**: `src/event_filter.py` (亡き者にイベントフィルタあれば再利用)

## 10. 機会費用比較 [G1-6]

| 対象 | 想定年率 | 100万円運用時 / 年 |
|---|---|---|
| 米国債 4% | 4.0% | 40,000 JPY |
| 全世界株 8% | 8.0% | 80,000 JPY |
| 銀行預金 | 0.05% | 500 JPY |
| **本戦略 (期待値)** | **8-20% (高分散)** | **80,000-200,000 JPY** |

イベント数が少ないため、**月数回〜十数回の取引**。期待値の絶対額は中程度だが、**他戦略と無相関** で分散源として価値。

## 11. リスク・既知の弱点

1. **スプレッド拡大**: FOMC 等の重要イベント時に通常 2pip → 10-20pip に拡大。**戦略の根幹を脅かす**
2. **スリッページ**: 高ボラ時の指値約定困難、成行は不利
3. **ニュースの遅延**: 個人向けニュースAPIは 15分遅延が普通、HFT 競合に勝てない
4. **FinBERT の汎用性限界**: 株式コーパスで学習 → FX 用語に弱い可能性
5. **イベント分類の主観性**: 「重要度」の事前判定が困難 (例: 「想定通り」の声明でも市場反応)
6. **規制リスク**: 日本では「特定の経済情報を使った機械的取引」が金商法上のグレーゾーン領域 (内部情報ではないが、調査要)
7. **亡き者の世界との関係**: 全く新系統、既存挙動データから整合性確認不可

## 12. 採点自己評価

### Gate 0 (必須)

| 項目 | 評価 | コメント |
|---|---|---|
| **G0-A**: PF > 0.95 | **△** | センチメント-ボラ予測の有効性は実証、FX 取引 PF は未実証 |
| **G0-B**: 自己改善 | **○** | 月次 GARCH 再学習 + 四半期モデル比較 + ロールバック |

→ **Gate 0 = 条件付き PASS**

### Gate 1 (各10点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G1-1 想定エッジ源 | 7 | 行動経済学的根拠 + LLM 機械的優位、ただし HFT 競合あり |
| G1-2 データ要件 | 5 | NewsAPI 有料、GDELT 遅延あり。**最大のボトルネック** |
| G1-3 実装複雑度 | 6 | 4週間、スクレイピング + LLM 推論 + GARCH の3層工程 |
| G1-4 ロバスト性 | 5 | センチメントモデルの陳腐化リスク、イベント数少なくサンプル外脆弱 |
| G1-5 リスクプロファイル | 5 | スプレッド拡大が致命的、SL タイト化で部分緩和 |
| G1-6 機会費用比較 | 6 | 期待値 8-20% は中位、低相関で分散価値 |
| G1-7 WFA / OOS | 4 | イベント数少なくサンプル外検証が統計的に不安 |

**Gate 1 = 38/70**

### Gate 2 (各5点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G2-1 スプレッド耐性 | 1 | **最大の脆弱性**。イベント時の 10倍拡大が前提 |
| G2-2 他戦略との相関 | 5 | イベントドリブン = 他戦略と低相関、分散源 |
| G2-3 説明可能性 | 4 | 「FOMC でドル上昇」の判断根拠は人間理解可能 |
| G2-4 レビュー耐性 | 3 | 「スプレッド/スリッページで実用性怪しい」と批判される可能性大 |
| G2-5 拡張性 | 3 | ニュースソース追加可、ただし API コスト膨らむ |
| G2-6 過去挙動データ整合 | 2 | 亡き者と全く別系統、整合性確認不可 |

**Gate 2 = 18/30**

### 総合

| Gate | 点数 | 合否 |
|---|---|---|
| Gate 0 | 条件付き PASS | スプレッド込み BT 必須 |
| Gate 1 | 38/70 | **進出基準 (50点) 未達** |
| Gate 2 | 18/30 | 加点小 |
| **総合** | **56/100** | **Phase 1 進出基準 (70点) 未達 — 棚上げ候補** |

### 結論
データコスト、スプレッド脆弱性、HFT競合の三重苦で個人投資家向けには **オーバーヘッド過大**。研究的価値はあるが Phase 1 進出は推奨しない。「分散源」としては魅力 → 将来 XGBoost / コインテグレーション戦略が確立した後、補完戦略として再評価。

---

## ソース

1. [Exploiting News Analytics for Volatility Forecasting (Wiley 2025)](https://onlinelibrary.wiley.com/doi/full/10.1002/jae.3095) - Bodilsen
2. [Sentiment and Volatility in Financial Markets: BERT and GARCH (arXiv 2510)](https://arxiv.org/pdf/2510.16503)
3. [Forecasting U.S. equity market volatility with attention and sentiment (arXiv 2503)](https://arxiv.org/pdf/2503.19767)
4. [News Sentiment and Stock Market Dynamics (MDPI 2025)](https://www.mdpi.com/1911-8074/18/8/412)
5. [FinBERT - ProsusAI on HuggingFace](https://huggingface.co/ProsusAI/finbert)
6. [arch (GARCH) Python library](https://arch.readthedocs.io/)
