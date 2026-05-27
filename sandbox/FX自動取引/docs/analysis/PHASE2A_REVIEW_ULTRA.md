# Phase 2'A 起動可否レビュー — ultrathink (構造バグ担当)

**判定**: **設計修正必要** (起動延期、最低限の修正＋反論屋再査読を経るまで Phase 2'A は起動しない)

**査読時刻**: 2026-05-27
**査読範囲**: SPEC_V3.md / PHASE_2A_PLAN.md / IMPROVEMENT_META_ANALYSIS.md / RETREAT_2026-05-26.md / SPEC_V3_DEPLOY.md / `src/spec_v3/*` 全ファイル / `scripts/_cycle2_extract_signals.py` / `tests/spec_v3/test_demo_loop.py`
**継承する Ultra スタンス**: 「表層 (ドキュメントの言葉) ではなく構造 (実装の挙動)」「PoC 三重定義パターンの再演を厳しくチェック」

---

## TL;DR — 3行で

1. **SPEC v3 § 2.1 step 2 が宣言した「GBP_JPY VOLATILE フィルタ」は実装に存在しない**。BT 検証データも実は NO_VOLATILE で取られていた (n=2,443)。**SPEC ↔ BT ↔ 実装の三重不整合**。これは RETREAT バグ ① と ② の構造再演である。
2. **スプレッド異常キルスイッチ未配線** (`check_spread_anomaly()` 関数定義のみ、`process_pair` / `evaluate_safety` から呼び出しゼロ)。SPEC v3 § 5.2 が明記した 4 トリガのうち 1 つが構造的に発火不能。これも「字面達成、実質未実装」のパターン。
3. **撤退条件発火時のオープンポジション扱いが未定義**。`retreat_5_all_pairs` 検知後 `break` でループ終了するが、Open Position は MT5 にそのまま残る。「全停止 = 何もせず放置」になっていて、Phase 2'A 安全設計として致命。

---

## 発見した構造バグ (重大度順)

### バグ ① 【最重度】 SPEC ↔ BT ↔ 実装の三重不整合 (GBP_JPY VOLATILE フィルタ問題)

**証拠の階層**:

| 層 | GBP_JPY での VOLATILE フィルタ | 出処 |
|---|---|---|
| **SPEC v3 ドキュメント** | **適用すると宣言** | `SPEC_V3.md` L37, L92-93 (擬似コード step 2), L272 (§6 ペア別パラメータ), L285 (§6.1) |
| **Phase 0' BT (= 採用根拠)** | **適用していない (no_volatile)** | `data/signal_v2_historical_signals_gbp_jpy_no_volatile.csv` 2,443件 → これが `IMPROVEMENT_META_ANALYSIS.md` L6 の "GBP_JPY 2,443件" の出処 |
| **`src/spec_v3/` 実装** | **適用していない (コード上に存在しない)** | `seasonal_detection` モジュールが `src/spec_v3/` のどのファイルからも import されていない。`demo_loop.process_pair` は `signal_v2.generate_signal(m15_df)` を直接呼ぶだけ |

**定量比較**:
- VOLATILE 適用版 GBP_JPY シグナル: **216 件 / 2 年** (= 月 9 件)
- NO_VOLATILE 版 GBP_JPY シグナル: **2,443 件 / 2 年** (= 月 102 件、**11.3 倍**)

検証根拠の中核となった Proposal 3 の GBP_JPY 数字 (CONFIRM × conf≥0.60 → PF 1.294 / n=469) は、後者の **n=2,443 母集団** から導出されている。

**構造的影響**:
- **SPEC が言ったこと ≠ BT が見たこと ≠ 実装が出すこと** → 3層がバラバラ。これは RETREAT バグ ② 「自分が書いた文書内で認識の非対称が発生」の正確な再演
- 実装側だけ見れば「SPEC v3 が宣言したシグナル分布」とは別物が出ている (= RETREAT バグ ④ 「PoC 三重定義」の構造そのもの)
- GBP_JPY 想定取引件数 (SPEC_V3.md L283: `~20-25 trades / 月`) は 469 件 / 22 ヶ月 → 月 21 件で算出されているが、これは VOLATILE 適用後ではなく NO_VOLATILE+LLM 後の数字なので、実装の挙動と一致する。**ドキュメントは「VOLATILE 適用」と書いておきながら数字は NO_VOLATILE 前提**。「言葉と数字が違う場所を指している」=後付け説明の典型パターン

**推奨修正**: 起動前に **どちらかに統一する**。
- (A) VOLATILE フィルタを `src/spec_v3/` に実装し、BT を VOLATILE 適用版で再検証する (取引機会は月 ~9 件相当に減るので Phase 2'A 30 日で n が足りない可能性、延長検討)
- (B) SPEC_V3.md から VOLATILE 適用記述を削除し「NO_VOLATILE で運用する」と明記し直す (短期的に整合性は取れるが、なぜ VOLATILE を捨てるかの合理化が必要 = 「SPEC v2 で苦労して作ったフィルタは無視」を意味する)

**判断**: SPEC を修正して実装に合わせる (B) のほうが整合性は早く取れるが、それは「VOLATILE フィルタの存在意義」(SPEC v2 で ★★★★★ を取った季節判定器) を捨てる宣言になる。**ユーザーの意思決定が必要**。

---

### バグ ② 【高】 スプレッド異常キルスイッチが未配線

**証拠**:
- `src/spec_v3/risk_manager.py` L121-129 で `check_spread_anomaly()` 関数を定義
- ところが `grep "check_spread_anomaly|get_spread|baseline_spread" src/spec_v3/` でヒットゼロ
- `demo_loop.py` `process_pair` でも `evaluate_safety` でも呼び出しなし

つまり SPEC_V3.md § 5.2 が明記した「スプレッド 3 倍拡大 → 当該ペア新規発注停止」**トリガは定義済みだが配線されていない**。

**SPEC v3 § 5.2 のキルスイッチ表 (4 トリガ) の状態**:

| トリガ | 実装状態 |
|---|---|
| VIX > 30 | **未実装** (SPEC_V3.md § 5.2 で「外部データ依存のためデフォルト無効」と risk_manager L12 で書かれているが、SPEC は「実装する」と書いている) |
| 1 日 ±3σ 急変 | **未実装** (同上) |
| **スプレッド 3 倍拡大** | **関数だけ存在、配線なし** (本バグ) |
| LLM API 連続 5 失敗 | 実装あり、配線あり (`process_pair` で正常に呼ばれる) |

「字面達成、実質未実装」が **3/4 トリガに該当**。SPEC v3 § 5.2 を素直に読めば 4 つ動くと思う読者を欺く構造になっている。これは RETREAT バグ ① 「検証範囲と運用範囲のミスマッチ」の Phase 2'A 版。

**推奨修正**: 
- 最低限、スプレッド異常トリガを `process_pair` の LLM 呼び出し前に挿入 (Mt5Client.get_spread を呼んで `check_spread_anomaly` を回す)
- SPEC v3 § 5.2 の表に「実装状態」列を追加して、未実装トリガは「Phase 2'B 以降」と明記
- 起動前チェックリストに「キルスイッチ 4 トリガが全て発火可能か手動シミュレーション」を追加

---

### バグ ③ 【高】 撤退条件発火時のオープンポジション処理が未定義

**証拠**:
- `demo_loop.py` L649-657: `action.startswith("retreat_")` または `daily_stop` / `monthly_stop` で `break`
- `grep "close_all_positions|emergency_close|on_retreat|exit_open" src/spec_v3/` でヒットゼロ
- `retreat_5_all_pairs` (システム全停止) を検出して `break` した瞬間、**MT5 デモ口座にある Open Position はそのまま残る**

これは Phase 2'A (ペーパー) では金銭的影響は小さいが、Phase 2'C (本番) に移行した時に同じコードがそのまま動けば、**「停止したつもりが市場に晒され続ける」状態が発生**する。SPEC v3 § 4.5 の撤退条件 #5「両ペア撤退条件成立 → SPEC v3 全体終了」は止まらない。

**RETREAT バグ ⑤「4時間損切りミスマッチ」と同型**: 安全装置の設計が「停止トリガを引く」だけで「停止後の状態」を定義していない。Ultra が言った「亡き者の挙動データ未活用」と同じ構造 — 「停止後、Open Position はどう挙動するか」を実測検証していない。

**推奨修正**:
- `evaluate_safety` が `retreat_5` を返した時点で `client.close_all_positions()` 相当を呼ぶ
- `daily_stop` でもオープン継続にするか即時クローズにするかの方針を SPEC v3 に明記 (現状コードは「継続」だが、根拠が文書化されていない)
- ループの `finally` ブロックで `notifier.bot_stopped` だけが呼ばれるが、ここに「open position 件数」のスナップショットを必ず通知する

---

### バグ ④ 【中】 signal_v2 が「GBP_JPY 専用」だが USD_JPY にも適用されている

**証拠**:
- `src/spec_v2/signal_v2.py` L1-26 (モジュール docstring) に **明示的に「GBP_JPY 専用」「pips 計算は GBP_JPY」「PIP_SIZE = 0.01 // GBP_JPY 専用設定 (JPY クロス)」** と書かれている
- 同モジュール L1 で「§ 3-1 確定までのプレースホルダ」と自認
- USD_JPY もたまたま JPY クロスなので PIP_SIZE は同じ 0.01 で動くが、**ロジックの汎用性を SPEC v2 著者は宣言していない**
- `src/spec_v3/__init__.py` L22: `ENABLED_PAIRS = ("USD_JPY", "GBP_JPY")` で平然と USD_JPY を採用

**構造的影響**:
- SPEC v3 § 1.1 表で「ベース戦略: `src/spec_v2/signal_v2.py` ... 改変禁止 (完成済)」と書いているが、**著者本人 (signal_v2.py の docstring) は「placeholder」「GBP_JPY 専用」と言っている**。SPEC v3 がこの状態の signal_v2 を「完成済」とラベリングしたことは、検証層の取り違え (RETREAT バグ ① の「★★★★★ ≠ 経済性」と同じ構造)
- 実装上は動くが、ドキュメント上の主張と原コードの主張が一致していない

**推奨修正**:
- `signal_v2.py` の docstring を更新し、「USD_JPY/GBP_JPY 両対応、JPY クロス専用、SPEC v3 で確定」と明記
- それを SPEC v3 § 1.1 と同期させる
- もし将来 EUR_USD 等を再検討する場合は PIP_SIZE のハードコードを config 化する必要があるが、これは Phase 2'A スコープ外

---

### バグ ⑤ 【中】 `daily_block_until` 不揮発化未対応 — プロセス再起動で挙動が変わる

**証拠**:
- `KillSwitchState` (risk_manager.py L65-) は dataclass で in-memory 管理
- `daily_block_until: Optional[str]` (L73) は **プロセス再起動で消える**
- コメント L67-69:「プロセス再起動でリセットされるのは仕様 (再起動=人手介入=ヘルスチェック前提)」

**問題**:
- VPS タスクスケジューラ設定 `RestartCount=5, RestartInterval=PT5M` (`_register_spec_v3_tasks.ps1` L60) で、**プロセス障害時に自動再起動する設計**
- ところが「再起動 = 人手介入前提」と risk_manager のコメントは仮定している → **タスクスケジューラの設定とコード前提が矛盾**
- 仮に日次損失 -5% で `daily_block_until` が立った直後にプロセス障害＋自動再起動が起きると、ブロックが解けて新規発注が再開する

**RETREAT バグ ⑤「亡き者の挙動データ未活用」と同じパターン**: 「安全装置はある」が、それが想定する運用環境 (人手介入) と実環境 (自動再起動) の前提が一致していない。

**推奨修正**:
- `daily_block_until` を SQLite (`loop_health` テーブルで代替するか専用テーブル) に永続化
- プロセス起動時に「未解除の daily_block_until が DB にあれば in-memory に復元」する初期化処理を `run_loop` に追加
- それまでは VPS タスクの `RestartCount=0` に変更し「自動再起動しない」を明文化するのが最低ライン (人手介入前提を環境に強制する)

---

### バグ ⑥ 【中】 ATR を LLM プロンプトに常に N/A で渡している (Phase 0' との非対称)

**証拠**:
- `demo_loop.py` L412 で context 構築時に `"atr": None` を**強制設定**
- 理由コメント L412:「signal_v2 が ATR を返さないので None」
- ところが Phase 0' の `_cycle2_extract_signals.py` L359, L374 では `atr` を明示的に保存し LLM に渡している (raw ATR 値)
- `llm_filter.py` L142: プロンプト本体で `[シグナル情報] - ATR: {atr}` を含む
- `_fmt` 関数 (L130-132) によって None は "N/A" として文字列化されてプロンプトに入る

**構造的影響**:
- **Phase 0' で LLM が見た情報セット** (シグナル + 実 ATR 値) と **Phase 2'A で LLM が見る情報セット** (シグナル + ATR=N/A) が異なる
- LLM が ATR を判定材料として使っていた場合、confidence 分布が Phase 0' と本番でずれる可能性
- Proposal 3 の閾値 0.65 / 0.60 は **ATR 付きのプロンプトで校正された値** なので、ATR なしの本番では別の閾値が最適になる可能性
- SPEC v3 § 3.2 のプロンプトテンプレートには ATR が明記されている → ドキュメント上は「ATR を渡す」が実装は「N/A 固定」

**RETREAT バグ ② の再演**: 「自分が書いた文書 (SPEC § 3.2 プロンプト = ATR 含む) 内で認識の非対称」が発生。

**推奨修正**:
- `signal_v2.calc_atr()` を呼んで ATR を context に入れる (signal_v2 を改変せず、`process_pair` 側で計算)
- もしくは ATR をプロンプトから外し、SPEC v3 § 3.2 のテンプレートも改訂する。ただしこの場合は Phase 0' の confidence 校正が再現するか追加検証必要
- 起動前 §2.2 の再現性テスト (5 回判定で confidence ブレ < 0.1) は **本番と同じ "atr=N/A" でやらないと意味がない**

---

### バグ ⑦ 【低-中】 多重検定オーバーフィット緩和策が運用開始後に動かない

**証拠**:
- `IMPROVEMENT_META_ANALYSIS.md` § リスク評価 で 5 ビン × 7 閾値 × 5 セッション × 5 レジーム の多重検定を認めている
- 緩和策は「IS/OOS 分割」のみ。Deflated Sharpe Ratio (DSR) は §1.2 で「Phase 2'A 終了後に実施」と書いている
- 一方 `SPEC_V3.md` § 10.4 (meta) の応答で「DSR で多重検定補正後の有意性確認は Phase 2'A 終了後に実施」とも書いてある
- **問題**: Phase 2'A 30 日 で実取引 N=30〜40 件しか出ない設計なので、DSR は計算しても統計的に意味ある結果が出ない

**構造的影響**:
- 多重検定リスクの正当化として DSR 計算が約束されているが、**約束された時点で計算不能なサンプル数しか溜まらない**
- 「事後 DSR で補正します」と言ってしまうのは「約束が形だけ」=  effort heuristic (RETREAT メタ要因)
- Phase 2'B 経済性 Gate (§4.1) の「OOS trades USD≥8 / GBP≥20」も Proposal 3 の閾値の再評価には足りない (n=30 級だと PF の標準誤差が大きく、Phase 0' の PF 1.354 から ±0.4 程度の幅がある)

**推奨修正**:
- 「DSR は Phase 2'A 30 日では計算しない (n 不足)」を SPEC v3 § 12.x に明記
- 代わりに「Phase 2'A は『閾値の妥当性検証』ではなく『実約定と Phase 0' BT の乖離測定』が目的」と再定義
- 多重検定リスクは Phase 2'B 60 日延長で n=120+ 集めてから DSR 計算と明示する

---

## 三層分離の評価

SPEC v3 § 10.2 で ultra への応答として「分類器 (signal_v2 + 季節フィルタ) と LLM 補完層と confidence 閾値層は **独立した3層** で分離」と書いている。実装を見た結果:

| 層 | 独立性 | 何を検証しているか明確か | コメント |
|---|---|---|---|
| 1. 分類器 (signal_v2 + 季節フィルタ) | △ | △ | signal_v2 は単独で稼働 (改変禁止)。季節フィルタは **SPEC では含まれるが実装に存在しない** (バグ①)。よって実質的には「分類器 = signal_v2 のみ」 |
| 2. LLM 補完層 | ○ | ○ | `LLMFilter.judge()` は独立、Phase 0' プロンプトと同じ (ATR=N/A 除く、バグ⑥) |
| 3. confidence 閾値層 | ○ | ○ | `should_take_trade()` は独立、判定基準も明確 |

**評価**: 3層のうち層1がドキュメントと実装で割れている。「独立3層」の主張は実装層を見ない読者を欺く字面達成。

**SPEC v2 PoC との比較**:
- SPEC v2 PoC: 「分類器 + 戦略 + 実発注」が同居して「何を検証しているか不明」(RETREAT バグ ④)
- SPEC v3: ドキュメントは「3層分離」を宣言、実装は層1 (季節フィルタ部分) が抜け落ちている → 「宣言された分離 ≠ 実装された分離」

これは PoC 三重定義の **進化系** であり、より発見が困難な形に変形している。「文書だけ見れば分離されている」「コードだけ見れば signal_v2 → LLM → 閾値 で一見シンプル」だが、**文書とコードを突き合わせて初めて層1の欠落が見える**。

---

## 観測性評価

SPEC v2 PoC の「シグナル出てないから正常か異常か分からん」(RETREAT L26) の再演リスク評価:

| 観察対象 | 仕組み | 評価 | リスク |
|---|---|---|---|
| signal_v2 シグナル件数 | `insert_llm_judgment` で全件記録 (拒否含む) | ○ | OK |
| LLM 判定分布 (CONFIRM/NEUTRAL/CONTRADICT/REJECT/API_ERROR) | DB に記録、日次サマリでカウント | ○ | OK |
| confidence 分布 | DB に記録、日次サマリで CONFIRM 内訳 | ○ | OK |
| **抑制シグナルの仮想 PnL** | DB に「24h 後の挙動」記録なし → 後から算出が必要 | △ | 後付け計算は可能 (MT5 から M15 取得して算出) だが、**SPEC v3 にスクリプトが用意されていない**。「週次レビューで仮想 PnL を集計」(SPEC_V3.md § 8.4) が口約束 |
| 死活監視 | 1h ごとに最新判定の age を Slack 通知 | ○ | OK (Once+RepetitionInterval=PT1H、SPEC v2 ノウハウ継承) |
| キルスイッチ発火履歴 | `loop_health` テーブル | ○ | OK |
| **スプレッド推移** | 記録なし (バグ②と関連) | × | スプレッド異常検知が配線されてないので、推移そのものが記録されていない |
| **MT5 接続状態** | `process_pair` で MT5 例外をログに残すのみ、専用記録なし | △ | 接続断が頻発した場合の後追いが難しい |

**観察盲点 (バグ①と並んで重要)**: 「signal_v2 が **何件出して** **どの段階で何件落とされたか**」のパイプラインサマリが存在しない。SPEC v2 PoC 撤退後に作った `pipeline:` 1行サマリログ (memory `project_fx_pipeline_trace.md`) が SPEC v3 に継承されていない。これは「観察盲点」を防ぐために自分が作った仕組みを自分で忘れたパターン (memory `feedback_baseline_check_failure.md` と同型)。

**推奨修正**:
- `process_pair` の summary dict を「pipeline:」プレフィックスで 1行ログに出力 (memory ノウハウ継承)
- 抑制シグナル仮想 PnL 計算スクリプトを Phase 2'A 起動前に用意し、週次バッチで `data/fx_spec_v3_suppressed_pnl.csv` を出力 (口約束を仕組みに落とす)

---

## K2 残課題の構造的影響度

ユーザー指示で「K2 実装の残課題評価」として挙げられた 3 点を構造的影響度で評価:

| 残課題 | 構造的影響度 | 起動可否への影響 |
|---|---|---|
| **スプレッド異常キルスイッチ未配線** | **高** (本レビュー バグ ②) | **起動延期妥当**。SPEC § 5.2 が明示するキルスイッチ 4 トリガのうち 1 つが構造的に発火不能。Phase 2'A はデモなので致命的損失は出ないが、Phase 2'C で同じコードが動けば実害発生する。Phase 2'A 中に修正することは可 |
| **ATR が LLM プロンプトで常に N/A** | **中-高** (本レビュー バグ ⑥) | **修正後起動が望ましい**。Phase 0' BT との情報非対称 = Proposal 3 閾値の校正前提が崩れる可能性。修正コストは小 (`signal_v2.calc_atr()` を `process_pair` で呼ぶだけ) なので、起動前に直すべき。直さないなら **SPEC § 3.2 プロンプトテンプレートから ATR を外す + 再現性テストを ATR なしで実施** が代替案 |
| **`daily_block_until` 不揮発化未対応** | **中** (本レビュー バグ ⑤) | **VPS タスク `RestartCount=0` に変更で当面回避可**。Phase 2'A 中に SQLite 永続化を入れる前提なら、起動延期理由にはならない |

**統合判定**: K2 残課題のうち、バグ ② (スプレッド配線) は起動延期理由として妥当。バグ ⑥ (ATR N/A) は起動前修正が望ましい。バグ ⑤ (永続化) は当面 RestartCount=0 で運用すれば許容範囲。ただしいずれも **「字面達成」と「実質実装」の差** を示す構造例である点を強調する。

---

## 撤退時の安全性

ユーザー指示の重点項目 F の評価:

| 項目 | 評価 | コメント |
|---|---|---|
| 撤退条件 #5 トリガ後の Open Position 扱い | **× 未定義** (バグ ③) | 即時 break で MT5 にポジション残置。VPS 上で SPEC v3 全停止後に MT5 がスリッページや反転で意図しない損益を確定するリスクあり |
| LLM API 障害時 | ○ | `LLMFilter.judge()` は例外を投げず `API_ERROR` ラベル返却。`should_take_trade` で `api_error_failsafe` で取らない。連続 5 失敗で全ペアブロック (確認済) |
| VPS タスクスケジューラ罠 (PT72H) | ○ | `ExecutionTimeLimit=[TimeSpan]::Zero` で回避済 (memory `feedback_task_scheduler_execution_time_limit.md` 反映) |
| RestartCount | △ | 5 回設定。これは「障害時の自動復旧」前提だが、バグ ⑤ と組み合わせると `daily_block_until` を吹き飛ばすリスクあり |
| MT5 接続断 | △ | `process_pair` で例外捕捉してログに残すのみ、再接続ロジックなし。`Mt5Client` 側に reconnect があるかは未検証 |

**最大リスク**: **撤退条件 #5 発火後にデモ口座でポジションが浮いたまま放置される**。Phase 2'A はデモなので金銭損失は出ないが、**「全停止 = 安全」のメンタルモデルが間違っている** ことを Phase 2'C 移行前に必ず認識する必要がある。これは RETREAT バグ ⑤「亡き者の挙動データを参照せずに設定された安全装置」と同じ構造 — 「停止後の挙動」を実測検証していない安全装置。

---

## 推奨アクション

### 起動前に必須 (これを直さないと起動 OK 出せない)

1. **バグ ① の整合性回復**: SPEC_V3.md の VOLATILE フィルタ記述を実装に合わせて削除する (= NO_VOLATILE で運用すると明記する) **か** 実装に VOLATILE フィルタを追加して BT を再実行する。**ユーザー判断必須**
2. **バグ ② スプレッド異常キルスイッチを配線**: 関数定義済なので `process_pair` で `Mt5Client.get_spread()` を呼んで `check_spread_anomaly` を回すだけ。コスト小、影響大
3. **バグ ③ 撤退発火時の close_all_positions 追加**: `evaluate_safety` が `retreat_5` を返した場合に `client.close_all_positions()` を呼ぶ。10 行程度の追加

### Phase 2'A 開始 1 週間以内に修正 (運用しながら直せる)

4. **バグ ⑥ ATR を LLM プロンプトに渡す**: `signal_v2.calc_atr()` を呼んで `context["atr"]` に渡す。もしくはプロンプトから ATR を抜く
5. **バグ ④ signal_v2.py docstring を SPEC v3 に同期**: 「USD_JPY/GBP_JPY 両対応、JPY クロス専用、SPEC v3 確定」と書き換え
6. **観察性**: pipeline 1行サマリログを `process_pair` summary dict から出力。memory ノウハウ継承

### Phase 2'A 中に進める (運用継続して問題なし)

7. **バグ ⑤ `daily_block_until` の SQLite 永続化**: VPS タスクの `RestartCount=0` で当面回避し、永続化実装後に戻す
8. **抑制シグナル仮想 PnL 計算スクリプト**: SPEC § 8.4 の「週次レビュー」を実機能化
9. **バグ ⑦ DSR 計算を Phase 2'B 60 日延長後に明記**

### Phase 2'A 起動前に追加でやるべき事

10. **反論屋3体 (karen / ultra / pragmatist) 再査読**: 本修正反映後にもう 1 ラウンド。特に karen の Goodhart 化評価がバグ ① の発覚で再評価必要 (VOLATILE フィルタなしの GBP_JPY は別物の戦略になる)
11. **K2 (デプロイ実装) との突き合わせ**: バグ ② ③ の修正パッチが入った状態で `python -m src.spec_v3.demo_loop --dry-run --single-iter` を再実行し、retreat シミュレーションを手動でやって `close_all_positions` が呼ばれるか確認

---

## ultrathink としての総評

**SPEC v3 は SPEC v2 で発見した PoC 三重定義パターンを「3 層分離」という名前で書き直したが、構造バグの再演を完全に回避できていない**。

具体的な再演パターン:
- **バグ ① = RETREAT バグ ②「自分が書いた文書内で認識の非対称」の正確な再演** (SPEC が宣言した VOLATILE が BT にも実装にもない)
- **バグ ② = RETREAT バグ ④「PoC 三重定義」の小型版** (SPEC § 5.2 が宣言したキルスイッチ 4 トリガのうち 3 つが「字面達成、実質未実装」)
- **バグ ③ = RETREAT バグ ⑤「亡き者の挙動データ未活用」と同型** (「停止後の挙動」を実測検証せずに安全装置を設計)
- **バグ ⑤ = RETREAT メタ要因「effort heuristic」と同型** (「再起動 = 人手介入」と仮定したコードと「`RestartCount=5`」の自動運用が矛盾)
- **観察盲点 = memory `feedback_baseline_check_failure.md` の構造再演** (自分で作ったパイプラインサマリログを SPEC v3 で忘れている)

これらはいずれも**「SPEC を書いた直後の高揚状態で発生する自己一貫性崩壊」**であり、SPEC v3 全体の戦略性 (Proposal 3 の Combined PF 1.354 / OOS +0.041) を否定するものではない。**戦略の質は Phase 0' で十分に検証されている**。問題はその戦略を **どう運用環境に落とし込むか** の実装層に集中している。

判定を**「設計修正必要」(起動延期)**とする理由は、上記バグ ①〜③ が起動前に直せる範囲のものでありながら、**直さずに起動すると「Phase 2'A で何を観察したか」が後から再度争点になる**ためである。SPEC v2 PoC は「15 日間 VOLATILE 判定 0 回」で観察不能になった。SPEC v3 Phase 2'A も、バグ ① のまま走らせると「Phase 0' で見た n=2,443 母集団とは別物の母集団から実取引が出る」状態になり、Phase 2'B 経済性 Gate 判定の根拠 (Phase 0' BT との乖離測定) が成立しなくなる。

**直して、karen と pragmatist の再合意を取ってから起動するのが、Phase 2'A の検証価値を最大化する道**である。

---

## 付録: 検証で使ったコマンド

```bash
# バグ ① の証拠
python -c "import pandas as pd; print(pd.read_csv('data/signal_v2_historical_signals.csv')['pair'].value_counts()); print(len(pd.read_csv('data/signal_v2_historical_signals_gbp_jpy_no_volatile.csv')))"
# → VOLATILE 適用 GBP_JPY 216件 vs NO_VOLATILE 2443件 (11.3 倍)

grep -rn "use_volatile_filter\|GBP_JPY_CONFIG\|seasonal_detection" src/spec_v3/
# → ヒットゼロ → 実装に VOLATILE フィルタなし

# バグ ② の証拠
grep -rn "check_spread_anomaly|get_spread|baseline_spread" src/spec_v3/
# → 定義箇所のみ、呼び出しなし

# バグ ③ の証拠
grep -rn "close_all_positions|emergency_close|on_retreat|exit_open" src/spec_v3/
# → ヒットゼロ

# 24h hold-time cap の影響 (BT との乖離測定)
python -c "
import pandas as pd
df = pd.read_csv('data/_part3_input_signals.csv')
h = df['holding_minutes_first_touch'].dropna()
print('max hold:', h.max(), 'min /', '24h 超え:', (h > 1440).sum(), '/', len(h))
"
# → max 7,065 min (~5 day) / 24h 超え 15/599 = 2.5% (PF への影響は小だが SPEC との不整合あり)
```
