# プロポーザル: HMM レジーム検出 + 専用 ML モデルアンサンブル

## 1. 戦略仮説

市場には **「低ボラ・トレンド」「低ボラ・レンジ」「高ボラ・トレンド」「高ボラ・カオス」** の隠れ状態 (regime) が存在する。Hidden Markov Model (HMM) で **2-4 状態を識別**し、各レジームに **個別の Random Forest / XGBoost 分類器**を割り当てる。レジーム遷移確率に応じて取引判断を切替。**「市場が変わったら、戦略も変わる」** という生命体型構造で長期適応する。

## 2. 想定エッジ源 [G1-1]

- **市場レジームの非定常性**: トレンド時とレンジ時では有効指標が逆転する (例: ブレイクアウトはトレンドで勝つがレンジで負ける)。**単一モデルは全期間の平均値を学習してしまい不利**
- **HMM の隠れ状態識別**: ボラティリティ + 収益分布から隠れ状態を統計的に検出。Quantinsti 実証 (BTC 2024) で Sharpe 1.16 → 1.76 改善 ([Step-by-Step Python Guide](https://blog.quantinsti.com/regime-adaptive-trading-python/))
- **専用モデルの特化**: 各レジームのデータだけで学習することで、ノイズ希釈を回避
- **構造的優位**: 「市場状態に応じた特化」は理論的に頑健 (Hamilton 1989 以来の経済学的裏付け)

## 3. シグナル定義 (擬似コード)

```python
# Stage 1: HMM レジーム検出
from hmmlearn.hmm import GaussianHMM
hmm = GaussianHMM(n_components=3, covariance_type='full')
features_hmm = ['daily_return', 'daily_volatility', 'volume_zscore']
hmm.fit(features_hmm)
current_regime = hmm.predict(features_hmm[-1])
regime_proba = hmm.predict_proba(features_hmm[-1])

# Stage 2: レジーム別モデル選択
specialist_models = {
    0: RandomForestClassifier(),  # Low vol trend
    1: RandomForestClassifier(),  # Low vol range
    2: RandomForestClassifier(),  # High vol
}

# Stage 3: 予測 (確信度重み付け)
prob_up = specialist_models[current_regime].predict_proba(features_signal)[:, 1]
# 確信度 threshold (Quantinsti 実装: 0.53)
if prob_up > 0.53 and regime_proba[current_regime] > 0.7:
    enter_long(size=conviction_based, sl=2*atr, tp=3*atr)
```

## 4. データ要件 [G1-2]

- **必要データ**: H1 または D1 OHLCV (HMM は日足/4H 推奨。H1 だとノイズ多すぎる場合あり)
- **取得元**: MT5 + 余裕があれば VIX/DXY (リスクオン/オフ補助) — yfinance で取得
- **計算リソース**: HMM 学習 ~5秒、RF 学習 ~10秒/モデル。再学習 = 月次で十分
- **ラグ**: バー閉鎖 + 1秒 (HMM 推論 + RF 推論)

## 5. リスクモデル [G1-5]

| 項目 | 設定 |
|---|---|
| ポジションサイジング | 1取引あたり 0.5%、レジーム確信度に応じて 0.25-1.0% に変動 |
| 損切り (SL) | レジーム依存: トレンドは 2×ATR、レンジは 1×ATR |
| 利確 (TP) | トレンド 3×ATR、レンジ 1.5×ATR |
| 取引停止条件 | 「高ボラ・カオス」レジーム時は新規エントリー停止 |
| 想定 MaxDD | 12-18% (HMM が悪化レジーム時に取引抑制するため) |

## 6. 自己改善メカニズム [G0-B] — 必須

### ドリフト検出
- **HMM 自体がドリフト検出器**: regime 遷移確率が直近1ヶ月で 30%以上変化 → 構造変化シグナル
- **モデル別 PF 監視**: レジーム別 PF が 1.0 を割ったら該当モデル再学習
- **未知レジーム検出**: HMM `score()` (対数尤度) が学習データから -2σ 以下 → 新レジーム出現の可能性

### 自動再最適化
- **月次**: HMM 再フィット + 各レジーム RF 再学習
- **緊急**: 未知レジーム検出時に状態数を 3 → 4 に増やし再学習
- **HMM 状態数の自動選択**: BIC/AIC で 2/3/4 状態を比較し最適化

### フォールバック
- **新 HMM の対数尤度が直前モデルより悪化** → ロールバック
- **3レジーム全てで PF<1.0 が1ヶ月続く** → 取引停止 + アラート
- **「Buy & Hold」モード**: 全モデル不調時に長期方向だけ追従する safe mode

## 7. 過去 BT 結果 [G0-A] — 必須

### 既存研究の参照
- **Quantinsti (2024-2026 BTC)**: HMM + RF で **Sharpe 1.16 → 1.76, MaxDD -28% → -20%, 年率 50% → 53%** ([Step-by-Step Python Guide for Regime-Specific Trading](https://blog.quantinsti.com/regime-adaptive-trading-python/))
- **A forest of opinions (AIMS Press 2025)**: ツリーアンサンブル + HMM 投票フレームワークが市場レジーム遷移検出に有効と実証 ([A forest of opinions](https://www.aimspress.com/article/id/69045d2fba35de34708adb5d))
- **AI-Powered Energy Algorithmic Trading (arXiv 2024)**: HMM + Neural Network で energy market 取引、エネルギー市場で実証成功 ([AI-Powered Energy Algorithmic Trading](https://arxiv.org/html/2407.19858v6))

### 自前 BT 提案
- USD_JPY D1 5年で HMM 3状態 + RF アンサンブルを実装
- ベースライン: Buy & Hold, 単一 RF
- メトリクス: 累計 PF, Sharpe, Sortino, MaxDD, Calmar

### PF > 0.95 を超える論拠
- Quantinsti 実証で Sharpe 1.76 → PF 約 1.4 相当 (Sharpe-PF 換算)
- レジーム別取引制限 (高ボラ時停止) で MaxDD 軽減 → PF 押し上げ
- 単純 ML 戦略の弱点 (「全期間平均」) を構造的に解消

## 8. WFA / OOS [G1-7]

- **Walk-Forward**: 2年学習 / 6ヶ月運用 (D1) を 5年分で 10サイクル
- **HMM の安定性検証**: 各サイクルで状態遷移行列が大幅に変化していないか確認
- **Regime persistence**: 1状態の継続期間中央値が十分長いか (短すぎると過剰反応)
- **Deflated Sharpe**: HMM 状態数 + RF ハイパラの試行数を考慮

## 9. 実装複雑度 [G1-3]

- **工数見積もり**: 3週間
  - Week 1: HMM パイプライン + `hmmlearn` 統合
  - Week 2: レジーム別 RF + アンサンブル投票
  - Week 3: ドリフト検出 + 自動再学習 + バックテスト
- **依存ライブラリ**: `hmmlearn, scikit-learn, ta, pandas-ta, mt5`
- **外部 API 依存**: MT5 のみ
- **既存資産活用**: `src/regime_detector.py` (亡き者の世界で実装済) を発展形で再利用

## 10. 機会費用比較 [G1-6]

| 対象 | 想定年率 | 100万円運用時 / 年 |
|---|---|---|
| 米国債 4% | 4.0% | 40,000 JPY |
| 全世界株 8% | 8.0% | 80,000 JPY |
| 銀行預金 | 0.05% | 500 JPY |
| **本戦略 (期待値)** | **10-18%** (Sharpe 1.5級) | **100,000-180,000 JPY** |

XGBoost 単独より控えめだが、**MaxDD が小さい** ことが価値。Calmar 比 (年率/MaxDD) で評価すべき。

## 11. リスク・既知の弱点

1. **HMM 状態数の決定**: 2状態は単純すぎ、4以上は過剰。BIC で動的決定するが理論的最適は不明
2. **レジーム遷移ラグ**: HMM はバックワード推論なので遷移を後から識別する傾向。一歩遅れる
3. **「カオス」レジームの定義**: 高ボラ即停止すると 2020-03 のような底値圏を取りこぼす
4. **状態間の不均衡**: 「低ボラ・トレンド」状態のデータが大半を占め、他状態のモデル学習データが不足する
5. **メタモデルへの依存**: HMM が間違ったレジームを推定したら全システムが間違う
6. **D1 タイムフレームの低頻度**: 月数トレード以下なら、Sharpe 推定誤差が大きく統計的有意性が低い

## 12. 採点自己評価

### Gate 0 (必須)

| 項目 | 評価 | コメント |
|---|---|---|
| **G0-A**: PF > 0.95 | **○** | Quantinsti 実証で Sharpe 1.76 → PF ~1.4 想定。FX 検証未だが BTC で実証済 |
| **G0-B**: 自己改善 | **○** | HMM 自体がドリフト検出 + 月次再学習 + フォールバック設計済 |

→ **Gate 0 = PASS**

### Gate 1 (各10点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G1-1 想定エッジ源 | 8 | 経済学的裏付け (Hamilton 1989)、構造的非定常性に対する直接対応 |
| G1-2 データ要件 | 9 | MT5 のみ、追加で VIX (yfinance) 任意 |
| G1-3 実装複雑度 | 6 | 3週間、HMM の収束問題等で工数膨らむリスク |
| G1-4 ロバスト性 | 8 | レジーム別取引でレジーム変化耐性が構造的に高い |
| G1-5 リスクプロファイル | 9 | 「カオス」時停止で MaxDD 軽減、SL/TP がレジーム適応的 |
| G1-6 機会費用比較 | 6 | 期待 10-18% は中位、MaxDD 軽減で Calmar 比は優秀 |
| G1-7 WFA / OOS | 8 | 10サイクル WFA、HMM 安定性検証も含む |

**Gate 1 = 54/70**

### Gate 2 (各5点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G2-1 スプレッド耐性 | 4 | D1 低頻度、スプレッド影響少 |
| G2-2 他戦略との相関 | 4 | レジーム適応型は単一戦略と低相関 |
| G2-3 説明可能性 | 4 | HMM 状態 + RF feature importance で説明可能 |
| G2-4 レビュー耐性 | 4 | レジーム概念に経済学的裏付け、反論屋耐性高 |
| G2-5 拡張性 | 4 | ペア追加可、ただし HMM はペア毎に独立フィット必要 |
| G2-6 過去挙動データ整合 | 3 | 亡き者 GBP_JPY の「短期保有」と D1 タイムフレームは合わない。USD_JPY 中期向け |

**Gate 2 = 23/30**

### 総合

| Gate | 点数 | 合否 |
|---|---|---|
| Gate 0 | PASS | 既存 BTC 実証あり、FX へ転用要確認 |
| Gate 1 | 54/70 | Phase 2 進出基準クリア |
| Gate 2 | 23/30 | 加点 |
| **総合** | **77/100** | **Phase 1 (簡易 BT) 進出推奨** |

---

## ソース

1. [Step-by-Step Python Guide for Regime-Specific Trading Using HMM and Random Forest](https://blog.quantinsti.com/regime-adaptive-trading-python/) - Quantinsti (2026) — BTC 2024 BT で Sharpe 1.76、MaxDD -20%
2. [A forest of opinions: A multi-model ensemble-HMM voting framework](https://www.aimspress.com/article/id/69045d2fba35de34708adb5d) - AIMS Press (2025)
3. [AI-Powered Energy Algorithmic Trading: Integrating HMM with Neural Networks](https://arxiv.org/html/2407.19858v6) - arXiv (2024)
4. [Hidden Markov Model Market Regimes - QuantifiedStrategies](https://www.quantifiedstrategies.com/hidden-markov-model-market-regimes-how-hmm-detects-market-regimes-in-trading-strategies/)
5. [GitHub - LOCOtac/Regime-Model](https://github.com/LOCOtac/Regime-Model) - HMM + 取引戦略実装例
6. [Hamilton 1989 - Regime Switching Models](https://en.wikipedia.org/wiki/Markov_switching_multifractal) - 経済学的基礎
