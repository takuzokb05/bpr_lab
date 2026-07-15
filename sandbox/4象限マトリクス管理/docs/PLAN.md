# Neuro Matrix Task OS — 統合改善プラン

4エージェントチームによる UI/UX・コード・競合・アーキテクチャの4観点レビューを統合した、優先度付き改善ロードマップ。

**参照**:
- [review_uiux.md](review_uiux.md) — UI/UX レビュー
- [review_code.md](review_code.md) — コード品質と Why の深堀
- [benchmark.md](benchmark.md) — 競合タスク管理ツールからの輸入候補
- [architecture.md](architecture.md) — ファイル分離と安定化の設計

---

## エグゼクティブサマリ

現状（`タスク管理.html` 1292行、単一HTML）は**4象限思想が一等地に据えられた稀少なプロダクト**で、Survivalモードという独自のアイデアが光る。一方で、

1. **データ損失リスクが1件ある**（マイグレーション失敗で空配列を保存）
2. **入力1文字ごとに全面再描画 + 全保存 + 履歴ログが積まれる**設計
3. **D&Dはキーボード操作不可、色覚依存、aria属性欠落**
4. **機能として「堆積防止（Review/Migration）」と「開始摩擦（Focus/Pomodoro）」が欠けている**
5. **単一HTMLが配布性を高めている反面、保守・テスト・CSPに制約**

これらを **Phase 0（緊急）→ Phase 1（分離 + コア機能）→ Phase 2（機能拡張）** の3段階で解く。

---

## 保全すべき強み（壊さない）

- オフライン完結（サーバー不要・ネット不要）
- `file://` でも動く配布性
- 4象限 + Survivalモードの独自 UX
- LocalStorage 1層のシンプル永続化（拡張はするが置換しない）
- 個人1人・シンプル志向（階層タスク、プロジェクト、チーム機能は**入れない**）

---

## Phase 0: 緊急パッチ（所要2〜3時間 / 単一HTMLのまま）

**目的**: データ損失リスクを止め、触り心地の最大の悪さ（1文字ごと再描画）を潰す。分離作業の前にやる。

| # | 内容 | 箇所 | 効果 | 工数 |
|---|------|------|------|------|
| P0-1 | マイグレーション退避: `safeParse` 失敗時は `legacy_backup` キーに退避、空配列で上書きしない | `:608-637` | データ消失事故ゼロ化 | 30分 |
| P0-2 | 各タスクに `schemaVersion: 6` を付与 | `baseTask :591` | 将来マイグレーションの基盤 | 15分 |
| P0-3 | 入力の debounce 化（title/note に 300ms デバウンス、`logEvent('updated')` も同期間集約） | `:767-773, 844-849` | IMEぶつかり解消、履歴汚染解消、保存コスト激減 | 45分 |
| P0-4 | Undo スタックを 5 件に拡張（`lastDeletedSnapshot` → 配列） | `:1059-1092` | 連続削除時の取り戻し不可を解消 | 30分 |
| P0-5 | Survivalモードでスロット割り当て状態を `taskState.survivalSlot` に保存、exit→再enterで復元 | `:1205-1228` | ABORT 後も意思決定が消えない | 30分 |
| P0-6 | aria 最低限: `role="dialog"` on `survival-overlay`、`aria-live="polite"` on `undo-toast`、象限に `aria-label` | `:464, 482, 447-450` | SR利用者に意味が届く | 15分 |

このフェーズでビッグバン移行前にユーザー体験が目に見えて向上する。

---

## Phase 1: ファイル分離 + コア機能強化（1〜3週間）

**目的**: 保守性・テスト可能性を上げ、ベンチマークで効果が高く実装軽量な機能を3件入れる。

### 1-A. 分離（architecture.md 案A 採用）

```
4象限マトリクス管理/
├── index.html                  # 40行程度、マークアップのみ
├── styles.css                  # 430行程度、CSS分離
├── src/
│   ├── constants.js            # ゾーン定義、キー名
│   ├── tasks.js                # 純粋関数（baseTask, sortTasks, dueBadge, appendLog）
│   ├── storage.js              # LocalStorage + マイグレーション
│   ├── render.js               # zone単位の部分再描画
│   ├── dnd.js                  # ドラッグ&ドロップ（onDropコールバック渡し）
│   ├── survival.js             # Survivalモードとタイマー
│   └── app.js                  # エントリ、配線
├── tests/
│   ├── tasks.test.js           # node:test で純粋関数テスト
│   └── e2e/                    # Playwright 3本（D&D / Survival / migration）
└── docs/                       # 本ディレクトリ
```

- ビルド不要、`<script type="module">` で動く
- `file://` では CORS 制約に当たるため、配布は `python -m http.server` またはローカルで開く手順書を添える
- 案B（Vite + singlefile）は**必要になってから**導入（当面は案Aで止める判断）
- 旧 `タスク管理.html` は**跡地案内**を入れて残す（既存ブックマーク破壊回避）

### 1-B. コア安定化（分離と同時に実施）

