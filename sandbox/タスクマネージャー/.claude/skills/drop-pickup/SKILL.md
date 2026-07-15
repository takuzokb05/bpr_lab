---
name: drop-pickup
description: "スマホから投げられたリンク（Gmail自分宛て[drop]メール・Slack #dropチャンネル）を回収し、library/inbox/drop.md に追記して curate に渡す。curate 開始前の前処理。"
user_invocable: true
allowed-tools: Read, Edit, Write, Grep, Bash, mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_thread, mcp__claude_ai_Gmail__list_labels, mcp__claude_ai_Gmail__create_label, mcp__claude_ai_Gmail__label_thread, mcp__claude_ai_Slack__slack_search_channels, mcp__claude_ai_Slack__slack_read_channel
---

# /drop-pickup — スマホ投げ口の回収スキル

## 概要

外出先のスマホから「気になったリンク」を投げておくと、PC側セッションが自動回収して
`library/inbox/drop.md` に追記するスキル。curate の前処理として実行する。

**投げ口は2系統:**
- **Gmail** … 自分宛てに `[drop]` を件名に含むメールを送る（本文にURLを貼る）。X共有シートからの最短動線（後述）。
- **Slack** … `#drop` チャンネルにリンクを貼る（チャンネルが存在する場合のみ。無ければスキップ）。

回収したURLを drop.md に日付付きで追記し、**最後に「/curate を実行してください」で終了する**
（このスキルは自動では curate を起動しない）。

## 前提: コネクタ接続の確認

このスキルは claude.ai の MCP コネクタ（Gmail / Slack）を使う。以下のいずれかの場合は
**エラーにせず「コネクタ未接続」と報告して終了**する:

- MCP ツール（`mcp__claude_ai_Gmail__*` 等）がそもそもロードできない（headless / CLI セッション等）
- ツール呼び出しが `requires re-authorization`（トークン期限切れ）を返す
- ツール呼び出しが認証エラー・権限エラーを返す

報告例: 「Gmailコネクタがトークン期限切れ（要再認証）のため回収をスキップしました。claude.ai の
コネクタ設定から再認証後、再度 /drop-pickup を実行してください。」

Gmail が使えず Slack だけ使える（あるいはその逆）場合は、**使える方だけ処理して続行**する。

---

## 処理フロー

### Phase 0: drop.md の既存URLを読み込む（重複排除の準備）

1. `library/inbox/drop.md` を Read する
2. 既に貼られているURL（テンプレのHTMLコメント内の例URLは除く）を集合として保持する。
   後段の追記で、この集合に含まれるURLは重複としてスキップする。

---

### Phase 1: Gmail 回収

1. `mcp__claude_ai_Gmail__search_threads` を `query: "subject:[drop] newer_than:30d"` で呼ぶ。
   - `requires re-authorization` / 認証エラーが返ったら Gmail はスキップし Phase 2 へ（コネクタ未接続扱い）。
   - 結果0件なら「Gmail: 新規なし」として Phase 2 へ（正常）。
2. `drop-processed` ラベルのIDを確認する:
   - `mcp__claude_ai_Gmail__list_labels` を呼び、`drop-processed` の label ID を取得。
   - 無ければ `mcp__claude_ai_Gmail__create_label` で `displayName: "drop-processed"` を作成し、返ったIDを使う。
3. 各スレッドについて:
   - **既に `drop-processed` ラベルが付いているスレッドはスキップ**（処理済み）。search クエリに
     `-label:<drop-processed-id>` を足して最初から除外してもよい。
   - `mcp__claude_ai_Gmail__get_thread` で本文（plaintext_body / html_body）を取得する
     （search_threads は本文を返さないため get_thread が必須）。
   - 本文から `https?://` で始まるURLを全て抽出する。
   - URL以外に短いメモ（コメント）が本文にあれば、そのURLの併記メモとして拾う（1行、長すぎる場合は先頭80字）。
   - 抽出したURL群を「今回の回収リスト」に追加する（送信日時をメモに含めてもよい）。
4. 処理し終えたスレッドに `mcp__claude_ai_Gmail__label_thread` で `drop-processed` ラベルを付与する
   （次回以降の重複回収を防ぐ）。
   - **URL抽出とラベル付与は必ずセットで**。ラベル付与に失敗したスレッドは今回の回収リストからも外し、
     次回に回す（「回収したのにラベルが付かず、drop.md には入らない」取りこぼしを防ぐ）。

---

