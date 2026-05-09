# STATUS — FX自動取引 運用ダッシュボード

> **「いま」のスナップショット。** ふわっと指示を受けたAI/未来の自分が**最初に見る**ファイル。
> 過去判断や根拠は `docs/INDEX.md` / `memory/MEMORY.md` / git log を参照。

| メタ | 値 |
|---|---|
| **最終更新** | 2026-05-08 (Step C P0-2 完了反映) |
| **次回更新予定** | 2026-05-15（7日後）または重要変更時 |
| **更新方法** | `python scripts/update_status.py [--with-vps]` / 手動編集（緊急時） |

---

## 🌐 プロジェクトの2レイヤー構造

本プロジェクトは現在 **2つのレイヤー** が並行している。混同しない。

| レイヤー | 状態 | 何をしているか |
|---|---|---|
| **🪦 亡き者の世界（応急処置）** | VPS 稼働中 / PR #30 OPEN | 既存戦略 (MTFPullback) の運用を維持しつつ撤退判断（GBP_JPY 撤退） |
| **🌱 ゼロベース再構築の世界** | SPEC v2 § 2-1 検証中 | STORY/PREMISE/OPERATING_MODEL v2.1 → SPEC v2 数値降ろし。**再構築完了まで本番投入禁止** |

**判断指針** (`docs/vision/PREMISE.md` から):
- 「既存運用の判断 (USD_JPY 処遇 / GBP_JPY 撤退PR 等) を運用モデルで決めようとしない」 = **亡き者の世界の問題は応急処置で対応、再構築モデルが答える問題ではない**
- 既存戦略・パラメータ・数値は **亡き者** として扱う。**コードベース骨格と教訓だけ** 継承

---

## 🟢 いま稼働中の構成（🪦 亡き者の世界）

| 項目 | 値 |
|---|---|
| **本番VPS** | ConoHa Windows Server (160.251.221.43) |
| **Pythonプロセス** | PID 6108、起動 2026-05-05 12:52 JST、RAM 17MB |
| **稼働ペア** | EUR_USD / USD_JPY （GBP_JPY は 2026-05-07 撤退、PR #30 OPEN・VPS反映待ち） |
| **timeframe** | M15、60秒間隔ループ |
| **ブローカー** | 外為ファイネスト MT5 デモ口座 |
| **PR #30** | `fix(strategy): GBP_JPY 撤退` / マージ後 VPS pull + 再起動が必要 |

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
| **SPEC v2 § 2-1 - 指標–リターン単峰性 / グリッド拡張 / CHOP <25 再検証** | ⬜ Step C 新 P0 (P1-1b 発見受け) |
| **SPEC v2 § 2-1 - PF 置換 + BCa CI / HMM / 直交性** | ⬜ 上記完了まで保留 |
| **SPEC v2 § 2-2〜5-2 (他14スキーム)** | ⬜ 未着手 |
| **本番投入** | 🔴 禁止 (Step C 完了まで) |

**現時点の重要発見 (P1-1b 完了時点で大幅更新)**:
- **🚨 物語破棄オプション条項 発火条件成立** — ★☆☆ が 5件 (H2, H3, H6, H7, H8)。HYPOTHESES_2-1.md は再起草対象
- **Mode B (閾値再選定) で 11/12 が Mode A 値と不一致** — Mode A の閾値はほぼ全て最適ではない
- **真に頑健 (CV<0.1) なのは 2 件のみ**: EUR_USD/GBP_JPY M15 CHOP <25 (ただし Mode A の <30 ではない)
- **M15 YZ_vol が 10/90%ile に二極化** — 指標–リターン関係が単峰でない可能性、H2 (直交分解) の前提揺らぐ
- **H1 YZ_vol 3ペアがグリッド上限選定** — SPEC 値の +50% が良い、グリッド再設計必要
- **GBP_JPY D1 YZ_vol が Mode A 5/5 → Mode B n_pass=0/5 で完全崩壊** — 典型的なカーブフィット
- **確定する判定**: EUR_USD D1 YZ_vol 棄却 / GBP_JPY D1 YZ_vol 棄却 (Mode B 完全崩壊)
- **教訓**: ねじれを都合よく片付けない、追加検証で本質を解明する → `feedback_anomaly_is_signal_not_conclusion.md`
- σ_TR 仮定値の試算は誤誘導 → `feedback_assumption_vs_measurement.md`

詳細: `memory/project_fx_spec_v2_verification.md` / `docs/vision/HYPOTHESES_2-1.md` / `docs/vision/research/`

---

## ⚠️ 観察中の課題（🪦 亡き者の世界、高優先度のみ）

| 課題 | ステータス | 次のアクション | 詳細 |
|---|---|---|---|
| **PR #30 GBP_JPY 撤退** | OPEN, CI Vercel関連で2失敗 (FX無関係) | マージ → VPS pull + 再起動 | `gh pr view 30` |
| USD_JPY パフォーマンス | 観察中 (7件中1勝) | 1〜2週間後に再評価 | `memory/project_fx_pending_items.md` |
| trading_loop.py 重複INFO格下げ (L462/L529/L640) | follow-up 登録済 | 別PRで一括対応 | `memory/project_fx_pending_items.md` § 認識済みfollow-up |
| EUR/GBP の HOLD パターン | LDN-NY セッション (JST 21:00-02:00) で観察必要 | 該当時刻のログ追加調査 | `memory/project_fx_signal_status_2026_05_05.md` |
| postmortem 出力率の定常運用率 | サンプル 2/2 = 100% だが少 | 2週間後に再計測 | 同上 |
| 退避ブランチ `vps-backup-20260505-pre-trace-deploy` 削除 | 2026-05-12 以降 | 1週間経過後 | `memory/feedback_vps_git_hygiene.md` |

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
