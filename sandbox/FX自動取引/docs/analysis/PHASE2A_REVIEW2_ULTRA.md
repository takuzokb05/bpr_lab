# Phase 2'A 起動可否レビュー②（修正後再査読） — ultrathink (構造バグ担当)

**判定**: **設計修正必要 (起動延期)** — 前回 7 バグのうち 6 件は是正済 / 残り 1 件 (バグ⑤) は条件付き解消だが、**新たに発見した構造バグ H-① (close_position の戻り値キー不一致による PnL 取り違え) が前回バグ③以上の致命度** で Phase 2'A の検証価値そのものを毀損するため。

**査読時刻**: 2026-05-28
**査読範囲**: `docs/SPEC_V3.md` (Proposal 3 改訂版) / `docs/PHASE_2A_PLAN.md` / `docs/proposals/cycle2/STANDARD_SPLIT_REANALYSIS.md` (§1-2 を中心) / `src/spec_v3/*` 全 6 ファイル / `src/spec_v3/__init__.py` / `src/mt5_client.py` (get_spread / close_all_positions / market_order / close_position / get_positions の戻り値) / `tests/spec_v3/test_demo_loop.py` 34 件 / commit `cdcee8d` + `d18969e` の diff
**テスト実行**: `pytest tests/spec_v3/test_demo_loop.py -v` → **34/34 PASS (2.43s)**
**継承する Ultra スタンス**: 「表層 (ドキュメントの言葉) ではなく構造 (実装の挙動)」「修正の表面達成と実質達成の差を見る」

---

## TL;DR — 4 行で

1. 前回 7 バグのうち **バグ① VOLATILE 三重不整合 / バグ② スプレッド配線 / バグ③ retreat 時 close / バグ④ docstring / バグ⑥ ATR / バグ⑦ DSR は完全是正**。テスト 34 件で挙動確認済。
2. **バグ⑤ daily_block_until 永続化は部分解消**: 状態保存・復元・過去日付クリアは実装されたが、**`process_pair` 内でスプレッド異常により `blocked_pairs` に追加されるパスがないまま `spread_baseline` 更新のたびに自動保存もされていない** (運用中の baseline ドリフトが再起動で失われ、再起動直後にスプレッド異常検知が誤発火する可能性)。
3. **【最重度・新規】H-① close_position 戻り値キー不一致**: `Mt5Client.close_position` は `{"close_price": ...}` を返すが `_close_and_record` (demo_loop.py L264-265) は `result.get("price", 0)` で読んでいる → **常に `0` → `or entry` フォールバックで exit_price = entry_price** → **24h 時間損切り発火時の PnL が常に 0、Phase 2'A の PF 計測そのものが歪む**。
4. **三層分離は前回より進展、観察性は前回指摘した pipeline 1行ログが未継承**。撤退条件 #0 (lift ベース) は SPEC §4.5 で定義されたが実装 (`check_retreat_per_pair`) に未配線 — 「字面達成、実質未実装」が 1 トリガに後退して残っている。

---

## A. バグ① VOLATILE 三重不整合の解消確認 → **✅ 完全解消**

