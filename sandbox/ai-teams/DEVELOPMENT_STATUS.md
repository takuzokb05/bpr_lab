# AI Teams - 開発状況まとめ (2026-06-02)

> このファイルは現行 **v3（core / api / web の3層）** の状況を集約する。
> 2025-12 までの旧 Streamlit 版（`app.py` / `database.py` / SQLite）は v3 に置き換え済みで、
> 経緯は git 履歴と `archive/` を参照（旧版の説明は本書の対象外）。

## 📊 現状サマリ（2026-06-02）

v2 の致命傷（人格混線・途中経過が見えない・厨二ボイス）を構造から作り直した v3 が、**VPS に実デプロイ
され公開URLで稼働中**（cloudflared クイックトンネル）。追い質問の割り込み・報道テロップUIに加え、本セッションで
**(1) VPS 公開デプロイ**（uvicorn 単一プロセスが静的SPA同居配信）、**(2) BYOK 3社対応**（Anthropic/OpenAI/
Gemini・各自キー持参・サーバ非保存）、**(3) 討論履歴＆再開**（localStorage・モバイル復帰/再読込から復帰）、
**(4) 自分のペルソナ**（クライアント定義・サーバ非保存）、**(5) 編成整理**（司会・議長を自動固定/書記除外）、
**(6) ペルソナ19体**（職種＋偉人）、**(7) 応答の長さプリセット**、**(8) 終了討論を続ける**、を実装・デプロイ。
次の方向は **内製（自前ホスト）LLM**（`SELF_HOSTED_LLM_2026-06.md`）。

> ⚠️ **公開トンネルの罠（要記憶）**: cloudflared は **GET のストリーミングをバッファし POST は素通し**する。
> 再接続/再開は **POST**（`/sessions/{id}/stream` を GET/POST 両対応）で叩く。これを踏まないと「モバイルで
> 切替→Load failed→再開/投げかけが死ぬ」になる。詳細 `DEPLOY_2026-06.md`。

## 📊 旧サマリ（2026-06-01・MVP確定時）

`FEATURE_REVIEW_2026-06.md` で MVP を確定後、本丸「追い質問の割り込み」を実装。報道テロップUI・編成管理・
実LLMトグルを実装。設計→実装→対抗的レビュー→修正のワークフローで high（パストラバーサル・追い質問の
永久ドロップ・HTTPテスト欠落）を是正。

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

## ✅ 2026-06-02 セッションで追加（実装・デプロイ済み）

- **VPS 公開デプロイ**: Next 静的書き出し(out/)を uvicorn が同一オリジン同居配信＋cloudflared クイックトンネル
  ＋Task Scheduler 常駐（AITeams_API/AITeams_Tunnel）。`requirements-v3.txt` を ASCII 化（cp932 罠）。
- **BYOK 3社対応**: 実LLMは各自の `X-LLM-Key`＋`X-LLM-Provider`（Anthropic/OpenAI/Gemini）。サーバ非保存
  （メモリのみ）。`AI_TEAMS_BYOK=1` でサーバ鍵を来訪者に使わせない。OpenAIClient は gpt-5 系の
  max_completion_tokens/temperature 非対応・reasoning_effort、Gemini は thinking_level/temperature 非送信に対応。
  既定モデル gpt-5.5 / gemini-3.5-flash / claude-opus-4-8（env 可変）。レート制限・同時上限・readonly CRUD・
  hmac 定数時間比較・/health の鍵漏洩防止。
- **討論履歴＆再開**: transcript を localStorage 保存（最大20件）。`resumeSession`（POST・cursor=0 replay）で
  再読込/モバイル復帰から復帰。pump は切断で throw せず再接続ループ＋visibilitychange 復帰。
- **自分のペルソナ**: クライアント定義（localStorage）をセッション限定で `custom_personas` 同送（サーバ非保存）。
- **編成整理**: 司会・議長は進行の固定役として自動付与（ピッカーから外す）。書記は除外。
- **ペルソナ19体**: 職種（法務/CFO/エンジニア/マーケター/規制）＋偉人（マスク/ドラッカー/信長/タレブ/アドラー/
  武蔵/室伏）。
