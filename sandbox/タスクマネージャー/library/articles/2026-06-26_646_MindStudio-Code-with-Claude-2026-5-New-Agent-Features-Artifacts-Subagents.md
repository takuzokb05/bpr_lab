# Code with Claude 2026: 5 New Agent Features — Artifacts・Nested Subagents・/rewind・fallbackModel

- URL: https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-26

## 投稿内容
MindStudio blog "Code with Claude 2026: 5 New Agent Features Anthropic Just Shipped" — a practical breakdown of five features released to Claude Code in May–June 2026, each targeting a different layer of the agent orchestration stack.

## 要約
2026年5〜6月にAnthropicがClaude Codeへ投入した5つの主要エージェント機能を解説。①**階層型エージェントスポーン（最大5階層）**: 親エージェントが子エージェントを生成し、さらにその子も孫を生成可能。各エージェントが独立したコンテキスト窓を持ち、コンテキスト枯渇の解決策として設計。トークンコストは階層ごとに複利的に増加するため、必要最小限の深さに留めることを推奨。②**Artifacts（2026年6月18日ベータ開始）**: セッション作業をself-contained HTMLページとして出力。PRウォークスルー・インシデントダッシュボード・チェックリスト等に活用可能。Team/Enterprise planが必要、プライベートURLで組織内のみ共有。③**Agent view**: 全Claude Codeセッションを一画面で管理、実行中/ブロック中/完了の状態を可視化。④**/rewind**: セッション途中の任意チェックポイントへコードと会話を同時巻き戻し。⑤**fallbackModel**: 主モデル失敗時の自動フォールバックモデルをパラメータで指定可能。本番環境での信頼性向上に直結する実践的機能。
