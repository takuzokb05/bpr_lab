# プロポーザル: GBP_JPY M15 RSI Pullback (BT で OOS PF 7.38 が出るが、サンプル少+亡き者撤退矛盾を慎重評価)

## 1. 戦略仮説 (1段落)

**意図的にGate 0 FAIL リスクを表明する候補**として提出。`data/backtest_grid_GBP_JPY.csv` の M15 BTグリッドで OOS PF 7.38 (RSI 30/70, ATR 2.0)、勝率 66.7%、しかし **OOS trades = 4 件のみ**。亡き者で撤退判断した GBP_JPY を主候補にする論証が必要 (`[[feedback-deceased-world-data-inheritance]]`)。本プロポーザルは「BTで好成績だが実用性に疑問符が立つ候補」をカタログに残す目的で起草。

## 2. 想定エッジ源 [G1-1]

- **BTグリッド数字**: GBP_JPY M15 で 20 パラメータ中 18 が OOS PF > 1.0、ベスト PF 7.38、3-5 件中央値で高勝率 50-70%
- **GBP_JPY のボラ特性**: 短期ジャンプ後の反転が顕著 (Andersen-Bollerslev intraday vol patterns、JPY クロスで特に明瞭)
- **しかし**: OOS trades 3-15 件は **統計信頼性が極めて低い** → エッジが本当か偶然か区別不能

## 3. シグナル定義 (擬似コード)

```python
def signal(bar_close, history_m15):
    rsi_14 = RSI(history_m15.close, 14)
    atr_14 = ATR(history_m15, 14)
    ema50 = EMA(history_m15.close, 50)

    if rsi_14 < 30 and bar_close > ema50:
        return Signal("long", entry=bar_close,
                     sl=bar_close - atr_14*2.0,
                     tp=bar_close + atr_14*3.0)
    if rsi_14 > 70 and bar_close < ema50:
        return Signal("short", entry=bar_close,
                     sl=bar_close + atr_14*2.0,
                     tp=bar_close - atr_14*3.0)
    return None
```

## 4. データ要件 [G1-2]

- M15 OHLC (既存)
- コスト: ゼロ

## 5. リスクモデル [G1-5]

- SL: ATR×2.0、TP: ATR×3.0 (RR=1.5)
- 想定 MaxDD: BT グリッドで -5〜-10% (M15高頻度)
- **テールリスク 大**: GBP_JPY は BOE/日銀イベントで突発的ジャンプ多発、SL slippage 想定 +2pip

## 6. 自己改善メカニズム [G0-B]

### ドリフト検出
- ローリング20件 PF<1.0 で警告
- 亡き者 PF 0.87 との対比モニタ (反論屋 ULTRA 教訓の継承)

### 自動再最適化
- 月次 M15 5y BTグリッド再走

### フォールバック
- **撤退条件 (反論屋 ULTRA 推奨)**: 90日経過時 trades < 5 で即撤退 (機会喪失)
- 直近20件で累計 -3% で停止

## 7. 過去 BT 結果 [G0-A] — 必須

### Source: `data/backtest_grid_GBP_JPY.csv`

| パラメータ | full PF | OOS PF | OOS trades | full WR | OOS WR |
|---|---:|---:|---:|---:|---:|
| RSI 30/70, ATR 2.0 | **4.00** | **7.38** | **4** | 66.7% | (推定 75%) |
| RSI 30/70, ATR 3.5 | **5.71** | **5.25** | **3** | 70.0% | (推定) |
| RSI 30/70, ATR 3.0 | **3.64** | **5.24** | **3** | 63.6% | (推定) |
| RSI 32/68, ATR 3.5 | **2.92** | **5.09** | **3** | 57.1% | (推定) |
| RSI 32/68, ATR 3.0 | **2.05** | **5.07** | **3** | 50.0% | (推定) |

**警告**:
- OOS trades **3-4 件は統計的に意味なし** (信頼区間が PF 0.5〜∞)
- BT 期間が 2年なら年 1.5-2件 → 月 0.13 件 → ペーパー1年で 1-2件しか出ない
- **「BTで好成績、実取引で機会喪失」の典型パターン**

### 亡き者 GBP_JPY との対比

- 亡き者 H1 戦略 (MTFPullback): 37件、PF 0.87、勝率 35.1%、-1,239 JPY
- 本提案 M15 RSI: 4件、PF 7.38、勝率 67%
- **時間軸も戦略も別物、サンプル数桁違い** → 比較困難

### PF > 0.95 を超える論証
- BTで OOS PF 7.38 は記録上は超える
- **しかし** OOS trades 4 件は無視できない弱点
- Deflated Sharpe で deflation を考慮すると、**実質的な PF 信頼区間下限は 1.0 を割る可能性**
- → **G0-A は「BT上は PASS だが信頼性低」** で条件付き PASS

## 8. WFA / OOS [G1-7]

- 5-fold WFA で OOS 3-4 trades は **fold あたり 0.6-0.8 trades** → 検定不能
- 本提案を Phase 2 で進める場合、**10年M15 データへの拡張 (現2年)** が必須

## 9. 実装複雑度 [G1-3]

- 既存 RSI Pullback コード流用、1日
- 依存: 既存

## 10. 機会費用比較 [G1-6]

