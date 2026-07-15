# UI 要件書 — Neuro Matrix Task OS（Google Stitch 投入用）

**目的**: 機能仕様は確定済み・Phase 0 の応急処置も完了。ここから UI の見た目を一段上げるため Google Stitch にデザイン生成を依頼する。本書はその投入プロンプトと画面仕様をまとめたもの。

**対象ファイル**: `タスク管理.html`（単一 HTML / vanilla JS / LocalStorage）
**現行参照**: [review_uiux.md](review_uiux.md)（UIUX課題）/ [PLAN.md](PLAN.md)（改善ロードマップ）
**書き直しの範囲**: 見た目のみ（HTML 構造と CSS）。機能ロジック（JS）は触らない前提で要件を書く。

---

## 1. プロダクトの背景と世界観

### 1-1. 一行で
「アイゼンハワーマトリクス（4象限）を、**ADHD気質の個人1人**が**オフライン・単一HTML**で回し続けられる、タスクOS。」

### 1-2. 差別化の核
- **4象限を一等地に据える**数少ないプロダクト（TickTick 以外にほぼない）
- **Survivalモード**: 締切プレッシャーに耐える「追い込み演出」。カウントダウン・ネオン・スロット分類（MUST / SHOULD）で緊急時の意思決定を強制する
- **「削除」と「完了」を分離**: 完了は履歴として残り、削除は Undo 付き。混同しがちな操作を明示的に分ける

### 1-3. ユーザー像
- 1人（共有なし、チームなし）
- 日中は公務員業務、夜〜休日は個人プロジェクト複数
- 散らばったタスクを頭から追い出すために使う
- 凝ったUIを自宅の楽しみとして歓迎する（オフィス PC 制約を回避する意味でも）

### 1-4. 絶対に壊したくない設計思想
- オフライン完結（サーバー不要、ネット不要）
- `file://` でも動く単一 HTML
- LocalStorage 1層、階層タスク・プロジェクト・チーム機能は**入れない**
- ゲーミフィケーション（Streak / Badge）は**入れない**（ADHD は1日抜けると全投げする反転リスク）

---

## 2. デザイン方針（Stitch に渡す前提）

### 2-1. トーン候補（選択肢を Stitch に提示する）

| 案 | トーン | 通常モード | Survivalモード | 推奨度 |
|----|--------|------------|----------------|--------|
| **A. Dual-Persona（推奨）** | 二面性 | 洗練されたモダンミニマル（Linear/Notion 系、落ち着いた無彩色+アクセント1色） | サイバーパンク（ネオン、グリッチ、モノスペース、scan line） | ★★★ |
| B. Neo-Brutalism | 紙と墨 | 太い黒ボーダー、手書き的フォント、マスキングテープ風の色パッチ | 同系で赤と黒のコントラスト強化 | ★★ |
| C. Cyberpunk 統一 | 世界観ガチ | 通常モードもスキャンライン + ネオン | 現行そのまま | ★ |

**デフォルトは A**。通常モードは長時間使うので目に優しく、Survivalモードで世界を切り替える演出にする。

### 2-2. 共通原則
- **情報密度を落とさない**: タスクを一覧できることが最優先。装飾で件数が見えなくなるのは NG
- **アニメーションは機能的理由のあるものだけ**: ドラッグ中、モード切替、完了時の触覚視覚フィードバック。装飾アニメはカット
- **色覚多様性対応**: Q1/Q3（赤/黄）を色だけで区別せず、左ボーダーの太さ・パターンでも冗長化
- **ダークモード対応**: A案の通常モードはライト/ダーク切替可能にする。Survivalは常にダーク

---

## 3. 画面インベントリ（Stitch で生成する画面一覧）

