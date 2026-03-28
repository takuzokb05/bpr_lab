# Phase 2 実装計画 — ペーパートレード

> 作成日: 2026-02-14
> 前提: Phase 1 完了（213テスト all pass）、MT5Client 実装済み

---

## 1. Phase 2 スコープ

### 実装対象（F11〜F17）

| ID | 機能名 | ファイル | 依存 |
|----|--------|---------|------|
| F11 | pip_value動的計算 | src/risk_manager.py 修正 | MT5Client |
| F12 | ポジション管理 | src/position_manager.py 新規 | MT5Client |
| F13 | トレーディングループ | src/trading_loop.py 新規 | F11, F12 |
| F14 | 自動キルスイッチ連動 | risk_manager.py + trading_loop.py | F13 |
| F15 | 戦略改善 | src/strategy/ 修正 or 新規 | F8（独立進行可） |
| F16 | Phase 1 送り項目 | 各ファイル修正 | F11 |
| F17 | コードレビュー・統合テスト | tests/ + docs/ | F11〜F16 |

### Phase 1 送り項目の消化（F16 に統合）

| ID | 内容 | 統合先 |
|----|------|--------|
| M1 | pip_value動的計算 | F11 |
| M3 | fill_rate自動適用 | F13 |
| M4 | spread自動適用 | F13 |
| L1 | n_windows自動調整 | F15 |
| L2 | DD自動キルスイッチ | F14 |

---

## 2. 依存グラフと並列化

```
MT5Client ✓（完了）
 │
 ├─→ F11（pip_value動的計算）──┐
 │                              │
 ├─→ F12（ポジション管理）────├─→ F13（トレーディングループ）
 │                              │         │
 │                              │         └─→ F14（キルスイッチ連動）
 │                              │                    │
 └─→ F15（戦略改善）──────────┘                    │
      ↑ researcher + analyst                        │
                                                     ↓
                                              F17（レビュー・テスト）
                                              ↑ code-review + error-handling-audit
                                              ↑ karen + Jenny + task-completion-validator
```

**並列化ポイント**:
- **Step 2**: F11 / F12 / F15 は完全に独立 → **3並列**
- **Step 3**: code-review / error-handling-audit → **2並列**
- **Step 5**: karen / Jenny / task-completion-validator → **3並列**

---

## 3. サブエージェント構成

### 全エージェント一覧（.claude/agents/）

| エージェント | 種別 | Phase 2 での役割 | 有用度 |
|-------------|------|-----------------|--------|
| **researcher** | カスタム | 戦略改善の事前調査（Web検索） | ★★★ 必須 |
| **analyst** | カスタム | 調査結果の安全性/効率性評価 | ★★★ 必須 |
| **karen** | ClaudeCodeAgents | Phase 2 完了時の現実チェック（実際に動くか？） | ★★★ 必須 |
| **Jenny** | ClaudeCodeAgents | SPEC 準拠の検証（仕様 vs 実装のギャップ分析） | ★★★ 必須 |
| **task-completion-validator** | ClaudeCodeAgents | 各F完了時の動作検証（スタブ/未実装の検出） | ★★☆ 有用 |
| **code-quality-pragmatist** | ClaudeCodeAgents | 過剰設計の検出（金融系は安全側に倒すので特に重要） | ★★☆ 有用 |
| **ultrathink-debugger** | ClaudeCodeAgents | MT5 API 接続問題のデバッグ（実行時エラー対応） | ★★☆ 有用（オンデマンド） |
| **claude-md-compliance-checker** | ClaudeCodeAgents | CLAUDE.md 規約準拠チェック | ★☆☆ 補助 |
| **ui-comprehensive-tester** | ClaudeCodeAgents | — | ☆☆☆ 対象外（UIなし） |

### スキル（.claude/skills/）

| スキル | Phase 2 での役割 |
|--------|-----------------|
| **code-review** | 中間+最終レビュー（4観点: 堅牢性・効率性・セキュリティ・保守性） |
| **error-handling-audit** | 中間+最終監査（6カテゴリ: 金融系固有含む） |
| **spec-driven-dev** | Phase 2 SPEC 作成 |

### 組込みエージェント

| エージェント | Phase 2 での役割 |
|-------------|-----------------|
| **general-purpose** | F11/F12/F13/F14 の実装（ファイル読み書き+Bash） |

### Phase 1 での学び

- サブエージェント3並列（F4/F5/F6+F7）は成功 → Phase 2 でも3並列を踏襲
- researcher は `bypassPermissions` が必須（Web検索の権限問題）
- 中間レビュー2回（修正→再レビュー）が品質担保に有効 → Phase 2 でも踏襲
- **新規**: karen / Jenny で「完了詐欺」を防止（Phase 1 では未使用）

---

## 4. 実行ステップ

### Step 1: Phase 2 SPEC 作成（メイン）

- spec-driven-dev スキルで F11〜F17 の詳細仕様を定義
- 完了基準・テストケース・入出力を明確化

### Step 2: 並列実装（3並列サブエージェント）

| Agent | 担当 | subagent_type | mode | 成果物 |
|-------|------|---------------|------|--------|
| **Agent A** | F11: pip_value動的計算 | general-purpose | default | risk_manager.py修正 + テスト |
| **Agent B** | F12: ポジション管理 | general-purpose | default | position_manager.py + テスト |
| **Agent C** | F15: 戦略改善（調査） | researcher | bypassPermissions | 戦略調査レポート |

