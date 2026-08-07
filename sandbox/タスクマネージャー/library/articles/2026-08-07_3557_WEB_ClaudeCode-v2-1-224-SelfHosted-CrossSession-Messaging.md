# Claude Code v2.1.224: 自己ホスト環境とセッション間メッセージングが正式追加

- URL: https://dev.classmethod.jp/en/articles/20260807-cc-updates-v2-1-224/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-07

## 要約

Claude Code v2.1.224（2026-08-06リリース）で2つの大型機能が追加された。

**Self-Hosted Environments（パブリックβ）**: セッションをAnthropicホスト基盤ではなく自組織のインフラ上で実行できる。Web・モバイル・デスクトップ・ルーティンから起動し、内部ネットワーク・セキュリティコントロール内で動作。リポジトリ・ビルド成果物・秘密情報・生成ファイルはすべて組織が管理するマシン上に留まる。Claude TeamおよびEnterpriseプラン向け、デフォルトはオフ。

**Cross-Session Messaging（macOS/Linux）**: Claude Codeセッション間でメッセージを送受信できる`SendMessage`ツールと、送信先を探す`ListAgents`ツールが追加。設定項目として`crossSessionInbound`と`dialogExpiry`が追加され、bypassPermissionsで送られたメッセージは承認待ちに、それ以外は自動配信される。

その他の修正: サブエージェントspawnキャップ（200件/セッション）を削除（長期セッションで制限なし）、セッションコストのテレメトリ二重カウント修正、`claude update`/`claude doctor`がサイレントハングするバグ修正、MCP一時エラー修正、メモリフロントマター値の切り捨て修正。

**なぜ重要か**: 自己ホストにより企業はAIエージェントをセキュリティ境界内に留められる。セッション間メッセージングはマルチマシン・マルチエージェント協調の基盤となる。