| # | 画面 | 状態 | 必須要素 |
|---|------|------|---------|
| S1 | **メイン（4象限グリッド）** | ライト / ダーク | 4象限タイル、ヘッダ、カード複数、カウントバッジ |
| S2 | **メイン + 完了パネル展開** | ライト / ダーク | S1 + 右スライドインパネル（完了タスク履歴） |
| S3 | **カード展開詳細** | ライト / ダーク | 1カードが展開され、締切/メモ/履歴を編集中の状態 |
| S4 | **Survivalモード** | ダーク固定 | カウントダウン、MUST/SHOULD スロット、未割り当てピッカー |
| S5 | **Survival中のスロット割当後** | ダーク固定 | MUSTに2件、SHOULDに3件、未割り当てに残り |
| S6 | **Undo トースト表示** | ライト | 削除直後のトースト（「タスクを削除しました (残り 2件戻せる)」） |
| S7 | **空状態**（新規ユーザー初回） | ライト | 全象限が空、オンボーディング的ヒント |
| S8 | **モバイル（象限縦積み）** | ライト | <=880px のレスポンシブ、スワイプ切替タブ or 縦スクロール |

---

## 4. グローバルスタイル仕様

### 4-1. カラートークン（A案 前提）

```
/* ライトモード */
--surface-0: #fafaf7    /* アプリ背景 */
--surface-1: #ffffff    /* カード / パネル */
--surface-2: #f2f2ed    /* 非アクティブ領域 */
--ink-0:     #0a0a0a    /* 本文 */
--ink-1:     #3f3f3f
--ink-2:     #737373    /* サブ */
--ink-3:     #a3a3a3    /* プレースホルダ */
--line:      #e5e5e0

/* 象限アクセント（ライト） */
--q1: #d13c3c   /* 重要・緊急 赤 */
--q2: #2b7a4b   /* 重要・非緊急 緑 */
--q3: #c08a1e   /* 非重要・緊急 黄土色 */
--q4: #6b7280   /* UNSORTED グレー */

/* Survivalモード */
--panic-bg:    #050505
--panic-ink:   #e8e8e8
--neon-red:    #ff2d4a
--neon-yellow: #ffe347
--neon-cyan:   #3df0ff    /* アクセント追加 */
```

### 4-2. タイポグラフィ
- 本文: Inter / Noto Sans JP 400–600（和文混在を考慮）
- 数字・タイマー: JetBrains Mono または IBM Plex Mono（等幅で桁揺れなし）
- Survivalタイマー: さらに太く、Orbitron もしくは Mono の Black
- 見出し階層: h1 / h2 / h3 を CSS で明示（現状 div で済ませている箇所を要修正）

### 4-3. スペーシング
- 4 / 8 / 12 / 16 / 24 / 32 / 48 の8px グリッド
- カード間ギャップ: 12px、象限内パディング: 16px
- タッチターゲット最小: **44×44px**（モバイル）

### 4-4. 角丸・影
- カード: `border-radius: 14px` / `box-shadow: 0 2px 8px rgba(0,0,0,.06)`（ライト）
- ダーク: 影の代わりに `border: 1px solid rgba(255,255,255,.08)`
- Survival: 角は `4px` まで鋭くする（緊張感）

### 4-5. モーション
- ドラッグ中: 4° tilt + scale 1.03 + drop shadow 強化（現行踏襲）
- モード切替: 200ms ease で fade
- Undo トースト: 下から 28px スライドイン、250ms
- Survival 起動: 800ms で scan line が上から降りてくる演出（1回のみ）

---

## 5. 画面別 詳細要件

### S1: メイン（4象限グリッド）

**レイアウト**:
- ヘッダ（高さ 64px、sticky）
  - 左: ロゴ `Neuro Matrix` + サブコピー「完了履歴・メモ・締切を記録」
  - 右: `＋ 新規タスク` / `完了一覧` / `⚠️ サバイバル` の3ボタン（アイコン+短テキスト）
- **軸ラベル**（新規追加要件）
  - 左端縦書き: `← 重要度 →`（上下）
  - 上端横書き: `← 緊急度 →`（左右）
  - これで4象限が「重要度×緊急度」の2軸であることを常時示す
- 4象限グリッド（2×2、gap 4px）
  - 各象限に: `象限タイトル`（h2）+ `件数バッジ`（右寄せ、角丸ピル）
  - 象限背景色 + 上辺 6px の象限色ボーダー
  - 内部はカードの縦リスト、空ならヒント文（空状態テキスト: 「カードをドラッグして移動できます」）

