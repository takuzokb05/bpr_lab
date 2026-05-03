# システムロジック精査レポート

実施日: 2026-05-03
対象: `src/`, `config/`, `main.py` 全体の「仮決め・未検証マジックナンバー・根拠不明な閾値」抽出
目的: 既知タスク (`remaining_tasks.md` / Phase 2 synthesis) と重複しない**新規発見**を優先度付きで列挙

## サマリ

- 重大 (実害ありそう): **6 件**
- 中 (再現性 / 信頼性): **8 件**
- 軽微 (コード品質): **6 件**
- 既知 (重複・参照のみ): **5 件**

TODO/FIXME/XXX/HACK コメントは grep で 0 件（リテラル "XXX" は docstring の通貨ペア記法説明のみ）。「STAGE2/STAGE3/LOOSE_MODE」マーカーは「本来値に復帰」コメント付きで意図的に管理されており本レポートでは別カテゴリ扱い。

---

## 重大（実害ありそう）

### A1: ConvictionScorer の合計上限と閾値の整合性が破綻

- 場所: `src/conviction_scorer.py:50-55, 142-150, 336-356` + `src/config.py:95`
- 現状: 5 項目 × 0-2 点 = **10 点満点**だが、`_calc_multiplier` が `score >= 8` で 1.5 倍、`>= 7` で 1.0 倍と設定。一方 `MIN_CONVICTION_SCORE = 4` で `should_trade = score >= 4`。さらに `final_score = max(1, min(10, raw_score))` で HOLD 時のみ 1 を返す。
- なぜ問題:
  - 5 項目すべて満点でも 10 点。`>= 8` を満たすには 5 項目中 4 項目で満点必須 → 実際には極めてレア（バックテストで分布検証なし）。
  - 一方 `>= 4` でトレードを許容 → 5 項目のうち 2 項目満点 or 4 項目で 1 点ずつ取れば通る。**「ほぼ全部のシグナルが倍率 0.3〜0.5 で通る」**設計になっている可能性が高い。
  - 設計上の意図（高 conviction を増し玉、低 conviction を見送り）と運用挙動が乖離。
- 推奨対応: 本番 DB の `conviction_score` 分布を抽出 → ヒストグラム化。`>= 8` が実際に何 % か確認した上で閾値を再校正。あわせて閾値の根拠 (どのスコアで PF どう変わるか) をバックテストで検証する。

### A2: ATR 異常時のフォールバック値が「為替レートとして 12 円」を意味し、JPYクロス以外で激しい誤計算になる

- 場所: `src/risk_manager.py:786-787, 825-873`
- 現状: 非JPYペアで決済通貨 JPYレートが取得できなかった場合、`_FALLBACK_PIP_VALUE_NON_JPY = 12.0` を使う。コメントは「Phase 1 固定値」のみ。
- なぜ問題:
  - 12.0 は `0.0001 × 1000 × 120` 相当で、当時の USD_JPY 想定値。**現在 USD_JPY は 156 円付近**で 23% の過小評価 → ロットが約 23% 過大計算される（risk_per_trade を超過）。
  - GBP_USD 等の決済通貨 USD なら 156、EUR_GBP なら 195+ 等、ペアによって全く違う値が必要なのに**1 つの定数**で代用。
  - フォールバック発動が `try-except + WARNING ログ` だけで、実際に発火したことをユーザーが認識する手段がない（Telegram/Slack 通知なし）。
- 推奨対応: フォールバック値を「最近の決済通貨 JPYレート」として動的に保持（例: 24h ローリング中央値）。さらにフォールバック発動時は WARNING → CRITICAL に上げて Telegram/Slack に通知し、見えるようにする。

### A3: Bear Researcher の severity 閾値と penalty 範囲が「ほぼ常に発火」する設計

- 場所: `src/bear_researcher.py:46, 128-130` + `src/config.py:107-108` + `src/trading_loop.py:486-494`
- 現状: `severity = len(risk_factors) / 5`、`BEAR_SEVERITY_THRESHOLD = 0.4`、つまり**5 項目中 2 項目検出で発火**。`penalty = max(0.5, 1.0 - severity * 0.5)` → 最大半減。
- なぜ問題:
  - `_check_volume_confirmation` は「MFI が 40-60」で発火 = MFI 中立帯はかなり頻繁。
  - `_check_bb_squeeze` は「BBW < 平均 BBW × 0.5」で発火 = 平常時のスクイーズで頻繁。
  - 上の 2 つだけで severity 0.4 = 閾値到達。**「弱い相場ではほぼ常に penalty 半減」**になっている可能性。
  - 5 件中の重み付けがなく、「上位足矛盾（重大）」と「MFI 中立（軽微）」が等価に扱われる。
