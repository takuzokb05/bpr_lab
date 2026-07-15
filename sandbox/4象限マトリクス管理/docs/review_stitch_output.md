# Stitch 納品物レビュー結果 — 2026-04-17

2 エージェント並列レビュー（Jenny = 仕様準拠 / code-quality-pragmatist = 実装現実性）の合体所見と意思決定記録。

## 納品物

- `stitch_output/code.html`（Survival Mode 1画面、約200行）
- `stitch_output/screen.png`（レンダリング画像）
- `DESIGN.md`（Dual-Persona Architecture 宣言 + カラートークン + タイポ指針）

## 合体判定: 再発注（ただし Survival の CSS 片と DESIGN.md は流用）

### 致命的な不一致（両エージェント一致）

| # | 項目 | 状態 |
|---|------|------|
| 1 | 画面カバレッジ | 8画面中 **S4 のみ（12.5%）**。Normal モード不在で Dual-Persona 未成立 |
| 2 | オフライン原則 | Tailwind CDN / Google Fonts×2 / Material Symbols の **4 CDN 依存**。`file://` で崩壊 |
| 3 | DOM id 契約 | `q1`〜`q4`, `undo-toast`, `completed-panel`, `exit-survival`, `undo-btn` など **欠落**。`target-time` は input のはずが div 化で既存 JS 即死 |
| 4 | 日本語コピー | 要件指定 4点中 1点のみ適用（「通常モードに戻す」だけ） |
| 5 | アクセシビリティ | `role="dialog"` / `aria-modal` / `aria-live` 全滅、`lang="en"` のまま、フォーカスリング指定なし |

### 中程度の不一致

- カラートークン: DESIGN.md 定義（Q1=#b5272b / Q2=#1a6d3f）が要件（Q1=#d13c3c / Q2=#2b7a4b）と不一致。**Q3/Q4 は定義すら無い**
- フォント: 要件「Inter / Noto Sans JP / JetBrains Mono / Orbitron」に対し **Noto Sans JP 欠落**、要件外の Manrope / Space Grotesk 混入
- Tailwind config に 60 トークン定義、実使用 1 トークンのみ（残り 59 デッドコード）
- 要件外の装飾テキスト `SYS.REQ // OVERRIDE` が追加

### 活用できる資産

- `.scanlines` / `.text-glow-red` / `.text-glow-cyan` / `.border-glow-red` / `.border-glow-yellow` / `.slash-pattern` の CSS 片（Survival 世界観、品質良好）
- `DESIGN.md` の「Kinetic Archive」「Dual-Persona」コンセプトと Normal パレット（surface / surface-container-* 階層）

## 意思決定

### 戦略

1. **再発注は Normal モード S1 のみに絞る**（全8画面を再依頼すると Stitch の癖で同じ失敗を繰り返すリスク）
2. Normal トーンが確定したら、残り画面（S2/S3/S6/S7/S8）は**こちらで手動量産**
3. Survival 側（S4/S5）は既納品を **CDN 外し + DOM id 注入 + a11y 補修**で採用

### 想定作業時間

| アプローチ | 時間 |
|-----------|------|
| Normal S1 再発注（プロンプト改善込み） | 15分 + 待ち + 評価 30分 |
| Survival 既納品の手直し（CDN外し・id注入・a11y） | 2〜3時間 |
| Normal 残り画面の手動量産（トーン確定後） | 4〜6時間 |

### 再発注時の必須追加指示

前回納品で欠けた項目を Stitch プロンプトに命令形で明記（次節参照）:

1. 「出力は HTML 1 ファイル。`<script src="cdn...">` / `<link href="fonts.googleapis...">` **禁止**。Tailwind 不使用、`<style>` にプレーンCSSで書け」
2. DOM id 契約を `ui_requirements.md §8` から抜粋して命令形で再掲。`target-time` は **input 要素必須**と明記
3. 日本語コピーは「完全一致必須」と明示。`lang="ja"` 必須
4. Noto Sans JP の `@font-face` 同梱または `system-ui, -apple-system, "Hiragino Sans"` フォールバック指定
5. **S1 のみ**依頼する（一度に多画面を出させると品質が落ちる）

## 次のアクション

- [x] レビュー所見の合体（本ファイル）
- [ ] `docs/ui_requirements.md §9` を v2 に改訂（次のステップ）
- [ ] Stitch に Normal モード S1 のみ再発注（ユーザー実施）
- [ ] Normal 受領後、Dual-Persona トーン確定の意思決定
- [ ] Survival 既納品の CDN 外し + DOM id 注入（こちら実施可）
