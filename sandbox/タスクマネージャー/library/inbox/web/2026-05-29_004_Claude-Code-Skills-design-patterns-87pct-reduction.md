# Claude Code Skills設計パターン完全ガイド: SKILL.md肥大化87%削減の実践

- URL: https://www.playpark.co.jp/blog/claude-code-skills-design
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-05-29

## 要約
SKILL.mdが肥大化するとコンテキストトークンを大量消費し精度が低下する問題を、「決定論的処理はスクリプト化」の原則で87%削減した実践事例。元312行のSKILL.mdを42行まで削減。日付計算・ファイル確認・JSON生成などの決定論的処理はBashスクリプトに移し、自然言語記述はAI判断が必要な部分のみに限定する設計パターンを詳解。実装にはBash+jqを使用しmacOS/Linuxの両対応を確保。`get_next_date.sh`・`detect_mode.sh`・`orchestrate.sh`の完全動作サンプルを掲載。`set -euo pipefail`でエラーハンドリングを堅牢化。結果として月次エラーを80%削減、トークン効率化によるコスト削減も実現。SKILL.mdは「AIが判断すべきことのみを記述し、機械が計算できることはスクリプトへ」が核心原則。
