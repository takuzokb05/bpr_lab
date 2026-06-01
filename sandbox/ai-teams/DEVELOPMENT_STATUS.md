# AI Teams - 開発状況まとめ (2026-06-01)

> このファイルは現行 **v3（core / api / web の3層）** の状況を集約する。
> 2025-12 までの旧 Streamlit 版（`app.py` / `database.py` / SQLite）は v3 に置き換え済みで、
> 経緯は git 履歴と `archive/` を参照（旧版の説明は本書の対象外）。

## 📊 現状サマリ

v2 の致命傷（人格混線・途中経過が見えない・厨二ボイス）を構造から作り直した v3 が動作。
`FEATURE_REVIEW_2026-06.md` で MVP を確定後、本丸「**追い質問の割り込み**」を実装完了。
あわせて UI を**報道テロップ強化**（ON AIR / フェーズ字幕 / 名プレート / 時刻）、**編成管理**
（プリセット編成・ペルソナ CRUD・検索/タグ/折りたたみ）、**実 LLM 接続トグル**（.env 読込）を実装。
設計→実装→対抗的レビュー→修正のワークフローを回し、検出した high（パストラバーサル・
追い質問の永久ドロップ・HTTP テスト欠落）を是正済み。テスト 15 件 pass / `next build` 通過。

## 🏗 アーキテクチャ（v3）

