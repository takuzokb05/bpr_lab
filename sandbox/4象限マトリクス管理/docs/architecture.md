# アーキテクチャ設計提案

対象: `タスク管理.html`（1292行、単一HTML、HTML + 内蔵CSS + IIFE内の素のJS）

## 推奨案（結論先出し）

**段階的移行、最終形は案B（Vite + singlefile）。ただし直近3週間は案Aで止める。**

- **Phase 0（即日〜1週間）**: 単一HTMLのまま「安定化のクイックウィン」だけ先に打つ。debounce、部分再描画、Undoキュー、マイグレーション退避、`schemaVersion` 付与。ビッグバン移行の事故を避ける。
- **Phase 1（1〜3週間）**: 案A（ES Modules + 手ロード）に分離。`index.html` + `styles.css` + `src/*.js` 構成で `<script type="module">` 方式。開発は `python -m http.server` か VS Code Live Server で回す（どちらもnpm不要）。配布は「フォルダごとzip + ダブルクリックで `index.html` を開く」で済ませる。
- **Phase 2（必要になったら）**: 案B（Vite + `vite-plugin-singlefile`）。配布物を単一HTMLに戻したくなった時点で導入。公務員PCで `npm install` が通らなければPhase 1で止めてよい。

**判断理由**:
- 案A単独だと `file://` で ES Modules の動的import/同一オリジン制約に引っかかる。ローカルサーバー起動が必須になる時点で「ダブルクリックで開く」が崩れる。
- ただし「自PC内で小サーバーを叩く」運用は許容範囲。npm不要・インストール不要（Pythonは標準搭載、VS Codeの拡張1クリック）。
- 案Bは配布時に単一HTMLへ戻せるのが最大の利点だが、`node`/npm環境のメンテが公務員PCで継続可能か不透明。必要になったら足す、で十分。

---

## 前提と制約

| 項目 | 内容 |
|------|------|
| 利用者 | 個人1名（公務員、業務外PC運用） |
| オフライン動作 | 絶対維持（外部CDN依存も避ける） |
| ビルド必須FW | 不採用（React/Vue/Svelte等） |
| `file://` 動作 | 極力維持。ただし案A採用時はローカルサーバー経由を許容 |
| npm install | 避けたい。必須なら最小限 |
| 壊したくない機能 | LocalStorage永続化、v5→v6マイグレーション、D&D、Survivalモード、アクティビティログ |

---

## 案A: 最小構成（ES Modules + 手ロード）

### ディレクトリ構成

```
4象限マトリクス管理/
  index.html              # <link rel="stylesheet"> と <script type="module" src="src/app.js">
  styles.css              # 現 <style> を丸ごと移動
  src/
    app.js                # エントリ。DOM取得とイベント配線のみ
    storage.js            # LocalStorage / IndexedDB / マイグレーション
    tasks.js              # 純粋関数: baseTask, sortTasks, dueBadge, logEvent, cloneTask
    dnd.js                # pointerdown/move/up、placeholder、drop判定
    survival.js           # enter/exit/toggleSurvival, startTimer
    render.js             # renderAll, renderActiveZones, renderCompleted, refreshMeta
    dom.js                # DOM参照のキャッシュ（matrix, completedPanel 等）
    constants.js          # KEY_DATA, ACTIVE_ZONES, NORMAL_ZONES, SCHEMA_VERSION
  docs/
  tests/
    unit/
      tasks.test.mjs      # node:test で純粋関数テスト
      migrate.test.mjs
    e2e/
      smoke.spec.js       # Playwright（任意）
  タスク管理.html          # 旧版を残す（跡地案内）
```

### トレードオフ

**得られるもの**:
- モジュール境界で変更影響が局所化する。D&Dの修正がSurvivalに波及しない。
- 純粋関数を `tasks.js` に切り出せばnode標準の `node:test` で単体テストが書ける。
- CSS編集が高速化（HTML内の巨大 `<style>` を行ったり来たりしなくて済む）。

**失われるもの**:
- **ダブルクリックでHTMLを開く運用が `file://` 環境では動かない**（モジュール読込がCORSブロック）。`python -m http.server 8000` を立てるか、VS Code Live Serverを起動する1手が増える。
- 配布が「フォルダごと」になる。単一ファイルを誰かにメール添付する運用はしづらい（個人利用なので影響は小さい）。

