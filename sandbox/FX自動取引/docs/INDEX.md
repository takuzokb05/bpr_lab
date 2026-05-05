# docs/ INDEX — ドキュメント現在地マップ

> 30 ファイルのドキュメントについて「**いま読む価値があるか**」を一覧化したインデックス。
> 各ファイルが何を扱い、どのフェーズの成果物で、現在の運用に対して現役か参考か廃止候補かを判定する。
>
> **最終更新**: 2026-05-05（本セッションで作成）
> **メンテ方針**: 新規 docs 追加 / 既存 docs のステータス変化があった時にこのファイルを更新する。

## ステータス凡例

| 印 | 意味 |
|---|---|
| 🟢 **現役** | 直近2週間で参照価値あり。実装の根拠になっているか、進行中の議論に紐付く |
| 🟡 **参考** | 過去の経緯・判断ログとして価値あり。現役の議論には直接寄与しない |
| 🔴 **廃止候補** | 既に古く、現状と乖離。次回整理タイミングで削除/アーカイブ判断 |

## 本セッション (2026-05-05) の成果物への入口

このセッションで何が起きたかを追跡するための起点：

| 種類 | リンク | 内容 |
|---|---|---|
| PR | [#26](https://github.com/takuzokb05/bpr_lab/pull/26) | パイプライン1行サマリログ追加（観測性整備の本体） |
| PR | feat/silence-legacy-session-info | 旧『時間帯フィルター』INFO 格下げ（PR #26 二段構え完成） |
| メモリ | `memory/project_fx_pipeline_trace.md` | PR #26 で追加した観測性機構の使い方 |
| メモリ | `memory/project_fx_signal_status_2026_05_05.md` | 半日観察スナップショット（3ペアの DECISION 分布） |
| メモリ | `memory/feedback_baseline_check_failure.md` | 「実装済み提案」事故防止のための skill 化背景 |
| メモリ | `memory/feedback_vps_git_hygiene.md` | VPS git運用ルール（pull-only / divergence 解消手順） |
| skill | `skills-registry/skills/pre-review-baseline-check/SKILL.md` | コードレビュー/現状分析前の認識ベースライン確認 |

## カテゴリ別ドキュメント一覧

### 🔍 調査（Phase A 成果物）

| ファイル | 状態 | 1行サマリ | 最終更新/参照 |
|---|---|---|---|
| [01_FX自動取引の現状.md](01_FX自動取引の現状.md) | 🟡 | プラットフォーム/API/規制の市況調査 | 2026-02-13 (Phase A) |
| [02_リスク管理と安全設計.md](02_リスク管理と安全設計.md) | 🟡 | 1-2%ルール/ATR-SL/DD制御の体系整理 | 2026-02-13 (Phase A) |
| [03_AI戦略の評価.md](03_AI戦略の評価.md) | 🟡 | AI/MLのFX有効領域と限界 | 2026-02-13 (Phase A) |
| [04_技術設計と実装方針.md](04_技術設計と実装方針.md) | 🟡 | OANDA+Pythonアーキ/段階移行方針 | 2026-02-13 (Phase A) |

### 📝 レビュー（調査文書へのレビュー）

| ファイル | 状態 | 1行サマリ | 最終更新 |
|---|---|---|---|
| [review_fact-check_01-03.md](review_fact-check_01-03.md) | 🟡 | doc01-03ファクトチェック52主張 | 2026-02-13 |
| [review_devils-advocate_04.md](review_devils-advocate_04.md) | 🟡 | doc04反論1stパス（致命4件） | 2026-02-13 |
| [review_devils-advocate_04_v2.md](review_devils-advocate_04_v2.md) | 🟡 | doc04反論2ndパス | 2026-02-13 |
| [review_devils-advocate_04_v3.md](review_devils-advocate_04_v3.md) | 🟡 | doc04反論3rdパス（条件付Yes） | 2026-02-14 |

### 📐 設計・仕様

| ファイル | 状態 | 1行サマリ | 最終更新/参照PR |
|---|---|---|---|
| [SPEC.md](SPEC.md) | 🟡 | Phase 1 機能仕様 F1-F9 | 2026-02-14 |
| [SPEC_phase2.md](SPEC_phase2.md) | 🟡 | Phase 2 機能仕様 F11-F17 | 2026-02-14 |
| [phase2_plan.md](phase2_plan.md) | 🟡 | Phase 2 実装計画書 | 2026-02-14 |
| [phase1_retrospective.md](phase1_retrospective.md) | 🟡 | Phase 1 振り返り（成果物リスト） | 2026-02-14 |
| [code_review_checklist.md](code_review_checklist.md) | 🟡 | Phase 1 4観点+6カテゴリレビュー結果 | 2026-02-14 |
| [usdjpy_strategy_refresh_plan.md](usdjpy_strategy_refresh_plan.md) | 🟢 | USD/JPY戦略刷新の候補A-E比較 | 2026-05-03 (PR #18) |

### 🔍 監査（実装後システム監査）

| ファイル | 状態 | 1行サマリ | 最終更新/参照PR |
|---|---|---|---|
| [system_logic_audit.md](system_logic_audit.md) | 🟢 | マジックナンバー/未検証閾値の20件抽出 | 2026-05-03 (PR #18-#21進行中) |
| [market_analysis_audit.md](market_analysis_audit.md) | 🟢 | market_analysis.json更新頻度監査 | 2026-05-03 (P1#7) |
| [ai_advisor_effectiveness.md](ai_advisor_effectiveness.md) | 🟢 | AIAdvisor通過/拒否率3105件集計 | 2026-05-03 (P2-E) |

### 📊 バックテスト・検証

| ファイル | 状態 | 1行サマリ | 最終更新/参照PR |
|---|---|---|---|
| [strategy_validation_phase1.md](strategy_validation_phase1.md) | 🟢 | RsiPullback M15 60日グリッド検証 | 2026-05-03 (P1-1+3) |
| [strategy_validation_h1.md](strategy_validation_h1.md) | 🟢 | RsiPullback H1 730日（USD/JPY負エッジ確定） | 2026-05-03 (P2-C) |
| [public_strategy_benchmark.md](public_strategy_benchmark.md) | 🟢 | RsiPullback vs HLHB vs Holy Grail比較 | 2026-05-03 (P1-4) |
| [live_vs_backtest_diff.md](live_vs_backtest_diff.md) | 🟢 | 実戦vsBT乖離分析（3ペア） | 2026-05-03 (P1-2) |
| [gbp_jpy_slippage_analysis.md](gbp_jpy_slippage_analysis.md) | 🟢 | GBP/JPYスリッページp95=21pips | 2026-05-03 (P2-D) |
| [phase1_synthesis.md](phase1_synthesis.md) | 🟢 | P1-1〜P1-4統合・原因特定 | 2026-05-03 |
| [phase2_synthesis.md](phase2_synthesis.md) | 🟢 | P2-C/D/E統合・M15vsH1矛盾の再判断 | 2026-05-03 |

### 🚀 運用（デプロイ・VPS）

| ファイル | 状態 | 1行サマリ | 最終更新 |
|---|---|---|---|
| [deployment_guide.md](deployment_guide.md) | 🟡 | Phase1→2 ローカルデプロイ手順 | 2026-02-14 |
| [vps_deployment_guide.md](vps_deployment_guide.md) | 🟢 | ConoHa Windows VPSデプロイ手順 | VPS稼働中(2026-03-28〜) |
| [vps_setup_handoff.md](vps_setup_handoff.md) | 🔴 | VPSセットアップ引き継ぎ書（既に完了済み手順、削除候補） | 完了タスク化 |

### 🗺️ ロードマップ

| ファイル | 状態 | 1行サマリ | 最終更新 |
|---|---|---|---|
| [ROADMAP_post_loose_mode.md](ROADMAP_post_loose_mode.md) | 🟢 | LOOSE_MODE脱却3段階プラン | 2026-04-21 |
| [phase3_roadmap.md](phase3_roadmap.md) | 🟢 | AI強化Phase3（実践者知見ベース） | 2026-03-30 |
| [remaining_tasks.md](remaining_tasks.md) | 🟢 | 残タスクP0/P1リスト・PR #15-#21 | 2026-05-03 |

## 「いま何を読むべきか」シナリオ別ガイド

| 知りたいこと | 読むべき順 |
|---|---|
| **プロジェクト全体像をゼロから理解** | `01_FX自動取引の現状.md` → `04_技術設計と実装方針.md` → `phase1_retrospective.md` |
| **現在稼働中の戦略の根拠** | `strategy_validation_h1.md` → `phase2_synthesis.md` → `usdjpy_strategy_refresh_plan.md` |
| **バックテストと実戦の乖離** | `live_vs_backtest_diff.md` → `gbp_jpy_slippage_analysis.md` |
| **次に何をやるべきか** | `remaining_tasks.md` → `phase3_roadmap.md` → `ROADMAP_post_loose_mode.md` |
| **VPS の本番運用** | `vps_deployment_guide.md` + memory/project_vps_trading.md |
| **観測性（ログから何が読み取れるか）** | memory/project_fx_pipeline_trace.md → memory/project_fx_signal_status_2026_05_05.md |
| **既知バグ・要対応案件** | memory/project_fx_pending_items.md |
