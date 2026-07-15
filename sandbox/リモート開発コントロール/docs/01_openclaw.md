## OpenClaw のアーキテクチャ・セットアップ手順

調査日: 2026-03-03

---

### 主要な発見

1. **OpenClaw とは何か**
   - 要点: OpenClaw は MIT ライセンスのオープンソース自律AIエージェント。WhatsApp, Telegram, Discord, Signal, iMessage 等のメッセージングアプリを通じて操作できる、自己ホスト型パーソナルAIアシスタント
   - データ/数字: GitHub スター約 199,000。ClawHub（スキルレジストリ）には 5,700 以上のスキルが登録済み
   - ソース: [OpenClaw GitHub](https://github.com/openclaw/openclaw), [OpenClaw 公式サイト](https://openclaw.ai/)

2. **アーキテクチャ（Gateway, Dashboard, Agent の関係）**
   - 要点:
     - **Gateway**: 常時稼働プロセス。WebSocket サーバーとして動作し、メッセージングプラットフォームと制御インターフェースに接続。チャネルセッションの保持、セッションルーティング、Control UI の提供、Canvas ホスト、エージェント協調を担当
     - **Agent Runtime**: AI ループを端から端まで実行。セッション履歴とメモリからコンテキストを組み立て、モデルを呼び出し、ツールコール（ブラウザ自動化、ファイル操作、Canvas、スケジュールジョブ等）を実行し、更新された状態を永続化
     - **Dashboard**: ゲートウェイヘルス、コスト、cron ステータス、アクティブセッション、サブエージェント実行、モデル使用量、git ログを一画面に集約。ローカルのみ、ログイン不要、クラウド不要
     - **チャネルアダプター**: 各チャネル（Telegram, Discord, WhatsApp, Slack, Signal, iMessage）はプラグイン形式の個別アダプターで、メッセージを共通フォーマットに正規化
   - ソース: [OpenClaw Architecture - Substack](https://ppaolo.substack.com/p/openclaw-system-architecture-overview), [Inside OpenClaw - DEV Community](https://dev.to/entelligenceai/inside-openclaw-how-a-persistent-ai-agent-actually-works-1mnk)

3. **Windows 対応状況**
   - 要点:
     - **公式サポート**: Windows 10/11 で動作可能だが、**WSL2 が強く推奨**される
     - **ネイティブ Windows**: 公式には「未テスト」で、Unix ドメインソケットやファイルシステム監視周りで互換性問題あり
     - **WSL1**: 非対応（OpenClaw が必要とするバックグラウンドデーモン systemd をサポートしていない）
     - **インストーラー**: Windows 用 PowerShell スクリプト `iwr -useb https://openclaw.ai/install.ps1 | iex` が提供されている
   - データ/数字: WSL2 環境での npm エラーの 40% がファイルパーミッションに起因
   - ソース: [Windows 11: WSL2 vs Native - GitHub Discussion](https://github.com/openclaw/openclaw/discussions/7462), [Deploy OpenClaw on Windows via WSL2 - Markaicode](https://markaicode.com/deploy-openclaw-windows-wsl2/)

4. **Telegram 連携の設定方法**
   - 要点:
     - BotFather で `/newbot` を実行し、ボットトークンを取得
     - 設定: `channels.telegram.botToken` にトークンを設定（または `channels.telegram.tokenFile` でファイルパス指定）
     - DM ポリシー: `pairing`（デフォルト）/ `allowlist` / `open` / `disabled`
     - グループポリシー: `open` / `allowlist`（デフォルト）/ `disabled`
     - アクセス制御: `channels.telegram.allowFrom` に数値の Telegram ユーザー ID を設定
     - `openclaw channels login telegram` は使用しない（config/env でトークンを設定してからゲートウェイを起動する方式）
     - ペアリングコードは1時間で期限切れ
   - ソース: [Telegram - OpenClaw Docs](https://docs.openclaw.ai/channels/telegram), [OpenClaw Telegram Setup Guide](https://www.getopenclaw.ai/help/telegram-bot-setup-guide)

5. **ClawPhone（Termux版）との違い**
   - 要点:
     - **OpenClaw**: PC/サーバー上で動作する完全版ゲートウェイ。全チャネル・全スキル対応
     - **ClawPhone**: Android スマートフォン上で OpenClaw を動作させるプロジェクト。Termux + tmux セッション内で稼働。$25 程度の安価な Android 端末でも動作
     - **ClawPhone の特徴**: スマートフォンのハードウェア（フラッシュライト、カメラ、センサー、通話、SMS）を直接制御可能。Termux:API と Termux:GUI を使用
     - **openclaw-termux**: Flutter アプリとしてのスタンドアロン版もあり、ターミナル・Web ダッシュボード・ワンタップセットアップを内蔵。proot 経由で Ubuntu 環境を構築（root 不要）
     - **制約**: Termux のネイティブ依存関係に問題があるため、proot-distro で Ubuntu 環境を作成する手法が一般的
   - ソース: [ClawPhone GitHub](https://github.com/marshallrichards/ClawPhone), [openclaw-termux GitHub](https://github.com/mithun50/openclaw-termux), [OpenClaw on Android](https://docs.openclaw.ai/platforms/android)

6. **必要な前提条件**
   - 要点:
     - **ランタイム**: Node.js >= 22（必須）
     - **メモリ**: 最小 2 vCPU / 4 GB RAM、推奨 4 vCPU / 8 GB RAM
     - **ストレージ**: 最小 40 GB SSD（Docker イメージだけで 2-8 GB）
     - **OS**: Ubuntu 22.04 LTS / Debian 12 推奨。Windows は WSL2 経由
     - **Docker**: 24+（VPS デプロイ時）
     - **ビルド手順**（ソースから）: `git clone` → `pnpm install` → `pnpm ui:build` → `pnpm build` → `pnpm openclaw onboard --install-daemon`
     - **推奨インストール**: `curl -fsSL --proto '=https' --tlsv1.2 https://openclaw.ai/install.sh | bash`（macOS/Linux）
   - ソース: [OpenClaw README](https://github.com/openclaw/openclaw/blob/main/README.md), [OpenClaw Install Docs](https://docs.openclaw.ai/install)

7. **既知の制限事項・セキュリティ Issues**
   - 要点:
     - **CVE-2026-25253（CVSS 8.8）**: Control UI が query string の gatewayUrl を検証なしで信頼。悪意のあるリンクをクリックするだけで RCE が可能。v2026.1.29 で修正済み
     - **GHSA-f7ww-2725-qvw2**: Node system.run の承認バイパス脆弱性（2026-02-26 公開）
     - **悪意あるスキル**: ClawHub 上で 1,184 以上の悪意あるスキルが確認。全 ClawHub スキルの 36% にプロンプトインジェクションが含まれる
     - **暴露されたインスタンス**: 30,000 以上のインターネット公開インスタンスが認証なしで稼働（Censys, Bitsight, Hunt.io が報告）
     - **設計上の制限**: API キーの暗号化なし、マルチユーザーアクセス制御なし、デフォルト設定でインスタンスがインターネットに公開される
     - **WSL2 固有**: ポートフォワーディング問題、Ollama 統合の検出エラー（v2026.2.26）
   - データ/数字: 1,467 の悪意あるペイロードが確認、うち 91% がプロンプトインジェクションと従来のマルウェア技術を組み合わせ
   - ソース: [OpenClaw Security - GitHub](https://github.com/openclaw/openclaw/security), [Bitsight Security Report](https://www.bitsight.com/blog/openclaw-ai-security-risks-exposed-instances), [Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/02/19/running-openclaw-safely-identity-isolation-runtime-risk/), [The Hacker News - CVE-2026-25253](https://thehackernews.com/2026/02/openclaw-bug-enables-one-click-remote.html), [Top 20 Problems - GitHub Discussion](https://github.com/openclaw/openclaw/discussions/26472)

---

### 情報の信頼性評価

- 一次ソース（公式・GitHub）: 8件
  - OpenClaw 公式 GitHub リポジトリ、README、Security ページ
  - OpenClaw 公式ドキュメント（docs.openclaw.ai）
  - GitHub Issues / Discussions
- 二次ソース（テックメディア・ブログ）: 6件
  - Microsoft Security Blog、Bitsight、The Hacker News、DEV Community、Substack
- 注意が必要な情報:
  - Windows ネイティブ対応状況は公式が「未テスト」としているため、実運用では WSL2 一択と見るべき
  - ClawHub のスキルはサプライチェーン攻撃のリスクが高い（36% にプロンプトインジェクション）
  - セキュリティ脆弱性は頻繁に発見されており、最新版への更新が必須

---

### ソース一覧

1. [OpenClaw GitHub Repository](https://github.com/openclaw/openclaw) - 公式リポジトリ
2. [OpenClaw 公式サイト](https://openclaw.ai/) - 公式
3. [OpenClaw README](https://github.com/openclaw/openclaw/blob/main/README.md) - 公式ドキュメント
4. [OpenClaw Install Docs](https://docs.openclaw.ai/install) - 公式インストールガイド
5. [Telegram - OpenClaw Docs](https://docs.openclaw.ai/channels/telegram) - 公式チャネル設定
6. [OpenClaw Security - GitHub](https://github.com/openclaw/openclaw/security) - 公式セキュリティ
7. [Windows 11: WSL2 vs Native - Discussion #7462](https://github.com/openclaw/openclaw/discussions/7462) - 公式 Discussion
8. [Top 20 OpenClaw Problems - Discussion #26472](https://github.com/openclaw/openclaw/discussions/26472) - 公式 Discussion
9. [ClawPhone GitHub](https://github.com/marshallrichards/ClawPhone) - コミュニティプロジェクト
10. [openclaw-termux GitHub](https://github.com/mithun50/openclaw-termux) - コミュニティプロジェクト
11. [Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/02/19/running-openclaw-safely-identity-isolation-runtime-risk/) - セキュリティ分析
12. [Bitsight Security Report](https://www.bitsight.com/blog/openclaw-ai-security-risks-exposed-instances) - セキュリティ分析
13. [The Hacker News - CVE-2026-25253](https://thehackernews.com/2026/02/openclaw-bug-enables-one-click-remote.html) - 脆弱性報告
14. [OpenClaw Architecture - Substack](https://ppaolo.substack.com/p/openclaw-system-architecture-overview) - アーキテクチャ解説
15. [Deploy OpenClaw on Windows via WSL2 - Markaicode](https://markaicode.com/deploy-openclaw-windows-wsl2/) - セットアップガイド
16. [OpenClaw Hardware Requirements - Boostedhost](https://boostedhost.com/blog/en/openclaw-hardware-requirements/) - ハードウェア要件