### file:// で動くか

**動かない（案A単独では）**。Chrome/Edgeは `file://` からの ES Modules import をセキュリティ上ブロックする。回避策:

1. **ローカルサーバーを立てる**（推奨）: `python -m http.server 8000` をタスクスケジューラでログオン時自動起動、ブラウザのお気に入りに `http://localhost:8000/index.html` を登録。
2. **`<script>` を classic で連結**: `type="module"` をやめ、IIFEを並べて依存順にロード。`export`/`import` が使えず実質「巨大IIFE」のままになるので分離の旨味が消える。非推奨。
3. **案Bに進む**: ビルド時に単一HTMLにインライン化して `file://` 動作を回復。

---

## 案B: Vite + singlefile ビルド

### ディレクトリ構成

```
4象限マトリクス管理/
  package.json            # vite, vite-plugin-singlefile, @playwright/test（devDependenciesのみ）
  vite.config.js
  index.html              # 開発用
  src/                    # 案Aと同じ分割
  styles.css
  dist/
    index.html            # ビルド成果物。CSS/JSがインライン化された単一HTML
  tests/
```

### vite.config.js（骨子）

```js
import { defineConfig } from 'vite'
import { viteSingleFile } from 'vite-plugin-singlefile'

export default defineConfig({
  plugins: [viteSingleFile()],
  build: { target: 'es2020', cssCodeSplit: false, assetsInlineLimit: 100000000 }
})
```

### トレードオフ

**得られるもの**:
- **開発は分離、配布は単一HTML**。現状の「ダブルクリックで開く」強みを100%保持。
- `npm run dev` でHMR。保存即反映で編集体験が大きく上がる。
- Playwrightと統合しやすい（`npm test`一発）。

**失われるもの**:
- `npm install` が必須。公務員PCでプロキシ/権限がアウトだと導入不可。
- 依存（vite, plugin）を年1回は更新する運用が発生。放置すると脆弱性警告が溜まる。
- ビルドを忘れると配布物が古い状態で出回る（`dist/` コミット前にビルド必須）。

### file:// で動くか

**`dist/index.html` は動く**（単一HTMLだから）。開発中の `index.html` は `npm run dev` でサーバー経由。

---

## 比較表

| 観点 | 現状（単一HTML） | 案A（ES Modules） | 案B（Vite+singlefile） |
|------|---------------|------------------|----------------------|
| `file://` ダブルクリック起動 | ◎ | × | ◎（dist） |
| 編集しやすさ（1292行） | △ | ○ | ◎（HMR） |
| npm必要 | 不要 | 不要 | 必要 |
| テスト容易性 | × | ○（node:test） | ◎ |
| 依存メンテ負荷 | ゼロ | ゼロ | 年数回 |
| 公務員PC導入可否 | ◎ | ◎ | △（プロキシ次第） |
| 配布物サイズ | 1ファイル | フォルダ一式 | 1ファイル |
| 学習コスト | ゼロ | 低 | 中 |
| 推奨 | Phase 0のみ | **Phase 1で採用** | Phase 2（必要時） |

---

## モジュール分割設計

### 依存関係図

```
                  constants.js
                       ^
                       |
          +------------+------------+
          |            |            |
       dom.js      tasks.js     storage.js
          ^            ^            ^
          |            |            |
          +------+-----+------+-----+
                 |            |
              render.js    survival.js
                 ^            ^
                 |   dnd.js   |
                 |     ^      |
                 +-----+------+
                       |
                     app.js
```

### 各モジュール仕様

#### `constants.js`
**責務**: 変更不能な定数、スキーマバージョン。
**公開API**:
```js
export const SCHEMA_VERSION = 6;
export const KEY_DATA = 'neuro_matrix_v6_data';
export const KEY_STATE = 'neuro_matrix_v6_state';
export const KEY_LEGACY_BACKUP = 'neuro_matrix_legacy_backup';
export const LEGACY_DATA = 'neuro_matrix_v5_data';
export const LEGACY_STATE = 'neuro_matrix_v5_state';
export const ACTIVE_ZONES = ['q1','q2','q3','q4','survival-picker','slot-must','slot-should'];
export const NORMAL_ZONES = ['q1','q2','q3','q4'];
export const DEBOUNCE_MS = 300;
export const UNDO_STACK_MAX = 5;
export const UNDO_TTL_MS = 5000;
```
**依存**: なし。

