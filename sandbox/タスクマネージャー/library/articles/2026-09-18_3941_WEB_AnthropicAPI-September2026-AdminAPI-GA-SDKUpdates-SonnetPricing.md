# Anthropic Developer Platform September 2026: Admin API GA・SDK更新・Sonnet価格確定

- URL: https://releasebot.io/updates/anthropic/claude-developer-platform
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-18

## 投稿内容
Key Anthropic developer platform updates September 2026:

1. **Admin API GA**: User-management endpoints for Claude Enterprise orgs (members, invites, groups, custom roles) out of beta.
2. **anthropic-workspace-id header**: New response header carrying the wrkspc_-prefixed workspace ID.
3. **SDK code_execution support**: Python, TypeScript, Go, Java, Ruby, PHP, C# SDKs now support code_execution_20260120 with REPL state persistence.
4. **SDK naming change**: BetaSkill → BetaContainerSkill; skill deletion behavior updated.
5. **Sonnet 5 pricing confirmed**: $2/$10 per MTok is now the permanent price; previously scheduled Sep 1 increase cancelled.
6. **Claude Code v2.1.270**: Fixed git commands unexpectedly asking for permission in long sessions.

Also: Claude Fable 5.1 cache read pricing dropped to $0.25/MTok.

## 要約
Anthropic Developer Platformの2026年9月主要変更点まとめ。Admin APIがベータ卒業しエンタープライズ組織管理が正式機能に。全主要言語SDKがcode_execution_20260120（REPL状態持続）をサポートし、コード実行ツールの実用性が向上。BetaSkill→BetaContainerSkillのリネームと削除動作変更はSDKアップグレード時の破壊的変更として注意が必要。Claude Sonnet 5の2$/10$/MTokが恒久価格として確定し、値上げ懸念が解消。Fable 5.1のキャッシュリード価格が$0.25/MTokに低下。APIを利用した長期プロジェクトのコスト計算が安定する。
