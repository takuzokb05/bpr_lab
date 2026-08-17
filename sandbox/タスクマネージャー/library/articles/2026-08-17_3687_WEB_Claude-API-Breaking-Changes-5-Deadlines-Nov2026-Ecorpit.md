# Claude API Breaking Changes: 5 Deadlines to November 2026

- URL: https://ecorpit.com/claude-api-breaking-changes-august-2026-parameter-migration/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-17

## 要約

2026年8月から11月にかけてClaude APIで発生する破壊的変更5件と移行期限をまとめた技術記事。本日（8月17日）が初回の期限日となるWorkbench廃止が含まれており、API利用者は早急な対応が必要。

主な破壊的変更:
1. **Legacy Workbench廃止** (2026-08-17): platform.claude.com/workbenchへのアクセス終了。データは事前エクスポート要
2. **実験的プロンプトツールAPI廃止** (2026-08-17): /v1/experimental/generate_prompt、/v1/experimental/improve_prompt、/v1/experimental/templatize_prompt の3エンドポイント廃止
3. **パラメータ名変更** (〜2026-10-01): 旧パラメータ名は非推奨化（後方互換は一時継続）
4. **レガシーSDKバージョンサポート終了** (2026-11-01): anthropic-python < 0.40、anthropic-typescript < 0.30
5. **旧トークンカウントAPI廃止** (2026-11-15): /v1/tokenize エンドポイント → /v1/messages/count_tokens に移行

各変更の移行手順と確認チェックリストを提供。特にWorkbench廃止はプロンプト管理フローを持つチームへの影響大。
