# Claude Code ワークフロー最適化・自動化テクニック調査

> 調査日: 2026-02-21
> 対象: Claude Code の実用的な最適化テクニック（すぐ使えるもの優先）

---

## 1. Git ワークフロー最適化

### 1.1 Git Worktree を使った並列セッション

**何ができるか**: 1つのリポジトリに複数の作業ディレクトリ（worktree）を作成し、それぞれで独立した Claude Code セッションを同時実行できる。機能開発とバグ修正を完全に分離して並列作業が可能。

**具体的な手順**:
```bash
# worktree を作成して Claude Code を起動（-w フラグ）
claude -w feature-auth       # feature-auth ブランチの worktree で起動
claude -w bugfix-123         # bugfix-123 ブランチの worktree で起動

# 手動で worktree を作成する場合
git worktree add ../my-feature feature-branch
cd ../my-feature
claude
```

**メリット**:
- 各セッションのコンテキストが汚染されない（互いの変更が見えない）
- 同じ問題に複数アプローチを試して比較できる
- マージコンフリクトが発生しない
- `/resume` で worktree 含む全セッションの一覧が表示される

**ソース**:
- [Claude Code 公式ドキュメント: Common Workflows](https://code.claude.com/docs/en/common-workflows)
- [incident.io: Shipping Faster with Claude Code and Git Worktrees](https://incident.io/blog/shipping-faster-with-claude-code-and-git-worktrees)
- [Git Worktrees with Claude Code Complete Guide](https://notes.muthu.co/2026/02/git-worktrees-with-claude-code-the-complete-guide/)

### 1.2 コミット・PR 作成のベストプラクティス

**何ができるか**: Claude Code にコミットメッセージの規約を守らせ、質の高い PR を自動作成させる。

**具体的な手順**:
```markdown
# CLAUDE.md に以下を記載
## Git 規約
- コミットメッセージ: `<type>(<scope>): <subject>`
- type: feat / fix / docs / refactor / test
- 小さく焦点を絞ったコミットを作成する
- git add は対象ファイルを明示的に指定（git add . は使わない）
```

```bash
# コミット作成
/commit  # 対話モードで自動的にメッセージ生成

# PR 作成（ブランチ名が説明的であること）
# Claude に「コミットして PR を作成して」と指示
# → セッションが PR にリンクされ、レビュー対応で再開可能
```

**メリット**:
- PR 作成時にセッションがリンクされ、レビューフィードバック対応時に同じコンテキストで再開可能
- CLAUDE.md にフォーマットを定義すれば一貫したコミットメッセージ

**ソース**:
- [Claude Code 公式ドキュメント: Best Practices](https://code.claude.com/docs/en/best-practices)
- [Claude Code GitHub: commit-push-pr.md](https://github.com/anthropics/claude-code/blob/main/.claude/commands/commit-push-pr.md)

### 1.3 Hooks（pre-commit 連携）

**何ができるか**: Claude Code の Hooks 機能で、コミット前にリンター・フォーマッター・テストを強制実行。失敗時は Claude が自動修正を試みる。

**具体的な手順**:
```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit*)",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/pre-commit-check.sh"
          }
        ]
      }
    ]
  }
}
```

```bash
# .claude/hooks/pre-commit-check.sh
#!/bin/bash
# テストが通っていなければブロック
if [ ! -f /tmp/agent-pre-commit-pass ]; then
  echo "テストを先に実行してください" >&2
  exit 2  # exit 2 = ブロック（Claude にメッセージが渡る）
fi
```

**使い分けの原則**:
| 手段 | 用途 | 例 |
|------|------|-----|
| CLAUDE.md | ガイドライン（破っても致命的でない） | 「Bun を優先」 |
| Hooks | ルール（絶対に破らせない） | 「Prettier でフォーマット」「.env に触れない」 |

**exit コードの意味**:
- `0`: 許可
- `2`: ブロック（stderr のメッセージが Claude に渡る）
- その他の非ゼロ: 非ブロックエラー（ユーザーに表示）

**ソース**:
- [Claude Code 公式ドキュメント: Hooks Guide](https://code.claude.com/docs/en/hooks-guide)
- [Claude Code Hooks: 20+ Examples](https://aiorg.dev/blog/claude-code-hooks)
- [Steve Kinney: Claude Code Hook Examples](https://stevekinney.com/courses/ai-development/claude-code-hook-examples)

---

## 2. テスト・CI 連携

### 2.1 TDD ワークフロー

**何ができるか**: Claude Code で Red-Green-Refactor サイクルを強制し、テスト駆動開発を実現。

**具体的な手順**:
```markdown
# CLAUDE.md に追加
## テスト方針
- 新機能は必ず「失敗するテストを先に書く → 実装 → リファクタリング」の順
- テスト名は振る舞いを記述する（例: test_should_return_error_when_invalid_input）
- AAA パターン（Arrange-Act-Assert）を使う
```

**重要な指示の仕方**:
```
# 明示的に TDD を指示する（これが重要）
「[機能] の失敗するテストを書いて。実装はまだ書かないで。」

# その後
「テストを実行して失敗を確認して。」
「テストが通る最小限の実装を書いて。」
```

**注意**: Claude は放っておくと実装を先に書く傾向がある。「テストを先に」「実装はまだ」と明示的に指示する。

**高度な方法**: [tdd-guard](https://github.com/nizos/tdd-guard) — Claude Code にTDD を強制する Hook ツール。テストなしで実装を書こうとするとブロックする。

**ソース**:
- [TDD with Claude Code Guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/guide/workflows/tdd-with-claude.md)
- [Forcing Claude Code to TDD](https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/)
- [tdd-guard: Automated TDD enforcement](https://github.com/nizos/tdd-guard)

### 2.2 GitHub Actions 連携（claude-code-action）

**何ができるか**: PR やイシューに `@claude` メンションするだけで、AI がコードレビュー・修正・実装を自動実行。

**具体的な手順**:
```bash
# 最も簡単なセットアップ方法
claude
# Claude Code 内で:
/install-github-app
# → GitHub App のセットアップとシークレット設定をガイド
```

```yaml
# .github/workflows/claude.yml（手動設定の場合）
name: Claude Code Action
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]
  pull_request:
    types: [opened, synchronize]

jobs:
  claude:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

**主な用途**:
- PR の自動コードレビュー
- イシューの自動トリアージ
- `@claude` でコード修正依頼 → 自動コミット
- リント修正、ドキュメント更新の自動化

**認証方法**: Anthropic API 直接 / Amazon Bedrock / Google Vertex AI / Microsoft Foundry に対応

**ソース**:
- [Claude Code Action (GitHub Marketplace)](https://github.com/marketplace/actions/claude-code-action-official)
- [Claude Code 公式ドキュメント: GitHub Actions](https://code.claude.com/docs/en/github-actions)
- [anthropics/claude-code-action (GitHub)](https://github.com/anthropics/claude-code-action)

### 2.3 ヘッドレスモード（CI/スクリプト統合）

**何ができるか**: 対話なしで Claude Code をスクリプトやCI パイプラインから実行。

**具体的な手順**:
```bash
# 基本的な非対話実行
claude -p "src/utils.py のユニットテストを書いて"

# JSON 出力（パイプライン向け）
claude -p "コードレビューして" --output-format json

# 追加指示を付与
claude -p "テスト実行" --append-system-prompt "pytest を使用。失敗時は exit 1"

# 前回のセッションを継続
claude -p "残りのテストも書いて" --continue

# 特定セッションを再開
claude -p "修正して" --resume SESSION_ID
```

**注意**: `/commit` や `/review` などのスラッシュコマンドはヘッドレスモードでは使えない。タスクを直接記述する。

**ソース**:
- [Claude Code 公式ドキュメント: Headless Mode](https://code.claude.com/docs/en/headless)
- [Claude Code Headless 解説](https://adrianomelo.com/posts/claude-code-headless.html)

---

## 3. コスト最適化

### 3.1 モデル選択戦略

**何ができるか**: タスクの複雑さに応じてモデルを切り替え、コストを60-80%削減。

**モデル別コスト・用途の目安**:

| モデル | API価格 (入力/出力) | 適するタスク |
|--------|---------------------|-------------|
| Opus 4.6 | $15/$75 | 複雑な設計判断、大規模コードベース分析、マルチエージェント |
| Sonnet 4.5 | $3/$15 | 日常的な開発作業の90%（デフォルト推奨） |
| Haiku 4.5 | $1/$5 | 軽量タスク、ワーカーエージェント |

**具体的な手順**:
```bash
# インタラクティブモードでモデル切り替え
/model sonnet       # Sonnet に切り替え
/model haiku        # Haiku に切り替え（簡単なタスク）
/model opus         # Opus に切り替え（複雑なタスク）

# OpusPlan モード（計画は Opus、実行は Sonnet）
# → 80-90% のコスト削減と高品質な設計判断を両立
```

**サブエージェントでの活用**:
```python
# 高コストタスクは Opus、低コストは Sonnet/Haiku
# CLAUDE.md または scaffolder の設定で:
# - researcher/analyst: デフォルト（Sonnet）
# - file-generator: Sonnet（明示指定）
# - 複雑な設計レビュー: Opus
```

**Sonnet + Haiku の組み合わせ**: オーケストレーター（Sonnet）+ ワーカー（Haiku）で全体コストを 2-2.5x 削減。

**ソース**:
- [Claude Code 公式ドキュメント: Model Configuration](https://code.claude.com/docs/en/model-config)
- [Claude Code Models: Choose the Right AI](https://claudefa.st/blog/models/model-selection)
- [Tactical Model Selection](https://claudelog.com/mechanics/tactical-model-selection/)

### 3.2 トークン使用量の監視

**何ができるか**: リアルタイムでコストを把握し、無駄な消費を防ぐ。

**具体的な手順**:
```bash
# セッション内でコスト確認
/cost    # 現在のセッションのトークン使用量・コストを表示

# 詳細ログを有効化
claude config set verbose true   # コンテキスト残量を常時表示

# 外部ツールで詳細分析
pip install ccusage
ccusage    # 日別のトークン消費量・コスト内訳を表示
```

**コスト目安**:
- 平均: $6/開発者/日
- 90%のユーザー: $12/日以下
- 月額: $100-200/開発者（Sonnet 4.5 中心）

**ソース**:
- [Claude Code 公式ドキュメント: Manage Costs](https://code.claude.com/docs/en/costs)
- [Claude Code Usage Monitor (GitHub)](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor)
- [Shipyard: Track Claude Code Usage](https://shipyard.build/blog/claude-code-track-usage/)

### 3.3 コンテキスト管理によるコスト削減

**何ができるか**: コンテキストウィンドウを効率的に管理し、トークンの無駄遣いを防ぐ。

**具体的な手順**:
```bash
# 手動コンパクション（70-75% で実行が理想）
/compact                          # 全体を要約
/compact "TODO一覧と変更ファイルは保持して"  # 保持する情報を指定

# セッション間のクリア
/clear                            # 無関係なタスクの間で実行

# 「Document & Clear」パターン（長時間タスク向け）
# 1. Claude に進捗を .md に書き出させる
# 2. /clear でコンテキストをリセット
# 3. 新セッションで「この .md を読んで続きをやって」
```

**CLAUDE.md でコンパクション動作をカスタマイズ**:
```markdown
# CLAUDE.md に追加
## コンパクション時のルール
- 変更したファイル一覧は必ず保持する
- テスト実行コマンドは保持する
- TODO リストの残項目は保持する
```

**ベストプラクティス**:
- Auto-compact（95%で自動発動）を待たない。70% で手動実行
- 無関係なタスクの合間に `/clear`
- CLAUDE.md は簡潔に保つ（200行超えたら見直す）
- この3つだけで 40-80% のコスト削減が報告されている

**ソース**:
- [Claude Code Compaction](https://stevekinney.com/courses/ai-development/claude-code-compaction)
- [Auto-Compact 解説](https://claudelog.com/faqs/what-is-claude-code-auto-compact/)
- [Context Window 管理ガイド](https://www.arsturn.com/blog/why-does-claude-forget-things-understanding-auto-compact-context-windows)

---

## 4. 便利なパターン・ベストプラクティス

### 4.1 Plan-First ワークフロー（計画→実行の分離）

**何ができるか**: 「いきなりコードを書く」のを防ぎ、まず計画を立てさせてから実装に移る。

**具体的な手順**:
```
# 方法1: 明示的に指示
「[要件] を実装したい。まず計画を立てて。コードはまだ書かないで。」
→ 計画を確認
「OK、実装して。」

# 方法2: Plan Mode（Shift+Tab で切り替え）
# Plan モードでは Claude がファイル変更せずに調査・計画のみ行う
```

**メリット**: Claude が間違った問題を解決するリスクを大幅に低減。大規模な変更ほど効果が高い。

**ソース**:
- [Claude Code 公式ドキュメント: Best Practices](https://code.claude.com/docs/en/best-practices)
- [InfoQ: Inside Claude Code Creator's Workflow](https://www.infoq.com/news/2026/01/claude-code-creator-workflow/)

### 4.2 検証基準の提示

**何ができるか**: Claude に「完了条件」を明示することで、出力品質を劇的に向上させる。

**具体的な手順**:
```
# 悪い例
「ログイン機能を実装して」

# 良い例
「ログイン機能を実装して。完了条件:
1. pytest tests/test_auth.py が全件パス
2. 無効なパスワードで 401 が返る
3. ログイン成功後に JWT トークンが発行される」
```

**メリット**: Claude が自分で検証できるため、精度が飛躍的に向上。Claude Code 公式が「最もレバレッジの高いプラクティス」と位置づけている。

**ソース**:
- [Claude Code 公式ドキュメント: Best Practices](https://code.claude.com/docs/en/best-practices)
- [How Claude Code's Creator Uses It](https://medium.com/@rub1cc/how-claude-codes-creator-uses-it-10-best-practices-from-the-team-e43be312836f)

### 4.3 CLI ツールの活用

**何ができるか**: 外部サービスとのやり取りに CLI ツールを使わせることで、コンテキスト効率を最大化。

**具体的な手順**:
```markdown
# CLAUDE.md に追加
## 外部サービス連携
- GitHub: `gh` コマンドを使う（gh pr, gh issue 等）
- AWS: `aws` CLI を使う
- GCP: `gcloud` CLI を使う
- Sentry: `sentry-cli` を使う
- Docker: `docker` / `docker compose` を使う
```

**メリット**: API ドキュメントを読ませるよりも CLI のほうがコンテキスト効率が良い。

**ソース**:
- [Claude Code 公式ドキュメント: Best Practices](https://code.claude.com/docs/en/best-practices)

### 4.4 カスタムスキル（スラッシュコマンド）

**何ができるか**: 繰り返し行うワークフローをスキルとして定義し、`/skill-name` で即座に起動。

**具体的な手順**:
```markdown
# .claude/skills/review/SKILL.md
---
description: "コードレビューを実行"
user_invocable: true
---

# コードレビュー
1. `git diff main...HEAD` で変更差分を確認
2. セキュリティ観点でチェック
3. パフォーマンス観点でチェック
4. 問題点と改善案をリストアップ
```

```bash
# 使い方
/review   # スキルが起動される
```

**スキルの種類**:
- `user_invocable: true` — ユーザーが `/name` で起動
- `user_invocable: false`（デフォルト）— Claude が文脈に応じて自動読み込み

**ソース**:
- [Claude Code 公式ドキュメント: Skills](https://code.claude.com/docs/en/skills)
- [awesome-claude-code (GitHub)](https://github.com/hesreallyhim/awesome-claude-code)
- [Production-ready slash commands collection](https://github.com/wshobson/commands)

### 4.5 よくある落とし穴と回避法

| 落とし穴 | 原因 | 回避法 |
|---------|------|--------|
| Claude が間違った問題を解く | いきなりコード生成を始める | Plan-First: 「まず計画して。コードはまだ書かないで。」 |
| セッション後半で品質低下 | コンテキストウィンドウが満杯 | 70% で `/compact`、無関係なタスク間で `/clear` |
| CLAUDE.md が肥大化 | 何でも書き足す | 各行に「これがないと Claude はミスするか？」と問う |
| セキュリティ脆弱性の混入 | AI生成コードの傾向 | 入力バリデーション・パスワード処理を明示的に指示 |
| 1セッションに複数タスクを詰め込む | コンテキスト汚染 | 1タスク1セッション。完了したら `/clear` |
| auto-compact で重要情報が消える | 95% で自動要約される | 70% で手動 compact（保持情報を指定） |
| サブエージェントの WebSearch が動かない | permissions.allow 未設定 | settings.json に静的許可 + Hook の2層構成 |

**ソース**:
- [Claude Code: Don't Use Before Reading This](https://medium.com/@erennaktas/dont-use-claude-code-before-reading-this-a-comprehensive-guide-to-productivity-and-safety-677df4decca3)
- [Claude Keeps Making the Same Mistakes](https://medium.com/@elliotJL/your-ai-has-infinite-knowledge-and-zero-habits-heres-the-fix-e279215d478d)
- [32 Claude Code Tips](https://agenticcoding.substack.com/p/32-claude-code-tips-from-basics-to)

---

## 5. すぐ使えるアクション一覧（優先度順）

### 即日導入可能

| # | アクション | コマンド/設定 | 期待効果 |
|---|----------|-------------|---------|
| 1 | `/cost` でコスト監視 | `/cost` | 使用量の可視化 |
| 2 | Sonnet をデフォルトにする | `/model sonnet` | コスト80%削減 |
| 3 | 70% で手動 `/compact` | `/compact "TODOと変更ファイルは保持"` | 品質低下を防止 |
| 4 | Plan-First を習慣化 | 「まず計画して」と指示 | 手戻り削減 |
| 5 | 検証基準を毎回提示 | 完了条件をリスト形式で記載 | 出力品質向上 |

### 1週間以内に導入

| # | アクション | 作業内容 | 期待効果 |
|---|----------|---------|---------|
| 6 | Git Worktree 並列開発 | `claude -w feature-name` | 並列作業の実現 |
| 7 | カスタムスキル作成 | `.claude/skills/` にSKILL.md配置 | 繰り返しワークフロー効率化 |
| 8 | Hooks でフォーマッター強制 | `.claude/settings.json` に Hook 定義 | コード品質の担保 |

### 将来的に検討

| # | アクション | 作業内容 | 期待効果 |
|---|----------|---------|---------|
| 9 | GitHub Actions 連携 | `/install-github-app` + ワークフロー定義 | PR レビュー自動化 |
| 10 | ヘッドレスモード活用 | `claude -p` でスクリプト統合 | CI/CD パイプライン自動化 |
| 11 | ccusage 導入 | `pip install ccusage` | 日別コスト分析 |
