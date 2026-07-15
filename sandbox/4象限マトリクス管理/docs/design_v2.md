# Design v2 — Neuro Matrix Task OS

**スコープ**: UI を 0 から再設計する。既存 `タスク管理.html` は保存用に残し、新実装は `app/` 配下に構築する。

## 1. デザイン哲学

### 1-1. プロダクトの立ち位置
**個人 1 人の「脳外ストレージ兼意思決定補助」**。タスクを頭から追い出し、4象限で重要度×緊急度を即判断し、必要なら Survival モードで締切プレッシャーに耐える。表計算やToDoリストではなく、「意思決定ツール」として振る舞う。

### 1-2. "ツール vs 表" — 分岐点
ユーザーが叱ったとおり、これまでは「カラフルな表」に寄り過ぎていた。ツールに見せる要件:

| 次元 | 表（ダメ） | ツール（正解） |
|------|-----------|---------------|
| 情報階層 | 全セル同じ重み | タイトル > メタ > アクション の強弱 |
| 色味 | カードと背景が同色相 | 背景（彩度あり） × カード（無彩度 or 対比色）で色相差 |
| 陰影 | フラット・枠線主体 | 強い box-shadow でカードが物理的に浮く |
| インタラクション | hover しても変わらない | hover / active / drag で明確な状態変化 |
| 密度 | 余白なし詰め込み | 意図的な余白（16-24px） |
| ブランド | 量産感 | 独自配色・独自アイコン・独自タイポで立ち位置を主張 |

### 1-3. 参照プロダクト（インスピレーション）
- **Linear**: ダーク基調、キーボード駆動、Cmd+K、サイドバーナビ、微細なトランジション
- **Height**: カラフルなステータスピル、カード型タスク、豊かなメタ表示
- **Superhuman**: 速さへの執着、ショートカット、ステータスバー
- **Things 3**: 余白の使い方、ユーモラスなアイコン、Areas/Today/Inbox の階層
- **TickTick**: 4象限ネイティブ（直接的競合）、カレンダー連動

## 2. 情報アーキテクチャ

### 2-1. 画面グリッド（デスクトップ、>=1024px）

```
┌─ TopBar (48px) ──────────────────────────────────────────┐
│ [logo] [quick-add] [search]               [theme] [user] │
├──────┬──────────────────────────────────────┬────────────┤
│      │  ← 緊急度 →                          │            │
│  Nav │ ┌──────────┬──────────┐              │  Drawer    │
│ 240  │ │    Q1    │    Q2    │              │ (完了/履歴/│
│  px  │ ├──────────┼──────────┤  ← 重要度 →  │  設定)     │
│      │ │    Q3    │    Q4    │              │  320px     │
│      │ └──────────┴──────────┘              │ (toggable) │
│      │                                      │            │
├──────┴──────────────────────────────────────┴────────────┤
│ StatusBar: [件数] [未保存] [next:Pomodoro] [shortcuts]   │
└──────────────────────────────────────────────────────────┘
```

### 2-2. モバイル（<768px）
- Nav → 下部タブバー（Dashboard / Survival / Completed / Settings）
- Drawer → フルスクリーンモーダル
- Matrix → 4タブ切替 (Q1/Q2/Q3/Q4) + カード縦リスト

### 2-3. ナビゲーション（左サイド）
```
NEURO.MATRIX (logo)
━━━━━━━━━━━━
[⌂] ダッシュボード        ← default
[⚡] サバイバル            ← 赤アクセント、ホバーで pulse
[✓] 完了一覧
━━━━━━━━━━━━
VIEWS
[📅] 今日                 (フィルター: today)
[🗂] 全件
━━━━━━━━━━━━
[⚙] 設定                 ← 下部固定
[💾] JSON書出/取込
```

## 3. カラーシステム

### 3-1. 基調: ダーク（デフォルト）
プロツールらしさと目の疲労軽減を優先。GitHub Dark と Linear の中間。

```css
/* Dark theme */
--bg:            #0e1116;   /* app canvas */
--surface:       #161b22;   /* sidebar / topbar / card */
--surface-hover: #1c2229;   /* hover state */
--surface-2:     #21262d;   /* nested / elevated */
--border:        #30363d;
--border-muted:  #21262d;
--text-0:        #f0f6fc;   /* primary */
--text-1:        #c9d1d9;
--text-2:        #8b949e;   /* secondary */
--text-3:        #6e7681;   /* tertiary */
```

