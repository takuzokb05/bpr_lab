# CLAUDE.md完全ガイド: メモリ・ルール・ロード・クロスツール圧縮の全解説

- URL: https://medium.com/@bijit211987/the-complete-guide-to-claude-md-memory-rules-loading-and-cross-tool-compression-97cc12ed037b
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-28

## 要約
CLAUDE.mdの包括ガイド（Bijit Ghosh著、2026年5月）。4層メモリ構造（Project/User/Session/Dynamic）の違いと使い分け、ファイルロードのタイミング・優先順位・スコープルールを詳説。クロスツール圧縮（Claude Code↔API間でのコンテキスト転送）の仕組みも解説。実践推奨事項：80-120行の上限で高シグナルなルールのみ記載、/initで生成した内容を精査・削減してから利用、一般的なアドバイス（"シニアエンジニアのように振る舞え"等）は削除してHooksに変換。よくある失敗例：長すぎるCLAUDE.mdで重要ルールが無視される問題とその修正方法を具体的に提示。
