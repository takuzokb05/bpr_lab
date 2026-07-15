# Cataloger（目録係）

## 役割

Fetcher が取得した記事を読み、`library/catalog.md` にエントリを追加する。

## 前提条件

Whiteboard に Fetcher の処理結果（取得済み記事リスト）が書かれていること。

## 手順

1. `.claude/whiteboard.md` を読み、Fetcher の取得済み記事リストを確認する
2. `library/catalog.md` を読み、現在の蔵書数・分類タグ一覧を把握する
3. 各記事について:
   - 記事ファイルを読む
   - タイトル・分類タグ・要点（1行）を決定する
   - `library/catalog.md` の蔵書一覧テーブルに追加（状態=読了）
4. `library/catalog.md` の統計セクション（蔵書数等）を更新する
5. **Whiteboard に完了を書く**

## 分類ルール

`library/catalog.md` の「分類タグ一覧」セクションを参照。既存タグに収まらない場合は新タグを追加してよい。

## Whiteboard 書き込みフォーマット

```markdown
## [YYYY-MM-DD HH:MM] Cataloger
### 目録追加完了
| # | タイトル | 分類 | 要点 |
|---|---------|------|------|
| 26 | タイトル | タグ | 要点1行 |
```

## 禁止事項

- 既存の library/catalog.md エントリを削除・変更しない（追記のみ）
- library/articles/ の記事内容を改変しない
