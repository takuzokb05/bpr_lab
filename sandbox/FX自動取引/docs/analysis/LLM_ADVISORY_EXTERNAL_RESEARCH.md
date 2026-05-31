# LLM トレードフィルター／諮問機関アーキテクチャ 外部エビデンス調査

> **調査日**: 2026-05-31
> **手法**: deep-research harness（5角度 Web 検索 → 24ソース取得 → 114主張抽出 → 25主張を3票敵対的検証 → 19確認 / 6棄却 → 10 findings 統合）
> **動機**: SPEC v3 の「LLM 単体判定をノーチェックで発注」構成への懸念。LLM 判断を検証する"諮問機関"（debate / Bull-Bear / verifier / reflection）を入れるべきか、外部事例で検証する。
> **位置づけ**: 一次情報（学術論文）中心。"絶対儲かる"系を排除し、懐疑論・再現失敗も意図的に収集。各主張は3票の敵対的検証（2/3 反証で棄却）を通過したもののみ採用。

---

## エグゼクティブサマリー

諮問機関（マルチエージェント検証・debate・Bull/Bear 対立・verifier・reflection）アーキテクチャは学術界で複数の具体実装が存在する（TradingAgents, TradingGPT, FinMem, FinAgent, FinCon 等）が、その**「有効性」は独立検証でほぼ全滅している**。

- TradingAgents は Bull/Bear 研究員の討論＋リスク管理チーム＋トレーダー統合という、**まさに当方が検討中の構成をコード付き（LangGraph）で実装した先行事例**だが、論文の優位性主張は定性的または極小サンプル（AAPL 等3銘柄・約5か月）に留まる。
- 独立再評価では、知識カットオフ後データで **Sharpe 51-62%・総リターン 50-72% が崩壊する「Profit Mirage（利益の蜃気楼）」** が複数の一次論文で実証されている。
- 20年・63-91銘柄・バイアス制御の長期評価（FINSABER）では LLM エージェントは Buy-and-Hold に勝てず、**αの p値はすべて >0.34（統計的にゼロと区別不能）**。FinMem の +23.26% が**窓を2か月ずらすだけで -22.04% に符号反転**する過学習が文書化されている。
- confidence 校正は、verbalized confidence の ECE が 3B モデルで 0.49-0.57 と深刻に未校正であり、**当方が旧 AIAdvisor で観測した失敗（confidence 0.43-0.46 でラベル間分離なし・REJECT 0%）が学術的に裏付けられている**。

**結論**: 諮問機関は「リターンを改善する証拠」としてではなく**「設計参照」として価値があるに留まる**。当方の構成（価格のみ・単体判定・confidence 未校正）に対しては、まず **①バックテストのリーク制御（カットオフ後 hold-out 検証）と ②confidence の事後校正・discrimination 測定（AUC）を優先**すべきで、討論層の追加は複雑性に見合うリターン改善の独立エビデンスが乏しい点を直視した上で慎重に判断すべき。

---

## Findings（3票敵対的検証を通過した確認済み主張）

### 1. 諮問機関アーキは複数の学術フレームワークで実装済み（設計先例として有効）
- **TradingAgents**（arXiv:2412.20138, GitHub: TauricResearch/TradingAgents）: Bull/Bear 研究員の多ラウンド討論＋リスク管理チーム（risk-seeking / neutral / conservative の3視点）＋トレーダー統合＋ファンドマネージャー承認の完全パイプラインを **LangGraph でコード実装**。
- **TradingGPT**（arXiv:2309.03736）: inter-agent debate ＋個別化された trading traits を decision robustness の機構として明示。
- **multi-critic 拡張**（arXiv:2410.21741, ICAIF'24）: reflection/critic agent を「観点別に特化した複数の critic」へ拡張。
- 票: 3-0 / 3-0 / 2-1

### 2. ただし「有効性」は proposal レベルの定性主張か極小サンプルに留まる
- TradingAgents の優位性主張は abstract では定量値なし。本文でも **AAPL/GOOGL/AMZN 3銘柄・約5か月（2024年6-11月）のみ**（AAPL: CR 26.62% vs 2.05%、Sharpe **8.21** vs 2.31 ← 非現実的に高く、極小サンプルのチェリーピック疑い）。
- TradingGPT は **backtest 数値・収益図が一切なく**、著者自身が「prompt design 段階の proposal」と明記（Section 5 で ablation/backtest は PLANNED）。
- → P&L 改善の証拠としては使えず、**アーキテクチャ参照としてのみ有効**。
- 票: 3-0 / 3-0

