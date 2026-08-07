# Claude Code Subagents: The 2026 Production Playbook — Totalum Blog

- URL: https://www.totalum.app/blog/claude-code-subagents-totalum
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-07

## 要約

本番環境でのClaude Codeサブエージェント運用知見をまとめた実践ガイド。

**サブエージェントの3種類**:
1. **セッション内サブエージェント**: 単一セッション内で動作し、メインエージェントへのみ報告
2. **Agent Teams**: 複数の独立したClaude Codeセッションが直接通信。同一マシン内のチームメイト
3. **外部オーケストレーター**: 複数リポジトリ・マシン跨ぎで実行

**コスト最適化戦略**:
- 純粋に「答えだけ欲しい」タスクにはサブエージェントが安上がり（思考過程が不要）
- モデルを落として（Haiku等）コスト削減しながらも並列で品質担保
- depth制限（CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH）と並列上限（CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS、デフォルト20）を設定

**AGENTS.md設計のベストプラクティス**:
- `name`・`description`・`tools`・`model`のフロントマターを明示
- ツールを制限し最小権限原則を適用
- description はオーケストレーターがrouting判断に使うため精確に

**v2.1.224での変更**: 1セッションあたり200件のspawnキャップ廃止。長期セッションでの制限がなくなった（並列・depth制限は継続）

**なぜ重要か**: FX自動取引システムやキュレーションルーチンの分散化設計に直接応用できる実務知見。
