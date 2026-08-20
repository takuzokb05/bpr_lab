# Claude Code v2.1.236〜v2.1.237 主要アップデート：ANTHROPIC_DEFAULT_MODEL・Concise出力スタイル追加

- URL: https://dev.classmethod.jp/en/articles/20260820-cc-updates-v2-1-237/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-20

## 要約

DevelopersIO（クラスメソッド）による2026年8月20日公開のClaude Code v2.1.236〜v2.1.237アップデート解説。

主な追加機能: ①**ANTHROPIC_DEFAULT_MODEL環境変数** — 既存ANTHROPIC_MODELとの違いは「新セッションの開始モデルを指定するが、/modelコマンドで都度上書き可能かつ再起動後も維持される」点。②**notify_when_idle機能** — cross-session SendMessageに追加された、他セッションがアイドルになったら通知を送る機能（macOS/Linux、opt-in・one-shot設計でポーリング不要）。③**Concise出力スタイル** — /config→Output style→Concise で有効化。作業の詳細さは変わらず「結果を先に書き、前置きや実況を省く」スタイル。settings.jsonに "outputStyle": "Concise" と書けばグローバル適用。④**プロンプトキャッシュ修正** — LLMゲートウェイやカスタムベースURL利用時のキャッシュバグ修正。⑤**スクリーンリーダー対応** — VSCodeでのライブアナウンス・見出しナビゲーション追加。⑥**macOSサンドボックス強化** — ファイル保護セキュリティ向上。重要な制約: Concise出力スタイルの変更は /clear または新セッション開始後に有効になる。
