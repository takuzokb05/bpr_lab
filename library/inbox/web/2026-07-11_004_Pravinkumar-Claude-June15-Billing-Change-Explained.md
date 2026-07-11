# Claude June 15 Billing Change Explained: Interactive vs Automated Usage

- URL: https://www.pravinkumar.co/blog/claude-june-15-billing-change-explained-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-11

## 要約
2026年6月15日のClaude課金変更を開発者視点で解説。変更内容：自動エージェント使用（Claude Agent SDK、ヘッドレスClaude Code、GitHub Actions、サードパーティエージェント）が月次クレジット制に移行、APIレートで課金。インタラクティブなClaude.aiチャットとターミナルセッションは既存サブスクリプションのまま。プラン別クレジット割り当て：Pro約$20/月、Max 5x約$100、Max 20x約$200。クレジット繰越なし、上限到達後はAPI標準料金。背景：サブスクリプションが重い自動使用を推定15〜30倍補助していたため。影響対象：CI/CDパイプライン、スケジュールcronジョブ、ビルドシステム、ボット実装。推奨対応：①プロンプトキャッシュとコンテキスト最適化②重い処理を直接APIキーへ移行③トークン使用量モニタリング導入。