### 3-2. 象限アクセント（彩度中、ダーク背景で映える）

```css
--q1: #f85149;   --q1-bg: rgba(248, 81, 73, 0.08);   --q1-ring: rgba(248, 81, 73, 0.35);
--q2: #3fb950;   --q2-bg: rgba(63, 185, 80, 0.08);   --q2-ring: rgba(63, 185, 80, 0.35);
--q3: #d29922;   --q3-bg: rgba(210, 153, 34, 0.08);  --q3-ring: rgba(210, 153, 34, 0.35);
--q4: #8b949e;   --q4-bg: rgba(139, 148, 158, 0.08); --q4-ring: rgba(139, 148, 158, 0.3);
```

**象限コンテナ**: 濃ダーク `#161b22` ベース + 象限色 8% の薄いバックドロップで識別
**カード**: `#1c2229` (surface-hover) + 左 3px 象限色ボーダー
→ カード（濃グレー）と象限（超濃グレー + 色かかり）で **明度差 + 色相差**で自律

### 3-3. ライトテーマ（optional）
デフォルトはダーク。トグルで切替。

### 3-4. Survival モード
既存 Cyberpunk 路線を維持（`#050505` + `#ff2d4a` + `#ffe347` + `#3df0ff`）。ダークテーマから切り替わると世界が変わる演出。

### 3-5. Status colors
```
success: #3fb950  danger: #f85149  warn: #d29922  info: #58a6ff
```

## 4. タイポグラフィ

- **UI / Body**: Inter 400/500/600/700（英数）+ Noto Sans JP 400/500/700（和文）
- **数値・モノスペース**: JetBrains Mono 500/700（タイマー・カウント・タイムスタンプ）
- **Survival タイマー**: Orbitron 900（CRT グロー）

スケール:
```
text-xs:   11px / 1.4
text-sm:   13px / 1.5
text-base: 14px / 1.55
text-md:   15px / 1.5
text-lg:   17px / 1.4  (card title)
text-xl:   20px / 1.3  (quadrant title)
text-2xl:  24px / 1.25 (page heading)
```

## 5. コンポーネント

### 5-1. TopBar (h=48)
- 左: ブランド `◈ NEURO.MATRIX`（ロゴマーク + wordmark）
- 中央: クイック追加ボタン `＋ タスク` (Cmd+N ヒント表示) / 検索フィールド (optional、Phase 2)
- 右: テーマトグル / サバイバル緊急ボタン（赤） / ユーザーアバター（プレースホルダー）

### 5-2. Sidebar (w=240)
- ロゴセクション 上部 64px
- 縦並びメニュー、各項目に `Material Symbols` アイコン + テキスト + hover で `surface-hover`
- アクティブ項目は左 3px の accent ボーダー + `surface-hover` 背景
- カウントバッジ右寄せ（件数をモノスペースで表示）
- 折りたたみ ≤1200px

### 5-3. Matrix grid
- 2×2 grid、各 quadrant は rounded 12px、border-muted 1px
- 上端に 4px の象限色の発光バー
- 内側 padding 16px
- 象限タイトル行: `[アイコン] [ラベル] [件数ピル]`、下に 1px 区切り

### 5-4. Task Card
```
┌─────────────────────────────────────────────┐
│ ≡ [title text in Inter Semi]             ⋯ │ ← ハンドル・タイトル・メニュー
│                                             │
│ [due-pill] [note-dot]           2h ago      │ ← メタ行
│                                             │
│ ─────────────────────────────────────────── │ ← 区切り（hover時のみ表示）
│ [✓ 完了]  [📝 詳細]            [🗑 削除]   │ ← アクション（hover時表示）
└─────────────────────────────────────────────┘
```
- 背景: `surface-hover` `#1c2229`（象限背景よりワントーン明るい）
- 左 3px: 象限色 accent
- shadow: `0 1px 0 0 rgba(255,255,255,0.04)` + `0 4px 12px rgba(0,0,0,0.3)` + hover で強化
- hover: translateY(-2px) + shadow 増、左ボーダー 3→4px に太く
- タイトル: `text-lg semibold`、ink `text-0`
- メタ行: `text-xs`、ink `text-2`、mono
- アクション: hover時のみ表示、tap targetは 36px
- ドラッグハンドル: 左縁の `≡` アイコン（hover表示）

