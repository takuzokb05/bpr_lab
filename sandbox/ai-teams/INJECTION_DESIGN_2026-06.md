# 追い質問の割り込み — 設計 v2（2026-06・レビュー反映）

MVP必須機能の本丸。議論の進行中に人間が「追い質問」を差し込み、パネリストに
深掘りさせる。`FEATURE_REVIEW_2026-06.md` F節で MVP 入りが確定。

> **v2 改訂**: 設計レビューで「実装の手間よりUX」を再確認し、2つの上位決定を追加した
> 結果、**注入単体**から**セッション/トランスポート層の再設計**にスコープが広がった
> （実装量は当初比 約2〜3倍）。本書はその確定版。

## 決定（ユーザー確定）

1. **アーキ = 案A：ステートフル・セッション**（最もUXが高い方）。
2. **応答ルーティング = 司会が再提示 → 次ラウンドで全員が織り込む**。
3. **drain 粒度 = ターン境界**（各発言の直後に確認）。
4. **🆕 トークンストリーミングを先に入れる**（UX最大のレバー。「生きた会議」感）。
5. **🆕 軽い再接続 resume を入れる**（案Aの弱点「切断でセッション消滅」を緩和）。

レビューで挙げた軽量UX修正 B/E/F も本設計に織り込み済み（後述）。

## 大前提（唯一の制約）と、再設計の理由

SSE は **サーバー→クライアントの一方向**。進行中の議論への割り込みには
**クライアント→サーバーの裏チャネル**が要る（→ 別エンドポイント＋キュー）。

決定4・5により、さらに次が必要になる:

- **再接続 resume**: 討論を **HTTP接続から切り離してバックグラウンドで実行**し、
  セッションが **イベントを溜める**。接続が切れても進行は続き、再接続時に
  「溜まったぶんを再生 → ライブ継続」できる。
- **ストリーミング**: 1発言を「`turn_start` → `delta`* → `turn_end`」の
  **イベント列**に変える。

この2つは同じ「セッション内イベントバッファ＋ファンアウト」機構で噛み合う。

## アーキ全体像

```
POST /sessions ──▶ Session生成 + プロデューサ起動(別スレッド) ──▶ SSEで tail
                      │
   council.run(topic, pull=…, emit=…)  ← バックグラウンドで完走まで実行
                      │  各 turn_start/delta/turn_end を
                      ▼
            Session.events: list[Event]   (append-only, 各 event に連番 seq)
                      ▲                         │ notify
   POST /sessions/{id}/messages              読み手(複数可)が cursor から tail
        → inbox.put(HumanMessage)         GET /sessions/{id}/stream?cursor=N で再接続
```

- FastAPI は同期ジェネレータ/スレッドを **スレッドプール** で回すので、`queue.Queue`
  と `threading.Condition` でスレッド間連携できる（**asyncio 全面書き換えは不要**）。
- プロデューサは **接続が無くても完走**（resume のため）。誰も見ていない間も LLM が
  進む点は「軽い」MVP の割り切り。将来 pause-on-no-client を足せる。

## データモデル（メモリ常駐・単一ワーカー前提）

```python
@dataclass
class HumanMessage:
    kind: str = "followup"   # 将来: "intervention" | "rewind" を同機構で追加
    text: str = ""
    target: str | None = None   # 将来のペルソナ指名。MVP未使用

@dataclass
class Session:
    id: str
    inbox: "queue.Queue[HumanMessage]"
    events: list[dict]                 # 連番 seq 付きイベントログ（再生元）
    cond: "threading.Condition"        # 新イベントを読み手に通知
    status: str = "running"            # running | done | error
    # producer スレッド参照、created_at など

SESSIONS: dict[str, Session] = {}
```

- 終了後も **短時間 TTL** で残し、遅れた再接続が最終 transcript を再生/エクスポート
  できるようにする。その後 GC（件数上限＋古い順破棄）。

## イベント・プロトコル（SSE）

各イベントに単調増加 `seq` を載せる（再接続カーソル用）。

| event | data |
|---|---|
| `start` | `{topic, session_id}` |
| `turn_start` | `{turn_id, speaker_id, speaker_name, phase, round}` |
| `delta` | `{turn_id, text}` （差分トークン） |
| `turn_end` | `{turn_id}` （発言確定） |
| `done` | `{}` |
| `error` | `{message}` |

- 人間ターン／司会の再提示も、同じ `turn_start`→`delta`→`turn_end`（`speaker_id` が
  `"human"` ／ 司会id、`phase` が `"human"` ／ `"followup"`）。新イベント型は増やさない。

## core 側：ストリーミング＋注入

### llm_client
- `generate_stream(*, system, messages, model, temperature) -> Iterator[str]` を追加。
  Anthropic は `messages.stream()` のテキスト差分を yield。
  `MockLLMClient` は決定的に数チャンクに割って yield（テスト可能）。
- 既存 `generate()` は残す（非ストリーム経路・後方互換）。

