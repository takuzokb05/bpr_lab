# Claude Code v2.1.236〜v2.1.237：ANTHROPIC_DEFAULT_MODEL・Concise出力スタイル追加

- URL: https://dev.classmethod.jp/en/articles/20260820-cc-updates-v2-1-237/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-20

## 投稿内容

DevelopersIO（クラスメソッド）による2026年8月20日付けClaude Code最新アップデート解説。v2.1.236（8月19日）とv2.1.237（8月20日）の主要変更点を網羅。

**v2.1.236の主な追加機能:**
- ANTHROPIC_DEFAULT_MODEL環境変数（新セッション開始モデルを設定。/modelコマンドで都度上書き可能かつ再起動後も維持。既存ANTHROPIC_MODELとの違いはこの永続性）
- notify_when_idle（cross-session SendMessageへの追加機能。他マシンのClaudeセッションがアイドルになったら通知。opt-in・one-shot設計、ポーリング不要。macOS/Linuxのみ）
- /permissionsを作業中に開けるよう改善（ルール変更が現ターン残りに即時適用）
- 組み込みclaude-apiスキルのコンテキストコストを~200Kトークン→~25Kに削減（参照ドキュメントをオンデマンドロードへ変更）

**v2.1.237の主な追加機能:**
- Concise出力スタイル（「作業は従来通り丁寧に、ただし結果を先頭に書き前置き・実況を省く」。/config → Output style → Concise で有効化。またはsettings.jsonに"outputStyle": "Concise"）
- LLMゲートウェイ・カスタムベースURL利用時のプロンプトキャッシュバグ修正
- VSCodeスクリーンリーダー対応（ライブアナウンス・見出しナビゲーション追加）
- macOSサンドボックスセキュリティ強化（ファイル保護向上）

## 要約

Claude Code v2.1.236〜237の実用的アップデート2点が特に重要。①ANTHROPIC_DEFAULT_MODELは既存環境変数との使い分けが必要な設計で、モデルのデフォルト固定とセッション単位の上書きを両立する。②Concise出力スタイルは長年の要望だった「実況コメント削減」を解決する機能で、グローバル設定には settings.json への記述が必要（/config は現プロジェクト限定）。また claude-api スキルのコンテキスト削減（200K→25K）は長期セッションでの費用対効果向上に直結する実質的な改善。LLMゲートウェイ経由のプロンプトキャッシュ修正も、カスタム環境利用者には重要な bugfix。