**カード**:
- タイトル（textarea、1〜N行、自動伸長）
- 右上: ドラッグハンドル（`⋮⋮` アイコン、カード全体がドラッグ可能だがハンドルで意図を明示）
- 左端 5px の象限色ボーダー
- 下段メタ行: 締切バッジ（`今日` / `期限超過` / `締切 04/20` / `締切なし`）+ メモありバッジ
- 下段右: 更新時刻（小、グレー）
- アクション3ボタン（ホバー時に表示、モバイルは常時表示）
  - `✓ 完了` / `📝 詳細` / `🗑 削除`

**マイクロコピー（適用）**:
- サブコピー: 「完了履歴・メモ・締切を記録。削除と完了を別扱いにしています」
- 新規タスクボタン: `＋ 新規タスク`
- 象限タイトル: `🔥 重要・緊急` / `✨ 重要・非緊急` / `💨 非重要・緊急` / `📥 UNSORTED（未仕分け）`
- 空状態: `まだタスクはありません。＋ボタンか、他象限からドラッグで追加`

---

### S2: 完了パネル展開

- 画面右からスライドイン、幅 `min(440px, 100vw)`
- モバイル（<=640px）は全画面 + 上部に「← 戻る」バー
- パネル内カードは左ボーダーを成功色（緑）で統一、元の象限は小さく `元: Q1` のピル表示
- 完了日時を大きく表示、作成日時は小さく
- アクション: `↩ 未完了に戻す` / `🗑 削除`
- 空状態: 「まだ完了タスクはありません。タスクを完了すると、ここに履歴が残ります。」

---

### S3: カード展開詳細

- カードをタップ/クリックで展開（現行踏襲）
- 展開時に表示:
  - 締切入力（日付ピッカー）
  - メモ入力（textarea、高さ 76px〜可変）
  - タイムスタンプ3行（作成・更新・完了）
  - 履歴リスト（最新30件、スクロール可能）
- **展開状態は再描画後も保持**（現行バグ: renderAll で畳まれる — 要修正要件）

---

### S4: Survivalモード

**トーン**: 完全ダーク、ネオン、scan line
- 背景: `--panic-bg: #050505` + `linear-gradient(var(--scan-line) 1px, transparent 1px)` size 4px
- カウントダウン: 画面上部中央、Mono Black、`18vw` 可変 / max 140px
  - 残 30分超: 白 / 残 15〜30分: ネオンイエロー / 残 15分以下: ネオンレッド + パルス
- 上部ヘッダ: `斜線パターン (45°)` の黒赤で「緊急モード起動中」
- スロット2段:
  - `MUST (絶対やる)` — 上部赤バッジ、枠ネオンレッド、カード背景 `#300`
  - `SHOULD (できれば)` — 同黄、枠ネオンイエロー、カード背景 `#332b00`
- 下部「未割り当てタスク」ピッカー（横スクロール可能なカードストリップ）
- 最下部: 目標時刻入力 + `通常モードに戻す` ボタン（「ABORT」は使わない）

**コピー修正**:
- `EMERGENCY PROTOCOL ACTIVE` → `緊急モード起動中`
- `DEADLINE ENFORCEMENT SYSTEM` → `締切までの残り時間`
- `UNASSIGNED TASKS // ドラッグして割り振れ` → `未割り当て — ドラッグしてスロットへ`
- `ABORT MODE` → `通常モードに戻す`

---

### S5: Survival スロット割当後

- MUST に 2件、SHOULD に 3件、ピッカーに残り
- **新要件**: MUST に 3件目を置こうとすると警告（「MUSTは1〜2件に絞りましょう」）、または自動で SHOULD に押し戻す
- MUST カードは赤背景・白文字、SHOULD カードは黄背景・白文字で差別化（既存踏襲）

---

### S6: Undoトースト

- 画面下部中央、角丸ピル、ダーク背景
- `タスクを削除しました (5秒以内なら取り消せます)` + `元に戻す` ボタン
- 連続削除時: `タスクを削除しました (残り 3件戻せる)` と残数表示
- 5秒自動退場、アニメーションは下から 28px スライド

---

### S7: 空状態（新規ユーザー）

- 全象限が空
- ヘッダ直下に軽いオンボーディングカード1枚（閉じれる）
  - 「＋ボタンでタスク追加。ドラッグで象限を変えられます。SURVIVAL は締切が迫った時に使います」