### Phase 2: Slack 回収（#drop チャンネルがある場合のみ）

1. `mcp__claude_ai_Slack__slack_search_channels` を `query: "drop"` で呼ぶ。
   - 認証エラー/ツール未ロードなら Slack はスキップ（コネクタ未接続扱い）。
   - `#drop`（または drop を含むチャンネル）が**見つからなければスキップ**（作成はしない）。
2. 見つかったら `mcp__claude_ai_Slack__slack_read_channel` で直近メッセージ（30日分/上限20件程度）を読む。
3. 各メッセージ本文から `https?://` URLを抽出し、短いメモがあれば併記メモとして拾う。
4. Slack には処理済みラベルの仕組みが無いため、**処理済み管理は「drop.md との重複排除」で代替**する
   （Phase 0 の既存URL集合 + drop.md への追記済みURLと照合し、重複は追記しない）。

---

### Phase 3: drop.md へ追記

1. Phase 1・2 で回収したURLから、Phase 0 の既存URL集合に含まれるものを除いた**新規URLのみ**を対象にする。
   同一回収内での重複も1件にまとめる。
2. 新規URLが0件なら追記せず、「回収0件」としてサマリーへ。
3. 新規URLがあれば、drop.md の**末尾**に以下フォーマットで追記する（Edit で末尾に追加。既存の
   ヘッダー・HTMLコメント・過去セクションは絶対に消さない）:

   ```markdown

   ## YYYY-MM-DD 回収（drop-pickup）
   https://example.com/foo
     → メモ本文（あれば。無ければこの行は省略）
   https://x.com/user/status/123456789
     → [Gmail 2026-07-07 / Slack #drop] などソースを併記してもよい
   ```

   - 日付は実行日（今日）。
   - URLは1行1つ。メモがある場合のみ次行にインデントして `→ ` で併記する。
   - **x.com / twitter.com のリンクはそのまま貼る**。内容取得は後段の curate（adhx /
     collect-x-articles 相当）が行う前提なので、ここでは展開しない。

---

### Phase 4: 終了メッセージ

追記完了後、以下を出して終了する（**自動で curate は起動しない**）:

```
=== drop-pickup 完了 ===
Gmail: 回収 N件 / スキップ（処理済・重複）M件 / コネクタ状態: OK|未接続
Slack: 回収 N件 / チャンネル: あり|なし / コネクタ状態: OK|未接続
drop.md 追記: 新規 N件（重複除外 M件）

→ 続けて /curate を実行してください（回収分を articles/ に反映します）。
```

---

## スマホ側の操作手順（ユーザー向け・最短動線）

### Gmail 経由（推奨・どのアプリからでも使える）
1. X / ブラウザ / 記事アプリで「共有」→「Gmail」を選ぶ。
2. 宛先 = 自分のアドレス、**件名の先頭に `[drop]`** を入れる（本文は共有で自動挿入されるURLでOK）。
3. 送信。次に PC で `/drop-pickup`（または `/curate`）を実行すれば回収される。
   - ヒント: Gmail アプリで宛先・件名 `[drop]` を固定した下書きテンプレを1つ作っておくと、
     以降は本文にURLを貼って送るだけになる。

### Slack 経由（#drop チャンネルを作った場合）
1. 共有シート →「Slack」→ `#drop` チャンネルを選んで送信、またはチャンネルにURLを直接貼る。
2. PC で `/drop-pickup` 実行時に回収される。
   - ※現状 `#drop` チャンネルは未作成。使う場合は claude.ai / Slack 側で作成が必要。

---

## Gotchas

- **search_threads は本文を返さない**。URL抽出には必ず `get_thread` で本文を取得すること。
- **Gmail の重複防止はラベルで、Slack の重複防止は drop.md との照合で**行う（Slackにはラベルが無い）。
- ラベル付与に失敗したスレッドはその回の回収から外す（取りこぼしより二重回収防止を優先しない。
  「回収したがラベルが付かない」中途半端状態を作らない）。
- コネクタが片方だけ死んでいても、生きている方だけで続行する。両方死んでいたら「コネクタ未接続」で終了。
- drop.md のヘッダー・HTMLコメント・過去の回収セクションは消さない（追記のみ）。処理済みURLの
  除去は curate 側の責務。
- `[drop]` 以外の件名のメールは対象外。誤って自分の通常メールを巻き込まないよう、必ず
  `subject:[drop]` で絞る。
- x.com リンクはここで展開しない（curate の adhx / collect-x-articles が内容取得する前提）。
