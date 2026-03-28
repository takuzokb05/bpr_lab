# How We Use Claude Code Skills to Run 1,000+ ML Experiments a Day (Hugging Face Blog / Sionic AI)

- URL: https://huggingface.co/blog/sionic-ai/claude-code-skills-training
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-28

## 要約

Sionic AIによるClaude Code Skillsの大規模ML運用実例。典型的な開発者ツール用途を超えた産業スケールでの活用：
- 1日1000件以上のML訓練実験を自動オーケストレートするスキルパイプライン構成
- GPU割り当て・訓練ジョブ起動・結果収集・比較レポート生成を単一スキルセットで自動化
- **スキルの連鎖実行**（skill-A → skill-B の自動引き継ぎパターン）の設計方法
- 並列実験実行時のコンテキスト分離（worktreeとスキルの組み合わせ）

「スキルはコーディング補助だけでなくMLOpsパイプライン自動化にも使える」という発想転換を促す事例。