| 層 | 確認内容 | 結果 |
|---|---|---|
| SPEC v3 §1.1 (L41) | 「(廃止)」「USD_JPY も GBP_JPY も VOLATILE フィルタなしで運用」と明記 | ✅ |
| SPEC v3 §2.1 step 2 (L95-96) | 「(旧 GBP_JPY VOLATILE フィルタは Ultra バグ① 是正で削除、2026-05-27)」とコメント | ✅ |
| SPEC v3 §6 (L275) | 季節フィルタ列に「なし (Ultra バグ① 是正、Phase 0' BT データと整合)」 | ✅ |
| SPEC v3 §6.1 (L288-299) | 削除理由を「VOLATILE 適用版だと月 9 件、なし版だと月 102 件で 11.3 倍差」「Phase 0' BT 上 PF はほぼ変わらず (0.96 → 0.945)」と数字で明記 | ✅ |
| `src/spec_v3/` 実装 | `seasonal_detection` を import せず `signal_v2.generate_signal` を直接呼ぶ | ✅ |
| Phase 0' BT データ | `signal_v2_historical_signals_gbp_jpy_no_volatile.csv` 2,443 件を採用 | ✅ |

**SPEC ↔ BT ↔ 実装の三層が「VOLATILE フィルタなし」で完全整合**。RETREAT バグ② の再演リスクが構造的に解消された。**ユーザー判断 (B 案: 適用なしを採用) で整合**を取った形跡が SPEC §6.1 のメタコメントから明確に追跡可能。

**残留する弱い懸念**: SPEC §1.1 で「VOLATILE 適用版での再検証は別 SPEC で扱う (スコープ外)」と書いているが、これは **SPEC v2 PoC で「★★★★★」を取った季節判定器の永続的な棚上げ** を意味する。「将来のために残しておく」という曖昧さがあると、別 SPEC で再導入される時に同じ三重不整合が再発しうる。本起動可否には影響しないが、Phase 2'B 経済性 Gate 評価の際に「VOLATILE なしのこの戦略を正式版とする」決定を docs/RETREAT_2026-05-26.md 系列の決定ログに残すことを推奨。

---

## B. バグ② スプレッドキルスイッチ配線の解消確認 → **✅ 完全解消**

| 確認内容 | 結果 |
|---|---|
| `KillSwitchState.update_spread()` 実装 (risk_manager.py L104-132) | ✅ EMA alpha=0.1 で追従、3 倍超のサンプルは baseline 更新から除外 (汚染防止) |
| `KillSwitchState.check_spread_anomaly()` 実装 (L134-145) | ✅ baseline 未確立時は False (誤発火防止) |
| `demo_loop.process_pair` での配線 (L352-390) | ✅ **LLM 呼び出し前** に `client.get_spread(pair)` → `kill_switch.update_spread()` → `kill_switch.check_spread_anomaly()` の順で呼ばれる |
| 3 倍超時の SKIPPED 記録 (L366-378) | ✅ `llm_label="SKIPPED"`, `decision_reason="spread_anomaly"` で DB に残る |
| Slack 通知 (L380-387) | ✅ try/except で通知失敗が処理を止めない |
| `Mt5Client.get_spread()` 実装 (mt5_client.py L542-566) | ✅ pip サイズ (0.01 / 0.0001) を pair から判定 |
| テスト `test_spread_anomaly_blocks_signal` | ✅ PASS (1回目 baseline 確立 → 2 回目 3.5 倍で `stage="spread_anomaly_blocked"`) |
| テスト `test_spread_killswitch_state_methods` | ✅ PASS (baseline 未確立時 False / 3 倍ちょうど True / 異常値で baseline 不汚染) |

実装層に「字面と実質の差」は残っていない。**SPEC §5.2 が宣言する 4 トリガの実装状態は VIX/3σ が依然 stub だが、SPEC §5.2 の表自体にこれは記載済**。

---

## C. バグ③ retreat 時 close_all_positions の解消確認 → **✅ 完全解消**

| 確認内容 | 結果 |
|---|---|
| `Mt5Client.close_all_positions()` 実装 (mt5_client.py L572-626) | ✅ `Mt5ClientError` も `Exception` も catch して個別失敗で全体停止しない設計 |
| 戻り値 `{"closed": [...], "failed": [...], "total": N}` | ✅ |
| `demo_loop.run_loop` で `retreat_*` / `monthly_stop` 発火時に呼び出し (L781-808) | ✅ `daily_stop` は当日のみ停止のためクローズしない明示分岐 |
| `loop_health` テーブルに `retreat_close` イベント記録 (L792-797) | ✅ |
| 失敗時の Slack 通知 + ログ + retreat_close_failed イベント記録 (L809-817) | ✅ |
| テスト `test_retreat_closes_all_positions` | ✅ PASS (両ペアで PF<1.0 を仕込み → run_loop(single_iter=True) で `close_all_positions.assert_called_once()` + reason に "retreat" を含む) |

**1 つだけ弱点**: `close_all_positions` 呼び出しの後に **DB の `trades.status`** を `closed` に更新する処理がない。MT5 側では決済されているが、SPEC v3 DB の `trades` テーブルは `status='open'` のまま残置される。次回起動時 (= 撤退後の人間判断による再起動時) に `manage_open_trades` がこれら trades を「まだオープン」として扱い、`mt5_ticket_map` に存在しないことから即 `_record_closure_from_history` を呼び出して **現在価格で近似 PnL を計算** → 撤退時の実 exit_price と乖離した PnL が DB に書き込まれる。Phase 2'A 30 日中に撤退が起きなければ顕在化しないが、Phase 2'C 本番で撤退条件 #5 発火時に **撤退時 PnL の事後集計を歪める** ので、Phase 2'B 評価期間中に追加修正を入れるべき。**バグ③ の解消判定は維持** (撤退発火時にポジションが市場に晒され続ける問題そのものは解決済)。

---

## D. バグ④ signal_v2 docstring 問題の解消確認 → **✅ 完全解消**

| 確認内容 | 結果 |
|---|---|
| SPEC v3 §1.1 表 ベース戦略行 (L40) | ✅ 「docstring が『GBP_JPY 専用、placeholder』だが SPEC v3 では USD_JPY/GBP_JPY 両ペアに適用 (JPY クロス pip size 0.01 共通、ロジック改変不要)」と明示 |
| signal_v2.py 本体 (`src/spec_v2/signal_v2.py` L1-26) | docstring は「GBP_JPY 専用、placeholder」のまま (改変禁止) |

「改変禁止のルールを守りつつ SPEC v3 側で乖離を明文化する」という解決アプローチで、原則と整合性が両立している。前回指摘した「ドキュメント著者 (signal_v2.py docstring) と SPEC 著者の食い違い」は SPEC §1.1 で**事実として認識・記録**された。文書同士の認識非対称は解消。

---

## E. バグ⑤ daily_block_until 永続化の解消確認 → **⚠️ 部分解消 (運用上の盲点が 2 つ残る)**

| 確認内容 | 結果 |
|---|---|
| `db.kill_switch_state` テーブル (db.py L144-152) | ✅ シングルトン (id=1 固定) で daily/monthly/blocked_pairs/global_block_reason/spread_baseline を永続化 |
| `save_killswitch_state()` / `load_killswitch_state()` (db.py L532-619) | ✅ UPSERT、blocked_pairs は JSON list、spread_baseline は JSON dict |
| `demo_loop._restore_killswitch_state()` (L594-634) | ✅ 起動時に呼ばれ、過去日付の daily/monthly はクリア (今日/当月のものだけ復元) |
| `demo_loop._persist_killswitch_state()` (L579-591) | ✅ 例外を debug ログで吸収 (致命でない) |
| `evaluate_safety` の daily_stop / monthly_stop 時に永続化呼び出し (L662, L669) | ✅ |
| テスト `test_killswitch_state_persist_and_restore` | ✅ PASS |
| テスト `test_killswitch_state_old_dates_not_restored` | ✅ PASS (yesterday/last_month は復元しない) |

**残留する盲点 1 (運用上のリスク中)**: **`spread_baseline` の更新時は永続化されていない**。
- `process_pair` 内で `kill_switch.update_spread(pair, current_spread)` (L354) を毎ループ呼ぶたびに baseline が EMA で動くが、`_persist_killswitch_state` は呼ばれない。
- 結果: VPS タスクスケジューラ自動再起動 (RestartCount=5) で **直近 5 分以内の baseline がロールバック** → 再起動直後に「baseline と現在スプレッドの差」が大きい状況だと **正常スプレッドを異常と誤判定するか、逆に異常を見逃す**。
- 影響度: Phase 2'A 30 日中に MT5 側の自動再起動が発生する確率は memory `feedback_task_scheduler_execution_time_limit.md` で「PT72H 罠で停止する事例あり」とあり、無視できる頻度ではない。
- 推奨修正: `process_pair` の最後 (return 前) または `run_loop` の `iter_count % 60 == 0` の heartbeat タイミングで `_persist_killswitch_state(kill_switch)` を呼ぶ。

**残留する盲点 2 (運用上のリスク低)**: **`block_pair()` (L163-165) と `unblock_pair()` (L171-173) が呼ばれた後にも永続化が走らない**。
- 現状 `block_pair()` を呼んでいる呼び出し元は spec_v3 コードベースに存在しない (`grep block_pair src/spec_v3/` で risk_manager.py 内の定義のみ)。
- VIX/3σ トリガが未実装のため、Phase 2'A では未使用関数だが、Phase 2'B で配線した時に永続化漏れに気づかないリスクあり。
- 推奨修正: `block_pair` / `unblock_pair` / `unblock_global` 内で `_persist_killswitch_state` を呼ぶか、`KillSwitchState` の状態変更メソッドに永続化フックを集約する。

**判定**: バグ⑤ の核心 (daily_stop が再起動で吹き飛ぶ) は解消だが、**「永続化すべき状態の網羅性」が未完成**。本起動可否を変えるレベルではないが、Phase 2'A 中に修正すべき項目。

---

## F. バグ⑥ ATR を LLM プロンプトに渡す解消確認 → **✅ 完全解消**

| 確認内容 | 結果 |
|---|---|
| `llm_filter.calc_atr()` 実装 (llm_filter.py L55-82) | ✅ signal_v2 と同等ロジック (TR の rolling mean、period=14)、None フォールバック |
| `demo_loop.process_pair` で `atr_value = calc_atr(m15_df)` (L450) | ✅ LLM context 構築前に計算 |
| `build_context` の signal dict に atr 格納 (L460) | ✅ |
| `build_user_prompt` で `- ATR: {_fmt(atr)}` (llm_filter.py L176) | ✅ None 時は "N/A" だが、calc_atr が値を返せば数値が入る |
| `insert_llm_judgment` の atr 列に値を記録 (L492) | ✅ DB ミラー |
| テスト `test_calc_atr_returns_finite_value` | ✅ PASS |
| テスト `test_calc_atr_returns_none_when_insufficient` | ✅ PASS (5 本のみで None) |
| テスト `test_atr_in_llm_prompt` | ✅ PASS (`captured_context["atr"] > 0` + `"- ATR: N/A" not in prompt` + DB の atr 列に値) |

**Phase 0' との情報対称性が完全に確立**。RETREAT バグ② の再演リスク解消。

**Phase 0' との微妙な差 (要監視、起動可否には影響しない)**: `_cycle2_extract_signals.py` の ATR 値は **シグナル時点の m15 終値時点の ATR** だが、`demo_loop.process_pair` の `calc_atr(m15_df)` は **最新足の ATR** を計算する。M15 200 本のうちシグナルが直近足で出るパターンが多ければ差は小さいが、`signal_v2.generate_signal` が過去足でシグナルを返した場合に時刻が一致しない可能性。Phase 2'A 開始 1 週間で `llm_judgments.atr` 分布を Phase 0' の `atr` 分布と比較し、外れていなければ問題なし。

---

## G. バグ⑦ DSR 評価条件の解消確認 → **✅ 完全解消**

| 確認内容 | 結果 |
|---|---|
| SPEC v3 §9.3 「DSR 評価条件」(L388-391) | ✅ 「n ≥ 100 または Phase 2'B 60 日延長終了時」と明記。Phase 2'A 30 日 (n=30-40) では計算しないと明示。代替評価として「IS/OOS 乖離 ≤ 20%」を併記 |
| SPEC v3 §10.4 meta 応答 (L485) | ✅ 同条件を反映 |
| PHASE_2A_PLAN.md §4.2 (L138-148) | ✅ 加点ゲート表に「評価タイミング」列追加。DSR の評価タイミングは「n ≥ 100 または Phase 2'B 60 日延長終了時」、Sortino / 連敗最長 / キルスイッチ動作回数は「Phase 2'A 終了時 (n=30-40)」と区別 |
| commit `d18969e` (`docs(spec-v3): DSR 評価条件を n≥100 or Phase 2'B 終了時に修正`) | ✅ 経緯・代替評価を commit message に明記 |

「effort heuristic」(約束された時点で計算不能な約束) の構造再演リスクは解消。

---

## H. 新たに発見した構造バグ

### H-① 【**最重度・新規**】 close_position 戻り値キー不一致による exit_price 取り違え

**証拠**:

- `Mt5Client.close_position` (mt5_client.py L425-430) の戻り値:
  ```python
  return {
      "trade_id": trade_id,
      "realized_pl": pos.profit,
      "close_price": result.price,   # ← キーは "close_price"
      "comment": result.comment,
  }
  ```

- `demo_loop._close_and_record` (demo_loop.py L264-265):
  ```python
  result = client.close_position(str(ticket))
  exit_price = float(result.get("price", 0)) or entry   # ← "price" を探している
  ```

- `result.get("price", 0)` は `close_position` の戻り dict に `"price"` キーが**ない**ため常に `0` を返し、`0 or entry` で **常に `entry_price` にフォールバック**する。

**影響**:

- `_close_and_record` は `MAX_HOLDING_MINUTES=24*60=1440` 分経過時の**時間損切り**経路 (manage_open_trades L242-245) で呼ばれる
- `_calc_pnl` (L193-209) は `exit_price - entry` (long) または `entry - exit_price` (short) で pips を計算するため、**exit_price = entry_price なら pips=0、pnl_jpy=0**
- 結果: **24h 時間損切りで決済された trade はすべて PnL=0 として DB に書き込まれる**
- Phase 2'A 30 日で 24h 時間損切りに掛かる trade は (Phase 0' BT で hold_time > 24h が 2.5% 程度) Phase 0' の母集団分布をそのまま当てると約 1 件 / 月だが、**Phase 0' BT は 24h cap を設けていない**ため Phase 2'A の実約定で初めて時間損切りに掛かる trade の割合が上振れする可能性があり、最大で trade の 10-30% が 24h 経過で決済されうる
- **Phase 2'A の PF 計測そのものが歪む**: 時間損切り trade の PnL がすべて 0 として記録されると、PF = wins / losses の分子・分母に偏った影響が出る (損失方向に寄っている trade が 0 にされると PF が見かけ上良くなる)

