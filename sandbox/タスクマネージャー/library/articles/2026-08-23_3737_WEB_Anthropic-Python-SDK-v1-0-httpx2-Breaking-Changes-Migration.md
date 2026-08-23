# Anthropic Python SDK v1.0.0 正式リリース：httpx2移行・Text Completions廃止

- URL: https://github.com/anthropics/anthropic-sdk-python/releases
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-23

## 投稿内容

Anthropic Python SDK v1.0.0 GitHubリリースページ（2026-08-20公開）。v1.0.0は長らく予告されてきたメジャーバージョンアップ。

## 要約

**リリース日：2026年8月20日（v0.125.0から昇格）**

**Breaking Changes（既存コードへの影響あり）：**
1. HTTPレイヤーがhttpx → **httpx2**に移行（API互換フォーク、独自移行ステップあり）
2. **Python 3.10+必須**（3.9以下サポート終了）
3. 長期非推奨だった**Text Completions API完全削除**
4. Messagesメソッドの`temperature`・`top_p`・`top_k`パラメータ削除
5. asyncクライアントの`.with_raw_response`結果に`await response.parse()`が必要

**新機能（v0.124〜0.125で追加済みをv1.0でGA）：**
- Files API・Skills API 正式GA
- コンピュータ使用ツール・ブラウザ使用ツールセット
- マネージドエージェントのウェブ検索設定とself-hostedサンドボックスメモリ対応

**移行方法：**
- MIGRATION.md に全変更のBefore/After解説あり
- Claude Code v2.1.239の`/claude-api upgrade`コマンドで0.x→1.x移行を半自動化可能
- `pip install --upgrade anthropic` でv1.0.0に更新

**実務上の注意：** 既存の0.xベースのWrapperやClaude Code関連スクリプトは要確認。特にasync利用者の`.with_raw_response`変更とhttpx2移行は影響範囲が広い。