### 3. 有効性エビデンスは独立検証で崩壊する
- **FINSABER**（arXiv:2505.07078, Oxford）: 20年（2004-2024）・63-91銘柄・サバイバーシップ/ルックアヘッド/データスヌーピング制御の長期評価。FinMem/FinAgent は Buy-and-Hold を上回れず、**B&H が常に上位**。両エージェントとも統計的に有意なαを生成せず、**p値はすべて >0.34**（B&H Sharpe 0.703 vs FinAgent 0.241、FinMem α -1.04%）。
- 票: 3-0

### 4. 根本原因は事前学習汚染／データリーク（Profit Mirage）
- **Profit Mirage**（arXiv:2510.07920）: 基盤モデルは過去の価格変動の事後説明を web 規模で取り込み「なぜ動くか」でなく「既に動いた事実」を記憶。FinMem/FinAgent/QuantAgent/FinCon/TradingAgents の5系全てで、過去期→直近期（市場リターンを揃えて drift 排除）へ移すと **Sharpe 51-62%減・総リターン 50-72%減**（FinMem が最悪 71.85%）。
- **Memorization Problem**（arXiv:2504.14765）: GPT-4o の S&P500 方向精度が pre-cutoff 69-82% → post-cutoff で MAPE 13-20% に膨張。
- **MemGuard-Alpha**（arXiv:2603.26797）: clean 信号 14.48bp/day vs tainted 2.13bp（7倍差）、汚染で in-sample 精度↑・OOS 精度↓。
- 票: 3-0 / 2-1

### 5. サーベイ群が既存研究の方法論的脆弱性を批判
- 多くがエージェント全体でなく素のモデルをテスト、狭い期間・限定銘柄（10銘柄未満）・1年未満・コード未公開。
- **164論文のレビューでルックアヘッドバイアスを認識するのは 26.8%、サバイバーシップに対処は 1.2% のみ**（arXiv:2602.14233）。
- 票: 3-0

### 6. 主要8システムが最低評価基準を満たさない
- 汚染制御・point-in-time 銘柄・rolling-window 報告・net-of-cost リターン・レジームカバレッジの5項目で、**FinMem 0/5、TradingAgents 1/5**、他も2/5以下（arXiv:2603.27539）。「No system satisfies all five」「cross-system comparisons are currently unreliable」。
- 票: 3-0

### 7. FinMem の報告値が窓のずれで符号反転（過学習の直接実証）
- FinMem の MSFT 報告 **+23.26% → -22.04% に符号反転**、Sharpe **1.440 → -1.247**（FINSABER 再評価、取引コスト込み・窓を2か月延ばしただけ、arXiv:2505.07078 Appendix D）。
- → 当方が懸念する backtest vs live 乖離・パラメータ恣意性を直接実証。
- 票: 2-1

### 8. LLM の自己申告 confidence は深刻に未校正（当方の観測を裏付け）
- verbalized confidence の ECE: Qwen2.5-3B **0.492**、Llama-3.2-3B **0.570**（0=完全校正、arXiv:2604.01457）。誤答に 93% confidence を割り当てる例も（arXiv:2502.11028）。
- → 当方の旧 AIAdvisor の「confidence 0.43-0.46 でラベル間分離なし・REJECT 0%」は**既知の limitation** として裏付け。
- ⚠️ **留保**: ECE 0.49-0.57 は **3B 小モデル固有**。70B+ 級は約 0.1 とされ、Claude Sonnet 級の verbalized confidence の実測校正値は本調査に**含まれない**。
- 票: 3-0 / 2-1（medium に降格）

### 9. 当方の「価格のみ・ニュース非投入」はリーク防御として学術的に正当
- ルックアヘッドバイアスは訓練期間と backtest 期間が重なると成績を水増しする（arXiv:2309.17322 Columbia、Economics Letters S0165176525004392）。
- ただしバイアスは均一でなく、**データ頻度・モデルサイズ・集計レベルで変動**（年次 S&P500 指数で recall 相関 100% vs 個別株日次で 0%）。小モデル・高頻度/細粒度データでは無視できる一方、低頻度・集計データで記憶が最大。
- → 価格のみ・news withhold は well-founded。ただし **USD_JPY 等の流動ペアの価格パスは記憶されうる**ため、細粒度（intraday）入力＋カットオフ後 OOS 検証を推奨。
- 票: 3-0 / 3-0

