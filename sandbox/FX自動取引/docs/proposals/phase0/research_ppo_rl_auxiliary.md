# プロポーザル: PPO Reinforcement Learning + Auxiliary Task

## 1. 戦略仮説

Proximal Policy Optimization (PPO) エージェントを **EUR/USD H1 環境** に投入し、Buy/Sell/Hold の3アクションを学習させる。**Auxiliary Task (補助課題)** として「次バー方向予測」を同時に学習させ、報酬関数を補強する。エージェント自身が試行錯誤しながらポリシーを更新するため、**人手介入なしで戦略が進化する** 構造を持つ。

## 2. 想定エッジ源 [G1-1]

- **エンドツーエンド最適化**: 教師あり学習が「予測精度」を最適化するのに対し、RL は **「累積報酬 (= PnL)」** を直接最適化する
- **PPO の安定性**: TRPO 等より学習が安定し、ハイパラ依存が小さい (OpenAI 2017)
- **Auxiliary Task の貢献**: 補助タスクが「世界モデル」を強化し、サンプル効率が向上 (arXiv 2024)
- **構造的優位**: 「報酬最大化」というシンプルな目的関数 + 自己探索が、人間の固定ルールを超える可能性
- **既知のリスク**: 「儲かるルール」と「無トレード」のニアミスを引き起こしやすい。コミッション込みだと Buy & Hold に収束する事例あり (arXiv 2411.01456)

## 3. シグナル定義 (擬似コード)

```python
# Environment 定義 (gym 互換)
class ForexEnv(gym.Env):
    observation_space = spaces.Box(shape=(50,))  # 直近50バーの正規化特徴量
    action_space = spaces.Discrete(3)  # 0=Hold, 1=Buy, 2=Sell

    def step(self, action):
        # 報酬 = 次バー PnL (スプレッド込み)
        reward = pnl_next_bar - spread_cost - holding_penalty
        # Auxiliary loss: 方向予測 (CE loss)
        aux_loss = cross_entropy(direction_pred, actual_direction)
        return obs, reward, done, {'aux_loss': aux_loss}

# PPO Agent (stable-baselines3)
from stable_baselines3 import PPO
model = PPO(
    "MlpPolicy", env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    gamma=0.99,
    clip_range=0.2,
)
model.learn(total_timesteps=1_000_000)

# 推論
action, _states = model.predict(current_obs)
if action == 1: enter_long(size=fixed_pct, sl=2*atr, tp=3*atr)
```

## 4. データ要件 [G1-2]

- **必要データ**: H1 OHLCV (過去5年) + 計算指標 50種程度
- **取得元**: MT5
- **計算リソース**: PPO 学習 1M steps = **8-12時間 (CPU)** または **1-2時間 (GPU)**。GPU 無い場合は CPU 学習で十分
- **計算ピーク**: ハイパラ探索時に Optuna で 20試行 × 8時間 = 160時間。**この計算コストが本戦略最大の弱点**
- **ラグ**: 推論は数百 ms (NN forward)

## 5. リスクモデル [G1-5]

| 項目 | 設定 |
|---|---|
| ポジションサイジング | 固定ロット (0.01 lot/口座10万円) — RL の不安定性に備え |
| 損切り (SL) | **環境内で実装** (報酬関数に組込) + **環境外でも MT5 SL 設定** (二重防衛) |
| 利確 (TP) | 環境内で TP 到達なら強制 close 報酬 |
| 取引停止条件 | 直近100トレード PF < 0.8 で停止 + 再学習 |
| 想定 MaxDD | **25-35%** (RL の探索性質上、教師あり学習より大きい) |

## 6. 自己改善メカニズム [G0-B] — 必須

### ドリフト検出
- **直近 PF が学習時 PF の 60% 以下** → ドリフト疑い
- **PolicyEntropy の上昇**: PPO のポリシーエントロピーが過去より高い → 確信度低下 → 再学習
- **報酬分布の KL ダイバージェンス**: 直近1ヶ月 vs 学習時の報酬分布が乖離

