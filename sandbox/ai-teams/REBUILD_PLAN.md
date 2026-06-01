# AI Teams v3 — 再構築計画 / TODO

作成日: 2026-05-31
背景: 2025-12 に初作成（v1 ai_council / v2 app.py）したが討論挙動が不安定で中断。
モデル自体が安定した今、作り直す。後続の **dynamicworkflows** に乗る土台を作るのが本ゴール。

---

## 0. 今回の方針（決定事項）

- **デフォルトは単一プロバイダー（Claude）**。
  - v2 不安定の主因は 3社マルチAPI対応の肥大化（`llm_client.py`）。
    - マルチモーダル形式差・メッセージスキーマ差・OpenAI `stop` 最大4個制限・`o1` 特殊分岐。
    - Gemini パスが会話を `"role: content"` の1本文字列に潰しており役割構造が壊れる（`llm_client.py:202,206`）。
    - `models.txt` / `model_versions.txt` / `check_models.py` 等＝3社のモデル名変動に振り回された痕跡。
  - **ペルソナの違い ≠ モデルの違い**。キャラはシステムプロンプトで作る。単一モデルの方が安定・再現性・コスト管理で有利。
  - ただし `LLMClient` は差し替え可能なIFを維持し、「特定ペルソナだけ別モデル」を後から任意でONできる余地は残す。
  - **【2026-05 調査による補正】** 「混線」と「均質化」は別問題（→ `RESEARCH_2026-05_orchestration.md`）。
    単一モデルは**混線対策としては十分**だが、同一モデルで全ペルソナを動かすと出力が収束する
    **representational collapse（均質化/echo chamber）**が起きる（査読系で繰り返し報告）。
    そこで `persona.model` 上書きは「任意」ではなく**多様性確保の正式機能に格上げ**し、
    モデルを分けない場合も反同調プロンプト・対立ペア・温度差を必須とする。
    → 単一APIは「安定のため」には不要、「多様性のため」には有効。

- **ペルソナはデータ駆動（レジストリ化）**。コードに埋めず、追加＝データ追加で済む形に。
  - これが dynamicworkflows で「誰を・どの順で・何をさせるか」を動的合成する前提になる。

---

## 1. 後始末（done / 本コミット）

- [x] 実APIキー入りの `API_KEY.txt` を git 追跡解除（キーは全て失効・再発行済み）
- [x] `ai_teams.db` を追跡解除
- [x] `__pycache__/*.pyc` を追跡解除
- [x] `dist/ai_teams_standalone.py`（ビルド成果物）を追跡解除
- [x] `models.txt` / `model_versions.txt` を追跡解除
  - すべて `.gitignore` 記載済みだが ignore 前にコミットされていたため。ローカルファイルは保持。
- [ ] （任意・要判断）履歴からも完全消去するか（`git filter-repo`）。キー失効済みなら優先度低。

---

## 2. アーキテクチャ（dynamicworkflows を見据えた3層分離）

```
ai-teams/
├─ core/
│  ├─ llm_client.py     # 単一IF。デフォルト=Claude。プロバイダーは差し替え可能だが標準は1社
│  ├─ personas.py       # ペルソナ・レジストリ（データ駆動・YAML/JSON ロード）
│  └─ orchestrator.py   # 討論エンジン：ターン制御・フェーズ・終了条件（UIから独立）
├─ personas/            # ペルソナ定義（データ）
│  ├─ thinking/         # 論理 / アイデア / 共感 / 司会 / 書記
│  ├─ founders/         # 著名経営者
│  └─ philosophers/     # 哲学者
├─ app.py               # UI（薄く保つ。ロジックは core/ に置かない）
└─ data/                # SQLite 等（gitignore）
```

- **orchestrator を UI から完全に分離**するのが最重要。
  - v2 の「DBに保存されるが画面に出ない / 途中経過が見えない」は Streamlit `st.rerun()` 依存の表示ロジックが原因。
  - エンジンを純粋関数的なジェネレータ（`yield` で1発言ずつ返す）にし、UIは描画専念にする。
