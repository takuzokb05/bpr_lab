# Claude APIがキーレス認証導入: AWS IAM/GCP/GitHub Actions/k8s/Entra ID/Okta対応

- URL: https://x.com/na0AaooQ/status/2051408465151901710
- ソース: x
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-05-04
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @na0AaooQ / フォロワー 518

## 投稿内容
ClaudeがAPIキーレス認証を導入するとのことです。

詳細は引用元 ならびに 引用元のコメント欄にあります、公式記事に記載されています。
https://t.co/LDpuMBxb2C

要約すると、Claude APIの認証について、以下の方式に移行できるもののようです。

長期APIキーを保存する方式
　↓
AWS IAM、GCP、GitHub Actions、Kubernetes(k8s)、Microsoft Entra ID、Oktaなどを使って、短期間のトークンを都度発行する方式

内部的には、JWT認証を利用するようですね。

## 要約
@na0AaooQ（フォロワー518）が解説。Claude Platformが長期APIキーの保存から短期トークン動的発行方式へ移行するWorkload Identity Federation機能を正式提供。対応プロバイダ: AWS IAM、GCP、GitHub Actions、Kubernetes (k8s)、Microsoft Entra ID、Okta。都度トークンを発行する方式でキー漏洩リスクを大幅削減。公式ドキュメント: https://platform.claude.com/docs/en/build-with-claude/workload-identity-federation。エンタープライズセキュリティ要件への対応として重要なアップデート。
