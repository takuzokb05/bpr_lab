# P2-E: AIAdvisor 通過/拒否率と取引結果集計

生成日時: 2026-05-03T19:53:53.374525
対象ログ: ['trading_prod_snapshot.log.1', 'trading_prod_snapshot.log']

## 1. 全体集計

AIフィルター 評価総数: **3105**

| 判定 | 件数 | 比率 |
|---|---:|---:|
| CONFIRM | 392 | 12.6% |
| NEUTRAL | 2102 | 67.7% |
| CONTRADICT | 611 | 19.7% |
| REJECT | 0 | 0.0% |

## 2. ペア別

| pair | CONFIRM | NEUTRAL | CONTRADICT | REJECT | 計 |
|---|---:|---:|---:|---:|---:|
| AUD_USD | 10 | 0 | 11 | 0 | 21 |
| EUR_JPY | 0 | 0 | 2 | 0 | 2 |
| EUR_USD | 122 | 1964 | 348 | 0 | 2434 |
| GBP_JPY | 238 | 0 | 196 | 0 | 434 |
| USD_JPY | 22 | 138 | 54 | 0 | 214 |

## 3. AI direction 別 内訳

AIが bullish/bearish/neutral と評価した内訳。
| 判定 | bullish | bearish | neutral |
|---|---:|---:|---:|
| CONFIRM | 119 | 273 | 0 |
| NEUTRAL | 0 | 0 | 2102 |
| CONTRADICT | 215 | 396 | 0 |
| REJECT | 0 | 0 | 0 |

## 4. confidence 分布

| 判定 | n | 平均 conf | 中央値 |
|---|---:|---:|---:|
| CONFIRM | 392 | 0.46 | 0.43 |
| NEUTRAL | 2102 | 0.42 | 0.39 |
| CONTRADICT | 611 | 0.45 | 0.46 |
| REJECT | 0 | - | - |

## 5. 実取引 PL × AI判定（DB集計）

| instrument | ai_decision | n | wins | WR | avg PL | sum PL |
|---|---|---:|---:|---:|---:|---:|
| AUD_USD | (なし) | 2 | 0 | 0.0% | -482.5 | -965.0 |
| EUR_JPY | (なし) | 2 | 0 | 0.0% | -192.5 | -385.0 |
| EUR_USD | (なし) | 13 | 5 | 38.5% | 255.0 | 3315.0 |
| GBP_JPY | (なし) | 37 | 13 | 35.1% | -33.5 | -1239.0 |
| GBP_USD | (なし) | 3 | 0 | 0.0% | -329.0 | -987.0 |
| USD_JPY | (なし) | 7 | 1 | 14.3% | -131.3 | -919.0 |


## 6. 解釈

- REJECT 比率 0.0%、CONTRADICT 比率 19.7%、CONFIRM 比率 12.6%
- REJECT がほぼ無いため、AI は事実上見送り判定をしていない

詳細な「AI 有/無 のA/B 比較」は実取引 PL を AIfilter 倍率と紐づけて分析する必要があり、
市場分析 JSON （`data/market_analysis.json`）の更新頻度依存。本レポートでは集計のみ。