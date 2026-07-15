# 意思決定に資するスライドの見せ方・設計原則

## 目次

1. [意思決定者向けスライドの構成パターン](#1-意思決定者向けスライドの構成パターン)
2. [視覚的なベストプラクティス](#2-視覚的なベストプラクティス)
3. [ストーリーテリング手法](#3-ストーリーテリング手法)
4. [McKinsey / BCG / Amazon 等のスライド哲学](#4-mckinsey--bcg--amazon-等のスライド哲学)
5. [アンチパターン](#5-アンチパターン)
6. [日本語プレゼン特有の考慮事項](#6-日本語プレゼン特有の考慮事項)
7. [実装への示唆](#7-実装への示唆)
8. [参考文献](#8-参考文献)

---

## 1. 意思決定者向けスライドの構成パターン

### 1.1 エグゼクティブサマリー先行型

意思決定者は時間が限られている。CEOが会議間に持つ時間は15分程度ということも珍しくない。結論がスライド12枚目にあれば読まれない。スライド1枚目にあれば、即座に議論に入れる。

**推奨構成:**

| セクション | 内容 | 枚数目安 |
|-----------|------|---------|
| 表紙 | タイトル・日付・発表者 | 1枚 |
| エグゼクティブサマリー | 結論・主要な論拠・推奨アクションの要約 | 1-2枚 |
| 本論（分析・根拠） | データ・分析結果・比較 | 目的に応じて可変 |
| 結論・推奨アクション | 具体的な次のステップ | 1-2枚 |
| 付録 | 補足データ・詳細分析 | 必要に応じて |

> 出典: [How McKinsey Consultants Make Presentations](https://slideworks.io/resources/how-mckinsey-consultants-make-presentations) — McKinsey のプレゼンテーション構成は、表紙 → エグゼクティブサマリー → 本体スライド → 結論/推奨 → 付録 の5部構成を標準とする。

### 1.2 問題提起 → 解決策型

意思決定を促すには「なぜ今行動が必要か」を明確にする必要がある。

**基本フロー:**
1. **現状**（Situation）: 合意できる事実ベースの状況認識
2. **問題**（Complication）: 行動が必要な理由・課題
3. **解決策**（Resolution）: 具体的な推奨アクション

> 出典: [McKinsey SCR Framework](https://speakingsherpa.com/how-to-tell-a-business-story-using-the-mckinsey-situation-complication-resolution-scr-framework/)

### 1.3 比較表・意思決定マトリクス型

複数の選択肢から一つを選ぶ場面では、構造化された比較が有効。

**設計ルール:**
- 選択肢は **3〜7個**、評価基準は **4〜8個** が最適範囲
- 統一されたスコアリング（例: 1〜5、または「優/良/可」）を使用
- 各基準に重み付けを設定し、評価の根拠を透明にする
- MECE原則（相互排他的かつ全体網羅的）に基づいて評価軸を設計
- 色分け（緑 / 黄 / 赤）で視覚的に優劣を把握可能にする

> 出典: [Decision Matrix by McKinsey Alum](https://www.stratechi.com/decision-matrix/) — 3-7 options, 4-8 criteria が推奨範囲。MECE 原則に従い、重複なく網羅的に設計する。

### 1.4 ピラミッド型（結論→根拠→詳細）

Barbara Minto が McKinsey 在籍時に開発した「ピラミッド原則」は、トップダウンで情報を構造化する手法。

**構造:**
```
        [主結論]
       /    |    \
  [根拠1] [根拠2] [根拠3]
  /  \     |  \    /  \
[詳細] [詳細]  ...  [詳細]
```

**ルール:**
- 主結論（推奨アクション）を最初に提示
- 根拠は **3つ** に絞る（人間のワーキングメモリが快適に保持できるのは3〜4項目）
- 各根拠はMECE（相互排他的かつ全体網羅的）であること
- 聴衆が「なぜ?」と問うたびに、下の階層で回答できる構造

> 出典: Barbara Minto『The Pyramid Principle』(1987); [The Pyramid Principle - Consulting Toolbox](https://slideworks.io/resources/the-pyramid-principle-mckinsey-toolbox-with-examples); [think-cell: Using the Pyramid Principle](https://www.think-cell.com/en/resources/content-hub/using-the-pyramid-principle-to-build-better-powerpoint-presentations)

---

## 2. 視覚的なベストプラクティス

### 2.1 フォントサイズ

| 要素 | 推奨サイズ | 最小サイズ |
|------|-----------|-----------|
| スライドタイトル | 32〜44pt | 28pt |
| 本文テキスト | 24〜28pt | 20pt |
| 補足・注釈 | 14〜18pt | 12pt |
| チャートラベル | 16〜20pt | 14pt |

- **Guy Kawasaki の 10-20-30 ルール**: フォントサイズ最小 **30pt**（スライド10枚以内、発表20分以内）
- **PLOS Computational Biology**: スライド1枚あたり **約1分** で説明できる情報量が目安（20分なら約20枚）

> 出典: [Guy Kawasaki 10/20/30 Rule](https://guykawasaki.com/the_102030_rule/); Naegle KM (2021) [Ten simple rules for effective presentation slides](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009554), PLOS Computational Biology 17(12): e1009554

### 2.2 色使い

**コントラスト比（WCAG 2.1準拠）:**
- 通常テキスト: **4.5:1以上**（AA基準）、**7:1以上**（AAA基準）
- 大テキスト（18pt以上 or 14pt太字以上）: **3:1以上**（AA基準）
- 暗い背景に明るい文字、または明るい背景に暗い文字が基本

**配色ルール:**
- テキスト色は **1色** に統一し、全スライドで一貫して使用
- 強調用に **補色を1色** 追加（計2色体制）
- 重要データのハイライトには **明るい色（アクセントカラー）** を使用
- 色覚多様性への配慮: 赤緑の組み合わせを避け、パターンや形状でも区別可能にする

> 出典: [WCAG 2.1 Contrast Requirements](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html); [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

### 2.3 余白とレイアウト

**デザイン4原則**（Robin Williams『ノンデザイナーズ・デザインブック』）:

| 原則 | 内容 | スライドへの適用 |
|------|------|----------------|
| **近接**（Proximity） | 関連する要素を近くに配置 | 見出しと本文、チャートとラベル |
| **整列**（Alignment） | 要素を基準線に揃える | タイトル位置・テキスト左端を全スライドで統一 |
| **反復**（Repetition） | デザインルールを繰り返す | フォント・色・レイアウトの一貫性 |
| **対比**（Contrast） | 重要度の差を視覚的に表現 | タイトルを太字大サイズ、本文を細字小サイズ |

**余白の役割:**
- 余白は「何もない空間」ではなく、視線を重要な要素に誘導する機能を持つ
- Garr Reynolds の Presentation Zen: 「引き算による増幅」（amplification through simplification）
- スライド面積の **40%以上** は余白として確保することが望ましい

> 出典: Robin Williams『The Non-Designer's Design Book』(1994); [Garr Reynolds: Presentation Zen Design Tips](https://www.garrreynolds.com/design-tips); [プレゼン初心者必見！レイアウト4原則](https://studio.virtual-planner.com/layout1/)

### 2.4 情報密度

**認知負荷の科学的根拠:**

| 基準 | 数値 | 出典 |
|------|------|------|
| Miller の法則 | 7 +/- 2 個（ワーキングメモリ容量） | Miller (1956) |
| David JP Phillips の推奨 | **6個以下** / スライド | TEDxStockholmSalon |
| 認知負荷の増大 | 6個超で **500%** の認知リソース増加 | David JP Phillips |
| 箇条書き項目数 | **3〜5個** | 複数の研究による合意 |
| Minto ピラミッド | 根拠は **3個** | Barbara Minto |

- 6個を超えるオブジェクトをスライドに配置すると、聴衆は理解に500%多くのエネルギーと認知リソースを必要とする
- 「気が散った人でも主要メッセージを把握できる」設計が理想

> 出典: [David JP Phillips: Death by PowerPoint (TEDx)](https://singjupost.com/how-to-avoid-death-by-powerpoint-david-jp-phillips-at-tedxstockholmsalon-transcript/); Naegle KM (2021) [Ten simple rules for effective presentation slides](https://pmc.ncbi.nlm.nih.gov/articles/PMC8638955/) — Rule 7: "keep the total number of elements on the slide to 6 or less"

### 2.5 チャート vs 箇条書きの使い分け

| 状況 | 推奨形式 | 理由 |
|------|---------|------|
| 時系列の変化 | 折れ線グラフ / 棒グラフ | トレンドが一目で把握できる |
| 全体に対する割合 | 円グラフ / ドーナツ | 構成比が直感的 |
| 複数選択肢の比較 | 比較表 / 棒グラフ | 並列比較が容易 |
| プロセス・手順 | フローチャート / 番号付きリスト | 順序が明確 |
| ビジネスモデル・戦略 | 箇条書き | 構造化された思考の明示 |
| 独立配布（口頭説明なし） | 箇条書き + 注釈 | ナレーションなしでも理解可能 |

> 出典: [Infographics vs. Bullet points](https://www.pitchdeckstudios.com/infographics-vs-bullet-points-when-to-use-what-in-your-slides/) — データ重視の聴衆にはチャート、分析者向けには箇条書きが適切。視覚スライドとテキストスライドの交互配置がリズムを生む。

### 2.6 フォント選択

- **サンセリフ体** を基本とする（デジタル表示での可読性が高い）
- 英語: Calibri、Helvetica Neue、Segoe UI
- 日本語: 游ゴシック、メイリオ、ヒラギノ角ゴシック（詳細は第6章）
- スライド全体で使用するフォントは **1〜2種類** に統一
- 全角大文字のみ（ALL CAPS）や下線は **避ける**（可読性が低下する）

> 出典: [Slide Fonts: 11 Guidelines for Great Design](https://sixminutes.dlugan.com/slide-fonts/); Naegle KM (2021) Rule 7: sans serif fonts, avoid all capitals and underlining

---

## 3. ストーリーテリング手法

### 3.1 SCR（Situation-Complication-Resolution）

McKinsey が標準的に使用するナラティブフレームワーク。

| 要素 | 内容 | 例 |
|------|------|-----|
| **Situation** | 全員が同意できる事実ベースの現状 | 「当社の市場シェアは過去3年間25%で安定」 |
| **Complication** | 行動が必要になった理由・課題 | 「新規参入者が価格破壊を起こし、シェアが半年で20%に低下」 |
| **Resolution** | 推奨する解決策・具体的アクション | 「既存顧客のLTV向上に注力し、年間$5M の投資で30%のシェア回復を目指す」 |

**使い方のポイント:**
- Situation は聴衆が「そうだよね」と頷ける内容にする
- Complication で緊急性・重要性を高める
- Resolution は具体的な数字・期限・担当を含める

> 出典: [Speaking Sherpa: SCR Framework](https://speakingsherpa.com/how-to-tell-a-business-story-using-the-mckinsey-situation-complication-resolution-scr-framework/); [Slideworks: SCR Framework with Examples](https://slideworks.io/resources/how-to-use-McKinseys-scr-framework-with-examples)

### 3.2 SCQA（Situation-Complication-Question-Answer）

Barbara Minto が『The Pyramid Principle』で提唱した拡張版。SCR に「問い」を明示的に挿入する。

| 要素 | 内容 |
|------|------|
| **Situation** | 現状の事実 |
| **Complication** | 問題・課題 |
| **Question** | 聴衆の頭に浮かぶ自然な問い |
| **Answer** | その問いに対する回答 = 主結論 |

- エグゼクティブサマリーでは Q と A を統合して SCR として簡潔に提示することが多い

> 出典: Barbara Minto『The Pyramid Principle』(1987); [ModelThinkers: Minto Pyramid & SCQA](https://modelthinkers.com/mental-model/minto-pyramid-scqa); [Analytic Storytelling: SCQA](https://analytic-storytelling.com/scqa-what-is-it-how-does-it-work-and-how-can-it-help-me/)

### 3.3 Nancy Duarte の Resonate モデル

Nancy Duarte が著書『Resonate』(2010) で提唱した「今日 / 明日」の対比構造。

**核心的な考え方:**
- 聴衆をヒーロー、発表者をメンター（導き手）として位置付ける
- 「現状（What Is）」と「あるべき姿（What Could Be）」を交互に提示し、緊張と解決のリズムを作る
- 最後に「New Bliss（新しい理想状態）」を描いて行動を促す

**STAR モーメント（Something They'll Always Remember）:**
- 聴衆が必ず記憶に残す印象的な瞬間を意図的に設計する
- 5つのタイプ: 劇的な実演、繰り返し使える名言、喚起的なビジュアル、感動的なストーリー、衝撃的な統計データ

> 出典: Nancy Duarte『Resonate: Present Visual Stories that Transform Audiences』(2010); [Duarte: Resonate](https://www.duarte.com/resources/books/resonate/); [What makes a STAR moment shine?](https://tweakyourslides.wordpress.com/2014/02/03/what-makes-a-star-moment-shine/)

### 3.4 各フレームワークの使い分け

| フレームワーク | 最適な場面 | 特徴 |
|---------------|----------|------|
| **SCR** | 経営層への提案・報告 | 簡潔、行動指向 |
| **SCQA** | 分析報告・リサーチ発表 | 問いの明示で論理性を強調 |
| **ピラミッド原則** | 複雑な論証の構造化 | 「なぜ?」への階層的回答 |
| **Resonate** | 全社会議・外部講演 | 感情に訴えかける |
| **10-20-30** | 投資家向けピッチ | 厳格な枚数・時間制約 |

---

## 4. McKinsey / BCG / Amazon 等のスライド哲学

### 4.1 McKinsey のスライド設計原則

**1スライド1メッセージの原則:**
- 各スライドが伝えるのは **1つの洞察のみ**
- 2つのポイントがあれば、2枚のスライドに分ける

**アクションタイトル:**
- スライドのタイトルは「トピック」ではなく「洞察」を記述する
- **最大15語**（日本語なら30〜40文字目安）、**2行以内**
- 能動態・アクション動詞で始める（「Grow...」「Minimize...」「Improve...」）
- アクションタイトルだけを通して読めばプレゼン全体のストーリーが理解できるようにする

| 悪い例（トピックタイトル） | 良い例（アクションタイトル） |
|--------------------------|--------------------------|
| 「サプライチェーンの最適化」 | 「サプライチェーン最適化でコスト20%削減を実現」 |
| 「専門家インタビューの結果」 | 「8つの高インパクトなコスト削減レバーを特定」 |
| 「プロジェクト体制」 | 「運営委員会がプロジェクト構成とスケジュールを決定」 |

**ゴーストデック（Ghost Deck）手法:**
1. 白紙のスライドにアクションタイトルだけを並べる
2. 全体の流れ（水平フロー）を確認・調整する
3. タイトルが確定してから、各スライドの中身（垂直フロー）を作り込む

**2つのフロー:**
- **水平フロー（Horizontal Flow）**: スライド間の論理的な流れ。アクションタイトルを順に読んだだけでストーリーが成立すること
- **垂直フロー（Vertical Flow）**: 1枚のスライド内でのタイトル → サブヘッド → 本体 → ソースの論理構造

> 出典: [Slideworks: How McKinsey Consultants Make Presentations](https://slideworks.io/resources/how-mckinsey-consultants-make-presentations); [Slideworks: How to Write Action Titles Like McKinsey](https://slideworks.io/resources/how-to-write-action-titles-like-mckinsey); [Deckary: MBB Guide to Professional Slides](https://deckary.com/blog/pillar-consulting-presentations-guide)

### 4.2 BCG のスライド設計原則

- BCG コンサルタントは「タイトルだけ読んで全体が理解できるプレゼン」を書くよう訓練される
- McKinsey と同様に1スライド1メッセージだが、BCG はより **視覚的なフレームワーク（2x2マトリクス等）** を多用する傾向がある
- データの出典は全スライドのフッターに必ず記載

> 出典: [Mastering the McKinsey/BCG-Style PowerPoint Deck](https://www.linkedin.com/pulse/mastering-mckinseybcg-style-powerpoint-deck-your-niklas-scipio); [Analyst Academy: 3 Great Examples of Slide Structure](https://www.theanalystacademy.com/consulting-slide-structure/)

### 4.3 Amazon のナラティブメモ哲学

Jeff Bezos は2004年に Amazon 社内での PowerPoint 使用を禁止し、**6ページのナラティブメモ** を導入した。

**PowerPoint を排した理由（Bezos の主張）:**
> 「良い4ページのメモを書くのが、20ページの PowerPoint を『書く』より難しい理由は、ナラティブ構造が、何がより重要か、アイデアがどう関連しているかについて、より良い思考とより良い理解を強制するからだ。PowerPoint スタイルのプレゼンは、アイデアの上辺を撫でることを許し、相対的な重要性の感覚を平坦にし、アイデアの相互関連性を無視する許可を与えてしまう。」

**6ページメモの原則:**
- 密なナラティブ形式（箇条書きではない）で書く
- 論理的な矛盾を隠すことが不可能になる
- 会議冒頭で **全員が黙読** してからディスカッションに入る
- 2ページ目で生じた疑問が4ページ目で解消される構造

**スライド作成ツールへの示唆:**
- Amazon の哲学は「スライドに頼るな」だが、これは「論理構造を先に確立してから視覚化せよ」と読み替えることができる
- ツールとしてはまずテキストベースの構造化を行い、その後にスライド化するワークフローが望ましい

> 出典: [CNBC: Why Jeff Bezos makes Amazon execs read 6-page memos](https://www.cnbc.com/2018/04/23/what-jeff-bezos-learned-from-requiring-6-page-memos-at-amazon.html); [Slab: How Jeff Bezos Turned Narrative into Competitive Advantage](https://slab.com/blog/jeff-bezos-writing-management-strategy/)

### 4.4 Edward Tufte のデータ可視化原則

情報デザインの泰斗 Edward Tufte は著書『The Cognitive Style of PowerPoint』(2003) で PowerPoint の構造的問題を批判した。

**主要概念:**

| 概念 | 定義 | スライド設計への適用 |
|------|------|---------------------|
| **データインク比** | データを表現するインクの割合を最大化する | 装飾的な要素を排除し、データそのものに紙面を使う |
| **チャートジャンク** | データ理解を妨げる不要な視覚装飾 | 3Dエフェクト、グラデーション、装飾的グリッドを排除 |
| **Small Multiples** | 同じ形式の小さなチャートを並列に並べる | 複数条件の比較を一目で可能にする |

**Tufte による PowerPoint の問題点:**
- PowerPoint はスライド面積の **40〜60%** をPhluff（装飾）、箇条書き記号、フレーム、ブランディングに使い、独自コンテンツに使える面積は40〜60%しかない
- 人為的に深い階層構造を強制し、アイデアの相互関連性を壊す
- 聴衆を発表者のペースに合わせたリニアな進行にロックする

> 出典: Edward R. Tufte『The Cognitive Style of PowerPoint: Pitching Out Corrupts Within』(2003); [Wikipedia: Edward Tufte](https://en.wikipedia.org/wiki/Edward_Tufte); [Free Power Point Templates: Edward Tufte Tips](https://www.free-power-point-templates.com/articles/edward-tufte-presentation-tips-data-visualization-guru/)

### 4.5 Garr Reynolds の Presentation Zen

**Signal-to-Noise Ratio（信号対雑音比）:**
- 伝えたいメッセージ（信号）と無関係な視覚要素（雑音）の比率を最大化する
- 不要な要素を徹底的に削減する「引き算による増幅」

**主要原則:**
- 各スライドは **1つの明確なアイデア** のみを表現する
- 複数ポイントの箇条書きリストは、個別のスライドに分割する
- 大きなイラスト・写真を使い、テキストは最小限に
- 空白（ネガティブスペース）を十分に確保し、1〜2の重要な要素を際立たせる

> 出典: Garr Reynolds『Presentation Zen: Simple Ideas on Presentation Design and Delivery』(2008); [Garr Reynolds: Design Tips](https://www.garrreynolds.com/design-tips)

---

## 5. アンチパターン

### 5.1 Death by PowerPoint（情報過多による死）

スライドにテキスト・データ・箇条書きを詰め込みすぎると、聴衆を巻き込むどころか圧倒してしまう。

### 5.2 具体的なアンチパターン一覧

| # | アンチパターン | 問題点 | 解決策 |
|---|--------------|--------|--------|
| 1 | **テキスト壁** | 聴衆は読むか聞くかのどちらかしかできない | 1スライド1メッセージ、本文は箇条書き3〜5項目以内 |
| 2 | **スライド読み上げ** | 聴衆の読解力を侮辱し、注意が分散 | スライドはビジュアル補助、口頭で補足 |
| 3 | **チャート過密** | 変数が多すぎる・ラベルなしのチャート | 1チャート1メッセージ、ラベル必須 |
| 4 | **可視化混在** | 同一スライドに円グラフ・棒グラフ・折れ線が混在 | 1スライド1チャートタイプ |
| 5 | **アニメーション過多** | 進行が遅延、技術トラブルのリスク増大 | アニメーションは **プレゼン全体で3個以内** 、目的がある場合のみ |
| 6 | **トピックタイトル** | 「売上分析」のような見出しでは何も伝わらない | アクションタイトルで洞察を述べる |
| 7 | **装飾過多（チャートジャンク）** | 3D効果・グラデーション・無関係なクリップアート | データインク比を最大化、装飾を排除 |
| 8 | **フォント混在** | 統一感がなく、素人感が出る | スライド全体で 1〜2 フォントに統一 |
| 9 | **低コントラスト** | 薄い背景に薄い文字、プロジェクターで読めない | WCAG AA 基準（4.5:1以上）を遵守 |
| 10 | **ソース欠如** | データの信頼性が不明 | 全データスライドのフッターに出典を記載 |

> 出典: [SlideModel: Death by PowerPoint](https://slidemodel.com/death-by-powerpoint/); [Analyst Academy: 7 PowerPoint Mistakes](https://www.theanalystacademy.com/common-powerpoint-mistakes/); David JP Phillips [TEDxStockholmSalon](https://singjupost.com/how-to-avoid-death-by-powerpoint-david-jp-phillips-at-tedxstockholmsalon-transcript/); Edward R. Tufte『The Cognitive Style of PowerPoint』(2003)

### 5.3 チェックリスト: アンチパターン回避

スライド作成後に以下を確認する:

- [ ] 各スライドに明確な1つのメッセージがあるか?
- [ ] アクションタイトルだけ通して読んでストーリーが成立するか?
- [ ] 1スライドあたりのオブジェクト数が6個以下か?
- [ ] フォントサイズが最小20pt以上か?
- [ ] テキストと背景のコントラスト比が4.5:1以上か?
- [ ] 全データにソース（出典）が記載されているか?
- [ ] 不要なアニメーション・装飾はないか?
- [ ] 箇条書きは5項目以内か?

---

## 6. 日本語プレゼン特有の考慮事項

### 6.1 日本語フォントの選択

| フォント | 特徴 | 推奨場面 |
|---------|------|---------|
| **游ゴシック** | Win/Mac 互換性あり、太さ選択可能 | 汎用（最も推奨） |
| **メイリオ** | 視認性追求、UD設計に近い | 大会場での投影 |
| **ヒラギノ角ゴシック** | Mac標準、美しい字形 | Mac環境 |
| **Noto Sans JP** | Google フォント、Web対応 | クロスプラットフォーム |

**注意事項:**
- スライドでは **ゴシック体** を使用（明朝体は論文・文書向き、スクリーン投影では線が細く読みにくい）
- 10〜15名程度の会議室では **26pt以上** を推奨
- 日本語と英語の混在時は、英数字にサンセリフ体（Segoe UI、Calibri 等）を指定

> 出典: [発表用のスライドにはゴシック系のフォントがお勧め！](https://silenceinfo.net/research-slide-7/); [パワーポイント資料に最適なフォント6選](https://studio.virtual-planner.com/powerpoint-font/); [Slideflow: パワーポイントのおすすめフォント](https://www.slideflow.me/blog/power-point-fonts)

### 6.2 投影資料 vs 配布資料の使い分け

日本のビジネス慣行では、投影用スライドと配布資料を **別物として** 設計することが重要。

| 属性 | 投影資料 | 配布資料 |
|------|---------|---------|
| **情報量** | 最小限（口頭説明で補完） | 豊富（資料単体で完結） |
| **文字サイズ** | 24pt以上 | 12pt以上でも可 |
| **余白** | 多め | 効率的に使用 |
| **目的** | 視覚的インパクト、注目誘導 | 後日の参照、詳細確認 |
| **構造** | 1スライド1メッセージ | 密な情報構成も許容 |

> 出典: [投影資料と配付資料の使い分け](https://letter.sorimachi.co.jp/gadget/20221207_01); [プレゼン資料と配付資料。面倒でもきちんと使い分けよう](https://dnm.jp/1865-2/)

### 6.3 日本のビジネス文化への適応

**根回し（Nemawashi）との関係:**
- 日本の意思決定プロセスでは、会議の場で初めて情報を提示するのではなく、事前に関係者への根回しが行われる
- スライドには **新しい情報を最小限** にし、事前共有済みの内容を視覚的に整理する役割が求められる
- 会議は「形式的な合意形成の場」であり、プレゼンは説得ではなく確認の機能を持つことが多い

**稟議（Ringi）制度との整合:**
- 稟議書に添付するスライドは、個別の承認者が独立して読んで理解できる必要がある
- 口頭説明を前提としない **自己完結型** の設計が求められる（配布資料に近い）

**起承転結 vs 結論ファースト:**
- 日本の伝統的な文章構成「起承転結」は、ビジネスプレゼンでは **非推奨**
- 意思決定者向けには **結論ファースト**（ピラミッド原則 / SCR）が効果的
- ただし、相手が結論を受け入れにくい場合は、背景説明から入る配慮も必要

> 出典: [Nihonium: Japanese vs. Western Business Presentations](https://nihonium.io/japanese-vs-western-business-presentations/); [GLOBIS: The Invisible Hand — Nemawashi](https://globis.eu/nemawashi-in-japanese-culture/); [MANABINK: What is Japanese Style Presentation?](https://manabink.com/en/2020/06/15/what-is-japanese-style-presentation/)

### 6.4 情報量の日米比較

一般的に、日本のプレゼン資料はアメリカのものに比べて **3倍以上** の情報量を含む傾向がある。これは日本の「資料で全てを説明しきる」文化と、アメリカの「プレゼンターが口頭で補完する」文化の違いに起因する。

本ツールでは、投影用（情報量を絞った国際標準寄り）と配布用（情報量を充実させた日本寄り）の両方に対応できる設計が望ましい。

> 出典: [アメリカ型プレゼンで重要なポイント5つ](https://blog.btrax.com/jp/presentation/)

### 6.5 日本語テキストの品質

- 「ら抜き言葉」「い抜き言葉」などの表現の乱れに注意
- ビジネス経験豊富な読み手ほど、文章の違和感にすぐ気づく
- 体言止め・名詞句を活用して簡潔に（「〜を実現する」→「〜の実現」）
- 漢字・ひらがなのバランスに配慮（漢字過多は堅苦しく、ひらがな過多は軽い印象）

> 出典: [プレゼン資料の正しい日本語・文章の基本テクニック](https://note.com/jissen_presen/n/n35c1818f4aaf)

---

## 7. 実装への示唆

本ツール（スライド作成ツール）への設計原則の反映方針:

### 7.1 構造面

| 原則 | 実装方針 |
|------|---------|
| 1スライド1メッセージ | Gemini API で構成生成時、各スライドに1つのキーメッセージを割り当てる |
| アクションタイトル | スライドタイトルはトピックではなく洞察・結論を記述するようプロンプト設計 |
| ピラミッド原則 | 全体構成を「結論→根拠→詳細」の階層で生成 |
| SCR フレームワーク | ストーリーラインのテンプレートとして SCR/SCQA を選択可能にする |

### 7.2 視覚面

| 原則 | 実装方針 |
|------|---------|
| 6オブジェクト制限 | python-pptx でスライド内の要素数を監視・警告 |
| フォントサイズ下限 | 設定可能な最小フォントサイズ（デフォルト: 20pt） |
| コントラスト比 | テーマカラー選択時に WCAG AA 基準を自動チェック |
| 余白確保 | レイアウトテンプレートに最低マージンを組み込む |

### 7.3 日本語対応

| 原則 | 実装方針 |
|------|---------|
| フォント | デフォルトを游ゴシック、フォールバックをメイリオ |
| 投影/配布モード | 同一内容から情報密度が異なる2種類の出力を生成可能にする |
| 結論ファースト | デフォルト構成をピラミッド型（結論先行）とする |

---

## 8. 参考文献

### 書籍

| 著者 | タイトル | 出版年 | 主要概念 |
|------|---------|--------|---------|
| Barbara Minto | The Pyramid Principle | 1987 | ピラミッド原則、SCQA、MECE |
| Edward R. Tufte | The Cognitive Style of PowerPoint | 2003 | データインク比、チャートジャンク |
| Garr Reynolds | Presentation Zen | 2008 | 信号対雑音比、引き算の美学 |
| Nancy Duarte | Resonate | 2010 | 今日/明日の対比、STAR モーメント |
| Robin Williams | The Non-Designer's Design Book | 1994 | デザイン4原則（近接・整列・反復・対比） |

### 学術論文

- Naegle KM (2021) "Ten simple rules for effective presentation slides." PLOS Computational Biology 17(12): e1009554. https://doi.org/10.1371/journal.pcbi.1009554
- Miller GA (1956) "The magical number seven, plus or minus two." Psychological Review, 63(2), 81-97.

### Web 記事・ガイド

- [Slideworks: How McKinsey Consultants Make Presentations](https://slideworks.io/resources/how-mckinsey-consultants-make-presentations)
- [Slideworks: How to Write Action Titles Like McKinsey](https://slideworks.io/resources/how-to-write-action-titles-like-mckinsey)
- [Slideworks: The Pyramid Principle - Consulting Toolbox](https://slideworks.io/resources/the-pyramid-principle-mckinsey-toolbox-with-examples)
- [Speaking Sherpa: SCR Framework](https://speakingsherpa.com/how-to-tell-a-business-story-using-the-mckinsey-situation-complication-resolution-scr-framework/)
- [Guy Kawasaki: The 10/20/30 Rule of PowerPoint](https://guykawasaki.com/the_102030_rule/)
- [David JP Phillips: How to avoid Death by PowerPoint (TEDx)](https://singjupost.com/how-to-avoid-death-by-powerpoint-david-jp-phillips-at-tedxstockholmsalon-transcript/)
- [WCAG 2.1: Understanding Contrast (Minimum)](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [Nihonium: Japanese vs. Western Business Presentations](https://nihonium.io/japanese-vs-western-business-presentations/)
- [CNBC: Why Jeff Bezos makes Amazon execs read 6-page memos](https://www.cnbc.com/2018/04/23/what-jeff-bezos-learned-from-requiring-6-page-memos-at-amazon.html)
- [Garr Reynolds: Presentation Design Tips](https://www.garrreynolds.com/design-tips)
- [SlideModel: Death by PowerPoint](https://slidemodel.com/death-by-powerpoint/)
- [Analyst Academy: 7 PowerPoint Mistakes](https://www.theanalystacademy.com/common-powerpoint-mistakes/)
- [Deckary: MBB Guide to Professional Slides](https://deckary.com/blog/pillar-consulting-presentations-guide)

---

*調査日: 2026-02-21*
*調査者: researcher agent*
