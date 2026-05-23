# STATUS — FX自動取引 運用ダッシュボード

> **「いま」のスナップショット。** ふわっと指示を受けたAI/未来の自分が**最初に見る**ファイル。
> 過去判断や根拠は `docs/INDEX.md` / `memory/MEMORY.md` / git log を参照。

| メタ | 値 |
|---|---|
| **最終更新** | 2026-05-23 (PoC 11日停止からの復旧 + ExecutionTimeLimit=PT72H 罠の修正) |
| **次回更新予定** | 2026-05-30（7日後）または重要変更時 |
| **更新方法** | `python scripts/update_status.py [--with-vps]` / 手動編集（緊急時） |

---

## 🌐 プロジェクトの状態 (亡き者整理完了 2026-05-13)

**🪦 亡き者の世界は全停止**。SPEC v2 PoC (再構築の世界) のみ稼働。
PREMISE.md 「過去は捨てた。教訓だけ持って、ゼロから組み立てる」に従い、亡き者の延命を打ち切り。

| 状態 | 内容 |
|---|---|
| 🪦 亡き者の世界 | **全停止 (2026-05-13)**。FX_AutoTrading / FX_Healthcheck / FX_DailySummary / FX_MarketAnalysis / FX_MemoryMonitor の5タスク全 `Disabled`、PID 7028 (MTFPullback main.py) 停止 |
| 🌱 再構築の世界 | SPEC v2 PoC (GBP_JPY 単一通貨) 稼働中。SPECv2_PoC タスク Running |
| PR #30 | **クローズ (2026-05-13)**。亡き者の世界の論件は運用モデルで答える対象外 (PREMISE.md) |

---

## 🟢 いま稼働中の構成（🌱 再構築の世界）

| 項目 | 値 |
|---|---|
| **本番VPS** | ConoHa Windows Server (160.251.221.43) |
| **Pythonプロセス** | PID 6392、起動 2026-05-23 10:09:07 JST、RAM 100MB |
| **稼働ペア** | GBP_JPY 単一 (SPEC v2 § 2-1 H4 ★★★★★ 確定) |
| **戦略** | SeasonalDetector (M15 YZ_vol > 30%ile + H1 YZ_vol > 0.00175 二層判定) |
| **lot** | 0.01 固定 / 最大保持 4時間 / 1ポジション制限 |
| **timeframe** | M15+H1 二層、60秒間隔ループ |
| **ブローカー** | 外為ファイネスト MT5 デモ口座 (22005467) |
| **リポジトリ** | `C:\bpr_lab_spec_v2` (worktree、亡き者と物理分離) |
| **DB / ログ** | `data/fx_spec_v2.db` / `data/spec_v2_poc.log` |
| **タスク設定** | `SPECv2_PoC` ExecutionTimeLimit=`PT0S` (無制限、2026-05-23 修正) / RestartCount=3 / RestartInterval=1分 |

### 🚨 PoC 稼働履歴（重要 — 1-2週間観察は 5/23 起点でやり直し）
- **2026-05-12 23:37:51** 初回起動（PID 4036）
- **2026-05-13 〜 2026-05-15** 正常稼働（iter 4304 まで、エントリー0件、regime=transitional 中心）
- **2026-05-15 23:37:35** ExecutionTimeLimit=PT72H に到達して強制終了 (267014 = SCHED_S_TASK_TERMINATED)
- **2026-05-15 〜 2026-05-23** 8日間放置（成功終了扱いで RestartCount 不発火 + 単発トリガーで再起動なし）
- **2026-05-23 10:09:07** ユーザー指摘で復旧 + ExecutionTimeLimit を PT0S (無制限) に変更
- 真因と再発防止: → `memory/feedback_task_scheduler_execution_time_limit.md`

---

## 📊 最新 statistics

(VPS DB未取得 — `--with-vps` で取得。手動更新時は前回値を保持)

---

## 🔄 直近7日のマージ済PR

