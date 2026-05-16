# envをdenyリストとgitignore両方で保護する具体手順

- URL: https://x.com/akaoniudetate/status/2055755295675252876
- ソース: x
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-05-16
- いいね: 0 / RT: 0 / リプライ: 1
- 投稿者: @akaoniudetate / フォロワー 6,676

## 投稿内容
3、.envファイルに目隠しをする
APIキーやパスワードが入っている.envファイルはデフォルトだとClaude Codeが普通に読める。悪意がなくてもやり取りの中にAPIキーが混ざったら終わりだ。denyリストへの追加と.gitignoreへの記載の両方をやって二重に塞ぐ。片方だけでは足りない。

## 要約
.envをdenyリストと.gitignore両方で保護する具体手順
（判断理由: .envをdenyリスト＋.gitignoreで二重保護）
