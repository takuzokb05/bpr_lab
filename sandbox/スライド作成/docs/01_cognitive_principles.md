# Q1a: 認知科学に基づくスライド設計原則

> 担当: ux-psychologist
> 作成日: 2026-02-26
> ステータス: 初稿（fact-checker/devils-advocate 検証前）

## 概要

本ドキュメントは、スライドデザインの「なぜ伝わるか」「なぜ記憶に残るか」を認知科学・UX の理論的根拠に基づいて体系化する。各原則には理論的根拠、実証データ、スライド設計への適用方法、および Claude への具体的指示を含む。

---

## 認知科学に基づくスライド設計原則

### 原則 1: 認知負荷の最小化（Cognitive Load Theory）

- **理論的根拠**: John Sweller（1988）が提唱した認知負荷理論。人間の作業記憶（ワーキングメモリ）には厳しい容量制限がある。George Miller（1956）は「マジカルナンバー 7 +/- 2」を提唱したが、Nelson Cowan（2001）の再検討により、作業記憶の実質的容量は **約4チャンク** に修正された（Cowan, 2001, "The magical number 4 in short-term memory: A reconsideration of mental storage capacity", *Behavioral and Brain Sciences*, 24(1), 87-114）。
- **認知負荷の3分類**:
  - **内在的負荷（Intrinsic Load）**: 学習対象そのものの複雑さ。スライドの主題に依存し、制御が難しい
  - **外在的負荷（Extraneous Load）**: 不適切なデザインによる不要な認知的努力。**これを最小化することがスライド設計の核心**
  - **本質的負荷（Germane Load）**: 理解・記憶の定着に貢献する生産的な認知処理。これは保持すべき
- **実証データ**:
  - 作業記憶の容量は成人で約4チャンク（Cowan, 2001）
  - 不要な画像・装飾を除去するだけで学習効果が向上する — Mayer のコヒーレンス原則（効果量 d = 0.86）（Mayer, 2009）
  - スライドに表示されたテキストを読み上げると、言語入力が2チャネルで競合し、作業記憶がオーバーロードする（冗長性効果、d = 0.87）
- **スライド設計への適用**:
  - 1スライドの情報量を4チャンク以内に制限する
  - 装飾的な画像・アニメーション・背景パターンを排除する
  - テキストを読み上げる場合、スライドにはテキストではなく図解を表示する
  - 複雑なプロセスは1枚に詰め込まず、段階的に複数スライドに分割する
