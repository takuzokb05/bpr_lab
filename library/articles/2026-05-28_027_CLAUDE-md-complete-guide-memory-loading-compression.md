# CLAUDE.md完全ガイド: 4層メモリ・ロードタイミング・クロスツール圧縮の全解説

- URL: https://medium.com/@bijit211987/the-complete-guide-to-claude-md-memory-rules-loading-and-cross-tool-compression-97cc12ed037b
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-28

## 投稿内容
The Complete Guide to CLAUDE.md: Memory, Rules, Loading, and Cross-Tool Compression. CLAUDE.md is a special file that Claude reads at the start of every conversation. The most battle-tested structure organizes content into three layers: The What (your tech stack, project structure, and key dependencies), The Why (the purpose of key components and architectural decisions), and The How (explicit rules for how you want Claude to work). Keep it to 80-120 lines max. General advice like 'be a senior engineer' consumes instruction budget without paying it back — convert these to hooks.

## 要約
CLAUDE.mdの包括ガイド（Bijit Ghosh著、2026年5月、Medium）。4層メモリ構造（Project/User/Session/Dynamic）の違いと使い分け、ファイルロードのタイミング・優先順位・スコープルール（Project→User→Session→Dynamic の優先順位）を詳説。クロスツール圧縮：Claude Code↔API間でのコンテキスト転送・圧縮の仕組みも解説。実践推奨：80-120行上限で高シグナルなルールのみ記載、/initで生成した内容を精査・削減してから利用、一般的なアドバイス（"シニアエンジニアのように振る舞え"等）は削除しHooksに変換して確実な実行を保証。よくある失敗：長すぎるCLAUDE.mdで重要ルールが無視される→解決策は容赦ない削減とHooks化。3層構成（What/Why/How）を基本骨格とした実践的サンプル付き。
