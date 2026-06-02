# AI Teams v3 — 内製（自前ホスト）LLM 設計図 / 2026-06

外部 API（Anthropic/OpenAI/Gemini, BYOK）に加えて、**自前ホストの LLM** を討論エンジンの選択肢に
する設計。最終的にこれが「面白いプロダクト」の核になる、という見立て。

## なぜ内製か（得られるもの）

- **従量コストがゼロ**になる → 「この討論を続ける」の**全文文脈が実質タダ**で使える（今は推奨=軽量にした
  最大の理由がコスト。自前なら全文が既定にできる）。多人格×多ラウンドの討論は呼び出しが多いので効く。
- **プライバシー/データ主権**：議題・資料・発言が外部 API に出ない（業務・機微な議題に向く）。
- **レート制限・他社の仕様変更に振り回されない**（GPT-5 の temperature 拒否のような罠が無い）。
- **共有が簡単**：自前モデルを所有者が立てれば、来訪者はキー不要で使える（BYOK の鍵配りが消える）。
- **将来の遊び**：人格ごとに別モデル／自前 fine-tune など、外部 API では難しい実験ができる。

## 既存設計がそのまま土台になる（重要）

この実装は**ほぼ追加コードなしで入る**。理由：
1. `core/llm_client.py` の `LLMClient` ABC で provider を抽象化済み（v2 を殺した「3社同時吸収」を避け、
   1セッション=1クライアントに統一した設計）。
2. **vLLM / Ollama などの自前推論サーバは OpenAI 互換 API＋ストリーミング**を出す。つまり既存の
   `OpenAIClient` に **base_url を渡すだけ**で自前モデルに向く（コード書き換え不要・移行は設定変更）。
3. SSE 配信・再接続（POST 経由）・履歴・編成・「続ける」など今セッションで作った土台は provider 非依存
   なので全部効く。

→ **「内製化」は新 provider を1枚クリーンに足すだけ**。v2 の轍（吸収しすぎ）は踏まない。

## 構成図

```
[ブラウザ] --HTTPS--> [cloudflared] --> [uvicorn(FastAPI) 既存]
                                            │  OpenAIClient(base_url=ローカル)
                                            ▼
                                   [推論サーバ: Ollama / vLLM]  ← OpenAI互換API(/v1, stream)
                                            │
                                       [自前 GPU / Mac(Metal) / GPU VPS]
```

## 推論サーバの選択（2026 時点）

| 用途 | 推奨 | 備考 |
|------|------|------|
| まず動かす・単一/少人数 | **Ollama**（`:11434/v1`） | セットアップ最速・モデル管理が楽・Metal(Mac) も可 |
| スループット・本番 | **vLLM**（`:8000/v1`） | 並列で Ollama の約2倍。移行は base_url 変更のみ |

いずれも **OpenAI 互換 + `stream=True`** 対応。本アプリの同時実行は低い（数人格を順に回す）ので
**Ollama で開始 → 必要なら vLLM** が現実的。

## モデル選択（2026・要再確認）

モデルは更新が速い（カットオフ後に大きく変動）。**実装時に最新を確認**したうえで：

- **本命（バランス）**：**Qwen3 系**（多言語＝日本語強め・Apache 2.0・量子化/サイズ豊富・ツール対応）。
  討論用途（日本語＋役割演技＋推論）に合い、量子化で1 GPU に載る。**14B〜32B（Q4/Q5 量子化）が日本語品質と
  VRAM のスイートスポット**の見込み。
- **軽量・実用**：**Gemma 4** 系（Apache 2.0・ローカル実用枠）。
- **最高峰の推論**：DeepSeek V4 / GLM-5.1 等は強力だが巨大でマルチ GPU 必須 → 個人ホストには過剰。
- **日本語特化 fine-tune**（Swallow/ELYZA 系等の最新）も候補。**council vs 単体の比較手法**
  （`COMPARISON_2026-06_council_vs_single.md`）で実測して選ぶ。

> 注: 役割演技（ペルソナ）と日本語の自然さは benchmark に出にくい。**実際に討論を1本回して質感を見る**のが
> 一番確実（mock→実モデルで `verbosity`/`temperature` も含め体感する）。

## ハードウェア / VRAM の目安

- 量子化 Q4 の VRAM ≒ パラメータ数 × 約 0.6GB（+ KV キャッシュ＝文脈長で増）。
  例: 14B Q4 ≒ 10–12GB、32B Q4 ≒ 20–24GB。**全文文脈（長い）を載せるなら KV キャッシュ分の余裕**を見る。
