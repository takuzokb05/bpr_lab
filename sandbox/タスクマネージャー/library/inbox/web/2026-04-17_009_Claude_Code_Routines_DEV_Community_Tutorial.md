# Claude Code Routines: スケジュール・API・GitHubイベントで自律タスク自動化チュートリアル

- URL: https://dev.to/onsen/claude-code-routines-automate-dev-workflows-4ijn
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-17

## 要約
DEV Communityに投稿されたClaude Code Routinesの実践チュートリアル。Routinesの3つのトリガー方式：(1)スケジュール—cron式で毎朝テストスイート実行・毎日コードベースの依存性チェックなど；(2)APIトリガー—外部システムからHTTP POSTでRoutineを起動、CI/CDパイプラインからの呼び出しに対応；(3)GitHubイベント—PR作成時・コミットプッシュ時に自動実行。構成要素：プロンプト（自然言語の指示）＋リポジトリ（1つ以上）＋コネクタ（GitHub・外部APIなど）。具体的ユースケース：①毎朝「オープンPRを確認して古いブランチをレポートする」Routine；②PR作成時に「コードレビューとテスト提案を実施」するRoutine；③週次「技術的負債のホットスポットを分析」Routine。制限：Pro 5件/日、Max 15件/日、Team/Enterprise 25件/日。ターミナル不要でCloud上で実行されるためMac/PCをオフにしても継続。
