# codex/claude codeでhtmlレポート作成をリッチにするプラグインを公開

- URL: https://x.com/u1/status/2065832522198761650
- ソース: drop
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-07-16
- いいね: 852 / RT: 74 / リプライ: 5 / views: 230764
- 投稿者: @u1（Yuichi Uemura）

## 投稿内容
codex/claude codeでhtmlレポート作成をリッチにするプラグイン「reviewable-html-workbench」を公開。Notionのように成果物のHTMLへインラインでコメントを入れ、それをAIが読んで直す（レビュー→修正）ワークフローをローカルで実現できる。
リポジトリ: https://github.com/u-ichi/reviewable-html-workbench
（説明: Claude Code / Codex CLI plugin for generating reviewable HTML documents with preview, inline review comments, and agent feedback ingestion）

## 要約
Claude Code / Codex CLI 向けの OSS プラグイン。AIが生成したHTMLレポート／ドキュメントに対し、①プレビュー表示、②Notion風のインラインレビューコメント付与、③そのコメントをエージェントが取り込んで修正、というレビュー駆動のローカルワークフローを提供する。「AIに一発生成させて終わり」ではなく、人間のレビューコメントを構造化してエージェントにフィードバックする点が要点で、成果物の反復改善をローカル完結でできる。ドキュメント生成を業務で回す用途に直結する実用ツール。

判定理由: 具体的なOSSツールの一次情報（作者本人の公開告知＋GitHubリポジトリ）。Claude Code/Codexのレビュー駆動ワークフローという実装パターンを含みSIGNAL。
