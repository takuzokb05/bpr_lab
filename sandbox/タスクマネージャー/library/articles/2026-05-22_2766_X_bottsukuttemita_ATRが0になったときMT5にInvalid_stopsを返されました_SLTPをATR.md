# ATRが0になったとき、MT5に「Invalid stops」を返されました。

SL/TPをATR×倍率で計算していたので、
ATRが極小になると注文が通らな

- URL: https://x.com/bottsukuttemita/status/2057615699481370709
- ソース: x
- 言語: ja
- テーマ: ai-trading
- 取得日: 2026-05-22
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @bottsukuttemita / フォロワー 166

## 投稿内容
ATRが0になったとき、MT5に「Invalid stops」を返されました。

SL/TPをATR×倍率で計算していたので、
ATRが極小になると注文が通らない。

max(ATR計算値, 固定pips) で下限を保証して解決しました。

ゼロ除算よりタチが悪い「ゼロ乗算」でした。

#AI #Python https://t.co/AZMZhkUbsZ



## 要約
MT5でATRが0になった際に「Invalid stops」エラーが発生する問題を解決した技術的知見。SL/TPをATR×倍率で計算していたため、ATR極小時に注文が通らなくなる。解決策はmax(ATR計算値, 固定pips)で下限を保証する方式。ゼロ除算より発見しにくい「ゼロ乗算」バグとして整理されており、MT5/MQL5開発者に実践的に役立つ情報。
