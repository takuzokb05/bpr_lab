# Q1b: コンサル実務に基づくスライド設計原則

> **担当**: battle-consultant
> **作成日**: 2026-02-26
> **ステータス**: 初版（fact-checker / devils-advocate レビュー前）

---

## コンサル実務に基づくスライド設計原則

### 原則 1: アクションタイトル（Action Title）

- **現場の現実**: McKinsey / BCG の役員向けデッキでは、読み手がスライドのタイトルだけを流し読みして全体のストーリーを把握することを前提に設計される。タイトルが「売上推移」のような単なるラベルであれば、忙しい経営層は「で、何？」と感じて先を読まない。BCG では「タイトルだけ読めばプレゼン全体が分かるように書け」と訓練される（出典1）。
- **やるべきこと**:
  - 各スライドのタイトルを「主張を含む完全な文」にする（例: 「直接営業が収益成長の主要ドライバーであり、注力により10〜15%の増収が見込める」）
  - 最大15語（英語）/ 2行以内に収める
  - 能動態を使う（受動態は避ける）
  - タイトルだけを A4 1枚に並べて読み、ストーリーが通るか検証する（Ghost Deck テスト）
- **やってはいけないこと**:
  - ラベル型タイトル（「市場概況」「財務分析」）を使う
  - 当たり前すぎて洞察のないタイトル（「売上を伸ばせば収益が増える」）
  - フォントサイズを縮小して長文タイトルを押し込む