### 5-5. Due Badge
```
期限超過  → bg: rgba(248,81,73,.15)  color: #ff7b72  border: rgba(248,81,73,.4)
今日      → bg: rgba(210,153,34,.15) color: #e3b341  border: rgba(210,153,34,.4)
締切      → bg: rgba(88,166,255,.15) color: #79c0ff  border: rgba(88,166,255,.4)
締切なし  → bg: rgba(139,148,158,.1) color: #8b949e
```
モノスペースで日付、形状はピル `border-radius: 6px`。

### 5-6. Drawer（完了一覧・履歴）
- 右スライドイン（既存）、320px
- ヘッダ: タブ `完了 / 履歴`
- 本体: 完了カード縦リスト

### 5-7. StatusBar（底部、24px）
- 左: 総タスク数 / active/completed 内訳
- 中央: 次のマイルストーン（「次の Survival まで 2時間」等）
- 右: キーボードショートカットヒント

### 5-8. Survival Mode Overlay
既存路線踏襲（scan line / Orbitron / neon）だが、今回の新テーマとの橋渡しとして、Survival 開始時に 300ms のフェードイン + scan line が上から降りるアニメ。

### 5-9. Undo Toast
- 下中央固定、ダーク ink surface、角丸 pill
- スタック残数表示（`残り 2件戻せる`）
- 5秒自動退場

## 6. アニメーション言語

- **Hover**: 150ms ease-out、translateY(-1〜-2px) + shadow 増
- **Mode switch**: 400ms ease-in-out、fade
- **Drawer**: 280ms cubic-bezier(.4,.0,.2,1)、slide
- **Card drag**: 即時、tilt 2deg + scale 1.02
- **Toast**: 250ms ease-out、slide up + fade in

`prefers-reduced-motion: reduce` ではアニメ無効化。

## 7. アクセシビリティ

- 全インタラクティブ要素に `aria-label`
- フォーカスリング: `outline: 2px solid var(--accent); outline-offset: 2px;`
- キーボード操作: Tab / Shift+Tab / Enter / Space / Esc / 矢印
- Cmd+K でクイック追加（将来）
- コントラスト比: 最低 WCAG AA 4.5:1 を全テキストで満たす

## 8. ファイル構成

```
4象限マトリクス管理/
├── app/
│   ├── index.html         # エントリ
│   ├── styles.css         # カスタムCSS（Tailwind 補完）
│   └── app.js             # アプリロジック（既存JSから移植）
├── タスク管理.html        # 旧、保存用
├── docs/
│   ├── design_v2.md       # 本書
│   └── ...
└── stitch_output*/        # Stitch 納品物参考
```

## 9. 外部依存

- **Tailwind CSS** via CDN (`cdn.tailwindcss.com`)
- **Google Fonts**: Inter / Noto Sans JP / JetBrains Mono / Orbitron
- **Material Symbols** (Google Fonts): アイコン全般
- **Lucide Icons** (optional): SVG スプライト、Material Symbols と併用可

単一 HTML 縛りを解除したので上記の CDN 使用は許容。オフライン切断時は最低限機能（フォールバックフォント + Unicode 絵文字）で動作。

## 10. 実装順序

1. **Phase A**: 本書（design_v2.md）完成 ← 今
2. **Phase B**: app/index.html + app/styles.css の **メイン画面（マトリクス + ヘッダ + サイドバー）だけ**を完璧に作り、ユーザーに見せる（60分）
3. **Phase C**: ユーザー承認後、app/app.js に既存機能を移植（データ層、D&D、Survival、Undo）
4. **Phase D**: Drawer、StatusBar、モバイルレイアウト、テーマ切替
5. **Phase E**: Survival モードの新画面（既存視覚は踏襲、骨格を新構造に統合）

各フェーズ完了ごとに動作確認してフィードバックもらう。
