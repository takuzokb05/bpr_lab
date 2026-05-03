# Phase 1 統合: 戦略検証の結論と Phase 2 優先度

実施日: 2026-05-03
対象: Phase 1 P1-1 / P1-2 / P1-3 / P1-4
入力ドキュメント:
- `docs/strategy_validation_phase1.md` (P1-1+3)
- `docs/public_strategy_benchmark.md` (P1-4)
- `docs/live_vs_backtest_diff.md` (P1-2)

## 1. 結論サマリ

| 問い | 回答 | 根拠 |
|---|---|---|
| RsiPullback は壊れているか？ | **否** | 戦略デフォルト 35/65 では USD/JPY PF 1.97 / EUR/USD PF 1.60。実戦勝率は EUR_USD 38.5% vs BT 40%、GBP_JPY 35.1% vs BT 35.3% と整合 |
| 公開戦略へ乗り換えるべきか？ | **否** | freqtrade HLHB は 3ペア全敗（Sharpe -2〜-9）、Holy Grail も MaxDD -50%超。RsiPullback が全メトリクスで上回る |
| なら本番が低勝率なのは何故？ | **設定の不一致 + 実装の欠陥** | (1) pair_config が検証ベースライン (35/65) と異なる 30/70・25/75 を本番に投入。USD/JPY 30/70 は PF 0.46 で**エッジ消失**。(2) 同ペア複数ポジ抑止が欠如し 2倍トレード化。(3) GBP/JPY スリッページが BT 想定の 3-4倍 |

**最大の発見**: 「USD_JPY が 1勝6敗だから戦略がダメ」は**因果が逆**。
本番投入された pair_config の RSI 30/70 が、検証された 35/65 とは別物の「未検証パラメータ」だった。

## 2. P1 各タスクの主要数値

### P1-1+3 戦略検証（strategy-validator）

| ペア | 戦略デフォルト (RSI 35/65) | 本番 pair_config | 本番条件相当 |
|---|---|---|---|
| USD/JPY | PF 1.97, SR 2.89, OOS PF 1.94 | RSI **30/70**, ADX 20 | **PF 0.46** |
| EUR/USD | PF 1.60, SR 2.54, OOS PF 1.11 | RSI **30/70**, ADX 25 | PF 1.77 (Trades 12) |
| GBP/JPY | PF 1.19, OOS PF 1.34 | RSI **25/75**, ADX 25 | グリッド外 |

- 過学習診断: USD/JPY は IS↔OOS で隣接セル維持（過学習小）。EUR/USD は IS最適 → OOS PF 0.44 で崩壊（過学習）。GBP/JPY は WFE 解釈不能。
- ロバスト領域: USD/JPY 35/65×ATR2.0、EUR/USD 38/62×ATR全域。GBP/JPY ロバスト領域なし。

### P1-4 公開実装ベンチマーク（public-strategy-porter）

3ペア × 全メトリクス（PF / Sharpe / MaxDD / Return）で RsiPullback が freqtrade HLHB / Holy Grail を上回る。

| Strategy | PF >1 のペア数 | Sharpe>0 のペア数 | 平均 Return% | 平均 MaxDD% |
|---|:---:|:---:|---:|---:|
| **RsiPullback** | **3/3** | **3/3** | **+34.7%** | **-23.7%** |
| Holy Grail | 1/3 | 1/3 | -12.5% | -50.4% |
| freqtrade HLHB | 0/3 | 0/3 | -34.7% | -55.3% |

→ **公開戦略を新規移植する必要はなし**。

### P1-2 実戦 vs バックテスト乖離（team-lead）

| pair | live n | live WR | live PF | BT n | BT WR | BT PF | filter pass | slip avg |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| USD_JPY | 7 | 14.3% | 0.48 | 3 | 66.7% | 3.36 | 2.33x | 0.94 pips |
| EUR_USD | 13 | 38.5% | 2.37 | 10 | 40.0% | 1.24 | 1.30x | 1.96 pips |
| GBP_JPY | 37 | 35.1% | 0.87 | 17 | 35.3% | 0.53 | 2.18x | 3.51 pips |

- 同時保有: USD_JPY 2/7、EUR_USD 5/13、**GBP_JPY 21/37 (うち同方向 16)**
- 勝率は EUR/EUR_USD/GBP_JPY とも BT と整合 → 戦略ロジックは正常
- 取引数の 2倍化と GBP_JPY のスリッページ過大が PF を押し下げている

## 3. Phase 2 優先度（根拠付き再整理）