### orchestrator: `run(topic, *, pull=None, emit=None)`
- `emit: Callable[[dict], None] | None` … `turn_start` と `delta` を流す。
- `pull: Callable[[], list[HumanMessage]] | None` … 未処理の人間メッセージを drain。
- 各発言 `_speak` は:
  1. `turn_id` を採番し `emit(turn_start…)`。
  2. `generate_stream` を消費して `emit(delta…)` しつつ全文を蓄積。
  3. 完成した `Turn`（`turn_id` 付き）を **yield**（=従来の契約を維持）。呼び出し側が
     `turn_end` を出し、transcript に積む。
- **後方互換**: `emit=None` なら `generate()` で一括生成し、従来どおり `Turn` だけを
  yield ＝ **既存テストは無改修で通る**。
- 注入（決定2・3）: 各 `Turn` を yield した直後に `pull()`。来ていたら順に:
  - **人間ターン**を transcript に積み emit（`build_context` は他者発言を `【名前】…`
    で全員に渡すので **改修不要**で「【あなた】追い質問…」が文脈に入る）。
  - **司会の再提示**（`phase="followup"`、ストリーム発言）。司会不在ならスキップ。
  - **追い質問ラウンド**を挿入。本編ローテーションを乱さないよう **順序スナップショット
    固定**で1周（修正E）。directive に `【追い質問対応】…まずこれに答えてから…` を前置き。
    Red Team 指名者には反対役の特命も従来どおり付与。
  - 復帰して元プラン継続。複数同時は **1ラウンドに束ねて**処理（修正E）。
- 割り込みを拾うのは本編フェーズのみ（opening 前・summary/synthesis 中は拾わない）。

## API 側
- `POST /sessions`: Session 生成 → プロデューサ起動 → cursor 0 から tail する SSE を返す。
  `start` に `session_id`。
- `GET /sessions/{id}/stream?cursor=N`: **再接続**。`events[N:]` を再生 → ライブ tail。
  未知 id は 404。
- `POST /sessions/{id}/messages`: `{kind,text,target?}` → `inbox.put` → 202。未知/終了は 404。
- プロデューサ終了で `status` 更新、TTL 後に `SESSIONS` から破棄（リークしない）。

## web 側
- `lib/sse.ts`: `turn_start/delta/turn_end` をパース。`turn_id` ごとに部分テキストを
  保持し `delta` で追記 → **タイピング表示**。`start` で `sessionId` と `seq` 追跡開始。
- **再接続**: `done` 前にストリームが切れたら `GET …/stream?cursor=lastSeq+1` で
  自動再接続し、バックログ＋ライブをマージ。
- **楽観的エコー（修正B）**: 追い質問の送信時に、クライアント生成idで即「あなた」吹き出し
  ＋「次の発言から反映します」を表示。サーバーの human ターン到着時に重複解消。
- **入力欄**: `status==="running"` かつ本編フェーズの間だけ有効。summary/synthesis 突入で
  無効化＋理由表示（修正F）。
- 案A はストリームを開いたままなので通常時 abort 不要（切断時のみ再接続）。
- Next.js rewrite が `/api/sessions/:id/stream` と `/messages` を転送するか確認。

## テスト計画（mock で決定的に）
- llm: `generate_stream` の連結が全文と一致。
- orchestrator: `emit` 捕捉で `turn_start→delta*→turn_end` の順序／delta連結＝`Turn.content`
  ／`turn_id` 単調増加。`pull` 注入がストリーム経路でも動く。`emit=None` で従来と一致。
- service: `events`/`seq` のバッファ、cursor 再生（バックログ→tail）、`inbox` 取り出し、
  終了後の TTL 破棄。
- 既存テスト（ターン数・分離・モデル上書き・Red Team・summary）が無改修で通ること。

## 実装ステップ（小さく刻む・ストリーミング先行）
1. **core ストリーミング**: `generate_stream` ＋ `run(emit=…)` ＋ テスト（既存維持）。
2. **API トランスポート**: バックグラウンド実行＋`events/seq`バッファ＋tail SSE
   ＋`GET …/stream`再接続 ＋ テスト。
3. **core 注入**: `run(pull=…)` ＋ 追い質問ラウンド（順序固定・束ね）＋ テスト。
4. **API メッセージ**: `POST …/messages`、`start` に session_id。
5. **web**: delta タイピング描画／再接続／楽観的エコー／入力欄（フェーズ制御）。
6. 実起動で疎通（ストリーム表示・割り込み注入・接続断→再接続）。

## 既知の限界 / 将来拡張
- 単一ワーカー前提（マルチワーカーは共有ストア＝Phase 6 永続化と一緒に）。
- 誰も見ていない間も進行＝LLM コストが出る（pause-on-no-client は将来）。
- `target`（指名）・`intervention`（司会への指示）・`rewind`（巻き戻し）は **同じ
  inbox / human ターン機構** に `kind` 追加で後付け可能＝「人間操作を厚く」を1本で拡張。
- セッション TTL/上限は MVP で簡易（件数上限＋古い順破棄）。
