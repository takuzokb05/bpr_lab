# Claude Code Week 34 (Aug 17–21): /design・Concise・Remote Control GA

- URL: https://code.claude.com/docs/en/whats-new/2026-w34
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-28

## 要約

Claude Code 公式 Week 34 (v2.1.234→v2.1.239) の新機能3本まとめ。

1. **/design（research preview）**: `/design <brief>` を実行するとUIのartboard（編集可能なキャンバス）を複数案生成し、公開リンクを返す。Artifacts基盤上で動作し、Pro/Max/Team/Enterprise対応。v2.1.233以降が必要。ピックした案をそのままClaude Codeで実装できる一気通貫ワークフロー。

2. **Concise出力スタイル（v2.1.237）**: 前置きや説明を省略し「結果を先に出す」新しいビルトインスタイル。`/config` の Output Style か `settings.json` の `"outputStyle": "Concise"` で有効化。詳細説明を求めれば通常通り全文返答。エラー・セキュリティ警告・危険な操作の確認は常に完全表示。

3. **Remote Control GA（モバイル）**: `claude remote-control` を実行したマシンがClaudeモバイルアプリのCodeタブ上部に「デバイスカード」として表示。スマホからディレクトリ選択→セッション開始が可能。Remote Controlがresearch previewから正式リリースへ。

その他改善: usage limit到達時の自動継続、スペルチェック設定（aspell/hunspell/ispell）、GitLab MR連携バッジ、モバイルからの努力レベル変更が即時反映、`/permissions` や `/add-dir` の作業中実行対応、`/goal` の30分チェックイン、自分のプロンプトのMarkdownレンダリング、`ANTHROPIC_DEFAULT_MODEL` 環境変数、`notify_when_idle` クロスセッションメッセージ、Windows native対応 SendMessage/ListAgents、自己ホストランナーの `--defer-shutdown-max-min` / `--proxy-authorization-command`。

**なぜ重要**: /design + Concise + Remote Control GAの3本立ては開発ワークフロー最適化に直結。特に/designは従来claude.ai/designとターミナルを往復していた作業をゼロ往復に短縮する。Conciseは長いAI返答に慣れてしまったユーザーの作業速度を上げる。
