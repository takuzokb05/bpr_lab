# Claude Sonnet 5 Developer Guide: Migration, API Changes, and Effort Levels

- URL: https://www.developersdigest.tech/blog/claude-sonnet-5-developer-guide-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-13

## 要約
Developers Digestによる開発者向けClaude Sonnet 5移行ガイド。3つのAPIの破壊的変更、新effortパラメータの使い方、トークン消費量の変化を詳細に解説。

**APIの破壊的変更（3件）**:
1. **サンプリングパラメータ削除**: `temperature`・`top_p`・`top_k`をデフォルト以外の値に設定すると400エラー（Adaptive Thinkingの品質向上のため廃止）
2. **Extended Thinking（manual）廃止**: `budget_tokens`パラメータ削除。代わりに`effort`パラメータに移行
3. **Adaptive Thinkingがデフォルトで有効**: Sonnet 4.6と異なり、デフォルトで"high"effortで動作（トークン消費・動作パターンが変化）

**新effortパラメータ（effort levels）**:
- `low`: 大量処理・単純分類タスク向け
- `medium`: コスト重視・Sonnet 4.6相当の品質
- `high`（デフォルト）: 複雑推論・コーディング・エージェントタスク
- `max` / `xhigh`: 最大推論能力（困難な問題向け）

**トークン変化への注意**:
- 同じテキストでSonnet 4.6比1.0〜1.35倍のトークンを消費（平均約30%増）
- 既存プロンプトのトークン再カウントと予算30%追加が必要

**価格**:
- プロモーション価格（〜2026年8月31日）: $2/$10/Mトークン
- 標準価格: $3/$15/Mトークン
- トークン増加分をプロモ価格がほぼ相殺するためコスト中立な移行

**パフォーマンス**:
- SWE-Bench Verified: 85.2%（一部コーディングベンチマークでOpus 4.8を上回る）
