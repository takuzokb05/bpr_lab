# PHASE 2'A 起動可否 — karen (虚飾排除担当) 再査読

**判定**: **起動 OK (実質的合格)**

**判定日**: 2026-05-28
**担当**: karen — 虚飾排除・実質的合格判定 (前回 2026-05-27 判定 = 設計修正必要 → 修正後再判定)
**対象**: M1 (実装層バグ② ③ ⑤ ⑥ 是正) + M1b (SPEC 整合修正) + M2 (標準分割再分析) 後の SPEC v3 / PHASE_2A_PLAN / src/spec_v3 / tests

---

## TL;DR — 3 行

1. **前回重大発見 3 件すべて解消確認**。IS-OOS 虚飾は M2 標準分割再分析 (4/4 PASS、lift 安定 σ=0.04) で実質的に覆された。スプレッドキルスイッチは demo_loop.py L349-390 で完全配線、テスト `test_spread_anomaly_blocks_signal` PASS。GBP_JPY 副ペア再採用は SPEC §10.1 反論 B で「亡き者本番 PF 0.868 ≈ Phase 0' BT base PF 0.867 = signal_v2 単独でも負ける、Proposal 3 で PF 1.294 に押し上げ」と整理済。
2. **形式合格でなく実質合格**。Karen 前回指摘 (J メタ分析の per-pair-count-half 特別分割で IS<OOS 崩れる) が SPEC §10.1 反論 A で **事実として認められた上で**、16 分割全体で lift +0.46〜+0.60 が分割不変であることが正しく提示されている。「Goodhart 化なし」主張が **強い証拠で支えられた** (前回は弱い証拠だった)。
3. **新たな重大問題なし**。低重大度の小さな整合不備 (PHASE_2A_PLAN.md §6 が SPEC §4.5 撤退条件 #0 lift ベースを未反映、 `SPREAD_WARN_THRESHOLD_PIPS` がコードに残るが未使用) があるが、起動を止める理由にはならない。

これらは前回 SPEC v2 撤退の決定打となった構造バグ (撤退済再採用、★★★★★ 虚飾、経済性 Gate 不在) が **実質的に解消された** ことを意味する。**Phase 2'A 起動承認**。

---

## A. 前回発見 1 (IS-OOS 整合性主張の虚飾) — 解消確認 ✅

### A-1. M2 標準分割再分析の検証結果

`docs/proposals/cycle2/STANDARD_SPLIT_REANALYSIS.md` と `data/_standard_split_reanalysis.json` を直接読み込んで以下を確認:

**標準分割 4 方式すべてで Proposal 3 が +0.30 lift ゲート PASS**:

| 分割 | IS PF | OOS PF | base OOS | lift | G0-A | G0-B | Consistency |
|---|---|---|---|---|---|---|---|
| 時間半々 (共通カットオフ 2025-05-07) | 1.338 | 1.377 | 0.841 | **+0.536** | PASS | PASS | 102.9% |
| 年単位 (2024 IS / 2025 OOS) | 1.268 | 1.629 | 0.898 | **+0.731** | PASS | PASS | 128.5% |
| 2026 Hold-out | — | 1.304 | 0.807 | **+0.497** | PASS | PASS | — |
| 直近 12 ヶ月 | 1.338 | 1.377 | 0.842 | **+0.535** | PASS | PASS | 102.9% |

→ **3 標準分割すべて all_pass=True**、ゲート評価 `pass_rate_pct: 100.0` (JSON 検証済)。

**16 分割の選択バイアスチェック**:
- OOS PF > IS PF: 7/16 = 43.8% (Karen 前回指摘の通り IS<OOS は分割依存)
- ただし全 16 分割で lift +0.46〜+0.60 = **lift は分割不変**
- 標準偏差 0.04 (極めて安定)
- 最悪値 (trailing_6m, lift +0.460) でも +0.30 ゲートを 50% 超過 PASS

### A-2. SPEC v3 §0 / §10.1 での反映状況

**SPEC §0 TL;DR L23-29** で:
- 時間半々: Combined OOS PF **1.377** (lift **+0.536**) — JSON と完全一致 ✅
- 年単位 2025 OOS: Combined OOS PF **1.629** (lift **+0.731**) — JSON と一致 ✅
- 2026 Hold-out: Combined OOS PF **1.304** (lift **+0.497**) — JSON と一致 ✅
- 直近 12 ヶ月: Combined OOS PF **1.377** (lift **+0.535**) — JSON と一致 ✅
- 16 分割 lift 標準偏差 0.04 — 明記 ✅
- **「Karen 反論屋指摘 (J メタ分析の per-pair-count-half 特別分割で IS<OOS が崩れる現象) は事実」と SPEC 本文で認めた上で標準分割で +0.30 PASS を提示** ✅

**SPEC §10.1 反論 A 応答** で:
- Karen 前回数字 (Combined IS 1.368 / OOS 1.330 / -0.038 劣化) を **「事実として再現確認」と明示** ✅
- 16 分割の lift 標準偏差 0.04 で「base からの大幅改善」が **分割不変で必ず成立** と整理 ✅
- 「IS<OOS かどうか」は分割依存 (43.8% のみ) だが結論「Proposal 3 = ゲート PASS」は変わらない ✅
- 撤退条件 §4.5 #0 で「lift < +0.30 が 3 ヶ月連続」を停止トリガに事前明文化 ✅

### A-3. karen 評価

**判定**: ✅ **完全解消**

前回「字面の選び方による有利な数字」と指摘した点が、M2 標準分割再分析で **正面から反証** された。SPEC が選択バイアスを認めた上で標準分割の数字を採用し、lift 安定性を主軸に据え直したのは **誠実な是正**。形式的合格でなく実質的合格。

「Goodhart 化なし」の根拠が前回より **構造的に強くなった**:
- 前回: 11 閾値中 1 個を選んだ多重検定 → IS-OOS 主張で緩和 (ただし特別分割依存)
- 今回: 16 分割で lift +0.46〜+0.60 が σ=0.04 で安定 → **分割選択に依存しない edge** の証拠

これは karen 視点で「**虚飾なし**」と判定できる。

---

## B. 前回発見 2 (スプレッドキルスイッチ未配線) — 解消確認 ✅

### B-1. demo_loop.py L349-390 の配線確認

```python
# 3a. スプレッド異常キルスイッチ (Ultra/Karen バグ② 是正、2026-05-27)
current_spread = client.get_spread(pair) if hasattr(client, "get_spread") else None
if current_spread is not None:
    kill_switch.update_spread(pair, current_spread)
    if kill_switch.check_spread_anomaly(pair, current_spread):
        # ... SKIPPED 記録 + Slack 通知 + return
        summary["stage"] = "spread_anomaly_blocked"
        return summary
```

**確認項目**:
- `process_pair` 内で `client.get_spread(pair)` を呼び出し ✅
- `kill_switch.update_spread(pair, current_spread)` で EMA baseline 追従 ✅
- `kill_switch.check_spread_anomaly(pair, current_spread)` で 3 倍超判定 ✅
- 異常時は `SKIPPED` ラベルで DB (`llm_judgments` テーブル) に記録 ✅
- `decision_reason="spread_anomaly"` で識別可能 ✅
- Slack 通知 `notifier.kill_switch(...)` 呼び出し ✅
- `summary["stage"] = "spread_anomaly_blocked"` で早期 return → 後続の LLM 呼び出し+発注を完全ブロック ✅

### B-2. KillSwitchState.check_spread_anomaly / update_spread の設計確認

`src/spec_v3/risk_manager.py` L100-145 で:
- **baseline 未確立時は False を返す (誤発火防止)** L142-144 — Phase 2'A 起動直後の安全設計
- **異常値 (3 倍超) は EMA 更新からスキップ** L124-128 — baseline 汚染防止 (重要)
- EMA alpha=0.1 で緩やかに追従
- `KILLSWITCH_SPREAD_MULTIPLIER = 3.0` 定数化 (SPEC §5.2 と整合)

### B-3. テスト確認

`tests/spec_v3/test_demo_loop.py`:
- `test_spread_anomaly_blocks_signal` (L466-514) PASS ✅
  - 1 回目 1.0 pip で baseline 確立
  - 2 回目 3.5 pip で異常検知 → ブロック
  - DB に SKIPPED 記録 / market_order.assert_not_called() ✅
- `test_spread_killswitch_state_methods` (L517-544) PASS ✅
  - baseline 未確立時 False
  - 3 倍ちょうど True (境界値)
  - 異常値で update_spread しても baseline 汚染なし

**全 34 テスト PASS** (`pytest tests/spec_v3/test_demo_loop.py -v` で確認、4.95s)

### B-4. PHASE_2A_PLAN.md §2.1 のベースライン認識共有

L54: **「スプレッド異常 baseline 確立期間 (起動後 数時間〜半日) の認識共有 (この期間は異常検知が発火しない誤発火防止設計)」** が起動前チェックリストに明示 ✅

### B-5. karen 評価

**判定**: ✅ **完全解消**

前回「実装は 4 トリガ中 2 つのみ」と指摘した点が、**3 つ目 (スプレッド) が正面から配線された**。
残り 1 つ (VIX > 30 / ±3σ) は依然未実装だが、これは SPEC §5.2 で「外部データ依存のためデフォルト無効」と認識共有済 (risk_manager.py L11 コメント明記)。Phase 2'A デモ口座運用では許容範囲。Phase 2'B 経済性 Gate 判定までに実装すべき (中重大度、起動阻害要因ではない)。

CLAUDE.md「資金管理最優先」原則への抵触は **解消**。Phase 2'A 集計の精度を歪める「異常スプレッド約定の混入」リスクが構造的に排除された。

---

## C. 前回発見 3 (撤退済 GBP_JPY 副ペア再採用の自己一貫性監査) — 解消確認 ✅

### C-1. SPEC §10.1 反論 B 応答の確認

L451-456 で:
```
- 亡き者本番 GBP_JPY (n=37、PF 0.868) は MTFPullback 戦略 で、
  本仕様の signal_v2 (ATR breakout) とは別物 ✅
- Phase 0' BT GBP_JPY 全 2,443件 base PF 0.867 ≈ 亡き者本番 PF 0.868
  (ほぼ完全一致) → signal_v2 単独でも亡き者と同じく負けることを確認 ✅
- ただし Proposal 3 (CONFIRM × confidence ≥ 0.60) で PF 1.294 (lift +0.427)
  に押し上げ ✅
- 通貨ペア固有リスク (スプレッド 1.5pip、JPY 介入、ボラ大) は依然存在するが、
  スプレッド 1.5pip は BT 計算に控除済 ✅
- Phase 2'A 30 日で実約定 PF と Phase 0' BT 乖離を測定し、
  乖離 > 20% なら撤退 (§9.7 既存条件) ✅
- 「戦略変更だから本番実績無関係」とは言えず、通貨構造的不利が残ることを前提に
  撤退条件を厳格運用する ✅
```

### C-2. karen 前回指摘の各点の対応

| 前回 karen 指摘 | 今回 SPEC での対応 |
|---|---|
| 亡き者本番 PF 0.868 と Phase 0' BT PF 1.294 の乖離は +0.426 — なぜか? | **base PF 0.867 ≈ 亡き者 0.868 = signal_v2 自体は同水準。+0.426 lift は LLM フィルタの効果** と数値で説明 ✅ |
| 「戦略が違うから本番実績は無関係」が明示されていない | 反論 B で「signal_v2 と MTFPullback は別物」を明示 ✅ |
| ペア固有要因 (スプレッド/介入/ボラ) の言及がない | 「スプレッド 1.5pip は BT 計算に控除済」「JPY 介入、ボラ大」と明示 ✅ |
| 「亡き者本番マイナス期間に LLM が CONFIRM を出すか」 | Phase 0' BT 2,443件のうち CONFIRM × conf≥0.60 で n=469 まで絞り PF 1.294 — 全期間データで検証済 ✅ |

### C-3. karen 評価

**判定**: ✅ **解消**

前回「自己一貫性崩壊パターンの再演」と指摘した点が、**正面から数値で反論された**。特に重要なのは:

1. **Phase 0' BT base PF 0.867 ≈ 亡き者 PF 0.868** という偶然とは思えない完全一致 — これは「signal_v2 が亡き者の MTFPullback と同水準の弱戦略」という強い証拠。**戦略の差で本番実績がリセットされる根拠が崩れていない可能性** を示唆する一方、**素の signal_v2 は使わない (LLM フィルタ + 閾値で +0.427 lift)** が本仕様の前提なので、リスクは管理されている。
2. **「通貨構造的不利が残ることを前提に撤退条件を厳格運用する」** と SPEC 自体が明示 — 楽観論を排し、Phase 2'A 30 日で実約定 PF 乖離 > 20% なら撤退、という条件付きでの再採用。

SPEC v2 撤退の「3 日後再採用」とは構造的に異なる:
- SPEC v2: 撤退翌週に同じ戦略で再開 (= 一貫性崩壊)
- SPEC v3: **戦略を別物に変更 + 乖離 > 20% で撤退** の防衛線を引いた上での慎重な再採用

形式的合格でなく実質合格。**起動を止める理由がない**。

---

## D. 新たに発見した問題

修正で新たな問題が発生していないか、慎重にチェック。

### D-1. PHASE_2A_PLAN.md §6 が SPEC §4.5 撤退条件 #0 (lift ベース) を未反映 [低]

**所見**:
- SPEC §4.5 で撤退条件 #0「lift vs base < +0.30 が 3 ヶ月連続」が追加された (M2 提案で lift ベースに変更)
- PHASE_2A_PLAN.md §6.1-6.4 では条件 1-5 のみ列挙、**#0 lift ベースの記載なし**
- L175「## 6. 撤退条件 (SPEC v3 §4.5 継承)」とあるが、本文に #0 が引用されていない

**重大度**: 低。SPEC v3 が最新の真実 (truth source) で、PHASE_2A_PLAN は派生物。実装は SPEC を参照するため、運用上の動作は問題ない。

**推奨対応**: Phase 2'A 起動と並行で PHASE_2A_PLAN.md §6.1 に「条件 0: lift < +0.30 が 3 ヶ月連続 → 当該ペア停止」を追記。Phase 2'A 期間中はそもそも 3 ヶ月のロールバックウィンドウが取れないため、起動時点での運用影響はゼロ。

### D-2. `SPREAD_WARN_THRESHOLD_PIPS` がコードに残っているが未使用 [低]

**所見**:
- `src/spec_v3/__init__.py` L27-34 で `SPREAD_WARN_THRESHOLD_PIPS` 定数が定義されている
- L27 コメントに「Pragmatist P0-2 是正、Phase 2'A は WARN ログのみ、Phase 2'B 前に完全配線予定」と書かれている
- しかし `demo_loop.py` でこの定数は **使われていない** (実装は KillSwitchState.spread_baseline の EMA で動的に閾値を持つ)
- `__all__` にも含まれているが import されていない (Grep で確認: 定義箇所のみ)

**重大度**: 低。混乱要因だがバグではない。EMA baseline 方式 (現行) と固定閾値方式 (旧設計) の二重設計の名残。

**推奨対応**: コメントを更新して「EMA baseline 方式に置換された (KillSwitchState.spread_baseline + update_spread / check_spread_anomaly)。WARN ラインはまだ未配線、Phase 2'B 前に検討」と明示するか、定数を削除する。

### D-3. ATR が LLM プロンプトに渡るようになった (前回 A-4 指摘) — 解消 ✅

前回 A-4「ATR が常に N/A」を指摘していたが、demo_loop.py L444-465 で:
- `from src.spec_v3.llm_filter import build_context, calc_atr`
- `atr_value = calc_atr(m15_df)` を計算
- `build_context(..., signal={..., "atr": atr_value, ...})` でコンテキストに含める

テスト `test_calc_atr_returns_finite_value`, `test_calc_atr_returns_none_when_insufficient`, `test_atr_in_llm_prompt` の 3 件すべて PASS で確認済。これは前回中重大度として指摘した項目の **おまけ解消** で評価加点要素。

### D-4. daily_block_until 自動再起動衝突 (前回 A-3 指摘) — 解消 ✅

前回 A-3「daily_block_until クリア機構なし」と指摘した点も M1 で是正された。
demo_loop.py L578-633 で:
- `_persist_killswitch_state()`: 状態を DB (`kill_switch_state` テーブル) に保存
- `_restore_killswitch_state()`: 起動時に DB から復元、当日/当月のものだけ継承
- 過去日付は復元しない (test_killswitch_state_old_dates_not_restored で確認)

これも前回中重大度の **おまけ解消**。Phase 2'A の VPS 自動再起動 (RestartCount=5) との衝突が構造的に解消。

### D-5. 全体への新規問題評価

**判定**: ✅ **新たな重大問題なし**

M1 (実装層バグ② ③ ⑤ ⑥ 是正)、M1b (整合修正)、M2 (標準分割再分析) のすべての修正が、新たな副作用や設計矛盾を導入していない。テスト 34 件すべて PASS。

修正後に「VOLATILE フィルタ削除」がされているが、これは Ultra バグ① 是正で **Phase 0' BT データと SPEC v3 実装の整合性を確保するための正当な是正**。当初設計意図 (= GBP_JPY VOLATILE フィルタ) は SPEC v2 PoC 由来だが、Phase 0' BT データ (`signal_v2_historical_signals_gbp_jpy_no_volatile.csv` 2,443 件) は VOLATILE フィルタなしで集計済 → SPEC を BT データに合わせるのが正解。実装と BT の三重不整合 (RETREAT バグ① 再演) を回避する正当な是正。

---

## E. 総合評価

### E-1. 前回判定からの変化

| 重大発見 | 前回判定 (2026-05-27) | 今回判定 (2026-05-28) |
|---|---|---|
| 発見 1: IS-OOS 整合性虚飾 | 重大 — 起動延期 | ✅ **完全解消** |
| 発見 2: スプレッドキルスイッチ未配線 | 重大 — 起動延期 | ✅ **完全解消** |
| 発見 3: GBP_JPY 自己一貫性監査未実施 | 重大 — 起動延期 | ✅ **解消** |
| (中) A-3: daily_block_until 自動再起動衝突 | 中 | ✅ **おまけ解消** |
| (中) A-4: ATR LLM プロンプト常に N/A | 中-低 | ✅ **おまけ解消** |

### E-2. SPEC v3 (Proposal 3) の実質的妥当性 (karen 視点)

**虚飾排除レンズで見て:**

1. **「IS PF 1.335 → OOS PF 1.376 で +0.041 改善 (オーバーフィットなし)」** という前回の主張 → 今回は **「16 分割で lift +0.46〜+0.60 (σ=0.04)、4 標準分割で +0.30 ゲート PASS、2026 Hold-out で +0.497 lift」** という **構造的に強い証拠** に置き換わった。
2. **「PF 1.304-1.629 (中央値 1.377)」**: これは標準分割の生数値で、 J メタ分析 1.354 (per-pair-count-half) よりわずかに高い。J メタ分析の数字が選択バイアスで「やや甘め」ではなく「むしろ厳しめ」だったことが分かり、誠実性が高い。
3. **2026 Hold-out PF 1.304 (n=185, lift +0.497)** がモデル知識カットオフ以降の純粋な未見データ → **本番期待値の最も信頼できる基準**。これでも +0.30 ゲートを十分超過。
4. **経済性年率の試算 (PF 1.354 / 月 ~28 trades / 1 trade ≈ 60 pips / lot 1.0 換算)** → 別途試算が必要だが、SPEC v2 PoC で構造的不在だった経済性 Gate が Phase 2'B で機能する設計。

### E-3. 残存中重大度問題 (Phase 2'A 起動と並行で対応可)

| # | 項目 | 対応タイミング |
|---|---|---|
| A-2 | VIX > 30 / ±3σ キルスイッチ未実装 | Phase 2'B 経済性 Gate 判定までに実装 |
| A-5 | LLM モデル ID `claude-sonnet-4-6` の有効性 | Phase 2'A 起動前の再現性テスト (§9.4) で実体確認 → SPEC §3.1 でフルバージョン形式に更新 |
| B-2 | 撤退条件3 (累計 -3,000 JPY) の早期発動確率推定 | Phase 2'A 第1週目までに推定 |
| C-3 | 直近 2025Q3+ PF の構造的偏り (USD_JPY 高 PF スパースサンプル) | Phase 2'A 月次レビューで追跡 |
| D-1 | PHASE_2A_PLAN.md §6 に撤退条件 #0 lift ベース追記 | Phase 2'A 起動と並行 |
| D-2 | `SPREAD_WARN_THRESHOLD_PIPS` 未使用定数の整理 | コードクリーンアップ |

### E-4. karen の最終判定

**結論**: ✅ **起動 OK (実質的合格)**

前回 SPEC v2 撤退の決定打となった karen 指摘 3 件 (撤退済再採用、★★★★★ 虚飾、経済性 Gate 不在) すべてが、SPEC v3 で **形式的にも実質的にも継承された**:

- ✅ 撤退条件の事前明文化 (§4.5、運用後追加禁止、定数化で機能)
- ✅ PoC 三重定義の役割分離 (signal_v2 改変禁止、LLM フィルタ独立、閾値層独立)
- ✅ 24 時間最大保持で亡き者挙動データを反映 (§5.3)
- ✅ Phase 2'B → 2'C 段階移行で本番投入を慎重化 (§7)
- ✅ 経済性 Gate (Phase 2'B、PF≥1.3 / Sharpe≥0.8 / MaxDD≤15% / OOS trades / LLM コスト) 構造的に組み込み (§7.2)
- ✅ 標準分割再分析で「OOS で性能維持」主張が **複数分割で堅牢** に確認
- ✅ スプレッドキルスイッチ配線で「資金管理最優先」原則を実装層で担保
- ✅ GBP_JPY 副ペア再採用の自己一貫性監査 (反論 B で誠実な整理)

**前回「修正後の判定変更条件」テーブル** (PHASE2A_REVIEW_KAREN.md L337-343) に照らすと:

| 条件 | 今回の状況 | 判定 |
|---|---|---|
| 重大 1, 2, 3 のすべてに対応 | ✅ すべて解消 | **起動 OK** |

---

## F. 推奨アクション

### F-1. Phase 2'A 起動承認 (即時可)

K2 完了 + ultrathink-debugger + code-quality-pragmatist の独立合意が揃えば、Phase 2'A を VPS で起動 OK:

```powershell
Start-ScheduledTask -TaskName "FX_SPEC_V3_PAPER"
```

### F-2. Phase 2'A 起動と並行で対応 (中重大度)

- A-2: VIX/3σ キルスイッチを Phase 2'B 経済性 Gate 判定までに実装
- A-5: LLM モデル ID 再現性テスト (§9.4) → フルバージョン固定
- B-2: 撤退条件3 早期発動確率推定 (Phase 2'A 起動前 1 日以内に Phase 0' データから算出)

### F-3. Phase 2'A 期間中に追跡 (低重大度)

- C-3: 2025Q3+ PF の USD_JPY 高 PF スパースサンプル影響を月次レビュー
- D-1: PHASE_2A_PLAN.md §6 に撤退条件 #0 lift ベース追記
- D-2: `SPREAD_WARN_THRESHOLD_PIPS` 未使用定数の整理

### F-4. Phase 2'A 終了時 (30 日後 or 60 日延長後) に再度反論屋呼び出し

PHASE_2A_PLAN.md §4 経済性 Gate 判定時に、再び karen / ultrathink-debugger / code-quality-pragmatist で独立レビュー。
特に Karen は:
- 実約定 PF と Phase 0' BT (1.354) の乖離 > 20% でないか
- 撤退条件 #0 lift ベースが想定通り機能しているか
- LLM コスト累計が想定 (¥30-50/月) から大きく外れていないか

を再評価する。

---

## G. 他の反論屋判定との独立性

PHASE_2A_PLAN.md §11 「反論屋3体合意」規定に従い、karen は **起動 OK で投票**。
- karen: ✅ 起動 OK (本判定)
- ultrathink-debugger: 別途独立判定 (構造バグ視点)
- code-quality-pragmatist: 別途独立判定 (実装健全性視点)

3/3 揃った時点で Phase 2'A 起動承認となる。

---

## 付録: 検証に使った実測データ

- `docs/SPEC_V3.md` (M1b 整合修正後、Proposal 3 確定版)
- `docs/PHASE_2A_PLAN.md`
- `docs/proposals/cycle2/STANDARD_SPLIT_REANALYSIS.md` (M2 再分析の生レポート)
- `data/_standard_split_reanalysis.json` (4 標準分割 + 16 分割 + ゲート評価の生データ)
- `data/_cycle2_meta_analysis_temporal_v2.json` (J メタ分析の元データ、前回検証で参照)
- `src/spec_v3/demo_loop.py` L349-390 (スプレッドキルスイッチ配線)
- `src/spec_v3/risk_manager.py` L100-145 (KillSwitchState.update_spread / check_spread_anomaly)
- `src/spec_v3/__init__.py` (CONFIDENCE_THRESHOLDS, ENABLED_PAIRS, ACCEPT_DECISIONS)
- `tests/spec_v3/test_demo_loop.py` 34 件すべて PASS (pytest 4.95s で確認)

### Phase 0' BT と JSON 数字の整合 (本査読で再確認)

```
標準分割 1 (時間半々、共通カットオフ 2025-05-07):
  Proposal 3 Combined OOS PF = 1.377, base OOS PF = 0.841, lift = +0.536
標準分割 2 (年単位、2024 IS / 2025 OOS):
  Proposal 3 Combined OOS PF = 1.629, lift = +0.731
2026 Hold-out:
  Proposal 3 Combined OOS PF = 1.304, base OOS PF = 0.807, lift = +0.497
標準分割 3 (直近 12 ヶ月):
  Proposal 3 Combined OOS PF = 1.377, lift = +0.535
16 分割 lift 範囲: +0.460 〜 +0.596 (標準偏差 0.04)
ゲート PASS 率: 3/3 標準分割 = 100%
OOS PF > IS PF: 7/16 = 43.8% (lift は分割不変、IS<OOS は分割依存)
```

SPEC v3 §0 / §10.1 の数字すべてが JSON データと **完全一致**。捏造・改変なし。

---

**起草**: 2026-05-28、karen 反論屋エージェント (再査読)
**前回 (2026-05-27) 判定**: 設計修正必要 (起動延期、最低 1-2 日)
**今回判定**: ✅ **起動 OK (実質的合格)**
**変化要因**: M1 (実装層バグ② ③ ⑤ ⑥ 是正) + M1b (SPEC 整合修正) + M2 (標準分割再分析) で前回重大発見 3 件すべて解消、新たな重大問題なし
