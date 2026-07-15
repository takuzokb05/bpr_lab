settings.local.json の一回限りエントリを検出し、汎用パターンへの置き換えを提案する。定期メンテナンス用。

## タスク

このプロジェクトの `.claude/settings.local.json`（なければユーザーの `~/.claude/settings.local.json`）を読み、allowリストを分析してください。

## 分析の手順

1. **settings.local.json を読む**
2. allow リスト内の各エントリを以下に分類する:

### カテゴリA: 汎用パターン（残すべき）
ワイルドカード付きの再利用可能なパターン:
- `Bash(git commit:*)`, `Bash(python:*)`, `WebSearch` 等

### カテゴリB: 一回限りエントリ（置き換え候補）
特定のパス・コマンド・メッセージがハードコードされたもの:
- `Bash(cd "C:/specific/path" && mv ...)` — 特定パスのファイル移動
- `Bash(git commit -m "specific message")` — 特定コミットメッセージ
- `Bash(del "C:\\specific\\path")` — 特定ファイル削除
- `WebFetch(domain:specific-domain.com)` — 一回だけアクセスしたドメイン

### カテゴリC: 追加すべき汎用パターン（不足している）
agent-governance.md の設計思想に基づき、あるべきだが無いパターン:
- 読み取り系: `Bash(cat:*)`, `Bash(head:*)`, `Bash(wc:*)`, `Bash(ls:*)`
- Git安全: `Bash(git commit:*)`, `Bash(git add:*)`, `Bash(git branch:*)`
- テスト: `Bash(pytest:*)`, `Bash(ruff:*)`

## 出力フォーマット

```
## settings.local.json 分析結果

### 現状
- 全エントリ数: N
- 汎用パターン（カテゴリA）: N
- 一回限り（カテゴリB）: N

### 削除候補（カテゴリB）
| # | エントリ | 理由 |
|---|---------|------|
| 1 | `Bash(cd "C:/..." && mv ...)` | 特定パスの一回限り操作 |

### 追加推奨（カテゴリC）
| # | パターン | 理由 |
|---|---------|------|
| 1 | `Bash(git commit:*)` | 汎用Git操作。毎回許可が不要になる |

### 提案するクリーンな allow リスト
\```json
[
  // ここにクリーンなリストを出力
]
\```
```

## 注意
- deny リストは変更提案しない（安全側に倒す）
- WebFetch のドメインは、3回以上アクセスしたドメインのみ汎用化を提案
- 提案を実行するかはユーザーに委ねる（自動で書き換えない）