- 象限内は空ヒント文のみ

---

### S8: モバイル（<=880px）

- 現行: 象限を縦積み（4行均等分割）→ 各象限が小窓になり内部スクロール
- **変更要件**: 以下2案のどちらかを Stitch に選んでもらう
  - 案a: 象限を**スワイプ切替タブ**に変更。上部にタブバー `Q1 / Q2 / Q3 / Q4`、横スワイプで遷移
  - 案b: 象限を**縦スクロール**に変更。`minmax(200px, auto)` で各象限の高さが内容に応じて伸び、ページ全体を縦スクロール
- ヘッダのボタン3個: <=640px で縦積みではなく、`＋` ボタンを FAB 化（右下固定）して `完了一覧` と `サバイバル` はハンバーガー内に収める
- タッチターゲット: すべて 44px 以上

---

## 6. アクセシビリティ要件（必須）

- すべてのインタラクティブ要素に `aria-label`
- `survival-overlay` に `role="dialog" aria-modal="true" aria-labelledby`
- `undo-toast` に `role="status" aria-live="polite"`
- 各象限に `aria-label="重要・緊急"` 等（絵文字を読み上げさせない）
- キーボードのみでカード移動可能: カードに `tabindex="0"`、フォーカス時に矢印キー + `M` で「移動先を選択」ダイアログ
- フォーカスリング: ブラウザデフォルトに頼らず、`focus-visible` で 2px のアクセント色アウトライン
- `user-scalable=no` を外す（拡大を許可）
- 色覚: 象限判別に左ボーダーの**太さ**か**パターン**を併用

---

## 7. レスポンシブ

- ブレークポイント: 1200 / 880 / 640 / 420
- `>=1200px`: 2×2 グリッド、カード幅 380px 上限
- `880〜1200px`: 2×2 維持、カード幅縮小
- `640〜880px`: モバイル案a or b（上記 S8 参照）
- `<=640px`: 案a/b + FAB 化

---

## 8. 触らない領域（明示）

- LocalStorage スキーマ（`neuro_matrix_v6_data` / `_state`）
- イベントモデル（pointerdown / pointermove / pointerup の D&D）
- JS の関数インターフェース
- Undo の挙動（5件スタック）
- Survival のスロットロジック

デザインで変えるのは **HTML マークアップ + CSS + 最低限のクラス名** のみ。JS から参照されている id（`q1`〜`q4`, `survival-overlay`, `undo-toast`, `completed-panel`, `countdown`, `target-time` 等）は**そのまま残す**。

---

## 9. Stitch 投入プロンプト v2（Normal モード S1 特化・コピペ用）

**v1 からの改訂理由**: v1 で全 8 画面を一括依頼したところ、Survival Mode 1 画面のみ納品（12.5% カバレッジ）、CDN 依存、DOM id 欠落、日本語コピー未適用など重大な不一致が発生（詳細は [review_stitch_output.md](review_stitch_output.md)）。v2 では **S1（メイン4象限グリッド）1 画面に絞り**、失敗した項目をすべて命令形で再明記する。

