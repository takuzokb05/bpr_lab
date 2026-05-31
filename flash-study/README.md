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
    index.html           Phase 1 試作（単一HTML / Claude artifact APIでクイズ生成）
  .claude/
    settings.json        エージェントチーム有効化 + commit前フック
    agents/              architect / implementer / quiz-evaluator / reviewer / debugger
    scripts/check-no-secrets.sh   APIキー混入を検知してcommitを止める backstop
```

## 試作を動かす

`prototype/index.html` をブラウザで直接開くだけ（ビルド不要）。サンプルデッキを内蔵。

1. ライブラリから内蔵サンプル（地方自治 / 固定資産税 / 行政手続）を選ぶ
2. デッキ詳細で速度を調整して「学習をはじめる」→ 3カウント後に RSVP 再生
3. 読了後にそのまま 4択の「まとめ問題」→ 結果画面
4. 「＋ 教材から新規」で本文を貼り付け、原文/AI再構成の切替＋クイズ自動生成（Claude artifact API）
5. デッキの書き出し / 読み込み（JSON ファイル）、職場用に JSON 貼り付け取込も可

> Phase 1 はアーティファクト前提のため保存はファイル書出/読込で代替（localStorage は使わない）。
> AI 呼び出しは Claude 内 API のキーレス代理呼び出し。BYOK 3社対応は Phase 3。

データの背骨は **1デッキ = 1 JSON**（仕様書 §1）：

```json
{ "id":"", "title":"", "source":"", "flashMode":"original|ai",
  "flashText":"", "quiz":[{"q":"","o":["","","",""],"a":0,"e":""}],
  "quizStatus":"ready|unset", "createdAt":"ISO8601" }
```

> 注：`CLAUDE.md` の背骨は末尾が `category`、仕様書 v0.1 は `createdAt`。
> 現物の HTML は `category`（手動カテゴリ＝カテゴリ別グループ表示）を使用。Phase 2 で正式に統一する。

## フェーズ

- **Phase 1（試作・本コミット）** フラッシュUI / 4択クイズ / デッキJSON入出力 / 手動カテゴリ
- **Phase 2** PDF取込(pdf.js) / ワークモードJSON貼付 / 設定画面 / AI自動分類
- **Phase 3** PWA化 / `callLLM` 経由の3プロバイダBYOK / IndexedDBデッキライブラリ

詳細は `docs/flash-study-spec.md` と `CLAUDE.md` を参照。
