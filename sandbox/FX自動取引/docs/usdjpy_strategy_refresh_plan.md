# USD/JPY 戦略リフレッシュ設計 (P2 #4)

実施日: 2026-05-03
背景: H1 730日検証 (`docs/strategy_validation_h1.md`) で USD/JPY の RsiPullback が**全グリッドで負エッジ**と判明。M15 60日では PF 1.97 だったが、H1 で PF 0.91 / SR -0.29 / OOS PF 0.42。
M15 で測れる範囲では 35/65 が現状ベストだが、**戦略自体の構造的問題**として近い将来の入替えが必要。

## 1. 候補オプション

### A: BollingerReversal を USD/JPY にも適用
- **根拠**: GBP/JPY で稼働実績あり（PF 1.08, WR 41.7%）。Phase 1 ベンチで他公開戦略を上回る
- **懸念**: USD/JPY での未検証。GBP/JPY の高ボラ環境とは異なる
- **検証コスト**: 低（既存の variants_bt.py に BollingerReversalBT あり）

### B: RsiMaCrossover (ma_crossover.py) を USD/JPY に
- **根拠**: 既存実装、ADX フィルター付き
- **懸念**: 監査 B5 で「INSTRUMENT_STRATEGY_MAP に含まれずデッドコード化」と指摘済み。実戦投入経験なし
- **検証コスト**: 低（既存 RsiMaCrossoverBT あり）

### C: 真の MTF (D1 トレンド × M15 エントリー)
- **根拠**: rsi_pullback.py docstring に「将来拡張」と明記。監査 B4 で「命名と実装の乖離」指摘済み
- **メリット**: 上位足のトレンド確認で USD/JPY の H4/D1 中期トレンドを反映できる
- **懸念**: 実装コスト中（broker_client から H4/D1 並列取得、戦略本体改修）
- **検証コスト**: 中

### D: タイムフレームを M15 → H1 に変更
- **根拠**: H1 でも 35/65 は負エッジだが、グリッド全体で M15 より変動が小さい
- **懸念**: シグナル頻度が大幅低下（取引数 ~10/月）→ 統計的検出力低下
- **検証コスト**: 低（pair_config.yaml の granularity 変更のみ、ただし trading_loop は instrument 単位で統一 granularity 想定 → 戦略マップに pair 別 TF も追加必要）

### E: USD/JPY を `INSTRUMENT_STRATEGY_MAP` から外す（撤退）
- **根拠**: H1 で構造的問題確認済み。継続損失リスク回避
- **懸念**: ペーパートレードの統計データが減る
- **コスト**: 最小（main.py 1 行）

## 2. 推奨判断フロー

**Step 1**: PR #17 (MT5 export + Phase 3 検証) 完了後、M15 5y で再検証
- 結果が H1 730d と一致 → 構造的問題確定 → C/E のいずれか
- 結果が M15 60d と一致 → タイムフレーム/データ依存性 → 観察継続でも可

**Step 2**: Step 1 の結果を踏まえ、A/B/C/D を 1 ヶ月のペーパー A/B 比較
- 候補戦略を `_bench_` 接頭辞で実装し、本番と並走させる（実発注はせずシグナルのみログ）
- 1 ヶ月の合計 PF / WR / 最大 DD で比較

**Step 3**: 最強候補に切替 or E（撤退）

## 3. 即時実行可能なアクション

### A1: BollingerReversal を USD/JPY 用にバックテスト確認
```python
# scripts/_check_bollinger_for_usdjpy.py を新規作成
# 既存 variants_bt.py::BollingerReversalBT を yfinance H1 730d / M15 60d で実行
# 結果: PF / SR CI / OOS PF を Phase 1/2 と比較
```

### B1: RsiMaCrossover を USD/JPY 用にバックテスト確認
```python
# 同上、RsiMaCrossoverBT を流用
```

これらは本番影響なし、半日で実装+ラン可能。

### C1: 真の MTF 設計 (要 Plan agent)
- broker_client.get_prices(instrument, 100, "H1") を MTF 用に追加取得
- mtf_pullback.py を改修し、H1 の SMA(50) または D1 の close を確認してからエントリー
- 本番ロジック改修なので別 PR（コード追加分のみ、既存ロジックは温存）

## 4. リスク・前提

- **MT5 5y 検証 (PR #17 関連) 完了が前提**。それ以前に戦略変更すると、新戦略が「単に違うレジーム偶然」を捕まえているだけかもしれない
- **新戦略でも実戦勝率は当面低い可能性**。1 ヶ月のペーパー観察期間を必ず取る
- **USD/JPY は介入リスクが大きい通貨**。LLM の market_analysis でも「日銀介入観測」が頻出。戦略変更だけでなく**ニュースイベントフィルター**の追加も検討要

## 5. 本ドキュメントの位置付け

これは**設計方針案**であり、コード変更を含まない。次の打ち手:

1. PR #17 マージ後、VPS で MT5 5y export 実行
2. ローカルで Phase 3 (M15 5y) 検証実行
3. 結果次第で本ドキュメントの A/B/C/D/E から具体策を選定
4. 選定された施策を別 PR で実装

`remaining_tasks.md` P2 #4 の継続タスクとして、Phase 3 結果待ち。
