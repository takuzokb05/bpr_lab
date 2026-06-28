# Claude Codeを4ヶ月使ってわかった、おすすめコマンド・スキル 10 選

- URL: https://qiita.com/wataru86/items/b859f1578191a1e15808
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-06-28

## 投稿内容
4ヶ月間の日常使用から厳選したClaude Codeの高価値コマンド・スキル10選。

**セッション管理:**
- `/rewind`: 5つのロールバックオプション（会話のみ・コードのみ・両方・または要約）で任意の状態に巻き戻し
- `/resume`: 名前付きセッションの復元

**カスタマイズ・設定:**
- `/insights`: HTML使用レポートを生成し、摩擦点や機能提案を特定する分析ツール
- `/update-config`: 自然言語でsettings.jsonを変更（「〜を許可してほしい」と話すだけ）
- `/skill-creator`: スキル説明を反復改善してオートトリガー精度を向上させる公式プラグイン
- `/fewer-permission-prompts`: ログをスキャンしてread-only許可リストを自動構築、パーミッション確認ダイアログを削減

**実用ユーティリティ:**
- `/copy`: 最新レスポンスからフォーマット（マークダウン等）を除去してクリップボードにコピー
- `/loop`: インターバルを設定してCI監視等を自動繰り返し
- `/schedule`: ローカルセッション終了後も継続稼働するRoutinesをクラウドに登録

著者は4ヶ月の使用を通じて、各コマンドが解決する具体的な摩擦ポイントを特定しており、特に`/insights`による自分自身のClaude Code使用パターンの可視化と`/skill-creator`によるスキル精度向上を高く評価している。

## 要約
4ヶ月の実地使用から導き出したClaude Code厳選10コマンド。/rewindで5種ロールバック・/resumeでセッション復元、/insightsで使用パターンHTML分析レポート生成、/update-configで自然言語settings.json更新、/skill-creatorでスキルオートトリガー精度向上、/fewer-permission-promptsで許可リスト自動構築。さらに/copy（フォーマット除去コピー）・/loop（CI監視繰り返し）・/schedule（クラウドRoutines登録）の実用ツール。日常使用で発見した摩擦ポイントと解決策の実践知見。