- **応答の長さプリセット**（簡潔/標準/じっくり＝max_tokens＋発話指示）／**終了討論を続ける**（前回を文脈に
  引き継ぐ・全文/軽量選択）／**Markdown ストリーミング描画**／**Web検索中の「『〇〇』を調べています…」表示**／
  **ロゴで新規（idle）**。
- テスト: BYOK/provider/verbosity/custom_personas/research-start 等を追加（全 pass）。

## ✅ 2026-06-02（後半セッション）で追加（実装・検証済み・コミット `f331b8b`）

- **モバイルUI刷新**: 固定3レーン `grid-cols-[260px_1fr_320px]` がスマホで横オーバーフローしていた問題を解消。
  lg 未満は**討論を全画面化＋編成/成果を左右スライドドロワー**（ヘッダ ☰/成果 で開閉）、lg 以上は従来3レーン維持。
  中央 main の `min-w-0`＋検索クエリ/URL/topic の折り返しガードが核心修正。閉ドロワーは `inert`（モバイル限定）で
  タブ順/SR から除外＋開閉でフォーカス移動/復帰。Playwright で横オーバーフロー0（390/1366）を数値検証。
- **Web検索結果の可視化**（「活きてるか分からない」への回答）: 機能的には元々 `build_context` が
  `【調査】<brief>` を後続全員へ注入済み（生きている）。UX として、調査メモに「全員に共有」を明示し、
  右パネルに **「調べたこと（N件）」を出典リンク付きで集約**（`ResearchNotes.tsx`）。`buildContinuationContext` も
  「続ける」で調査事実を引き継ぐよう変更（researcher を捨てない）。
- **会議結果の書き出し**（`ExportBar.tsx` / `lib/export.ts`）: 要約/調査結果/会議内容をチェックで選び
  （既定すべて ON・1ファイル）、**コピー or Markdown 保存**。手持ち LLM にそのまま投げられる素の Markdown
  （`# 議題 → ## 要約 → ## 調査結果 → ## 会議内容`）。成果パネル下部に常設（モバイル成果ドロワーにも出る）。
- **対抗レビュー反映**（5次元×敵対的検証, 17→13確定）: continuation 文脈のクランプが末尾の続行指示(tail)を
  切る**回帰を修正**（tail 保護＋budget 下限0＋query 長クランプ）、出典URLの装飾記号剥がし、タップ領域、ほか。

## ✅ 2026-06-06 セッションで追加（実装・検証済み）

ユーザーフィードバック（「会話がスクロールしていって読めない・置いて読みたい」「ペルソナに説明が無いと
どんな人か分からず選べない」）への対応。

- **会話スクロールを『置いて読める』に**（`web/components/Timeline.tsx`）: 旧実装は delta（トークン）毎に
  無条件で末尾へ `scrollIntoView` していた＝上に戻して読もうとしても毎トークン引き戻された。新実装は
  **末尾付近(64px)に貼り付いている間だけ追従（stick-to-bottom）**し、ユーザーが上へスクロールしたら追従を
  止めて **「最新へ」フロートボタン**（ストリーミング中はパルス＋「新しい発言中」）を出す。セッション切替・
  履歴読込・再接続 replay（topic 変化 or turns 空）では貼り付きを初期化し末尾着地（旧挙動への回帰防止）。
- **ペルソナに「詳細」ボタン＋人物説明**（フィードバック2巡: 当初の常時表示が見切れる→詳細展開へ作り直し）:
  ピッカーのカードは **名前＋1行ティーザー（`description`・truncate で1行・見切れ解消）＋「詳細」ボタン**。
  詳細を押すと下に**アコーディオンで `detail` 全文**を表示。**偉人は「何をした人か（背景・功績）＋討論での持ち味」**、
  役割は「会議での具体的な振る舞い」。カードは選択トグルと詳細ボタンを**別 button（入れ子回避）**にした `div` 構成。
  検索は description+detail も対象。`description`/`detail` をデータモデル全層に追加 — `core/personas.py`／
  `api/service.py`（`persona_public`＋`_PERSONA_WRITE_KEYS`）／**`api/main.py` の `PersonaUpsert`・`CustomPersona`**／
  `web/lib/types.ts`／`PersonaPicker`／`PersonaForm`・`MyPersonasDrawer`（入力欄）。
  `personas/**/*.yaml` 46体すべてに description と detail を付与（system_prompt を読み文体・長さを揃え、偉人は事実確認）。
