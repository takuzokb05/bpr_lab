# web/ — AI COUNCIL フロントエンド（Next.js 15 + Tailwind 4）

`api/`（FastAPI + SSE）を購読し、討論を**1発言ずつストリーミング表示**する。
デザインは報道番組系の静かな上質さ（`../UIUX_REVIEW_2026-05.md` のトークン準拠）。
絵文字は使わず、アバターは**モノグラム＋カテゴリ色**。

## 画面構成（3レーン）

```
ヘッダー: AI COUNCIL                              ● 状態
┌──────────┬─────────────────────┬────────────┐
│ 編成(左)  │   討論(中央・主役)     │ 成果(右)    │
│ ペルソナ  │  議題 / 発言タイムライン │ 議事録      │
│ 選択      │  入力バー(⌘+Enter)    │ (議長の統合) │
└──────────┴─────────────────────┴────────────┘
```

## 起動（API と2プロセス）

```bash
# 1) バックエンド（別ターミナル、sandbox/ai-teams で）
uvicorn api.main:app --port 8000

# 2) フロント
cd web
npm install
npm run dev          # http://localhost:3000
```

`next.config.mjs` の rewrites で `/api/*` → `http://localhost:8000/*` にプロキシする
（`API_BASE` 環境変数で変更可）。

## 構成

| パス | 役割 |
|---|---|
| `app/page.tsx` | 3レーンのページ本体・状態管理 |
| `lib/sse.ts` | `fetch`+ReadableStream で SSE を自前パース（EventSource は POST 不可のため） |
| `lib/types.ts` | API と共有する型・表示ラベル |
| `components/Avatar.tsx` | モノグラム・アバター（絵文字の置き換え） |
| `components/PersonaPicker.tsx` | 左：カテゴリ別ペルソナ選択 |
| `components/Timeline.tsx` | 中央：発言タイムライン（フェードイン） |
| `components/MinutesPanel.tsx` | 右：議事録（議長の synthesis） |
| `app/globals.css` | デザイントークン（@theme） |

## 既知の未対応（次段）

- フロントは現状 `mock: true` 固定（API キー不要でデモ可能）。実 LLM 接続トグルは未実装。
- 「介入（司会に指示）」「この発言から巻き戻す」など人間操作系 UI は未実装。
- モバイル縦積みレイアウトは未対応（現状デスクトップ3カラム前提）。
