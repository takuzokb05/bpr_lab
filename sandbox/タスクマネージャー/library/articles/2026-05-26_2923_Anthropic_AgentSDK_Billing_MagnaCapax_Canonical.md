# Anthropic Agent SDK課金分離 May13発表 完全解析（MagnaCapax Gist）

- URL: https://gist.github.com/MagnaCapax/d9177e35b355853f03c730dfcaa693ef
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-26

## 要約
Anthropic が2026年5月13日発表の Agent SDK 課金分離ポリシーの一次分析。6月15日以降、Agent SDK・claude -p・Claude Code GitHub Actions・サードパーティアプリはサブスクリプション枠から別クレジットプールへ移行（Pro $20/月、Max 5x $100/月、Max 20x $200/月、ロールオーバーなし）。軽量ワークロードで実効12倍、重量ワークロードで最大175倍の価格上昇と試算。Community Note分析、競合比較、影響ケース整理、6月15日前のクレジット申請手順を詳述。インタラクティブ利用（Claude.ai・Claude Codeターミナル）は従来通りサブスクリプション枠。
