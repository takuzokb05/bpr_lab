# api/ — AI Teams v3 HTTP API（FastAPI + SSE）

core エンジン（UI 非依存）を HTTP で公開する薄い層。`council.run()` の `yield` を
Server-Sent Events でそのまま流すので、フロントは**討論の途中経過を逐次受信**できる
（v2 の「完了しないと何も見えない」を構造的に解消）。

## 構成

| ファイル | 役割 |
|---|---|
| `service.py` | ドメインロジック（**FastAPI 非依存**）。Council 組み立て・SSE 文字列生成・ペルソナ公開表現 |
| `main.py` | FastAPI ルーティングのみ（`/health` `/personas` `/sessions`） |

`service.py` に Web フレームワークを入れないので、SSE の挙動は API サーバを起動せず
`tests/run_tests.py` でユニットテストできる。

## エンドポイント

- `GET /health` → `{"status":"ok"}`
- `GET /personas` → ペルソナ一覧（`system_prompt` は出さない。`accent`/`monogram` 付き）
- `POST /sessions` → SSE ストリーム。body:
  ```json
  { "topic": "議題", "persona_ids": ["moderator","logic","idea","empathy","chair"],
    "rounds_per_phase": 1, "mock": false }
  ```
  イベント列: `start` → `turn`×N → `done`（途中失敗時は `error`）。

## 起動

```bash
pip install -r ../requirements-v3.txt
# 本番 LLM を使う場合のみ:
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn api.main:app --reload --port 8000   # sandbox/ai-teams で実行
```

`ANTHROPIC_API_KEY` 未設定、または `"mock": true` のときは MockLLMClient で動く
（キー無しでフロント開発・疎通確認ができる）。

## 動作確認（モック）

```bash
curl -N -X POST localhost:8000/sessions \
  -H 'Content-Type: application/json' \
  -d '{"topic":"空き家活用","persona_ids":["moderator","logic","idea","empathy","chair"],"mock":true}'
```
