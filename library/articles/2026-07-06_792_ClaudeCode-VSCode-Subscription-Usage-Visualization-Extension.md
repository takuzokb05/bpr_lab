# Claude Code のサブスク使用状況を VSCode で常時可視化する拡張機能を作った

- URL: https://zenn.dev/minedia/articles/17a07dc1ce4f12
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-07-06

## 投稿内容
Claude Code の週次使用量・残量をリアルタイムで VSCode ステータスバーに表示する拡張機能の開発記録。Claude Code v2.1+ の /usage コマンドが返す JSON を定期ポーリングし、残りトークン・コスト・リセット時刻を可視化。6月の料金体系変更（Agent SDK 分離課金）後、予算管理の重要性が増したことが開発動機。拡張機能のアーキテクチャ・ポーリング間隔の設計・VSCode Extension API との接続方法を詳述。GitHub でOSS公開済み。

## 要約
Claude Code の週次使用量をリアルタイムで VSCode ステータスバーに表示する拡張機能の開発記録。/usage コマンドの JSON を定期ポーリングして残りトークン・コスト・リセット時刻を可視化。6月の料金体系変更（Agent SDK 分離課金）後の予算管理ニーズに応えた実用ツール。拡張機能のアーキテクチャ・ポーリング設計・VSCode Extension API との接続方法を詳述し、GitHub でOSS公開済み。Claude Code ヘビーユーザーの予算管理に直接役立つ実践的ツール開発記録。
