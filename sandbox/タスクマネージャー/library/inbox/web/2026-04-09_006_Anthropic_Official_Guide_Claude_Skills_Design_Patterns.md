# Anthropic's 33-Page Official Guide Distilled: 5 Claude Skills Design Patterns & Debugging

- URL: https://smartscope.blog/en/generative-ai/claude/claude-skills-design-patterns-official-guide/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-09

## 要約
Anthropic公式33ページのAgent Skills設計ガイドを凝縮した技術記事。公式ドキュメントから抽出した5つの設計パターン（①ルーティングテーブル型、②Progressive Disclosure型、③モデル指定型、④外部スクリプト分離型、⑤スキルチェーン型）を説明。特に「ルーティングテーブル型」はSKILL.mdを100行以内に保ちつつ13の参照ファイルを管理する手法で、コンテキスト消費を最小化。スキルfrontmatterに`model: haiku`を指定すると軽量タスクをコスト削減しながら実行できる点も説明。デバッグ方法（`/skill-debug`コマンドの使い方、description改善の判断基準）も詳説。Anthropic公式ドキュメントの一次情報に基づく。
