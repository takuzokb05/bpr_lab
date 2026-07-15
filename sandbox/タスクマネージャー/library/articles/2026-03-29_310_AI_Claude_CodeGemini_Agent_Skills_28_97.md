# AIエージェントの世界で

- URL: https://x.com/noguryu/status/2037366260334485749
- ソース: x
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-03-29
- いいね: 28 / RT: 1 / リプライ: 2
- 投稿者: @noguryu / フォロワー 4,007

## 投稿内容

AIエージェントの世界で
静かに「共通規格」が生まれている。

Claude CodeもGeminiも採用している
「Agent Skills」という仕組み。

テキストファイルに知識を構造化して渡すだけで
コード生成精度が 28% → 97% になる。

Google DeepMindが117プロンプトで実証した。

しかもこれ、Anthropic独自でもGoogle独自でもない。
オープンスタンダード。共通規格。

Claude → .claude/skills/
Gemini → .gemini/skills/

どちらも同じ構造：
・SKILL.md にルールと知識を記述
・必要な時だけ動的にロード
・補助スクリプトやドキュメントも同梱可能

RAGでもMCPでもファインチューニングでもなく
「よく整理されたmarkdownファイル」が
AIエージェントの精度を決める時代。

GoogleとAnthropicが同じ結論に辿り着いた。

これはAIエージェント開発の
事実上の標準になると思う。

https://t.co/NKElnTkxVA

## 要約

（要約は次回 /curate 時に追記）
