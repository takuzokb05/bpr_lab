# MT5 Python：ブローカーサーバータイム差異による時間ウィンドウ取り逃しをposition_idで解決

- URL: https://x.com/bottsukuttemita/status/2058458004618670433
- ソース: x
- 言語: ja
- テーマ: ai-trading
- 取得日: 2026-05-24
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @bottsukuttemita / フォロワー 169

## 投稿内容
MT5でPythonを書くとき、
ブローカーによってサーバータイムが違います。

XMはEET（UTC+3）なので、
JST（UTC+9）との差は6時間です。

https://t.co/LO5MZp8vkY()で時間ウィンドウを作ると
この差で全部取り逃します。position_idで直接取得する方が安全です。

#AI #Python

## 要約
MT5 PythonでブローカーのサーバータイムとJSTの差異による時間ウィンドウ取り逃し問題の解決策。XMのサーバータイムはEET（UTC+3）でJSTとは6時間差があり、datetime関数で時間ウィンドウを作成するとすべてのポジションを取り逃す。解決策はposition_idを直接指定して取得する方法。MT5 Python API開発における見落としやすい時間管理の落とし穴を具体的に解説した技術的に価値の高い実践知見。FX自動売買システムのMT5連携実装時に必ず確認すべき事項。
