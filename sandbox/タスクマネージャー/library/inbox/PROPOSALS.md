# 反映提案ログ

記事収集から得た知見をCLAUDE.md・skills-registry・設定等に反映すべき提案をまとめます。

---

## 2026-03-27 収集分

### 1. CLAUDE.md への反映提案

#### 1-1. Progressive Disclosure パターンの採用
**出典:** articles/2026-03-27_013_効果的なCLAUDE_md書き方.md / articles/2026-03-27_003_50_Claude_Code_Tips_Best_Practices.md

**提案内容:**
CLAUDE.md に書く情報を「常に必要な情報」と「特定状況でのみ必要な情報」に分離する。

```
CLAUDE.md          … 常に必要なプロジェクト概要・必須コマンド・絶対的禁止事項
.claude/rules/*.md … 特定のファイル種別・タスク種別にのみ適用されるルール
```

YAMLフロントマターのglobパターンで条件付きルールを設定することで、コンテキスト消費を抑えつつ必要なルールだけを読み込める。

#### 1-2. CLAUDE.md の「禁止パターン」明記
**出典:** articles/2026-03-27_006_Claude_Code_Hooks_Guide_2026.md

**提案内容:**
CLAUDE.md は約80%の遵守率。**絶対に守らせたいルール（秘密情報コミット禁止・本番DBへの直接書き込み禁止等）はCLAUDE.mdではなくフックで実装する**ことを明記すべき。CLAUDE.mdには「このルールはフックで強制されている」とコメントを入れると読者への注意喚起になる。

#### 1-3. コンテキスト管理の閾値をCLAUDE.mdに記載
**出典:** articles/2026-03-27_007_Claude_Code_Complete_Guide_2026.md / articles/2026-03-27_002_Claude_Code_Tips_and_Tricks.md

**提案内容:**
コンテキスト管理の運用ガイドとして以下を記載：
- 0〜50%: 自由に作業
- 50〜70%: コンテキスト使用量に注意
- 70〜90%: `/compact` を使用
- 90%+: `/clear` 必須（この状態で作業継続するとハルシネーションが著しく増加）

#### 1-4. Auto Memory ディレクトリの設定
**出典:** articles/2026-03-27_001_Claude_Code_March_2026_Updates.md

**提案内容:**
`autoMemoryDirectory` 設定を `.claude/settings.json` に追加し、Claude が自動記録するメモリの保存先をプロジェクト管理下に含める（.gitignoreへの追加も検討）。

---

### 2. スキル設計への反映提案

#### 2-1. スキルの YAML フロントマター活用
**出典:** articles/2026-03-27_017_Claude_Code_Agent_Skills解説.md / articles/2026-03-27_009_Claude_Code_スキル活用術.md

**提案内容:**
既存スキルの SKILL.md に以下のフロントマターフィールドを追加・整備する：

```yaml
---
name: skill-name
description: Claude が自動判定に使う説明（詳細に書くほど自動呼び出し精度が上がる）
disable-model-invocation: true  # スクリプトのみのスキルの場合
allowed-tools: Read, Grep, Edit  # 必要なツールのみに限定
---
```

特に `description` の充実が自動呼び出し精度に直結するため、「どんなときに使うか」を具体的に記述する。

#### 2-2. スキルのオープンスタンダード対応
**出典:** articles/2026-03-27_017_Claude_Code_Agent_Skills解説.md

**提案内容:**
Agent Skills は GitHub Copilot Coding Agent や OpenAI Codex CLI とも SKILL.md フォーマットを共有可能。チームに複数のAIツール利用者がいる場合、共通スキルリポジトリとして管理する価値がある。

#### 2-3. スキルの「育てる」運用フロー整備
**出典:** articles/2026-03-27_009_Claude_Code_スキル活用術.md

**提案内容:**
スキル作成時は最小構成（SKILL.mdのみ）からスタートし、実際の使用を通じて段階的に育てるフローを標準化する：
1. Claude に「今やった作業をスキルにして」と依頼 → SKILL.md を自動生成
2. 2週間実際に使って不足を洗い出す
3. references/ に詳細ドキュメントを追加
4. 必要に応じて allowed-tools・disable-model-invocation を調整

---

### 3. フック設計への反映提案

#### 3-1. MCP ツール呼び出しへのフック適用
**出典:** articles/2026-03-27_006_Claude_Code_Hooks_Guide_2026.md / articles/2026-03-27_005_Claude_Code_Setup_MCP_Hooks_Skills_2026.md

**提案内容:**
MCP ツールの呼び出しにもフックが適用可能。マッチャーパターン `mcp__<server>__<tool>` を活用して特定 MCP 操作を傍受できる。例：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__github__push_files",
        "hooks": [{ "type": "command", "command": "scripts/pre-push-check.sh" }]
      }
    ]
  }
}
```

#### 3-2. 無人実行（Unattended）向けフック安全網の整備
**出典:** articles/2026-03-27_006_Claude_Code_Hooks_Guide_2026.md

**提案内容:**
Claude Code を無人実行（ヘッドレスモード・GitHub Actions等）で使う場合、以下のフックを必須とする：
- `PreToolUse` で `.env`・`.pem`・`credentials` 等を含むファイルのコミットをブロック
- `PreToolUse` で本番ブランチ（main/master）への直接pushをブロック
- `PostToolUse` でコードフォーマッターを自動実行

---

### 4. MCP 設定への反映提案

#### 4-1. MCP ツール検索（遅延ロード）の活用
**出典:** articles/2026-03-27_005_Claude_Code_Setup_MCP_Hooks_Skills_2026.md / articles/2026-03-27_003_50_Claude_Code_Tips_Best_Practices.md

**提案内容:**
MCP の Tool Search 機能（自動モード）を有効化することでコンテキスト使用量を最大 95% 削減できる。多数の MCP サーバーを登録している場合、この設定が必須。2026年1月のアップデートでデフォルト有効化済みだが、古い設定ファイルを持つ環境では明示的に確認する。

---

*以上の提案は優先度順ではなく、重要度に応じて実装タイミングを判断してください。*
