# FX自動取引 — 残タスク一覧

最終更新: 2026-05-03（PR #15〜#21 追加時点）

## 完了済み（本日）

- ✅ PR #10: 同ペア concurrent ポジションのブローカー直接照会ガード
- ✅ PR #11: pair_config を全ペア RSI 35/65 に統一
- ✅ PR #12: Phase 1 検証レポート + 再現スクリプト
- ✅ PR #13: EUR/USD のみ RSI 30/70 に再調整（H1 730日根拠）
- ✅ PR #14: sync_with_broker の ai_decision NULL 上書き保護
- ✅ VPS デプロイ・bot 再起動（PID 5844, 20:43:25 JST）
- ✅ PR #15: BT spread デフォルトをペア別実測値 (1.5〜2.5pip) に補正
- ✅ PR #16: 非JPY pip_value フォールバックを動的化（CRITICAL ロット過大計算リスク修正）
- ✅ PR #17: MT5 履歴 export + Phase 3 (M15 5y) 検証ランナー
- ✅ PR #18: P2 監査+設計ドキュメント（system_logic_audit / market_analysis_audit / usdjpy_strategy_refresh_plan）
- 🟡 PR #19 (open): MTFPullback/BollingerReversal の pair_config 配線漏れ修正 (CRITICAL)
- 🟡 PR #20 (open): 監査A6+B7+B8 — KILL_COOLDOWN拡張・SignalCoordinator timeout・日次UTC日境界
- 🟡 PR #21 (open): 監査A4 — RegimeDetector閾値を pair_config で上書き可能化

## 残タスク（優先度順）

### 🔴 P0: 月曜（2026-05-04 06:00 JST）市場オープン直後

| 項目 | 詳細 |
|---|---|
| **orphan #8953385 のクローズ** | USD_JPY 0.02 lot @159.875 (-5,638 JPY)。`scripts/_close_orphan_8953385.py` を市場オープン直後に手動実行 |
| **新規取引で ai_decision 記録確認** | PR #14 の効果検証。月曜の最初の AI 経由取引で DB に CONFIRM/CONTRADICT/NEUTRAL のいずれかが入っているか |
| **EUR/USD シグナル変化観察** | RSI 30/70 で発火条件が厳しくなるはず。エントリー数が減るか観察 |
| **GBP/JPY 取引数観察** | concurrent ガード後、~17 件/週（バックテスト水準）まで縮小するか |

### 🟠 P1: 2 週間以内（戦略の数値前提を更新）

#### 1. BT spread を 1pip → 2pip に補正
- **根拠**: P2-D で実測 avg +1.80 pips, p95 +10.19 pips
- **作業**: `src/backtester.py::calculate_spread()` のデフォルト `pip_spread=1.0` → `2.0`、または通貨ペア別マップを定数化
- **影響範囲**: 全バックテスト結果が下方修正される（過大評価の解消）
- **完了基準**: 既存テスト pass + 新スプレッドで USD_JPY/EUR_USD/GBP_JPY を再ベンチマーク

#### 2. MT5 から M15 5 年データを export → USD_JPY 戦略を真の長期データで再検証
- **根拠**: yfinance 60日上限が原因で M15 と H1 の結論が乖離。MT5 履歴は 5 年取れる
- **作業手順**:
  - VPS 上で MT5 から CSV export（`mt5.copy_rates_from()` で USD_JPY M15 5y）
  - ローカルに scp し `data/mt5_USD_JPY_15m_5y.csv` に保存
  - `scripts/_phase2_h1_validation.py` を流用し interval=M15, period=5y で実行
  - レポート `docs/usdjpy_m15_5y_validation.md`
- **完了基準**: USD_JPY 35/65 が長期 M15 でも妥当か明確判定

#### 3. 市場分析 JSON 更新頻度監査
- **根拠**: P2-E で AI 判定の 67.7% が NEUTRAL（市場分析が中立判断）
- **疑い**: `data/market_analysis.json` が古い、または `confidence < 0.3` で常に NEUTRAL fallback
- **作業**:
  - `data/market_analysis.json` の `generated_at` 履歴を 2 週間分確認
  - `scripts/generate_market_analysis.py` の cron スケジュール（タスクスケジューラ JST 06:30）が確実に走っているか
  - confidence 値の分布調査
- **レポート**: `docs/market_analysis_audit.md`
- **完了基準**: 更新頻度が想定どおりであることを確認、または問題を特定して修正 PR

### 🟡 P1.5: 監査残項目（PR #20/21 マージ後の検証 + データ依存）

監査ドキュメント `docs/system_logic_audit.md` のうち、**コード修正済**:
- A2 (pip_value 12.0 fallback) → PR #16
- A4 (RegimeDetector 二重定義) → PR #21
- A6 (KILL_COOLDOWN 5分) → PR #20
- B7 (SignalCoordinator timeout) → PR #20
- B8 (check_loss_limits 24hローリング) → PR #20
- C4 (戦略 pair_config 配線漏れ) → PR #19

