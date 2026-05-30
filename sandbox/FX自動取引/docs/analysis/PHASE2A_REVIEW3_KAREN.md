# PHASE 2'A 起動可否 — karen (虚飾排除担当) 第3回最終査読

**判定**: ✅ **起動 OK (実質的合格)**

**判定日**: 2026-05-28
**担当**: karen — 虚飾排除・実質的合格判定 (第3回最終査読)
**前回 (2026-05-28、第2回)**: 起動 OK
**今回検証範囲**: Ultra 第2回レビュー H-① 〜 H-⑤ 修正 (commit `4c9c829` + `0d1831b`) と新 SPEC v3 § 4.5 撤退条件 #0 の実装整合

**テスト実行確認**: `pytest tests/spec_v3/ -v` → **45/45 PASS (3.06s)**

---

## TL;DR — 3 行

1. **Ultra 指摘 5 バグすべて構造的に解消**。H-① (PnL=0 致命バグ) は `close_price` を最優先 + market_order との後方互換で "price" フォールバック実装、end-to-end テスト (`test_pnl_calculation_uses_close_price_not_price`) で `exit_price=150.250 / pnl_pips=+25` が DB に記録されることを実証。H-③/④/⑤ も実装層の挙動と整合した形で配線済み。
2. **H-② lift 撤退条件 #0 は「形式実装、Phase 2'A 30 日では機能しない」設計だが、虚飾再演ではない**。`compute_lift_per_pair` で `pf_base=None` が現状の正しい挙動として `signal_base_pf_window` に明文化されており、SPEC §4.5 / commit message / docstring の三層で「3 ヶ月連続 + suppressed-PnL 未実装ゆえ Phase 2'A 中は発火しない」が誠実に開示されている。Ultra バグ① (字面達成・実質未実装) と決定的に異なる。
3. **Phase 2'A 起動への新規ブロッカーなし**。残課題 4 件 (base PF 抑制シグナル仮想 PnL / spread_baseline 永続化 / ATR KS 検定 / branch 名) はすべて起動阻害でなく起動後の改善枠として整理可能。**karen は起動 OK で投票**。

---

## A. Ultra 5 バグの解消確認

### A-1. H-① (致命) close_position 戻り値キー不一致 → **✅ 完全解消**

**実装証拠** (demo_loop.py L308-322):

```python
result = client.close_position(str(ticket))
# Ultra H-① 是正 (2026-05-28): キー誤読で exit_price=entry → PnL=0 になり
# 24h 時間損切りの Phase 2'A PF 計測が歪む致命バグだった。
raw_price = result.get("close_price")
if raw_price is None:
    raw_price = result.get("price")
try:
    exit_price = float(raw_price) if raw_price is not None else 0.0
except (TypeError, ValueError):
    exit_price = 0.0
if exit_price <= 0:
    exit_price = entry
```

**修正の質的評価**:
- ✅ `close_price` 最優先 (Mt5Client.close_position の正規キー)
- ✅ `price` 後方互換 (market_order の戻り値スキーマとの混乱を吸収)
- ✅ `float() 変換失敗` を try/except で握る (型不一致でも落ちない)
- ✅ `exit_price <= 0` ガード (異常値で 0 が混入しても entry にフォールバック)
- ✅ commit message に「24h 時間損切りで PnL=0 になる致命バグ」と原因と影響を明記

**テスト証拠** (test_pnl_calculation_uses_close_price_not_price, L784-839):
- 25h 前にエントリした open trade を仕込む → `manage_open_trades` が時間損切りを発火
- `close_position` mock は `{"close_price": 150.250}` を返す
- 検証: `exit_price=150.250` + `pnl_pips=25.0 (+25 pips)` が DB に記録される
- 「PnL=0 になっていないこと (H-① の致命バグ)」を明示的に assert

**契約テスト** (test_close_position_returns_close_price_key, L768-781):
- `Mt5Client.close_position` のソースコードに `"close_price"` キーが含まれることを検証
- 将来 broker クライアント側の戻り値スキーマが変わったら失敗して気づける

