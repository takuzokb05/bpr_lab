# LOOSE_MODE脱却ロードマップ

2026-04-21: デモ口座で初の自動取引成功。
LOOSE_MODE設定（約定確認用の緩和）を本来の「安全に効率よく取引」する構成に戻すための段階ロードマップ。

## 現在位置

- ✅ Phase 1-3 実装完了（368テスト）
- ✅ VPS 24時間稼働（ConoHa Windows）
- ✅ **初自動取引成功**（2026-04-21 19:06 JST）
- ⚠️ LOOSE_MODE（約定確認用の緩和設定）稼働中
- ⚠️ 12ポジ全含み損（戦略品質の課題を顕在化）

## 3段階の復帰プラン

### Stage 1: 戦略品質テスト（1-2日）
**目的**: 現LOOSE設定でトレードサイクル（エントリー→SL/TP→再エントリー）を最低30件観測

- [ ] SL/TP ヒット率を収集（目標: 30件以上）
- [ ] ペア別勝率を集計
- [ ] トレード事後分析 (trade_postmortem) をAPIで有効化
- [ ] DB同期バグ確認（status=openのまま残っている）
- [ ] SignalCoordinatorタイムアウト率を確認

判定基準: **勝率 >= 40%** かつ **期待値 > 0** ならStage 2へ。
それ以下なら戦略見直し（MAクロス厳密版 + 他指標合流へ巻き戻し）。

### Stage 2: 閾値の段階復帰（3-7日）
**目的**: LOOSE_MODE設定を1項目ずつ本来の安全値へ戻す

優先順（影響小→大で戻す）:

1. **MAクロス条件**: MA位置ベース → 直近5バー以内クロス → 1バー厳密クロス
2. **MIN_CONVICTION_SCORE**: 1 → 3 → 4（本来値）
3. **ADX_THRESHOLD**: 0 → 10 → 15（本来値）
4. **MFI_ENABLED**: False → True（本来値）
5. **BEAR_RESEARCHER_ENABLED**: False → True（本来値）
6. **AI_ADVISOR_ENABLED**: False → True（本来値）
7. **MAX_RISK_PER_TRADE**: 0.001 → 0.005 → 0.01（本来値）
8. **MAX_DAILY_LOSS**: 0.20 → 0.05 → 0.02（本来値）
9. **MAX_CONSECUTIVE_LOSSES**: 30 → 10 → 5（本来値）
10. **MAX_OPEN_POSITIONS**: 12 → 8 → 6（本来値）
11. **MAX_CORRELATION_EXPOSURE**: 6 → 3 → 2（本来値）

各ステップで24〜48h観察し、勝率・drawdownが悪化していないことを確認してから次へ。

### Stage 3: 本格デモ運用（3か月）
**目的**: claude.md の「最低3か月デモ検証」を履行

- [ ] market_analysis.json daily運用の確認（6:30 AM JST自動生成）
- [ ] Slack/Telegram 通知の運用確認
- [ ] 日次サマリ自動生成 (daily_summary.py)
- [ ] 週次レポート運用
- [ ] 実運用で遭遇したエラーを memory に蓄積（既に volume_step / filling_mode / No money など5件蓄積済み）

判定基準: 3か月通算で **月次期待値 > 0** かつ **月次 drawdown < 5%** ならリアル口座移行検討。

## 今の観察期間（2026-04-21）でやること

1. 1時間観察で SL/TP ヒットが発生するか確認
2. ヒットしないなら、ATR_MULTIPLIER/MIN_RISK_REWARDを見直し（SL/TP幅が現状のM15ボラに対し適切か）
3. DB同期バグ（closed にならない）の原因調査
4. 勝敗統計スクリプト (scripts/trade_stats.py) の定期実行
5. 事後分析 L1 の有効化（POSTMORTEM_ENABLED=True は既に入っている、ANTHROPIC_API_KEY確認）

## 既知の改善候補（後続タスク）

- [ ] SignalCoordinator の5秒タイムアウトが頻発（LLM応答遅延）→ タイムアウト延長 or ローカル判定フォールバック強化
- [ ] 過去のレガシーポジション（sync_with_broker 未取り込み）問題 → sync 処理で自動クローズ or DB取り込み
- [ ] M15の強いトレンド中は同方向シグナル連打 → エントリー間隔のクールダウン（同ペア同方向は Nバーごとに1回まで）
- [ ] 日本時間深夜〜早朝（東京クローズ〜NY早朝）のボラ低下期は取引停止（時間帯フィルター）
- [ ] 経済指標前のエントリー停止（フォレックスカレンダーAPI連携）
