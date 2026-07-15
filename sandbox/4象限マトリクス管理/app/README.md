# Neuro Matrix Task OS — `app/`

## 起動
ブラウザで `index.html` を開く。オフライン動作（初回だけ Google Fonts / Material Symbols / Tailwind CDN を読み込み、以降はキャッシュ）。

## ファイル構造

```
app/
├── index.html             ← エントリ (まずここを開く)
├── README.md
├── assets/                ← 共通アセット
│   ├── styles.css         共通 CSS (Light/Dark トークン + 各コンポーネント)
│   ├── theme.js           テーマ切替 (Light/Dark/Auto)、FOUC 防止で <head> 先頭読込
│   └── app.js             データ層 + index 画面のロジック
└── pages/                 ← サブ画面
    ├── completed.html     完了一覧
    ├── survival.html      サバイバルモード (ダーク+ネオン専用スタイル)
    ├── today.html         今日フォーカス
    ├── overdue.html       期限超過
    └── settings.html      設定 (JSON 書出/取込、テーマ、ショートカット)
```

## 画面構成と遷移

- **ダッシュボード** (`index.html`) … 4象限マトリクス。ここから他画面へ遷移
- **サバイバル** (`pages/survival.html`) … 締切集中モード、Orbitron カウントダウン
- **完了一覧** (`pages/completed.html`) … 完了タスクを日付グループで表示
- **今日** (`pages/today.html`) … 今日締切 + 期限超過のみフォーカス
- **期限超過** (`pages/overdue.html`) … 超過タスク専用の警告ビュー
- **設定** (`pages/settings.html`) … テーマ / バックアップ / ショートカット

## データ永続化
LocalStorage に以下のキーを使用（既存 `タスク管理.html` と互換）:

| キー | 内容 |
|------|------|
| `neuro_matrix_v6_data` | タスク本体 (JSON 配列) |
| `neuro_matrix_v6_state` | UI 状態 (Survival中フラグ、target-time、survivalSlots 等) |
| `neuro_matrix_theme` | `light` / `dark` / `auto` |

## テーマ
- CSS 変数 `:root` (Light) / `html.dark` (Dark) の 2 層で定義
- `Auto` は `prefers-color-scheme: dark` に連動
- `pages/settings.html#appearance` で切替可能

## 将来課題
- 詳細編集モーダル（現時点では完了/削除のみ）
- ドラッグ & ドロップでの象限間移動
- Survival モードの JS 動作 (カウントダウン、スロット D&D)
- キーボードショートカット完全対応 (⌘S, ⌘J, ⌘Z)