**根本原因 (RETREAT バグ② パターンの再々演)**:

- `Mt5Client` (汎用 broker クライアント) は `close_price`、`market_order` は `price` を返す。**この命名の非対称が SPEC v3 実装者に伝わっていない**
- demo_loop.py L264 は `market_order` の戻り値 (`price`) と同じパターンで書かれているが、`close_position` は別のキーを使っている
- 結果: **「自分が呼んでいる関数の戻り値スキーマを実装者が誤解した」型のバグ**

**推奨修正** (5 行):
```python
# demo_loop.py L263-268 を以下に変更:
try:
    result = client.close_position(str(ticket))
    # Mt5Client.close_position は "close_price" を返す (market_order は "price")
    exit_price = float(result.get("close_price") or result.get("price") or entry)
except Exception as e:
    logger.error("close_position 失敗 ticket=%d: %s", ticket, e)
    exit_price = entry
```

**テストカバレッジ不足**: `test_demo_loop.py` の `test_retreat_closes_all_positions` は `mt5_mock.close_all_positions.return_value` を `{"closed": [...]}` でモックしているが、これは `Mt5Client.close_all_positions` を mock しており **`Mt5Client.close_position`** (`_close_and_record` 経由で `manage_open_trades` から呼ばれる) は test カバレッジから外れている。**「24h 時間損切り → close_position → exit_price 計算 → PnL 計算」のフローを通すテストが存在しない**。