- **対抗レビューで critical 1件を捕捉・修正**: `PersonaUpsert`（Pydantic）に `description`/`detail` が無いと
  extra='ignore' で黙って捨てられ、全置換 save により**既存ペルソナの編集保存で YAML から消える**破壊的バグを是正。
  `relationships` と同じ罠。サービス直叩きの既存テストでは検出不能だったため、**HTTP 層を通る round-trip
  回帰テスト**（description＋detail）を `tests/run_tests.py` に追加。reduced-motion ガード・「最新へ」/「詳細」の
  タップ領域・focus-visible・aria-controls・検索 a11y も改善。偉人 detail の事実精度（稲盛=DDI/KDDI）も是正。
- 検証: 全テスト pass／`next build` 通過／`GET /personas` が46体を description＋detail 付きで返すことを確認。
  2巡目レビューは critical/high/medium ゼロ（low の磨きのみ反映）。

## ✅ 2026-06-07 セッションで追加（個人開発の類似47件を調査→いいところどり）

公開OSS化（github.com/takuzokb05/ai-council）と身内アクセス（Cloudflare Access・https://ai.takuzokb.uk）の後、
個人開発の類似（多人格AI討論）47件を Web 調査し、ai-council に取り入れる価値のある工夫を triage して実装。

- **② 問題再定義ゲート（toggle・opt-in）**: 発散の前に各パネリストが議題を自分の視点で捉え直す1周を挟む
  （司会1人のフレーミングでは吸収できない解釈ズレを多視点で揃える）。`Council(redefine=)` ＋ `SessionRequest.redefine`
  ＋ web の「問題再定義」トグル（既定 OFF）。phase="redefine"（PHASE_LABELS / FOLLOWUP_DISABLED に追加）。
  出どころ: 0xNyk/council-of-high-intelligence, roundtable。
- **③ 議事録を「残った対立点・少数意見」先頭に**: `synthesize` のディレクティブを、合意先頭から
  「1.残った対立点/未解決の問い → 2.棄却/少数意見（理由付きで残す）→ 3.リスク → 4.合意 → 5.アクション」へ。
  意思決定者が「どこが危ういか」を最初に見られる。出どころ: Council(Divergence), AI Council Framework(Protected dissent)。
- **① ブラインド批評（匿名化）は実装→却下**: 批判フェーズで他者を匿名（登壇者A/B）提示し権威・忖度バイアスを
  外す案。実装後、**A/B 制御実験で「そもそも忖度が起きるか」を実測**（同じ穴ある主張を権威の実名 vs 匿名に帰属させ
  懐疑役に批判させる、3シナリオ）。**opus も本番の安いモデルも権威に忖度せず**（anti_conformity＋懐疑役の役割が勝つ）、
  ①が解く問題が存在しなかった＋因縁（差別化点）と哲学が衝突（匿名＝身元を消す／因縁＝身元で衝突）。**丸ごと revert**。
  → 教訓: 他ジャンル（系統1=マルチモデル合議の self-preference bias 対策）の道具を、系統2（偉人ペルソナ）に
  cargo-cult しない。**パクる前に前提を実測**。詳細 [[feedback_oss_extraction_from_monorepo]] と memory。
- 弾いた候補: 確信度スコア（LLM自己申告は校正不能＝偽の精度）／コスト表示（force_local=本人キーで身内利用は低価値）／
  議論フォーク・DB永続化（「続ける」で足り過剰）／@メンション・議長2モード（伸びしろ薄）。
- 内製LLM 着手時にやる: reasoning `<think>` 除去 / rival ペアを別モデルに物理割当（均質化を物理的に減らす）。

## ✅ 2026-06-08 セッションで追加（実討論ログの総動員レビュー→9件QA修正）

