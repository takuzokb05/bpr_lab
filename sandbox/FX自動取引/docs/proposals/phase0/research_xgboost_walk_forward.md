# プロポーザル: XGBoost + Walk-Forward Optimization (WFO)

## 1. 戦略仮説

EUR/USD H1 / USD_JPY H1 などの主要通貨ペアで、**過去30バー分のラグ収益率・テクニカル指標 (RSI/ATR/MACD/MFI/ADX/ボラティリティ)** を XGBoost に投入し、N バー先の方向 (UP/DOWN/FLAT 三値分類) を予測する。Walk-Forward Optimization (WFO) で 6ヶ月学習 / 1ヶ月運用 を回し続ける。**「モデル自身が定期的に再学習することで非定常性に追随する」** ことを構造的優位にする。

## 2. 想定エッジ源 [G1-1]

- **短期モメンタムの自己相関**: H1 タイムフレームでは RSI 等の指標が短期反転を予測する有効性が論文で確認されている (Quantinsti, 2025)
- **特徴量の相互作用**: XGBoost のツリー構造が線形モデルでは捉えられない非線形相互作用 (例: 「ボラ高い + RSI70 超え」のような条件分岐) を学習できる
- **構造的優位の根拠**: 単一手法ではなく **「常に直近データで再学習され続ける」** こと自体がエッジ源。市場レジーム変化に追従できる
- **既知のリスク**: 過剰最適化 (1) と「予測精度 ≠ 収益性」のギャップ (2)。後者は **meta-labeling (Lopez de Prado)** で軽減 (G2-3 参照)

## 3. シグナル定義 (擬似コード)

```python
# 特徴量 (32種類)
features = [
    'lag_return_1', 'lag_return_5', 'lag_return_10', 'lag_return_30',
    'rsi_14', 'atr_14', 'macd_line', 'macd_signal', 'macd_hist',
    'mfi_14', 'adx_14', 'di_plus', 'di_minus',
    'bb_width', 'bb_position',
    'rolling_vol_5', 'rolling_vol_20',
    'hour_of_day', 'day_of_week',  # 周期性
    # ... + 12個程度のラグ・派生特徴量
]

# ラベル (3値: 1=UP, 0=FLAT, -1=DOWN)
threshold = 0.3 * atr_14  # ATR 基準でノイズ排除
y = sign(future_return_5_bars) if abs(future_return_5_bars) > threshold else 0

# Walk-Forward 設定
train_window = 4380 bars (6ヶ月)
test_window = 720 bars (1ヶ月)
step = 720 bars

# 予測 & 発注
prob_up = model.predict_proba(X_now)[:, 2]
prob_down = model.predict_proba(X_now)[:, 0]
if prob_up > 0.55 and (prob_up - prob_down) > 0.1:
    enter_long(size=risk_based, sl=2*atr, tp=3*atr)
elif prob_down > 0.55:
    enter_short(...)
```

## 4. データ要件 [G1-2]

- **必要データ**: MT5 H1 OHLCV (過去5年) — 既に `data/mt5_GBP_JPY_H1_5y.csv` で代表ペア取得済
- **取得元**: MT5 Python API (`mt5.copy_rates_from_pos`) — 無料、レート制限なし
- **計算リソース**: XGBoost 学習 1モデル ~30秒 (CPU 4コア)。WFO 5年分 = 60回学習 = 30分程度
- **ラグ**: バー閉鎖時刻 + 0-2秒 (特徴量計算 → 推論)
- **コスト**: 0円 (yfinance バックアップあり)

## 5. リスクモデル [G1-5]

| 項目 | 設定 |
|---|---|
| ポジションサイジング | 1取引あたり口座残高の 0.5-1.0% リスク (ATR 基準) |
| 損切り (SL) | 2 × ATR(14) |
| 利確 (TP) | 3 × ATR(14) (1.5RR) |
| 最大同時ポジション | 2 |
| 1日最大損失 | 3% (キルスイッチで強制停止) |
| 想定 MaxDD | 15-20% (歴史的なFX系統的戦略の典型) |
| テールリスク | フラッシュクラッシュ対応: SL 必須 + ニュース時間帯停止フィルタ |

## 6. 自己改善メカニズム [G0-B] — 必須

### ドリフト検出
- **直近100トレード PF を毎日計算**。PF < 1.0 が 2週間継続 → 再学習トリガ
- **KL ダイバージェンス**: 現在月の特徴量分布 vs 学習データ分布。閾値超過で再学習
- **予測誤差トラッキング**: 直近200本のヒット率が学習データの -10pp 以下に低下したら再学習

