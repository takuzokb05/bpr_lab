# New in Claude Managed Agents: Dreaming, Outcomes, and Multiagent Orchestration — Official Blog

- URL: https://claude.com/blog/new-in-claude-managed-agents
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-07

## 要約

Anthropic公式ブログによるClaude Managed Agentsの新機能解説（2026-05-06出荷、2026-08現在一般提供中）。

**Dreaming（自律的記憶整理）**:
- エージェントのセッション間に走るスケジュール済みプロセス
- 過去セッションのトランスクリプトと記憶ストアを読み込み、パターンを抽出・整理
- 重複を統合、古いエントリを置き換え、新しい洞察を浮上させる
- 「1エージェントだけでは気づけない繰り返しパターン」を発見できる
- 制御オプション: 自動更新 or レビュー後適用の選択可能

**Outcomes（成果評価）**:
- ルーブリックベースの成果評価機能
- エージェントが目標を達成したか定量的に評価
- Harvey社実績: タスク完了率が6倍に向上

**Multiagent Orchestration**:
- 複数のManaged Agentが協調してタスクを分担
- Agent SDKの基盤上にscheduler・dreaming pass・rubric評価を重ねた構造

**Scheduled Tasks更新**: 2026-08以降、スケジュールタスクはサーバー側で実行（デバイス不要）

**なぜ重要か**: bpr_labのタスクマネージャーも記憶ストア整理に同様の仕組みを応用できる。dreamingパターンは alter-ego.md の自動更新機能として実装できる可能性がある。