- 置き場所の選択肢：
  - **自前 GPU PC**（RTX 4090/5090 等）＋ cloudflared で uvicorn から叩く。
  - **Mac（Apple Silicon, Ollama+Metal）**：手軽。大きめモデルは要メモリ。
  - **GPU VPS**（時間課金）：常時稼働ならコスト試算（自前 GPU の方が長期は安い）。
- ⚠️ 現 ConoHa VPS（FX/MT5 用 Windows・GPU 無し）には推論を載せない。**推論サーバは別ホスト**にして、
  uvicorn から base_url で繋ぐ（同一ホストである必要はない）。

## レイテンシの現実（設計上の注意）

討論は **人格数 × ラウンド数 ぶん逐次生成**する（例 5人格×3フェーズ ≒ 15 生成）。ローカルは外部 API より
遅いことが多く、**1討論が数分**になり得る。対策：
- **ストリーミングでライブ感を維持**（既存。1発言ずつ流れるので待ちが苦にならない）。
- 速いモデル/量子化を選ぶ、`verbosity`=簡潔を既定に、人格数・ラウンドを絞れるUIは既にある。
- vLLM の連続バッチングで改善。

## Web 検索のギャップ

自前モデルには **web_search ネイティブツールが無い**（今 research は Anthropic 限定）。選択肢：
1. **ハイブリッド**：討論本体は自前、**調査役だけ Anthropic**（検索が必要な時だけ外部・最小課金）。
2. **自前検索**：SearXNG 等の検索 + ツール/function calling（Qwen3 等はツール対応）で researcher を自前化。
3. **検索なし**：自前選択時は research トグルを無効（現状の非 Anthropic と同じ honest 劣化）。
→ まずは 3（無効）か 1（ハイブリッド）。2 は Phase 3。

## 実装フェーズ

- **Phase 0（今・本書）**：設計図。
- **Phase 1（最小・数十行）**：
  - `OpenAIClient` に `base_url` を渡せるようにする（`OpenAI(api_key=, base_url=)`）。env
    `AI_TEAMS_LOCAL_BASE_URL` / `AI_TEAMS_LOCAL_MODEL` を追加し、provider `"local"` を `make_client` に足す。
  - ローカルで Ollama に Qwen3 を入れて起動 → provider=local で討論を1本回す（mock→実）。
  - 自前は**温度/最大トークンが普通に効く**ので GPT-5 系の温度回避は不要（per-persona temperature が活きる）。
  - 共有運用なら：所有者が推論サーバを立て、サーバ既定 provider=local にすれば**来訪者はキー不要**（BYOK 不要・無料）。
- **Phase 2**：モデル選定＋日本語品質チューニング（複数試して比較手法で実測）／ハード確定／量子化。
  全文文脈を既定化（コストゼロなので）。
- **Phase 3**：vLLM 化（必要なら）／推論サーバの常駐・監視／自前 Web 検索（SearXNG＋tool calling）。
- **Phase 4（任意・遊び）**：人格ごとに別モデル（多様性＝collapse 対策）／ペルソナ特化 fine-tune。

## 2026-06 後半: 情勢更新（カットオフ後の事実調査）＋Phase 1 実装＋クイックスタート

> 設計図初稿（本書前半）は Jan 2026 知識ベースで「自前はOpus級に届かない／検索が無い」と書いたが、
> **2026-06 時点の事実調査で2点が古かった**ので訂正する（出典は git コミット説明/会話ログ）。

### 情勢の訂正（実測ベース）
- **開源モデルはOpus級に肉薄**：GLM-5.1（MIT・754B MoE）がGPT-5.4/Opus 4.6/Gemini 3.1 ProをSWE-Bench Proで同時に上回った初の開源モデル。DeepSeek V4 Pro はSWE-Bench Verified 80.6%でクローズド同水準。**Opus 4.8 は依然 #1** だが差は僅か。日本語も Qwen3.5-397B が日本語ベンチ初の0.80超え。
- **検索は解決済み**：OpenRouter の **web_search サーバツール**（`tools:[{type:"openrouter:web_search"}]`・$0.005/検索）で**どのモデルでも検索可**。Ollama も web_search API（ただし Ollama クラウド転送・要アカウント）。完全プライベートは SearXNG 自前。
- **コストが自前の動機を消した**：開源フロンティアAPIが激安（DeepSeek V4 Flash $0.14/$0.28 per M）。月90討論でも **$1-17/月**（Opus直接は ~$300/月）。**「コストゼロのために自前ホスト」はもう不要**＝自前の価値はコストでなく**所有・プライバシー・オフライン・特化**。
- **「育てる（蒸留）」**：DeepSeek-R1蒸留（32Bがo1-miniを超え）が示す通り**狙い撃ちタスクなら小型が教師に肉薄**。データ生成$50-300＋LoRA$10で可。ただし**教師にAnthropicを使うのはToS違反リスク**（競合モデル訓練禁止＋能動検出）→ **教師は開源フロンティア（GLM/Qwen/DeepSeek・寛容ライセンス）にする**。

