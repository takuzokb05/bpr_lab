# Claude Skillsとは？仕組み・作り方・活用事例を徹底解説

- URL: https://japan-ai.co.jp/media/7344/
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-07-02

## 要約

JAPAN AIラボによるClaude Skills完全解説記事。スキルはClaude Codeがセッション開始時に自動検出する再利用可能な指示パックで、SKILL.mdファイル＋オプションのサポートファイルで構成。動作原理：Claude全スキル説明を読み込み→ユーザーメッセージと照合→関連スキルをコンテキストに注入（常時ロードではなく遅延ロード）。作り方：.claude/skills/スキル名/SKILL.md に配置、フロントマター（name・description）必須。disable-model-invocation: trueで明示起動専用スキルに。活用事例：デプロイ前チェックリスト実行スキル・コードレビュー観点付きレビュースキル・Gitコミット規約遵守スキル・テスト生成スキル・API仕様書自動更新スキル。bundledスキル（/code-review・/batch・/debug・/loop・/claude-api）との使い分けも解説。
