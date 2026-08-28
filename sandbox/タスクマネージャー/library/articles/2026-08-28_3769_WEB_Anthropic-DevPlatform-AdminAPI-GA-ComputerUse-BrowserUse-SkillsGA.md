# Anthropic Developer Platform 8月2026：Computer Use GA・Browser Useツールセット・Admin API正式化

- URL: https://releasebot.io/updates/anthropic/claude-developer-platform
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-28

## 投稿内容
Releasebot compilation of Anthropic Claude Developer Platform updates for August 2026:

**API Status Changes**:
- **Computer Use → GA**: `computer_toolset_20260801` (beta ended). Batch action support, zoom enabled by default
- **Browser Use → New**: `browser_toolset_20260801` for driving hosted browsers. Element references, form input, tab management, download reporting
- **Files API → GA**: No longer requires `files-api-2025-04-14` beta header. New expiration controls and pagination
- **Skills API → GA**: No longer requires `skills-2025-10-02` beta header
- **anthropic-workspace-id header**: New response header carrying the `wrkspc_`-prefixed workspace ID

**SDK Updates (Aug 27)**: Python 1.2.0, TypeScript 0.122.0, Go 1.68.0 no longer send beta headers for files/skills APIs. `BetaSkill` renamed `BetaContainerSkill`. Skill deletion removes all versions simultaneously.

**Admin API GA**: User management endpoints (members, invites, groups, custom roles) for Claude Enterprise are now GA. `anthropic-beta` header no longer required. Available across CLI + 7 SDKs via `client.beta.organization`.

**Pricing finalized**:
- Sonnet 5: $2/$10 per MTok—introductory price is now permanent (no Sept 2026 increase)
- Opus 5: $5/$25 per MTok, 1M context, 128k max output, thinking enabled by default

**Managed Agents additions**: Budget controls, advisor support, geo-pinned inference, GitHub-loaded skills. Inference hooks (beta) for Enterprise AI security server approval workflows.

## 要約
Anthropic Developer Platform 2026年8月主要アップデートをReleasebotが集計。重要変更：①Computer Use正式GA（`computer_toolset_20260801`、バッチアクション対応、ズームデフォルト有効）②Browser Use新ツールセット（`browser_toolset_20260801`、要素参照・フォーム入力・タブ管理）③Files API beta終了（有効期限制御・ページネーション追加）④Skills API beta終了⑤anthropic-workspace-idレスポンスヘッダー追加（wrkspc_プレフィックスID）。SDK: Python 1.2.0等がbetaヘッダー自動排除、BetaSkill→BetaContainerSkillリネーム。Admin API GA（メンバー・招待・グループ・カスタムロール管理）。価格確定：Sonnet 5の$2/$10は永続化（9月値上げなし）、Opus 5は$5/$25で確定。Claude Opus 5は1Mコンテキスト・128k最大出力・思考モードデフォルト有効。Computer Use・Browser Use・SkillsのAPIがすべてbeta卒業し、本番組み込みの条件が整った。
