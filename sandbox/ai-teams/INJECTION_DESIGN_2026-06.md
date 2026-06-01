# 追い質問の割り込み — 設計（2026-06）

MVP必須機能の本丸。議論の進行中に人間が「追い質問」を差し込み、パネリストに
深掘りさせる。`FEATURE_REVIEW_2026-06.md` のF節で MVP 入りが確定した機能。

## 決定（ユーザー確定）

- **アーキ = 案A：ステートフル・セッション＋注入キュー**（実装の手間より最もUXが高い方）。
- **応答ルーティング = 司会が再提示 → 次ラウンドで全員が織り込む**。
- drain 粒度 = **ターン境界**（各発言の直後に確認）。フェーズ境界より反応が速く、
  「割り込んだ感」が出る＝最高UX方針に合わせる。半同期だが体感はほぼ即時。

## 大前提（唯一の制約）

SSE は **サーバー→クライアントの一方向**。進行中の議論に届く追い質問を扱うには、
ストリーム実行中の **クライアント→サーバーの裏チャネル** が要る。案Aはこれを
「メモリ上のセッション＋別エンドポイント＋スレッドセーフなキュー」で作る。

FastAPI は同期ジェネレータの `StreamingResponse` を **スレッドプール** で回す。
よって `queue.Queue` をそのまま裏チャネルにできる（**asyncio 書き換え不要**）。
`POST /sessions/{id}/messages` ハンドラがキューに積み、ストリーム側のジェネレータが
ターン境界で drain する。

## データモデル（メモリ常駐）

```python
# api/service.py（プロセス内・1ワーカー前提のMVP）
@dataclass
class HumanMessage:
    kind: str          # "followup" | "intervention"（当面 followup のみ使用）
    text: str
    target: str | None = None   # 将来のペルソナ指名用。MVPでは未使用

@dataclass
class Session:
    id: str
    inbox: "queue.Queue[HumanMessage]"

SESSIONS: dict[str, Session] = {}   # id -> Session
```

- セッションは `POST /sessions` で生成・登録、ストリーム終了（done/error/切断）で
  `finally` にて破棄。リークしないことをテストで担保。
- MVPは **単一ワーカー** 前提（uvicorn 1プロセス）。複数ワーカーに分けるなら
  共有ストア（Redis等）が要るが、それは Phase 6 の永続化と一緒に検討。

## core 側：`Council.run` を注入可能にする

シグネチャ拡張（後方互換・既存呼び出しはそのまま動く）:

```python
def run(self, topic, *, pull=None) -> Iterator[Turn]:
    # pull: Callable[[], list[HumanMessage]] | None
    #   呼ぶと「未処理の人間メッセージを全部取り出してキューを空にする」非ブロッキング関数
```

進行ロジックの変更点:

1. フェーズ・ラウンドの二重ループは現状維持。**各パネリスト発言を yield した直後**に
   `pull()` を呼ぶ（pull が None なら何もしない＝現状と完全一致）。
2. 取り出した各メッセージにつき、次を transcript に積み yield する:
   - **人間ターン** `Turn(speaker_id="human", speaker_name="あなた", phase="human")`。
     `build_context` は active 以外の発言を `【名前】…` の user 行として全員に渡すので、
     **改修不要**で全パネリストの文脈に「【あなた】追い質問…」が入る。
   - **司会の再提示** `phase="followup"`：司会が追い質問を論点として言い直す
     （司会が居なければスキップ）。
3. 直後に **追い質問ラウンド**（ラウンドロビン1周）を挿入。この周回の phase_directive に
   `【追い質問対応】人間から問いが入りました: "…"。各自まずこれに正面から答えてから…`
   を前置きし、全員が織り込む。Red Team 指名者にはこれまで通り反対役の特命も乗る。
4. 追い質問ラウンドが終わったら、**元のフェーズ・プランの続き**へ復帰。
5. 複数同時に積まれていたら、古い順に1件ずつ 2〜4 を繰り返す。

> 設計判断: 追い質問は「割り込みの1ラウンド」を挿入する方式（元の進行は失わない）。
> opening 前 / synthesis・summary 中の割り込みは MVP では拾わない（本編フェーズのみ）。

## API 側

- `POST /sessions`：Session を生成して `SESSIONS` に登録し、その `inbox.get_nowait`
  ベースの `pull` を `run(topic, pull=...)` に渡す。`start` イベントに **`session_id`** を
  載せる（`{"topic":…, "session_id":…}`）。クライアントは start から id を得る。
  `finally` で `SESSIONS.pop(id, None)`。
- `POST /sessions/{id}/messages`：body `{kind, text, target?}`。該当 Session の
  `inbox.put(HumanMessage(...))` して `202 Accepted`。未知/終了済み id は `404`。
- `human` / `followup` フェーズも既存の `turn` イベントとして流れる（新イベント型は不要）。

## web 側

- `lib/sse.ts`：`start` イベントから `sessionId` を取り出し `onEvent({type:"start", sessionId})`。
  案Aはストリームを開いたままにするので **abort は不要**。
- `lib/sse.ts`：`sendFollowup(sessionId, text)` を追加 → `POST /api/sessions/{id}/messages`。
- Next.js の rewrite が `/api/sessions/:id/messages` を API へ転送するよう確認（`next.config`）。
- UI：タイムライン下部に追い質問の入力欄。`status==="running"` の間だけ有効。
  送信後、注入された「あなた」「司会(followup)」ターンが同じストリームで流れて表示される。
  `human` フェーズはタイムライン上で人間の発言として強調（右寄せ等）。

## テスト計画（mock で決定的に）

- core: `pull` が1回だけメッセージを返すフェイクを渡して `run()` を回し、
  (a) `human` ターンが出る (b) `followup`（司会）ターンが続く
  (c) その後のパネリスト発言の messages に追い質問テキストが含まれる
  (d) pull=None なら従来と完全一致（ターン数不変）。
- service: Session 登録→pull が積んだ HumanMessage を取り出す→ストリーム終了で
  `SESSIONS` から消える（リークしない）。
- 既存のターン数テスト等が壊れないこと（pull 未指定の経路は不変）。

## 実装ステップ（小さく刻む）

1. core: `run(pull=...)` ＋ 追い質問ラウンド挿入 ＋ core テスト。
2. api: `Session`/`SESSIONS`、`POST /sessions/{id}/messages`、`start` に session_id、
   `finally` で破棄 ＋ service テスト。
3. web: sse.ts に sessionId 取得と sendFollowup、入力欄UI、human ターン表示。
4. 実起動で疎通（ストリーム中に追い質問POST→注入ターンが流れる）。

## 既知の限界 / 将来拡張

- 単一ワーカー前提（マルチワーカーは共有ストアが要る → Phase 6）。
- `target`（ペルソナ指名）・`intervention`（司会への指示）・巻き戻しは **同じキュー/同じ
  human ターン機構** に後付けできる設計。`kind` を増やすだけで「人間操作を厚く」を拡張可能。
- セッションの TTL/上限は未実装（メモリ保護が要るなら後で max件数＋古いものから破棄）。