### 10. 記憶駆動リークには再現可能な診断プロキシが存在（当方に転用可能）
- LLM に**文脈なしで過去株式リターンを retrieve させ、recall 精度を記憶バイアスのベンチマークとする**手法（Economics Letters S0165176525004392）。
- → **当方活用**: Claude に対象ペアの過去価格/リターンを文脈なしで recall させ、的中率が高ければ「価格のみでも記憶リークあり」と判定する事前診断が組める。
- 票: 3-0

---

## 棄却された主張（透明性のため記録 — 6件）

3票検証で 2/3 以上が反証し、**採用しなかった**主張。両極端な断定はいずれも票が割れた点に注意：

| 棄却主張 | 票 | 意味 |
|---|---|---|
| リーク制御後 LLM は完全にゼロα（記憶の吐き戻しに過ぎない） | 1-2 | 完全否定もしきれない |
| LLM は "confidently wrong"（confidence が信頼性を全く分離しない） | 1-2 | 当方の失敗の一般化は確証されず |
| confidence は固定の内部回路バイアス（実際の不確実性を反映しない） | 1-2 | メカニズム断定は時期尚早 |
| **フレームワーク（多エージェント層）が LLM backbone より結果を支配** | **0-3** | **諮問機関が効くという主張は否決** |
| SimpleQA で ECE 0.63-0.81（GPT-4o も 0.45） | 1-2 | データセット依存 |
| **coordination 除去で Sharpe 15-30%低下（討論層に価値）** | **0-2** | **著者自身 "suggestive" と格下げ、討論層の価値は未確証** |

**最重要**: 「**討論層／諮問機関を足せばリターンが改善する**」という主張は、肯定側エビデンス（0-2, 0-3）が**いずれも否決**された。諮問機関の P&L 改善効果には独立エビデンスが無い。

---

## Caveats（調査の留保）

1. **対象資産の不一致**: 否定的エビデンスの大半は米国株（NASDAQ-100/S&P500/AAPL 等）。**当方の FX/forex を直接扱った独立検証はほぼ無い**。株式の否定的結果が FX にそのまま転移する保証はない（逆に楽観する根拠も無い）。
2. **検証範囲 ≠ 運用範囲**: 学術論文の多くは「LLM が単独でトレードして勝てるか」を検証。当方の「テクニカル戦略の出力を LLM がフィルターする（LLM は発注権を持たずゲートのみ）」構成とは設計が異なる。フィルター用途では記憶した価格パスを使う余地が単独トレードより小さい可能性があるが、これを検証した一次論文は発見できなかった。
3. **confidence 校正の規模依存性**: ECE 0.49-0.57 は 3B 小モデルの値。Claude Sonnet 級の verbalized confidence の校正度を直接測った一次値は本調査に含まれない。当方の 0.43-0.46 無分離は実測の一次データであり、外部文献はそれを「既知の limitation」として裏付けるに留まる。
4. **「討論層を足せば改善」には独立エビデンスが無い**（上記棄却参照）。
5. **時間依存性**: Profit Mirage 等のカットオフ依存の結果はモデル更新で数値が変動。引用論文は 2025-2026 年が多く、field は「より懐疑的」方向にトレンド中。

---

## Open Questions（未解決、Phase 2'B 判定で参照）

1. FX/forex を対象に、テクニカルシグナルの「フィルター」として LLM を使った構成（発注はテクニカル、ゲートのみ LLM）の有効性を、カットオフ後 hold-out で検証した独立研究は存在するか。
2. Claude Sonnet 級の大規模モデルにおける verbalized confidence の ECE/discrimination（AUC）は具体的にいくつか。temperature scaling/事後校正でどこまで discrimination が改善するか。
3. 諮問機関を「リターン改善」でなく「リスク/異常検知（CONFIRM率暴騰やレジーム転換時の自動抑制）」用途に限定した場合、複雑性に見合う効果を示した独立検証はあるか。
4. 「REJECT 0%・confidence 無分離」を是正する具体手法（ラベル分布の強制、confidence を相対ランクで使う、複数サンプルの一致度を疑似 confidence にする等）のうち、discrimination 改善が実証されたものはどれか。

---

## SPEC v3 への含意と実装方針（案）

### 朗報：SPEC v3 は既に方法論的に先んじている
SPEC v3 は **「2026 Hold-out PF 1.304（LLM 知識カットオフ後の純粋未見データ）」** を実施済み。これは本調査が**最重要と名指しする「カットオフ後 hold-out 検証」を先取り**しており、世の LLM trading 論文の大半（8システム中 hold-out をまともにやっているものはゼロ）より上にある。

