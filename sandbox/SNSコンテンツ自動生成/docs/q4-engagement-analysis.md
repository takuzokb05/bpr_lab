# Q4: エンゲージメント分析手法

## 主要な発見

### 1. SNSエンゲージメント分析の一般的な手法

#### 1-1. エンゲージメント指標の定義と計算

1. **プラットフォーム別エンゲージメント指標（2026年版）**
   - 要点: 2026年時点で、各プラットフォームのアルゴリズムが重視する指標が変化している。InstagramはReels・Stories・投稿すべてで「Views（閲覧数）」を主要指標に統一。LinkedInは「Dwell Time（滞在時間）」と「Saves（保存）」を単純ないいねより重視。TikTokはシェア・保存・完視聴率をアルゴリズムスコアに組み込んでいる。
   - ソース: [The Social Media Metrics to Track in 2026 | Sprout Social](https://sproutsocial.com/insights/social-media-metrics/)

2. **エンゲージメント率の計算方法**
   - 要点: エンゲージメント率 = エンゲージメント数（リアクション + コメント + クリック等の合計）/ リーチ数 x 100。プラットフォームごとに分母（リーチ数 vs フォロワー数 vs インプレッション数）が異なるため、比較時は計算基準の統一が必要。
   - ソース: [SNSにおけるエンゲージメントとは？ | Cuenote](https://www.cuenote.jp/library/marketing/sns_engagement.html)

3. **プラットフォーム別ベンチマーク（2026年）**
   - 要点: Social Insiderによる大規模ベンチマーク分析では、プラットフォームごとにエンゲージメント率・インプレッション・いいね数・コメント数・シェア数・投稿頻度の基準値が公開されている。これを自社データと比較することで、相対的なパフォーマンス評価が可能。
   - ソース: [Social Media Benchmarks For 2026 | Social Insider](https://www.socialinsider.io/social-media-benchmarks)

#### 1-2. 分析アプローチの分類

| アプローチ | 概要 | 代表的手法 |
|-----------|------|-----------|
| **定量分析** | いいね・コメント・シェア等の数値集計 | 時系列分析、ベンチマーク比較 |
| **テキスト分析** | 投稿文や返信のテキストマイニング | 感情分析、トピックモデリング |
| **予測分析** | 機械学習によるエンゲージメント予測 | XGBoost、Random Forest、BERT |
| **解釈可能AI** | 予測モデルの要因分析 | SHAP、特徴量重要度 |

---

### 2. テキスト特徴量とエンゲージメントの相関分析手法

#### 2-1. 言語特徴量を用いた予測モデル

4. **言語特徴量による機械学習アプローチ（Springer, 2024）**
   - 要点: 51,615件のFacebook投稿を対象に、テキスト特徴量（TF-IDF）を抽出し、SVM・Naive Bayes・MLP（多層パーセプトロン）で投稿の成功/失敗を分類。最良モデルで精度72.2%（F1スコア）を達成。テキスト特徴量だけでもエンゲージメント予測に一定の有用性があることを実証。
   - ソース: [Using Linguistic Features to Predict Social Media Engagement | SpringerLink](https://link.springer.com/chapter/10.1007/978-981-97-1552-7_27)

5. **感情・時間特徴量による予測（arXiv, 2025）**
   - 要点: 感情特徴量（emotional features）と時間特徴量を組み合わせたモデルで、いいね数の予測はR^2 = 0.98と極めて高精度。一方、コメント数はR^2 = 0.41にとどまり、コメントはテキスト・感情以外の要因（コンテキスト、コミュニティ特性等）に依存することが判明。
   - ソース: [Predicting Social Media Engagement from Emotional and Temporal Features | arXiv](https://arxiv.org/abs/2508.21650)

6. **トピック・センチメントとエンゲージメントの因果分析（Chun et al., 2021）**
   - 要点: ToyotaのFacebookファンページを対象に、テキスト分析（トピックモデリング + 感情極性分析）でエンゲージメントへの影響を検証。負の二項回帰モデルで仮説検証。動画投稿、特定トピック、感情極性（ポジティブ/ネガティブ）がエンゲージメントに有意な影響を与えることを確認。
   - ソース: [Using text analytics to measure an effect of topics and sentiments on social-media engagement | SAGE Journals](https://journals.sagepub.com/doi/full/10.1177/18479790211016268)

7. **XGBoostによるエンゲージメント予測とSHAP解釈**
   - 要点: XGBoostがF1スコア0.82で最高性能（Random Forest: 0.79、Logistic Regression: 0.70を上回る）。SHAP分析により、投稿初期のエンゲージメント（最初の1時間のシェア・いいね数）が最も支配的な予測因子であり、次にコンテンツの感情が重要であることが判明。
   - ソース: [Social Media Popularity Prediction Based on Visual-Textual Features with XGBoost | ACM](https://dl.acm.org/doi/10.1145/3343031.3356072)

#### 2-2. 実用的な特徴量エンジニアリング

投稿テキストから抽出可能な特徴量の一覧:

| カテゴリ | 特徴量 | 抽出方法 |
|---------|--------|---------|
| **長さ** | 文字数、単語数、文数 | 基本カウント |
| **語彙** | ユニーク単語率（Type-Token Ratio）、語彙多様性 | 形態素解析 |
| **可読性** | Flesch Reading Ease、文の平均長 | textstat |
| **感情** | ポジティブ/ネガティブスコア、感情強度 | oseti, BERT |
| **トピック** | トピック分布（LDA）、キーワードTF-IDF | scikit-learn, gensim |
| **構文** | 品詞分布、疑問文率、命令文率 | GiNZA, spaCy |
| **意味** | 文埋め込みベクトル | Sentence-BERT |
| **時間** | 投稿曜日、時間帯 | メタデータ |

---

### 3. 文体分析（NLP）の実用的なアプローチ

#### 3-1. ソーシャルメディアの言語変化に関する研究知見

8. **SNSにおける言語簡略化パターン（PNAS, 2024）**
   - 要点: 約3億件の英語コメントを8プラットフォームで約30年間分析。テキスト長と語彙豊富さが一貫して減少する傾向を確認。しかし新語の導入率は安定しており、「簡潔だが新奇性のある表現」が好まれる。アルゴリズムが簡潔で感情的に共鳴する言語を優遇していることも示唆。
   - ソース: [Patterns of linguistic simplification on social media platforms over time | PNAS](https://www.pnas.org/doi/10.1073/pnas.2412105121)

9. **構文・意味役割ラベリングの優位性**
   - 要点: 構文構造と意味役割ラベリングを統合したモデルは、表面的特徴のみに依存するモデルを一貫して上回る。特に言語的変動性が高いドメイン（SNS投稿等）で効果が大きい。
   - ソース: [Recent advancements and challenges of NLP-based sentiment analysis | ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2949719124000074)

#### 3-2. テキスト分析パイプライン（Python実装）

**推奨パイプライン構成:**

```
テキスト収集 → 前処理 → 特徴量抽出 → 分析/モデリング → 解釈
```

**Step 1: 前処理**
```python
# GiNZA（spaCyベース）による日本語テキスト前処理
import spacy
nlp = spacy.load("ja_ginza")

doc = nlp("今日のランチめっちゃ美味しかった！おすすめ！")
for token in doc:
    print(token.text, token.pos_, token.lemma_)
```

**Step 2: 特徴量抽出**
```python
# TF-IDFによる特徴量抽出
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(max_features=5000, max_df=0.95, min_df=2)
tfidf_matrix = vectorizer.fit_transform(texts)
```

**Step 3: トピックモデリング**
```python
# LDAによるトピック抽出
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

count_vec = CountVectorizer(max_features=5000)
doc_term_matrix = count_vec.fit_transform(texts)

lda = LatentDirichletAllocation(n_components=10, random_state=42)
lda.fit(doc_term_matrix)
```

**Step 4: 予測モデル + SHAP解釈**
```python
import xgboost as xgb
import shap

# エンゲージメント予測モデル
model = xgb.XGBRegressor(n_estimators=100, max_depth=6)
model.fit(X_train, y_train)

# SHAP値による特徴量の寄与度可視化
explainer = shap.Explainer(model)
shap_values = explainer(X_test)
shap.summary_plot(shap_values, X_test)
```

**Step 5: 可読性分析**
```python
# textstatによる可読性スコア計算（英語テキスト用）
import textstat

score = textstat.flesch_reading_ease(text)
grade = textstat.flesch_kincaid_grade(text)
```

- ソース: [scikit-learn LDA Documentation](https://scikit-learn.org/stable/auto_examples/applications/plot_topics_extraction_with_nmf_lda.html)
- ソース: [textstat PyPI](https://pypi.org/project/textstat/)
- ソース: [XGBoost + SHAP | Kaggle](https://www.kaggle.com/code/bennyfung/model-interpretability-xgboost-shap)

---

### 4. 「受けのいい文章」のパターン抽出手法

#### 4-1. 日本語SNSの「バズる」テキストパターン

10. **LIPS laboの調査: SNS別「バズる言葉の法則」**
    - 要点: X（旧Twitter）では「ちょっと待って...これやばい...」のような友達に話すフランクな言い回し（親しみ感）と「速報」などオタク文化に通じる単語でバズりやすい。テキスト途中の「マジで〇〇になった！今すぐ買って！」のような強い言い切りがバズの要素。逆説構文、使用後の効果を含む構文、「絶対」「間違いない」など断定的な推薦フォーマットがパターンとして抽出されている。
    - ソース: [「バズる！言葉の法則」ユーザー調査 | LIPS labo（PR TIMES）](https://prtimes.jp/main/html/rd/p/000000128.000018721.html)

#### 4-2. パターン抽出に使える手法

| 手法 | 概要 | Pythonツール |
|------|------|-------------|
| **n-gram分析** | 高エンゲージメント投稿に頻出するフレーズを抽出 | scikit-learn CountVectorizer |
| **TF-IDF差分** | 高/低エンゲージメント群でTF-IDFの差が大きい語を特定 | scikit-learn TfidfVectorizer |
| **トピックモデリング** | LDA/NMFでトピック分布を抽出し、トピックとエンゲージメントの相関を分析 | scikit-learn, gensim |
| **Word2Vec + クラスタリング** | 単語埋め込みでテキストをベクトル化し、高エンゲージメント投稿のクラスタを特定 | gensim Word2Vec, K-means |
| **Sentence-BERT** | 文単位の類似度計算で「似た投稿」をグルーピング | sentence-transformers |
| **感情パターン分析** | 感情スコアの分布とエンゲージメントの相関 | oseti, BERT |
| **構文パターン** | 品詞パターン（例: 感嘆詞+名詞+動詞）の頻度分析 | GiNZA, spaCy |

#### 4-3. 実装例: 高エンゲージメント投稿の言語特徴抽出

```python
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# 高/低エンゲージメント群に分割
median_engagement = df['engagement_rate'].median()
high_eng = df[df['engagement_rate'] >= median_engagement]['text']
low_eng = df[df['engagement_rate'] < median_engagement]['text']

# TF-IDFで特徴語を抽出
vectorizer = TfidfVectorizer(max_features=1000)
high_tfidf = vectorizer.fit_transform(high_eng).mean(axis=0).A1
low_tfidf = vectorizer.transform(low_eng).mean(axis=0).A1

# 差分の大きい語 = 高エンゲージメント群に特徴的な語
feature_names = vectorizer.get_feature_names_out()
diff = high_tfidf - low_tfidf
top_indices = np.argsort(diff)[::-1][:20]

print("高エンゲージメント投稿の特徴語:")
for idx in top_indices:
    print(f"  {feature_names[idx]}: {diff[idx]:.4f}")
```

---

### 5. 日本語テキストの形態素解析・感情分析ライブラリ

#### 5-1. 形態素解析ライブラリ比較

11. **MeCab（+ mecab-python3 / fugashi）**
    - 要点: 京都大学とNTTが共同開発。C++実装で圧倒的な処理速度を誇り、大量テキスト処理に最適。辞書にIPAdic、UniDic、NEologd等を選択可能。Pythonラッパーとしてmecab-python3またはfugashi（Cython実装）が利用可能。
    - ソース: [Python形態素解析ライブラリ比較 | コードの泉](https://code-izumi.com/python/morphological-analysis/)

    ```python
    # fugashiによるMeCab利用
    import fugashi
    tagger = fugashi.Tagger()
    words = tagger("自然言語処理は面白い")
    for word in words:
        print(word, word.feature)
    ```

12. **GiNZA（spaCyベース）**
    - 要点: Megagon Labs開発。spaCyフレームワーク上で動作し、形態素解析に加え固有表現抽出・依存構造解析・係り受け解析にも対応。内部でSudachiPyを使用し、トークン化の精度は約96%。高度な分析が必要な場合に推奨。
    - ソース: [GiNZA - Japanese NLP Library](https://megagonlabs.github.io/ginza/)

    ```python
    # GiNZAによる解析
    import spacy
    nlp = spacy.load("ja_ginza")
    doc = nlp("東京タワーの近くで美味しいラーメンを食べた")

    # 形態素解析
    for token in doc:
        print(f"{token.text}\t{token.pos_}\t{token.lemma_}")

    # 固有表現抽出
    for ent in doc.ents:
        print(f"{ent.text}\t{ent.label_}")

    # 依存構造解析
    for token in doc:
        print(f"{token.text} --{token.dep_}--> {token.head.text}")
    ```

13. **Janome**
    - 要点: Pure Python実装のため、pipだけでインストール完結。C++コンパイラ不要で環境構築が最も簡単。速度はMeCab/GiNZAに劣るが、プロトタイプ開発や少量データの分析に最適。
    - ソース: [自然言語処理の形態素解析まとめ | Zenn](https://zenn.dev/megane_otoko/articles/008_morphological_analysis)

    ```python
    # Janomeによる解析
    from janome.tokenizer import Tokenizer
    t = Tokenizer()
    for token in t.tokenize("すもももももももものうち"):
        print(token)
    ```

14. **SudachiPy**
    - 要点: GiNZA内部で使われているトークナイザ。A（短単位）/ B（中単位）/ C（長単位）の3モードで分割粒度を制御可能。正規化辞書により表記揺れ（「食べれる」→「食べられる」等）を統一できる。
    - ソース: [Japanese NLP with SudachiPy, spaCy, and GiNZA | Qiita](https://qiita.com/acscharf/items/66017434ce1fc40deeb8)

#### 使い分けガイド

| 用途 | 推奨ライブラリ | 理由 |
|------|--------------|------|
| プロトタイプ・小規模データ | Janome | 環境構築が最も簡単 |
| 大量データの高速処理 | MeCab（fugashi） | 圧倒的な処理速度 |
| 高度な言語分析（NER・依存構造） | GiNZA | spaCyエコシステムの恩恵 |
| 表記揺れ統一が重要 | SudachiPy | 正規化辞書が強力 |

#### 5-2. 感情分析ライブラリ比較

15. **oseti（辞書ベース）**
    - 要点: 日本語評価極性辞書を用いた辞書ベースの感情分析。文ごとにポジティブ/ネガティブのスコアを返す。軽量で依存関係が少なく、ルールベースのため透明性が高い。
    - ソース: [oseti - GitHub](https://github.com/ikegami-yukino/oseti)

    ```python
    # osetiによる感情分析
    import oseti
    analyzer = oseti.Analyzer()

    # 文ごとの感情スコアを取得
    result = analyzer.analyze("今日のランチ最高だった！でもちょっと高かったかな")
    print(result)  # [1, -1] のようにスコアが返る

    # 詳細な感情分析
    detail = analyzer.analyze_detail("この映画は感動的で素晴らしい作品だ")
    print(detail)
    ```

16. **asari（機械学習ベース）**
    - 要点: 学習済みモデルによるポジティブ/ネガティブ分類。学習不要でそのまま利用可能。シンプルなAPIで使いやすい。
    - ソース: [asari - GitHub](https://github.com/Hironsan/asari)

    ```python
    # asariによる感情分析
    from asari.api import Sonar
    sonar = Sonar()
    result = sonar.ping(text="この商品はとても良い品質です")
    print(result)  # {'text': '...', 'top_class': 'positive', 'classes': [...]}
    ```

17. **pymlask（ML-Ask）**
    - 要点: 2,100語のパターン辞書により10種類の感情（喜・怒・哀・怖・恥・好・厭・昂・安・驚）を推定。感情分類が細粒度で、SNS分析において「どの感情がエンゲージメントを高めるか」の分析に有用。
    - ソース: [awesome-japanese-nlp-resources | GitHub](https://github.com/taishi-i/awesome-japanese-nlp-resources)

18. **BERT日本語感情分析モデル（Hugging Face）**
    - 要点: `daigo/bert-base-japanese-sentiment`がポジティブ/ネガティブの2値分類で高精度（テストデータで精度0.98）。`kit-nlp/bert-base-japanese-sentiment-irony`は皮肉検出にも対応。`christian-phu/bert-finetuned-japanese-sentiment`はAmazonレビュー20,000文で学習済み（3値分類: positive/neutral/negative）。
    - ソース: [daigo/bert-base-japanese-sentiment | Hugging Face](https://huggingface.co/daigo/bert-base-japanese-sentiment)

    ```python
    # Hugging Face Transformersによる日本語感情分析
    from transformers import pipeline

    # 事前学習済みモデルの読み込み
    classifier = pipeline(
        "sentiment-analysis",
        model="daigo/bert-base-japanese-sentiment",
        tokenizer="daigo/bert-base-japanese-sentiment"
    )

    result = classifier("今日の天気は最高で気分がいい！")
    print(result)  # [{'label': 'ポジティブ', 'score': 0.98...}]
    ```

#### 感情分析ライブラリの使い分け

| 用途 | 推奨ライブラリ | 理由 |
|------|--------------|------|
| 軽量・ルールベース分析 | oseti | 辞書ベースで透明性が高い |
| 手軽なポジネガ分類 | asari | APIが最もシンプル |
| 感情の細粒度分類 | pymlask | 10種類の感情を推定可能 |
| 高精度な感情分類 | BERT（Hugging Face） | Deep Learningで文脈を考慮 |
| 大規模データ・本番運用 | BERT + GPU | 精度と処理速度の両立 |

---

### 6. 本プロジェクトへの推奨アプローチ

SNSコンテンツ自動生成プロジェクトにおけるエンゲージメント分析の推奨パイプライン:

```
1. データ収集（X API）
   ↓
2. 前処理（GiNZA / MeCab で形態素解析）
   ↓
3. 特徴量抽出
   - テキスト特徴量: 文字数、単語数、語彙多様性、品詞分布
   - 感情特徴量: oseti（軽量）or BERT（高精度）
   - トピック特徴量: TF-IDF + LDA
   - 構文パターン: 疑問文率、命令文率、感嘆詞使用率
   ↓
4. 相関分析
   - 各特徴量とエンゲージメント率のピアソン/スピアマン相関
   - XGBoost + SHAP で非線形な寄与を可視化
   ↓
5. パターン抽出
   - 高/低エンゲージメント群のTF-IDF差分分析
   - n-gramによる頻出フレーズ抽出
   - 構文パターンのルール化
   ↓
6. コンテンツ生成への反映
   - 抽出したパターンをプロンプトテンプレートに組み込み
   - 生成後にエンゲージメント予測スコアで品質チェック
```

**必要なPythonパッケージ一覧:**

```
# 形態素解析・NLP
ginza           # spaCyベースの日本語NLP
ja-ginza        # GiNZAの日本語モデル
fugashi         # MeCab Pythonラッパー（高速処理用）
unidic-lite     # fugashi用辞書

# 感情分析
oseti           # 辞書ベース感情分析
transformers    # Hugging Face Transformers（BERTモデル用）
torch           # PyTorch（BERTのバックエンド）

# 特徴量抽出・モデリング
scikit-learn    # TF-IDF、LDA、機械学習全般
xgboost         # 勾配ブースティング
shap            # モデル解釈
gensim          # Word2Vec、トピックモデリング

# ユーティリティ
pandas          # データ操作
numpy           # 数値計算
matplotlib      # 可視化
textstat        # 可読性スコア（英語テキスト用）
```

---

## 情報の信頼性評価

- **一次ソース: 8件**
  - 学術論文（PNAS, Springer, SAGE Journals, arXiv, ACM）: 5件
  - 公式ライブラリドキュメント（GiNZA, scikit-learn, Hugging Face）: 3件
- **二次ソース: 10件**
  - 業界レポート・ブログ（Sprout Social, Social Insider等）: 5件
  - 技術ブログ・チュートリアル（Qiita, Zenn, コードの泉等）: 4件
  - PR・調査レポート（LIPS labo）: 1件

---

## ソース一覧

### 学術論文・研究

1. [Predicting Social Media Engagement from Emotional and Temporal Features | arXiv (2025)](https://arxiv.org/abs/2508.21650) - 学術論文（プレプリント）
2. [Using Linguistic Features to Predict Social Media Engagement | Springer (2024)](https://link.springer.com/chapter/10.1007/978-981-97-1552-7_27) - 学術論文（査読済み）
3. [Using text analytics to measure an effect of topics and sentiments on social-media engagement | SAGE Journals (2021)](https://journals.sagepub.com/doi/full/10.1177/18479790211016268) - 学術論文（査読済み）
4. [Patterns of linguistic simplification on social media platforms over time | PNAS (2024)](https://www.pnas.org/doi/10.1073/pnas.2412105121) - 学術論文（査読済み）
5. [Social Media Popularity Prediction Based on Visual-Textual Features with XGBoost | ACM](https://dl.acm.org/doi/10.1145/3343031.3356072) - 学術論文（査読済み）
6. [Recent advancements and challenges of NLP-based sentiment analysis | ScienceDirect (2024)](https://www.sciencedirect.com/science/article/pii/S2949719124000074) - 学術論文（査読済み）
7. [Enhancing Social Media Engagement Sentiment Prediction: A Random Forest and SMOTE-Based Approach | ResearchGate (2025)](https://www.researchgate.net/publication/390825678_Enhancing_Social_Media_Engagement_Sentiment_Prediction_A_Random_Forest_and_SMOTE-Based_Approach_with_Explainable_AI) - 学術論文
8. [Media analytics via machine learning: social media engagement prediction for TV channels | Springer (2025)](https://link.springer.com/article/10.1007/s13278-025-01568-y) - 学術論文（査読済み）

### 公式ドキュメント・ライブラリ

9. [GiNZA - Japanese NLP Library](https://megagonlabs.github.io/ginza/) - 公式ドキュメント
10. [scikit-learn: Topic extraction with NMF and LDA](https://scikit-learn.org/stable/auto_examples/applications/plot_topics_extraction_with_nmf_lda.html) - 公式ドキュメント
11. [daigo/bert-base-japanese-sentiment | Hugging Face](https://huggingface.co/daigo/bert-base-japanese-sentiment) - 公式モデルカード
12. [oseti - Dictionary based Sentiment Analysis for Japanese | GitHub](https://github.com/ikegami-yukino/oseti) - 公式リポジトリ
13. [asari - Japanese sentiment analyzer | GitHub](https://github.com/Hironsan/asari) - 公式リポジトリ
14. [textstat | PyPI](https://pypi.org/project/textstat/) - 公式パッケージ
15. [awesome-japanese-nlp-resources | GitHub](https://github.com/taishi-i/awesome-japanese-nlp-resources) - キュレーションリスト
16. [gensim Word2Vec Documentation](https://radimrehurek.com/gensim/models/word2vec.html) - 公式ドキュメント
17. [spaCy Japanese Models](https://spacy.io/models/ja) - 公式ドキュメント

### 業界レポート・ブログ

18. [The Social Media Metrics to Track in 2026 | Sprout Social](https://sproutsocial.com/insights/social-media-metrics/) - 業界レポート
19. [Social Media Benchmarks For 2026 | Social Insider](https://www.socialinsider.io/social-media-benchmarks) - 業界レポート
20. [SNSにおけるエンゲージメントとは？ | Cuenote](https://www.cuenote.jp/library/marketing/sns_engagement.html) - 解説記事
21. [「バズる！言葉の法則」ユーザー調査 | LIPS labo（PR TIMES）](https://prtimes.jp/main/html/rd/p/000000128.000018721.html) - 調査レポート

### 技術ブログ・チュートリアル

22. [Python形態素解析ライブラリ5選 | コードの泉](https://code-izumi.com/python/morphological-analysis/) - 技術ブログ
23. [自然言語処理の形態素解析まとめ | Zenn](https://zenn.dev/megane_otoko/articles/008_morphological_analysis) - 技術ブログ
24. [Japanese NLP with SudachiPy, spaCy, and GiNZA | Qiita](https://qiita.com/acscharf/items/66017434ce1fc40deeb8) - 技術ブログ
25. [日本語NLPライブラリGiNZAのすゝめ | Qiita](https://qiita.com/poyo46/items/7a4965455a8a2b2d2971) - 技術ブログ
26. [XGBoost + SHAP Model Interpretability | Kaggle](https://www.kaggle.com/code/bennyfung/model-interpretability-xgboost-shap) - チュートリアル
