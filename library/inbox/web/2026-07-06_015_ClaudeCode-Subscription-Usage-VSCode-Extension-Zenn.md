# Claude Code のサブスク使用状況を VSCode で「常時可視化」する拡張機能を作った

- URL: https://zenn.dev/minedia/articles/17a07dc1ce4f12
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-07-06

## 要約
Claude Code の週次使用量・残量をリアルタイムで VSCode ステータスバーに表示する拡張機能の開発記録。Claude Code v2.1+ の `/usage` コマンドが返す JSON を定期ポーリングし、残りトークン・コスト・リセット時刻を可視化。6月の料金体系変更（Agent SDK 分離課金）後、予算管理の重要性が増したことが開発動機。拡張機能のアーキテクチャ・ポーリング間隔の設計・VSCode Extension API との接続方法を詳述。GitHub で OSS 公開済み。Claude Code ヘビーユーザーの実用ツールとして再現性が高い。
