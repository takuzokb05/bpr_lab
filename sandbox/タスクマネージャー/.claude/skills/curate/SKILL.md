---
name: curate
description: "inbox/に溜まった収集記事・ユーザーのdropリンクを精査し、articles/とcatalogに反映するキュレーションスキル。drop.mdのURLを最優先処理。"
user_invocable: true
allowed-tools: Read, Edit, Write, Glob, Grep, Bash, WebFetch, WebSearch
---

# /curate — キュレーションスキル

## 概要

`library/inbox/` に溜まった生データ（ユーザー手動投入・X収集・Web収集）を精査し、
`library/articles/` に記事ファイルとして保存、該当の `catalog*.md` を更新する。

## ディレクトリ構造

```
library/
├── inbox/
│   ├── drop.md          ← ユーザーが気になったリンクを貼る場所（最優先）
│   ├── x/               ← SocialData API収集JSON
│   │   └── archive/     ← 処理済みJSON移動先
│   ├── web/             ← WebSearch収集記事
│   └── PROPOSALS.md     ← 反映提案
├── articles/            ← 精査済み記事の最終保存先
├── catalog.md           ← claude-code / claude-ecosystem 蔵書目録
├── catalog-trading.md   ← ai-trading 蔵書目録
└── catalog-news.md      ← ai-news 蔵書目録
```

## 処理フロー

**必ず Phase 1 → 2 → 3 → 4 の順に実行する。** 各フェーズで処理対象がなければスキップ。

---

### Phase 1: drop.md 処理（最優先）

1. `library/inbox/drop.md` を Read で読み込む
2. テンプレート部分（ヘッダー・コメント）以外にURLが貼られているか確認
3. URLごとに以下を実行:
   - **x.com / twitter.com のリンク**: adhx スキル相当の処理で投稿内容を取得
     - `GET https://adhx.com/api/share/tweet/{username}/{statusId}` を WebFetch で呼ぶ
     - `article` フィールドがあれば長文記事として扱う
   - **それ以外のURL**: WebFetch で内容を取得
4. 取得した内容を要約し、`library/articles/` に記事ファイルを生成（フォーマットは後述）
5. 該当の `catalog*.md` に追加（更新ルールは後述）
6. **処理済みURLを drop.md から除去**する。テンプレート部分は残す:
   ```markdown
   # Drop Box

   気になったリンクをここに貼る。タイトルやメモは任意。
   `/curate` 実行時に優先的に処理される。

   <!-- 例:
   https://example.com/interesting-article
     → AIエージェントの新しいアーキテクチャ

   https://x.com/someone/status/123456
   -->
   ```

---

### Phase 2: inbox/x/ のJSON処理

1. `library/inbox/x/` 配下の未処理JSONファイルを Glob で検索（`archive/` 配下は除外）
2. 各JSONファイルを Read で読み込み、ツイートデータを抽出
3. 各ツイートに対して **SIGNAL/NOISE 分類**（基準は後述）
4. SIGNALのツイートを `library/articles/` に記事ファイルとして保存
5. `catalog*.md` を更新
6. 処理済みJSONを `library/inbox/x/archive/` に移動（Bash で `mv`）
   - `archive/` ディレクトリがなければ作成

---

### Phase 3: inbox/web/ 処理

1. `library/inbox/web/` 配下の未処理ファイルを Glob で検索
2. 各ファイルを Read で読み込み
3. **SIGNAL/NOISE 分類**
4. SIGNALの記事を `library/articles/` に保存、catalog 更新

---

### Phase 4: PROPOSALS.md 更新

今回の処理で収集した記事群を横断的に分析し、以下への反映提案があれば
`library/inbox/PROPOSALS.md` に追記する:

- **CLAUDE.md のベストプラクティス更新** — 新しいパターン・禁止事項の発見
- **skills-registry への反映** — 新スキル候補・既存スキルの改善
- **FX自動取引への反映** — トレーディング戦略・リスク管理の新知見

提案がなければ追記しない（無理に書かない）。

---

## 記事ファイルのフォーマット

### ファイル名

`YYYY-MM-DD_連番_タイトル要約.md`

