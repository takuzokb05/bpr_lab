# src/ INDEX — コードの現在地マップ

> src/ 配下 28 Python ファイルの**責務・依存・課題**を一覧化したインデックス。
> 「どのモジュールが何をしているか」「修正時にどこを見るべきか」を即決するための起点。
>
> **最終更新**: 2026-05-05（本セッションで作成）
> **対の文書**: `docs/INDEX.md`（ドキュメント側マップ）/ `STATUS.md`（運用ダッシュボード）

## ステータス凡例

| 印 | 意味 |
|---|---|
| 🟢 | 本番稼働中、メイン経路で使用 |
| 🟡 | 補助・実験的、または注意点あり |
| 🔴 | 非推奨・廃止候補（`_接頭辞` 等のベンチ専用含む） |

## アーキテクチャ俯瞰

```
[main.py] → [trading_loop.TradingLoop]
              ├─ session_filter (時間帯フィルター)
              ├─ regime_detector (相場分類)
              ├─ strategy/* (シグナル生成: MTFPullback / BollingerReversal)
              ├─ conviction_scorer (確信度算出)
              ├─ ai_advisor (AI市場バイアス CONFIRM/CONTRADICT/REJECT)
              ├─ bear_researcher (反対論拠の検証)
              ├─ signal_coordinator (クロスペア相関判断 LLM)
              ├─ position_manager → broker_client (mt5_client)
              │     └─ trade_postmortem (非同期 LLM 勝因/敗因分析)
              ├─ risk_manager (キルスイッチ・サイジング)
              └─ notifier_group → telegram + slack
```

設定: `config.py` + `pair_config.py` (config/pair_config.yaml)
共通: `indicator_cache` で1イテレーション分の指標を一括計算

---

## 🔄 メインループ・統合

| ファイル | 責務 | ステータス | 主な依存 | 既知課題 |
|---|---|---|---|---|
| [trading_loop.py](trading_loop.py) | メインループ。残高/キル/同期/シグナル/発注を毎周回実行 | 🟢 | ai_advisor, bear_researcher, conviction_scorer, position_manager, regime_detector, signal_coordinator, indicator_cache | follow-up: L462/L529/L640 で重複INFO格下げ未完（PR #28系で対処予定） |
| [signal_coordinator.py](signal_coordinator.py) | 複数ペアシグナルを5sウィンドウ集約しLLMで相関判断 | 🟢 | Claude API (COORDINATOR_MODEL_ID) | 旧10s固定でwindow+LLM timeoutレース有（B7修正済） |
| [position_manager.py](position_manager.py) | ポジションのopen/close/同期、相関エクスポージャ制御 | 🟢 | broker_client, risk_manager, trade_postmortem | - |

## 🧠 戦略・判定

| ファイル | 責務 | ステータス | 主な依存 | 既知課題 |
|---|---|---|---|---|
| [ai_advisor.py](ai_advisor.py) | market_analysis.json 読込 → CONFIRM/CONTRADICT/NEUTRAL/REJECT 判定 | 🟢 | data/market_analysis.json | 24h超で失効。日次1回のみ更新（リアルタイム未対応） |
| [conviction_scorer.py](conviction_scorer.py) | 指標合流度から1-10スコア化、サイズ倍率算出 | 🟢 | pandas_ta, strategy.base | - |
| [bear_researcher.py](bear_researcher.py) | 「失敗しうる理由」をテクニカルで5項目検証（LLM不使用） | 🟢 | pandas_ta, strategy.base | Phase 3新規。重み付け済（PR #24） |
| [regime_detector.py](regime_detector.py) | trending/ranging/volatile/unknown 4分類とエクスポージャ倍率 | 🟢 | pandas_ta | pair_config 上書き対応済（PR #21） |
| [strategy/base.py](strategy/base.py) | StrategyBase 抽象基底 + Signal 列挙 | 🟢 | abc | last_diagnostics は抽象化未（getattr フォールバック中、別PR候補） |
| [strategy/ma_crossover.py](strategy/ma_crossover.py) | RSI+ADX+MFI フィルタ付き MA クロスオーバー | 🟢 | config, pandas_ta | 現在 main で未使用（MTFPullback優先） |
| [strategy/mtf_pullback.py](strategy/mtf_pullback.py) | 長期MA200方向 × RSI過熱で押し目/戻り（**本命 PF 2.05**） | 🟢 | config, pandas_ta | 本セッション現在の主戦略。USD/JPY+EUR/USD で稼働 |
| [strategy/bollinger_reversal.py](strategy/bollinger_reversal.py) | 2σタッチ+RSI過熱で逆張り平均回帰 | 🟡 | config, pandas_ta | DD-21〜26%、RR 1.5短め。GBP/JPY で稼働 |
| [strategy/__init__.py](strategy/__init__.py) | パッケージ初期化（Signal/StrategyBase/RsiMaCrossover公開） | 🟢 | - | - |

## 🛡️ リスク・キル

| ファイル | 責務 | ステータス | 主な依存 | 既知課題 |
|---|---|---|---|---|
| [risk_manager.py](risk_manager.py) | サイジング/DD制御/連敗/レバ/6種キルスイッチ | 🟢 | broker_client, sqlite3 | - |
| [session_filter.py](session_filter.py) | JST基準で許可セッション内かを跨日対応で判定 | 🟢 | pair_config | - |
| [pair_config.py](pair_config.py) | config/pair_config.yaml でペア別設定オーバーライド | 🟢 | yaml, src.config | YAML不在時はglobalにフォールバック |

