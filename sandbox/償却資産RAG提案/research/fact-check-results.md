# ファクトチェック結果

対象ドキュメント:
1. `proposal.md` — 償却資産税業務へのRAG導入提案書
2. `research/data-preparation.md` — データ準備ガイド

検証日: 2026-03-21

---

## サマリー

- 検証対象の主張数: 18件
- 確認済み: 11件
- 部分的に正確 / 要補足: 4件
- 不正確: 1件
- 検証不能: 2件

---

## 致命的な問題（結論に影響）

なし。

---

## 重要な問題

### 1. 神戸市の参考URLが別プロジェクトを指している

- **記載内容**: data-preparation.md の神戸市ボイスボット参考URLに `https://www.city.kobe.lg.jp/a51458/077877436738.html` が記載されている
- **検証結果**: 不正確
- **正しい情報**: このURLは神戸市の別プロジェクト「AI電話タクセル」（CyberAgent提供、個人住民税の24時間対応実証実験）のページである。提案書で言及しているNTTマーケティングアクトProCXのボイスボット（2025年8月〜10月試験導入）とは別事業。神戸市側のNTTボイスボット公式ページは現在404で確認できず。NTTマーケティングアクトProCX側のプレスリリース `https://www.nttactprocx.com/info/detail/260114.html` が一次ソースとして利用可能
- **ソース**: [神戸市:AI電話タクセル実証実験](https://www.city.kobe.lg.jp/a51458/077877436738.html) / [NTTマーケティングアクトProCXプレスリリース](https://www.nttactprocx.com/info/detail/260114.html)
- **影響**: 提案書の信頼性に関わる。URLを開いた読者が異なるプロジェクトの情報を見ることになる。proposal.md の表（第7章）にも同じURLが記載されており、両ファイルで修正が必要

### 2. 善通寺市の職員数推移の記述位置が不正確

- **記載内容**: data-preparation.md に「固定資産税係の職員が年々減少（6人→5人→4人）」と記載
- **検証結果**: 部分的に正確
- **補足**: デジタル庁ニュース（2026-01-15）の善通寺市発表資料にて「令和5年6名、令和6年5名、令和7年4名」と確認できる。数字は正確。ただし proposal.md では「職員4人体制でも業務維持」とのみ記載しており、推移の詳細はdata-preparation.mdだけに記載されている。一般のニュース記事（KSB、共同通信、日経等）にはこの職員数推移は掲載されておらず、デジタル庁の共創PFキャンプ発表が一次ソース
- **ソース**: [デジタル庁ニュース](https://digital-agency-news.digital.go.jp/articles/2026-01-15)

### 3. 総務省ガイドブックの名称が不完全

- **記載内容**: proposal.md の表（第7章）に「自治体AI活用ガイドブック第4版（2025.12）」と記載
- **検証結果**: 部分的に正確
- **補足**: 正式名称は「自治体におけるAI活用・導入ガイドブック＜導入手順編＞（第4版）」。公表日は令和7年12月16日（2025年12月16日）で月は正確。提案書内の略称は表の制約上許容範囲だが、信頼性を高めるなら正式名称を脚注等で補足するとよい
- **ソース**: [総務省報道資料](https://www.soumu.go.jp/menu_news/s-news/01gyosei04_02000155.html)

### 4. 国税庁KSK2の記述が参照先と一致しない

- **記載内容**: data-preparation.md に「参考: 国際税務」として `https://www.zeiken.co.jp/kokusaizeimu/article/202512/KZ2025120200101.php` を記載。proposal.md にも「KSK2移行、AI調査選定本格化（2026〜）」と記載
- **検証結果**: 部分的に正確
- **補足**: 参照先の国際税務記事（2025年12月号）はAI調査選定の話題を扱っているが、記事タイトルは「国税庁でもAIによる調査選定が進む！...調査事案選定の視点」であり、KSK2という固有名詞は記事中に明示されていない。KSK2の2026年9月移行は他の複数ソースで確認可能だが、この参照先はKSK2の根拠としては不十分。KSK2移行時期「2026年9月24日」は複数の税務専門メディアで確認済み
- **ソース**: [国際税務記事](https://www.zeiken.co.jp/kokusaizeimu/article/202512/KZ2025120200101.php) / [KSK2導入解説](https://www.fas-calm.co.jp/blog/2025/12/11/ksk2-ai-tax-audit-guide-2026/)

---

## 軽微な問題

### 5. 善通寺市の参考URLドメインが特殊

- **記載内容**: data-preparation.md の善通寺市参考URLが `https://digital-agency-news.digital.go.jp/articles/2026-01-15` と記載
- **検証結果**: 確認済み（URLは有効で内容も正確）
- **補足**: ただし、このドメイン（digital-agency-news.digital.go.jp）はデジタル庁のニュースサイトとして存在するが、URL構造が日付ベースでやや特殊。リンク切れリスクを考慮し、報道機関の記事（KSB、日経等）も併記しておくと安全

---

## 検証不能な主張

- 「デジタル統括本部が来年度より開始する手上げ制RAG導入支援」 — 庁内情報のため外部ソースで検証不能。事実であれば提案の前提として重要
- 「新基幹システムは資産データを5年分遡及して保持」 — 庁内システム仕様のため外部検証不能

---

## 正確性が確認された主張（主要なもの）

- 「草津市がkopo（固定資産税DXポータル）を令和6年度から導入」 — [ぎょうせいオンライン](https://shop.gyosei.jp/online/archives/cat02/0000114380)、[kopo公式](https://kopo.jp/)、[朝日航洋](https://www.aeroasahi.co.jp/spatialinfo/system/kopo/) で確認
- 「kopoは朝日航洋が提供するSaaS」 — [朝日航洋公式](https://www.aeroasahi.co.jp/spatialinfo/system/kopo/) で確認
- 「神戸市の生成AIボイスボットはNTTマーケティングアクトProCXと共同」 — [NTTマーケティングアクトProCXプレスリリース](https://www.nttactprocx.com/info/detail/260114.html) で確認
- 「年間40〜50万件の税務電話問い合わせ」 — [NTTマーケティングアクトProCXプレスリリース](https://www.nttactprocx.com/info/detail/260114.html) で確認。「税務部への電話問い合わせ」と記載
- 「定型的問い合わせの65%以上を自動回答」 — [NTTマーケティングアクトProCXプレスリリース](https://www.nttactprocx.com/info/detail/260114.html) で確認。「定型的な問い合わせの内65％以上を自動回答することに成功」
- 「善通寺市が衛星画像×AIで土地・家屋変化抽出」 — [KSBニュース](https://news.ksb.co.jp/article/15517617)、[日経](https://www.nikkei.com/article/DGXZQOUE1409I0U4A211C2000000/)、[デジタル庁](https://digital-agency-news.digital.go.jp/articles/2026-01-15) で確認
- 「善通寺市がオープンソース中心でランニングコスト最小化」 — [デジタル庁ニュース](https://digital-agency-news.digital.go.jp/articles/2026-01-15) で「QGIS、Python等」のオープンソース活用を確認
- 「国税庁KSK2が2026年移行」 — 複数の税務専門メディアで2026年9月24日移行を確認。[KSK2解説記事](https://www.fas-calm.co.jp/blog/2025/12/11/ksk2-ai-tax-audit-guide-2026/)
- 「総務省 自治体AI活用ガイドブック第4版が2025年12月公表」 — [総務省報道資料](https://www.soumu.go.jp/menu_news/s-news/01gyosei04_02000155.html) で2025年12月16日公表を確認
- 「ガイドブックPDF URL」 — `https://www.soumu.go.jp/main_content/000820109.pdf` の有効性を確認
- 「NTTマーケティングアクトProCXプレスリリースURL」 — `https://www.nttactprocx.com/info/detail/260114.html` の有効性を確認

---

## 修正推奨事項まとめ

| # | ファイル | 問題 | 推奨対応 |
|---|---------|------|---------|
| 1 | proposal.md, data-preparation.md | 神戸市参考URLが別プロジェクト | URLを `https://www.nttactprocx.com/info/detail/260114.html` に差し替え、または神戸市の正しいページURLを調査して記載 |
| 2 | data-preparation.md | 国際税務記事がKSK2の直接ソースではない | KSK2移行の一次ソース（国税庁公表資料や税務専門メディア）を追加 |
| 3 | proposal.md | ガイドブック略称 | 正式名称を脚注等で補足（任意） |