**判定**: 起動延期理由として十分。Phase 2'A は「Phase 0' BT との乖離測定」が主目的であり、**PnL 計測が歪むと検証目的そのものが達成できない**。前回バグ③「停止後の挙動データ未活用」と同じ構造 — 「PnL 計算経路を実機で通したことがない (テストでも通したことがない)」。

---

### H-② 【中】 撤退条件 #0 (lift ベース) が SPEC で定義されたが実装に未配線

**証拠**:

- SPEC v3 §4.5 (L223-231) 撤退条件表に追加された新条件:
  ```
  | 0 | lift vs base < +0.30 が 3 ヶ月連続 (M2 提案、絶対水準より lift が安定) | 当該ペア | 当該ペア停止 |
  ```
- `risk_manager.check_retreat_per_pair` (L280-315) は条件 1/2/3 のみチェック、条件 #0 (lift) を実装していない
- `grep "retreat_0|lift" src/spec_v3/` ヒットゼロ
- `check_retreat_system_wide` (L333-349) も #1-3 ベースで判定するため、lift 撤退が発火しない

**影響**:

- SPEC §4.5 の表は条件 #0 を読者に約束しているが、**Phase 2'A 30 日では「3 ヶ月連続」が物理的に成立しない**ためテストでも顕在化しない
- Phase 2'B 経済性 Gate 評価時 (60 日延長まで含めても 90 日) になって初めて「あれ、lift 撤退発火しないな」と気づくパターン
- これは **「字面達成、実質未実装」の縮小再演**だが、Phase 2'A 期間中は発火しないため起動可否そのものへの影響は軽微

