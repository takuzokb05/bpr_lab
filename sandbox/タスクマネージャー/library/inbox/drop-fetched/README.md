# drop-fetched — adhx 取得済み JSON の置き場

`drop.md` に貼られた X 投稿を **GitHub Actions（`.github/workflows/drop-fetch.yml`）** が
adhx API で取得し、`{statusId}.json`（adhx レスポンスそのまま）としてここに保存する。

- 生成元: `sandbox/タスクマネージャー/tools/drop_fetch.py`（Actions が2時間ごとに実行）
- 消費側: `/curate` の Phase 1 が、X URL の内容取得時にまずこのディレクトリの
  `{statusId}.json` を読む（あればネット取得せずそれを使う）。
- クラウドセッションは egress プロキシで adhx が 403 になるため、この事前取得により
  クラウドでも drop の記事化が完結する。

処理済み JSON は curate が `archive/` に退避する（任意）。手動で消してもよい（再実行時に再取得される）。
