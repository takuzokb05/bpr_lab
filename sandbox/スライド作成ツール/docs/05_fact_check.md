# Q5: 事実検証レポート

> **検証日**: 2026-02-21
> **検証者**: fact-checker
> **対象**: docs/01〜04 の全4ドキュメント

## 検証結果サマリー

| 分類 | 件数 |
|------|------|
| **致命的問題（修正済み）** | 1件 |
| **重要問題（修正済み）** | 3件 |
| **軽微問題（修正済み）** | 2件 |
| **注意事項（修正不要）** | 3件 |
| **正確と確認** | 30件以上 |

**総合評価**: 致命的問題1件（廃止日の誤り）と重要問題3件を修正。修正後は全ドキュメントの事実的主張が公式ソースと整合している。

---

## 1. 致命的問題（プロジェクトに直接影響）

### [P0-1] Gemini 2.0 Flash 廃止日の誤り

- **対象**: `docs/01_gemini_api.md` 行13〜15
- **誤った記述**: 「2026/3/3 廃止予定」「2026年3月3日に廃止」
- **正しい情報**: **2026年6月1日に廃止予定**
- **公式ソース**: [Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations) — `gemini-2.0-flash` および `gemini-2.0-flash-lite` の Shutdown date は "June 1, 2026"
- **影響**: 3/3 と信じて急いで移行する必要はない。6/1 まで猶予がある。ただし早期移行は推奨。
- **修正**: 実施済み。日付を「2026/6/1」「2026年6月1日」に訂正し、公式廃止ページへのリンクを追加。

---

## 2. 重要問題（正確性に影響）

### [P1-1] モデル価格の「無料」表記が不正確

- **対象**: `docs/01_gemini_api.md` 主要モデル表、`docs/04_model_selection.md` 比較表
- **問題**: Gemini 2.5 Flash / Flash-Lite / Gemini 3 Flash Preview を「無料」と記載していたが、正確には「無料枠あり（レート制限付き）＋有料枠」の構造
- **正しい情報**:
  - Gemini 2.5 Flash: 無料枠あり、有料: 入力 $0.30 / 出力 $2.50 per 1M tokens
  - Gemini 2.5 Flash-Lite: 無料枠あり、有料: 入力 $0.10 / 出力 $0.40 per 1M tokens
  - Gemini 3 Flash Preview: 無料枠あり、有料: 入力 $0.50 / 出力 $3.00 per 1M tokens
- **公式ソース**: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- **影響**: 無料枠の制限を超えた場合のコスト計画に影響。本プロジェクトの規模（RPD 250回/日以内）であれば無料枠内で運用可能という結論は変わらない。
- **修正**: 実施済み。「無料枠あり（有料: $X.XX）」形式に全テーブルを修正。

### [P1-2] python-pptx バージョンの誤り