**RETREAT バグ④ の影**: SPEC v3 §4.5 が宣言した 6 トリガ (#0-5) のうち #0 が未実装、#5 は #1-3 の組合せ判定で実装あり。**「4 トリガのうち 3 つが字面達成」(前回 §5.2 で指摘) と同じ構造を §4.5 にも持ち込んでいる**。

**推奨修正**:
- (A) `check_retreat_per_pair` に #0 (lift) を実装。`db.recent_pf` の base 版 (= `signal_v2` 単独 PF) を別関数で取得し、`(pf_after_filter - pf_base) < 0.30` が 3 ヶ月連続成立で発火させる
- (B) もしくは SPEC §4.5 の表から条件 #0 を削除し「Phase 2'B 評価時に手動チェック」と明記する (絶対水準の #2 ≥ PF 1.0 で代替)
- いずれにせよ「実装に存在する撤退条件」と「SPEC が宣言する撤退条件」を再整合させる

---

### H-③ 【中】 観察盲点 — pipeline 1 行サマリログが SPEC v3 に未継承

**証拠**:

- `process_pair` は summary dict を返すが、関数内では使われず呼び出し側 (`run_loop` L830-837) も結果を捨てている (`process_pair(mt5_client, pair, ...)` の戻り値を変数で受けていない)
- `grep "pipeline:" src/spec_v3/` ヒットゼロ
- memory `project_fx_pipeline_trace.md` 「PR #26、`Select-String "pipeline:"` で各ステージ通過/却下が時系列で見える」のノウハウが SPEC v3 にも spec_v3 コードにも継承されていない
- 観察できる代替: `loop_health` テーブルに `start/stop/error/heartbeat/kill_switch/retreat/retreat_close` が記録、`llm_judgments` テーブルに `stage` 相当の `decision_reason` 列があるので **DB クエリで後追い可能**だが、**ログファイル 1 本を tail で眺めて挙動を時系列で見る術がない**

**影響**:

- SPEC v2 PoC で発生した「シグナル出てないから正常か異常か分からん」(RETREAT L26) の再演リスクは DB クエリで部分軽減されているが、Phase 2'A 起動直後の最初の 24h で「ループは回ってるけど何も起きてない」状態の判別が現状の trading.log 構造では困難
- 死活監視 (Slack 1h ごと) は最新 1 件の age を見るだけで、各ステージの通過率を可視化しない

**推奨修正** (起動前 30 分作業):
- `process_pair` の return 前に 1 行のサマリログを出す:
  ```python
  logger.info(
      "pipeline: pair=%s stage=%s sig=%s label=%s conf=%s accepted=%s reason=%s",
      pair, summary.get("stage"), summary.get("signal_direction"),
      summary.get("llm_label"), summary.get("llm_confidence"),
      summary.get("accepted"), summary.get("decision_reason"),
  )
  ```
- これで `Select-String "pipeline:" data/spec_v3_demo.log | Select-Object -Last 100` で過去 100 イテレーションの全ペア通過/却下が即座に追える
- memory `project_fx_pipeline_trace.md` ノウハウの再活用

**判定**: 起動延期理由ではないが、Phase 2'A 開始 24h 以内に必ず入れる。前回レビューでも同じ指摘をしていたが、修正対象外として後送りされている (commit `cdcee8d` の修正 4 件には含まれない)。**自分が出した指摘を自分で忘れているパターン** (memory `feedback_baseline_check_failure.md` と同型)。

---

### H-④ 【低-中】 ENABLED_PAIRS のループ順固定で USD_JPY が常に GBP_JPY より先に評価される

**証拠**:

- `__init__.py` L22: `ENABLED_PAIRS: tuple[str, ...] = ("USD_JPY", "GBP_JPY")`
- `run_loop` L828: `for pair in enabled_pairs:` でこの順で処理
- 全体 2 ポジション上限 (`MAX_TOTAL_POSITIONS = 2`) のチェックが各ペアごとに走るため、両ペア同時にシグナルが出た iter では **USD_JPY が先に発注 → open=1、GBP_JPY もシグナル → open=1+1=2 で発注**、それぞれ問題なし
- ところが既に 1 ペア (例: USD_JPY) で open=1 の状態で **GBP_JPY と USD_JPY の両方に新規シグナルが出た iter** では、USD_JPY が「同一ペアで open あり」スキップ → GBP_JPY が `open_total=1` で発注可。この場合は OK
- 問題が顕在化するのは **全体 open=1, USD_JPY シグナルあり, GBP_JPY シグナルあり** の状況: USD_JPY が `open_pair=0, open_total=1<2` で発注 → open_total=2 → GBP_JPY が `open_total=2≥MAX` で却下。**USD_JPY 優先で GBP_JPY が枯渇する**

**影響**:

- Phase 2'A の取引機会想定: USD_JPY 月 ~8-12 件、GBP_JPY 月 ~20-25 件 (SPEC §7.1 L313)。GBP_JPY のほうがシグナル頻度が高いはずなので、**評価順固定の影響で GBP_JPY trade 数が想定より少なくなる可能性**
- 確率としては低い (両ペア同時にシグナル発生は稀) が、Phase 0' BT の n=469 GBP_JPY 母集団との乖離要因として混入

**推奨修正**:
- (A) ループごとに `enabled_pairs` をランダムシャッフル
- (B) もしくは「シグナル強度 / confidence の高い順」で評価 — ただしこれは confidence を先に計算する必要があり LLM コール 2 倍化のコスト発生
- (C) 起動可否には影響しないので Phase 2'A 中に観測し、実際に発火回数が多ければ修正検討

---

### H-⑤ 【低】 retreat 時の DB 整合性 — trades.status='open' が残置される

(C 節で既述、ここでは重大度判定のため再掲)

`run_loop` L781-808 で `close_all_positions` 呼び出し → 成功するが、DB の `trades.status` は `'open'` のまま。次回起動時に `manage_open_trades` が `_record_closure_from_history` を呼んで現在価格で近似 PnL を計算 → 撤退時の実 exit_price と乖離。

Phase 2'A 30 日で撤退が起きなければ顕在化しないが、Phase 2'B 評価時に撤退発火後の集計を歪める。

**推奨修正**: `close_all_positions` の `closed` リストを iterate して `v3_db.insert_trade_closure` を呼ぶ。reason="retreat_close"、exit_price は `close_position` の戻り値 `close_price` から取る (H-① と関連)。

---

## I. 三層分離の評価

| 層 | 独立性 | 何を検証しているか明確か | 前回からの変化 |
|---|---|---|---|
| 1. 分類器 (signal_v2 単独) | ◎ | ◎ | **前回 △ → 今回 ◎**。VOLATILE フィルタ廃止で「分類器 = signal_v2 のみ」が SPEC・実装で完全一致 |
| 2. LLM 補完層 | ○ | ○ | 前回 ○ → 今回 ○ (ATR 同期で Phase 0' との情報対称性が確立) |
| 3. confidence 閾値層 | ○ | ○ | 前回 ○ → 今回 ○ (USD_JPY 0.65、GBP_JPY 0.60 のペア別閾値が `__init__.py` で定数化) |

**SPEC v3 §10.2 で宣言した「独立3層」が、SPEC・実装・テストの全層で実態に追いついた**。前回指摘した「実装層を見ない読者を欺く字面達成」は構造的に解消。

**「何の PoC か」の明確化**: PHASE_2A_PLAN.md §0 で「Phase 2'A の目的: Phase 0' BT (PF 1.354) が実運用で再現するか / スリッページ・約定遅延・スプレッド変動の実体測定 / LLM 判定の安定性観察 / 撤退条件の妥当性確認」と明記。非目的 (本番投入 / 新戦略開発 / パラメータチューニング) も列挙。**「Phase 2'A は実発注 PoC のみ」** (Ultra 想定応答 §10.2) が PHASE_2A_PLAN.md で文書化済。

---

## J. 観測性評価

| 観察対象 | 仕組み | 評価 | 前回からの変化 |
|---|---|---|---|
| signal_v2 シグナル件数 | `insert_llm_judgment` で全件記録 (拒否含む) | ○ | 維持 |
| LLM 判定分布 (CONFIRM/NEUTRAL/CONTRADICT/REJECT/API_ERROR) | DB 記録、日次サマリでカウント | ○ | 維持 |
| confidence 分布 | DB 記録、日次サマリで CONFIRM 内訳 | ○ | 維持 |
| 抑制シグナルの仮想 PnL | DB に「24h 後の挙動」記録なし、SPEC §8.4 で「週次レビューで仮想 PnL を集計」と口約束 | △ | **前回 △ → 維持 (改善されていない)** スクリプトが未用意 |
| 死活監視 | 1h ごとに最新判定の age を Slack 通知 | ○ | 維持 |
| キルスイッチ発火履歴 | `loop_health` テーブル | ○ | 維持 |
| **スプレッド推移** | `kill_switch_state.spread_baseline_json` で baseline は永続化、各ループでの実 spread 値の時系列記録なし | △ | **前回 × → 今回 △**。baseline は保存されるが、過去推移を辿るにはログから掘る必要あり |
| MT5 接続状態 | `process_pair` で例外をログ + DB の loop_health に error 記録 | △ | 維持 |
| **pipeline 通過率** | `process_pair` の summary dict がログ未出力 (前回指摘の memory `project_fx_pipeline_trace.md` ノウハウ未継承) | × | **前回 × → 今回 ×**。修正されていない (H-③) |

**観察盲点の総括**:
- 「signal_v2 が **何件出して** **どの段階で何件落とされたか**」のパイプラインサマリログが未実装 (H-③)
- 「**撤退時の close_all_positions の各 trade 別 exit_price/PnL**」が DB に保存されない (H-⑤)
- 「**24h 時間損切り時の exit_price**」が H-① で 0 になる → そもそも観察不能

これら 3 つは「観察したいデータが取れていない」状態なので、Phase 2'A 終了時 (Phase 2'B 経済性 Gate 評価) に「PF 1.354 が再現したか」を判定する根拠が **歪んだまま提示される**。

---

## 前回 7 バグの解消サマリ

| バグ | 前回判定 | 今回判定 | 補足 |
|---|---|---|---|
| ① VOLATILE 三重不整合 | 最重度 | ✅ **完全解消** | SPEC・実装・BT が一致、ユーザー判断 (B 案) で整合 |
| ② スプレッド配線 | 高 | ✅ **完全解消** | テスト 2 件で挙動確認 |
| ③ retreat 時 close | 高 | ✅ **完全解消** | テスト 1 件で挙動確認、ただし H-⑤ (DB.status 未更新) が残る |
| ④ signal_v2 docstring | 中 | ✅ **完全解消** | SPEC §1.1 で明文化、改変禁止ルールも保持 |
| ⑤ daily_block_until 永続化 | 中 | ⚠️ **部分解消** | core 機能は OK、`spread_baseline` 更新時 + `block_pair` 時の永続化フックが欠落 |
| ⑥ ATR を LLM に渡す | 中-高 | ✅ **完全解消** | テスト 3 件で挙動確認、シグナル時刻 vs 最新足の微差は要監視 |
| ⑦ DSR 評価条件 | 低-中 | ✅ **完全解消** | SPEC §9.3 / PHASE_2A_PLAN §4.2 で n≥100 or Phase 2'B 60日終了時に統一 |

**前回バグの是正率: 6/7 完全 + 1/7 部分 = 93%**。前回ブロッカーだったバグ①〜③ は完全解消。

---

## 推奨アクション

### 起動前に必須 (これを直さないと起動 OK 出せない)

1. **H-① close_position 戻り値キー不一致を修正** (5 行)。**Phase 2'A 検証価値そのものを毀損する致命バグ**。修正パッチ:
   ```python
   # demo_loop.py L264-265
   exit_price = float(result.get("close_price") or result.get("price") or entry)
   ```
   加えて `test_close_and_record_uses_close_price_from_result` を追加 (Mt5Client.close_position の戻り値スキーマを fix した mock で `_close_and_record` を呼び、`trade_closures.exit_price` が `entry_price` でないことを検証)。

### 起動前にやるべき (1 日以内、起動価値を保つために)

2. **H-③ pipeline 1 行サマリログを追加** (process_pair の return 前に `logger.info("pipeline: ...")`)。前回レビューと今回レビューの 2 回連続で指摘されている

3. **E 節 残留盲点 1 — spread_baseline 永続化フック追加**: `process_pair` の最後または `heartbeat` タイミング (iter_count % 60 == 0) で `_persist_killswitch_state(kill_switch)` を呼ぶ

### Phase 2'A 開始 1 週間以内に修正 (運用しながら直せる)

4. **H-② 撤退条件 #0 (lift ベース) を実装するか SPEC から削除する**。Phase 2'A 期間中は発火条件 (3 ヶ月連続) を満たさないので延期可能だが、Phase 2'B 経済性 Gate 評価 (60-90 日後) までに必須

5. **H-⑤ close_all_positions 後の trades.status='closed' 同期**: `close_all_positions` の `closed` リストを iterate して `insert_trade_closure` を呼ぶ。reason="retreat_close"

6. **E 節 残留盲点 2 — `block_pair` / `unblock_pair` の永続化フック追加**

7. **抑制シグナル仮想 PnL 計算スクリプト** (`_spec_v3_suppressed_pnl.py`): SPEC §8.4 の週次レビュー口約束を仕組み化。前回レビュー指摘事項、未対応

### Phase 2'A 中に観測 (修正不要、データ蓄積)

8. **H-④ ENABLED_PAIRS 評価順による GBP_JPY 枯渇発生回数**: `loop_health` テーブルに `position_already_open` / `max_total_positions` の reason で記録される `insert_loop_health` を追加して定量化

9. **F 節 ATR 時刻ズレの監視**: Phase 2'A 開始 1 週間で `llm_judgments.atr` 分布 vs Phase 0' BT `atr` 分布の KS 検定

### Phase 2'A 起動前に追加でやるべき事

10. **反論屋3体 (karen / ultra / pragmatist) 再査読**: 本修正 (H-① + H-③ + E 節盲点 1) 反映後にもう 1 ラウンド。**H-① の修正が入っていないと karen は Goodhart 化評価のための実 PF が見えないため再査読自体が成立しない**

11. **K2 (デプロイ実装) との突き合わせ**: H-① 修正パッチ反映後に `python -m src.spec_v3.demo_loop --dry-run --single-iter` を実行し、24h 時間損切りシナリオを単体テストで pass させてから VPS デプロイ

---

## ultrathink としての総評

前回指摘した 7 バグのうち **6 件は構造的に完全解消、1 件は部分解消**。SPEC v3 ↔ Phase 0' BT ↔ 実装の三層整合は劇的に改善し、特にバグ① VOLATILE 三重不整合の解消アプローチ (SPEC を実装に合わせる B 案) は「ユーザー判断 → SPEC §6.1 でメタコメント記録 → 文書全体で一貫」の流れが正しく機能している。これは **RETREAT バグ② の再演を回避する成功事例**として記録に値する。

しかし今回新たに発見した **H-① close_position 戻り値キー不一致** は、前回の「字面達成、実質未実装」(SPEC §5.2 のキルスイッチ 4 トリガのうち 3 つが未配線) と**完全に同型の構造バグ**である。違いは:
- 前回バグ② は「SPEC で宣言、実装でゼロ」(発見しやすい)
- 今回 H-① は「SPEC で宣言なし、実装で呼んでいるが戻り値解釈を間違えている」(発見しにくい)

つまり**「字面と実質のズレ」が SPEC レベルから実装内 API レベルに降りた**。これは構造バグの**進化**であり、SPEC 整合性を担保しただけでは検出できない層のバグである。

加えて H-③ pipeline ログ未継承は **前回も今回も同じ指摘** であり、これは「自分が出した修正リストが直近 commit に反映されたかをユーザーが確認する」プロセスの盲点を示している (memory `feedback_baseline_check_failure.md` の構造再演)。

**判定を「設計修正必要」(起動延期) とする理由**:
- H-① は Phase 2'A の検証価値そのもの (= Phase 0' BT との PF 乖離測定) を毀損する
- 24h 時間損切りで決済される trade は Phase 0' BT には存在しないため、Phase 2'A で初めて発生する **未踏領域**。そこで PnL=0 が混入すると、Phase 2'B 経済性 Gate (§4.1 PF ≥ 1.30) の判定根拠が歪む
- 修正コストは 5 行 + テスト 1 件で 30 分以内に対応可能
- 直してから起動する経済性が圧倒的に高い

