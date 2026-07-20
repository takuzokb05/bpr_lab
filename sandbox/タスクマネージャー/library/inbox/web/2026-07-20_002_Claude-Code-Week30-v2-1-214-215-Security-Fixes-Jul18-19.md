# Claude Code Week 30：v2.1.214-215 セキュリティ修正・/verify /code-review 廃止

- URL: https://releasebot.io/updates/anthropic/claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-20

## 要約
Claude Code 2026年7月18〜19日（Week 30前半）のリリース内容。**v2.1.215（7/19）**：`/verify`・`/code-review`スキルを自動実行しないよう変更（明示的に呼び出した場合のみ実行）。**v2.1.214（7/18）**：(1) Edit(src/**)のような単一セグメントdir/**許可ルールが、ツリー内の任意のネストされたdirディレクトリへの書き込みを自動承認してしまうバグを修正 (2) Windows PowerShell 5.1セッションで実行されるコマンドに影響するパーミッションチェックバイパスを修正 (3) Bashパーミッションチェックがファイルディスクリプタリダイレクト形式（bashが権限アナライザーと異なる方法で解析）を誤判定するバグを修正 (4) 10,000文字超のコマンドでパーミッションチェックが誤判定するバグを修正（10,000字超は常にプロンプト表示に）。また前週（v2.1.211, 7/15）: `--forward-subagent-text`フラグとCLAUDE_CODE_FORWARD_SUBAGENT_TEXT環境変数を追加（stream-json出力にサブエージェントのテキスト・thinking を含める）。
