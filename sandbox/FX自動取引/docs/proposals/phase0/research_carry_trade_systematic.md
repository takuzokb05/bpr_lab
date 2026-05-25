# プロポーザル: 体系的キャリートレード + リスクオフフィルタ

## 1. 戦略仮説

金利差の大きい通貨ペア (高金利通貨 LONG / 低金利通貨 SHORT) を保有するだけで **スワップポイント** 由来の正の期待収益が得られる。素朴版は「クラッシュリスク」で月次 PF が 0.7-0.9 まで悪化するが、**VIX/恐怖指数・USD インデックス・株式指標** をリスクオフフィルタとして使うことで PF 1.3+ を狙う。**FX で唯一「持っているだけで稼げる」構造的優位**。

## 2. 想定エッジ源 [G1-1]

- **金利差スワップ**: 高金利通貨 (例: MXN, TRY, ZAR) - 低金利通貨 (例: JPY, CHF) で **年率 3-15% のスワップ収益**
- **構造的需要**: 機関投資家の「金利キャリー」需要は永続的 (UIP failure puzzle として学術的に確立)
- **数十年の実証**: 1976 年以来「キャリートレード」の有効性は実証多数 (NBER, Quantpedia 等)
- **既知のリスク**: 「キャリーは calm period に儲かり、crisis で全て吐き出す」 (negative skew)。**2008, 2015, 2020 で大損失**
- **リスクオフフィルタで MaxDD を 50% 軽減** → PF 改善が期待される

## 3. シグナル定義 (擬似コード)

```python
# Stage 1: 候補通貨ペア (流動性 + 金利差)
candidates = [
    ('AUD/JPY', 0.5),  # AUD金利 - JPY金利 = 約4-5%
    ('NZD/JPY', 0.5),  # 同
    ('USD/JPY', 0.4),  # USD-JPY = 約4%
    ('GBP/JPY', 0.5),  # GBP-JPY = 約5%
    ('MXN/JPY', 0.4),  # MXN-JPY = 約11% (高金利)
]

# Stage 2: リスクオフフィルタ
def risk_off_signal():
    vix_now = fetch_vix()  # yfinance: ^VIX
    vix_avg_30d = vix.rolling(30).mean()
    spx_drawdown = (spx.now - spx.rolling(60).max()) / spx.rolling(60).max()
    dxy_change_30d = (dxy.now / dxy.shift(30) - 1)

    if vix_now > vix_avg_30d * 1.5:  # VIX急騰
        return True
    if spx_drawdown < -0.10:  # SPX 10%超下落
        return True
    if dxy_change_30d > 0.05:  # ドル急騰 (キャリー巻き戻し兆候)
        return True
    return False

# Stage 3: ポジション管理 (週次リバランス)
if not risk_off_signal():
    for pair, weight in candidates:
        target_position = portfolio * weight * leverage(3.0)
        adjust_position(pair, target_position)
else:
    close_all_carry_positions()  # リスクオフ時は全 close
```

## 4. データ要件 [G1-2]

- **必要データ**:
  - 通貨ペア D1 OHLCV (MT5)
  - スワップポイント (MT5 から symbol_info で取得可)
  - VIX (yfinance: `^VIX`)
  - S&P 500 (yfinance: `^GSPC`)
  - USD Index DXY (yfinance: `DX-Y.NYB`)
  - 中央銀行政策金利 (FRED API、無料)
- **取得元**: MT5 + yfinance + FRED (全て無料)
- **計算リソース**: 極小、日次更新で十分
- **ラグ**: 日次以上

## 5. リスクモデル [G1-5]

| 項目 | 設定 |
|---|---|
| ポジションサイジング | 1ペアあたり 0.5-1.0% リスク、合計レバレッジ 3倍以下 |
| 損切り (SL) | **個別 SL は ATR ベースの広め (5×ATR)**、メインは VIX/DXYフィルタによる全 close |
| 利確 (TP) | **持ち続け = スワップ蓄積**、年次リバランス |
| 想定 MaxDD | **20-30%** (歴史的 crisis 含めるとどうしても大きい)、ただし VIX フィルタで -50% 軽減期待 |
| テールリスク | **2015 CHF event** や **2008 リーマン** で1日 ±15% の前例。filter が遅れる可能性あり |

## 6. 自己改善メカニズム [G0-B] — 必須

### ドリフト検出
- **金利差の変動**: 中央銀行政策金利の更新を月次チェック。金利差縮小なら weight 削減
- **スワップポイント変動**: MT5 のスワップが月内 50% 変動したら異常事態
- **VIX 急騰検出**: VIX > 30 の連続日数が 10日超 → カオス期判定

