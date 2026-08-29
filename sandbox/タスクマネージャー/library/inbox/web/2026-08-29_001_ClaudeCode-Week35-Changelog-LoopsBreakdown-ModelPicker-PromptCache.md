# Claude Code Week 35 Changelog: Loops Breakdown, Model Picker, PromptCache Settings

- URL: https://www.gradually.ai/en/changelogs/claude-code/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-29

## 要約
Week 35（2026-08-25〜29）のClaude Codeチェンジログ。主要追加機能：
- `/usage`にLoopsブレイクダウン表示追加（ループ実行回数・合計トークン・実行あたりトークン・最終実行）
- `modelPicker`設定でモデルセレクタをカスタマイズ可能（順序ラベル付きリスト）
- `promptCacheTtl` / `subagentPromptCacheTtl`設定でプロンプトキャッシュ期間を管理可能
- `modelPricing`マネージド設定で組織契約価格を`/cost`計算に反映（定価でなく実際の契約価格）
- Bash allowルールにワイルドカード警告追加・Auto modeタブを`/permissions`に追加
- ターン完了時刻をエンドターン継続行に追加
- `/claude-api`スキルにAdmin API coverage更新
- Linux glibc 2.44（Arch Linux・Fedora Rawhide）クラッシュバグ修正（v2.1.245）
- 起動時間改善：サンドボックス・MCP初期化が最初のフレームをブロックしなくなった
- ネイティブインストール・自動更新ダウンロードサイズをzstd圧縮で削減（Linux x64: 340MB→75MB）
