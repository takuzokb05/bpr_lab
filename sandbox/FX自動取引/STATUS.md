# STATUS — FX自動取引 運用ダッシュボード

> **「いま」のスナップショット。** ふわっと指示を受けたAI/未来の自分が**最初に見る**ファイル。
> 過去判断や根拠は `docs/RETREAT_2026-05-26.md` / `docs/INDEX.md` / `memory/MEMORY.md` / git log を参照。

| メタ | 値 |
|---|---|
| **最終更新** | 2026-05-28 JST (SPEC v3 Proposal 3 確定、反論屋3体 2/3 起動 OK、Ultra H-① 致命バグ指摘で修正待ち) |
| **次回更新予定** | N1 修正完了 + karen+pragmatist 再査読時 |
| **稼働状態** | **🛑 全停止維持** (Phase 2'A 起動準備中、未起動) |
| **現フェーズ** | 🌳 第2サイクル Phase 2'A 起動準備 (M3 反論屋3体再査読完了、Ultra H-① 修正待ち) |

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

## 🌳 第2サイクル SPEC v3 進捗 (2026-05-26〜28)

**「手法 → フレーム」の順を取り戻す**。第1サイクル 5/5 FAIL を経て、第2サイクルで signal_v2 (PF 0.95) を LLM Direct Filter で補完する Proposal 3 を確定。

| Phase | 内容 | ステータス |
|---|---|---|
| **Phase 0** | 候補手法ロングリスト構築 (26候補) | ✅ 完了 |
| **Phase 1** | 6評価委員査読 + Phase 2 BT 5候補精査 | ✅ 5/5 FAIL → 第2サイクルへ |
| **第2サイクル Phase 0'** | signal_v2 + LLM フィルタ 全件判定 (USD_JPY 2,616件 + GBP_JPY 2,443件) | ✅ 完了 |
| **第2サイクル Phase 0' 改善** | J 改善余地メタ分析で Proposal 3 発見 (PF 1.354 / lift +0.438) | ✅ 完了 |
| **第2サイクル Phase 0' 検証** | M2 標準分割 4/4 PASS、lift σ=0.04 で分割不変 | ✅ 完了 |
| **Phase 2'A 起動準備** | SPEC v3 確定、実装 (src/spec_v3/、34テスト PASS)、反論屋3体査読 | 🟡 進行中 (2/3 OK) |
| **Phase 2'A 実運用** | VPS デモ 30日 | ⬜ 未開始 (N1 修正待ち) |
| **Phase 2'B 経済性 Gate** | PF≥1.3, Sharpe≥0.8, MaxDD≤15%, 機会費用超過 | ⬜ Phase 2'A 終了後 |
| **Phase 2'C 本番投入** | lot 段階移行 (0.01→0.02→ATR可変) | ⬜ Phase 2'B 通過後 |

### Proposal 3 (確定)
- **USD_JPY**: CONFIRM × confidence ≥ 0.65 → PF 1.565 (n=203)
- **GBP_JPY**: CONFIRM × confidence ≥ 0.60 → PF 1.294 (n=469)
- **Combined PF 1.354 / lift +0.438** (4 標準分割すべて PASS、Karen ✅、Pragmatist ✅)
- 2026 Hold-out PF 1.304 (LLM 知識カットオフ後の純粋未見データ)

### 反論屋3体 M3 再査読結果 (2026-05-28)
- ✅ **karen**: 起動 OK (実質合格)、前回3重大発見すべて解消
- ✅ **pragmatist**: 起動 OK (無条件、条件付きから格上げ)、年率 +300-600% 確認
- ❌ **ultra**: 設計修正必要、**H-① close_position 戻り値キー不一致 (致命、PF 計測歪む)** + 4 中低度バグ

### 残作業 (Phase 2'A 起動まで)
1. **N1** 即修正 (H-① + H-② 撤退条件 #0 配線、1-2時間)
2. **N2** 推奨 (H-③④⑤ pipeline ログ / ペア順 / DB status、1日)
3. **N3** karen + pragmatist 再査読 (Ultra 不要、Ultra 自己提案に従い)
4. **N4** ユーザー最終承認 → VPS デプロイ → Phase 2'A 起動

採点フレーム: `docs/PROPOSAL_TEMPLATE.md`、SPEC: `docs/SPEC_V3.md`、計画: `docs/PHASE_2A_PLAN.md`

### Gate 0 (絶対必須、未充足は門前払い)
- **G0-A**: PF 0.95 を上回る成果を出せるか — ✅ Proposal 3 Combined PF 1.354 / +0.438
- **G0-B**: 放置してても自己改善ができるか — ✅ ドリフト検出、フォールバック (confidence 閾値 +0.05)、撤退条件 5レベル

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