| PR | タイトル |
|---|---|
| **#28** | chore: pair_config 未稼働ペアコメント + docs/ INDEX.md 作成（情報整合性整理） |
| **#27** | feat(observability): 旧『時間帯フィルター』INFO格下げで二段構え完成 |
| **#26** | feat(observability): パイプライン1行サマリログを追加 |
| **#24** | fix(audit): 監査P1 — Bear Researcher 重み付け化・ダイバージェンス検出刷新・spread alpha config化 |
| **#23** | fix(scorer): 監査P0 — ConvictionScorer の死んだ分岐と再ハードコードを修正 |
| **#21** | fix(regime): 監査A4 — RegimeDetector閾値をpair_configで上書き可能に |
| **#20** | fix(audit): A6+B7+B8 — KILL_COOLDOWN/SignalCoordinator/日次UTC境界 |
| **#25** | fix(postmortem): max_tokens=512 不足による JSON truncation バグを修正 |
| **#19** | fix(FX): MTFPullback/BollingerReversal の pair_config 配線漏れ修正 (CRITICAL) |
| **#22** | docs(audit): 監査進捗を remaining_tasks に反映（PR #19/20/21 追加） |
| **#18** | docs(FX): Phase 2 監査・分析レポートとプランを集約 |
| **#17** | feat(FX): MT5 履歴データ export + Phase 3 (M15 5y) 検証ランナー |
| **#16** | fix(FX): 非JPYペアのpip_valueフォールバックを動的化 (CRITICAL ロット過大計算リスク修正) |
| **#15** | fix(FX): BT spread のデフォルトを実測値に補正 (1pip → ペア別 1.5〜2.5pip) |
| **#14** | fix(FX): sync_with_broker が ai_decision を NULL で上書きしないよう保護 |

完全な履歴: `git log --oneline --since="7 days ago"`

## 🌱 ゼロベース再構築の世界 (SPEC v2 進捗)

| 項目 | 状態 |
|---|---|
| **STORY.md** (北極星: 庭師×生命体) | ✅ 完了 |
| **PREMISE.md** (亡き者と継承) | ✅ 完了 |
| **OPERATING_MODEL.md v2.1** (15スキーム / 数字なし) | ✅ 完了 |
| **SPEC v2 § 2-1 季節判定 - 仮説台帳** (HYPOTHESES_2-1.md) | ✅ Step A 完了 |
| **SPEC v2 § 2-1 - 文献調査** (researcher × 4並列) | ✅ Step B 完了 |
| **SPEC v2 § 2-1 - Permutation Test** (12閾値中 11/12 p<0.05) | ✅ Step C P0-2 完了 |
| **SPEC v2 § 2-1 - 多重補正** (Bonferroni N=606 / Romano-Wolf 12) | ✅ Step C P0-3 完了 (AAA 5 / AA 2 / A 3 / 🔴 2) |
| **SPEC v2 § 2-1 - rolling WFA Mode A** (閾値固定) | ✅ Step C P1-1 完了 (Mode A 5/5 が 9個) |
| **SPEC v2 § 2-1 - rolling WFA Mode B** (閾値再選定) | ✅ Step C P1-1b 完了 (重大発見: 11/12 が Mode A 値と不一致) |
| **SPEC v2 § 2-1 - 新 P0 Q1 (単峰性) v1+v2** | ✅ 完了 (50分位+bootstrap CI+dip+Spearman で 11/12 弱U字成分支持) |
| **SPEC v2 § 2-1 - 新 P0 Q2 (H1 グリッド拡張) v1+v2** | ✅ 完了 (TR bootstrap CI / low感度) — 隣接倍率 CI 重なり多数 |
| **SPEC v2 § 2-1 - Q1↔Q2 介入実験** (Mode B v2: low 群固定方式) | ✅ 完了 (M15 YZ_vol で CV 0.5-0.84→0.06-0.26、真因部分立証) |
| **SPEC v2 § 2-1 - 実用性検証 WFA** (固定閾値 ×{1.0,1.5,2.0,2.5}) | ✅ 完了 (EUR_USD ×2.0 は usable 1/5 で崩壊確認) |
| **SPEC v2 § 2-1 - Q3 (CHOP <25 多重補正)** | ⬜ 残課題 (次回優先順 1) |
| **SPEC v2 § 2-1 - HYPOTHESES_2-1.md 再起草判断** | ⬜ 庭師判断待ち |
| **SPEC v2 § 2-1 - PF 置換 + BCa CI / HMM / 直交性** | ⬜ 上記完了まで保留 |
| **SPEC v2 § 2-2〜5-2 (他14スキーム)** | ⬜ 未着手 |
| **本番投入** | 🔴 禁止 (Step C 完了まで) |