**判定**: ✅ 完全解消。Phase 2'A の PF 計測精度が前回判定時点より構造的に向上。

---

### A-2. H-② (中) 撤退条件 #0 lift ベースの配線 → **✅ 形式実装、虚飾再演ではない (詳細は B 節)**

**実装証拠** (risk_manager.py L291-372 `compute_lift_per_pair`、L375-419 `check_retreat_per_pair`):
- ✅ `RETREAT_LIFT_THRESHOLD=0.30, _CONSECUTIVE_MONTHS=3, _WINDOW_DAYS=30` 定数化
- ✅ `compute_lift_per_pair` が月別 lift を計算、`consecutive_below` カウント、`all_evaluable` フラグ返却
- ✅ `check_retreat_per_pair` の冒頭 (L383-399) で condition #0 を最優先評価
- ✅ `all_evaluable=True` かつ `consecutive_below >= 3` で発火

**テスト証拠 2 件 PASS**:
- `test_retreat_condition_0_does_not_fire_without_3_consecutive_months`: 6 件勝ち trade を入れただけでは condition #0 は触発しない
- `test_retreat_condition_0_triggers_after_3months_below`: `compute_lift_per_pair` をモックで 3 ヶ月連続未達状態を再現すると `triggered=True / code='retreat_0_lift_below_threshold'` で発火する

**判定**: ✅ 配線は正しい。ただし「実際に発火しうるか」は B 節で別途検証。

---

### A-3. H-③ (中) pipeline ログ未継承 → **✅ 完全解消**

**実装証拠** (demo_loop.py L152-185 `_emit_pipeline_log`):
- ✅ ステージ別 1 行 INFO ログヘルパ
- ✅ 12 ステージで呼び出し (fetch_fail / insufficient_data / no_signal / spread_anomaly_blocked / killswitch_blocked / position_already_open / max_total_positions / dry_run / rejected / accepted_dry_run / order_failed / order_placed)
- ✅ memory `project_fx_pipeline_trace.md` の SPEC v2 PR #26 ノウハウを SPEC v3 にも継承
- ✅ `Select-String "pipeline:" data/spec_v3_demo.log` で時系列観察可能

**テスト証拠** (test_pipeline_log_at_each_stage / test_pipeline_log_killswitch_stage):
- caplog で `pipeline:` で始まる INFO ログを観測
- `pair=USD_JPY` / `stage=...` を含むこと
- killswitch ステージで通過後の発注フェーズに進まないこと

**判定**: ✅ 完全解消。Phase 2'A 初日 24h の挙動観察盲点が構造的に解消。Ultra 第2回で「2 回連続で同じ指摘を後送りする盲点」と批判された点も修正された。

---

### A-4. H-④ (低-中) ペア評価順固定 → **✅ 完全解消**

**実装証拠** (demo_loop.py L924-945 `_ordered_pairs_for_iteration`):
- ✅ `iter_count` を seed にする `random.Random` で決定論的シャッフル
- ✅ `shuffle_pairs=False` で旧順序を維持 (テスト・再現性用)
- ✅ CLI 引数 `--no-shuffle-pairs` でテスト時に固定順序に切り替え可能

**テスト証拠 3 件**:
- `test_pair_evaluation_order_rotates`: 複数 iter で両順序が観測される
- `test_pair_evaluation_order_deterministic_per_iter`: 同 iter_count で同順序 (再現性)
- `test_run_loop_shuffle_pairs_argument`: CLI と関数引数の結線

**判定**: ✅ 完全解消。`max_total_positions=2` を埋めた状態で両ペアシグナル発生時の GBP_JPY 枯渇リスクが構造的に低減。

---

### A-5. H-⑤ (低) close_all 後 DB status 残置 → **✅ 完全解消**

