# flash-study

資格試験向けの学習ツール。フレーズ単位のフラッシュ読み（RSVP）＋ 4択クイズで定着を測る。
NotebookLM 的に「素材を貼る → AI がフラッシュ用テキストとクイズを生成」を目指す（AI は Phase 3）。

このフォルダは **self-contained** です。Claude Code で開発するときは
このフォルダを作業ディレクトリにすると、`.claude/agents` のエージェント群が読み込まれます。

```
flash-study/
  CLAUDE.md              プロジェクトガイド（Claude が最初に読む）
  SETUP.md               エージェントクルーの導入手順
  README.md              このファイル
  docs/
    flash-study-spec.md  仕様書（CLAUDE.md から参照）
  prototype/
    index.html           Phase 1 試作（単一HTML / AI無し / ブラウザで開くだけ）
  .claude/
    settings.json        エージェントチーム有効化 + commit前フック
    agents/              architect / implementer / quiz-evaluator / reviewer / debugger
    scripts/check-no-secrets.sh   APIキー混入を検知してcommitを止める backstop
```

## 試作を動かす

`prototype/index.html` をブラウザで直接開くだけ（ビルド不要・通信なし）。

1. 「サンプルを読込」でデッキを追加
2. 「フラッシュ」タブで RSVP 再生（速度調整可）
3. 「クイズ」タブで 4択に回答
4. 「編集」でデッキ作成・問題追加、「ライブラリ」から JSON の入出力

データの背骨は **1デッキ = 1 JSON**：

```json
{ "id":"", "title":"", "source":"", "flashMode":"original|ai",
  "flashText":"", "quiz":[{"q":"","o":["","","",""],"a":0,"e":""}],
  "quizStatus":"ready|unset", "category":"" }
```

## フェーズ

- **Phase 1（試作・本コミット）** フラッシュUI / 4択クイズ / デッキJSON入出力 / 手動カテゴリ
- **Phase 2** PDF取込(pdf.js) / ワークモードJSON貼付 / 設定画面 / AI自動分類
- **Phase 3** PWA化 / `callLLM` 経由の3プロバイダBYOK / IndexedDBデッキライブラリ

詳細は `docs/flash-study-spec.md` と `CLAUDE.md` を参照。