- 日付は取得日（今日の日付）
- 連番は `library/articles/` 内の既存ファイルから最大連番を取得し、+1 から採番
- タイトル要約は英語スネークケース（日本語記事も英訳して短縮）

### ファイル内容

```markdown
# タイトル

- URL: https://...
- ソース: web / x / drop
- 言語: ja / en
- テーマ: claude-code / claude-ecosystem / ai-trading / ai-news
- 取得日: YYYY-MM-DD
- いいね: N / RT: N（X投稿の場合のみ）
- 投稿者: @handle / フォロワー N（X投稿の場合のみ）

## 要約
（5-10行。具体的技術名・数値・なぜ重要かを含める）
```

- drop.md 由来の記事は `ソース: drop` とする
- X投稿でない場合は「いいね」「投稿者」行を省略
- テーマの判定:
  - Claude Code 関連 → `claude-code`
  - Anthropic API / MCP / Agent SDK → `claude-ecosystem`
  - トレーディング・FX・アルゴリズム取引 → `ai-trading`
  - その他AI全般 → `ai-news`

---

## catalog 更新ルール

### テーマ別振り分け

| テーマ | catalog ファイル |
|--------|----------------|
| claude-code | catalog.md |
| claude-ecosystem | catalog.md |
| ai-trading | catalog-trading.md |
| ai-news | catalog-news.md |

### 更新手順

1. **必ず該当 catalog ファイルを Read して既存フォーマットを確認**してから追記
2. 既存エントリの最大 No. を取得し、続きから採番
3. **重複チェック**: 既存エントリのURL・タイトルと照合。重複は除外
4. 状態は `読了` とする
5. テーブル行のフォーマットは既存行に厳密に合わせる

#### catalog.md のエントリ形式

```
| # | タイトル | ファイル | 分類 | 要点（1行） | 反映先 | 状態 |
```

#### catalog-trading.md / catalog-news.md のエントリ形式

```
| No. | タイトル | 言語 | 状態 | タグ | ファイル |
```

---

## SIGNAL/NOISE 分類基準

### SIGNAL（保存対象）

- 具体的な技術情報（実装例・アーキテクチャ・設定方法）
- 公式発表・リリースノート
- 一次情報（論文・公式ブログ・インタビュー）
- 定量データ（ベンチマーク・実験結果・統計）
- 新ツール・新サービスの紹介（実質的な情報あり）
- 実践知見・Gotchas・落とし穴の共有

### NOISE（除外対象）

- 感想のみ（「すごい！」「やばい」等、具体情報なし）
- 自己宣伝・アフィリエイト
- 内容のないリスト（「おすすめ10選」だけでリンク先が薄い）
- 同じニュースの繰り返し・転載（既にSIGNALで取得済みのもの）
- AIアート・AI音楽の作品投稿
- フォロワー稼ぎ・エンゲージメントベイト

---

## 最終出力: 処理サマリー

全フェーズ完了後、以下の形式でサマリーを出力する:

```
=== キュレーション完了 ===
Phase 1 (drop.md):  処理 N件 / 保存 N件
Phase 2 (inbox/x):  処理 N件 / SIGNAL N件 / NOISE N件
Phase 3 (inbox/web): 処理 N件 / SIGNAL N件 / NOISE N件
Phase 4 (PROPOSALS): 提案 N件

記事保存: 合計 N件
  claude-code:      N件 → catalog.md
  claude-ecosystem: N件 → catalog.md
  ai-trading:       N件 → catalog-trading.md
  ai-news:          N件 → catalog-news.md
```

---

## Gotchas

- drop.md のテンプレート部分（ヘッダー + HTMLコメント）は絶対に消さない
- catalog の連番は articles/ のファイル名連番とは別管理。catalog 内の最大 No. から続ける
- X投稿の取得で adhx API が失敗した場合はスキップしてログに残す（エラーで全体を止めない）
- WebFetch でタイムアウトやアクセス拒否が発生した場合も同様にスキップ
- 大量のJSONファイルがある場合、1回のセッションで全件処理しきれない可能性がある。その場合は処理済み分だけアーカイブし、残りは次回に回す
- `inbox/x/archive/` や `inbox/web/archive/` が存在しない場合は作成してから移動する
