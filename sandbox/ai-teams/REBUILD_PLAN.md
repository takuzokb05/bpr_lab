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
  - ただし `LLMClient` は差し替え可能なIFを維持し、「特定ペルソナだけ別モデル」を後から任意でONできる余地は残す（標準は使わない）。

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

- [ ] **Phase 0**: core/ ディレクトリ作成・既存資産を archive と整理
- [ ] **Phase 1**: `core/llm_client.py` を単一プロバイダー（Claude）に縮小・安定化
- [ ] **Phase 2**: `core/personas.py` + `personas/*.yaml` のレジストリ実装
- [ ] **Phase 3**: `core/orchestrator.py` を UI 非依存のジェネレータとして実装（ターン/フェーズ/終了条件）
- [ ] **Phase 4**: `app.py` を薄い UI に作り直し（途中経過のストリーム表示を最優先で検証）
- [ ] **Phase 5**: 経営者・哲学者ペルソナを YAML で追加
- [ ] **Phase 6**: 永続化（SQLite）を「あれば便利」レベルで戻す（v2のDB資産を流用可）

---

## 5. dynamicworkflows への引き継ぎポイント

- ペルソナ・レジストリ（データ駆動）と orchestrator（UI非依存ジェネレータ）が揃えば、
  「どのペルソナを・どの順で・どのフェーズで動かすか」を **ワークフロー定義（データ）** として外出しできる。
- v3 の固定討論（Opening→Divergence→Convergence→Conclusion）は、
  dynamicworkflows では「ワークフローテンプレートの1つ」に格下げできる設計にしておく。