- **判断基準**: タイトルだけを抜き出して読んだとき、プレゼンの結論と根拠が第三者に伝わるか。伝わらなければ失格。
- **Claude への指示として**: 「各スライドのタイトルは、そのスライドの核心的な主張を1文で述べるアクションタイトルにせよ。ラベル型（"市場概況"等）は禁止。最大2行、能動態で書け。全スライドのタイトルだけ並べてストーリーが通ることを検証せよ。」
- **ソース**: [How to Write Slide Action Titles Like McKinsey](https://slideworks.io/resources/how-to-write-action-titles-like-mckinsey) - Slideworks; [Crafting Slide Action Titles Like A Consultant](https://slidescience.co/action-titles/) - SlideScience; [BCG's Approach to Great Slides](https://slideworks.io/resources/bcg-approach-to-great-slides-practical-guide-from-former-consultant) - Slideworks

### 原則 2: ピラミッド原則（Pyramid Principle）— 結論ファースト

- **現場の現実**: コンサルティングファームのプレゼンは「最初に結論、次に根拠」のトップダウン構造を徹底する。Barbara Minto が McKinsey 在籍時に体系化したこのフレームワークは、現在も MBB（McKinsey, BCG, Bain）のデッキ構築の基盤である。分析のプロセスを時系列で見せる（ボトムアップ）のは致命的な誤り — 経営層は「お前の思考過程」ではなく「結論と推奨アクション」を求めている（出典2）。
- **やるべきこと**:
  - デッキの冒頭に推奨アクション（Recommendation）を置く
  - 各セクションも結論→根拠の順で構成する
  - 支持論拠は 3つ（±1）に絞り、各々をデータで裏付ける
  - MECE（Mutually Exclusive, Collectively Exhaustive）で論拠を構造化する
- **やってはいけないこと**:
  - 分析のプロセス順にスライドを並べる（「まずデータ収集→分析→結果→結論」）
  - 結論を最終スライドまで引っ張る（「サプライズエンディング」は小説だけでよい）
  - 支持論拠が重複する（MECEの "ME" 違反）
- **判断基準**: スライド1〜3を読んだ時点で、読み手が「何をすべきか」を理解できるか。
- **Claude への指示として**: 「デッキ構造はピラミッド原則に従え。最初のスライドで結論・推奨アクションを述べ、後続スライドで根拠をMECE構造で展開する。分析プロセスの時系列提示は禁止。支持論拠は3つ（±1）に絞れ。」
- **ソース**: [The Pyramid Principle: McKinsey's Secret](https://winningpresentations.com/pyramid-principle-presentations/) - WinningPresentations; [Barbara Minto 公式サイト](https://www.barbaraminto.com/); [MECE Framework - Slideworks](https://slideworks.io/resources/mece-mutually-exclusive-collectively-exhaustive)

### 原則 3: SCQA / SCR フレームワーク（ストーリーライン設計）

- **現場の現実**: MBB のエグゼクティブサマリーは例外なく SCQA（Situation-Complication-Question-Answer）または SCR（Situation-Complication-Resolution）フレームワークに従っている。これは聴衆を「なぜ今この話をするのか」→「何が問題か」→「どうすべきか」と導く構造であり、初めてデッキを見る人でもストーリーに自然に入れる。フレームワークなしで書かれたデッキは「で、何の話？」と最初の30秒で離脱される（出典3）。
- **やるべきこと**:
  - エグゼクティブサマリーを SCQA で構成する
  - Situation: 合意済みの前提（聴衆が「そうだね」と頷く事実）
  - Complication: 今行動が必要な理由（脅威 or 機会）
  - Question: 乗り越えるべき問い
  - Answer: 推奨アクションとその根拠
- **やってはいけないこと**:
  - 状況説明を延々と続ける（Situation が長すぎる）
  - Complication なしにいきなり Answer を提示する（文脈がなく説得力ゼロ）
  - 複数の Complication を混在させる（論点が散漫になる）
- **判断基準**: エグゼクティブサマリー1枚を読んだとき、「なぜ今この問題に取り組むのか」「何をすべきか」が伝わるか。
- **Claude への指示として**: 「エグゼクティブサマリーは SCQA フレームワークで構成せよ。Situation（合意済み前提）→ Complication（なぜ今行動が必要か）→ Question（核心的な問い）→ Answer（推奨アクション）の順で書け。Situation は3行以内に抑え、Complication に最も力を入れよ。」
- **ソース**: [SCQA Framework - Management Consulted](https://managementconsulted.com/scqa-framework/); [ModelThinkers - Minto Pyramid & SCQA](https://modelthinkers.com/mental-model/minto-pyramid-scqa); [PowerPoint Storytelling: SCQA Framework - Analyst Academy](https://www.theanalystacademy.com/powerpoint-storytelling/)

### 原則 4: 1スライド1メッセージ

- **現場の現実**: McKinsey のスライド設計の鉄則は「1スライドに1つの主張」。複数のメッセージを1枚に詰め込むと、読み手は何が重要か判断できず、結果として何も伝わらない。BCG でも「重要なポイントが複数あるスライドは分割せよ」と指導される（出典4）。
- **やるべきこと**:
  - 各スライドが証明する主張を1つだけ定義する
  - その主張をアクションタイトルに反映する
  - スライド本体の全要素（チャート、テキスト、図）がその1つの主張を支える構成にする
- **やってはいけないこと**:
  - 1枚に2つ以上のチャートを並べて「AもBも示す」
  - 「ついでにこのデータも」と関連性の薄い情報を追加する
  - 主張と無関係な装飾的グラフィックを入れる
- **判断基準**: スライドから1要素を取り除いたとき、メッセージが成立しなくなるか。成立するなら、その要素は不要。
- **Claude への指示として**: 「各スライドには1つの主張のみ。アクションタイトルがその主張を述べ、本体の全要素（チャート、テキスト、図）がその主張を裏付ける構成にせよ。主張に直接貢献しない要素は削除せよ。」
- **ソース**: [How McKinsey Consultants Make Presentations](https://slideworks.io/resources/how-mckinsey-consultants-make-presentations) - Slideworks; [BCG's Approach to Great Slides](https://slideworks.io/resources/bcg-approach-to-great-slides-practical-guide-from-former-consultant) - Slideworks

### 原則 5: Ghost Deck（骨格先行）でデッキを設計する

- **現場の現実**: MBB コンサルタントはスライド作成の最初のステップとして Ghost Deck（ゴーストデッキ）を作る。これはアクションタイトルのみを並べた骨格ドラフトで、チャートの粗いスケッチを添える程度のもの。本体のデザインやデータ収集に着手する前に、ストーリーラインの論理構造をマネージャーと合意する。これにより「80枚作ってから方向転換」という壊滅的な手戻りを防ぐ（出典5）。
- **やるべきこと**:
  - スライド作成の第一歩として、アクションタイトルだけを全スライド分書き出す
  - タイトルだけを読み通してストーリーの論理チェックを行う
  - 各スライドに必要なデータ・チャートの種類をラフスケッチで示す
  - ステークホルダーと Ghost Deck の段階で方向性を合意する
- **やってはいけないこと**:
  - いきなりデザインやデータ収集から始める
  - Ghost Deck を省略して「頭の中で構成を考えた」と済ませる
- **判断基準**: Ghost Deck（タイトル一覧）の段階で、ストーリーの論理的な穴や飛躍がないか。
- **Claude への指示として**: 「スライド生成は2段階で行え。Step 1: 全スライドのアクションタイトルを一覧として生成し、ストーリーラインの論理を検証する（Ghost Deck）。Step 2: 承認後、各スライドの本体を生成する。Step 1 を省略して直接スライドを生成してはならない。」
- **ソース**: [How to Write Slide Action Titles Like McKinsey](https://slideworks.io/resources/how-to-write-action-titles-like-mckinsey) - Slideworks; [How to Craft Slides like MBB Consultants](https://mconsultingprep.com/how-consultants-make-mbb-slides) - MConsultingPrep

### 原則 6: データ・インク比率の最大化（ビジュアルデザイン）

- **現場の現実**: Edward Tufte の「データ・インク比率」はコンサルスライドの視覚設計の基盤である。チャートジャンク（装飾的な3Dエフェクト、グラデーション、不要なグリッド線）は情報の読み取りを妨げる。McKinsey は色使いを極限まで抑え（白黒印刷でも分かるレベル）、BCG はアイコンや図を多用するがやはり装飾は排除する。Nancy Duarte は「聴衆は各スライドを約3秒で理解できるべき」と述べている（出典6, 出典7）。
- **やるべきこと**:
  - チャートのデータインク比率を最大化する（データを示すインク / 全インク）
  - 色は2〜3色に限定し、強調に使う（灰色がベース、アクセントカラー1〜2色）
  - 軸ラベル、凡例、出典を必ず記載する
  - ホワイトスペースを十分に確保する
  - テキストサイズはスライド本体で最大2種類（例: 見出し16pt、本文14pt）
- **やってはいけないこと**:
  - 3Dチャート、グラデーション、影、装飾的クリップアートを使う
  - 5色以上を使う
  - テキストでスライドを埋め尽くす
  - フォントサイズを3種類以上使う
- **判断基準**: 「スクイントテスト」— スライドを離れた距離から見て（目を細めて）、キーメッセージが判別できるか。
- **Claude への指示として**: 「チャートは Tufte のデータ・インク比率原則に従い、装飾要素（3D、グラデーション、影）を一切排除せよ。色は灰色ベース + アクセント2色以内。テキストサイズはスライド本体で2種類まで。ホワイトスペースを十分確保し、情報密度と可読性を両立させよ。」
- **ソース**: [Tufte's Principles of Data-Ink](https://jtr13.github.io/cc19/tuftes-principles-of-data-ink.html); [Slide:ology - Nancy Duarte](https://www.duarte.com/resources/books/slideology/); [Decoding McKinsey's Visual Identity](https://slideworks.io/resources/decoding-mckinseys-visual-identity-and-powerpoint-template) - Slideworks

### 原則 7: 聴衆レベル別のスライド設計

- **現場の現実**: 同じプロジェクトでも、役員会向けと実務チーム向けでスライドの設計は根本的に変わる。役員会では最初の3分で見解を形成するため、冒頭に推奨アクションが必要。一方、実務チーム向けには詳細なデータ、技術的な補足、ステークホルダーマップ等が必要になる。「万人向けのデッキ」は存在しない（出典8）。
- **やるべきこと**:
  - 経営層向け: 推奨アクション先行、スライド数10〜15枚、詳細はAppendixに退避
  - 実務担当向け: 分析の詳細を含む、スライド数20〜30枚、技術的補足あり
  - 外部パートナー向け: 文脈説明を厚く、前提共有に注力
  - マネジメント層が上がるごとに、詳細度を1段階下げる
- **やってはいけないこと**:
  - 経営層向けデッキに80枚のスライドを用意する
  - 実務チーム向けデッキから技術詳細を省く
  - 全聴衆に同じデッキを使い回す
- **判断基準**: 対象聴衆が、デッキを受け取って3分以内に「自分に何が求められているか」を理解できるか。
- **Claude への指示として**: 「スライド生成時にターゲット聴衆を必ず確認せよ。経営層向け: 推奨アクション先行、10〜15枚、詳細はAppendix。実務担当向け: 分析詳細を含む、20〜30枚。聴衆が指定されない場合は確認を求めよ。」
- **ソース**: [The Board Presentation Structure Nobody Teaches You](https://winningpresentations.com/board-presentation-structure/) - WinningPresentations; [Executive Presentations - Deb Liu](https://debliu.substack.com/p/executive-presentations-a-guide-to); [How Consulting Firms Use Presentation Design](https://www.rekarda.com/blog/how-consulting-firms-use-presentation-design-to-win-multi-million-dollar-contracts)

### 原則 8: フォーマッティングの一貫性

- **現場の現実**: MBB のデッキでは、フォント、色、配置の不整合は即座に信頼性を損なう。経営層は「この程度のフォーマットも揃えられないチームに、億単位の投資判断を任せられるか？」と考える。McKinsey は Arial（本文）+ Georgia（タイトル）、BCG は Trebuchet MS の1書体統一という厳格なルールを敷いている（出典9）。
- **やるべきこと**:
  - フォントは1〜2書体に統一する
  - 色パレットを事前定義し、全スライドで一貫させる
  - 全スライドに日付、ページ番号、出典、クライアントロゴを含める
  - テキストと図形のアライメント（整列）を徹底する
  - チャートの軸ラベル、凡例、注釈を統一フォーマットにする
- **やってはいけないこと**:
  - スライドごとにフォントや色が変わる
  - テキストボックスが微妙にずれている
  - ページ番号や日付が一部のスライドで欠落している
  - 異なるチャートライブラリのスタイルが混在する
- **判断基準**: デッキ全体を高速でめくったとき、視覚的な「ちらつき」がないか。あれば不整合がある。
- **Claude への指示として**: 「デッキ全体でフォント（1〜2書体）、色パレット（定義済み3色以内 + 灰色系）、レイアウトグリッドを統一せよ。全スライドにページ番号、日付、出典注を含めよ。異なるスタイルのチャートが混在しないよう、チャートテンプレートを統一せよ。」
- **ソース**: [Decoding McKinsey's Visual Identity and PowerPoint Template](https://slideworks.io/resources/decoding-mckinseys-visual-identity-and-powerpoint-template) - Slideworks; [Consulting Slide Standards - Deckary](https://deckary.com/blog/consulting-slide-standards)

---

## 致命的ミスのパターン集

| # | ミスのパターン | なぜダメか | 修正方法 |
|---|-------------|----------|---------|
| 1 | **ラベル型タイトル**（「売上推移」「市場分析」） | 読み手に解釈を丸投げ。忙しい経営層は自分で「So What?」を考えてくれない | アクションタイトルに書き換える（「国内市場は前年比12%縮小し、海外展開が急務」） |
| 2 | **結論が最後**（ボトムアップ構成） | 経営層は3分で見解を形成する。結論にたどり着く前に離脱される | ピラミッド原則で結論→根拠の順に再構成 |
| 3 | **1スライドに複数メッセージ** | 何が重要か判断できず、結果として何も伝わらない | 1スライド1メッセージに分割 |
| 4 | **仮説なしの分析** | 「海を沸かす」（Boil the Ocean）— 焦点のない分析は時間の浪費 | 分析前に仮説を立て、検証/棄却のフレームで進める |
| 5 | **チャートジャンク** | 3Dエフェクト、グラデーション、装飾がデータの読み取りを妨げる | Tufte のデータ・インク比率原則を適用し、装飾を排除 |
| 6 | **出典の欠落** | 「それ、何のデータ？」で信頼性が崩壊する | 全データに出典（情報源、年度）を脚注で記載 |
| 7 | **フォーマットの不整合** | フォント、色、配置のずれは「雑な仕事」の印象を与え、提案内容の信頼性を損なう | テンプレートを定義し、全スライドに適用 |
| 8 | **聴衆無視の情報量** | 経営層に80枚、実務チームに5枚 — どちらも機能しない | 聴衆レベルに応じてスライド数と詳細度を調整 |
| 9 | **SCQA なしのサマリー** | 文脈（なぜ今この話をするのか）がなく、提案が唐突に感じられる | SCQA フレームワークでサマリーを再構成 |
| 10 | **データなしの主張** | 「売上が伸びると思います」は意見であり、根拠ではない | 定量データ（数字、比較、トレンド）で主張を裏付ける |

**ソース**: [Top 12 Mistakes to Avoid - My Consulting Offer](https://www.myconsultingoffer.org/case-study-interview-prep/consulting-slide-deck/); [Consulting Slide Deck Do's and Don'ts - Management Consulted](https://managementconsulted.com/consulting-slide-deck/); [9 Critical Consulting Slide Deck Mistakes - Digital Hill](https://www.digitalhill.com/blog/9-critical-consulting-slide-deck-mistakes-that-kill-your-credibility/)

---

## スライドタイプ別テンプレート要件

### 1. エグゼクティブサマリー

- **必須要素**: SCQA 構造（Situation → Complication → Question → Answer）、推奨アクション、次のステップ
- **構造**: 1〜2枚。テキスト主体。箇条書きで要点を整理。最重要のアクションアイテムを明示
- **典型的な失敗**: Situation が長すぎて Complication に到達しない; 推奨アクションが曖昧（「検討する」ではなく「X月までにYを実行する」と書く）
- **Claude への指示**: 「SCQA構造で書け。Situation は3行以内。Answer に必ず具体的なアクションアイテム（担当・期限・内容）を含めよ。」

### 2. データスライド（チャート/グラフ）

- **必須要素**: アクションタイトル（データが示す主張）、チャート1種類、軸ラベル・凡例・出典注
- **構造**: チャートが面積の60〜70%を占める。タイトルが主張、チャートが証拠。テイクアウェイボックス（「主要な読み取り」）を添えてもよい
- **典型的な失敗**: チャートのタイプが主張と不一致（例: 時系列データに円グラフ）; 軸ラベルの欠落; 複数チャートの詰め込み
- **Claude への指示**: 「データスライドはチャート1つ + アクションタイトルの構成。チャートタイプはデータの性質に合わせて選択せよ（比較→棒グラフ、推移→折れ線、構成比→積み上げ棒 or ウォーターフォール）。円グラフは原則使用禁止（構成要素が3以下の場合のみ許容）。」

### 3. 比較スライド

- **必須要素**: アクションタイトル（比較の結論）、比較対象を並列配置、評価基準の明示
- **構造**: 2〜4列のマトリクスまたは表形式。評価基準を行、比較対象を列に配置。色やアイコンで優劣を視覚化
- **典型的な失敗**: 評価基準が MECE でない; 比較対象が多すぎる（5以上は情報過多）; 結論（推奨選択肢）が不明
- **Claude への指示**: 「比較スライドは2〜4選択肢を並列配置し、MECE な評価基準で比較せよ。アクションタイトルで推奨選択肢とその理由を明示せよ。」

### 4. ロードマップ / アクションプラン

- **必須要素**: アクションタイトル、フェーズ区分（3〜5段階）、各フェーズのマイルストーン・期限・担当
- **構造**: 横軸に時間、縦軸にワークストリーム。ガントチャート形式またはスイムレーン形式。現在地を明示
- **典型的な失敗**: フェーズが多すぎる（6以上は認知負荷超過）; マイルストーンに期限がない; 「とりあえず全部書いた」感
- **Claude への指示**: 「ロードマップは3〜5フェーズに分割し、各フェーズにマイルストーン（内容・期限・担当）を明記せよ。横軸=時間、縦軸=ワークストリームのスイムレーン形式を推奨。」

### 5. フレームワークスライド

- **必須要素**: アクションタイトル、フレームワーク図（2x2マトリクス、フロー図、ツリー図等）、各要素の簡潔な説明
- **構造**: 中央にフレームワーク図、周辺にラベルと短い説明。テキスト量は最小限
- **典型的な失敗**: フレームワークが複雑すぎる（要素数が多すぎ）; 各象限/要素の説明がない; フレームワークが結論と無関係
- **Claude への指示**: 「フレームワークスライドは図を中心に配置し、各要素に1行の説明を付けよ。フレームワークの選択理由をタイトルで示せ。」

### 6. タイトルスライド / セクションディバイダー

- **必須要素**: プレゼンテーションタイトル（またはセクション名）、日付、作成者/クライアント名
- **構造**: 最小限の要素で構成。セクションディバイダーはデッキの論理構造を視覚的に示す「休憩ポイント」
- **典型的な失敗**: 情報過多（タイトルスライドにアジェンダまで詰め込む）; ブランドガイドラインとの不整合
- **Claude への指示**: 「タイトルスライドはプレゼンタイトル、日付、クライアント名のみ。セクションディバイダーはセクション名と短い導入文（1文）のみ。」

---

## ストーリーライン設計の実務的パターン

### パターン A: SCR（Situation-Complication-Resolution）

最も汎用性が高い。MBB のエグゼクティブサマリーの標準形式。

```
[Situation] 当社の国内売上は過去5年間安定的に成長してきた
[Complication] しかし主力市場の成長率は2025年以降鈍化が見込まれ、現状維持では3年後に減収に転じる
[Resolution] 東南アジア3カ国への展開を2026年Q3までに開始し、2028年までに海外売上比率20%を達成する
```

### パターン B: Past → Present → Future

変革提案や戦略レビューに適する。

```
[Past] 過去の施策とその成果
[Present] 現在の状況と課題
[Future] 推奨するアクションと期待される効果
```

### パターン C: Problem → Evidence → Solution → Impact

データ駆動型の提案に適する。

```
[Problem] 顧客離反率が6ヶ月で15%上昇
[Evidence] 離反顧客の87%がオンボーディング期間中に離脱（データ分析）
[Solution] オンボーディングプロセスの再設計（具体的なアクション）
[Impact] 離反率を8%に低減、ARR +$2.4M の効果
```

**ソース**: [SCQA Framework - Analytic Storytelling](https://analytic-storytelling.com/scqa-what-is-it-how-does-it-work-and-how-can-it-help-me/); [PowerPoint Storytelling - Analyst Academy](https://www.theanalystacademy.com/powerpoint-storytelling/)

---

## McKinsey vs BCG: スタイルの違い

| 観点 | McKinsey | BCG |
|------|----------|-----|
| **カラーパレット** | 白+青ベース、極限までミニマル。白黒印刷でも判別可能 | より多彩だが抑制的。アイコン・図解を積極活用 |
| **フォント** | Arial（本文）+ Georgia（タイトル） | Trebuchet MS 一本 |
| **チャート使用** | テキストとチャートのバランス型 | チャート・グラフ・表を大きく使い、ビジュアル重視 |
| **情報密度** | テキストによる論理展開が強い | 視覚的な情報伝達に強い |
| **共通点** | アクションタイトル、ピラミッド原則、SCQA、MECE、Ghost Deck、1スライド1メッセージ — 全て共通 |

**ソース**: [think-cell: 外資コンサルパワポ最強説](https://www.think-cell.com/ja/resources/content-hub/learning-from-the-global-consulting-firms-powerpoint); [BCG's Approach to Great Slides](https://slideworks.io/resources/bcg-approach-to-great-slides-practical-guide-from-former-consultant) - Slideworks

---

## ソース一覧

1. [BCG's Approach to Great Slides: A Practical Guide From a Former Consultant](https://slideworks.io/resources/bcg-approach-to-great-slides-practical-guide-from-former-consultant) - Slideworks（元BCGコンサルによるスライド設計ガイド）
2. [The Pyramid Principle: McKinsey's Secret (Used Wrong by Most)](https://winningpresentations.com/pyramid-principle-presentations/) - WinningPresentations
3. [SCQA Framework - Management Consulted](https://managementconsulted.com/scqa-framework/) - ManagementConsulted
4. [How McKinsey Consultants Make Presentations](https://slideworks.io/resources/how-mckinsey-consultants-make-presentations) - Slideworks
5. [How to Write Slide Action Titles Like McKinsey (With Examples)](https://slideworks.io/resources/how-to-write-action-titles-like-mckinsey) - Slideworks
6. [Tufte's Principles of Data-Ink](https://jtr13.github.io/cc19/tuftes-principles-of-data-ink.html) - Columbia University
7. [Slide:ology - Nancy Duarte](https://www.duarte.com/resources/books/slideology/) - Duarte公式
8. [The Board Presentation Structure Nobody Teaches You](https://winningpresentations.com/board-presentation-structure/) - WinningPresentations
9. [Decoding McKinsey's Visual Identity and PowerPoint Template](https://slideworks.io/resources/decoding-mckinseys-visual-identity-and-powerpoint-template) - Slideworks
10. [3 Great Examples Of Slide Structure From McKinsey, Bain, And BCG](https://www.theanalystacademy.com/consulting-slide-structure/) - Analyst Academy
11. [Top 12 Mistakes to Avoid When Making a Consulting Slide Deck](https://www.myconsultingoffer.org/case-study-interview-prep/consulting-slide-deck/) - MyConsultingOffer
12. [Barbara Minto 公式サイト](https://www.barbaraminto.com/) - The Minto Pyramid Principle
13. [MECE Framework - Slideworks](https://slideworks.io/resources/mece-mutually-exclusive-collectively-exhaustive) - Slideworks
14. [ModelThinkers - Minto Pyramid & SCQA](https://modelthinkers.com/mental-model/minto-pyramid-scqa) - ModelThinkers
15. [SCQA Framework - Analytic Storytelling](https://analytic-storytelling.com/scqa-what-is-it-how-does-it-work-and-how-can-it-help-me/) - Analytic Storytelling
16. [PowerPoint Storytelling: SCQA Framework - Analyst Academy](https://www.theanalystacademy.com/powerpoint-storytelling/) - Analyst Academy
17. [think-cell: 外資コンサルパワポ最強説](https://www.think-cell.com/ja/resources/content-hub/learning-from-the-global-consulting-firms-powerpoint) - think-cell
18. [Consulting Slide Standards: The Unwritten Rules MBB Consultants Follow](https://deckary.com/blog/consulting-slide-standards) - Deckary
19. [Executive Presentations: A Guide - Deb Liu](https://debliu.substack.com/p/executive-presentations-a-guide-to) - Substack
20. [How Consulting Firms Use Presentation Design to Win Contracts](https://www.rekarda.com/blog/how-consulting-firms-use-presentation-design-to-win-multi-million-dollar-contracts) - Rekarda
