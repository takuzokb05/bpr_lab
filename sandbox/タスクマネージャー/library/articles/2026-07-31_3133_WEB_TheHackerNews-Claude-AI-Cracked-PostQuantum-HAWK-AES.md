# Claude AI Just Cracked a Post-Quantum Test Scheme and Found a Faster 7-Round AES Attack

- URL: https://thehackernews.com/2026/07/claude-ai-just-cracked-post-quantum.html
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-07-31

## 投稿内容
The Hacker Newsによる詳細報道。Anthropic Claude Mythos PreviewによるHAWK-256脆弱性発見の技術的背景・セキュリティコミュニティへの影響を詳説。

## 要約
The Hacker Newsによる上記Anthropic研究の独立報道。セキュリティ専門メディアの視点でHAWK-256脆弱性発見の意義を解説。

**HAWK-256とは:**
HAWK（High-security And Weaknesses-resistant Key）は、格子ベースのポスト量子デジタル署名スキームで、NISTが次世代ポスト量子署名標準の追加選定プロセスで第3ラウンドに進めた9候補の一つ。2024年から2年以上、専門家による集中的な審査を受けていた。

**Mythos Previewの攻撃手法:**
1. HAWK-256の格子構造に隠れた非自明な自己同型写像（nontrivial automorphism）を発見
2. 理論上この対称性が存在すればより高速な攻撃が可能と示唆されていたが、HAWK設計内での存在は未確認だった
3. Mythos PreviewがこのAI-assistance+数学的探索で60時間以内に存在を確認・攻撃を構築

**技術的インパクト:**
- HAWK-256: 2^64 → 2^38（実質的に鍵強度が半減）
- 7ラウンドAES-128: 既知攻撃の200〜800倍高速化
- 128ビットセキュリティを主張していたシステムが64ビット以下に実質劣化

**セキュリティ業界への示唆:**
AIによる暗号プリミティブの大規模自動解析時代の到来。レッドチーミングにAIを活用した先制的な脆弱性探索が標準的実践になる可能性。
