# 実行プラン — エージェントチーム運用

PLAN.md の Phase 0 → Phase 1 を、エージェントチーム分業で効率的に進めるための運用手順。

**参照元**: [PLAN.md](PLAN.md) / [architecture.md](architecture.md) / [review_code.md](review_code.md)

---

## 方針

1. **Phase 0 は逐次**（単一HTML 1292行を全員で触るとコンフリクト不可避）。1人で上から潰す。
2. **Phase 1-A 分離完了後、Phase 1-B / 1-C を並列化**（ファイルが分かれるので衝突しにくい）。
3. **検証は毎フェーズ末に独立エージェントで行う**（実装と検証を分離）。
4. エージェントチームは 3+ 並列が必要になったタイミングで `TeamCreate + SendMessage` を使う。それ未満は `Task run_in_background` で十分。

---

## Phase 0: 逐次実装（所要 2〜3時間、単一実装者）

実装順（依存関係が軽い順）:

| 順 | ID | 内容 | 検証観点 |
|----|-----|------|---------|
| 1 | P0-1 | safeParse 退避（legacy_backup 保存、空配列で上書きしない） | 壊れたJSONをLSに入れてリロード→退避キー生成を確認 |
| 2 | P0-2 | baseTask に schemaVersion: 6 付与 | 新規追加タスクに schemaVersion フィールド |
| 3 | P0-6 | aria 属性追加（dialog / aria-live / aria-label） | DevTools Accessibility ツリー確認 |
| 4 | P0-4 | Undo スタック 5件化（配列化 + トースト連動） | 連続3件削除 → 3回戻せる |
| 5 | P0-3 | 入力 debounce 化（title/note に 300ms） | 連続入力→保存ログ・activityLog が集約 |
| 6 | P0-5 | Survival スロット状態保存（taskState.survivalSlot） | Survival→ABORT→再enter→スロット復元 |

順序根拠: P0-1/P0-2/P0-6 は独立・軽量で最初にリスク潰し。P0-3 と P0-5 は save 経路を触るので schemaVersion 導入後に実施。

### 終了条件
- 手動リグレッション5項目（add / edit / drag / survival / reload）パス
- JSON Export→Import でラウンドトリップ

---

## Phase 1-A: ファイル分離（逐次、週末2日想定）

architecture.md 案A に沿う。1モジュール抽出ごとにリグレッション5項目を実行。

### 抽出順（依存の浅い順）
1. `src/constants.js` — ZONE 定義、KEY名
2. `src/tasks.js` — 純粋関数（baseTask, sortTasks, dueBadge, appendLog）+ **unit test**
3. `src/storage.js` — LS + マイグレーション + legacy_backup
4. `src/render.js` — renderAll を renderZone(zoneId) に分解しながら移植
5. `src/dnd.js` — onDrop コールバック化
6. `src/survival.js` — タイマー + スロット復元
7. `src/app.js` — エントリ

### 成果物
- `index.html`（約40行）+ `styles.css` + `src/*.js`
- `tests/tasks.test.js`（node:test）
- 旧 `タスク管理.html` は跡地案内に差し替え
- ローカル起動手順書（`python -m http.server` or 手順）

---

## Phase 1-B / 1-C: 並列実装（チーム運用）

分離後、以下を **2〜3 エージェント並列** で進める。

### チーム構成案（役割分担）

| 役割 | 担当 | 主な触る領域 |
|------|------|--------------|
| **Stability Eng** | 1-B-1 renderZone, 1-B-2 IndexedDB, 1-B-3 Export UI 昇格 | storage.js / render.js / app.js |
| **A11y Eng** | 1-B-4 D&D キーボード代替 | dnd.js / app.js / styles.css |
| **Feature Eng** | 1-C-5 Today ビュー → 1-C-6 Task Score → 1-C-7 Review バッジ | render.js / tasks.js / new: src/today.js |

### 並列化判断
- 2エージェント並列 → `Task(run_in_background: true)` を同一メッセージで発射
- 3エージェント並列 → `TeamCreate + SendMessage`（memoryの落とし穴参照: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 必要）

### マージ衝突回避
- render.js は Stability と Feature が両方触る。先に renderZone 化（1-B-1）を単独で完了させてから 1-C に着手
- 各エージェントに「他エージェントが触らないファイル範囲」を明記して渡す

---

## Phase 2 は見送り判断を入れる

Phase 1 完走後、実運用 2〜4週間のログ（activityLog）を見てから Phase 2 の選別。優先順はユーザー自身の詰まり箇所次第。

---

## エージェント投入時の厳守事項

1. **ブローカーでなく実装者として依頼**: 「修正方針の検討」ではなく「該当行をこう書き換える」レベルの指示を渡す
2. **リグレッション手順を必ず同梱**: 5項目チェック済みを復路で要求
3. **bypassPermissions + Write/Edit 許可** をサブエージェント起動時に設定（memory の落とし穴参照）
4. **1タスク10分以内で返る粒度**に切る。超えるなら分割

---

## 進捗トラッキング

本セッションでは `TaskCreate` に Phase 0 の6件を落として逐次実行する。Phase 1 に入るタイミングで改めて細分化。