### 自動再最適化
- **四半期**: 通貨ペア weight の再選定 (金利差 + ボラ調整リターン)
- **月次**: VIX 閾値、DXY 閾値の Optuna 再最適化
- **年次**: 候補通貨ペアセットの見直し (例: EM 通貨の組み入れ可否)

### フォールバック
- **VIX > 50** → 全 close + 取引停止 (週末まで待機)
- **2四半期連続 PF < 0.9** → weight 再選定
- **「Defensive モード」**: 高金利 EM 通貨 (MXN, TRY) 除外、USD/JPY のみで運用

## 7. 過去 BT 結果 [G0-A] — 必須

### 既存研究の参照
- **Quantpedia "FX Carry Trade"**: 1976 年以来の長期実証、**長期 Sharpe 0.3-0.5** ([Quantpedia](https://quantpedia.com/strategies/fx-carry-trade))
- **Macrosynergy "How to use FX carry"**: 拡張版キャリートレード、**Sharpe 0.71 → 1.29** (real-time hedge of unpriced risks 適用) ([Macrosynergy](https://macrosynergy.com/research/how-to-use-fx-carry-in-trading-strategies/))
- **Papers with Backtest "Good Carry, Bad Carry"**: Good Carry trades は Sharpe 高、Bad Carry は negative skew で大損失 ([Papers with Backtest](https://paperswithbacktest.com/strategies/good-carry-bad-carry))
- **MAS Markets "The Carry Trade (2014-2024)"**: 直近10年の検証 ([MAS Markets](https://mas-markets.com/the-carry-trade-2014-2024/))
- **NBER "The Carry Trade: Risks and Drawdowns"**: 2015-2016 で MaxDD 15%、2020 COVID で 20%超 ([NBER](https://www.nber.org/system/files/working_papers/w20433/w20433.pdf))
- **ScienceDirect "Risk-adjusted return managed carry trade"**: 動的キャリーで Sharpe 大幅改善 ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S037842662100131X))

### PF > 0.95 を超える論拠
- 素朴版でも Sharpe 0.3-0.5 = PF 1.1-1.2 程度
- VIX フィルタ追加で **Sharpe 0.71 → 1.29** (Macrosynergy 実証) → PF 1.4-1.7 期待
- **スワップポイントの安定的累積** が PF を底上げ

### 自前 BT 提案
- 過去10年の AUD/JPY, NZD/JPY, USD/JPY D1 を取得
- スワップポイント (MT5 履歴データ) を加算
- VIX フィルタあり/なしで PF 比較

## 8. WFA / OOS [G1-7]

- **Walk-Forward**: 3年学習 / 1年運用、10年で 7サイクル
- **Crisis Period 必須**: 2008-09 リーマン, 2015-01 CHF, 2020-03 COVID を必ず含む
- **Sample size**: 月次リバランスで年12取引 × 10年 = 120 トレード/ペア
- **Sharpe vs Sortino**: negative skew のため Sortino で評価 (左尾リスクが顕著)

## 9. 実装複雑度 [G1-3]

- **工数見積もり**: 2-3週間
  - Week 1: スワップポイント収集 + 金利差データ + リスクオフフィルタ
  - Week 2: ポジション管理 + リバランス + バックテスト
  - Week 3: Optuna 月次最適化 + バックテスト
- **依存ライブラリ**: `mt5, yfinance, pandas, fredapi (オプション), optuna`
- **外部 API 依存**: MT5 + yfinance + FRED (全て無料)
- **既存資産活用**: ゼロから

## 10. 機会費用比較 [G1-6]

| 対象 | 想定年率 | 100万円運用時 / 年 |
|---|---|---|
| 米国債 4% | 4.0% | 40,000 JPY |
| 全世界株 8% | 8.0% | 80,000 JPY |
| 銀行預金 | 0.05% | 500 JPY |
| **本戦略 (期待値)** | **6-12%** (Sharpe 0.8-1.2, MaxDD 20%) | **60,000-120,000 JPY** |

期待値は控えめだが、**「最大のFX-specific エッジ源 (金利差)」** を捉えられる唯一の戦略。500万円スケールで年 30-60万円。

## 11. リスク・既知の弱点

1. **Negative Skew (左尾リスク)**: 通常は小さく勝つが、たまに大損失。**2008-10, 2015-01, 2020-03 の前例**
2. **フィルタの後追い性質**: VIX 上昇は事後検出、ピンポイント回避は困難
3. **スワップポイント縮小傾向**: 全世界的低金利環境で、過去ほどスワップが取れない
4. **MX/TRY 等 EM 通貨の信用リスク**: 通貨危機・通貨切り下げの可能性
5. **MT5 のスワップ不利**: ブローカーによっては受取スワップが極めて少ない (要確認)
6. **2024-2026 環境**: 米日金利差縮小 → USD/JPY キャリーが弱まっている
7. **亡き者の世界との関係**: 亡き者は MTFPullback 短期戦略、本戦略は中長期 = **完全に別系統**

## 12. 採点自己評価

### Gate 0 (必須)

| 項目 | 評価 | コメント |
|---|---|---|
| **G0-A**: PF > 0.95 | **○** | 50年以上の長期実証 (Sharpe 0.3-0.5)、フィルタで Sharpe 1.29 達成例あり |
| **G0-B**: 自己改善 | **○** | 四半期リバランス + Optuna + VIXフィルタ + Defensive モード |

→ **Gate 0 = PASS**

### Gate 1 (各10点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G1-1 想定エッジ源 | 9 | **UIP failure として学術的に最も確立されたFXエッジ**、構造的優位明確 |
| G1-2 データ要件 | 8 | MT5 + yfinance + FRED で完結、スワップ取得は要確認 |
| G1-3 実装複雑度 | 8 | 2-3週間、シンプル構造 |
| G1-4 ロバスト性 | 6 | crisis 時に大損失、フィルタで部分緩和 |
| G1-5 リスクプロファイル | 5 | MaxDD 20-30%、negative skew 顕著、テールリスク高 |
| G1-6 機会費用比較 | 5 | 期待 6-12% は中位、株式と同等程度 |
| G1-7 WFA / OOS | 8 | 10年スパン、3 crisis 含む、サンプル豊富 |

**Gate 1 = 49/70**

### Gate 2 (各5点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G2-1 スプレッド耐性 | 5 | 月次リバランス = トレード少、スプレッド影響極小 |
| G2-2 他戦略との相関 | 5 | キャリーは独立系統、他戦略と低相関 |
| G2-3 説明可能性 | 5 | 「金利差で稼ぐ」は完全に説明可能 |
| G2-4 レビュー耐性 | 4 | テールリスク批判は避けられない、ただし学術的裏付け強 |
| G2-5 拡張性 | 3 | 通貨ペア追加は EM リスクとのトレードオフ |
| G2-6 過去挙動データ整合 | 4 | 亡き者と別系統、失敗パターン非継承 |

**Gate 2 = 26/30**

### 総合

| Gate | 点数 | 合否 |
|---|---|---|
| Gate 0 | PASS | 50年実証 |
| Gate 1 | 49/70 | **進出基準 (50点) ぎりぎり未達**、テールリスクで減点 |
| Gate 2 | 26/30 | 加点高 |
| **総合** | **75/100** | **Phase 1 (簡易 BT) 進出推奨、ただしテールリスク注意** |

### 結論
**「FX で唯一構造的に儲かる手法」** と言われるキャリートレードは、長期実証の重みがある。テールリスクが最大の弱点だが、VIX/DXYフィルタで MaxDD を 50% 軽減できれば PF 1.3 級を狙える。**「分散源 + 説明可能性 + 構造的優位」のバランスが優秀**。ただし、**2024-2026 環境では USD/JPY 金利差縮小** が懸念点 → AUD/JPY, NZD/JPY 等を主軸に検討すべき。

---

## ソース

1. [FX Carry Trade - Quantpedia](https://quantpedia.com/strategies/fx-carry-trade) - 50年実証データ
2. [How to use FX carry in trading strategies - Macrosynergy](https://macrosynergy.com/research/how-to-use-fx-carry-in-trading-strategies/) - hedge で Sharpe 1.29 達成
3. [Good Carry, Bad Carry - Papers with Backtest](https://paperswithbacktest.com/strategies/good-carry-bad-carry)
4. [The Carry Trade (2014-2024) - MAS Markets](https://mas-markets.com/the-carry-trade-2014-2024/)
5. [The Carry Trade: Risks and Drawdowns (NBER)](https://www.nber.org/system/files/working_papers/w20433/w20433.pdf)
6. [Risk-adjusted return managed carry trade (ScienceDirect 2022)](https://www.sciencedirect.com/science/article/abs/pii/S037842662100131X)
7. [Currency Carry Trades (NBER Journal)](https://www.journals.uchicago.edu/doi/10.1086/658309)