- 仮に PF 7.38 が実現すると年率 +50% 超だが、年4件の trade では絶対額が限定的
- 1取引 +200 JPY/lot 1.0 × 4 trade = 年 +800 JPY @ 100万 = **+0.08%**
- **取引数が少なすぎて機会費用に勝てない**: 銀行預金 (+0.05%) すら微妙
- ロット拡大で対応する場合、SL hit 時の絶対損失も比例拡大 → 結局意味なし

## 11. リスク・既知の弱点

1. **サンプル数不足**: OOS 3-4 件は統計的に無意味、Phase 1 で 10y データ拡張必須
2. **亡き者撤退との矛盾**: 2026-05-07 GBP_JPY 撤退判断 (BT PF 0.80, 本番 PF 0.87) と本提案 (BT PF 7.38) が同通貨で対立 → timeframe (H1 vs M15) と戦略 (MTFPullback vs RSI Pullback) の差で説明可能だが、サンプル少のため証拠力弱い
3. **過剰最適化リスク**: 20 パラメータ × 5 fold = 100 試行で偽陽性確率 5% → 高 PF が偽陽性の可能性
4. **取引頻度の絶対的不足**: 年 4 件では実用性なし
5. **反論屋 ULTRA バグ E 警告**: 「同じ過去5年 CSV データを別角度で見ただけ」の罠 → 本提案も BT のみで独立検証なし

## 撤退条件 (事前明記)

1. ペーパー90日で trades < 2 (頻度致命)
2. 直近5件で PF < 1.0
3. 累計 PnL < -1%

## 12. 採点自己評価

| Gate | 項目 | 点数 | コメント |
|---|---|---|---|
| **G0-A** | PF > 0.95 | ⚠️ **条件付き PASS** | BT で PF 7.38 だが OOS trades 4 件は信頼性低 |
| **G0-B** | 自己改善 | ⚠️ **条件付き PASS** | 自己改善あるが、頻度低でドリフト検出が機能しにくい |
| G1-1 | エッジ源 | **5/10** | BT 数字のみ、構造的論拠薄い |
| G1-2 | データ要件 | **8/10** | 既存だが2年では不足、10y拡張必須 |
| G1-3 | 実装複雑度 | **9/10** | 1日 |
| G1-4 | ロバスト性 | **3/10** | OOS 3-4 件は脆弱 |
| G1-5 | リスク | **5/10** | 個別はOKだが頻度低でDD評価困難 |
| G1-6 | 機会費用 | **2/10** | 年4件では絶対額不足、銀行預金未満 |
| G1-7 | WFA/OOS | **3/10** | OOS trades が fold あたり<1 |
| **G1合計** | | **35/70** | **進出基準 50点 を大幅未達** |
| G2-1 | コスト耐性 | **3/5** | 取引少でスプレッド負担少 |
| G2-2 | 相関 | **3/5** | M15なので他H1案と差別化 |
| G2-3 | 説明可能性 | **5/5** | RSI/ATR は完全可視 |
| G2-4 | レビュー耐性 | **1/5** | 反論屋に「サンプル少」と即撃沈確実 |
| G2-5 | 拡張性 | **3/5** | 他 JPY クロスへ展開可能 |
| G2-6 | 亡き者整合 | **1/5** | 反論屋 ULTRA バグ B (GBP_JPY 撤退矛盾) を再演リスク |
| **G2合計** | | **16/30** | |
| **総合** | | **51/100** | **Phase 2 進出 NG (G1<50 で却下)** |

## 13. 亡き者整合チェック

**重大な懸念**: 反論屋ULTRA バグ B「撤退済 GBP_JPY を3日後に再採用 (自己一貫性崩壊)」を再演するリスク

- 亡き者撤退根拠: BT PF 0.80, 本番 PF 0.87
- 本提案根拠: BT M15 PF 7.38 (但し OOS trades 4 件)
- **「BT 数字だけが好成績」という同じ罠**にハマっている可能性が高い
- `[[feedback-deceased-world-data-inheritance]]` ルールに従い、亡き者の 37 件 PF 0.87 を本提案の採用判定式に明示組み込み → **OOS trades 4 件 < 亡き者 37 件、サンプル比較で亡き者の方が信頼性高**
- → **採用判断の reversal 論拠は不十分**

## 14. 結論

**本プロポーザルは Gate 0-A が条件付き PASS だが、G1 合計 35/70 (進出基準 50点未達) で却下推奨**。

カタログには残すが、Phase 2 進出は推奨しない。代わりに:
- (a) 10y M15 データへ拡張して再評価 (Phase 1.5 として実施可)
- (b) GBP_JPY を主候補にせず、EUR_USD H1 RSI Pullback 主、GBP_JPY M15 を「補助分散源」として最小サイズで並走 (Phase 4 採用後)

## 15. ソース引用

- `data/backtest_grid_GBP_JPY.csv` (BT グリッドで PF 7.38)
- `data/fx_trading_prod_snapshot.db` (亡き者 GBP_JPY 37件 PF 0.87)
- `docs/analysis/CONTRARIAN_KAREN.md` (GBP_JPY 撤退判断の根拠)
- `docs/analysis/CONTRARIAN_ULTRA.md` バグ B (GBP_JPY 撤退矛盾)
- `memory/feedback_deceased_world_data_inheritance.md` (亡き者数字の継承ルール)
- `memory/project_fx_strategy_pivot_2026_05.md` (2026-05-07 撤退決定)
