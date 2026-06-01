# AI Teams - 開発状況まとめ (2026-06-01)

> このファイルは現行 **v3（core / api / web の3層）** の状況を集約する。
> 2025-12 までの旧 Streamlit 版（`app.py` / `database.py` / SQLite）は v3 に置き換え済みで、
> 経緯は git 履歴と `archive/` を参照（旧版の説明は本書の対象外）。

## 📊 現状サマリ

v2 の致命傷（人格混線・途中経過が見えない・厨二ボイス）を構造から作り直した v3 が動作。
直近は `FEATURE_REVIEW_2026-06.md` で **MVP を確定**し、低コスト機能を実装、
本丸「追い質問の割り込み」の**設計を確定（v2）**したところ。

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
- **MVP確定機能（今セッション実装・テスト緑）**
  - 🆕 **Red Team 保証**（最低1名が反論する役。同調バイアス対策。`run(red_team=…)`）
  - 🆕 **エグゼクティブサマリ3行**（議長が synthesis 前に 結論/根拠/次の一手）
  - UI: サマリを成果パネル上段に強調＋AI討論の免責表示。

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

## 🚧 次の一手（実装ステップ・ストリーミング先行）

`INJECTION_DESIGN_2026-06.md` の通り。`emit/pull=None` を後方互換の既定にするため、
**既存テストは無改修で通る**前提。

1. **core ストリーミング**: `generate_stream` ＋ `run(emit=…)` ＋テスト。
2. **API トランスポート**: バックグラウンド実行＋`events/seq`バッファ＋tail SSE＋
   `GET /sessions/{id}/stream?cursor=N` 再接続＋テスト。
3. **core 注入**: `run(pull=…)` ＋ 追い質問ラウンド（順序固定・束ね）＋テスト。
4. **API メッセージ**: `POST /sessions/{id}/messages`、`start` に session_id。
5. **web**: delta タイピング描画／再接続／楽観的エコー／入力欄のフェーズ制御。
6. 実起動で疎通（ストリーム表示・割り込み注入・接続断→再接続）。

## 🔭 後回し（Phase 6 以降）

品質レビュー / 観点テンプレート / 巻き戻し分岐 / 永続化（SQLite・マルチワーカー共有ストア）/
コスト表示 / pause-on-no-client。

## 📁 主要ファイル

```
sandbox/ai-teams/
├── core/        # orchestrator / context / llm_client / personas（FW非依存・テスト可）
├── api/         # service.py（ロジック）＋ main.py（FastAPI ルーティング・SSE）
├── web/         # Next.js15 + Tailwind4 フロント
├── personas/    # ペルソナ YAML
├── tests/       # run_tests.py（mock で決定的）
├── FEATURE_REVIEW_2026-06.md     # 機能の要不要レビュー＋MVP決定(F節)
├── INJECTION_DESIGN_2026-06.md   # 追い質問の割り込み 設計 v2
├── REBUILD_PLAN.md               # 再構築の全体計画
├── UIUX_REVIEW_2026-05.md / RESEARCH_2026-05_orchestration.md
└── archive/     # 旧 Streamlit 版ほか
```

---

**更新日**: 2026-06-01  
**ステータス**: v3 基盤稼働。MVP確定・低コスト機能実装済み。追い質問は設計v2確定 → 実装着手前。