#### `dom.js`
**責務**: `document.getElementById` の一括キャッシュ。テスト時にモックしやすくする。
**公開API**:
```js
export const el = {
  matrix: null, completedPanel: null, completedList: null,
  survivalOverlay: null, targetTimeInput: null,
  undoToast: null, undoMessage: null, countdown: null, /* ... */
};
export function initDom() { /* 一括取得 */ }
```
**依存**: なし。

#### `tasks.js`（純粋関数層）
**責務**: タスクモデルの生成・並べ替え・判定。副作用なし。**全関数がテスト可能**。
**公開API**:
```js
export function nowIso();
export function todayString();
export function baseTask(overrides);            // デフォルト値でタスク生成
export function cloneTask(task);                // 深いコピー
export function sortTasks(activeTasks);         // 締切→updatedAt降順
export function dueBadge(task, today=todayString()); // { label, className }
export function formatDateTime(value);
export function formatDueDate(value);
export function appendLog(task, type, detail);  // ミュータブル。testはクローン渡しで
```
**依存**: `constants.js` のみ。
**テスト**: `node:test` で全網羅。

#### `storage.js`（永続化層）
**責務**: LocalStorage/IndexedDBアクセス、マイグレーション、エクスポート/インポート。
**公開API**:
```js
export function loadTasks();          // { tasks, uiState }
export function saveTasks(tasks);     // debounced内部呼び出し向けの即時版
export function saveState(uiState);
export function scheduleSave(tasks, uiState);  // requestIdleCallback + debounce
export function migrateLegacyIfNeeded();       // v5→v6、失敗時はlegacy_backupへ退避
export function exportJson();                  // Blob DL用文字列
export function importJson(jsonString);        // 検証→差し替え
export async function mirrorToIndexedDB(tasks); // 層2書き込み
export async function restoreFromIndexedDB();   // LocalStorage崩壊時の救済
export function getStorageHealth();            // クオータ・書込失敗の状態
```
**依存**: `constants.js`, `tasks.js`。
**テスト**: `migrateLegacyIfNeeded` をnode環境でモックLocalStorage相手に単体テスト。

#### `render.js`（DOM差分描画層）
**責務**: タスク配列 → DOM。ゾーン単位で部分再描画。
**公開API**:
```js
export function renderZone(zoneId, tasks, uiState);  // 1ゾーンだけ
export function renderAll(tasks, uiState);           // 全ゾーン（初期化・大規模変更時）
export function renderCompleted(tasks);              // 完了パネル
export function renderCounts(tasks);                 // 件数バッジ
export function refreshCardMeta(card, task);         // カード1枚のメタのみ更新
export function createTaskCard(task, handlers);      // handlers: {onComplete, onDelete, onEdit, onNoteEdit, onDueChange}
```
**依存**: `tasks.js`, `dom.js`。
**差分化方針**: カードDOMに `data-task-id` を振り、更新時はDOMを作り直すのではなく既存要素に `refreshCardMeta` する。ゾーン変更時のみ `createTaskCard` を呼ぶ。

#### `dnd.js`（ドラッグ&ドロップ層）
**責務**: pointerイベント・placeholder・drop判定。
**公開API**:
```js
export function enableDnd(container, { onDrop, getActiveZones });
// onDrop(taskId, targetZoneId) がrender側/app側に委譲
export function disableDnd(container);
```
**依存**: `dom.js` のみ（`tasks.js`には依存させない＝純粋にUIレイヤ）。
**ポイント**: 状態更新は自前でやらず `onDrop` コールバック経由。

#### `survival.js`
**責務**: Survivalモードの入退場、ゾーン退避、カウントダウンタイマー。
**公開API**:
```js
export function enterSurvival(tasks);     // tasksをミュータブルに書き換え
export function exitSurvival(tasks);
export function startTimer(targetTimeInput, countdownEl);
export function stopTimer();
```
**依存**: `constants.js`, `tasks.js`。