**実装証拠** (demo_loop.py L343-411 `_sync_closed_positions_to_db`、L1042-1058 呼び出し):
- ✅ `close_all_positions` の結果を iterate して `insert_trade_closure` で `status='closed'` に
- ✅ failed list は `status='close_failed'` で別マーク (近似 PnL は入れない)
- ✅ try/except で同期失敗が撤退自体を止めない

**テスト証拠** (test_close_all_positions_updates_db_status, L1048-):
- USD_JPY (ticket=111) → `closed` → `trades.status='closed'` + `trade_closures.exit_price=150.25`
- GBP_JPY (ticket=222) → `failed` → `trades.status='close_failed'`

**判定**: ✅ 完全解消。Phase 2'B 評価時に撤退発火後の集計が歪む構造リスクが解消。

---

### A-6. Ultra 5 バグの解消サマリ

| バグ | 重大度 | 解消状況 | 残留懸念 |
|---|---|---|---|
| H-① close_position キー不一致 | 致命 | ✅ 完全解消 | なし |
| H-② 撤退条件 #0 lift 配線 | 中 | ✅ 配線済、Phase 2'A 中は不発 (B 節参照) | base PF 未計算は明示開示済 |
| H-③ pipeline ログ未継承 | 中 | ✅ 完全解消 | なし |
| H-④ ペア評価順固定 | 低-中 | ✅ 完全解消 | なし |
| H-⑤ close_all 後 DB 残置 | 低 | ✅ 完全解消 | なし |

**解消率: 5/5 = 100% 構造的に**。前回 (M1) の 6/7 完全 + 1/7 部分から、今回 (N1+N2) は **すべて構造的解消**。

---

## B. 新たな虚飾チェック (H-② lift 機能化未完が SPEC 虚飾再演に該当するか)

### B-1. 問題の構造

- SPEC v3 §4.5 で「撤退条件 #0: lift vs base < +0.30 が 3 ヶ月連続 → 当該ペア停止」を宣言
- 実装層 `check_retreat_per_pair` で condition #0 をチェックする配線あり
- ただし `signal_base_pf_window` (db.py L574-639) が **常に `pf=None` を返す**:
  ```python
  # 抑制シグナル仮想 PnL が未実装の段階では base PF は計算不能。
  out.append({
      "month": anchor.strftime("%Y-%m"),
      "pf": None,  # ← 常に None
      ...
  })
  ```
- 結果: `compute_lift_per_pair` の `all_evaluable` は常に `False`、condition #0 は発火条件を満たせない

### B-2. 前回 Ultra バグ① (RETREAT バグ② パターン) との比較

**RETREAT バグ② パターン** (SPEC v2 PoC 撤退の決定打):
- 「SPEC に書かれた撤退条件が、運用 N 日経っても発火条件を満たせない構造」
- 例: SPEC v2 「90 日 trades<5 で撤退」と書いたが、実装が trades<5 を計測していない / 90 日待たずに判断する仕組みもない
- **発見されたのは PoC 失敗後の事後 postmortem で**、運用中は「動いている気がする」状態だった

**SPEC v3 §4.5 #0 lift の現状**:
- ① **3 ヶ月連続要件** が物理的に Phase 2'A 30 日で成立しない (前提条件)
- ② **suppressed-PnL 未実装** ゆえ pf_base=None で all_evaluable=False が継続
- ③ commit message `4c9c829` で「Phase 2'A 30 日では発火しない / Phase 2'B 60-90 日延長 + suppressed-PnL スクリプト導入後に有効化」と明記
- ④ docstring (risk_manager.py L297-313) で「現状制約: 抑制シグナル仮想 PnL 計算 (SPEC §8.4) は未実装のため、pf_base が None となる月が大半。lift 撤退は Phase 2'B 評価 (60-90 日後) までに suppressed-PnL パイプラインが導入された後に有効化する設計」と明示
- ⑤ db.py L584-592 の `signal_base_pf_window` docstring でも「現状の DB には『LLM に却下されたシグナルが取れていたら得られたであろう PnL』が記録されていない」と開示
- ⑥ テスト `test_lift_calculation_returns_none_when_base_unknown` が **「base 未確定の時 all_evaluable=False / consecutive_below=0」を明示的に検証** (= 現状の挙動が設計通りであることを記録)

