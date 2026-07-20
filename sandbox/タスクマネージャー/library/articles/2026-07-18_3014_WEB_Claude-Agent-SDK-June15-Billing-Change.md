# Claude Agent SDK課金変更（6/15）・API大幅強化：独立クレジット制・全言語コード実行対応

- URL: https://releasebot.io/updates/anthropic/claude-developer-platform
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-18

## 投稿内容
2026年6月15日からClaude Agent SDK（旧Claude Code SDK、2026年初頭に改名）が独立した月次エージェントSDKクレジットから課金開始。SDK需要は「claude agent sdk」月次検索で2025年5月の50件→2026年4月の14,800件（約50,000%増）。同時期のAPI強化：(1) SonnetとHaikuのレートリミットをOpus水準に統一（3ティア：Start/Build/Scale）、(2) APIキー有効期限設定（作成時にプリセット/カスタム/Never選択）、(3) コード実行ツール（code_execution_20260120：REPLステート永続化、プログラマティックツールコール最小バージョン）をPython/TS/Go/Java/Ruby/PHP/C#全SDK対応、(4) Enterprise向け管理者API：メンバー管理・ロール変更・グループ管理をAPI経由で可能に。

## 要約
Claude Agent SDKは独立課金化されたことで本格的なプロダクト扱いに格上げ。APIレートリミット統一・コード実行ツール全言語対応・企業向け管理API追加など、エンタープライズ採用を加速させる変更が重なった。Claude Codeのスキル/フックでコード実行を呼ぶ場合は最新SDK・code_execution_20260120への更新が必要。