**残（プロダクションデータ待ち）**:
- A1 (ConvictionScorer 閾値): >=8 が 1ヶ月以上発火していない可能性。本番DBの conviction_score 分布確認が必要
- A3 (Bear Researcher always-fires): severity分布と penalty_multiplier 適用率を log 集計
- A5 (AIAdvisor CONTRADICT 0.2倍): PR #14 デプロイ後の ai_decision DB から CONTRADICT trades の PL を集計

これらは PR #14 + PR #19 の VPS デプロイ後 1〜2 週間のデータ蓄積を待ってから定量評価。

### 🟡 P2: 1 ヶ月以内（戦略レベルの判断）

#### 4. USD/JPY 戦略リフレッシュ
- **根拠**: H1 730日で全グリッド負エッジ。35/65 は M15 で測れる範囲では最善だが構造的問題
- **候補**:
  - 戦略変更: BollingerReversal を USD/JPY にも適用？ または ma_crossover (RsiMaCrossover) を試す
  - タイムフレーム変更: H4 / H1 への移行検討
  - 真の MTF 化（D1 トレンド × M15 エントリー）— `rsi_pullback.py` docstring に「将来拡張」と記載
  - ペア撤退: USD/JPY を `INSTRUMENT_STRATEGY_MAP` から除外
- **判断条件**: P1 #2 (M15 5y 検証) の結果次第
- **完了基準**: USD_JPY の戦略を決定し PR 化

#### 5. AIAdvisor の REJECT 閾値見直し
- **根拠**: P2-E で REJECT が 0/3105 (0.0%)。実質シグナル拒否機能が無効
- **現状ロジック**: `regime == "volatile" AND confidence > 0.7` のみ REJECT (`src/ai_advisor.py:82-87`)
- **作業**:
  - 過去 1 ヶ月の bias.regime / confidence 分布を解析
  - REJECT 条件を見直し（例: confidence > 0.6 で direction が逆方向の場合は REJECT 等）
  - A/B 検証（PR #14 デプロイ後の ai_decision データを使う）
- **完了基準**: AIAdvisor の倍率調整 / REJECT 機能の妥当性を定量評価

#### 6. GBP_JPY 大幅スリッページ対策
- **根拠**: P2-D で max +31.20 pips（個別取引 #8753886）。スプレッド/急変動が主因
- **候補**:
  - 経済指標発表前後（NFP 等）の取引停止フィルター（既存 session_filter の拡張）
  - 大幅 spread 検出キルスイッチ強化（`_normal_spread × 3` 超で発注停止）
  - GBP/JPY のみ取引時間帯をさらに絞る
- **完了基準**: max スリッページが p95 と同水準（10 pips 程度）に収まる

### 🔵 P3: 長期改善・運用

#### 7. メソドロジー教訓の CLAUDE.md 反映
- **記載内容**:
  - 「60日 M15 単独での結論は危険、H1 730日も併用必須」
  - 「Sharpe 95% CI でゼロからの距離を必ず確認」
  - 「OOS Trades < 30 のセルは WFE 高くてもロバストとは言えない」
  - 「PF 1.97 のような派手な数字は要検証時間軸の確認」
- **対象**: `~/.claude/projects/.../memory/` のプロジェクトメモリ + 必要なら CLAUDE.md（FX 専用）

#### 8. orphan ポジション自動精算機構
- **根拠**: 今回の #8953385 のように bot 不調時に手動クローズが必要なケース対応
- **設計**:
  - 起動時に DB の `status='open'` & MT5 にも存在する trade を検知
  - opened_at が古すぎる（例: 24h 以上）なら警告 → ユーザー承認 → 自動クローズ
  - 許可セッション外の場合はスキップ
- **完了基準**: 同種 incident で手動介入不要

#### 9. テストカバレッジ拡充
- **対象**: `trading_loop.py` (10 → 20 件)、`signal_coordinator.py`、`bear_researcher.py` の境界条件
- **完了基準**: pytest -q で 500 件超 + coverage 80%+

## メソドロジー: 残タスク着手の進め方

各 P0/P1 項目を着手する際の推奨フロー:

1. **タスクを 1 つに絞る**（並列でやらない、コンテキスト散逸を防ぐ）
2. **作業ブランチを origin/main から切る**（過去の積み残しブランチに重ねない）
3. **コードのみ or 設定のみ or ドキュメントのみ**で 1 PR にまとめる（混在させない）
4. **テストを先に書く**（特に挙動変更を伴う場合）
5. **PR 作成 → ユーザー承認 → マージ → デプロイ**のフローを固定化
6. **デプロイ後は 24h 観察してから次へ**（複数同時デプロイで因果が見えなくなるのを防ぐ）

## 関連ドキュメント

- `docs/phase1_synthesis.md` — Phase 1 (P1-1〜P1-4) 統合分析
- `docs/phase2_synthesis.md` — Phase 2 (P2-C/D/E) 統合 + 矛盾分析
- `docs/strategy_validation_phase1.md` — M15 60日検証
- `docs/strategy_validation_h1.md` — H1 730日検証
- `docs/live_vs_backtest_diff.md` — P1-2 実戦 vs BT 乖離
- `docs/public_strategy_benchmark.md` — P1-4 公開戦略比較
- `docs/gbp_jpy_slippage_analysis.md` — P2-D スリッページ実態
- `docs/ai_advisor_effectiveness.md` — P2-E AI 効果測定