#### `app.js`（エントリ）
**責務**: 起動、イベント配線、状態オーケストレーション。**ロジックは書かない**。
**骨子**:
```js
import { initDom, el } from './dom.js';
import * as storage from './storage.js';
import * as render from './render.js';
import * as dnd from './dnd.js';
import * as survival from './survival.js';
import { baseTask, appendLog, cloneTask } from './tasks.js';

let tasks = [];
let uiState = {};
let undoStack = [];   // 最大5件

initDom();
({ tasks, uiState } = storage.loadTasks());
wireEvents();
render.renderAll(tasks, uiState);

function wireEvents() { /* add-btn, completed-toggle, survival-btn, etc. */ }
```

---

## 永続化の冗長化

### 層1: LocalStorage（現状継続）

- キー: `neuro_matrix_v6_data`, `neuro_matrix_v6_state`
- **書き込みポリシー**:
  - タイトル/メモ編集は **300ms debounce**（現状: 1文字ごとに `saveAll()` → 履歴肥大＋重い）。
  - Undo対象のイベント（削除/完了/移動）は **即座に保存**。
  - 書込ラップ関数 `scheduleSave()` を経由し、`requestIdleCallback`（未対応ブラウザは `setTimeout(fn, 0)`）でメインスレッドを空けてから書く。
- **エラー検知**:
  - `try/catch` で `QuotaExceededError` を捕捉。
  - ヘッダに「保存エラー」バナー表示（赤背景）、クリックでJSONエクスポートを促す。
  - `getStorageHealth()` を起動時に呼び、失敗時はIndexedDBからの復元を提案。

### 層2: IndexedDB（追加）

- **用途**: 容量上限（LS: 5〜10MB、IDB: 数百MB〜GB）の保険、履歴消去耐性（ブラウザのサイト毎データ削除は両方消えるが、シークレットモード/別プロファイルでは独立）。
- **実装**: 依存ライブラリなしで `indexedDB.open('neuro_matrix', 1)` + `objectStore('snapshots')` 直書き。idb-keyvalのような薄い依存も許容可。
- **書き込みタイミング**: LocalStorage書込成功のたびに非同期ミラーリング（awaitしない）。
- **復元**: LocalStorageが空 or 読込失敗時、起動時に `restoreFromIndexedDB()` でフォールバック。

### 層3: JSON export/import（手動バックアップ）

- ヘッダに `エクスポート` / `インポート` ボタン追加。
- エクスポート: `{ schemaVersion: 6, exportedAt: ISO, tasks: [...], uiState: {...} }` を `Blob` でダウンロード。ファイル名 `neuro-matrix-YYYY-MM-DD.json`。
- インポート: ファイル選択 → スキーマ検証 → 確認ダイアログ → 差し替え or マージ。
- **7日ごとにエクスポート促しトースト**（最終エクスポート日時を `uiState` に保存）。

### 書き込みパイプライン

```
編集イベント
  → appendLog(task, type, detail)   （同期、純粋）
  → scheduleSave(tasks, uiState)     （debounce 300ms）
      → requestIdleCallback
          → LocalStorage書込（try/catch、失敗時バナー）
          → IndexedDBミラー（非同期、awaitしない）
  → 部分再描画（ゾーン単位 or カード単位）
```

---

## 安定化のクイックウィン（ビッグバン移行前に打つ手）

**優先度順。現状の単一HTMLのままでも全部実装可能。**

### P0（今日やる）

1. **マイグレーション失敗時の退避**
   - `migrateLegacyIfNeeded()` の先頭で `localStorage.setItem('neuro_matrix_legacy_backup', JSON.stringify({data: legacyData, state: legacyState, at: nowIso()}))`。
   - 既存の `legacy_data`/`legacy_state` **削除処理は今は書かない**（現状も消してないので維持）。
   - **効果**: マイグレーションバグでv5データが壊れても復旧可能。

2. **各タスクに `schemaVersion` を持たせる**
   - `baseTask()` で `schemaVersion: 6` を付与。
   - 次回v7マイグレーション時、タスク単位で未処理タスクを見分けられる（全体ローテーションより安全）。