- この core/ がそのまま dynamicworkflows のランタイムになる。

---

## 3. ペルソナ・レジストリ仕様（Q3対応）

ペルソナ1件 = 1データ。スキーマ（案）:

```yaml
id: steve_jobs
display_name: スティーブ・ジョブズ
category: founders        # thinking | founders | philosophers
avatar: "🍎"
model: null               # null=デフォルト(Claude)。後から任意で上書き可能
tags: [product, design, vision]
system_prompt: |
  あなたはスティーブ・ジョブズとして振る舞う。...（思想・口調・判断軸）
```

### 実装したいペルソナ（初期案・要取捨選択）
- 思考スタイル系（v1継承）: 司会 / 論理 / アイデア / 共感 / 書記
- 経営者: スティーブ・ジョブズ / イーロン・マスク / ジェフ・ベゾス / 稲盛和夫 / 孫正義 / ウォーレン・バフェット
- 哲学者: ソクラテス / ニーチェ / 老子 / カント / マルクス・アウレリウス

> ⚠️ 実在人物の「なりきり」は史実・思想に基づく演出である旨を UI に明示（誤情報・誤帰属の注意書き）。

---

## 4. 実装 TODO（順序）

- [~] **Phase 0**: core/ ディレクトリ作成（done）／既存 v2 資産の archive 整理は未（旧 app.py 等は当面残置）
- [x] **Phase 1**: `core/llm_client.py` を単一プロバイダー（Claude）に縮小・安定化（抽象IF＋AnthropicClient＋MockLLMClient）
- [x] **Phase 2**: `core/personas.py` + `personas/*.yaml` のレジストリ実装（thinking/founders/philosophers、id重複検知つき）
- [x] **Phase 3**: `core/orchestrator.py` を UI 非依存のジェネレータとして実装（run() が Turn を逐次 yield）
  - [x] 4.5-A: 1ペルソナ=1隔離コール（自分=assistant / 他者=name付きuser側。AutoGen方式）で人格混線を根治 → `core/context.py`・テスト pass
  - [x] 4.5-B: コード側のラウンドロビンで各ラウンド全員発言＝沈黙を根治 → `RoundRobinScheduler`・テスト pass
  - [x] 4.5-C: 均質化対策の土台＝`persona.model`分散（テスト pass）＋反同調プロンプト（`ANTI_CONFORMITY`）＋温度差（YAML）
  - [x] 4.5-D: chairman統合（chair ペルソナが最後に合意/対立/リスク/ネクストアクションを統合）※収束検知での早期停止は未
  - [x] 4.5-E: 毎ターン system にペルソナ再注入（fidelity decay対策）
  - 検証: `tests/run_tests.py`（API不要・全 pass）、疎通は `demo.py`
- [ ] **Phase 4**: UI（→ `UIUX_REVIEW_2026-05.md` で方向決定）
  - 見た目=報道番組系の静かな上質さ／絵文字ほぼ全廃＋アイコン体系／**Streamlitから Next.js+SSE へ移行検討**
  - [x] `api/`(FastAPI) で `council.run()` を SSE 配信（`/health` `/personas` `/sessions`）→ v2の「途中経過が見えない」を構造的に解消。service.py はFW非依存でテスト済み
  - [x] ペルソナに `accent` 色＋`monogram` を追加（絵文字 `avatar` 依存をUIから外す下ごしらえ）
  - [x] `web/`(Next.js15+Tailwind4) で3レーンIA・モノグラムアバター・SSEストリーミング表示。`next build`通過＋両サーバ実起動でプロキシ/SSE/HTML描画を疎通確認
  - [x] ボイス刷新（厨二語の置換）をUI文言に反映（討論を開始/編成/成果(議事録)/進行中…）
  - [ ] 人間操作系UI（「介入」「巻き戻し」）・実LLM接続トグル（現状フロントは mock 固定）・モバイル縦積みは次段