- **core/**（フレームワーク非依存・テスト可能）
  - `orchestrator.py` … `Council.run()` が `Turn` を逐次 yield する純粋ジェネレータ。
    フェーズ進行（発散→批判→収束）＋ラウンドロビンで沈黙ゼロ。
  - `context.py` … 自分=assistant / 他者=`【名前】`付き user で人格混線を根治。
  - `llm_client.py` … Anthropic / Mock の統一IF（Mock はキー不要で決定的）。
  - `personas.py` … YAML からペルソナ読込（accent 色・monogram 付き）。
- **api/**（FastAPI・薄い）… `service.py`（FW非依存ロジック）＋ `main.py`（ルーティング）。
  `council.run()` を SSE 配信 → 「途中経過が見えない」を構造的に解消。
- **web/**（Next.js15 + Tailwind4）… 3レーンIA・モノグラムアバター・SSEストリーミング表示。

## ✅ 完了

- v3 3層の基盤（core / api(SSE) / web）。`next build` 通過・両サーバ実起動で疎通済み。
- ボイス刷新（厨二語→「討論を開始/編成/成果」等）。
- **Red Team 保証** / **エグゼクティブサマリ3行**（MVP確定機能）。
- **トークンストリーミング**（`generate_stream` + `run(emit=…)`、delta タイピング表示・自動再接続）。
- **追い質問の割り込み**（本丸）: core `run(pull=…)`＋`POST /sessions/{id}/messages`。人間ターン・
  司会再提示・追い質問ラウンド（順序固定1周・束ね）を既存イベントで表現。本編フェーズのみ受理し、
  仕上げ中は 409。楽観的エコー＋FIFO 重複解消。`DELETE /sessions/{id}` で協調キャンセル（実LLM課金停止）。
- **報道テロップ UI**: OnAir / Chyron（フェーズ字幕）/ NamePlate（名前·フェーズ·時刻、サーバ採番 ts）。
- **編成管理**: プリセット編成（builtin 同梱＋ユーザー保存）/ ペルソナ CRUD（YAML 生成・category 移動）/
  PersonaPicker 検索・タグ・折りたたみ。書込 id はパストラバーサル防止で charset 制限。
- **実 LLM 接続トグル**: `.env`（python-dotenv, override=False）読込＋`/health` 拡張（キー値非露出）。
  既定は Mock（無料）。実 LLM 選択時のみコスト注記。
- テスト 15 件（既存9＋ followup_injection / llm_status / persona_service_crud / preset_service /
  http_api(TestClient) / followup_e2e）。`IMAGE_ASSETS_PROPOSAL_2026-06.md`（画像は CSS/SVG で完結＝採用候補ゼロ）。

## 🧭 確定した方針（決定ログ）

`FEATURE_REVIEW_2026-06.md` F節 / `INJECTION_DESIGN_2026-06.md` に詳細。

1. **MVP = D案＋「人間操作を厚く」**。
2. MVP必須 = 追い質問の割り込み・サマリ3行・Red Team保証（＋KEEPと低コストなバッジ/免責）。
3. **品質レビュー（AIがAIを採点）= 後回し**。観点テンプレ = 任意。
4. 追い質問のアーキ = **案A ステートフル・セッション**（最もUXが高い方）。
5. 応答ルーティング = **司会が再提示 → 次ラウンドで全員が織り込む**。
6. **トークンストリーミングを先に入れる**（UX最大のレバー）。
7. **軽い再接続 resume**（案Aの弱点「切断でセッション消滅」を緩和）。
8. レビューで挙げた軽量UX修正を設計に織り込み（楽観的エコー / 注入ラウンドの順序固定・
   束ね / まとめ段階で入力無効化）。

## 🚧 次の一手（残作業・改善候補）

ストリーミング先行の6ステップ（core stream → API transport → core 注入 → API messages →
web → 実起動疎通）は**完了**。残りは磨き込みと保留事項:

1. **実 LLM での実走確認**: `.env` に `ANTHROPIC_API_KEY` を入れ、UI トグルを実 LLM にして
   1セッション通す（コスト発生。プロデューサは無観客でも完走する点に留意）。
2. **レビュー保留事項（低リスク）**: 楽観的エコーの client_msg_id 厳密照合（現状 FIFO 推測）/
   再接続で初回 start フレーム欠落時の hang フォールバック / PersonaForm の monogram プレビューを
   サーバ規則と一致 / 旧 `stream_council`（テスト専用）の整理。
3. **`.gitignore` 方針の最終確認**: ユーザー作成プリセットは ignore（builtin はコミット）にした。
   UI 生成ペルソナ（`personas/` 配下）の追跡可否は要判断（個人 system_prompt 混入に注意）。

## 🔭 後回し（Phase 6 以降）

品質レビュー / 観点テンプレート / 巻き戻し分岐 / 永続化（SQLite・マルチワーカー共有ストア）/
コスト表示 / pause-on-no-client。

## 📁 主要ファイル

```
sandbox/ai-teams/
├── core/        # orchestrator(run emit/pull) / context / llm_client(stream) / personas（FW非依存）
├── api/         # service.py（ロジック・Session・CRUD）＋ main.py（FastAPI ルーティング・SSE）
├── web/         # Next.js15 + Tailwind4。components/ に OnAir/Chyron/NamePlate/Persona系/Preset系/LlmToggle
├── personas/    # ペルソナ YAML（UI から CRUD 可）
├── presets/     # 編成プリセット。builtin/ は同梱（コミット）、直下はユーザー作成（gitignore）
├── tests/       # run_tests.py（mock で決定的・15件）
├── FEATURE_REVIEW_2026-06.md     # 機能の要不要レビュー＋MVP決定(F節)
├── INJECTION_DESIGN_2026-06.md   # 追い質問の割り込み 設計 v2
├── IMAGE_ASSETS_PROPOSAL_2026-06.md # 画像素材提案（CSS/SVG完結＝採用候補ゼロ）
├── REBUILD_PLAN.md               # 再構築の全体計画
├── UIUX_REVIEW_2026-05.md / RESEARCH_2026-05_orchestration.md
└── archive/     # 旧 Streamlit 版ほか
```

---

**更新日**: 2026-06-01  
**ステータス**: v3 稼働。追い質問の割り込み・報道テロップUI・編成管理・実LLMトグルを実装完了
（設計→並列実装→対抗的レビュー→修正のワークフロー実施、high 是正済み、テスト15件 pass）。
次は実 LLM 実走確認と保留事項の磨き込み。