ユーザーが ②③ 反映後の実討論ログ(Jobs×共感×マーケター)を「総動員でレビュー」依頼。3並列診断WF→12件発見→
重複統合9件 triage→**修正案そのものを9並列で対抗検証**（診断の誤りと直し方の妥当性を実コードで叩く）→
横断インターフェース確定→実装→独立検収（既存テスト/新規8テスト/web独立ビルド/interactive実produce e2e/対抗レビュー）。

- **rank1 tool-call特殊トークン・`<think>`漏れ除去**: `core/llm_client.py` に `_strip_model_artifacts()` 新設、
  全文確定地点（各 generate 戻り・調査要約・`orchestrator.py` の stream 全文確定 L302）に適用。delta には適用しない
  （境界跨ぎで壊れる＝別PR）。**レビュー案の正規表現は実観測トークン `<｜｜DSML｜｜tool_calls>`(内部に複数バー)を
  取りこぼしていた**ため `_SPECIAL_TOK_RE=r"<[｜|][^>]*>"` に独自修正（誤爆ゼロを実検証）。
- **rank2 議事録の黙った途中切れ**: 空ターン救済リトライ(`_retry_no_reasoning`/`_retry_cloud_empty`)を
  `(content, finish_reason)` tuple化し、retried でも length を検出して `_TRUNCATION_MARKER` を付ける（空retryはゴースト防止）。
  ※budget不足でなく「検出スキップ」バグ（synthesis_mt=max(8192,vb*2)で潤沢を確認）。
- **rank3 調査JSON失敗の堅牢化**: `_openrouter_search_once` に `stream:false`/`Accept:application/json` 明示、
  urlopen戻りを`errors="replace"`で取り`JSONDecodeError`個別捕捉、失敗本文は `_sanitize_research_snippet()` で
  Bearer/sk-キー伏字にして surface。※「SSE混入が主因」は誤診（非ストリーミングPOSTは通常JSON）→SSE復元器は作らない。
- **rank4 司会指名の食い違い**: opening の「特定の立場の人へ発言を促す」→「特定の個人を名指しせず、全員が順に述べる
  と告げて口火」。RoundRobin実順と一致。※bridge/収束口火/closing の同型3箇所は**全て誤診**（あれは検証すべき「案の
  指名」でパネリスト指名でない）→ opening 1箇所のみ修正（commit 9e74283 の的絞り機能を壊さない）。
- **rank5 redefine等で要調査誘発**: `_speak(research_override:bool|None)` 追加（OFF専用論理積）。
  redefine/収束口火/bridge/closing/followup 取り次ぎで `research_override=False`。opening seed/本編/synthesis は維持。
  ※service側phaseガード案は opening seed 握り潰し＆同一phase文字列で分離不能のため**却下**。
- **rank6 出典の文脈肥大**: `context.py` で LLM 文脈に積む researcher ターンのコピーだけ出典を上位N件
  (`AI_TEAMS_RESEARCH_CTX_MAX_SOURCES` 既定5)に圧縮。**Turn.content 自体は不変**（フロント/export/SSE 5層を壊さない）。
  ※「Turn.contentから出典除去」案は破壊的で却下。
- **rank7 cap=有益調査回数**: `_is_useful_research()`（失敗/空/未対応/上限/モックは無価値＝cap非消費）＋
  per-turn上限(`AI_TEAMS_RESEARCH_PER_TURN` 既定2)。ターンは消さず（UI固着回避）count算入のみ変更。
- **rank8 export出典の非対称**: `web/lib/research.ts` に `splitBrief`/`hostOf` 切り出し、export は findings本文＋
  出典を `<details>` 折り畳みに。UI(ResearchNotes)と共有。
- **rank9 整形チョークポイント化**: `_format_research_brief()` で Anthropic/OpenRouter の出典整形を一本化（バイト一致）、
  調査プロンプトに「箇条書き最大5項目・各1〜2文」ガード。※「二重実装で乖離」は誤診（プロンプトは既に共有）。
- 検収: 既存テスト全pass＋新規8テスト＋web独立ビルドEXIT0＋interactive実produce e2e（rank4/rank5を全フェーズで確認・
  調査発火・dedup・done完走）＋対抗的レビュー。**「直し方が正しいか」を実装前に9並列で対抗検証した結果、診断の誤り
  （rank3/4/9の因果ミス）と危険な直し方（rank5②/rank6②/rank7の握り潰し）を実装前に除去できた**。