3. **Undoトーストを1件→5件キュー**
   - `lastDeletedSnapshot` を `undoStack: []` に変更、`push` + `shift` で `UNDO_STACK_MAX=5`。
   - `undoDelete()` は `pop()`。
   - トーストには「最新削除: タイトル」を表示、クリックで最新から復元。
   - **効果**: 連続削除した時の取り返しがつく（現状は最後の1件だけ復元可能）。

### P1（今週やる）

4. **タイトル/メモ編集のdebounce**
   - `input` イベントで `saveAll()` と `logEvent('updated')` を **300ms debounce**。
   - IMEの連続入力・1文字編集のたびに履歴が膨れて保存が走る現象を解消。
   - 注意: `updated` ログはdebounceするが、`blur` 時には強制flush。

5. **部分再描画**
   - `renderAll()` を呼んでいる箇所を精査し、ゾーン単位 `renderZone(zoneId)` に置換:
     - `moveTask` → `renderZone(from)` + `renderZone(to)`
     - `completeTask`/`reopenTask` → `renderZone(task.zone)` + `renderCompleted()`
     - `addTask` → `renderZone(targetZone)`
     - `deleteTask` → `renderZone(task.zone)`
     - タイトル/メモ編集 → `refreshCardMeta(card, task)` のみ（既にある）
   - `loadAll()` と Survival遷移のみ `renderAll()` を残す。
   - **効果**: カード数が増えた時のスクロール位置リセット・フォーカス消失を防ぐ。

6. **書き込みを `requestIdleCallback` 化**
   - `saveAll()` を `scheduleSave()` でラップ。UIブロック回避。

### P2（2週目〜）

7. **LocalStorage書込エラー検知バナー**
8. **IndexedDBミラーリング導入**
9. **JSON export/importボタン追加**
10. **定期エクスポート促しトースト**

---

## テスト戦略

### 対象の層別マトリクス

| 対象 | 戦略 | 実行方法 |
|------|------|---------|
| `tasks.js`（純粋関数） | **単体テスト必須** | `node --test tests/unit/*.test.mjs` |
| `storage.js`（マイグレーション） | **単体テスト必須**（localStorage をモック） | 同上 |
| `storage.js`（IndexedDB） | 手動確認 or E2E | ブラウザ |
| `dnd.js` | **E2E（Playwright）**、最小限 | `npx playwright test` |
| `survival.js`（タイマー） | 単体（日付モック） + 目視 | node + ブラウザ |
| `render.js` | スナップショット不要、E2E内で暗黙検証 | Playwright |

### `node:test` サンプル（`tests/unit/tasks.test.mjs`）

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { baseTask, sortTasks, dueBadge } from '../../src/tasks.js';

test('baseTask: 不正zoneはq4にフォールバック', () => {
  const t = baseTask({ zone: 'invalid' });
  assert.equal(t.zone, 'q4');
  assert.equal(t.normalZone, 'q4');
});

test('sortTasks: 締切昇順、同一なら更新降順', () => {
  const a = baseTask({ dueDate: '2026-04-20', updatedAt: '2026-04-01T00:00Z' });
  const b = baseTask({ dueDate: '2026-04-20', updatedAt: '2026-04-02T00:00Z' });
  const c = baseTask({ dueDate: '2026-04-10', updatedAt: '2026-03-01T00:00Z' });
  const sorted = sortTasks([a, b, c]);
  assert.deepEqual(sorted.map(t => t.id), [c.id, b.id, a.id]);
});

test('dueBadge: 期限超過判定', () => {
  const t = baseTask({ dueDate: '2020-01-01' });
  const today = '2026-04-17';
  assert.equal(dueBadge(t, today).className, 'overdue');
});
```

### マイグレーションテスト（最重要）

```js
// tests/unit/migrate.test.mjs
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

// LocalStorageモック
class MockStorage {
  constructor() { this.data = new Map(); }
  getItem(k) { return this.data.get(k) ?? null; }
  setItem(k, v) { this.data.set(k, String(v)); }
  removeItem(k) { this.data.delete(k); }
}

beforeEach(() => { globalThis.localStorage = new MockStorage(); });