> ---
>
> # STRICT REQUIREMENTS — read all before generating
>
> This is a design request for an **offline, single-HTML-file** Japanese personal task manager. Prior Stitch output violated core constraints. Do **not** repeat those mistakes.
>
> ## Hard constraints (any violation = reject)
>
> 1. **No external CDN**. Do not use `<script src="https://cdn.tailwindcss.com...">`, do not use `<link href="https://fonts.googleapis.com...">`, do not use `<link href="https://fonts.gstatic.com...">`, do not use Material Symbols CDN, do not use any `https://` URL in `src` or `href`. The file must render identically when opened by `file:///path/to/file.html` with the network disconnected.
> 2. **No Tailwind**, no utility-class framework. Write plain CSS inside a single `<style>` block. Use CSS custom properties (`--var`) for tokens.
> 3. **`<html lang="ja">`**. Title: `<title>Neuro Matrix Task OS</title>`.
> 4. **Preserve exact DOM IDs** for JS compatibility. The following IDs MUST appear on the exact element type listed:
>    - `id="matrix"` — root container of the 4 quadrants
>    - `id="q1"`, `id="q2"`, `id="q3"`, `id="q4"` — four `<section>` elements, one per quadrant
>    - `id="add-btn"`, `id="completed-toggle"`, `id="survival-btn"` — three `<button>` elements in the header
>    - `id="completed-panel"` — `<aside>` for the right slide-in (can start closed, i.e., `aria-hidden="true"`)
>    - `id="undo-toast"` — `<div role="status" aria-live="polite">` near the bottom (can start hidden)
>    - Each quadrant section must have `aria-label="重要・緊急"` / `aria-label="重要・非緊急"` / `aria-label="非重要・緊急"` / `aria-label="UNSORTED（未仕分け）"`
>    - Each quadrant's count badge must have `data-count-for="q1"` (or q2/q3/q4)
> 5. **Fonts**: use `font-family: 'Inter', 'Noto Sans JP', system-ui, -apple-system, 'Hiragino Sans', 'Yu Gothic', sans-serif;` for body. For numbers/monospace use `'JetBrains Mono', ui-monospace, 'Courier New', monospace;`. Do **not** reference Manrope or Space Grotesk.
> 6. **Japanese microcopy — use these strings verbatim**:
>    - Header title: `NEURO.MATRIX TASK OS`
>    - Header subtitle: `完了履歴・メモ・締切を記録。削除と完了を別扱いにしています`
>    - Add button: `＋ 新規タスク`
>    - Completed toggle: `完了一覧`
>    - Survival button: `⚠️ サバイバル`
>    - Q1 title: `🔥 重要・緊急`（絵文字には `aria-hidden="true"`）
>    - Q2 title: `✨ 重要・非緊急`
>    - Q3 title: `💨 非重要・緊急`
>    - Q4 title: `📥 UNSORTED（未仕分け）`
>    - Empty state per quadrant: `まだタスクはありません。＋ボタンか他象限からドラッグで追加`
>    - Count badge format: `3件` / `12件`
>    - Due badges (sample text): `今日 04/17（水）` / `期限超過 04/15（月）` / `締切 04/20（土）` / `締切なし`
>    - Card action buttons: `✓ 完了` / `📝 詳細` / `🗑 削除`
>
> ## Design direction — Normal Mode ONLY (the Curator persona)
>
> Build S1: the main 4-quadrant grid screen in **light mode only** (no dark mode on this request). Tone reference: Linear / Notion / Things 3. Atmospheric Precision — tonal hierarchy instead of borders where possible.
>
> ### Color tokens (use these exact hex values as CSS custom properties)
>
> ```css
> :root {
>   --surface-0: #fafaf7;          /* app background */
>   --surface-1: #ffffff;          /* cards */
>   --surface-2: #f3f4f0;          /* secondary panels */
>   --ink-0: #2e3430;              /* primary text (not pure black) */
>   --ink-1: #5a615c;              /* secondary text */
>   --ink-2: #767c77;              /* tertiary / placeholder */
>   --line: #e5e5e0;               /* use sparingly */
>   --q1: #d13c3c;                 /* 重要・緊急 red */
>   --q2: #2b7a4b;                 /* 重要・非緊急 green */
>   --q3: #c08a1e;                 /* 非重要・緊急 ochre */
>   --q4: #6b7280;                 /* UNSORTED gray */
>   --accent: #2b7a4b;             /* primary CTA */
> }
> ```
>
> ### Layout — the exact structure to render
>
> 1. **Header** (sticky, height ~72px): logo left (`NEURO.MATRIX TASK OS` + subtitle), 3 buttons right (`＋ 新規タスク` / `完了一覧` / `⚠️ サバイバル`). The `⚠️ サバイバル` button has a subtle red outline to hint at its intensity, but does NOT neon-glow in normal mode.
> 2. **Axis labels** (NEW, critical):
>    - Left edge: vertical-writing label `← 重要度 →` running top-to-bottom
>    - Above the matrix: horizontal label `← 緊急度 →` running left-to-right
>    - These make the 2-axis structure explicit at all times.
> 3. **4-quadrant grid** (2×2, gap 4px):
>    - Each quadrant is a `<section>` with: quadrant accent color as a 6px top bar + very subtle background tint (5% of accent) + quadrant title + count pill + card list
>    - Color-blind redundancy: use a distinct left-border **pattern** per quadrant on cards — Q1 solid 5px, Q2 double border, Q3 dashed, Q4 dotted
>    - Empty state: the text from constraint #6, centered, dashed ghost border
> 4. **Task cards** (show 3〜5 sample cards spread across quadrants):
>    - Left border: 5px of the quadrant's accent color (with the pattern from #3)
>    - Title: bold, multi-line capable (`<textarea>` semantics but visually static)
>    - Due badge pill: one of 4 states with color (red/orange/indigo/gray) AND text
>    - Meta row: `更新 2026/04/17 09:41` small, `--ink-2`
>    - Action row: 3 icon buttons with labels (`✓ 完了` / `📝 詳細` / `🗑 削除`). On desktop these are subtle; they become prominent on card hover. On mobile, always visible.
>    - One card in Q2 should be in the **expanded state** to show the detail view: date input, textarea for note, timestamps block, history list
> 5. **Responsive**:
>    - ≥1200px: full 2×2 matrix
>    - 880–1200px: 2×2 maintained, cards get narrower
>    - ≤880px: quadrants become **horizontal swipe tabs** with a tab bar `Q1 / Q2 / Q3 / Q4` above
>    - ≤640px: add button becomes a bottom-right FAB, other header buttons move into a hamburger
>
> ### Accessibility (MUST implement, not just mention)
>
> - Every interactive element has either meaningful text content or `aria-label`
> - Emojis in quadrant titles have `aria-hidden="true"` on a wrapper `<span>`
> - Focus ring: `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }`
> - Tap targets: minimum `44px × 44px` on touch (use `min-height` and padding, not just font-size)
> - Viewport meta: `<meta name="viewport" content="width=device-width, initial-scale=1.0">` (do NOT add `user-scalable=no` or `maximum-scale=1`)
> - Do not rely on color alone — always pair color with text, icon, or border pattern
>
> ### What NOT to include (hard exclusions)
>
> - No AI suggestions, streaks, badges, gamification
> - No sub-tasks, projects, folders, team features
> - No online sync UI, no login, no cloud indicators
> - No decorative stub text like `SYS.REQ // OVERRIDE` or fake task IDs (`T-992`). Use realistic Japanese task titles instead (e.g., `資料レビュー対応`, `買い出し（週末）`, `提案書レビュー`).
>
> ### Output format
>
> Return a **single standalone HTML file** (`index.html` or similar). Include all CSS in one `<style>` block. No external `<link>` or `<script src="https://...">`. No build step required. Opening the file with `file://` in a modern browser must produce the intended design pixel-for-pixel.
>
> ---
>
> ## Acceptance criteria (I will reject if any fail)
>
> 1. File contains zero `https://` URLs in `src` or `href` attributes
> 2. File contains all 12 required DOM IDs from constraint #4
> 3. All Japanese strings from constraint #6 appear verbatim
> 4. `lang="ja"` on `<html>`
> 5. `.quadrant` elements have `aria-label` per constraint #4
> 6. Axis labels `重要度` and `緊急度` are visible in the rendered output
> 7. 4 quadrants differentiable by border pattern (not color alone)
> 8. Opens correctly with network disabled
>
> ---

After Normal mode S1 is accepted, we will separately request S2 (Completed panel), S3 (Card expanded), S6 (Undo toast), S7 (Empty state), S8 (Mobile). Survival mode (S4/S5) will be hand-built from the prior Stitch delivery's CSS fragments, not re-requested.

---

## 10. 受領物チェックリスト

Stitch から戻ってきたデザインを評価する観点:

- [ ] 4象限の視覚的優位性が保たれているか（軸ラベル含む）
- [ ] 通常モードとSurvivalモードの世界観が**明確に違う**が、同一プロダクトとわかる
- [ ] カード情報密度が保たれ（タイトル/締切/メモ/更新時刻/3アクション）、1画面で最低 20 件見える
- [ ] ダークモードで目が疲れないコントラスト（AA 以上）
- [ ] 既存 DOM id が保たれている（JS を書き換えずに差し替え可能）
- [ ] モバイルで 44×44 タッチターゲット
- [ ] 色覚対応の冗長化（色 + ボーダーパターン）
