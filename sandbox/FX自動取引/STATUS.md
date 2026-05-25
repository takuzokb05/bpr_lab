# STATUS — FX自動取引 運用ダッシュボード

> **「いま」のスナップショット。** ふわっと指示を受けたAI/未来の自分が**最初に見る**ファイル。
> 過去判断や根拠は `docs/RETREAT_2026-05-26.md` / `docs/INDEX.md` / `memory/MEMORY.md` / git log を参照。

| メタ | 値 |
|---|---|
| **最終更新** | 2026-05-26 JST (SPEC v2 PoC 撤退、🌳 プロポーザル方式へ移行) |
| **次回更新予定** | プロポーザル Phase 0 候補ロングリスト確定時 |
| **稼働状態** | **🛑 全停止 (実発注なし、観察ループなし、通知なし)** |
| **現フェーズ** | 🌳 プロポーザル方式 Phase 0 (候補手法ロングリスト構築) |

---

## 🛑 稼働状態 — 完全停止 (2026-05-26〜)

| カテゴリ | 状態 |
|---|---|
| 🪦 亡き者の世界 (MTFPullback 系統) | 全停止 (2026-05-13 から、継続) |
| 🌱 再構築の世界 (SPEC v2 PoC) | **撤退完了 (2026-05-26)**。SPECv2_PoC / SPECv2_AliveCheck / SPECv2_DailySummary すべて Disabled、Python プロセス 0件 |
| 🌳 プロポーザル方式 (新フェーズ) | Phase 0 開始準備中 |
| **MT5 オープンポジション** | **0件** (撤退前に open=0 を確認) |
| **VPS** | 停止 (タスクスケジューラ Disabled、プロセスなし) |

### 撤退の理由 (3行で)
1. **Pragmatist BT で signal_v2 (ATR breakout) が過去2年 PF 0.95 / シャープ -0.39 / lot 1.0換算 2年-385,811 JPY** = 銀行預金以下確定
2. **3反論屋 (karen / ultrathink / pragmatist) が独立に「PoC 即停止」を結論**
3. **「叩いた論点 (経済性Gate追加 / 亡き者継承条項 / 三重定義整理) を実装しても PF 0.95 を超える保証なし」** → フレーム延命より手法選定優先

詳細: `docs/RETREAT_2026-05-26.md` / `docs/analysis/CONTRARIAN_*.md` (反論屋3本)

---

## 🌳 次フェーズ — プロポーザル方式

**「手法 → フレーム」の順を取り戻す**。先に PF > 0.95 を上回る手法を選定してから、それに合わせて新フレーム (SPEC v3) を起草する。

| Phase | 内容 | ステータス |
|---|---|---|
| **Phase 0** | 候補手法ロングリスト構築 (内部memory + 文献 + 内部アイデア) | 🟡 開始準備中 |
| **Phase 1** | 簡易 BT スクリーニング (PF > 1.3 通過のみ次段へ) | ⬜ 未開始 |
| **Phase 2** | 上位候補の精査 BT (WFA / OOS / Deflated Sharpe) | ⬜ 未開始 |
| **Phase 3** | 採用判断 + SPEC v3 起草 | ⬜ 未開始 |
| **Phase 4** | PoC 再起動 (採用後) | ⬜ 未開始 |

採点フレーム: `docs/PROPOSAL_TEMPLATE.md`

### Gate 0 (絶対必須、未充足は門前払い)
- **G0-A**: PF 0.95 を上回る成果を出せるか (過去5年 BT または理論的根拠)
- **G0-B**: 放置してても自己改善ができるか (ドリフト検出 + 自動再最適化 + フォールバック)

---

## 📜 撤退時点でのリポジトリ状態

| 項目 | 値 |
|---|---|
| **現ブランチ** | `feature/proposal-selection` (main から 2026-05-26 作成) |
| **アーカイブブランチ** | `archive/spec-v2-rebuild-20260526` (撤退直前の最終状態を凍結) |
| **保持データ** | `data/fx_spec_v2.db` (VPS のみ) / `data/fx_trading.db` / `data/fx_trading_prod_snapshot.db` / `data/mt5_GBP_JPY_H1_5y.csv` — 全て保持、Phase 0/1 で再利用 |
| **保持コード** | `src/spec_v2/` (撤退アーカイブ) / `src/` 亡き者系統 (撤退アーカイブ) — 削除しない |

---

## 📚 撤退判断の証跡 (反論屋3本 + 並列分析3本)

| ファイル | 内容 |
|---|---|
| `docs/analysis/AGENT_A_VOL_DISTRIBUTION.md` | H1 YZ_vol 実測分布 (PoC 7,834件 + 5年CSV) |
| `docs/analysis/AGENT_C_HYPOTHESIS_AUDIT.md` | 仮説台帳 H1 0.00175 監査 (Y2/Y4 依存・Y5 1.99%) |
| `docs/analysis/CONTRARIAN_KAREN.md` | 経済性 Gate 不在の構造欠陥指摘 (prod 実測 PF 0.87) |
| `docs/analysis/CONTRARIAN_ULTRA.md` | PoC 三重定義・4hr損切りミスマッチ・A/C 疑似独立 |
| `docs/analysis/CONTRARIAN_PRAGMATIST.md` | signal_v2 過去2年 BT (PF 0.95 / シャープ -0.39) |
| `docs/RETREAT_2026-05-26.md` | 撤退記録の全体まとめ |

---

## 🚪 振り返り起点リンク

| 用途 | リンク |
|---|---|
| 撤退記録 | `docs/RETREAT_2026-05-26.md` |
| プロポーザル採点フレーム | `docs/PROPOSAL_TEMPLATE.md` |
| メモリインデックス | `~/.claude/projects/.../memory/MEMORY.md` |
| GitHub | https://github.com/takuzokb05/bpr_lab |

---

## 📝 メンテナンス

### このセッションでの更新トリガー
- **2026-05-26**: SPEC v2 PoC 撤退、プロポーザル方式へ移行 (本書き換え)

### stale警告
最終更新から **14日経過** したら、AIは「STATUS.md が stale です」と警告すること。
