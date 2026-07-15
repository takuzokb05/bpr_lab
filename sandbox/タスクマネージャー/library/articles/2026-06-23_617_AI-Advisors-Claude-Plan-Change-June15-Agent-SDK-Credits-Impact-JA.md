# 【解説】Claude有料プラン変更 2026年6月15日〜「対話」と「自動化」の課金分離

- URL: https://ai-advisors.jp/media/ai-news/claude-plan-change-20260615/
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-06-23

## 要約
AI顧問社によるClaude課金体系変更（2026年6月15日）の日本語解説。重要変更：Claude Agent SDK・`claude -p`（非対話型）利用が対話型利用制限とは別の「Agent SDKクレジット」から引き落とされる。プランごとのAgent SDKクレジット月額：Pro $20・Max 5x $100・Max 20x $200・Team（組織管理者設定）。クレジット枯渇後は標準APIレートへフォールバック（有効化時のみ）。通常の対話型Claude Code・Claude Cowork・Claudeには影響なし。日本ユーザーへの影響：APIを組み込んだ自動化ツール・バッチ処理・定期実行スクリプトがAgent SDK扱いになるため月間使用量の再計算が必要。移行前後の課金差異シミュレーション例と推奨対応手順を提示。本ライブラリで管理する日次収集スクリプトも該当するため要確認。