**現時点の重要発見 (新 P0 v2 検証完了で大幅更新)**:
- **🚨 物語破棄オプション条項 発火条件 依然成立** — ★☆☆ が 5件 (H2, H3, H6, H7, H8)。ただし v2 検証で「破棄」より「個別仮説更新」が筋
- **指標–リターン関係は単峰でなく「単調 + 弱U字」の複合形状** — Q1 v2 で 11/12 が二次係数 a の 95%CI 完全正
- **M15 YZ_vol の Mode B 二極化の主因 = TR 評価式 low 群感度 (M15 のみ立証)** — 介入実験で CV 0.84→0.06 等の劇的改善
- **EUR_USD H1 YZ_vol ×2.0 は実用 WFA で完全崩壊** (usable 1/5) — Q2 v1 の「採用候補」表現は撤回
- **真に実用可能な閾値**: USD_JPY ×1.0, EUR_USD ×1.0, GBP_JPY ×1.0-1.5 (×2.0 は条件付き)
- **H4 (ペア別閾値) は強化** — EUR_USD と他 2 ペアの実用閾値帯が決定的に異なる
- **D1 層は形状判別困難** — Q1 v2 で D1 全件 a の CI ゼロ跨ぎ
- σ_TR 仮定値の試算は誤誘導 → `feedback_assumption_vs_measurement.md`
- ねじれを都合よく片付けない → `feedback_anomaly_is_signal_not_conclusion.md`
- 介入実験なしの真因主張は仮説止まり (新教訓) / 採用候補は実用 WFA を経てから (新教訓)

詳細: `docs/vision/research/STEP_C_NEW_P0_VERIFIED_SUMMARY.md` (v2 統合) / `memory/project_fx_spec_v2_verification.md` / `docs/vision/HYPOTHESES_2-1.md`

---

## ⚠️ 観察中の課題（🌱 再構築の世界のみ）

| 課題 | ステータス | 次のアクション | 詳細 |
|---|---|---|---|
| SPEC v2 PoC GBP_JPY 観察 | **5/23 復旧後の再起算**。実稼働は 5/12-5/15 の3日間 + 5/23 から | 1-2週間 regime/PnL 推移確認、エントリー件数監視 | `docs/SPEC_V2_POC_GUIDE.md` § 観察対象 |
| PoC死活監視の仕組み | 未着手（11日放置の再発防止としてユーザー気付き任せから脱却） | watchdog タスク or Slack 死活通知 を別タスクで | `memory/feedback_task_scheduler_execution_time_limit.md` |
| SPEC v2 § 2-2 (HMM) 未着手 | PoC 観察と並行で着手可 | OPERATING_MODEL.md v2.1 § 2-2 起点に Step A→B→C 再開 | `docs/vision/research/STEP_C_COMPLETION_2026-05-10.md` § Phase 4 分岐 |
| 退避ブランチ `vps-backup-20260505-pre-trace-deploy` 削除 | 2026-05-12 以降 | 1週間経過後 | `memory/feedback_vps_git_hygiene.md` |
| PR #35 (SPEC v2 一式 main へ) | OPEN | PoC 観察期間中に Bear/コードレビュー → main マージ | `gh pr view 35` |

**🪦 亡き者の世界の課題**: すべて停止により無効化。USD_JPY パフォーマンス / trading_loop.py 重複INFO格下げ / EUR/GBP HOLD パターン / postmortem 出力率 等は亡き者の論件のため対応不要。

---

---

## 🚪 振り返り起点リンク

| 用途 | リンク |
|---|---|
| ドキュメント全体マップ | `docs/INDEX.md` |
| コード全体マップ | `src/INDEX.md` (作成中) |
| メモリインデックス | `~/.claude/projects/.../memory/MEMORY.md` |
| 未対応リスト | `memory/project_fx_pending_items.md` |
| VPS運用ルール | `memory/feedback_vps_git_hygiene.md` |
| 観測性機構 | `memory/project_fx_pipeline_trace.md` |
| 半日観察スナップショット | `memory/project_fx_signal_status_2026_05_05.md` |
| GitHub | https://github.com/takuzokb05/bpr_lab |

---

---

## 📝 メンテナンス

### 更新トリガー
- 週次（毎週月曜）: `python scripts/update_status.py` 自動実行（タスクスケジューラ登録予定）
- 大きな PR マージ時: 手動更新（`# 直近7日のマージ済PR` セクション + 影響範囲）
- 本番運用構成変更時（ペア追加・戦略変更等）: 手動更新（`# いま稼働中の構成` セクション）

### stale警告
最終更新から **14日経過** したら、AIは「STATUS.md が stale です。手動再生成 or 自動更新スクリプト実行を推奨」と警告すること。