- 推奨対応: 過去 1 ヶ月の Bear Researcher ログから `severity` 分布と `penalty_multiplier` 適用率を集計。0.4 閾値が想定通り「年に数回の警告」になっているか「ほぼ毎回発火」になっているか確認。後者なら閾値を 0.6 以上 or 重み付けスコアに変更。

### A4: REGIME_BBW_SQUEEZE_RATIO=0.5 と他の REGIME_* 閾値が「同じ pair 設計」前提

- 場所: `src/config.py:99-102` + `src/regime_detector.py:141-228`
- 現状: `REGIME_ADX_TRENDING=20.0`, `REGIME_ADX_RANGING=15.0`, `REGIME_ATR_VOLATILE_RATIO=2.0`, `REGIME_BBW_SQUEEZE_RATIO=0.5` が**全ペア共通**。
- なぜ問題:
  - GBP_JPY（高ボラ）と EUR_USD（低ボラ）で同じ ADX/ATR 閾値が妥当な根拠なし。
  - `pair_config.yaml` には `adx_threshold` が **ペア別** で別途存在（25/20/25/25/25/25）。**RegimeDetector の閾値（20/15）と pair_config の閾値（25）が二重定義**されており、規律として混乱の元。
  - `signal_pipeline` 内で `regime_info.adx < pair_adx_threshold` チェックがあるため実質 pair 値が優先されるが、`RegimeInfo.regime` 自体は共通閾値で判定 → conviction score の `_score_regime` などに影響。
- 推奨対応:
  - RegimeDetector の閾値を pair_config に移行 (`regime_adx_trending`, `regime_adx_ranging` キー追加)、または `REGIME_ADX_TRENDING` を「ペア別 adx_threshold + 5」のように相対式にする。
  - 二重定義を解消し、「どの閾値が最終判断か」を明文化。

### A5: AIAdvisor の `position_size_multiplier` が REJECT 以外で常に正、CONTRADICT でも 0.2-0.5 倍残す

- 場所: `src/ai_advisor.py:124-137` + `docs/ai_advisor_effectiveness.md`
- 現状: `CONTRADICT` でも `max(0.5 - confidence * 0.3, 0.2)` = 最低 0.2 倍は残る。本番ログで CONTRADICT が 19.7%（611/3105）あり、`REJECT` は 0/3105。
- なぜ問題:
  - REJECT が機能していないことは既知（remaining_tasks.md #5）だが、**「CONTRADICT でもポジションを取る」設計の妥当性**自体が未検証。
  - AI が逆方向と言っているのに 0.2 倍でも取る → 期待値マイナス取引を増やしている可能性。
  - confidence < 0.3 で NEUTRAL になるが、「逆方向 + confidence 0.4」のような微妙な領域でも 0.38 倍の取引が成立する。
- 推奨対応: P2-E の続編として、CONTRADICT 取引の PL を CONFIRM/NEUTRAL と比較。明確にマイナスなら `position_size_multiplier(CONTRADICT) = 0.0` （= REJECT 同等）に変更。

### A6: KILL_COOLDOWN_MINUTES=5 が短すぎる可能性 + ボラティリティ/スプレッドキルが**過去のキャッシュ値**で評価される

- 場所: `src/config.py:149` + `src/risk_manager.py:218-223` + `src/trading_loop.py:106-110, 263-272`
- 現状: ボラ/スプレッドキルは「前回イテレーションの ATR/spread」を使って評価し、5 分でクールダウン解除可能。
- なぜ問題:
  - フラッシュクラッシュなら 1 分足でも数分間異常値が続く。5 分クールダウン → 異常継続中に解除 → 即再発動 → ログだけが暴れる。
  - `_pre_trade_checks` が `_last_atr`（前回キャッシュ）で判定 → 評価のタイミングが**ATR 取得の 1 イテレーション遅れ**。`evaluate_kill_switch` のあと `_fetch_and_compute` が走るため、最新 ATR でのキル判定は次イテレーションになる。
  - `KILL_API_DISCONNECT_SEC=30` も「30 秒で全決済」だが、何が 30 秒の根拠か不明。MT5 のリトライ間隔・通常切断時間の実測なしと思われる。
