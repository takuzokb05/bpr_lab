# 現行スキームの欠点整理と外部ツール比較 (2026-06-11)

> 2026-06-09 インシデント (SL未設定の裸ポジション → 撤退条件誤発火 → 停止2日間未検知)
> を契機に、SPEC v3 Phase 2'A スキームの欠点を FreqTrade / Jesse / OctoBot /
> Hummingbot / MQL5 定石と比較して整理した。修正済み項目は PR コミット 60b74e5 参照。

## 1. 欠点と対応状況

| # | 欠点 | 重大度 | 外部ツールの解法 | 対応 |
|---|---|---|---|---|
| 1 | **SLTP後付けの無言失敗** — order_send が成功扱いでも SL/TP がポジションに反映されないケースが実在 (ticket 10188884)。warning すら出ず、裸ポジションが 24h 放置 | 🔴 致命 | MQL5定石: SL/TP は発注リクエストに同梱 (atomic)。FreqTrade: SL設置失敗時は emergency_exit で即成行クローズ | ✅ 修正済 (atomic優先+検証付きフォールバック+フェイルセーフ) |
| 2 | **ポジション保護の単層防御** — ブローカー側 SL のみに依存し、ループ側の検証なし | 🔴 致命 | FreqTrade: stoploss_on_exchange_interval (60秒毎に SL 注文の存在を検証、消えていたら再作成) | ✅ 修正済 (毎ループ裸ポジ検知+再設定+synthetic_sl) |
| 3 | **撤退条件の最小サンプル不足** — PF<1.0 判定が n=5 で発火。異常値 1 件で PF 1.25→0.739 | 🟠 高 | FreqTrade MaxDrawdown protection: trade_limit=20 未満では DD 判定しない | ✅ 修正済 (RETREAT_PF_MIN_TRADES=20) |
| 4 | **死活監視のオオカミ少年化** — 生存判定が「直近10分の LLM 判定」基準。判定はシグナル時のみ (平均17分に1件) なので稼働中でも WARN 頻発 → 本物の停止が埋もれた | 🟠 高 | FreqTrade: heartbeat 60秒 + systemd WatchdogSec。healthchecks.io 型 dead man's switch (ping 途絶で外部から通知) | ✅ 修正済 (ハートビート基準+STOPPED明示通知)。dead man's switch は未着手 (下記) |
| 5 | **LLM confidence の張り付き** — CONFIRM/REJECT が全件 0.72。閾値 0.65/0.60 が実質無効化、Phase 2'B の AUC≥0.55 gate が測定不能になる | 🟠 高 | 研究コンセンサス: 生の言語化 confidence は ECE 0.2-0.38 で非推奨。離散ビン化 / 事後較正 (isotonic) / FreqAI は「入力が分布内か」(DI) で代替 | ✅ 一部修正 (離散9ビン+4観点ルーブリック)。事後較正はデータ蓄積後 |
| 6 | **撤退=恒久停止のみ** — FreqTrade 型の「クールダウン→自動再開」がなく、発火後は人間の再起動が必要 | 🟡 中 | FreqTrade protections: stop_duration_candles 経過後に自動再開、劣化ペアだけ停止 | ⬜ 未対応 (検討価値あり) |
| 7 | **照合 (reconciliation) が片方向** — MT5→DB の同期はあるが、「DB に SL/TP があるのに MT5 に無い」の逆方向検出は #2 で追加した分のみ。状態機械 (open→pending_close→closed) は未導入 | 🟡 中 | 実務定石: 定期 reconciliation ジョブ + 明示的状態遷移 | 🔶 部分対応 |
| 8 | **time_limit 決済の exit_price が近似値** — `_record_closure_from_history` が現在価格で近似 (実約定価格でない) | 🟡 中 | — (自前問題) | ⬜ 未対応 (デモの計測精度問題) |
| 9 | **ニュース時間帯回避なし** — 雇用統計等の高ボラ時間帯もシグナルが通る | 🟢 低 | MQL5: 経済カレンダー API で指標前後の新規停止 | ⬜ 未対応 (スプレッド異常キルスイッチが部分代替) |

## 2. 取り入れたもの (外部ツール → 本システム)

1. **atomic SL/TP 同梱発注** (MQL5 定石) — `market_order` が SL/TP 同梱を第一試行
2. **emergency_exit 型フェイルセーフ** (FreqTrade) — SL/TP 反映を検証できなければポジションを保持しない
3. **stoploss_on_exchange_interval 型の毎ループ SL 存在検証** (FreqTrade) — 裸ポジ検知 → 再設定 → synthetic_sl
4. **trade_limit=20 の最小サンプルガード** (FreqTrade MaxDrawdown) — PF 撤退判定
5. **heartbeat 基準の死活監視** (FreqTrade heartbeat) — シグナル依存の判定鮮度から脱却
6. **confidence の離散ビン化** (LLM較正研究) — 0.72 アトラクタの除去

## 3. 未着手の推奨 (優先順)

1. **healthchecks.io 型 dead man's switch** — ループ末尾に HTTP ping 1 行。VPS 丸ごと死んでも外部から通知が来る唯一の手段。無料アカウントで可 (ユーザーのアカウント作成が必要)
2. **FreqTrade 型クールダウン撤退** — 「PF<1.0 → 7日停止 → 自動再開 (3回目で恒久停止)」のような段階制。撤退発火のたびに人間が状況判断する現行運用の省力化
3. **confidence の事後較正** — デモで (confidence, 勝敗) が 30 件以上溜まったら isotonic 回帰で較正し、較正後の値で閾値を再設定
4. **time_limit 決済の実約定価格化** — `history_deals_get` から実価格を引く

## 4. インシデントの教訓 (恒久)

- **「retcode=DONE」は「反映された」を意味しない** — MT5 の TRADE_ACTION_SLTP は要検証。状態を変える API は変更後の実状態を読み戻して確認する
- **死活監視は「活動の発生」でなく「ハートビート」で測る** — 活動 (シグナル/取引) はゼロが正常の時間帯がある
- **撤退ゲートの判定データ自体が壊れている可能性** — ゲート発火時は「発火させたデータは正しいか」を先に検証する (今回: 発火原因の 1 取引がバグ起因で、除外すれば PF 1.25)
