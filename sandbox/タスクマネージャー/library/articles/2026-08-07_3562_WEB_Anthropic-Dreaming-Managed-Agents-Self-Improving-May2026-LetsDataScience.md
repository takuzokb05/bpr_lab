# Anthropic Launches Dreaming for Claude Agents: Self-Improving AI at Scale

- URL: https://letsdatascience.com/blog/anthropic-dreaming-claude-managed-agents-self-improving-may-6
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-07

## 要約

Let's Data ScienceによるClaude Managed Agents "dreaming" 機能の詳細分析。

**dreamingの仕組み詳細**:
- エージェントがセッション間にバックグラウンドで「夢を見る（dreaming）」—過去セッションのトランスクリプトを再読し、記憶ストアを自律的に更新
- `dream_schedule`で実行頻度を設定（デフォルト: 5セッションごとに1回）
- 出力は整理済みの記憶ストアとして返る

**実際のインパクト（報告事例）**:
- Harvey（法律AI）: タスク完了率6倍改善
- ある開発チーム: 週40時間かかっていたコードレビューを5時間に短縮
- エージェントが「ユーザーがPRの冒頭でテストを確認したい」というパターンを自律的に学習

**技術的詳細**:
- dreaming passは記憶の衛生管理（重複除去・陳腐化エントリ削除）をベースに実行
- 「エージェントが何を覚えているか」の可視化ダッシュボードも提供
- 記憶変更のdiffをレビューしてから適用する「慎重モード」あり

**批判的視点**:
- 記憶の「歪み」リスク: 過去のバイアスを増幅する可能性
- どの洞察を記憶するかの透明性が課題

**なぜ重要か**: 自律的に改善するエージェント設計の実践事例として最重要参考文献。
