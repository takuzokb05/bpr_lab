# Claude Mythos Preview Discovers Post-Quantum Cryptographic Weakness — Anthropic Official Research

- URL: https://www.anthropic.com/research/discovering-cryptographic-weaknesses
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-07-31

## 投稿内容
Anthropic公式研究発表。未公開モデル「Claude Mythos Preview」がポスト量子署名候補HAWK-256の構造的脆弱性を60時間で発見。NIST標準化プロセスから同日撤退。7ラウンドAES-128攻撃の200〜800倍高速化も達成。

## 要約
2026年7月29日、Anthropicが画期的な暗号解析研究を公表した。未公開モデル「Claude Mythos Preview」が、2年間の人間専門家レビューをパスしていたNISTポスト量子デジタル署名候補HAWK-256に構造的欠陥を発見した。

**発見の技術的詳細:**
- HAWK-256の格子構造内に存在する未使用の対称性（自己同型写像）を特定
- この対称性を悪用したend-to-endの鍵回復攻撃を60時間で導出
- HAWK-256の実効鍵強度が2^64から2^38オペレーションに低下（鍵強度が半分以下）
- 並行して7ラウンドAES-128攻撃の計算コストを200〜800倍削減する手法も発見

**影響と反応:**
- HAWKはNISTが2026年5月に第3ラウンドに進めた9候補のうち唯一の格子ベース方式だった
- Anthropicの研究発表当日、HAWKチームは自らNISTプロセスから撤退
- 現行本番システムへの即時脅威ではないが、将来の暗号標準設計に重大な示唆

**AI暗号解析の新地平:**
AIが複雑な数学的構造の探索において、専門家集団を数年分上回る速度で知見を生成できることを示した初の大規模事例。セキュリティコミュニティはAIを脅威分析ツールとして組み込む必要性が高まった。
