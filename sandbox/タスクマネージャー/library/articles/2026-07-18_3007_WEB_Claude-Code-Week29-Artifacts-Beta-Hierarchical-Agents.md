# Claude Code Week 29：Artifacts β・3段ネスト・/cd・Voice Mode

- URL: https://releasebot.io/updates/anthropic/claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-18

## 投稿内容
Claude Code 2026年7月13-17日（Week 29）の主要アップデート：

1. **Artifacts βリリース**：セッション成果物をclaude.aiのライブ共有ページとして公開・インプレース更新
2. **階層型エージェントスポーン**：親エージェントが最大3段階ネストで子エージェントを生成。複数モジュール横断タスクの分解に対応
3. **/cd コマンド**：会話中に作業ディレクトリを変更してもプロンプトキャッシュを維持
4. **Voice Mode**：/voiceコマンドでスペースバーpush-to-talk音声入力
5. **Opus 4.8デフォルト化**：Max/Team Premium/Enterprise pay-as-you-goでOpus 4.8がデフォルト（high effort設定）
6. **--safe-mode**：全カスタマイズ無効化デバッグオプション
7. **セッション上限設定**：WebSearch上限200件・サブエージェント上限200件（CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSIONで調整可）

## 要約
Week 29の目玉はArtifacts β（成果物のライブ共有ページ化）と3段階ネストの階層型エージェントスポーン。/cdコマンドでキャッシュ維持のままディレクトリ変更可能になりワークフローが柔軟化。Voice Modeも段階的ロールアウト中。Opus 4.8がMax/Enterprise向けデフォルトとなり、複雑なエージェントタスクの標準品質が向上。