### 自動再最適化
- **継続学習 (Continual Learning)**: 月次で直近データを足して `model.learn(reset_num_timesteps=False)` で追加学習
- **完全再学習**: 四半期に1回、フルリセットして直近5年で学習し直す
- **Online Learning**: 取引中も探索率 (entropy_coef) を低めに維持して微調整

### フォールバック
- **新ポリシー OOS PF が直前ポリシー比 -30%** → ロールバック
- **連続再学習失敗** → Buy & Hold モードまたは取引停止
- **「フリーズモデル」**: 過去に PF 1.3 を達成したスナップショットを保存し、緊急時に切替

## 7. 過去 BT 結果 [G0-A] — 必須

### 既存研究の参照

| 論文/実装 | 結果 |
|---|---|
| **arXiv 2411.01456 (Auxiliary Task)** | PPO + Aux Task で EUR/USD return **2.12% → 42.22%, Sharpe -2.93 → 0.47** |
| **arXiv 2411.01456 (Dataset 1)** | return **-25.25% → 14.86%, Sharpe -2.61 → 0.24** |
| **arXiv 1908.08036 (Original DRL)** | DRL の forex 応用基礎研究 |
| **GitHub D3F4LT4ST/RL-trading** | PPO + DQN forex trading 公開実装 |

### PF > 0.95 を超える論拠
- Auxiliary Task 論文では **Sharpe 0.47 達成** → スプレッド込みで PF 1.1-1.3 想定
- ただし、論文は「commission を入れると Buy & Hold に収束する」と明示警告
- **コミッション込み実証は未だ** という重大な留意点あり

### 自前 BT 提案
- `gym-anytrading` または独自 `ForexEnv` で PPO 学習 (1M steps)
- 過去 5年 USD_JPY H1 で OOS テスト
- スプレッド 1.5pip 込み、PF と Sharpe を測定

## 8. WFA / OOS [G1-7]

- **Walk-Forward**: 18ヶ月学習 / 6ヶ月運用、5年で 6サイクル
- **PPO は WFO 適応性低い**: 学習に時間かかるため、月次再学習は非現実的。**四半期 WFO が現実的**
- **複数シード**: PPO は初期化シード依存が強い。**5シード平均** で報告
- **Deflated Sharpe**: ハイパラ探索 + シード試行を試行回数として補正

## 9. 実装複雑度 [G1-3]

- **工数見積もり**: 4-6週間
  - Week 1-2: gym 互換環境構築 + 報酬関数設計
  - Week 3: PPO + Auxiliary Task 統合
  - Week 4: WFO + ハイパラ最適化
  - Week 5-6: バックテスト + デバッグ
- **依存ライブラリ**: `stable-baselines3, gym/gymnasium, torch, optuna, mt5`
- **外部 API 依存**: MT5 のみ。GPU あれば学習高速化
- **既存資産活用**: 環境設計はゼロから

## 10. 機会費用比較 [G1-6]

| 対象 | 想定年率 | 100万円運用時 / 年 |
|---|---|---|
| 米国債 4% | 4.0% | 40,000 JPY |
| 全世界株 8% | 8.0% | 80,000 JPY |
| 銀行預金 | 0.05% | 500 JPY |
| **本戦略 (期待値)** | **15-40% (高分散)** | **150,000-400,000 JPY** |

論文では 42% リターン報告だが、**バラツキが大きい**。シード依存・期間依存が顕著。期待値の中央値は 10-15% 程度と慎重に見るべき。

## 11. リスク・既知の弱点

