# Building Deep Agents + SKILL.md with Claude SDK: 本番エージェント設計パターン

- URL: https://abvijaykumar.medium.com/building-deep-agents-skill-md-with-claude-sdk-11d8bf47754b
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-11

## 要約
SKILL.mdとClaude Agent SDKを組み合わせた本番エージェント構築ガイド（2026年5月, A B Vijay Kumar）。

**3層アーキテクチャ**:
- AGENTS.md: プロジェクト規約（全エージェント共通）
- SKILL.md: ドメイン専門プレイブック（必要時ロード）
- SDK: ランタイムエンジン

**2つの必須設定ゲート**（失敗原因No.1）:
1. `settingSources=["user","project"]` → スキル発見を有効化
2. `allowedTools`に`"Skill"`を明示追加 → スキル使用を許可

**コード例5パターン**:
1. コミットメッセージ生成（最小スキル有効化）
2. マルチスキルオーケストレーター（code-analyzer/test-writer/security-checkerの3専門サブエージェント、Opusオーケストレーター）
3. フックベースのアクセス制御（本番データベース書き込み禁止等）
4. GitHub MCP＋スキル統合PR自動レビュー
5. AssistantMessage/ResultMessage/SystemMessageのストリーム処理

**フォルダ構造**: `.claude/skills/[skill-name]/SKILL.md`

著者の核心知見：「スキルなしのエージェントは即興が多すぎる」—SKILL.mdで決定論的・再現可能な挙動を実現、コードレビュー・セキュリティ監査の品質が一定化。本番環境での可測性・スケーラビリティ・コンポーザビリティが向上。
