# Claude Skills Tutorial: Build Your First SKILL.md in 10 Minutes

- URL: https://techsy.io/en/blog/claude-skills-tutorial
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-11

## 要約
Claude Skillsの構造と作り方を10分でカバーするチュートリアル。Skillは`~/.claude/skills/<name>/SKILL.md`に配置するフォルダで、YAMLフロントマター（name, description）＋本文で構成。2種類：ユーザー呼び出し型（`disable-model-invocation: true`でスラッシュコマンド専用）とモデル自動呼び出し型（プロンプトが説明フィールドにマッチすると自動ロード）。配置場所は個人（`~/.claude/skills/`）、プロジェクト（`.claude/skills/`、git共有）、プラグイン、エンタープライズ。最重要ポイント：「Claudeのために書く、人間向けではない」—曖昧な説明はトリガーに失敗する。具体的フレーズ例："when the user asks for a plain-English code walkthrough"。スキルはトークンコスト最小化のためロードオンデマンドで動作。