- 推奨対応:
  - クールダウンを 15-30 分に延長（fast crash 後の二次波対応）。
  - `_pre_trade_checks` 内で評価する ATR を「直近 fetch_data の結果」に変更（順序入れ替え）。
  - `KILL_API_DISCONNECT_SEC` の根拠を確認。MT5 のヘルスチェックを別途設けて実測してから決定。

---

## 中（再現性 / 信頼性）

### B1: `MAX_CORRELATION_EXPOSURE = 2` の計算が「グループ単位」だが USD_JPY が 2 グループに属する

- 場所: `src/config.py:57, 60-63` + `src/position_manager.py:203-236`
- 現状: USD_JPY は `JPY_CROSS` と `USD_GROUP` の両方に属する。各グループ独立に max=2。
- なぜ問題: USD_JPY がオープン中、EUR_JPY と EUR_USD と GBP_USD を全部取れる（USD_JPY 自身がカウントされる相関グループは 2 つあるが、各グループで 1/2 のため）。実質的な総保有数 = 4 ペアに膨らみ、想定の 2 を超える可能性。
- 推奨対応: グループの重複所属を許容するなら、`max_per_group` ではなく「ペア単位の相関度合い行列」に変更。または USD_JPY をどちらか 1 グループに固定する。

### B2: `MAX_CONSECUTIVE_LOSSES = 10` のコメントと実装の不一致

- 場所: `src/config.py:51-52` + `src/risk_manager.py:681`
- 現状: コメント「STAGE2: 本来5→10で一旦緩め」、docstring「MAX_CONSECUTIVE_LOSSES（5）連敗で24時間停止」（古い記述が残存）。
- なぜ問題: 実装は 10、コメントとドキュメントが矛盾。読み手が「5 で停止する」と誤解する。Phase 完了後に 5 に戻す予定なのか、10 が新基準なのかも未決。
- 推奨対応: docstring を修正。STAGE2 緩和を恒久化するなら「本来値」コメントを削除して根拠（DD 過剰停止の実害があった等）を残す。

### B3: BollingerReversal の閾値（BB_RSI_OVERBOUGHT=65, BB_RSI_OVERSOLD=35）が**戦略ファイル内ハードコード**

- 場所: `src/strategy/bollinger_reversal.py:28-33`
- 現状: BB_LENGTH=20, BB_STD=2.0, BB_RSI_OVERBOUGHT=65, BB_RSI_OVERSOLD=35, BB_ATR_MULTIPLIER=1.5, BB_MIN_RISK_REWARD=1.5。pair_config.yaml の RSI 閾値（GBP_JPY 35/65）と一致するが、これは偶然の一致。
- なぜ問題:
  - GBP_JPY 用に最適化された値が、将来他ペアで BollingerReversal を使う場合に同値で適用される。
  - pair_config の RSI 閾値変更が BollingerReversal に伝播しない（ma_crossover とロジックが別）。
  - `INSTRUMENT_STRATEGY_MAP` で割当を変えれば即座に他ペアに使える設計だが、パラメータが固定されている。
- 推奨対応: BollingerReversal が pair_config を読み込むように修正（`generate_signal(..., pair_config=...)` で kwargs 経由で渡されているのに使っていない）、または BollingerReversal 専用の pair_config セクションを設ける。

### B4: MTFPullback の MTF_TREND_MA=200, MTF_RSI_OVERSOLD=35 もハードコード + 「MTF」と謳いながら**単一タイムフレーム**

- 場所: `src/strategy/mtf_pullback.py:30-32, 1-12`
- 現状: docstring「長期MA(200)の上下でトレンド判定」、しかし実際は M15 データの SMA(200) を使うだけで、上位足（H1/H4/D1）は読んでいない。
- なぜ問題:
  - 「MTF (Multi-Timeframe)」と命名しているのに単一 TF の擬似 MTF。命名と実装の乖離は将来の保守者を必ず惑わす。
  - `remaining_tasks.md` #4 にも「真の MTF 化」と将来課題として明記されており、命名先行で実装が追いついていない既知問題。
