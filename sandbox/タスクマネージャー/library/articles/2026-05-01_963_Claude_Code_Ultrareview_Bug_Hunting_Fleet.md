# Claude Code /ultrareview: クラウド上のバグハンティングエージェント群

- URL: https://howaiworks.ai/blog/claude-code-ultrareview-agentic-code-analysis
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-01

## 要約
2026年4月16日にOpus 4.7と同時リリースされたClaude Code v2.1.86以降の新機能`/ultrareview`の詳細解説。構文チェックを超えた深層ロジック欠陥・セキュリティ脆弱性発見を目的とする。4専門エージェント（Logic Specialist・Security Auditor・Performance Optimizer・Verification Lead）がクラウドサンドボックスで並列稼働し、再現可能性を確認した発見事項のみレポートする検証優先設計。偽陽性を大幅削減。Pro/Maxユーザーは3回無料試用（2026-05-05まで）、以降$5〜$20/回。引数なしで現ブランチ↔デフォルトブランチのdiff全体を対象。大規模リポジトリはdraft PR作成後に`/ultrareview <PR番号>`推奨。認証にはAPI KeyではなくClaude.aiアカウントが必要（`/login`で設定）。