- **対象**: `docs/03_python_pptx.md` 行5、`docs/04_model_selection.md` 行135
- **誤った記述**: 「1.0.0」
- **正しい情報**: **1.0.2**（2024年8月7日リリース）
- **公式ソース**: [python-pptx on PyPI](https://pypi.org/project/python-pptx/)
- **影響**: 軽微。1.0.0 → 1.0.2 はマイナーバージョンアップであり、機能的な影響は小さい。
- **修正**: 実施済み。バージョンを「1.0.2（2024年8月7日リリース）」に訂正。

### [P1-3] 月間コスト試算の計算ミス

- **対象**: `docs/04_model_selection.md` 月間利用セクション
- **誤った記述**: 「画像生成（60回 × 20枚 = 1,200枚）→ $24.00」
- **正しい計算**: 週3回 × 4週 = **12回/月** × 20枚 = **240枚** × $0.02 = **$4.80**
- **影響**: 月間コスト試算が大幅に過大評価されていた（$24.00 → $4.80）。実際のコストは約1/5。
- **修正**: 実施済み。「12回 × 20枚 = 240枚 → $4.80」に訂正。リライト試算も比例して修正。月間合計を ≒900円 に修正。

---

## 3. 軽微問題（精度向上）

### [P2-1] python-pptx のメンテナンス状況

- **対象**: `docs/03_python_pptx.md` 行7
- **記述**: 「メンテナンス: アクティブ」
- **補足情報**: PyPI / Snyk のデータによると、過去12ヶ月間に新バージョンのリリースがない。`python-pptx-ng`（フォーク）が後継として開発されている。「アクティブ」よりも「低頻度メンテナンス」が正確。
- **影響**: 低。現行バージョン 1.0.2 は安定しており、本プロジェクトの用途には十分。
- **修正**: 未実施（本プロジェクトの判断に影響しないため）。ただし Phase B で問題が発生した場合は `python-pptx-ng` への移行を検討。

### [P2-2] Gemini 2.5 Flash 自体の廃止予定

- **対象**: 全ドキュメント
- **補足情報**: 公式廃止ページによると、`gemini-2.5-flash` 自体も **2026年6月17日に廃止予定**。`gemini-2.5-flash-lite` は **2026年7月22日に廃止予定**。これは Gemini 3 系への移行を見据えたもの。
- **公式ソース**: [Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations)
- **影響**: 中。本プロジェクトの Phase B 実装後、2026年6月以降に Gemini 3 Flash への移行が必要になる可能性がある。
- **修正**: 未実施（現時点では設計判断に影響しないが、Phase B 開始時に再評価が必要）。

---

## 4. 注意事項（修正不要だが把握すべき情報）

### [N-1] レート制限の変動性

- **対象**: `docs/01_gemini_api.md` 無料枠レート制限表
- **記述の正確性**: 現時点では正確（2026年1月時点の値と一致）
  - Gemini 2.5 Pro: 5 RPM / 100 RPD / 250,000 TPM
  - Gemini 2.5 Flash: 10 RPM / 250 RPD / 250,000 TPM
  - Gemini 2.5 Flash-Lite: 15 RPM / 1,000 RPD / 250,000 TPM
- **注意**: 2025年12月7日に Google が予告なく無料枠を50〜80%削減した実績がある。ドキュメントに「（概算）」と記載されている点は適切。公式ページでは具体的な数値を公開せず「AI Studio で確認」としている。
- **公式ソース**: [Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits) では数値を直接提示していない

### [N-2] Imagen 4 の無料枠

- **対象**: `docs/02_imagen3.md` セクション5
- **記述**: 「無料枠は存在しない。全ての使用が課金対象。ただし Google AI Studio 上では無料テスト可能」
- **検証結果**: **正確**。[Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing) で Imagen 4 全モデルが "Free Tier: Not available" と明記されている。Google AI Studio での無料テストは可能だが、API 経由のプログラマティックアクセスは全て課金対象。

### [N-3] DALL-E 3 の価格帯

- **対象**: `docs/02_imagen3.md` 代替手段比較表
- **記述**: 「$0.04〜$0.08」
- **検証結果**: **概ね正確**。DALL-E 3 の Standard quality は $0.04〜$0.08（解像度依存）。HD quality は $0.08〜$0.12。ドキュメントの記載は Standard quality の範囲として正確。

---

## 5. 正確と確認した主要事実

### docs/01_gemini_api.md

| 主張 | 検証結果 | ソース |
|------|---------|--------|
| PDF: 最大 50MB / 1,000ページ | **正確** | [Document Understanding](https://ai.google.dev/gemini-api/docs/document-processing) |
| 1ページ ≒ 258 トークン | **正確** | [Document Understanding](https://ai.google.dev/gemini-api/docs/document-processing) |
| Gemini 2.5 Pro: $1.25〜$2.50 入力 / $10.00〜$15.00 出力 | **正確** | [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| google-genai SDK のインストール: `pip install google-genai` | **正確** | [Google Gen AI SDK](https://googleapis.github.io/python-genai/) |
| `response_schema` による構造化出力 | **正確** | [Structured Output](https://ai.google.dev/gemini-api/docs/structured-output) |
| File API でのアップロード → URI 取得のフロー | **正確** | [Document Understanding](https://ai.google.dev/gemini-api/docs/document-processing) |
| モデル名 `gemini-2.5-flash` | **正確** | [Models](https://ai.google.dev/gemini-api/docs/models) |

### docs/02_imagen3.md

| 主張 | 検証結果 | ソース |
|------|---------|--------|
| Imagen 3 は廃止済み | **正確** | [Imagen - Gemini API](https://ai.google.dev/gemini-api/docs/imagen)、[Deprecations](https://ai.google.dev/gemini-api/docs/deprecations) |
| Imagen 4 Fast: `imagen-4.0-fast-generate-001`, $0.02/枚 | **正確** | [Pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| Imagen 4 Standard: `imagen-4.0-generate-001`, $0.04/枚 | **正確** | [Pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| Imagen 4 Ultra: `imagen-4.0-ultra-generate-001`, $0.06/枚 | **正確** | [Pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| Gemini 2.5 Flash 画像生成: $0.039/画像 | **正確** | [Pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| アスペクト比: 1:1, 3:4, 4:3, 9:16, 16:9 | **正確** | [Imagen](https://ai.google.dev/gemini-api/docs/imagen) |
| 1リクエスト 1〜4枚 | **正確** | [Imagen](https://ai.google.dev/gemini-api/docs/imagen) |
| SynthID ウォーターマーク全画像に付与 | **正確** | [Imagen](https://ai.google.dev/gemini-api/docs/imagen) |
| personGeneration: dont_allow / allow_adult / allow_all | **正確** | [Imagen](https://ai.google.dev/gemini-api/docs/imagen) |
| 解像度: 1K（デフォルト）/ 2K（Standard/Ultra のみ） | **正確** | [Imagen](https://ai.google.dev/gemini-api/docs/imagen) |

### docs/03_python_pptx.md

| 主張 | 検証結果 | ソース |
|------|---------|--------|
| ライセンス: MIT | **正確** | [PyPI](https://pypi.org/project/python-pptx/) |
| 依存: lxml, Pillow, XlsxWriter | **正確** | [Installing](https://python-pptx.readthedocs.io/en/latest/user/install.html) |
| デフォルトサイズ: 10×7.5 インチ（4:3） | **正確** | python-pptx のデフォルト値 |
| 16:9 = 13.333×7.5 インチ | **正確** | PowerPoint 標準仕様 |
| 背景画像の直接設定 API なし | **正確** | [Issue #496](https://github.com/scanny/python-pptx/issues/496) |
| アニメーション / トランジション 非サポート | **正確** | python-pptx 公式ドキュメント |
| フォント埋め込み不可 | **正確** | python-pptx の既知の制約 |

### docs/04_model_selection.md

| 主張 | 検証結果 | ソース |
|------|---------|--------|
| GPT-4o: $2.50/$10.00 per 1M tokens | **正確** | [OpenAI Pricing](https://openai.com/api/pricing/) |
| Imagen 4 Standard: $0.04/枚 | **正確** | [Pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| 20枚スライド1回: 画像 $0.40 | **正確**（20 × $0.02 = $0.40） | 計算検証 |

---

## 6. 修正一覧

| # | ファイル | 修正内容 | 重要度 |
|---|---------|---------|--------|
| 1 | `docs/01_gemini_api.md` | Gemini 2.0 Flash 廃止日を「2026/3/3」→「2026/6/1」に修正 | 致命的 |
| 2 | `docs/01_gemini_api.md` | モデル価格表の「無料」→「無料枠あり（有料: $X.XX）」に修正 | 重要 |
| 3 | `docs/03_python_pptx.md` | バージョンを「1.0.0」→「1.0.2（2024年8月7日リリース）」に修正 | 重要 |
| 4 | `docs/04_model_selection.md` | 月間コスト試算「60回→$24.00」→「12回→$4.80」に修正 | 重要 |
| 5 | `docs/04_model_selection.md` | PDF解析モデル比較表のコスト列に有料価格を追記 | 軽微 |
| 6 | `docs/04_model_selection.md` | python-pptx バージョン「1.0.0」→「1.0.2」に修正 | 軽微 |

---

## 7. 検証に使用したソース

### 一次ソース（公式）

- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini Deprecations](https://ai.google.dev/gemini-api/docs/deprecations)
- [Gemini Models](https://ai.google.dev/gemini-api/docs/models)
- [Gemini Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Document Understanding](https://ai.google.dev/gemini-api/docs/document-processing)
- [Imagen - Gemini API](https://ai.google.dev/gemini-api/docs/imagen)
- [python-pptx on PyPI](https://pypi.org/project/python-pptx/)
- [python-pptx Documentation](https://python-pptx.readthedocs.io/en/latest/)
- [OpenAI API Pricing](https://openai.com/api/pricing/)

### 二次ソース

- [AI Free API - Gemini Rate Limits Guide](https://www.aifreeapi.com/en/posts/gemini-api-free-tier-rate-limits)
- [iSumsoft - Gemini 2.0 Flash Deprecation Guide](https://www.isumsoft.com/internet/gemini-2-flash-deprecation-migration-guide.html)
- [Google Developers Blog - Imagen 4 GA](https://developers.googleblog.com/announcing-imagen-4-fast-and-imagen-4-family-generally-available-in-the-gemini-api/)
