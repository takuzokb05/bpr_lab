# P1 #7: 市場分析 JSON 更新頻度監査

実施日: 2026-05-03
対象: `data/market_analysis.json` の更新フロー + AI Advisor の判定分布

## 1. インフラ稼働確認

| 項目 | 状態 |
|---|---|
| `FX_MarketAnalysis` タスクスケジューラ | ✅ 稼働中 (Ready) |
| 最終実行 | 2026-05-03 06:30:01 (LastTaskResult=0 success) |
| 次回実行 | 2026-05-04 06:30:00 |
| Missed Runs | 0 |
| `market_analysis.json` 最終更新 | 2026-05-03 06:31:20 (生成完了 1 分以内) |
| ファイルサイズ | 5,965 bytes (3 ペア分) |
| `generated_at` トップレベル | **欠落** ← 軽微な改善点 |

→ **生成パイプラインは正常**。日次 06:30 に確実に走っている。

## 2. 今朝（2026-05-03）の生成内容

| ペア | direction | confidence | regime | reasoning |
|---|---|---:|---|---|
| EUR_USD | neutral | 0.49 | ranging | 「ADX=19.6でレンジ、RSI=51.2」 |
| USD_JPY | bearish | 0.84 | trending | 「ADX=37.0、日銀介入観測」 |
| GBP_JPY | bearish | 0.86 | trending | 「ADX=37.9、円買い圧力」 |

→ confidence は 0.49〜0.86 と健全な分布。NEUTRAL fallback は EUR_USD のみ（direction=neutral）。

## 3. P2-E で観測された 67.7% NEUTRAL の真因

P2-E (`docs/ai_advisor_effectiveness.md`) で AIフィルター判定の **67.7% (2102/3105) が NEUTRAL** と記録されていた件。

### 真因の特定

`src/ai_advisor.py::_classify()` の NEUTRAL 条件は以下:

```python
if self.confidence < 0.3:
    return "NEUTRAL", f"low_confidence({self.confidence:.2f})"
if self.regime == "unknown":
    return "NEUTRAL", "regime_unknown"
if self.direction == "neutral":
    return "NEUTRAL", "ai_direction_neutral"
```

つまり以下のいずれかで NEUTRAL になる:
1. **confidence < 0.3** （AI が自信なしと判定）
2. **regime == "unknown"** （市場分析ジョブが失敗 or データ不足）
3. **direction == "neutral"** （明確なバイアスなし）

### 各経路の発生条件

| 経路 | 想定発生条件 |
|---|---|
| confidence < 0.3 | LLM が「不明確」と判断、ニュース input が弱い、技術指標がフラット |
| regime == "unknown" | `compute_indicators()` 失敗 / バー数不足 / market_analysis.json 古い |
| direction == "neutral" | LLM が双方向のリスクファクター言及で中立判定（例: 今朝の EUR_USD） |

### 実態推定

今朝の生成では direction=neutral が 1/3 ペア (33%)。
約 **2 週間平均で 67.7%** ということは:
- 平日のうち、**market が trending な時間帯は半分以下**
- 米雇用統計前後・GW・連休等で direction=neutral が頻発した可能性
- レンジ相場中（ADX < 20）は LLM もフラットな判定を返しがち

→ **AIAdvisor のロジックではなく、市況自体がレンジ多めだった可能性が高い**。

## 4. 改善提案

### S1: トップレベル `generated_at` を追加（軽微）
- 現状: ペア別 `timestamp` のみ
- 改善: トップレベル `"generated_at"` で全体生成時刻を明示
- メリット: AIAdvisor 側の `MAX_ANALYSIS_AGE_HOURS=24` 判定が誤読しにくくなる
- 該当: `scripts/generate_market_analysis.py`

### S2: `MAX_ANALYSIS_AGE_HOURS=24` を 36 に緩和（軽微）
- 監査 B6 で既出
- 朝 06:30 生成 → 翌朝 06:30 で期限切れ。生成失敗 1 回で AI 完全停止
- 36h なら 1 日抜けても許容
- 該当: `src/ai_advisor.py:25`

### S3: NEUTRAL の理由別ロギング（中）
- 現状: NEUTRAL 全体の件数しか記録されていない
- 改善: low_confidence / regime_unknown / ai_direction_neutral の内訳を AI 倍率ログに含める
- メリット: 67.7% の内訳を後から分析可能
- 該当: `src/ai_advisor.py::_classify()` でログ出力 + `to_record()` に reason 追加

### S4: direction=neutral 時の AI 倍率を 1.0 → 戦略 conviction に委譲（要検証）
- 現状: NEUTRAL は倍率 1.0 で素通り、conviction だけが効く
- AI が「明確に方向感ない」と言っているなら、戦略エントリーを抑止する選択肢もあり
- ただし戦略が独自判断する余地を残すべき → S3 の集計データ取得後に判断

## 5. 結論

- **インフラ問題はない**。スケジューラ・JSON 生成は健全
- 67.7% NEUTRAL は **市況がレンジ寄りだった**+ **AIロジックの NEUTRAL 経路が複数ある**ことの合算
- 改善提案 S1〜S3 は軽微〜中の品質向上タスク。S4 は要検証
- **REJECT が 0/3105** の問題は別件（監査 A5 / `remaining_tasks.md` P2 #5）で対応

## 6. フォローアップ

- [ ] S1, S2 を 1 PR にまとめて適用 (低リスク、すぐ実装可)
- [ ] S3 適用後、1 ヶ月の NEUTRAL 内訳データを集計
- [ ] S4 は S3 の結果を見てから判断

PR #14 (ai_decision 永続化保護) で月曜以降の取引には ai_decision が記録されるため、S3 と組み合わせれば AI 効果の本格的 A/B 検証が可能になる。