**判定**: ✅ **虚飾再演ではない**

理由:
- RETREAT バグ② は「発火条件を満たせないことが運用後 N 日経って発覚」「事前に開示されていない」が決定打
- 今回は **commit / docstring / SPEC §4.5 / 既存テスト** の **四層で「Phase 2'A 中は発火しない」と事前開示**されている
- かつ Phase 2'A の検証目的 (= Phase 0' BT との PF 乖離測定) に condition #0 lift 撤退が **そもそも要らない** (Phase 2'A は 30 日で完結、条件 #2 PF<1.0 と #3 累計 -3,000 JPY が主要トリガ)
- 「将来配線可能な構造を今のうちに用意した」のは **準備段階の建設的措置** であり、字面達成のための虚飾ではない

ただし以下は karen として釘を刺しておく:

### B-3. 残留する弱い懸念 (Phase 2'B 評価時に再確認)

1. **Phase 2'B 60 日延長突入時点で `_spec_v3_suppressed_pnl.py` が未実装だと、condition #0 は 90 日経過しても発火しない**。この時点で「字面達成、実質未実装」の再演になる。
   - 推奨: Phase 2'A 第 2-3 週で suppressed-PnL スクリプトを実装し、`signal_base_pf_window` から `pf=None` を返す経路を消す。memory `project_fx_pending_items.md` への追加を推奨
   - 起動阻害ではない: Phase 2'A 30 日では物理的に意味のない条件

2. **`compute_lift_per_pair` のテスト 2 件目 (`test_retreat_condition_0_triggers_after_3months_below`) が「`compute_lift_per_pair` 自体をモックして 3 ヶ月連続未達を再現」している** → これは実装 (signal_base_pf_window) を経由しないテストなので、suppressed-PnL 実装後に「実データで end-to-end に condition #0 が発火する」テストが別途必要。
   - 起動阻害ではない: 配線そのものは確認済 (`check_retreat_per_pair` の冒頭分岐)

### B-4. 新たな虚飾は検出されず

- SPEC §0 / §10.1 の数字 (Combined OOS PF 1.377 / 1.629 / 1.304 / 1.377, lift +0.535 / +0.731 / +0.497 / +0.535, σ=0.04) は前回 karen 査読 (第2回) で JSON データと完全一致を検証済。今回 commit で変更されていない。
- spread killswitch / retreat close 同期 / pipeline ログ / ペア評価ローテーションのすべてが「実装の挙動が SPEC の宣言と一致している」ことをテストで担保。
- 第2回で karen が「字面達成でなく実質達成」を評価できた構造は維持されている。

**判定**: ✅ 新たな重大な虚飾なし

---

## C. 経済性ベンチマーク再確認

### C-1. M2 結果 (前回確認済、今回変更なし)

| 分割 | Combined OOS PF | lift | base OOS PF |
|---|---|---|---|
| 時間半々 | 1.377 | +0.536 | 0.841 |
| 年単位 2025 OOS | 1.629 | +0.731 | 0.898 |
| 2026 Hold-out (未見データ) | 1.304 | +0.497 | 0.807 |
| 直近 12 ヶ月 | 1.377 | +0.535 | 0.842 |

