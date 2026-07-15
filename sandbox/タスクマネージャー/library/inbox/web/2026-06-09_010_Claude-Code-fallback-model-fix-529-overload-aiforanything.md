# Claude Code fallbackModel設定で529過負荷エラーを撃退する実践ガイド

- URL: https://www.aiforanything.io/blog/claude-code-fallback-model-overload-fix-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-09

## 要約
v2.1.166（2026年6月6日）で追加されたfallbackModel設定の実践ガイド。最大3つのバックアップモデルを順番に設定可能。529過負荷エラー時に自動でフォールバック（ユーザー操作不要）。設定例：`{"model":"claude-sonnet-4-6-20260620","fallbackModel":["claude-haiku-4-5-20251001"]}`。トリガー条件：過負荷・予期しない非リトライエラー（認証/レートリミット/転送エラーは即座に表面化）。バックグラウンドセッション（/bg、--detach）もフォールバック設定を継承。--fallback-model CLIフラグはinteractiveセッションでは無効、printモード・バックグラウンドで有効。エージェントの長時間セッション品質が大幅向上。