### 採用方針：**シナリオA（開源フロンティアAPIを base_url で叩く）** を当面のベストとする
個人運用で最短・最安。蒸留や高価GPUは不要。Phase 1 のコードで即動く。

### Phase 1 実装済み（2026-06-02 後半）
- `OpenAIClient(base_url=, search_mode=)`：base_url で OpenAI互換（Ollama/vLLM/DeepSeek/GLM/Qwen/OpenRouter）へ。
  **local モードは `max_tokens`+`temperature`**（`max_completion_tokens`/`reasoning_effort` を使わない＝per-persona温度が効く）。
- `provider="local"`（`make_client`/`normalize_provider`、"ollama"等も寄せる）。鍵不要（`AI_TEAMS_LOCAL_API_KEY`）。
- **Web検索**：`web_research` が `search_mode="openrouter"` のとき OpenRouter web_search を直HTTPで叩き、本文＋`url_citation`出典を返す。`research_providers()`＝anthropic＋（検索設定済みの)local。`build_council` が local-with-search で research を許可。
- **`AI_TEAMS_FORCE_LOCAL=1`**：来訪者の provider 指定に関わらず**全実LLMを内製に固定**（フロント大改修不要・キー不要で実LLM可）。フロントは `/health` の `force_local`/`local_search` を見て実LLM/検索トグルを出し分け＋「内製/オープンで討論」注記。
- テスト：`test_local_provider`（normalize/make_client/_params/検索/research_providers/force_local/llm_status・全pass）。

### クイックスタート（シナリオA：OpenRouterで全開源モデル＋検索）
VPS/ローカルの `.env` に追記して uvicorn 再起動（**8000をListenするPIDをkillしてから** `Start-ScheduledTask`）：
```
AI_TEAMS_LOCAL_BASE_URL=https://openrouter.ai/api/v1
AI_TEAMS_LOCAL_MODEL=deepseek/deepseek-v4-pro   # or z-ai/glm-5.1, qwen/qwen3.5-plus
AI_TEAMS_LOCAL_API_KEY=<OpenRouterのAPIキー>
AI_TEAMS_LOCAL_SEARCH=openrouter                # 検索を使うとき
AI_TEAMS_FORCE_LOCAL=1                           # 全部を内製に固定（個人運用）
```
→ 実LLMトグルON＋Web検索ONで、DeepSeek/GLM/Qwen が検索付きで討論する。OpenRouter キーは [openrouter.ai/keys](https://openrouter.ai/keys)。
**完全プライベートにしたい**なら base_url を自前 vLLM/Ollama＋検索を SearXNG に差し替え（Phase 3）。
**育てる（蒸留）**に進むなら、A で集めた討論ログを開源教師で生成→Qwen3.5中型をLoRA（Phase 4）。

## リスク / 留意

- **v2 の轍**：provider を増やすほど不安定化した。**1枚クリーンに足す**（OpenAI 互換に寄せる）こと。
- **逐次レイテンシ**：上記。期待値設定＋ストリーミングで吸収。
- **日本語/演技品質**：開いてみないと分からない。**実測（討論1本）で判断**。
- **常駐コスト**：GPU を常時起動するなら電気代/VPS 課金。使う時だけ起動でも可（起動待ちは出る）。

## まとめ（一言）

今セッションで作った **provider 抽象・OpenAI 互換 BYOK・SSE/再接続・履歴/続ける** が、そのまま内製 LLM の
土台になっている。内製化は **「OpenAIClient に base_url を足し、Ollama に Qwen3 を載せ、provider=local を
選ぶ」** だけで動き始める。あとはモデル選定とハード、そして全文文脈をタダで回す——という順。

---
**作成日**: 2026-06-02 ／ 関連: `core/llm_client.py`（LLMClient ABC / OpenAIClient）, `DEPLOY_2026-06.md`（BYOK・公開構成）,
`COMPARISON_2026-06_council_vs_single.md`（モデル比較手法）。情勢（モデル/サーバ）は実装時に再確認すること。
