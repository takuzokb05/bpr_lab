# Claude Code Sessions Can Now Run on Your Own Infrastructure — Official Blog

- URL: https://claude.com/blog/run-claude-code-sessions-on-your-own-compute
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-07

## 要約

Anthropic公式ブログによるSelf-Hosted Environments機能の解説。

**背景**: 企業がAIエージェントを採用する上での最大障壁の一つは「コードとデータをAIプロバイダーのインフラ上で動かすこと」への抵抗。特に金融・医療・政府・防衛など機密データを扱うセクターで顕著。

**仕組み**: Claude Code webランチャーが組織のプロビジョニングしたマシン上でセッションを起動。セッション中に生成・変更されたすべてのファイル、秘密情報、ビルド成果物はAnthropicサーバーに送信されない。Claude Team/Enterpriseプランが対象。

**ユースケース例**:
- 内部APIキーを使うスクリプト実行
- プライベートリポジトリへのアクセス
- VPN内サービスとの連携
- 規制要件（SOC2, HIPAA等）対応

**Unite.AI補足分析**: この機能により「AIコーディングツールはSaaSオンリー」という前提が崩れ、オンプレ志向の大企業への普及が加速する見込み。Unite.AIはAnthropicがこれを「エンタープライズ獲得の決定打」と位置づけていると分析。

**なぜ重要か**: FX自動取引や社内業務ツール開発でも、API鍵や取引データをAnthropicに送らずにClaude Codeエージェントを使えるようになる。