| # | 内容 | 根拠 | 効果 |
|---|------|------|------|
| P1-1 | `renderAll()` を `renderZone(zoneId)` に分解、影響ゾーンのみ描画 | review_code.md M2 | スクロール位置・フォーカス保持、100タスク時の体感が変わる |
| P1-2 | IndexedDB ミラー層を追加（LocalStorageを主、IDBを控え） | architecture.md §5 | 容量限界対策、壊れても復元可能 |
| P1-3 | JSON Export / Import をUIに昇格（現 `window.neuroMatrixDebug` を「設定」メニューに移動） | review_code.md §D | 自己バックアップ可能 |
| P1-4 | D&D キーボード代替（象限移動ボタン、Space/矢印キー） | review_uiux.md C3 | アクセシビリティ起点、マウス疲れ対策にもなる |

### 1-C. 機能輸入（benchmark.md Top 10 から S 難度 3件）

| # | 機能 | 元ネタ | 効果 |
|---|------|------|------|
| P1-5 | **Today ビュー**（今日締切 + 期限超過のみを縦リスト表示） | Things 3 | 朝「何をやるか」選択麻痺解消。Q1/Q3に散ったタスクを一望 |
| P1-6 | **Task Score 自動ソート**（updated が古く締切近いものを同象限内で上に） | Amplenote | 放置タスクが勝手に浮上、Q2腐敗を抑える |
| P1-7 | **Review バッジ（Q2限定）**（14日触らないQ2タスクに警告バッジ） | OmniFocus | Q2（重要非緊急）の腐敗を検知 |

---

## Phase 2: 機能拡張（必要になってから）

### 2-A. 開始摩擦解消

| # | 機能 | 元ネタ | 備考 |
|---|------|------|------|
| P2-1 | **ポモドーロタイマー（25+5）+ Focus Mode**（選択1タスクだけ表示） | TickTick/SuperProd | Survivalモードと**排他**。Survivalは締切プレッシャー、Focusは着手プレッシャー |
| P2-2 | **CBT 先延ばし問いかけ**（長期Q1で「次の最小1ステップは？」プロンプト） | SuperProductivity | Q1塩漬け対策 |

### 2-B. 入力摩擦解消

| # | 機能 | 元ネタ | 備考 |
|---|------|------|------|
| P2-3 | **自然言語 Quick Add**（「資料提出 明日 Q1」→ パースして象限+締切設定） | Todoist | 実装M難度、ルーチン入力が激減 |
| P2-4 | **Magic Plus**（象限内で任意位置にカード挿入） | Things 3 | 順序が意味を持つ運用時に効く |

### 2-C. 堆積防止

| # | 機能 | 元ネタ | 備考 |
|---|------|------|------|
| P2-5 | **Monthly Migration ウィザード**（月1で全タスクを「継続/削除/象限変更」のバッチ操作） | Bullet Journal | Q4堆積を月1で掃除 |
| P2-6 | **Daily Shutdown Ritual**（終業時「今日の3件」と「明日に持ち越すもの」の振り返りUI） | Sunsama | 日次の締め切り儀式で切り替え |
| P2-7 | **軽量Markdownメモ**（メモ欄で `**bold**` `- list` だけレンダリング） | Amplenote/Notion | Notionまで行かない最小限 |

### 2-D. 配布・CI（必要時）

- Vite + `vite-plugin-singlefile` 導入で「単一HTML配布」に戻す道を確保
- GitHub Pages or ZIP配布
- Playwright E2E を GitHub Actions で自動化

---

## やらない判断（アンチパターン）

| 項目 | 理由 |
|------|------|
| Motion/Reclaim の AI 自動スケジューリング | オフライン単一HTMLの思想に反する |
| Trello Butler 級の自動化DSL | 設定迷子、個人1人では過剰 |
| Notion ブロックエディタ | スコープ外、再実装が巨大 |
| プロジェクト階層・サブタスク階層 | 4象限の「1階層でさばく」思想と衝突 |
| チーム機能・共有 | ユーザー要件外 |
| ハビットトラッカー・ゲーミフィケーション・Streak | ADHD で反転リスク（1日抜けると全部投げる） |
| React/Vue 等の重量フレームワーク | `npm install` 前提が制約に合わない |

---

## 優先度一覧（実施順）

1. **Phase 0 全6件**（2〜3時間で完了、即日効果）
2. **Phase 1-A 分離**（週末1〜2日）
3. **Phase 1-B 安定化 4件**（分離と同時 or 直後）
4. **Phase 1-C 機能輸入 3件**（Today ビュー → Task Score → Review バッジ の順）
5. **Phase 2 は使いながら必要性を見極めて選択**

---

## リスクと対策

| リスク | 発生フェーズ | 対策 |
|--------|-----------|------|
| 分離中に既存ユーザー（自分）のLocalStorageが壊れる | Phase 1-A | 各フェーズ開始前に**JSON Export を手動実行**、`legacy_backup` キーへ退避 |
| モジュール分割でD&Dが壊れる | Phase 1-A | 1モジュール抽出ごとに手動リグレッション5項目（add/edit/drag/survival/reload） |
| Phase 1-C の機能追加で象限UIが情報過多化 | Phase 1-C | Today ビューはタブ切替で隔離、Review バッジはQ2専用に限定 |
| Pomodoro と Survival の競合 | Phase 2-A | 排他制御（同時起動不可）、設計時に先にUI遷移図を描く |

---

## 次の一手

この PLAN.md を読んで、Phase 0 の 6 項目から着手するのが最もコスパが良い。Phase 0 は単一HTMLのままやれるので、分離に踏み切る前にユーザー体験とデータ安全性が底上げされる。

Phase 0 の実装に入るなら次のセッションで個別タスクに落として進める。
