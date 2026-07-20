# Anthropic Memory API beta（agent-memory-2026-07-22）& HIPAA自己設定機能

- URL: https://releasebot.io/updates/anthropic/claude-developer-platform
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-20

## 投稿内容
Two new developer platform features from Anthropic in July 2026.

**Memory API Beta Header (agent-memory-2026-07-22):** Changes memory listing behavior to return results in a stable server-defined order, restricts depth parameters to only 0, 1, or being omitted, and requires path_prefix to end with / and match whole path segments.

**Self-serve HIPAA Configuration:** Allows eligible Enterprise and API organization admins to review the Business Associate Agreement, download the implementation guide, and enable HIPAA configuration in a single flow — without going through sales.

## 要約
AnthropicのClaude Developer Platformに2つの新機能追加。(1) **Memory API betaヘッダ（agent-memory-2026-07-22）**：メモリ一覧をサーバー定義の安定した順序で返すよう変更、depthパラメータを0・1・省略のみ許可、path_prefixに`/`終端・全パスセグメント一致を必須化。エージェントメモリ一覧取得挙動の一貫性向上で、複数エージェントのメモリ管理が安定化。(2) **HIPAA自己設定**：Enterprise/API組織の管理者がBAA確認→実装ガイドDL→HIPAA有効化を単一フローで完結。医療・ヘルスケア向けClaude本番利用の導入ハードルが大幅低下。エンタープライズ展開加速を示す機能セットで、特に医療AIエージェント構築者にとって重要な変更。Memory APIのbetaヘッダは既存統合で動作が変わる可能性があるため要確認。