1. **コミッション込みで Buy & Hold に収束する罠**: arXiv 2411.01456 が明示警告。**最重要リスク**
2. **シード依存・初期化依存**: 同じハイパラでも結果が ±30% 変動
3. **学習時間 8-12時間**: 反復実験のテンポが落ちる
4. **オーバーフィッティング**: 観測空間が高次元なほど過剰適合しやすい
5. **方策崩壊 (Policy Collapse)**: 学習中盤で突然「全 Hold」に陥ることがある (PPO 既知の問題)
6. **説明可能性ゼロ**: NN の policy network はブラックボックス。SHAP も適用困難
7. **亡き者の世界との関係**: 未検証手法。亡き者は RL 不使用 → 「初の系統」だが、それだけリスク

## 12. 採点自己評価

### Gate 0 (必須)

| 項目 | 評価 | コメント |
|---|---|---|
| **G0-A**: PF > 0.95 | **△** | 論文では Sharpe 0.47 達成 (PF ~1.2)、ただしコミッション込みは Buy&Hold収束リスク |
| **G0-B**: 自己改善 | **○** | 継続学習 + ドリフト検出 + フリーズモデル切替を設計 |

→ **Gate 0 = 条件付き PASS** (コミッション込み BT 必須)

### Gate 1 (各10点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G1-1 想定エッジ源 | 6 | エンドツーエンド最適化は理論的に強いが、実装の悪魔が多い |
| G1-2 データ要件 | 7 | データは MT5 のみだが計算リソース要求が高い |
| G1-3 実装複雑度 | 4 | 4-6週間、PPO のデバッグが工数巨大化リスク |
| G1-4 ロバスト性 | 5 | シード依存大、ハイパラ感度高 |
| G1-5 リスクプロファイル | 6 | MaxDD 25-35% 想定、SL/TP は二重防衛 |
| G1-6 機会費用比較 | 6 | 期待値高いがバラツキ大 |
| G1-7 WFA / OOS | 5 | 学習コスト高でサイクル数少、シード平均必須 |

**Gate 1 = 39/70**

### Gate 2 (各5点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G2-1 スプレッド耐性 | 2 | **最大の脆弱性**。コミッション込みで Buy & Hold 収束報告あり |
| G2-2 他戦略との相関 | 5 | 教師あり学習・古典戦略と低相関、分散源として価値 |
| G2-3 説明可能性 | 1 | NN ブラックボックス、SHAP も困難 |
| G2-4 レビュー耐性 | 2 | 反論屋にとっては「再現性低い実験」と評される可能性大 |
| G2-5 拡張性 | 3 | ペア追加は容易だが学習時間倍増 |
| G2-6 過去挙動データ整合 | 3 | 全く新系統、整合性は確認できない |

**Gate 2 = 16/30**

### 総合

| Gate | 点数 | 合否 |
|---|---|---|
| Gate 0 | 条件付き PASS | コミッション込み BT で Buy&Hold回避を実証要 |
| Gate 1 | 39/70 | **進出基準 (50点) 未達** |
| Gate 2 | 16/30 | 加点小 |
| **総合** | **55/100** | **Phase 1 進出基準 (70点) 未達 — 棚上げ候補** |

### 結論
PPO RL は **理論的魅力 ≫ 実用性** の典型。学習コスト・シード依存・コミッション罠の三重苦で、個人投資家の 100-500万円スケールには **オーバーキル**。**研究的価値は高いが、Phase 1 進出は推奨しない**。XGBoost / HMM 系の検証が先。

---

## ソース

1. [Improving Deep Reinforcement Learning Agent Trading Performance in Forex using Auxiliary Task](https://arxiv.org/abs/2411.01456) - arXiv (2024) — Aux Task で Sharpe -2.93 → 0.47
2. [Deep Reinforcement Learning for Foreign Exchange Trading](https://arxiv.org/pdf/1908.08036) - 元祖 DRL forex 研究
3. [GitHub - D3F4LT4ST/RL-trading](https://github.com/D3F4LT4ST/RL-trading) - PPO + DQN forex 公開実装
4. [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3) - PPO 実装ライブラリ
5. [FinRL Contests 2024-2025](https://open-finance-lab.github.io/FinRL_Contest_2025/) - RL trading コンペ、ベンチマーク参照