- **Claude への指示として**: 「1スライドに含める主要メッセージは1つ。サポート要素（箇条書き・データ・図解）は最大4つ。装飾目的の画像やグラデーション背景は使用しない。テキストは箇条書きの場合、1行あたり10語以内（日本語は20文字以内）を目安とする」
- **ソース**:
  - [Cowan, N. (2001). The magical number 4 in short-term memory](https://pubmed.ncbi.nlm.nih.gov/11515286/) - 学術論文
  - [Sweller, J. (1988). Cognitive load during problem solving](https://www.instructionaldesign.org/theories/cognitive-load/) - 学術理論解説
  - [Using Cognitive Load Theory to improve slideshow presentations](https://my.chartered.college/impact_article/using-cognitive-load-theory-to-improve-slideshow-presentations/) - 実践的応用記事

---

### 原則 2: 二重符号化による記憶強化（Dual Coding Theory）

- **理論的根拠**: Allan Paivio（1971, 1986）が提唱した二重符号化理論。人間の認知システムは **言語系（verbal system）** と **非言語系（nonverbal/imagery system）** の2つの独立したチャネルで情報を処理・保存する。両チャネルで符号化された情報は、片方のみの場合と比較して記憶に残りやすい。Richard Mayer（2001）はこれを拡張し、マルチメディア学習の認知理論（CTML）を構築した。
- **実証データ**:
  - テキスト＋関連する図解の組み合わせは、テキスト単独と比較して理解度が 0.48 SD 向上する（Butcher, 2006 メタ分析）
  - 画像の記憶保持率はテキストの約6倍。聴覚情報のみの場合、3日後の記憶保持率は **10%** だが、画像を加えると **65%** に向上する（Medina, 2008, *Brain Rules*）
  - Mayer のマルチメディア原則: テキスト＋画像の学習効果はテキスト単独の効果量 d = 1.67（中央値）で上回る
- **スライド設計への適用**:
  - 全てのスライドにテキスト（言語系）と視覚要素（非言語系）の両方を含める
  - 視覚要素はテキストの「装飾」ではなく、テキストの内容を「別の表現で」再表現するものにする
  - 抽象的な概念にはメタファーを使った視覚表現を用いる（例: 「成長」→上向き矢印グラフ）
  - データはテキストの数値羅列ではなく、チャート・グラフで視覚化する
- **Claude への指示として**: 「各スライドには必ず視覚要素の指定を含める。テキストで述べた内容を図解・チャート・アイコンで別表現する。視覚要素は装飾ではなく情報伝達の手段として使う。データスライドでは数値の羅列ではなくグラフ（棒グラフ/折れ線グラフ/円グラフ）を使用し、テキストはグラフの解釈（So What?）のみに絞る」
- **ソース**:
  - [Paivio, A. (1986). Dual Coding Theory - InstructionalDesign.org](https://www.instructionaldesign.org/theories/dual-coding/) - 理論解説
  - [Dual-coding theory - Wikipedia](https://en.wikipedia.org/wiki/Dual-coding_theory) - 概要
  - [Medina, J. (2008). Brain Rules - Vision](https://brainrules.net/vision/) - 書籍・公式サイト
  - [Mayer's 12 Principles of Multimedia Learning - DLI](https://www.digitallearninginstitute.com/blog/mayers-principles-multimedia-learning) - 応用記事

---

### 原則 3: 前注意的処理とゲシュタルト原則（Preattentive Processing & Gestalt Principles）

- **理論的根拠**: 人間の視覚システムは、意識的な注意の **前に** 特定の視覚属性を自動的に処理する（前注意的処理、10ミリ秒以内）。この自動処理を活用すれば、視聴者の注意を意図した場所に誘導できる。ゲシュタルト心理学（20世紀初頭、Wertheimer, Koffka, Kohler）の知覚原則は、人間が視覚要素をどのようにグループ化・構造化して知覚するかを説明する。
- **前注意的属性**（10ms 以内に処理される属性）:
  - **色相（Hue）**: 異なる色は即座に検出される
  - **サイズ（Size）**: 大きさの違いは即座に検出される
  - **方向（Orientation）**: 傾きの違いは即座に検出される
  - **形状（Shape）**: 形の違いは即座に検出される
- **ゲシュタルト原則**:
  - **近接（Proximity）**: 近くにある要素はグループとして知覚される → スライド上の関連情報は物理的に近づける
  - **類似（Similarity）**: 見た目が似た要素は同じグループとして知覚される → 同カテゴリの情報は同じ色・形・サイズで統一する
  - **閉合（Closure）**: 不完全な形を脳が補完して完全な形として知覚する → フレームや境界線は完全に閉じなくても機能する
  - **連続（Continuity）**: 要素は滑らかな連続体として知覚される → フローやプロセスは視線の流れに沿って配置する
  - **図と地（Figure-Ground）**: 要素は前景と背景に分離して知覚される → 重要な要素を前景として際立たせる
- **実証データ**: 前注意的属性を使った視覚的強調は、テキストベースの強調（太字・下線等）と比較して、検出速度が数百ミリ秒レベルで速い。Colin Ware（2012, *Information Visualization: Perception for Design*）は、前注意的処理が「並列処理」で行われるため、要素数に関わらず一定時間で検出できることを実証した。
- **スライド設計への適用**:
  - 最も伝えたい要素を色・サイズ・位置で際立たせる（1スライド1強調点）
  - 関連する情報は物理的に近くに配置する（近接の原則）
  - カテゴリごとに色を統一する（類似の原則）
  - 視線の動き（左上→右下、またはZ/Fパターン）に沿って重要情報を配置する
- **Claude への指示として**: 「各スライドで最も伝えたい1つの要素を視覚的に強調する（色の変更、サイズの拡大、太字のいずれか1つ）。強調する要素は1スライドにつき1つだけ。関連する情報群は物理的に近接させ、カテゴリが異なるグループ間には明確な空白（ホワイトスペース）を置く。スライドの視覚階層は: タイトル（最大） > キーメッセージ > サポートデータ > 出典 の4層構造とする」
- **ソース**:
  - [Preattentive Attributes and Gestalt Principles - The Data School](https://www.thedataschool.co.uk/adam-sultanov/preattentive-attributes-and-gestalt-principles/) - 解説記事
  - [5 Principles of Visual Perception - UC Davis](https://ucdavisdatalab.github.io/workshop_data_viz_principles/principles-of-visual-perception.html) - 大学教材
  - [Ware, C. (2012). Information Visualization: Perception for Design](https://bbrejova.github.io/viz/pdf/L09_Preattentive_and_Gestalt.pdf) - 講義資料

---

### 原則 4: 系列位置効果によるスライド構成（Serial Position Effect）

- **理論的根拠**: Hermann Ebbinghaus（1885）が発見し、Glanzer & Cunitz（1966）が体系化した系列位置効果。リストの最初の項目（初頭効果 / Primacy Effect）と最後の項目（親近効果 / Recency Effect）は、中間の項目よりも記憶に残りやすい。
  - **初頭効果**: 最初の項目はリハーサル（繰り返し処理）の機会が多いため、長期記憶に転送されやすい
  - **親近効果**: 最後の項目は作業記憶にまだ保持されているため、即座に想起できる
  - **中間の凹み**: 中間の項目は両方の恩恵を受けないため、最も記憶に残りにくい
- **実証データ**:
  - 初頭効果はリストの項目がゆっくり提示されるほど強くなる（Glanzer & Cunitz, 1966）
  - 意思決定が情報提示から時間を置いて行われる場合（> 30秒）、初頭効果が優勢。即座に決定する場合は親近効果が優勢（Haugtvedt & Wegener, 1994）
  - プレゼンテーションの文脈では、開始後2分と終了前2分の内容が最も記憶に残る
- **スライド設計への適用**:
  - **冒頭スライド**（1-3枚目）: 最も重要なメッセージ・結論を配置する（初頭効果の活用）
  - **末尾スライド**（最後の2-3枚）: 行動喚起（Call to Action）と要約を配置する（親近効果の活用）
  - **中間セクション**: 詳細な根拠・データ・プロセス説明を配置する。ただし、中間にも「区切りポイント」を設けて小さな初頭/親近効果を生み出す
  - **プレゼン全体の構造**: 結論→根拠→詳細→要約→行動喚起（逆三角形＋まとめ）
- **Claude への指示として**: 「スライドデッキの構成は以下の順序に従う: (1) タイトルスライド, (2) エグゼクティブサマリー（結論と推奨アクションを先出し）, (3) 詳細スライド群（根拠・データ・分析）, (4) 要約スライド（主要メッセージの反復）, (5) Next Steps / Call to Action。最も重要なメッセージはスライド2枚目（エグゼクティブサマリー）と最終2枚（要約＋CTA）に配置する。中間の詳細セクションは3-5枚ごとにセクション区切りスライドを入れ、小さな初頭効果を生み出す」
- **ソース**:
  - [Serial-position effect - Wikipedia](https://en.wikipedia.org/wiki/Serial-position_effect) - 概要
  - [Glanzer & Cunitz (1966) - Simply Psychology](https://www.simplypsychology.org/primacy-recency.html) - 研究解説
  - [Serial Position Effect - Laws of UX](https://lawsofux.com/serial-position-effect/) - UXデザインへの応用
  - [Serial Position Effect - CXL](https://cxl.com/blog/serial-position-effect/) - 意思決定との関連

---

### 原則 5: ストーリーテリングの認知的効果（Narrative Cognition）

- **理論的根拠**: 人間の脳は物語構造の情報処理に最適化されている。Paul Zak（2014）の神経科学研究により、説得力のある物語はオキシトシン（信頼・共感に関わる神経化学物質）の分泌を促進することが示された。Uri Hasson（Princeton University）のfMRI研究では、話し手と聞き手の脳活動パターンが物語の進行中に同期する「神経カップリング（neural coupling）」が確認された。物語的輸送理論（Narrative Transportation Theory; Green & Brock, 2000）は、物語に没入した状態では批判的思考が抑制され、態度変容が起きやすいことを示す。
- **実証データ**:
  - 物語的輸送状態でオキシトシンを投与された被験者は、寄付行動が **57%** 増加した（Zak, 2014, "Why Inspiring Stories Make Us React"）
  - 物語形式の情報は、事実の羅列と比較して最大 **22倍** 記憶に残りやすい（Stanford研究、Jerome Bruner の推定に基づく。ただしこの「22倍」の数値は厳密な実験データではなく推定値であることに注意）
  - 物語の進行中、聞き手の脳は話し手の脳と同じ領域（前頭前皮質、側頭頭頂接合部、島皮質等）が活性化する（Hasson et al., 2010）
- **スライド設計への適用**:
  - プレゼンテーション全体に物語構造（導入→課題→葛藤→解決→教訓）を持たせる
  - 「現状（As-Is）→ 課題 → 変革（To-Be）」の3幕構成はコンサルティングスライドの基本パターン
  - データスライドにも「So What?（だから何？）」のメッセージを必ず付ける — データだけでは物語にならない
  - 人間的要素（具体的な事例・影響を受ける人々の姿）を含めてオキシトシン反応を促す
- **Claude への指示として**: 「スライドデッキ全体は以下の物語構造に従う: (1) 現状の描写（Context）: 聞き手が共感できる状況を設定, (2) 課題の提示（Complication）: 現状の問題点・ギャップを明示, (3) 解決策の提示（Resolution）: 推奨アクションとその根拠, (4) 将来像（Transformation）: 解決後の姿・期待される成果。各データスライドのタイトルは『数値の説明』ではなく『So What（示唆・解釈）』を記述する（例: NG『売上推移 2020-2025』→ OK『売上は3年連続で減少し、構造改革が急務』）」
- **ソース**:
  - [Zak, P. (2014). Why Inspiring Stories Make Us React - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4445577/) - 学術論文
  - [Hasson et al. - Neural Coupling - Princeton](https://futureofstorytelling.org/case-study/the-neuroscience-of-good-storytelling/) - 研究紹介
  - [Narrative Transportation - PNAS](https://www.pnas.org/doi/10.1073/pnas.2018409118) - 学術論文

---

### 原則 6: チャンキングによる情報の構造化（Chunking）

- **理論的根拠**: George Miller（1956）が提唱し、後続の研究で精緻化されたチャンキング理論。個別の情報断片を意味のあるグループ（チャンク）にまとめることで、作業記憶の実質的な容量を拡張できる。Dirlam（1972）の数学的分析により、1チャンクあたり **3-4項目** が最適であることが示された。チャンキングの効果は、グループ化が学習者にとって **意味がある** 場合にのみ発揮される — 恣意的なグループ化はむしろ認知負荷を増加させる。
- **実証データ**:
  - 最適なチャンクサイズは3-4項目（Dirlam, 1972; Cowan, 2001）
  - 作業記憶でのグループ化は長期記憶でのチャンク形成と密接に関連する（ScienceDirect, 2024）
  - 階層的なチャンキング（チャンクのチャンク）により、4 x 4 = 16項目程度までの情報を構造的に保持できる
- **スライド設計への適用**:
  - 箇条書きは3-4項目でグルーピングする。5項目以上は2グループに分割する
  - 大きなプロセスは3-4ステップのフェーズに分割して表示する
  - 情報の階層を視覚的に表現する（インデント、色分け、枠囲み）
  - MECE（Mutually Exclusive, Collectively Exhaustive）の原則でチャンクを設計すれば、意味のあるグループ化になる
- **Claude への指示として**: 「箇条書きの項目数は1グループあたり3-4個を上限とする。5個以上になる場合は、上位カテゴリでグループ分けして2-3グループに構造化する。プロセスやタイムラインは3-4ステップの大きなフェーズに分割し、各フェーズ内のサブステップは必要に応じて別スライドで展開する。グループ化の基準は『論理的な関連性』であり、単純に均等分割してはならない」
- **ソース**:
  - [Miller, G. (1956). Chunking (psychology) - Wikipedia](https://en.wikipedia.org/wiki/Chunking_(psychology)) - 概要
  - [Dirlam (1972) - Chunking research - NN/g](https://www.nngroup.com/articles/chunking/) - 実践的解説
  - [Grouping in working memory guides chunk formation - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0010027724000817) - 学術論文

---

### 原則 7: 対比効果とフォン・レストルフ効果（Contrast & Von Restorff Effect）

- **理論的根拠**: 対比効果（Contrast Effect）は、2つの刺激を比較する際に差異が増幅される認知バイアス。スライド上で「Before/After」「現状/目標」を並置すると、差異が強調されて意思決定を促進する。フォン・レストルフ効果（Von Restorff Effect / Isolation Effect、1933）は、周囲と異なる特徴を持つ要素が記憶に残りやすいという現象。アンカリング効果（Tversky & Kahneman, 1974）は、最初に提示された数値（アンカー）が後続の判断に過度な影響を与えることを示す。
- **実証データ**:
  - Von Restorff の1933年の研究: 同質なリスト中の異質な項目の再生率は、同質な項目と比較して有意に高い
  - 対比効果は知覚的・認知的に自動的に発生し、意識的に制御することが困難（Effectiviology）
  - アンカリング効果: 最初の数値の提示が後続の数値判断を40-60%の範囲で偏向させる（Tversky & Kahneman, 1974の一連の実験）
- **スライド設計への適用**:
  - **Before/After の並置**: 現状と目標を同じスライドで比較する。差異が視覚的に明らかになる
  - **データのアンカリング**: 大きな数値（市場規模、損失額等）を先に提示し、その後に提案のコストを提示すると、コストが小さく感じられる
  - **1スライド1強調**: 最も重要な要素を色・サイズ・位置で差別化する（Von Restorff 効果）。ただし過剰な強調は効果を打ち消す
  - **競合比較**: 自社の強みが際立つ比較軸を選んで並置する
- **Claude への指示として**: 「比較・対照を行うスライドでは、Before/After または As-Is/To-Be を左右に並置する2カラムレイアウトを使用する。数値の提示では、文脈を与えるアンカー数値を先に示す（例: 『市場規模 5,000億円に対し、投資額はわずか 5億円（0.1%）』）。各スライドで視覚的に強調する要素は1つだけとし、色の変更（アクセントカラー）またはサイズの拡大で差別化する。強調要素が2つ以上あると注意が分散し効果が失われる」
- **ソース**:
  - [Von Restorff Effect - Laws of UX](https://lawsofux.com/von-restorff-effect/) - UXデザイン応用
  - [The Contrast Effect - Effectiviology](https://effectiviology.com/contrast-effect/) - 認知バイアス解説
  - [Anchoring Effect - Wikipedia](https://en.wikipedia.org/wiki/Anchoring_effect) - 概要

---

## 補足原則: Mayer のマルチメディア学習 12原則（スライド設計に特に関連する抜粋）

上記7原則を支える実証的フレームワークとして、Richard Mayer の12原則から特にスライド設計に関連するものを補足する。

| # | 原則名 | 定義 | 効果量 | スライド設計への示唆 |
|---|--------|------|--------|-------------------|
| 1 | マルチメディア原則 | テキスト＋画像 > テキスト単独 | d = 1.67 | 全スライドにテキストと視覚要素を含める |
| 2 | コヒーレンス原則 | 無関係な情報を除くと学習向上 | d = 0.86 | 装飾画像・不要なアニメーションを排除 |
| 3 | シグナリング原則 | 重要情報にキューを付けると学習向上 | d = 0.46 | 矢印・ハイライト・太字で注意を誘導 |
| 4 | 冗長性原則 | 音声＋画像 > 音声＋画像＋テキスト | d = 0.87 | 読み上げるなら画面テキストは最小限に |
| 5 | 空間的近接原則 | 関連するテキストと画像は近くに配置 | — | ラベルは図解の中に直接配置する |
| 6 | セグメンティング原則 | 情報を分割して提示すると学習向上 | d = 0.70 | 複雑な内容は複数スライドに段階分割 |
| 7 | パーソナリゼーション原則 | 会話調の言葉遣いが学習を促進 | — | 「〜である」より「あなたの〜」の語調 |

- **ソース**: [Mayer's 12 Principles of Multimedia Learning - DLI](https://www.digitallearninginstitute.com/blog/mayers-principles-multimedia-learning)

---

## 補足: 認知的流暢性（Cognitive Fluency）

- **理論的根拠**: Alter & Oppenheimer（2009, "Uniting the Tribes of Fluency to Form a Metacognitive Nation"）の研究。情報の処理が容易に感じられる（流暢に処理できる）とき、その情報は真実であり、好ましく、信頼できると判断されやすい。逆に処理が困難だと、不信感・不快感を引き起こす。
- **スライド設計への影響**:
  - 読みやすいフォント、十分なコントラスト、適切な行間はスライドの説得力を直接向上させる
  - 複雑なレイアウト、小さなフォント、低コントラストの配色は、内容そのものへの不信感を生む
  - シンプルで一貫したデザインテンプレートの使用は、認知的流暢性を通じて信頼性を高める
- **Claude への指示として**: 「フォントサイズは本文24pt以上、タイトル36pt以上を基本とする。1スライド内で使用するフォントファミリーは最大2種類。配色は背景と文字のコントラスト比 4.5:1 以上を確保する。レイアウトは全スライドで一貫したグリッドシステムを使用する」
- **ソース**: [Alter & Oppenheimer (2009). Uniting the Tribes of Fluency](https://journals.sagepub.com/doi/10.1177/1088868309341564) - 学術論文

---

## 反直感的な知見

### 知見 1: 情報を減らした方が伝わる（Less is More の認知的根拠）

- **なぜ直感に反するか**: プレゼンターは「情報が多い方が説得力がある」と考えがちだが、認知科学は逆を示す
- **認知科学的な説明**: 作業記憶の容量は約4チャンクに限られる（Cowan, 2001）。容量を超えた情報は処理されず、既に処理された情報の保持すら阻害する（外在的認知負荷の増大）。Mayer のコヒーレンス原則（d = 0.86）は、無関係な情報の除去が学習を有意に向上させることを実証した
- **実務への影響**: 1スライド1メッセージを徹底する。「念のために入れておく」データは認知負荷を増やすだけで、逆に説得力を下げる。補足資料はアペンディックスに回す

### 知見 2: スライドのテキストを読み上げてはいけない（冗長性効果）

- **なぜ直感に反するか**: テキストの読み上げは「強調」に感じられるが、認知科学では逆効果
- **認知科学的な説明**: 言語チャネルは1つしかないため、目で読むテキストと耳から入る音声が競合し、作業記憶がオーバーロードする（冗長性効果、d = 0.87）。画面にテキストがある場合、人は自動的にそれを読み始めるため、音声との同期が崩れる
- **実務への影響**: プレゼンのスライドには要点のみを表示し、詳細は口頭で補足する。あるいは、テキストの代わりに図解を表示し、口頭で説明を加える

### 知見 3: 物語は事実より説得力がある

- **なぜ直感に反するか**: ビジネスの場では「データ・事実・論理」が説得の王道と考えられる
- **認知科学的な説明**: 物語的輸送（Narrative Transportation）状態では批判的思考が抑制され、態度変容が起きやすくなる（Green & Brock, 2000）。物語はオキシトシン分泌を促し、信頼・共感を生む（Zak, 2014）。これはデータの論理的分析とは異なる経路（感情的経路）で説得が行われることを意味する
- **実務への影響**: データだけでは人は動かない。データを物語の中に埋め込む（「このデータが示すのは、現場の〜さんが毎日直面している〜という課題です」）。特に意思決定者への提案では、データ＋ストーリーの組み合わせが最も効果的

### 知見 4: 最初と最後しか覚えていない

- **なぜ直感に反するか**: プレゼンターは全スライドを均等に重要だと考えがち
- **認知科学的な説明**: 系列位置効果（Glanzer & Cunitz, 1966）により、最初（初頭効果）と最後（親近効果）の情報が圧倒的に記憶に残る。中間の情報は最大40-50%の想起率低下が見られる
- **実務への影響**: 最も重要なメッセージを冒頭（エグゼクティブサマリー）と末尾（要約・CTA）に2回配置する。中間セクションはセクション区切りで「小さな冒頭」を作り、記憶の谷間を軽減する

---

## 7原則の統合: Claude への指示テンプレート

以下は、上記7原則を統合した Claude への包括的指示の骨格である。SKILL.md 設計時のベースとして使用する。

```
## スライド設計の認知科学ルール

### 情報量制御
- 1スライド = 1メッセージ + 最大4サポート要素
- 箇条書きは1グループ3-4項目まで。5+は上位カテゴリで分割
- テキストは箇条書き1行あたり10語以内（日本語20文字以内）

### 視覚設計
- 全スライドにテキスト + 視覚要素（図解/チャート/アイコン）
- 1スライド1強調点（色 or サイズで差別化）
- 関連情報は近接配置、異カテゴリ間にはホワイトスペース
- フォント: 本文24pt+、タイトル36pt+、最大2フォントファミリー
- コントラスト比 4.5:1 以上

### 構成設計
- 全体構造: タイトル → エグゼクティブサマリー → 詳細 → 要約 → CTA
- 物語構造: 現状 → 課題 → 解決策 → 将来像
- データスライドのタイトルは「So What（示唆）」で記述
- 3-5枚ごとにセクション区切り

### 比較・強調
- Before/After は左右2カラムで並置
- 数値にはコンテキスト（アンカー）を付ける
- 装飾目的の画像・アニメーションは使用しない
```

---

## 本調査の限界

1. **実験室条件 vs 実務条件の差**: 認知科学の知見の多くは統制された実験環境で得られたものであり、プレゼンテーションの実務条件（ノイズ、中断、聴衆の多様性）では効果サイズが減衰する可能性がある
2. **文化差の未考慮**: 視線のパターン（F/Z パターン）は左から右に読む言語を前提としている。日本語の縦書き文書では異なるパターンが適用される可能性がある。ただし横書きスライドでは概ね適用可能
3. **「22倍」の数値の信頼性**: ストーリーテリングの記憶効果「22倍」は Jerome Bruner の推定に基づくとされるが、元の研究を直接確認できなかった。定性的な方向性（物語 > 事実の羅列）は複数の研究で支持されているが、具体的な倍率は慎重に扱うべき
4. **効果量の文脈依存性**: Mayer の効果量はマルチメディア学習（e-learning）の文脈で計測されたものであり、対面プレゼンテーションへの直接適用には一定の留保が必要

---

## ソース一覧

1. [Cowan, N. (2001). The magical number 4 in short-term memory - PubMed](https://pubmed.ncbi.nlm.nih.gov/11515286/) - 学術論文
2. [Cowan, N. (2010). The Magical Mystery Four - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2864034/) - 学術論文
3. [Sweller, J. Cognitive Load Theory - InstructionalDesign.org](https://www.instructionaldesign.org/theories/cognitive-load/) - 理論解説
4. [Using Cognitive Load Theory to improve slideshow presentations - Chartered College](https://my.chartered.college/impact_article/using-cognitive-load-theory-to-improve-slideshow-presentations/) - 実践記事
5. [Paivio, A. Dual Coding Theory - InstructionalDesign.org](https://www.instructionaldesign.org/theories/dual-coding/) - 理論解説
6. [Dual-coding theory - Wikipedia](https://en.wikipedia.org/wiki/Dual-coding_theory) - 概要
7. [Medina, J. (2008). Brain Rules - Vision](https://brainrules.net/vision/) - 書籍公式サイト
8. [Mayer's 12 Principles of Multimedia Learning - Digital Learning Institute](https://www.digitallearninginstitute.com/blog/mayers-principles-multimedia-learning) - 応用記事
9. [Preattentive Attributes and Gestalt Principles - The Data School](https://www.thedataschool.co.uk/adam-sultanov/preattentive-attributes-and-gestalt-principles/) - 解説
10. [5 Principles of Visual Perception - UC Davis DataLab](https://ucdavisdatalab.github.io/workshop_data_viz_principles/principles-of-visual-perception.html) - 大学教材
11. [Serial-position effect - Wikipedia](https://en.wikipedia.org/wiki/Serial-position_effect) - 概要
12. [Serial Position Effect - Simply Psychology](https://www.simplypsychology.org/primacy-recency.html) - 研究解説
13. [Serial Position Effect - Laws of UX](https://lawsofux.com/serial-position-effect/) - UX応用
14. [Serial Position Effect - CXL](https://cxl.com/blog/serial-position-effect/) - マーケティング応用
15. [Zak, P. (2014). Why Inspiring Stories Make Us React - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4445577/) - 学術論文
16. [Storytelling increases oxytocin - PNAS](https://www.pnas.org/doi/10.1073/pnas.2018409118) - 学術論文
17. [Neuroscience of Good Storytelling - Future of Storytelling](https://futureofstorytelling.org/case-study/the-neuroscience-of-good-storytelling/) - 研究紹介
18. [Chunking (psychology) - Wikipedia](https://en.wikipedia.org/wiki/Chunking_(psychology)) - 概要
19. [How Chunking Helps Content Processing - NN/g](https://www.nngroup.com/articles/chunking/) - UX解説
20. [Von Restorff Effect - Laws of UX](https://lawsofux.com/von-restorff-effect/) - UX応用
21. [The Contrast Effect - Effectiviology](https://effectiviology.com/contrast-effect/) - 認知バイアス解説
22. [Anchoring Effect - Wikipedia](https://en.wikipedia.org/wiki/Anchoring_effect) - 概要
23. [Alter & Oppenheimer (2009). Uniting the Tribes of Fluency - SAGE](https://journals.sagepub.com/doi/10.1177/1088868309341564) - 学術論文
24. [Cognitive Load Theory explained for presentations - Ethos3](https://ethos3.com/cognitive-load-theory-explained-for-presentations/) - 実践記事
25. [Miller's Law - Laws of UX](https://lawsofux.com/millers-law/) - UX応用