**Agent C の詳細（2段階）**:
1. **C-1**: researcher で戦略リサーチ
   - MA戦略のパラメータ最適化手法
   - 代替戦略の調査（ブレイクアウト、ミーンリバージョン等）
   - SR > 1.0 達成のための実践的アプローチ
2. **C-2**: analyst で調査結果の評価・推奨
   - 安全性・効率性・実現可能性の3軸で評価
   - 推奨戦略の選定

### Step 3: 中間レビュー（2並列サブエージェント）

F11 / F12 実装完了後:

| Agent | 担当 | 手法 |
|-------|------|------|
| **Agent D** | code-review スキル | 4観点レビュー |
| **Agent E** | error-handling-audit スキル | 6カテゴリ監査 |

→ Critical/High を修正 → 再レビュー（C0/H0 まで）

**オプション**: code-quality-pragmatist を Agent D と並列で追加し、過剰設計チェック

### Step 4: 統合実装（メイン or サブエージェント）

- F13: トレーディングループ（F11 + F12 を統合）
- F14: 自動キルスイッチ連動
- F15: 戦略改善の実装（Step 2 の調査結果を基に）
- **ultrathink-debugger**: MT5 実接続で問題が出たらオンデマンド投入

### Step 5: 最終検証（3段階）

#### 5-a: 最終レビュー（2並列）

| Agent | 担当 |
|-------|------|
| **Agent F** | code-review スキル（全コード最終レビュー） |
| **Agent G** | error-handling-audit スキル（全コード最終監査） |

#### 5-b: 完了検証（3並列） ← **Phase 2 新規**

| Agent | 担当 | 検証内容 |
|-------|------|---------|
| **Jenny** | SPEC準拠検証 | F11〜F16 の実装が SPEC の完了基準を満たすか |
| **task-completion-validator** | 動作検証 | 各機能が実際にエンドツーエンドで動くか |
| **claude-md-compliance-checker** | 規約検証 | CLAUDE.md のルール（日本語コメント、.env管理等）に準拠しているか |

#### 5-c: 現実チェック（karen）

- Step 5-a/5-b の結果を踏まえて **karen** が最終判定
- 「本当に Phase 2 完了と言えるか？」のリアリティチェック
- 未完了項目があれば修正計画を作成

+ カオステスト追加（MT5対応シナリオ）
+ 全テスト実行・合格確認

---

## 5. エージェント連携フロー図

```
                         Step 1: SPEC
                            │
            ┌───────────────┼───────────────┐
            │               │               │
        Step 2-A        Step 2-B        Step 2-C
     general-purpose  general-purpose  researcher
      (F11 pip値)     (F12 ポジション)  (F15 戦略調査)
            │               │               │
            │               │           analyst
            │               │          (戦略評価)
            └───────┬───────┘               │
                    │                       │
               Step 3: 中間レビュー          │
        code-review + error-handling-audit   │
        (+ code-quality-pragmatist)          │
                    │                       │
                    ├───────────────────────┘
                    │
               Step 4: 統合実装
           F13 トレーディングループ
           F14 キルスイッチ連動
           F15 戦略実装
                    │
           [問題時] ultrathink-debugger
                    │
               Step 5-a: 最終レビュー
        code-review + error-handling-audit
                    │
               Step 5-b: 完了検証（3並列）
       Jenny + task-completion-validator
       + claude-md-compliance-checker
                    │
               Step 5-c: 現実チェック
                  karen
                    │
                 完了判定
```

---

## 6. リスクと対策

| リスク | 影響 | 対策 | 投入エージェント |
|--------|------|------|-----------------|
| MT5 API の予期しない挙動 | 実装遅延 | デモ口座で段階的に検証 | ultrathink-debugger |
| 戦略改善で SR > 1.0 未達 | 判定基準未達 | 複数戦略を試す | researcher + analyst |
| サブエージェント間の整合性 | 統合コンフリクト | SPEC でインターフェース厳密定義 | Jenny（ギャップ検出） |
| 完了詐欺（動かないのに完了扱い） | 品質低下 | karen + task-completion-validator | karen チーム |
| 過剰設計 | 複雑化・保守性低下 | code-quality-pragmatist | 中間レビューで検出 |

---

## 7. 成功基準

| 項目 | 基準 |
|------|------|
| テスト | 全テスト pass（既存213 + 新規） |
| コードレビュー | Critical/High 未修正 0件 |
| デモ口座接続 | MT5 デモ口座で発注→決済が正常動作 |
| トレーディングループ | 10分以上の連続稼働（クラッシュなし） |
| キルスイッチ | DD STOP/EMERGENCY で自動停止が発動 |
| 戦略 | SR > 1.0 または代替戦略で DD < 20% + WFE > 50% |
| Jenny検証 | SPEC完了基準を全項目パス |
| karen判定 | 「Phase 2 完了」の現実チェック合格 |

---

## 8. 想定タイムライン

```
Step 1: SPEC作成            ← メイン
Step 2: 3並列実装           ← Agent A + B + C(researcher → analyst)
Step 3: 中間レビュー        ← code-review + error-handling-audit → 修正 → 再レビュー
Step 4: 統合実装            ← メイン (+ ultrathink-debugger オンデマンド)
Step 5-a: 最終レビュー      ← code-review + error-handling-audit
Step 5-b: 完了検証          ← Jenny + task-completion-validator + claude-md-compliance-checker
Step 5-c: 現実チェック      ← karen
```

合計サブエージェント起動回数: 最大13回
並列度ピーク: 3（Step 2, Step 5-b）