`項目` の前の P0/P1/P2 はビジネス影響度。`期待効果` は P1-1〜P1-4 の数値から逆算。

### P0 (今週中、システム健全性が前提条件)

#### P2-A: 同ペア concurrent-position ガード追加
- **根拠**: GBP_JPY 21/37 重複 + 同方向 16/37。BT は exclusive_orders=True 前提
- **実装**: `trading_loop._evaluate_signal` で `position_manager.has_open_position(instrument)` チェック
- **期待効果**: GBP_JPY 取引数 37→17（BT 同等）、同方向ナンピン消失で平均PL改善
- **リスク**: 既存ロジックに後付けのガード。テスト追加要

#### P2-B: pair_config パラメータの再校正
- **根拠**: USD_JPY 本番 RSI 30/70 は検証外。35/65 で PF 1.97 だが 30/70 で PF 0.46
- **実装案 A**: pair_config を **検証で勝った 35/65 に戻す**（保守的）
- **実装案 B**: 30/70 でも勝てるよう ADX 閾値やトレンドフィルタを追加検証してから残す
- **判断**: A を採用し、後で B の検証を追加するのが最速で安全
- **期待効果**: USD_JPY バックテスト水準のエッジ復活

### P1 (2 週間以内、信頼性向上)

#### P2-C: 1年 H1 データで Phase 1 再検証
- **根拠**: 60日 M15 では OOS Trades 9〜16 で統計的検出力不足
- **実装**: 同スクリプトの `interval="1h"`、`period="1y"` で再ラン。OOS Trades 50+ 確保
- **期待効果**: 「pair_config の RSI 35/65 が頑健」を統計的に確証

#### P2-D: GBP_JPY スリッページ実態の本番ログ調査
- **根拠**: avg 3.5 pips, p95 21 pips。BT 想定 1pip と 3〜20倍乖離
- **実装**: 本番 trading.log から「シグナル検出時刻 → 発注時刻 → 約定時刻」を抽出
- **期待効果**: スプレッド要因か発注遅延要因かを切り分け、対策が決まる

#### P2-E: AIAdvisor の通過/拒否ログ集計
- **根拠**: P1-2 の filter pass ratio は「発注後」のみ。AIAdvisor が REJECT したシグナルは未測定
- **実装**: 本番 trading.log から `AIAdvisor decision` を抽出し、CONFIRM/CONTRADICT/NEUTRAL/REJECT 比率と取引結果を集計
- **期待効果**: AIAdvisor が役立っているか有害かを定量判定

### P2 (来月、戦略改善)

#### P2-F: 真の MTF（D1 トレンド × M15 エントリー）への拡張検討
- **根拠**: rsi_pullback.py docstring に「真の MTF は将来拡張」と明記。MA200×M15 = 50時間は中途半端
- **実装**: H1 ベース MA200 を追加トレンド判定に組み込む
- **期待効果**: トレンドフィルタの精度向上、含み益の伸長

#### P2-G: GBP_JPY の戦略変更 or 撤退判断
- **根拠**: ロバスト領域なし。実戦 PF 0.87 で損益分岐
- **判断条件**: P2-A 適用後の 2 週間で取引数半減・PF が 1.0 を超えるかを観察
- **不可なら**: 撤退（pair_config から GBP_JPY を外す）または別戦略試験

## 4. Phase 2 開始の決定事項（提案）

| 項目 | 着手 | 完了目標 | 担当 |
|---|---|---|---|
| P2-A 同ペア concurrent ガード | 即時 | 5/4 | team-lead 直接 |
| P2-B pair_config を 35/65 に戻す | P2-A 後 | 5/4 | team-lead 直接 |
| P2-C 1年 H1 再検証 | 並列 | 5/7 | strategy-validator 再起動 |
| P2-D ログ解析（GBP_JPY スリッページ） | 並列 | 5/7 | log-investigator agent |
| P2-E AIAdvisor 通過率集計 | 並列 | 5/7 | log-investigator agent |

## 5. orphan ポジション処置

別管理（`scripts/_close_orphan_8953385.py` で月曜オープン後即時クローズ予定）。
本シンセシスとは独立。

## 6. リスク・前提

- **本検証は 60日 M15 データに限定**。長期再現性は P2-C 完了まで未確証
- **本番投入の `pair_config` 値は誰がいつ決めたか不明**（Git ログ要確認）。
  実は意図的なチューニング結果かもしれない → 変更前に履歴を確認
- **P1-2 の BT 比較は yfinance 価格**。MT5 配信との乖離は数 pip 単位。スリッページ絶対値は参考程度
