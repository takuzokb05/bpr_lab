# Phase 2 BT 計画書

**作成日**: 2026-05-26
**根拠**: `docs/proposals/REVIEW_SUMMARY.md` (6評価委員レビュー集計、案B採用)
**対象**: 5候補の精査 BT (Walk-Forward + Deflated Sharpe + Black Swan)
**ゲート**: PF ≥ 1.3、Sharpe ≥ 0.8、機会費用 (米国債 4%) 超過、6評価委員 再採点で 4/6 以上 PASS

---

## Phase 2 進出 5候補

| # | 候補 | 担当ファイル | 戦略タイプ |
|---|---|---|---|
| 1 | memory_eur_usd_h1_rsi_pullback | `docs/proposals/phase0/memory_eur_usd_h1_rsi_pullback.md` | 平均回帰 (RSI Pullback) |
| 2 | memory_usd_jpy_m15_rsi_pullback | `docs/proposals/phase0/memory_usd_jpy_m15_rsi_pullback.md` | 平均回帰 (RSI, M15) |
| 12 | research_cointegration_pairs | `docs/proposals/phase0/research_cointegration_pairs.md` | 統計的裁定 |
| 14 | research_london_breakout_adaptive | `docs/proposals/phase0/research_london_breakout_adaptive.md` | ブレイクアウト |
| 15 | research_meta_labeling_ensemble | `docs/proposals/phase0/research_meta_labeling_ensemble.md` | ML (Lopez de Prado) |

---

## Phase 2 BT 必須要件 (5候補共通)

### A. BT 期間・サンプル要件

| 項目 | 要件 |
|---|---|
| **過去期間** | 最低 5年 (2021-2026)。データ不足なら期間延長 or 別ペア追加 |
| **OOS (Out-of-Sample) trades 数** | **≥30 件 強制** (達成しなければゲート FAIL) |
| **In-Sample / OOS 比率** | 70/30 を基準 (期間ベース) |
| **Walk-Forward** | 6-12 ヶ月 windows、step 1 ヶ月、最低 6 windows |
| **複数ペア検証** | 単一通貨依存リスク回避のため、可能なら主ペア + 関連ペア 2-3 |

### B. リスク管理要件 (CLAUDE.md 安全性原則準拠)

| 項目 | 要件 |
|---|---|
| **日次最大損失上限** | -1.5% で警告、-3% で半量化、-5% で停止 |
| **月間最大損失上限** | -10% で月停止 |
| **1取引最大損失** | 元本の 1% 以下 (デフォルト) |
| **キルスイッチ** | VIX > 30 / 1日 ±3σ / スプレッド 3倍拡大 |
| **約定不能時** | MT5 接続断 / 週末ギャップ時の挙動明示 |

### C. コスト要件

