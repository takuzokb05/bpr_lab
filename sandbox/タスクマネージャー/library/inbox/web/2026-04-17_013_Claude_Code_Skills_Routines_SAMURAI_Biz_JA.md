# Claude Codeスキル機能とスケジュール実行徹底解説: Routinesで繰り返し作業を自動化

- URL: https://note.com/samuraijuku_biz/n/n00cd6c7b3521
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-04-17

## 要約
SAMURAI Bizによるスキル機能とRoutinesの組み合わせ活用解説。スキル基礎：.claude/skills/ディレクトリ構造・SKILL.mdのYAMLフロントマター書き方・descriptionへのトリガー文言の重要性。Routinesとスキルの連携パターン：Routineのプロンプトでスキルを直接呼び出す方法（例：「/curate スキルを実行して結果をcommitする」をRoutineとして設定）。実践例：(1)毎朝PR確認＆要約をRoutineで自動実行、スラックbotスキルで通知；(2)コード変更後にsimplifyスキルをRoutineのPostToolUseと組み合わせて自動品質チェック；(3)週次「依存関係監査」Routineでセキュリティ脆弱性を自動検出。注意点：RoutinesはリサーチプレビューでSkillツールを呼び出せないという制約（issue #38719）への対処法も解説。非エンジニアがスケジュールで日常業務を自動化するユースケースを詳述。
