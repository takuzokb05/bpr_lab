---
name: collect-x-articles
description: "SocialData APIでX上の記事・投稿をバルク収集する。url:x.com/i/articleで長文記事、min_faves指定でバズ投稿、lang:ja/enで日英両方。テーマ指定でドメイン別収集も可能"
user_invocable: true
---

# /collect-x-articles — X記事バルク収集スキル

## 概要

SocialData API を使って X (Twitter) 上の記事・投稿をバルク収集し、`library/` に蓄積する。
元ネタ: 蔵書#45「バズってるX記事を全自動で収集する方法（beku_AI）」

## 前提条件

- `SOCIALDATA_API_KEY` が環境変数に設定済みであること
- Python 3.10+ と `requests` ライブラリが利用可能であること

## 入力

ユーザーからモードとパラメータを受け取る:

| モード | 例 | 説明 |
|--------|---|------|
| **記事収集** | 「X記事を集めて」 | `url:x.com/i/article` で長文記事のみ |
| **バズ投稿** | 「Claude Codeのバズ投稿」 | テーマ指定 + `min_faves:100` |
| **ドメイン収集** | 「AI Tradingの最新」 | ドメイン別の検索クエリセットを実行 |
| **全自動** | 「全ドメイン収集して」 | 4ドメイン × 日英で一括実行 |

パラメータ未指定時のデフォルト:
- 期間: 直近7日 (`within_time:7d`)
- いいね閾値: 100 (`min_faves:100`)
- 言語: 日英両方
- 上限: 各クエリ200件

## プロセス

### Step 1: 検索クエリ生成

ドメインに応じた検索クエリを生成する。各ドメインに最低10クエリ。

#### ドメイン別クエリテンプレート

**Claude Code（アプデ+ユースケース）**:
```
"Claude Code" min_faves:100 lang:en within_time:7d
"Claude Code" min_faves:50 lang:ja within_time:7d
"CLAUDE.md" min_faves:50 within_time:7d
"claude code" skills min_faves:50 within_time:7d
"claude code" hooks min_faves:50 within_time:7d
"claude code" MCP min_faves:50 within_time:7d
url:x.com/i/article "Claude Code" within_time:30d
url:x.com/i/article "claude" "agent" within_time:30d
from:AnthropicAI "Claude Code" within_time:7d
from:alexalbert__ within_time:7d
```

**Claude エコシステム（API/MCP/SDK）**:
```
"Anthropic API" min_faves:100 within_time:7d
"Claude API" min_faves:100 within_time:7d
"MCP server" min_faves:50 within_time:7d
"Model Context Protocol" min_faves:50 within_time:7d
"Agent SDK" anthropic min_faves:50 within_time:7d
url:x.com/i/article MCP within_time:30d
from:modelaborotocol within_time:7d
```

**AI Trading**:
```
"AI trading" min_faves:100 lang:en within_time:7d
"LLM trading" min_faves:50 within_time:7d
"algorithmic trading" AI min_faves:50 within_time:7d
"FX" "自動売買" AI min_faves:30 lang:ja within_time:7d
"trading bot" LLM min_faves:50 within_time:7d
url:x.com/i/article "AI trading" within_time:30d
url:x.com/i/article "algorithmic trading" within_time:30d
```

**AI News**:
```
"AI news" min_faves:500 lang:en within_time:3d
"LLM" "release" min_faves:200 within_time:7d
"AI regulation" min_faves:100 within_time:7d
"AI agent" min_faves:200 within_time:7d
"生成AI" min_faves:100 lang:ja within_time:7d
from:OpenAI within_time:3d
from:GoogleAI within_time:3d
from:AnthropicAI within_time:3d
```

### Step 2: SocialData API 実行

`library/scripts/collect_x.py` を使って収集を実行する。

```bash
cd library/scripts
python collect_x.py --domain all --days 7 --min-faves 100
```

スクリプトが以下を行う:
1. 各クエリを順次実行（120 req/min リミット遵守）
2. レスポンスからツイートデータを抽出
3. 重複排除（tweet ID ベース）
4. `library/inbox/x/` に一時保存

### Step 3: フィルタリング・精査

収集した投稿を以下の基準でフィルタリング:
- スパム・宣伝・アフィリエイト除外
- 実質的内容がないもの除外（「すごい！」だけ等）
- 同一ニュースの転載は最もエンゲージメントが高いものだけ残す
- URL付き投稿はURLの先にある記事の存在を確認

### Step 4: articles/ に保存

精査を通過した投稿を `library/articles/` に保存する。

ファイル名: `YYYY-MM-DD_連番_タイトル要約.md`

ファイル形式:
```markdown
# タイトル（投稿の要点を短く）

- URL: https://x.com/ユーザー名/status/ID
- 言語: ja / en
- テーマ: claude-code / claude-ecosystem / ai-trading / ai-news
- 取得日: YYYY-MM-DD
- いいね: N / RT: N / リプライ: N
- 投稿者: @handle (フォロワー数)

## 投稿内容

（投稿テキストそのまま）

## 要約

（3-5行で要点と意義を記載）
```

### Step 5: 蔵書目録を更新

テーマに応じて該当する蔵書目録を更新:
- claude-code / claude-ecosystem → `catalog.md`
- ai-trading → `catalog-trading.md`
- ai-news → `catalog-news.md`

### Step 6: 統計レポート

収集結果を報告:
```
=== 収集完了 ===
検索クエリ数: N
取得投稿数: N（重複排除後）
精査通過: N
ドメイン別: Claude Code N件 / AI Trading N件 / AI News N件
コスト: $X.XX（$0.0002 × N件）
```

## Gotchas

- SocialData APIのレートリミットは120 req/min。大量収集時は待機が必要
- `url:x.com/i/article` は長文記事のリンクを含む投稿を返す（記事本文は別途取得が必要）
- 記事詳細取得には `GET /twitter/user/{user_id}/articles` を使う
- `within_time:30d` で30日分取得可能だが、古い投稿ほど取得漏れが増える
- 日本語クエリは `lang:ja` を付けないと英語結果に埋もれる
- 1ページ約20件返却。200件取得にはカーソルで10ページ分ページネーションが必要
- 残高ゼロで HTTP 402。事前にクレジット確認を推奨