- [~] **Phase 4.6**: 機能の要不要レビュー（→ `FEATURE_REVIEW_2026-06.md`）で MVP 確定（D＋人間操作厚め）
  - [x] Red Team 保証（core: 最低1名が反論。同調バイアス対策）＋テスト
  - [x] エグゼクティブサマリ3行（core: 議長が synthesis 前に結論/根拠/次の一手）＋テスト
  - [x] UI: サマリを成果パネル上段に強調表示＋AI討論の免責表示。`next build`通過・SSEでphase順疎通確認
  - [ ] 追い質問の割り込み（進行中セッションへの人間入力）＝次段の本丸
        → 設計確定 v2: `INJECTION_DESIGN_2026-06.md`。レビューで「UX優先」を再確認し
          **トークンストリーミング先行**＋**軽い再接続resume**を追加 → 注入単体から
          セッション/トランスポート層の再設計にスコープ拡大（案A・司会再提示→全員織り込み）
  - [ ] 合意/対立バッジ（議長出力の構造化＋UI）
- [ ] **Phase 5**: 経営者・哲学者ペルソナを YAML で追加（jobs / socrates を雛形として実装済み。今後拡充）
- [ ] **Phase 6**: 永続化（SQLite）を「あれば便利」レベルで戻す（v2のDB資産を流用可）
- [ ] **Phase 7（残課題）**: 収束検知による早期停止、ストリーミング出力、コスト計上

---

## 4.5. v2 で挫折した2大バグと根治策

> 両方とも根因は同じ＝「ターン制御と人格管理を LLM 任せにした」。v3 では **制御を orchestrator（コード）に移す**ことで根治する。

### バグA: キャラが混ざる（人格混線）
- **原因（v2）**: 全エージェントの過去発言を1つの `messages` 配列に `role: assistant` で詰め、モデルに「今は X ね」と渡していた。モデルは自分の過去発言として多人格ログを読むため混線。
  - 境界を stop シーケンスで物理停止しようとしたが、OpenAI の stop 最大4個制限で5人以上だと破綻（`llm_client.py:103`）。`sanitize_context()` の指名ブロック除去・System注入は応急処置だった。
- **根治策（v3）**:
  1. **1ペルソナ=1隔離コール**。他者発言は `assistant` ではなく **話者名つき transcript（user側 or 明示ラベル）** で渡し、`assistant` スロットは当該ペルソナ専用にする。←最重要
  2. 単一プロバイダー化で stop 4個制限から解放。出力契約「自分の1発言だけ／他人のセリフは書くな」＋ name-marker 後処理トリム。
  3. 可能なら構造化出力 `{speaker, content}`（JSON）で自由文の漏れを断つ。

### バグB: 全く発言しない人が出る（沈黙）
- **原因（v2）**: 発言順が指名駆動（`AgentScheduler.get_next_agent_id`）。司会/前任者の `【指名】` 次第で、指名されない人は永遠に出番なし。`silent_ones` 救済・Attention Logic（`app.py:342-348, 456-476`）は後追いの対症療法。
- **根治策（v3）**:
  1. **発言順は LLM でなく orchestrator（コード）が決定**。
  2. **ラウンドロビン＋公平スケジューラ**：発言回数を記録し最少の人を選ぶ。各フェーズで全員1回の**強制ロールコール**。
  3. 司会の `【指名】` は「提案」止まり。**コードが発言下限（floor）を保証**。

---

## 5. dynamicworkflows への引き継ぎポイント

- ペルソナ・レジストリ（データ駆動）と orchestrator（UI非依存ジェネレータ）が揃えば、
  「どのペルソナを・どの順で・どのフェーズで動かすか」を **ワークフロー定義（データ）** として外出しできる。
- v3 の固定討論（Opening→Divergence→Convergence→Conclusion）は、
  dynamicworkflows では「ワークフローテンプレートの1つ」に格下げできる設計にしておく。