test('v5データがv6形式にマイグレーションされる', async () => {
  localStorage.setItem('neuro_matrix_v5_data', JSON.stringify([
    { id: 'x', text: 'old task', zone: 'q1' }
  ]));
  const { migrateLegacyIfNeeded, loadTasks } = await import('../../src/storage.js');
  migrateLegacyIfNeeded();
  const { tasks } = loadTasks();
  assert.equal(tasks.length, 1);
  assert.equal(tasks[0].title, 'old task');
  assert.equal(tasks[0].zone, 'q1');
  assert.ok(localStorage.getItem('neuro_matrix_legacy_backup'));
});

test('v6データが既にあればマイグレーションしない', async () => {
  localStorage.setItem('neuro_matrix_v6_data', JSON.stringify([{ id: 'new' }]));
  localStorage.setItem('neuro_matrix_v5_data', JSON.stringify([{ id: 'old', text: 'legacy' }]));
  const { migrateLegacyIfNeeded, loadTasks } = await import('../../src/storage.js');
  migrateLegacyIfNeeded();
  const { tasks } = loadTasks();
  assert.equal(tasks[0].id, 'new');
});
```

### Playwright E2E（最小）

```js
// tests/e2e/smoke.spec.js
import { test, expect } from '@playwright/test';

test('D&D: q4からq1へ移動', async ({ page }) => {
  await page.goto('http://localhost:8000/');
  await page.click('#add-btn');
  await page.fill('.card .card-title', 'テスト');
  const card = page.locator('.card').first();
  const q1 = page.locator('#q1');
  await card.dragTo(q1);
  await expect(q1.locator('.card')).toHaveCount(1);
});

test('Survival: モード切替でゾーン移動', async ({ page }) => {
  await page.goto('http://localhost:8000/');
  await page.click('#add-btn');
  await page.click('#survival-btn');
  await expect(page.locator('#survival-picker .card')).toHaveCount(1);
});

test('マイグレーション: v5キーからv6へ', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('neuro_matrix_v5_data', JSON.stringify([{ id: 'a', text: 'legacy', zone: 'q2' }]));
  });
  await page.goto('http://localhost:8000/');
  await expect(page.locator('#q2 .card')).toHaveCount(1);
  await expect(page.locator('#q2 .card .card-title')).toHaveValue('legacy');
});
```

### テスト不能 or 諦める領域

- **iOS Safariのpointer挙動差分**: Playwrightは再現しきれない。目視確認でカバー。
- **実クオータ超過**: IDB含め実ブラウザでしか再現しない。手動確認項目としてチェックリスト化。
- **年跨ぎ・タイムゾーン**: 日付モックで単体テスト可能だが、優先度低。

### 実行

- Phase 1: `node --test tests/unit/**/*.test.mjs` をpackage.jsonの `scripts.test` に。npm不要でも `node` さえあれば動く。
- Phase 2以降: `npm test` で単体+E2Eを連続実行。

---

## マイグレーション計画（v6単一HTML → 分離版への移行）

**データマイグレーションは発生しない**（キー名・スキーマ不変）。発生するのは **コード構造の移行**のみ。

### ステップ

1. **Phase 0（1日）: クイックウィン反映**
   - 単一HTMLのまま P0 の3項目（退避・schemaVersion・Undoキュー5件）を適用。
   - git commit: `feat(四象限): v6安定化クイックウィン`
   - 手動確認: 追加・編集・削除・Undo・Survival遷移・リロード。

2. **Phase 1a（1日）: ファイル作成とコピー**
   - `index.html` を新規作成、現HTMLの `<body>` 以降をコピー。`<style>` を `styles.css` に切り出し `<link>` で参照。
   - `<script>` 内のIIFE本体を `src/app.js` に丸コピー。`<script type="module" src="src/app.js">`。
   - **この時点では単一ファイル→2ファイルへの分解のみ**。モジュール化はまだ。
   - ローカルサーバーで動作確認。

3. **Phase 1b（2〜3日）: モジュール抽出**
   - 順序: `constants.js` → `tasks.js` → `storage.js` → `dom.js` → `render.js` → `dnd.js` → `survival.js`。
   - **1モジュール抽出するごとに手動リグレッション**（add/edit/drag/survival/reload）。
   - 純粋関数が抽出できた段階で `tests/unit/` を並行追加。
   - git: モジュールごとに1コミット。

4. **Phase 1c（1日）: クイックウィン P1/P2 の残りを反映**
   - debounce、部分再描画、IndexedDBミラー、JSON export/import。

5. **Phase 1d（1日）: 旧HTMLのリタイア**
   - `タスク管理.html` は削除せず、先頭に以下の跡地案内を挿入:
     ```html
     <!DOCTYPE html><meta charset="UTF-8">
     <p>このファイルはv6単一版のアーカイブ。現行版は <a href="./index.html">index.html</a>。</p>
     ```
   - ファイル名変更せず、旧運用（ブックマーク）を壊さない。

6. **Phase 2（判断後）: Vite導入**
   - `package.json` 追加、`vite.config.js` 作成、`npm run build` → `dist/index.html` 生成。
   - 配布は `dist/index.html` を単一ファイルで配る運用に戻す。

### リスクと退避

- **各Phaseの開始前にブラウザのLocalStorageをJSONエクスポート**（今すぐ運用化）。
- Phase 1b でバグったら `git revert` で単一HTMLに即戻し。
- `file://` 運用に戻したくなったらPhase 2（Vite）にジャンプ、もしくはPhase 1aをrevert。

