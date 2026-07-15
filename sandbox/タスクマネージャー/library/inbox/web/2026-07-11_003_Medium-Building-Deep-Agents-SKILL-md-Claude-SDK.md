# Building Deep Agents + SKILL.md with Claude SDK

- URL: https://abvijaykumar.medium.com/building-deep-agents-skill-md-with-claude-sdk-11d8bf47754b
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-11

## 要約
SKILL.mdとClaude Agent SDKを組み合わせた本番エージェント構築の実践ガイド（2026年5月）。3層モデル：AGENTS.md（プロジェクト規約）＋SKILL.md（専門プレイブック）＋SDK（ランタイム）。重要設定ゲート：`settingSources=["user","project"]`でスキル発見を有効化、`allowedTools`に`"Skill"`を明示追加が必須。具体的コード例5点：①コミットメッセージ生成エージェント（最小スキル有効化）②マルチスキルオーケストレーター（code-analyzer/test-writer/security-checkerの3専門サブエージェント）③フックベースのアクセス制御④GitHub MCPツール統合⑤メッセージストリーム処理。フォルダ構造：`.claude/skills/[skill-name]/SKILL.md`。著者がスキルなしエージェントは「即興が多すぎる」と指摘—SKILL.mdで決定論的・再現可能な挙動を実現。
