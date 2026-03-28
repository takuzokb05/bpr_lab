# claude-code-hooks-mastery (GitHub / disler)

- URL: https://github.com/disler/claude-code-hooks-mastery
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-28

## 要約

本番利用可能なClaude Codeフックのコレクションリポジトリ。各フックはPythonスクリプトとして実装され、**インラインdependency宣言**（PEP 723形式）を使用しているため別途requirements.txtが不要。
- `.claude/hooks/`ディレクトリへの配置・即時使用が可能な構造
- 含まれるフック例：git diff自動要約、TODO自動抽出、API呼び出しコスト計算、テスト自動実行
- フックのデバッグ方法（`CLAUDE_HOOKS_DEBUG=1`環境変数）も含む

再利用可能なフックのスターターコードとして活用できる。