---

## 配布戦略

### 配布方法

| 形態 | Phase | 手順 |
|------|-------|------|
| 単一HTMLをダブルクリック | 現状 / Phase 2以降 | `タスク管理.html` or `dist/index.html` をダブルクリック |
| フォルダ一式をzip | Phase 1 | フォルダをzip → 解凍 → ローカルサーバー起動 → ブックマーク |
| GitHub Pages | 任意 | Phase 1/2どちらでも可。プライベート運用ならリポジトリをprivate |

**推奨**: 個人1名利用なので配布自体はほぼ不要。**Phase 1の間は自PCにフォルダを置いてlocalhostで使う**。Phase 2に上がったら `dist/index.html` をクラウドドライブ（個人用）に置いてどのPCからでも開ける形に。

### バージョン管理戦略

- **セマンティックバージョニング**: `MAJOR.MINOR.PATCH`
  - MAJOR: スキーマ破壊的変更（v6→v7のマイグレーション要）
  - MINOR: 機能追加（後方互換）
  - PATCH: バグ修正のみ
- 現状は `v6.0.0` 相当。Phase 0適用で `v6.1.0`、Phase 1完了で `v6.2.0`。
- **`index.html` の `<title>` と `constants.js` の `APP_VERSION` を同期**させ、ヘッダのsubtitleに表示。
- gitタグ `v6.2.0` をPhase完了時に打つ。`CHANGELOG.md` をdocs/に置く（**今は作らない**、3版目以降で検討）。
- スキーマバージョン（`SCHEMA_VERSION`）はアプリバージョンと**独立**。v7に上げる時はマイグレーション関数 `migrateV6ToV7()` を追加。

### 公務員PC運用メモ

- npm不要の Phase 1 で止めることを推奨（制約回避）。
- ローカルサーバーは以下のどれかで起動:
  - Python標準: `python -m http.server 8000`
  - VS Code + Live Server拡張（オフラインインストール可）
  - Node: `npx serve`（プロキシ要、Phase 2に進んだ場合のみ）
- 個人PCで開発→USB/クラウド経由で業務PCへ → 業務PC側ではダブルクリックで `index.html`（Phase 2後）のみ使用、という運用がPhase 2到達後は可能。

---

## 補足: 各Phaseの時間見積もり

| Phase | 見積もり | 前提 |
|-------|---------|------|
| Phase 0（クイックウィン P0） | 2〜3時間 | 現HTMLに追記のみ |
| Phase 0（P1/P2も含む） | 半日〜1日 | debounce・部分再描画・IDBミラー追加 |
| Phase 1a（2ファイル化） | 1〜2時間 | CSS切り出しと `type="module"` 化 |
| Phase 1b（モジュール抽出） | 1〜2日 | 1モジュールあたり30分〜2時間 |
| Phase 1c（追加安定化） | 半日 | JSON export/import等 |
| Phase 1d（旧HTMLリタイア） | 30分 | |
| Phase 2（Vite導入） | 半日 | `npm install` が通る前提で |

**最短ルート**: Phase 0だけで止める → 2〜3時間で劇的に安定化。案Aへの進行は「編集が辛くなってから」で十分。