### 不足：confidence の discrimination 測定が未実施
SPEC v3 は CONFIRM × confidence≥閾値で発注するが、**その confidence が実勝率を分離するか（discrimination, AUC）は未測定**。旧 AIAdvisor は 0.43-0.46 で分離ゼロだった。SPEC v3 の confidence が同じ運命かは、デモのデータで測るしかない。

### 実装方針（決定案）

**決定1：Phase 2'A で諮問機関（討論層）は実装しない。**
- 理由：リターン改善の独立エビデンスが無く（本調査で 0-2 / 0-3 棄却）、複雑性・LLM コストに見合わない。

**決定2：SPEC v3 はデモ起動する（hold-out 済みの強みを活かす）。ただしデモ期間を「confidence 校正＋リーク診断データ収集フェーズ」と明確に位置づける。**

**決定3：起動前後に以下の「データ取得」を準備する（戦略は変えない＝再 BT 不要）。**
- (a) **リーク診断スクリプト**（起動前に1回）: Claude に文脈なしで USD_JPY/GBP_JPY の過去価格/リターンを recall させ、的中率を測定。高ければ「価格のみでも記憶リークあり」→ hold-out PF 1.304 を割り引いて解釈。
- (b) **confidence 校正測定スクリプト**（デモ後に実行する枠）: `llm_judgments`（confidence）× `trade_closures`（勝敗/PnL）を judgment_id で突合し、confidence vs 実勝率の校正曲線・**AUC（discrimination）**・ECE を算出。
- (c) **計器拡張**: 日次サマリに CONFIRM率・confidence 分布・（可能なら）経済指標発表時刻のマーキングを出す。

**決定4：Phase 2'B 判定時に、デモで集めた AUC を見て次を決める。**
- AUC ≈ 0.5（旧 AIAdvisor 同様、信号にならない）→ confidence 閾値ロジックを見直す or 事後校正層を追加。
- リーク診断で記憶リークが強い → hold-out PF を割り引いて経済性 Gate を再評価。
- 諮問機関は、**異常検知用途**で必要性が出た場合に限り、Open Question 3 を再調査の上で別途検討。

---

## 出典一覧（24ソース、一次情報中心）

**諮問機関アーキテクチャ**
- TradingAgents: https://arxiv.org/abs/2412.20138 / https://github.com/TauricResearch/TradingAgents
- TradingGPT: https://arxiv.org/abs/2309.03736
- multi-critic 拡張 (ICAIF'24): https://arxiv.org/abs/2410.21741
- サーベイ (Debate-Driven 分類): https://arxiv.org/abs/2408.06361

**有効性の独立検証・懐疑論**
- FINSABER (Oxford, 20年評価): https://arxiv.org/html/2505.07078v5
- Profit Mirage: https://arxiv.org/html/2510.07920v1
- Memorization Problem: https://arxiv.org/abs/2504.14765
- MemGuard-Alpha: https://arxiv.org/abs/2603.26797
- 評価信頼性 (8システム判定): https://arxiv.org/abs/2603.27539
- バイアス調査 (164論文): https://arxiv.org/abs/2602.14233
- AMA benchmark: https://arxiv.org/abs/2510.11695

**ルックアヘッド/リーク**
- Look-Ahead Bias (Columbia): https://arxiv.org/abs/2309.17322
- Economics Letters (recall プロキシ): https://www.sciencedirect.com/science/article/pii/S0165176525004392

**confidence 校正**
- Wired for Overconfidence (ECE): https://arxiv.org/pdf/2604.01457
- Mind the Confidence Gap: https://arxiv.org/html/2502.11028v3
- verbalized confidence (元祖): https://arxiv.org/abs/2306.13063

**実践者（参考、blog/forum 品質）**
- "I lost 40% trusting an AI": https://medium.com/@kojott/i-lost-40-of-my-trading-account-by-trusting-an-ai-and-how-i-fixed-it-91b63d2f565a
- viral AI trading debunk: https://cybernews.com/ai-news/viral-ai-trading-debunk-model-lost-money-polymarket-kalshi/

> 注: synthesis 過程で一部 URL の取り違え（FinMem 符号反転の正典は 2505.07078、評価8システム判定は 2603.27539）があったが、本レポートでは検証済みの正しい対応に修正済み。