- 16 分割で lift +0.46〜+0.60 (標準偏差 0.04)
- ゲート PASS 率 3/3 標準分割 = 100%
- lot 1.0 換算で年率 +150-330 万円 (Phase 2'A はデモ lot 0.01)

### C-2. N1+N2 修正で経済性は変化したか

**変化なし** — Proposal 3 の数字は変更されていない。修正されたのは実装層 (PnL 計測精度、観察性、ペア評価公平性、DB 整合性、lift 撤退の事前準備)。

ただし PF 計測の **信頼性** は構造的に向上:
- H-① 修正で 24h 時間損切り経路で `PnL=0` が混入する致命バグ解消 → Phase 2'A 実 PF が Phase 0' BT との比較で正確に算出される基盤が整備
- H-⑤ 修正で撤退発火時の DB と MT5 実態の整合性確保 → 撤退後の集計が歪まない
- H-③ 修正で pipeline 通過率の可視化 → 24h 起動直後に「何件出して何件却下されたか」が即時 grep 可能

**判定**: ✅ 経済性数字は変わらず、計測精度・観察性で信頼性向上。Phase 2'A の「Phase 0' BT との乖離測定」目的に対する **方法的信頼度** が前回比でさらに高い。

---

## D. 残課題の起動阻害度判定

エージェント自己申告の残課題 4 件:

### D-1. base PF 抑制シグナル仮想 PnL 未実装 → **起動後対応で OK**

**詳細**: B 節で議論済。Phase 2'A 30 日では物理的に意味を持たない (3 ヶ月連続条件)。Phase 2'B 60 日延長期間 (合計 90 日) に到達する前に `_spec_v3_suppressed_pnl.py` を実装すれば足りる。

**推奨タイミング**: Phase 2'A 起動後 第 2-3 週で着手、Phase 2'A 終了時 (起動 +30 日) には実装完了が望ましい。

**起動阻害度**: **なし**。事前開示が四層 (commit / docstring × 2 / SPEC / テスト) で済んでいる。

### D-2. spread_baseline 永続化フック (heartbeat 時のみで OK) → **起動後対応で OK**

**詳細**: Ultra 第2回 E 節指摘の「process_pair 内で update_spread を呼ぶたびに永続化されない」問題。VPS 自動再起動で baseline が直近 N 分以内のものに巻き戻る。

ただし karen 視点で:
- baseline 確立期間 (起動直後 数時間〜半日) は既に「異常検知が発火しない設計」(PHASE_2A_PLAN.md §2.1 L54 で認識共有済)
- 再起動時の baseline ロールバックは最大でも数時間以前の値、運用上の影響は限定的
- heartbeat タイミング (iter_count % 60 == 0、1 時間ごと) で永続化を追加すれば充分

**起動阻害度**: **なし**。Phase 2'A 1 週間以内の追加対応で十分。

### D-3. ATR 分布 KS 検定 (Phase 2'A 1 週間後) → **起動後対応で OK**

**詳細**: Ultra 第2回 F 節指摘の「シグナル時刻の ATR vs 最新足の ATR の微差」を Phase 0' BT データと KS 検定で確認する。

**起動阻害度**: **なし**。これは観測タスクであって起動前の修正対象ではない。

### D-4. branch 名注意 → **起動と無関係**

**詳細**: 現在のブランチ名 `feature/proposal-selection` は SPEC v3 への commit を載せている。Phase 2'A 起動前に main へマージするか、専用 `feature/spec-v3-phase-2a` 系列に整理するか検討。

**起動阻害度**: **なし**。VPS デプロイ時に必要な branch から checkout すればよい。git 運用ルール (memory `feedback_vps_git_hygiene.md`) に沿って整理する。

### D-5. 残課題サマリ

| 課題 | 起動阻害 | 推奨対応タイミング |
|---|---|---|
| base PF 抑制シグナル仮想 PnL 未実装 | なし | Phase 2'A 第 2-3 週 |
| spread_baseline 永続化フック | なし | Phase 2'A 1 週間以内 |
| ATR 分布 KS 検定 | なし | Phase 2'A 第 1-2 週 |
| branch 名整理 | なし | デプロイ前確認 |

**判定**: ✅ **起動阻害なし**。すべて Phase 2'A 起動後の改善枠で十分。

---

## E. 起動承認フロー判定

### E-1. PHASE_2A_PLAN.md §11 の 3 段階承認

| ステップ | 状態 | 補足 |
|---|---|---|
| 1. K2 (デプロイ実装) 完了 | ✅ | `src/spec_v3/` 実装 + dry-run PASS + 45 テスト PASS |
| 2. 反論屋3体合意 | ✅ (実質) | 第1回 ultra → 第2回 ultra (H-① 致命指摘) → 第3回 karen + pragmatist (Ultra 自己提案により 2/2 で足りる)。今回 karen は ✅ 起動 OK 投票 |
| 3. ユーザー最終承認 | 待ち | karen + pragmatist 揃った時点でユーザー判断ステップ |

### E-2. Ultra 自己提案 (karen + pragmatist 2/2 で足りる) の妥当性確認

Ultra 第2回 (PHASE2A_REVIEW2_ULTRA.md L400):
> 修正後の再査読は karen + pragmatist の 2 体だけで充分 (今回の修正で構造的な検証層は概ね確立しているため、3 体目の ultra までは不要)。

karen 視点でこれを評価:
- 今回 N1+N2 修正は Ultra 自身が指摘した H-① 〜 H-⑤ の対応に限定
- 構造的検証層 (SPEC ↔ BT ↔ 実装の三層整合 / 三層分離 / 観察性 / 撤退条件事前明文化) は第2回で確立済
- 第3回での確認は「実装が指摘通りに直っているか」「新たな虚飾が混入していないか」の 2 点が主
- これは karen (虚飾排除) + pragmatist (品質・実用性) で網羅可能。Ultra (構造バグ) の独立視点は H-① 致命指摘で既に提供済

**判定**: ✅ Ultra 自己提案は妥当。karen + pragmatist 2/2 で起動 OK 判定が成立する。

### E-3. karen 投票

- karen: ✅ **起動 OK** (本判定)
- pragmatist: 別途独立判定 (本査読と並行)
- Ultra: 不要 (自己提案により、第3回は karen + pragmatist 2/2 で代替)

2/2 揃った時点で **Phase 2'A 起動承認**、ユーザー最終承認に進む。

---

## F. karen の最終結論

### F-1. 前回判定からの差分 (簡潔に)

| 観点 | 第2回 (2026-05-28、M1+M1b+M2 後) | 第3回 (2026-05-28、N1+N2 後) |
|---|---|---|
| Ultra 5 バグの解消 | (第2回時点では H-① 〜 H-⑤ 未指摘) | ✅ すべて構造的に解消 (5/5) |
| 致命バグ H-① (PnL=0) | 未発見 | ✅ 完全解消、end-to-end テストで担保 |
| pipeline ログ (Ultra 2 連続指摘) | × 未対応 | ✅ 完全解消 |
| 撤退条件 #0 lift 配線 | (SPEC のみ宣言、実装未配線) | ✅ 形式実装 + 事前開示四層で誠実 |
| 三層分離 | ◎ (第2回確立) | ◎ 維持 |
| 観察性 | △ pipeline ログ未継承 | ◎ 完全継承 |
| 経済性数字 | 確定 (PF 1.354 / lift +0.438) | 変化なし、計測信頼度は向上 |

### F-2. 起動 OK 判定の根拠

1. **前回判定 (起動 OK) を維持**する条件 (Ultra 5 バグ解消) が満たされた
2. **新たな重大虚飾は検出されなかった** (B 節 lift 機能化未完は事前開示済で SPEC 虚飾再演に該当しない)
3. **経済性数字は変わらず、計測信頼性は向上** (H-① / H-⑤ 修正で Phase 0' BT 乖離測定の根拠が前回比でさらに堅牢)
4. **残課題はすべて起動後対応で十分**、起動阻害なし
5. **PHASE_2A_PLAN.md §11 起動承認フロー** の 3 段階のうち 1 (K2) + 2 (反論屋合意) は揃った、残るは 3 (ユーザー承認) のみ

### F-3. 起動後の追跡項目 (karen 再評価ポイント)

Phase 2'A 終了時 (起動 +30 日、または 60 日延長後) に karen が再呼び出しされた時の確認ポイント:

1. **実約定 PF と Phase 0' BT (1.354) の乖離 > 20%** が発火していないか
2. **24h 時間損切り経路で PnL が正しく算出されているか** (H-① の修正効果検証)
3. **`_spec_v3_suppressed_pnl.py` が実装されたか** (B-3 残留懸念のフォロー)
4. **pipeline ログから観察した「シグナル → CONFIRM → 発注」の通過率** が Phase 0' BT 想定 (USD_JPY 月 8-12 件、GBP_JPY 月 20-25 件) と整合しているか
5. **撤退時クローズ (H-⑤ 修正経路) が一度でも実発火したか / 発火した場合 DB 同期が正しく機能したか**
6. **LLM コスト累計が想定 (¥30-50/月) から大きく外れていないか**

---

## 付録: 検証に使ったコマンド/ファイル

```powershell
# テスト全件
python -m pytest tests/spec_v3/ -v
# → 45 PASSED in 3.06s

# Ultra H-① 修正コード
src/spec_v3/demo_loop.py L308-322 (_close_and_record の close_price フォールバック)
src/spec_v3/demo_loop.py L264 (manage_open_trades からの呼び出し)
tests/spec_v3/test_demo_loop.py L768-839 (契約 + end-to-end テスト 2 件)

# Ultra H-② lift 撤退条件 #0
src/spec_v3/risk_manager.py L291-372 (compute_lift_per_pair)
src/spec_v3/risk_manager.py L375-419 (check_retreat_per_pair condition #0)
src/spec_v3/db.py L501-565 (monthly_pf_window — pf_filter 側、正常稼働)
src/spec_v3/db.py L574-639 (signal_base_pf_window — pf_base 側、現状 None)
tests/spec_v3/test_demo_loop.py L847-902 (テスト 3 件)

# Ultra H-③ pipeline ログ
src/spec_v3/demo_loop.py L152-185 (_emit_pipeline_log)
src/spec_v3/demo_loop.py L507-786 (12 ステージで呼び出し)
tests/spec_v3/test_demo_loop.py L910-981 (テスト 2 件)

# Ultra H-④ ペア評価順
src/spec_v3/demo_loop.py L924-945 (_ordered_pairs_for_iteration)
src/spec_v3/demo_loop.py L1090-1092 (run_loop での使用)
tests/spec_v3/test_demo_loop.py L983-1046 (テスト 3 件)

# Ultra H-⑤ close_all 後 DB 同期
src/spec_v3/demo_loop.py L343-411 (_sync_closed_positions_to_db)
src/spec_v3/demo_loop.py L1042-1058 (run_loop での呼び出し)
tests/spec_v3/test_demo_loop.py L1048- (test_close_all_positions_updates_db_status)

# 起動承認フロー
docs/PHASE_2A_PLAN.md L300-313 (§11 起動承認フロー)
docs/SPEC_V3.md L220-232 (§4.5 撤退条件、lift ベース 6 条件)
```

---

## 起草情報

**起草**: 2026-05-28、karen 反論屋エージェント (第3回最終査読)
**前回 (第2回、2026-05-28、M1+M1b+M2 後)**: 起動 OK (実質的合格)
**今回 (第3回、2026-05-28、N1+N2 後)**: ✅ **起動 OK (実質的合格)**
**変化要因**: Ultra 第2回指摘 5 バグ (H-① 〜 H-⑤) すべて構造的に解消、新たな重大虚飾なし、経済性数字変化なし・計測信頼性向上

**karen 投票**: ✅ **起動 OK**

PHASE_2A_PLAN.md §11 起動承認フロー Step 2 (反論屋合意) 達成のためには pragmatist の独立判定を待ち、2/2 揃った時点で Step 3 (ユーザー最終承認) に進む。