- 推奨対応: 短期では `PullbackOnLongMA` のような名前にリネーム、または上位足取得を実装。

### B5: `MA_CROSS_LOOKBACK_BARS = 5` の根拠が「LOOSE_MODE 緩和のため」のみ、検証なし

- 場所: `src/config.py:72-73` + `src/strategy/ma_crossover.py:185-203`
- 現状: 「直近 5 本以内にクロスがあれば BUY/SELL 候補」。コメント「M15 なら直近 75 分」のみ。
- なぜ問題:
  - 5 本という値の根拠（バックテスト結果）が記録されていない。
  - クロス後 5 本待つ間に値動きが反転していた場合、遅参どころか逆張りエントリーになる可能性がある。
  - ma_crossover.py は現在 INSTRUMENT_STRATEGY_MAP に含まれず（`MTFPullback` と `BollingerReversal` のみ使用）デッドコードに近いが、設定だけ残っている。
- 推奨対応: ma_crossover を本番から外したのなら戦略ファイルを `archived/` に移動 or 設定もコメントアウト。残すなら 5 の根拠を検証して記録。

### B6: AI 分析の有効期限 `MAX_ANALYSIS_AGE_HOURS = 24` がコード内ハードコード

- 場所: `src/ai_advisor.py:25`
- 現状: 25 行目に直接 `MAX_ANALYSIS_AGE_HOURS = 24`。`config.py` に移されていない。
- なぜ問題:
  - 他の AI 関連定数（AI_ADVISOR_ENABLED, AI_MODEL_ID）は config.py に集約されているのに、これだけ別管理。
  - 朝 6:30 生成 → 翌朝 6:30 で期限切れ。生成が 1 度失敗すると即座に AI フィルターが無効化される（NEUTRAL fallback）。`remaining_tasks.md` #3 で 67.7% NEUTRAL の原因疑いとして既出。
- 推奨対応: config.py に移動し、`AI_ANALYSIS_MAX_AGE_HOURS = 36` 程度に緩和（生成 1 回失敗を許容）。

### B7: SignalCoordinator のウィンドウ `COORDINATION_WINDOW_SEC = 5.0` と timeout=10s の関係

- 場所: `src/signal_coordinator.py:29, 89-90, 126-134`
- 現状: 5 秒ウィンドウ集約、register_signal の timeout 10 秒、Claude API timeout 10 秒。
- なぜ問題:
  - `_evaluator_loop` で `time.sleep(window_sec=5)` → LLM 呼び出し（最大 10 秒）→ 計 15 秒。register 側 timeout=10 秒だと**ウィンドウ内に来た 2 番手以降は確実にタイムアウト**で「安全側で承認」フォールバック。
  - つまり LLM 評価が成功しても結果が register 側に届かない → 実質的にクロスペア相関判断が機能しない可能性。
  - 単一ペアシグナルの場合は `time.sleep(5)` 待つだけで即承認（5 秒の遅延がメインループの 60 秒間隔に影響）。
- 推奨対応: register 側 timeout を `window_sec + claude_timeout + 2` 以上に。もしくは LLM 評価結果を Future で待つ設計に変更。

### B8: `check_loss_limits` の期間が「過去 24h / 7 days / 30 days」で**カレンダー基準と不一致**

- 場所: `src/risk_manager.py:596-606`
- 現状: `day_start = now - timedelta(days=1)` のローリング 24 時間。MAX_DAILY_LOSS のコメントは「日次」。
- なぜ問題:
  - 「日次 5%」を**ローリング 24 時間**で評価している。「今日 0:00 から」ではなく「24 時間前から」。
  - 04:00 に -4% 損失、翌 02:00 に +0.5% で再エントリー → 「日次」上限に到達せずトレード可能。だがカレンダー日 (UTC 0:00 始まり) で見れば前日と当日のいずれかは超えている可能性。
  - `KillSwitch.should_auto_deactivate` は `daily_loss` 解除を「翌日 0:00 UTC」で判定 → こちらはカレンダー基準。**評価とリセットでロジックが不一致**。
- 推奨対応: カレンダー日基準に統一（UTC 0:00 始まり）。または「ローリング 24h」とコメントを正確に書き換える。

---

## 軽微（コード品質）

