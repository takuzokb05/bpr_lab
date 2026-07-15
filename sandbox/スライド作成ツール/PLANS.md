# スライド作成ツール

## Purpose / Big Picture

**完成物: AI スライド自動生成 CLI ツール**

ドキュメント（PDF/テキスト）を読み込み、Gemini API でスライド構成を生成し、Imagen 3 で背景画像を作成、AI でテキスト配置を最適化して PPTX を出力する CLI ツール。

具体的には:
1. ユーザーが資料ファイルを指定する
2. スライドのテイスト（色調・スタイル）を対話的に決める
3. AI がスライド構成を生成し、背景画像を作成する
4. テキストを最適配置して PPTX を出力する
5. 1枚単位でのリライト（再生成）が可能

**背景**: NotebookLM のスライド生成は便利だが15枚制限がある。枚数無制限で、背景画像生成・テキスト配置最適化まで行える自作ツールを構築したい。

## Progress

### Phase A: 技術調査（完了）

- [x] Q1: Gemini API → docs/01_gemini_api.md
- [x] Q2: Imagen 3→4, Nano Banana Pro → docs/02_imagen3.md
- [x] Q3: python-pptx → docs/03_python_pptx.md
- [x] Q4: モデル選定 → docs/04_model_selection.md
- [x] fact-checker → docs/05_fact_check.md
- [x] devils-advocate → docs/06_devils_advocate.md

### Phase B: 実装 <!-- ← 現在のフェーズ -->

- [x] SPEC.md の具体化（Gemini 3 Flash + Nano Banana Pro で確定）
- [x] F1: CLI基盤 + config + Gemini API接続
- [x] F2: 資料読み込み（document_reader）
- [x] F3: スライド構成生成（slide_planner / Gemini 3 Flash）
- [x] F4: 背景画像生成（image_generator / Nano Banana Pro + Imagen 4 Fast フォールバック）
- [x] F5: テキスト配置（ルールベース）+ PPTX出力（pptx_builder）
- [ ] F6: 1枚単位リライト機能
- [ ] 動作確認（実際のPDF/テキストでエンドツーエンドテスト）

## Surprises & Discoveries

<!-- 作業中に遭遇した予期しない知見を記録する -->

## Decision Log

- 判断: プロジェクトタイプを hybrid（調査→実装）とする
  理由: Gemini API / Imagen 3 / python-pptx / テキスト配置最適化手法など、
        実装前に調査が必要な外部依存が多数あるため
  日付: 2026-02-21

- 判断: CLI ツールとして構築する（Web UI ではなく）
  理由: 最もシンプルに構築でき、パイプライン処理にも適している
  日付: 2026-02-21

- 判断: 背景画像生成に Imagen 3（Gemini API 経由）を使用する
  理由: ユーザーが既に Gemini API キーを保有しており、追加コストが最小限
  日付: 2026-02-21

## Outcomes & Retrospective

<!-- 各Phase完了時に振り返りを記録する -->

## Context and Orientation

### ディレクトリ構造

```
スライド作成ツール/
├── PLANS.md              # このファイル
├── SPEC.md               # 実装仕様書（Phase B）
├── .claude/
│   ├── claude.md         # Claude Code設定
│   ├── settings.json     # WebSearch/WebFetch自動承認
│   ├── whiteboard.md     # エージェント間情報共有
│   ├── skills/           # スキル定義
│   └── agents/           # エージェント定義
├── docs/                 # Phase A: 調査ドキュメント
├── references/           # 元資料・参考文献
├── src/                  # Phase B: 実装
├── tests/                # テスト
└── data/output/          # 生成スライド出力先
```

### 関連ファイル

- `claude.md`: プロジェクトのClaude Code設定（フェーズ構成・開発ルール・調査ルール）
- `SPEC.md`: 実装仕様書（Phase B で具体化）
- `.env.example`: 環境変数の一覧

### 既知の制約

- Gemini API のレート制限は調査フェーズで確認する
- Imagen 3 の出力解像度・フォーマットは調査フェーズで確認する
- テキスト配置最適化に使う AI は Phase A Q4 で選定する