- **実装後の対抗的レビュー（独立エージェント・74分・テスト自己再実行）で M1/L1 を追加是正**:
  - **M1（実害最大・是正済）**: `_strip_model_artifacts` が「AI内部仕様を“話題として”論じる討論本文」を破壊し得た。特に
    閉じ無し `<think>` が以降を全削除＝発言全消失。→ ①`_THINK_OPEN_RE` を `\A` 固定し**先頭の推論リークのみ**全削除（途中
    言及は孤立タグだけ落とし本文は残す）②コード(```…``` / `…`)内のリテラル例は退避して保護。回帰4テスト追加。
  - **L1（軽微・是正済）**: `_RESEARCH_SOURCES_RE` が出典途中の空行でマッチを切り後続URLを取りこぼし得た（制御経路では非発生）。
    →空行/空白行を許容、非"- "プローズ行はマッチを切る（過剰マッチ防止）。回帰2テスト追加。
  - **L2（記録のみ・意図的）**: deepen追い質問のパネリスト応答は `research_override=False` で実web調査を起こさない。乱発抑制の
    トレードオフ。事実取得が要る追い質問では調査されない点は仕様として記録（将来見直し候補）。
  - critical/high はゼロ（3-wayマージ整合・tuple化・後方互換・prefix一致・synthesis経路は健全と再確認）。再検収テスト 405 assertions 全pass。
- ⚠️ 未反映: 上記9件＋M1/L1是正は**ローカルのみ**。OSS(github.com/takuzokb05/ai-council)と②③＋本QA修正は未同期。VPS本番も未デプロイ。

## 🚧 次の一手

1. **内製 LLM = Phase 1 実装済み（2026-06-02 後半）**: `SELF_HOSTED_LLM_2026-06.md`。`OpenAIClient(base_url=,
   search_mode=)` ＋ `provider="local"` ＋ `AI_TEAMS_FORCE_LOCAL` ＋ OpenRouter web_search を実装・テスト pass。
   **採用方針＝シナリオA**（開源フロンティアAPIを base_url で叩く）。情勢調査の訂正: 開源モデルは Opus 4.6 級に
   肉薄／検索は OpenRouter で解決／API が激安で「コストゼロのための自前ホスト」は不要＝自前の価値は所有・特化。
   **次**: `.env` に OpenRouter キー等を入れて実討論で Opus と比較（クイックスタートは設計図参照）。育てる(蒸留)は
   開源教師で Phase 4。
2. **安定URL＋ログイン**（任意）: 名前付きトンネル＋Cloudflare Access（要 Cloudflare ドメイン・対話ログイン）。
   今は揮発URL（`cloudflared.log` で確認）＋BYOK＋レート制限が公開ゲート。
3. **磨き込み（低リスク）**: 楽観エコーの厳密照合 / continueScope の永続化 / 自前 Web 検索(SearXNG)。

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
├── DEPLOY_2026-06.md             # 公開デプロイ手順（同一オリジン+cloudflared+BYOK・cloudflared GET罠）
├── SELF_HOSTED_LLM_2026-06.md    # ★内製（自前ホスト）LLM 設計図（次の主軸）
├── COMPARISON_2026-06_council_vs_single.md # council vs 単体 比較（モデル選定手法）
├── FEATURE_REVIEW_2026-06.md     # 機能の要不要レビュー＋MVP決定(F節)
├── INJECTION_DESIGN_2026-06.md   # 追い質問の割り込み 設計 v2
├── REBUILD_PLAN.md / UIUX_REVIEW_2026-05.md / RESEARCH_2026-05_orchestration.md
└── archive/     # 旧 Streamlit 版ほか
```

---

**更新日**: 2026-06-02  
**ステータス**: v3 を **VPS に実デプロイ・公開URLで稼働**（cloudflared クイックトンネル）。BYOK 3社対応・履歴/再開・
自分のペルソナ・編成整理・ペルソナ19体・応答長/続ける・モバイル復帰、まで実装＆デプロイ。テスト全 pass。
次の主軸は **内製 LLM**（`SELF_HOSTED_LLM_2026-06.md`）。