| 項目 | 要件 |
|---|---|
| **スプレッド** | ペア別実測値 (EUR_USD 1.0pip / USD_JPY 1.0pip / GBP_JPY 1.5pip 等) |
| **スリッページ** | エントリー +1pip、決済 +1pip (保守的) |
| **コミッション** | 外為ファイネスト MT5 仕様 (基本ゼロ、要確認) |
| **スワップ** | 長期保有候補 (#12 cointegration) は必須計算 |

### D. 統計的検定要件

| 項目 | 要件 |
|---|---|
| **PF** | 過去5年累計、スプレッド込み |
| **Sharpe** | 年率換算 |
| **Sortino** | Downside risk 評価 |
| **Deflated Sharpe Ratio** | 多重検定補正、Bailey & Lopez de Prado |
| **MaxDD** | 実 BT 期間中の最大 / 月別分布 |
| **勝率** | 純粋勝率、Risk-Reward Ratio とセット |
| **連敗最長** | キルスイッチ設計の根拠 |
| **パラメータ感度** | ±20% 変動で PF が 0.8x 以下に落ちないか |

### E. Black Swan ストレステスト (必須)

| 事象 | 期間 | チェック内容 |
|---|---|---|
| **2015 SNB ショック** | 2015-01-15 | EUR/CHF 急騰、関連ペアの挙動 |
| **2016 Brexit** | 2016-06-23〜24 | GBP 急落 |
| **2020 COVID 暴落** | 2020-03-09〜18 | 全通貨ボラ爆発 |
| **2024 円介入** | 2024-07-11、08-05 | USD/JPY 急落 |
| **2024-08 円キャリー巻き戻し** | 2024-08-02〜05 | クロス円大幅 |

各事象で:
- 戦略が**自動停止**したか (キルスイッチ動作確認)
- 損失額が日次/月次上限を超えなかったか
- 約定不能 / スプレッド拡大時の挙動

### F. 自己改善メカニズム動作確認 (G0-B 実証)

| 項目 | 要件 |
|---|---|
| **ドリフト検出** | 過去5年中のドリフト発生回数、検出時刻 |
| **再学習トリガ** | 月次 / 直近100trades PF<1.0 / 等の作動回数 |
| **フォールバック** | 改善失敗時、直前パラメータへ戻ったか |
| **撤退条件** | 90日 trades<5 / PF<1.0 / 累計-3,000 JPY のシミュレーション |

### G. レポート要件 (6評価委員 再採点用)

各候補で以下を統一フォーマットで出力 (`docs/proposals/phase2/<候補>_BT_REPORT.md`):

```markdown
# Phase 2 BT レポート: <候補名>

## 1. 戦略概要 (Phase 0 からの確定)
- 戦略仕様 (擬似コードレベル)
- ペア / TF / パラメータ (固定 vs 動的)

## 2. BT 結果 (5年、OOS≥30)
- 累計 PF / Sharpe / Sortino / MaxDD
- スプレッド込み数字 / 込まない数字 (比較)
- 取引件数 (Total / IS / OOS)
- Deflated Sharpe Ratio

## 3. Walk-Forward Analysis
- Windows ごとの PF / Sharpe
- 安定性評価

## 4. パラメータ感度
- ±20% 変動時の PF / Sharpe

## 5. Black Swan ストレステスト
- 5事象 各検証結果
- キルスイッチ動作

## 6. リスク管理シミュレーション
- 日次/月次損失上限の作動回数
- 想定 vs 実測 MaxDD

## 7. 自己改善メカニズム動作
- ドリフト検出 / 再学習 / フォールバック / 撤退

## 8. 機会費用比較
- 100万円口座 × 5年
- 預金 / 米国債 / 全世界株 との対比

## 9. ゲート判定
- PF ≥ 1.3 : PASS / FAIL
- Sharpe ≥ 0.8 : PASS / FAIL
- 機会費用超過 : PASS / FAIL
- OOS ≥ 30 : PASS / FAIL
- Black Swan 耐性 : PASS / FAIL
- 自己改善実証 : PASS / FAIL
- 総合: Phase 3 進出推奨 / 棚上げ / 廃案
```

### H. スクリプト要件

各候補で `scripts/_phase2_bt_<候補名>.py` を作成:
- `scripts/_contrarian_bt.py` / `_donchian_bt.py` のロジックを再利用可能
- 結果 CSV を `data/_phase2_bt_<候補名>_{trades,monthly,stress}.csv` に保存

---

## 並列実行体制

### 5候補並列 BT エージェント (analyst × 5)

| エージェント | 担当候補 | 想定工数 |
|---|---|---|
| phase2-bt-1 | #1 EUR_USD H1 RSI Pullback | 90-120 分 |
| phase2-bt-2 | #2 USD_JPY M15 RSI Pullback | 90-120 分 |
| phase2-bt-12 | #12 Cointegration Pairs | 120 分 (ペア選定含む) |
| phase2-bt-14 | #14 London Breakout Adaptive | 90 分 (実装最速) |
| phase2-bt-15 | #15 Meta-Labeling Ensemble | 120 分 (ML 学習) |

### 完了後

1. 5 BT レポート完了 → 6評価委員で **再採点** (各 60-90分)
2. 6視点 Phase 2 通過判定 → 1-2 候補 確定
3. Phase 3 SPEC v3 起草

---

## ゲート判定基準 (Phase 3 進出)

### 必須条件 (絶対)
- PF ≥ **1.3** (スプレッド込み)
- Sharpe ≥ **0.8**
- OOS trades ≥ **30**
- 機会費用 (米国債 4%) を **超過**
- 日次/月次損失上限 **実装済 + 作動確認**
- Black Swan 5事象で **キルスイッチ正常作動**
- 自己改善メカニズム **実証** (シミュレーションで作動確認)

### 望ましい (加点)
- Sortino ≥ 1.0
- Deflated Sharpe ≥ 0.5
- MaxDD ≤ 15%
- パラメータ感度 良好 (±20% で PF 0.8x 以上)
- Walk-Forward 6 windows 中 4以上 PASS

### 即時棚上げ (FAIL)
- 上記必須条件のいずれか1つでも FAIL
- 起草者自身が「BT 結果が予想より悪い」と認めた場合

---

## 採点フレーム改訂 (Phase 3 通過後に実施、Phase 2 では Goodhart 化を抑制)

メタ視点で指摘された 7項目はこのフェーズで対処せず、Phase 3 SPEC v3 起草時に **フレーム改訂 PR** として実施:

1. G0-A 自前BT強制
2. OOS trades ≥ 30 強制
3. Phase レイヤー欄
4. 反論屋応答セクション
5. G2-7 採点フレーム批判
6. 依存戦略明示
7. 自己採点高得点警告

ただし Phase 2 BT レポートは上記要件で **自動的に Goodhart 化を抑制** する設計になっている (BT 数字を強制、字面達成を排除)。

---

## 関連
- 評価集計: `docs/proposals/REVIEW_SUMMARY.md`
- 6評価委員定義: `.claude/agents/proposal-reviewer-*.md`
- 採点フレーム: `docs/PROPOSAL_TEMPLATE.md`
- プロセス文書: `docs/PROPOSAL_REVIEW_PROCESS.md`
- 撤退記録: `docs/RETREAT_2026-05-26.md`
