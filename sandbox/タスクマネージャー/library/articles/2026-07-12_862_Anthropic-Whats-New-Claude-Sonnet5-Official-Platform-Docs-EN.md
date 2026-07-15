# What's New in Claude Sonnet 5 - Official Anthropic Platform Documentation

- URL: https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-12

## 要約
Anthropic公式ドキュメントによるClaude Sonnet 5（2026年6月30日リリース）の変更点・技術仕様まとめ。

**技術仕様（新機能）**:
- 1Mトークンコンテキストウィンドウをデフォルトサポート（128k最大出力トークン）
- Adaptive Thinkingがデフォルトで有効化
- 手動extended thinkingは廃止（設定すると400エラー）
- サンプリングパラメータを非デフォルト値に設定すると400エラー（API互換性注意）

**セキュリティ**:
- リアルタイムサイバーセキュリティセーフガードを初搭載（Sonnet tierで初）
- 禁止・高リスクサイバーセキュリティトピックのリクエストを自動拒否

**位置づけ**:
- 「最もAgenticなSonnetモデル」: 計画立案・ツール操作・マルチステップタスクの自律実行が強化
- Opus 4.8に近い性能を大幅に低いコストで提供

**価格（一次情報）**:
- プロモーション価格（〜2026年8月31日）: 入力$2/Mトークン・出力$10/Mトークン
- 通常価格（9月1日〜）: 入力$3/Mトークン・出力$15/Mトークン

**Claude Codeへの影響**: デフォルトモデルがSonnet 5に更新済み。FX自動取引（P-007・P-033）のモデル指定も更新を検討。