## 🌐 ブローカー・MT5

| ファイル | 責務 | ステータス | 主な依存 | 既知課題 |
|---|---|---|---|---|
| [broker_client.py](broker_client.py) | ブローカーAPI抽象基底（OANDA/IB等共通IF） | 🟢 | abc, pandas | Phase1はMT5実装のみ |
| [mt5_client.py](mt5_client.py) | 外為ファイネスト MT5 実装、シンボル変換/リトライ/フィリング検出 | 🟢 | MetaTrader5, broker_client | **volume_step整列必須**（feedback_mt5_volume_step.md 記録）、`mt5.history_deals_get` の `position=` フィルタ不具合に注意 |

## 📊 指標・分析

| ファイル | 責務 | ステータス | 主な依存 | 既知課題 |
|---|---|---|---|---|
| [indicator_cache.py](indicator_cache.py) | 1イテレーション分の指標を一括計算し全モジュールで共有 | 🟢 | pandas_ta, config | - |
| [trade_postmortem.py](trade_postmortem.py) | 決済済みトレードを LLM で勝因/敗因分析（非同期デーモン）→ DB `trade_postmortems` に保存 | 🟢 | Claude API (POSTMORTEM_MODEL_ID), sqlite3 | max_tokens 不足での JSON truncation は PR #25 で修正済（出力率 3% → 100%）。**集約・自己改善ループは未実装**（サンプル数蓄積待ち） |

## 📢 通知

| ファイル | 責務 | ステータス | 主な依存 | 既知課題 |
|---|---|---|---|---|
| [notifier_group.py](notifier_group.py) | 複数通知先のコンポジット、個別失敗を許容 | 🟢 | (汎用) | - |
| [telegram_notifier.py](telegram_notifier.py) | Telegram Bot 送信 + ロングポーリングでコマンド受信 | 🟢 | requests, threading/queue | - |
| [slack_notifier.py](slack_notifier.py) | Slack Incoming Webhook 送信（Block Kit） | 🟢 | requests | 受信機能なし（一方向のみ） |

## 🧪 バックテスト・実験

| ファイル | 責務 | ステータス | 主な依存 | 既知課題 |
|---|---|---|---|---|
| [backtester.py](backtester.py) | Backtesting.py ラッパ。IS/OOS/WFE + SQLite 永続化 | 🟢 | backtesting, pandas_ta, sqlite3 | スリッページ1pip/約定80%固定（実態より楽観的） |
| [strategy/variants_bt.py](strategy/variants_bt.py) | Donchian/BB/MTF/ATRChannel の backtesting.py 用アダプタ | 🟡 | backtesting, pandas_ta | 比較検証用、本番ロード対象外 |
| [strategy/_bench_hlhb.py](strategy/_bench_hlhb.py) | freqtrade HLHB 移植のベンチマーク戦略 | 🔴 | backtesting, pandas_ta | `_接頭辞` で本番ロード対象外、ベンチ専用 |
| [strategy/_bench_holy_grail.py](strategy/_bench_holy_grail.py) | Linda Raschke "Holy Grail" インスピレーション版 | 🔴 | backtesting, pandas_ta | 原典と100%一致せず、ベンチ専用 |

## ⚙️ 設定・ベース

| ファイル | 責務 | ステータス | 主な依存 | 既知課題 |
|---|---|---|---|---|
| [config.py](config.py) | リスク/指標/AI/通知の全パラメータ一元管理 + .env 読込 | 🟢 | dotenv | MAX_RISK_PER_TRADE 0.05% に DD 対策で抑制中。`DEFAULT_INSTRUMENTS` で稼働ペア定義 |
| [__init__.py](__init__.py) | パッケージ初期化（コメント1行のみ） | 🟢 | - | - |

---

## 「いま何を読むべきか」シナリオ別ガイド

| 知りたいこと | 読むべき順 |
|---|---|
| **取引判定ロジック全体** | `trading_loop._signal_pipeline` → strategy/mtf_pullback.py → conviction_scorer.py → bear_researcher.py |
| **シグナルがなぜ発火しないか** | trading.log の `pipeline:` 行 → trading_loop.py の trace 経路 → 該当戦略の `last_diagnostics` |
| **損益が想定外** | position_manager.py → trade_postmortem の DB レコード → backtester でリプレイ検証 |
| **キルスイッチ発動原因** | risk_manager.py + DB の kill_switch_log テーブル |
| **ブローカー API エラー** | mt5_client.py + memory/feedback_mt5_volume_step.md |
| **AI判定のチューニング** | ai_advisor.py + scripts/generate_market_analysis.py + data/market_analysis.json |
| **戦略パラメータ変更** | config/pair_config.yaml → pair_config.py → 戦略ファイル(`pair_config.get(...)` 参照箇所) |

---

## メンテナンス方針

- **新規 .py 追加 / 大きな責務変更時**: 本ファイルの該当カテゴリ表に行追加・更新
- **PR マージ時**: 「既知課題」列を更新（解決した課題は削除）
- **ステータス変更時**: 🟢⇄🟡⇄🔴 を更新（廃止判断時は理由をコミットメッセージに）
- **2026-08-05 (3ヶ月後)**: カテゴリ全体の見直しタイミング