### C1: `MT5_DEVIATION = 20` (ポイント) の根拠コメントなし、外為ファイネスト推奨値か検証なし
- 場所: `src/config.py:157`。スリッページ許容を 20 ポイント (= 2 pips) で固定。GBP_JPY は実測 max +31 pips の事例あり (P2-D)。**注文時の deviation と post-fill の slippage は別概念**だが、リテラルの妥当性は要確認。

### C2: `data["close"].iloc[-1]` を「最新価格」とする前提
- 場所: `src/position_manager.py:352`、`src/strategy/*.py` 多数。
- M15 ローソク足の **未確定足** を `iloc[-1]` で取得しているため、エントリー価格が「現在進行中バーの close」になる。市場実態とのズレが発生しうる。MT5 の `mt5.symbol_info_tick()` で最新気配を取るほうが正確。

### C3: TradingLoop の `data = ...get_prices(instrument, 300, granularity)` で 300 本固定
- 場所: `src/trading_loop.py:323-326`
- MA200 + 余裕で 300、というコメントだが、もし将来 MA500 戦略を入れたら**サイレントにデータ不足**で全シグナルが HOLD に。マジックナンバー化されている。最低必要本数を戦略から取る or 定数化。

### C4: BollingerReversal が pair_config を受け取る引数を**無視**している
- 場所: `src/trading_loop.py:406-408` で `pair_config=pair_cfg` を kwargs で渡しているが、`BollingerReversal.generate_signal` も `MTFPullback.generate_signal` も pair_cfg を読んでいない。**インターフェイスはあるが配線なし**。
- B3 と関連。コメントには「将来の戦略側オーバーライド用」とあるが、実装漏れ。

### C5: `slack_notifier`, `telegram_notifier` の retry/timeout 設定の有無が未確認
- 場所: 本レポートでは未読。CLAUDE.md「外部 API はタイムアウト必須」に照らして要確認項目として記載。

### C6: SQL 例外を `except sqlite3.Error` で warning 飲み込み多数
- 場所: `src/risk_manager.py:153-154`, `position_manager.py:175-176, 196-197` 等。
- DB 書き込み失敗が WARNING ログだけで、ポジションオープンは成功扱い → DB と実ポジションのズレが発生。少なくとも Telegram/Slack に通知すべき。

---

## 既知（重複・参照のみ）

### K1: BT spread 1pip→2pip 補正
→ `remaining_tasks.md` P1 #1。`src/backtester.py` には既に `TYPICAL_SPREADS_PIPS` (USD_JPY 1.5, EUR_USD 2.0, GBP_JPY 2.5) と `DEFAULT_SPREAD_PIPS = 2.0` が定義済み。`calculate_spread()` のデフォルト挙動も実測値を使う。**ただし `auto_spread=True` を呼び出し側が指定しないと適用されない**点は実務上の落とし穴。

### K2: USD/JPY M15 5y 検証
→ `remaining_tasks.md` P1 #2。

### K3: AIAdvisor REJECT 0/3105 問題（A5 と関連、対応箇所は重複）
→ `remaining_tasks.md` P2 #5。本レポートの A5 は「CONTRADICT 倍率の妥当性」という新観点。

### K4: GBP_JPY スリッページ対策
→ `remaining_tasks.md` P2 #6。

### K5: MTFPullback「真の MTF 化」
→ `remaining_tasks.md` P2 #4。本レポート B4 は同問題を「命名と実装の乖離」観点で再掲。

---

## 全体所感（プラグマティスト視点）

1. **A1 (conviction 閾値分布) が最優先**。実運用 DB のスコア分布を見れば 30 分で判明する。設計意図と運用挙動の乖離は最も直すべき仮決め。
2. **A2 (pip_value フォールバック)** は「滅多に発火しない」が、発火時のロット計算ミスは即実害。発火頻度の監視を入れるだけでも価値が大きい。
3. **A3-A4 (Bear/Regime 閾値)** は同じ症状（共通閾値の妥当性）。pair_config への移行と「実際の発火率の集計」がセットで必要。
4. **B 系**は既知タスク完了の前後で取り組むべき中堅。特に B7 (SignalCoordinator timeout) は「機能しているように見えて機能していない」典型で、ログ精査で簡単に検証できる。
5. **C 系**は急がない。リファクタリング機会で拾えばよい。

具体的な数値はすべて `~/.claude/projects/.../memory/` の Phase 1/2 検証メモを更新する素材になる。
