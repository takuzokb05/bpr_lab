# 心理的安全性の定量データ調査

## 調査目的

設計戦略レポートに記載された「心理的安全性の高い組織は生産性が50%向上し、従業員エンゲージメントが76%向上する」という数字の一次ソースを特定し、レポートで使える信頼性の高い定量データを整理する。

---

## 1. 「生産性50%向上」「エンゲージメント76%向上」の出どころ

### 結論: Accenture（2021年）の集計データ。一次ソースではなく、複数調査の集約

- **出典**: Torin Monet (Accenture), "Why psychological safety at work matters to business", 2021年10月28日
  - [Accenture Blog](https://www.accenture.com/us-en/blogs/business-functions-blog/work-psychological-safety)
- **Accentureが主張する数字一覧**:
  - 50% more productivity（生産性50%向上）
  - 76% more engagement（エンゲージメント76%向上）
  - 27% reduction in turnover（離職率27%低下）
  - 74% less stress（ストレス74%低下）
  - 29% more life satisfaction（生活満足度29%向上）
  - 57% more likely to collaborate（協力する可能性57%向上）
  - 26% greater skills preparedness（スキル準備度26%向上）
  - 67% higher probability of applying newly learned skills（新スキル適用確率67%向上）

### 問題点

1. **Accentureは「複数の調査からデータを集約した」と述べているが、各数字の個別の一次ソースを明示していない**
2. Accentureの2020年レポート "Care to Do Better: Building Trust to Leave Your People and Your Business Net Better Off" が関連するが、このレポートの主要発見は「人材の潜在能力の64%が6つの基本ニーズの充足度に影響される」「5%の収益成長が可能」であり、50%/76%という数字は直接含まれていない
3. 調査方法: C-suite 3,200名 + 従業員15,000名、15業種・10カ国（"Care to Do Better"の場合）
4. **「心理的安全性」に限定した調査なのか、より広い「Net Better Off」フレームワークの一部なのかが不明確**
5. 二次ソース（Niagarainstitute.com等）ではこの数字が「Accenture」「Gallup」「HBR」「McKinsey」など異なる出典で引用されており、引用の連鎖で原典が曖昧になっている

### 評価: レポートでの使用は非推奨

- コンサルファームの集計データであり、査読された学術研究ではない
- 一次ソースが特定できないため、DXリーダー100人への提示には適さない
- 「Accenture調べ」として使うことは可能だが、学術的信頼性は低い

---

## 2. Google Project Aristotleの定量的成果データ

### 研究概要
- **期間**: 2012年開始、2年間の調査
- **対象**: 180チーム（エンジニアリング115チーム + セールス65チーム）
- **チームサイズ**: 3〜50人（中央値9人）
- **分析**: 250以上の項目（従業員エンゲージメント調査）、35以上の統計モデル
- **ソース**: [Google re:Work - Understand team effectiveness](https://rework.withgoogle.com/intl/en/guides/understanding-team-effectiveness)

### Google公式が発表した定量データ

**Googleはre:Workの公式ページで具体的な効果量（パーセンテージ）をほとんど公表していない。**

公式に確認できる定量的表現:
1. **「経営陣から効果的と評価される確率が2倍」** — 心理的安全性が高いチームは、低いチームと比較して
2. **「Googleを離職する可能性が低い」** — 具体的な数値は非公開
3. **「より多くの収益をもたらす」** — 具体的な数値は非公開
4. **「多様なアイデアを実装する」** — 定性的評価

### 注意事項

- **「250以上のチーム変数を分析」は不正確**: 正確には「180チームの250以上の項目（従業員調査の項目）」。fact-checkerが指摘済み
- Project Aristotleは社内研究であり、peer-reviewedの学術論文として公開されていない
- Julia Rozovsky（研究リーダー）による発表はあるが、方法論や統計結果の詳細は非公開

### 評価: 定性的発見としては信頼性が高いが、具体的な数値データは限定的

---

## 3. エドモンドソンの研究の定量データ

### 原著論文: Edmondson (1999)

- **論文**: "Psychological Safety and Learning Behavior in Work Teams", *Administrative Science Quarterly*, 44(2), 350-383
- **対象**: 製造業企業の51チーム、個人レベル調査n=427
- **方法**: 7項目のチーム心理的安全性尺度を開発、回帰分析
- **主要発見**:
  - チーム心理的安全性は学習行動と有意に関連する
  - 学習行動がチーム心理的安全性とチームパフォーマンスを媒介する
  - チーム効力感は心理的安全性を統制すると有意でない
- **ソース**: [SAGE Journals](https://journals.sagepub.com/doi/10.2307/2666999), [MIT PDF](https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Group_Performance/Edmondson%20Psychological%20safety.pdf)

### Edmondson & Bransby (2023) レビュー論文

- **論文**: "Psychological Safety Comes of Age: Observed Themes in an Established Literature", *Annual Review of Organizational Psychology and Organizational Behavior*, 10, 55-78
- **内容**: 185本の研究論文（うち定量153本、定性24本、混合8本）のレビュー
- **主要テーマ**: (1) 業務遂行、(2) 学習行動、(3) 職場体験の改善、(4) リーダーシップ
- **発見**: 過去10年の研究はEdmondson (1999)と一貫しており、リーダーシップ→心理的安全性→学習行動の関係が再確認された
- **ソース**: [Annual Reviews](https://psycnet.apa.org/record/2023-48430-003)

### 重要な注記

**エドモンドソンの研究には「生産性50%向上」「エンゲージメント76%向上」という数字は一切登場しない。** エドモンドソンの研究は心理的安全性→学習行動→チームパフォーマンスという媒介モデルを実証したものであり、パーセンテージでの効果量を主張していない。

---

## 4. Frazier et al. (2017) メタ分析 — 最も信頼性の高い定量データ

### 研究概要
- **論文**: "Psychological Safety: A Meta-Analytic Review and Extension", *Personnel Psychology*, 70(1), 113-165
- **規模**: 136の独立サンプル、22,000人以上の個人、約5,000グループ
- **ソース**: [Wiley Online Library](https://onlinelibrary.wiley.com/doi/abs/10.1111/peps.12183)

### 心理的安全性とアウトカムの修正相関係数（ρ）

| アウトカム | 修正相関 ρ | 解釈 |
|-----------|-----------|------|
| 学習行動 (Learning behavior) | .62 | 強い正の相関 |
| 情報共有 (Information sharing) | .52 | 中〜強の正の相関 |
| 満足度 (Satisfaction) | .53 | 中〜強の正の相関 |
| コミットメント (Commitment) | .48 | 中程度の正の相関 |
| 組織市民行動 (Citizenship behaviors) | .32 | 中程度の正の相関 |
| 創造性 (Creativity) | .13 | 弱い正の相関 |

### 先行要因（心理的安全性を高める要因）
- 積極的性格 (Proactive personality)
- 情動安定性 (Emotional stability)
- 学習志向 (Learning orientation)
- ポジティブなリーダー関係 (Positive leader relations) — 包括的リーダーシップ、変革的リーダーシップ、LMX、リーダー信頼

### 評価: レポートで使用する定量データとして最も信頼性が高い

- 査読付き学術誌に掲載
- 136サンプル・22,000人超の大規模メタ分析
- 具体的な効果量（相関係数）が公開されている

---

## 5. Gallupの心理的安全性関連データ

### Gallup Q12メタ分析（2024年版、第11版）

- **規模**: 183,000以上のビジネスユニット、330万人以上の従業員、50以上の業種
- **ソース**: [Gallup Q12 Meta-Analysis](https://www.gallup.com/workplace/321725/gallup-q12-meta-analysis-report.aspx)

### エンゲージメント上位四分位 vs 下位四分位の比較（2024年版）

| 指標 | 上位四分位の優位性 |
|------|-------------------|
| 収益性 (Profitability) | **23%高い** |
| 生産性 (Productivity) | **18%高い** |
| 欠勤率 (Absenteeism) | **81%低い** |
| 離職率 — 低離職業界 (Turnover - low) | **43%低い** |
| 離職率 — 高離職業界 (Turnover - high) | **最大59%低い** |

### Gallupの心理的安全性に直接言及するデータ

- **Q07「職場で自分の意見が尊重されていると感じる」**に強く同意する米国労働者はわずか30%
- この比率を30%→60%に改善した場合の効果:
  - **離職率: 27%低下**
  - **安全事故: 40%低下**
  - **生産性: 12%向上**
- **ソース**: [Gallup - How to Create a Culture of Psychological Safety](https://www.gallup.com/workplace/236198/create-culture-psychological-safety.aspx)

### Gallupのグローバル職場状況（2024年）

- 世界の従業員のうちエンゲージメント状態にあるのはわずか**23%**
- 非エンゲージメントによる世界的な生産性損失: **年間8.8兆ドル**（世界GDPの約9%）
- エンゲージメント差異の**70%**がマネージャーに起因する

### 評価: 信頼性が高い。ただし「心理的安全性」と「エンゲージメント」は別概念

- GallupのQ12はエンゲージメント指標であり、心理的安全性そのものの測定ではない
- Q07（意見の尊重）は心理的安全性に近い概念だが、完全に同一ではない
- レポートでは「エンゲージメントの文脈で」と明示して使用すべき

---

## 6. McKinseyの調査データ

### McKinsey (2021) "Psychological safety and the critical role of leadership development"

- **方法**: 構造方程式モデル（SEM）
- **主要発見**:
  - リーダーシップ開発に多大な投資をしている組織の従業員は、シニアリーダーをより包括的と評価する確率が**64%高い**
  - ポジティブなチーム風土が心理的安全性の最も強い直接的予測因子
  - **89%**の従業員が職場での心理的安全性を不可欠と回答
- **ソース**: [McKinsey](https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/psychological-safety-and-the-critical-role-of-leadership-development)

### 評価: リーダーシップとの関連データとして有用

---

## 7. その他の学術研究

### Hu et al. (2020) — 心理的安全性とチームパフォーマンスの媒介モデル

- **論文**: "How Psychological Safety Affects Team Performance: Mediating Role of Efficacy and Learning Behavior", *Frontiers in Psychology*
- **主要結果**（パス係数）:
  - 心理的安全性 → 学習行動: β = 0.747***
  - 心理的安全性 → チーム効力感: β = 0.596***
  - チーム効力感 → チーム効果性: β = 0.694***
  - 心理的安全性 → チーム効果性（直接効果）: β = 0.037（非有意）
  - **心理的安全性の総効果**: β = 0.722（学習行動とチーム効力感を媒介して）
- **ソース**: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7393970/)

---

## 8. レポートで使える信頼性の高い定量データ（推奨）

### Tier 1: 一次ソースで確認済み、そのまま使用可

| 主張 | 数値 | ソース | 信頼度 |
|------|------|--------|--------|
| エンゲージメント上位チームは収益性が高い | 23%高い | Gallup Q12メタ分析 2024（183K+ BU, 3.3M+ 人） | ★★★ |
| エンゲージメント上位チームは生産性が高い | 18%高い | Gallup Q12メタ分析 2024 | ★★★ |
| エンゲージメント上位チームは離職率が低い | 43〜59%低い | Gallup Q12メタ分析 2024 | ★★★ |
| 心理的安全性は学習行動と強く相関 | ρ = .62 | Frazier et al. 2017（22K+ 人, 136サンプル） | ★★★ |
| 心理的安全性は情報共有と中〜強の相関 | ρ = .52 | Frazier et al. 2017 | ★★★ |
| 心理的安全性は職務満足度と中〜強の相関 | ρ = .53 | Frazier et al. 2017 | ★★★ |
| 「意見が尊重される」と感じる割合を倍増させると生産性12%向上 | 12% | Gallup | ★★★ |
| 心理的安全性の高いチームは経営陣から効果的と評価される確率が2倍 | 2倍 | Google Project Aristotle (re:Work) | ★★☆ |
| 従業員の89%が心理的安全性を不可欠と回答 | 89% | McKinsey 2021 | ★★☆ |

### Tier 2: 使用可だが出典明記が必要

| 主張 | 数値 | ソース | 注意点 |
|------|------|--------|--------|
| 心理的安全性のある職場は生産性50%向上 | 50% | Accenture 2021（Torin Monet） | 一次ソース不明の集計データ |
| 心理的安全性のある職場はエンゲージメント76%向上 | 76% | Accenture 2021 | 同上 |

### 修正案: レポートでの表現

**修正前（設計戦略レポート）**:
> 心理的安全性の高い組織は生産性が50%向上し、従業員エンゲージメントが76%向上する

**修正案A（Gallupデータで差し替え）**:
> Gallupの183,000以上のチームを対象としたメタ分析では、エンゲージメントの高いチームは生産性が18%高く、収益性が23%高い。また、心理的安全性に直結する「職場で自分の意見が尊重されている」と感じる従業員の割合を2倍にすると、生産性は12%向上し、離職率は27%低下する。

**修正案B（Frazierメタ分析で差し替え）**:
> 136の研究・22,000人を対象としたメタ分析（Frazier et al., 2017）では、心理的安全性は学習行動（ρ=.62）や情報共有（ρ=.52）と強い正の相関を示す。Googleの社内研究でも、心理的安全性の高いチームは経営陣から効果的と評価される確率が2倍であった。

**修正案C（Accentureを残す場合）**:
> Accenture（2021）の集計によれば、心理的安全性の高い職場は生産性50%向上、エンゲージメント76%向上と報告されている。ただし、より厳密なGallupの調査では生産性向上は12〜18%とされており、数字の解釈には幅がある。

---

## 情報の信頼性評価

- **一次ソース（学術・公式）**: 5件
  - Edmondson (1999) — 原著論文
  - Frazier et al. (2017) — メタ分析（最重要）
  - Edmondson & Bransby (2023) — レビュー論文
  - Hu et al. (2020) — 媒介モデル研究
  - Google re:Work — 公式ページ
- **準一次ソース（大規模調査）**: 2件
  - Gallup Q12メタ分析 (2024) — 企業調査だが規模・継続性で信頼性高
  - McKinsey (2021) — コンサルだがSEMモデル使用
- **二次ソース（注意が必要）**: 1件
  - Accenture (2021) — 集計データ、一次ソース不明

## ソース一覧

1. [Google re:Work - Understand team effectiveness](https://rework.withgoogle.com/intl/en/guides/understanding-team-effectiveness) - 公式
2. [Edmondson (1999) - Psychological Safety and Learning Behavior in Work Teams](https://journals.sagepub.com/doi/10.2307/2666999) - 学術（原著）
3. [Frazier et al. (2017) - Psychological Safety: A Meta-Analytic Review and Extension](https://onlinelibrary.wiley.com/doi/abs/10.1111/peps.12183) - 学術（メタ分析）
4. [Edmondson & Bransby (2023) - Psychological Safety Comes of Age](https://psycnet.apa.org/record/2023-48430-003) - 学術（レビュー）
5. [Gallup - How to Create a Culture of Psychological Safety](https://www.gallup.com/workplace/236198/create-culture-psychological-safety.aspx) - 企業調査
6. [Gallup Q12 Meta-Analysis 2024](https://www.gallup.com/workplace/321725/gallup-q12-meta-analysis-report.aspx) - 企業調査
7. [McKinsey - Psychological safety and the critical role of leadership development](https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/psychological-safety-and-the-critical-role-of-leadership-development) - コンサル
8. [Accenture - Psychological Safety: The Corporate Culture Code](https://www.accenture.com/us-en/blogs/business-functions-blog/psychological-safety-corporate-culture) - コンサル
9. [Hu et al. (2020) - How Psychological Safety Affects Team Performance](https://pmc.ncbi.nlm.nih.gov/articles/PMC7393970/) - 学術
10. [Accenture - Care to Do Better (2020)](https://newsroom.accenture.com/news/2020/building-trust-and-fulfilling-peoples-core-needs-at-work-can-help-companies-achieve-increased-business-performance-even-amid-weak-gdp-growth-according-to-new-research-from-accenture) - コンサル
