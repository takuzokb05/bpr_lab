---
description: "x.com または twitter.com のリンクが会話に含まれるとき、投稿内容を自動取得する"
---

# ADHX — X/Twitter 投稿リーダー

X（Twitter）の投稿を公開APIでJSON取得するスキル。認証不要。

## 使い方

ユーザーが x.com / twitter.com のリンクを貼ったら:

1. URLからユーザー名とステータスIDを抽出
2. ADHX APIを呼び出す
3. 取得した内容を表示・活用する

## API

```
GET https://adhx.com/api/share/tweet/{username}/{statusId}
```

### URL解析パターン

```
https://x.com/{username}/status/{statusId}
https://twitter.com/{username}/status/{statusId}
```

クエリパラメータ（`?s=20` 等）は無視する。

### 呼び出し例

```bash
curl -s "https://adhx.com/api/share/tweet/trq212/2033949937936085378"
```

### レスポンス構造

```json
{
  "id": "ステータスID",
  "url": "元URL",
  "text": "投稿テキスト（通常ツイート）",
  "author": { "name": "表示名", "username": "ハンドル", "avatarUrl": "..." },
  "createdAt": "投稿日時",
  "engagement": { "replies": 0, "retweets": 0, "likes": 0, "views": 0 },
  "article": {
    "title": "記事タイトル（X Articleの場合）",
    "content": "本文（Markdown形式）"
  }
}
```

- 通常ツイート → `text` に本文
- X Article（長文投稿） → `article.content` に全文Markdown

## Gotchas

- 削除済み・非公開アカウントの投稿は取得できない
- `article` フィールドは X Article のみ。通常ツイートでは null または空
- レート制限は現時点でなし（変更される可能性あり）
