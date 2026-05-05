# STATUS — FX自動取引 運用ダッシュボード

> **「いま」のスナップショット。** ふわっと指示を受けたAI/未来の自分が**最初に見る**ファイル。
> 過去判断や根拠は `docs/INDEX.md` / `memory/MEMORY.md` / git log を参照。

| メタ | 値 |
|---|---|
| **最終更新** | 2026-05-05 13:51 JST |
| **次回更新予定** | 2026-05-12（7日後）または重要変更時 |
| **更新方法** | `python scripts/update_status.py [--with-vps]` / 手動編集（緊急時） |

---

## 🟢 いま稼働中の構成

| 項目 | 値 |
|---|---|
| **本番VPS** | ConoHa Windows Server (160.251.221.43) |
| **Pythonプロセス** | PID 6108、起動 2026-05-05 12:52 JST、RAM 17MB |
| **稼働ペア** | EUR_USD / USD_JPY / GBP_JPY |
| **timeframe** | M15、60秒間隔ループ |
| **ブローカー** | 外為ファイネスト MT5 デモ口座 |

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

## ⚠️ 観察中の課題（高優先度のみ）

| 課題 | ステータス | 次のアクション | 詳細 |
|---|---|---|---|
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