**修正後の再査読は karen + pragmatist の 2 体だけで充分** (今回の修正で構造的な検証層は概ね確立しているため、3 体目の ultra までは不要)。H-① 修正 + H-③ pipeline ログ追加の 2 件さえ入れば、起動 OK の判定に切り替え可能。

**「直して、karen と pragmatist の再合意を取ってから起動するのが、Phase 2'A の検証価値を最大化する道」** という前回判定は今回も維持する。前回はバグ①〜③ がブロッカーだったが、今回は H-① と H-③ (+E 節盲点 1) がブロッカーである。

---

## 付録: 検証で使ったコマンド

```bash
# テスト全件実行
python -m pytest tests/spec_v3/test_demo_loop.py -v
# → 34 PASSED in 2.43s

# H-① の証拠
grep -n "close_price\|result.price" src/mt5_client.py
# → close_position の戻り値が close_price (L425-430)

grep -n "result.get" src/spec_v3/demo_loop.py
# → L264: result.get("price", 0) → "price" キーが存在しないので常に 0

# H-② lift 撤退の未実装証拠
grep -rn "retreat_0\|lift" src/spec_v3/
# → ヒットゼロ

# H-③ pipeline ログ未継承
grep -rn "pipeline:" src/spec_v3/
# → ヒットゼロ

# E 節 spread_baseline 永続化の証拠
grep -n "update_spread\|_persist_killswitch_state" src/spec_v3/demo_loop.py
# → update_spread (L354) → _persist_killswitch_state 呼び出しなし
# → _persist_killswitch_state は L662, L669 (daily_stop, monthly_stop) のみ
```
