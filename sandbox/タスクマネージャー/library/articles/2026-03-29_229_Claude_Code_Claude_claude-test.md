# 【Claude Codeを本気で使うための僕のプロジェクト設定を全部公開します】

- URL: https://x.com/nosuke_moneque/status/2036804065817247899
- ソース: x
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-03-29
- いいね: 190 / RT: 9 / リプライ: 4
- 投稿者: @nosuke_moneque / フォロワー 12,830

## 投稿内容

【Claude Codeを本気で使うための僕のプロジェクト設定を全部公開します】

「毎回同じこと説明するのが面倒」
「Claudeにルールを覚えさせたい」

  そんな人のために作りました👇

  【フォルダ構造とは？】

  まずはこのフォルダ構造を作るだけ。

  claude-test/
  ├── CLAUDE.md        ← Claudeへの指示書
  ├── CLAUDE.local.md  ← 自分だけの個人設定
  ├── .gitignore
  └── .claude/
      ├── settings.json   ← 許可・禁止コマンド
      ├── commands/       ← スラッシュコマンド
      └── rules/          ← Claudeが守るルール

これを作ると毎回説明しなくてよくなる。

まずは【CLAUDE.md】 がすべての起点です。

プロジェクトフォルダに置くとClaude Codeが自動で読み込みます。

例）
  # プロジェクト概要
  eBay→ヤフオク 裁定取引リサーチツール

  ## コーディングルール
  - コメントは日本語で書く
  - 関数には必ずdocstringをつける
  - エラーハンドリングを必ず実装する

  ## 絶対にやってはいけないこと
  - APIキーをコードに直接書く
  - テストせずにコミットする

  これだけで毎回言わなくてよくなるんですね。

次に
【.claude/settings.json】で
  Claudeに使っていいコマンドを教える。

  {
    "permissions": {
      "allow": [
        "Bash(python:*)",
        "Bash(pytest:*)",
        "Read(*)",
        "Write(*)"
      ],
      "deny": [
        "Bash(rm -rf:*)",
        "Bash(sudo:*)"
      ]
    }
  }

rm -rf はファイルを全部消す超危険コマンドなのでを禁止しておくと安心して使)

.claude/commands/ にmdファイルを置くと
  スラッシュコマンドになる。

 /project:review https://t.co/Ra5vx4CisE
  → バグ・セキュリティ・読みやすさを自動チェック

 /project:pre-deploy
  → テスト実行→セキュリティ確認→requirements.txt更新まで自動でやってくれる。

繰り返す作業はコマンド化が正解です。

【.claude/rules/】 にルールを分けて書ける。

  【code-style.md】
  クラス名：大文字始まり（EbayFetcher）
  関数名：小文字＋アンダースコア（get_item_price）
  コメントは「なぜ」を書く：

  ❌ price = price * 1.1  # 1.1をかける
  ✅ price = price * 1.1  # 消費税10%を加算

  【testing.md】
  新しい関数 → 必ずテストも作る
  カバレッジ80%以上を目標

  【api-conventions.md】
  APIキーは必ず.envに。直書き即アウト。
  リトライは最大3回まで。

  【グローバル設定】
  さらに上位の設定も作れます。

  ~/.claude/CLAUDE.md
  ↑ PCの全プロジェクトに適用される

ここに書いておくと どのプロジェクトでも自動で有効になります。

僕はここに  「すべての応答は日本語で」  と書いています。

一度設定すれば二度と言わなくていいです。

  【まとめ】
  
  CLAUDE.md    → 毎回の説明が不要になる
  settings.json   → 危険なコマンドを禁止できる
  commands/    → 繰り返し作業をコマンド化
  rules/              → コードの品質を自動で保つ
  ~/.claude/      → 全プロジェクトに共通設定

Claude Codeは設定次第で全然別物になります！

参考になったらRT・いいねお願いします🙏

※　僕のフォルダ構造（ディレクトリ構造）↓↓

## 要約

（要約は次回 /curate 時に追記）