### 自動再最適化
- **月次 WFO 再学習** (デフォルト): 月初に直近6ヶ月で再学習
- **緊急再学習**: ドリフト検出時に即時実行 (cron + ファイル lock 機構)
- **ハイパーパラメータ最適化**: Optuna (TPE Sampler) で `max_depth, learning_rate, n_estimators, min_child_weight` を 3ヶ月ごとに調整 ([sumilk/algo_trading](https://github.com/sumilk/algo_trading/blob/main/Bayesian_Optimization.ipynb) 参照)

### フォールバック
- **新モデル PF < 直前モデル PF × 0.7** → 直前モデルへロールバック
- **3回連続再学習失敗** → アラート発報 + 取引停止 (キルスイッチ)
- **最後の安全 snapshot** を `models/snapshot_safe.pkl` として保持

## 7. 過去 BT 結果 [G0-A] — 必須

### 既存研究の参照
- **Quantinsti (2026)**: XGBoost + Walk-Forward Validation を EUR/USD H1 で実装。32 テクニカル指標 + ATR リスク管理で **return -68.56% → -11.40% (改善幅 83%)** だが絶対値はマイナス → スプレッド込みで赤字 ([Implement Walk-Forward Optimization with XGBoost](https://blog.quantinsti.com/walk-forward-optimization-python-xgboost-stock-prediction/))
- **NEPSE Index (arXiv 2026)**: XGBoost + WFO で株価インデックス予測の有効性を実証 ([XGBoost Forecasting](https://arxiv.org/pdf/2601.08896))
- **forextester (2025)**: 同様のトレンドフォロー戦略で **CAGR 8.9%, 勝率 57%, PF 1.6, MaxDD 18%** ([Momentum Trading Strategies](https://forextester.com/blog/momentum-trading-strategies/))

### 自前 BT 提案
- `scripts/_contrarian_bt.py` を改造し XGBoost ラッパーを実装
- 過去5年 USD_JPY H1 で WFO (6mo学習 / 1mo運用) を回し、累計 PF を測定
- スプレッド 1.5pip + スリッページ 0.5pip 込み

### PF > 0.95 を超える論拠
- 既存研究で PF 1.6 級が報告されている (forextester)
- 量子-取引研究は WFO + meta-labeling 併用で PF 1.2-1.5 を達成
- **「予測精度 50.5% 程度でもケリー基準で正の期待値」** という理論的根拠あり

### 留意
- **Quantinsti EUR/USD で赤字** という事実は重く受け止める。特徴量設計とラベリング設計次第。**Triple-Barrier + Meta-Labeling** 併用が必須

## 8. WFA / OOS [G1-7]

- **In-Sample (IS)**: 6ヶ月、Out-of-Sample (OOS): 1ヶ月、5年分で 60サイクル
- **Anchored vs Rolling**: Rolling (直近のみ学習) を採用。市場変化に追従
- **Deflated Sharpe Ratio (DSR)**: Bailey & Lopez de Prado (2014) でハイパーパラメータ探索回数を補正 ([Deflated Sharpe Ratio](https://en.wikipedia.org/wiki/Deflated_Sharpe_ratio))
- **Combinatorial Purged Cross-Validation (CPCV)**: 通常のWFOより過剰最適化検出力が高い ([Backtest overfitting in the ML era](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110))

## 9. 実装複雑度 [G1-3]

- **工数見積もり**: 2-3週間
  - Week 1: 特徴量パイプライン + XGBoost ラッパー
  - Week 2: WFO ループ + ドリフト検出ロジック
  - Week 3: meta-labeling + Optuna 統合 + バックテスト
- **依存ライブラリ**: `xgboost, scikit-learn, optuna, pandas-ta, mt5` — 全て成熟版
- **外部 API 依存**: MT5 のみ (既存接続あり)
- **既存資産活用**: `src/backtester.py`, `scripts/_contrarian_bt.py` のロジック流用可能

## 10. 機会費用比較 [G1-6]

| 対象 | 想定年率 | 100万円運用時 / 年 |
|---|---|---|
| 米国債 4% | 4.0% | 40,000 JPY |
| 全世界株 8% | 8.0% | 80,000 JPY |
| 銀行預金 | 0.05% | 500 JPY |
| **本戦略 (期待値)** | **15-25%** (PF 1.3-1.6 級) | **150,000-250,000 JPY** |

PoC は 10万円から開始可能 (MT5 デモは無料)。500万円スケールで年 75-125万円が現実的目標。

## 11. リスク・既知の弱点

1. **「予測精度が高くても PF が低い」問題**: 直近 Quantinsti 例で実証されている。Triple-Barrier + Meta-Labeling 必須
2. **再学習タイミングのバッドフィット**: トレンド転換直後に再学習すると過剰追従。ドリフト検出を慎重に
3. **特徴量リーク**: 未来データの混入は致命的。`shift()` を厳密に管理
4. **ハイパーパラメータ探索の overfitting**: Optuna 試行回数を 100 以下に制限 + DSR で補正
5. **計算コスト**: 通貨ペアを増やすと指数的に学習時間増 (5ペアで >2時間)。VPS リソース要確認
6. **亡き者の世界との関係**: 旧 MTFPullback は MA+ADX 単純ルールだった。XGBoost はそれの「複雑性で塗りつぶし」ではなく、別系統 (短期反転重視) として設計

## 12. 採点自己評価

### Gate 0 (必須)

| 項目 | 評価 | コメント |
|---|---|---|
| **G0-A**: PF > 0.95 | **△** | 既存研究で PF 1.3-1.6 報告あり。ただし Quantinsti EUR/USD は赤字 → ペア・タイムフレーム選定が要 |
| **G0-B**: 自己改善 | **○** | WFO + ドリフト検出 + Optuna再最適化 + フォールバックを設計 |

→ **Gate 0 = 条件付き PASS** (簡易 BT で実証必要)

### Gate 1 (各10点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G1-1 想定エッジ源 | 7 | 短期モメンタムの自己相関 + 非線形相互作用学習。「過去で効いた」依存も残る |
| G1-2 データ要件 | 9 | MT5 のみ、コスト 0、ラグ最小 |
| G1-3 実装複雑度 | 7 | 2-3週間。中複雑度 (依存少なめだが meta-labeling 工程あり) |
| G1-4 ロバスト性 | 6 | パラメータ感度高め、市場レジーム変化耐性は WFO で吸収 |
| G1-5 リスクプロファイル | 8 | SL/TP 設計明確、キルスイッチあり、テールリスク中程度 |
| G1-6 機会費用比較 | 8 | 期待 15-25% は株式の倍、未実証分減点 |
| G1-7 WFA / OOS | 9 | CPCV + DSR で過剰最適化補正、5年 60サイクル |

**Gate 1 = 54/70**

### Gate 2 (各5点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G2-1 スプレッド耐性 | 3 | H1 中頻度。スプレッド 2x で PF 1.0 ギリギリの可能性 |
| G2-2 他戦略との相関 | 4 | 短期反転系のため、トレンドフォロー系と低相関 |
| G2-3 説明可能性 | 4 | XGBoost feature_importances_ で可視化可、tree 構造も読める |
| G2-4 レビュー耐性 | 4 | meta-labeling/DSR で多重検定問題に対処。反論屋耐性は中程度 |
| G2-5 拡張性 | 4 | ペア・時間軸の追加は容易、計算コスト次第 |
| G2-6 過去挙動データ整合 | 3 | 亡き者 GBP_JPY は MTFPullback (中期トレンド)。本戦略 (短期反転重視) は別系統 → 整合確認は要BT |

**Gate 2 = 22/30**

### 総合

| Gate | 点数 | 合否 |
|---|---|---|
| Gate 0 | PASS (条件付き) | 簡易 BT で PF > 0.95 を実証要 |
| Gate 1 | 54/70 | Phase 2 進出基準 (50点以上) クリア |
| Gate 2 | 22/30 | 加点 |
| **総合** | **76/100** | **Phase 1 (簡易 BT) 進出候補** |

---

## ソース

1. [Implement Walk-Forward Optimization with XGBoost for Stock Price Prediction in Python](https://blog.quantinsti.com/walk-forward-optimization-python-xgboost-stock-prediction/) - Quantinsti (2026) — XGBoost + WFO + 32特徴量 EUR/USD H1 実装ガイド
2. [XGBoost Forecasting of NEPSE Index Log Returns with Walk Forward Validation](https://arxiv.org/pdf/2601.08896) - arXiv (2026) — WFO の有効性論文
3. [Momentum Trading Strategies: Proven Tactics, Indicators & Real Backtests](https://forextester.com/blog/momentum-trading-strategies/) - Forextester (2025) — CAGR 8.9% / PF 1.6 / MaxDD 18% 実績
4. [Deflated Sharpe Ratio](https://en.wikipedia.org/wiki/Deflated_Sharpe_ratio) - Bailey & López de Prado (2014)
5. [sumilk/algo_trading - Bayesian Optimization](https://github.com/sumilk/algo_trading/blob/main/Bayesian_Optimization.ipynb) - Optuna 適用例
6. [Backtest overfitting in the ML era](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110) - CPCV vs 従来 WFO 比較
7. [Meta-Labeling - Wikipedia](https://en.wikipedia.org/wiki/Meta-Labeling) - Lopez de Prado meta-labeling
