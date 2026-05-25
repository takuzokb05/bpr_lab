# プロポーザル評価プロセス

> `docs/PROPOSAL_TEMPLATE.md` (採点**項目**) の対になる、採点**プロセス**を定義する文書。SPEC v2 撤退 (2026-05-26) の教訓を制度化し、SPEC v3 以降も再利用可能なワークフローとして残す。

---

## 設計原則 (撤退教訓から制度化)

| 原則 | 由来 | 制度化方法 |
|---|---|---|
| **手法 → フレーム の順** | フレーム延命バイアス (Claude) | Phase 0 で手法選定、フレーム整備は採用後 |
| **観点漏れ防止のため評価する側を先に固める** | effort heuristic 罠 | 6評価委員を Phase 0 候補が出揃う前に定義 |
| **同じデータの別角度ではなく、別データの別観点** | Agent A/C 疑似独立 | 3エージェント (memory/research/internal) で別ソース起草 |
| **重複統合は集計フェーズ、査読は全件** | M 違反候補も視点別に異なる評価あり得る | MECE 監査結果は集計時に参照、査読は全件並列 |
| **placeholder 禁止、撤退条件事前明文化** | SPEC v2 三重定義 + 90日放置 | PROPOSAL_TEMPLATE.md Gate 0 + 採用却下基準 |
| **亡き者の挙動データを反証材料として継承** | 撤退済 GBP_JPY 再採用矛盾 | 全エージェント・全委員に必読指示 |

---

## ワークフロー全体図

```
        ┌────────────────────────────────────────────┐
        │  Phase 0: 候補ロングリスト構築              │
        │  ├─ phase0-memory (実践者知見抽出)        │
        │  ├─ phase0-research (Web 文献調査)        │
        │  ├─ phase0-internal (既存資産活用)        │
        │  └─ 補強起草 (MECE 監査で欠落発見時)       │
        │  出力: docs/proposals/phase0/<source>_*.md  │
        └────────────────────────────────────────────┘
                          ↓
        ┌────────────────────────────────────────────┐
        │  MECE 監査 (ultrathink-debugger)            │
        │  ├─ M 違反 (重複) 検出 + 統合提案          │
        │  ├─ C 違反 (欠落) 検出 + 補強提案          │
        │  ├─ 粒度の不揃い検出 (ポートフォリオ層等)   │
        │  └─ 採点フレームへのフィードバック         │
        │  出力: docs/proposals/phase0/MECE_AUDIT.md  │
        └────────────────────────────────────────────┘
                          ↓
        ┌────────────────────────────────────────────┐
        │  Phase 1: 6評価委員並列査読                │
        │  各委員 (.claude/agents/proposal-reviewer-*.md):│
        │  ├─ economics    PF/シャープ/機会費用     │
        │  ├─ structure    G0-B 具体性/三重定義回避  │
        │  ├─ history      亡き者DB/既存Gate継承    │
        │  ├─ implementation データ/複雑度/6ヶ月内   │
        │  ├─ risk         MaxDD/Black Swan         │
        │  └─ meta         Goodhart/effort heuristic │
        │  出力: docs/proposals/reviews/REVIEW_*.md   │
        └────────────────────────────────────────────┘
                          ↓
        ┌────────────────────────────────────────────┐
        │  集計フェーズ                              │
        │  ├─ 6視点合算スコア + 中央値               │
        │  ├─ 全委員 PASS 候補抽出                  │
        │  ├─ 委員間意見対立検出 (分散大)           │
        │  ├─ MECE 統合提案を反映                   │
        │  └─ Phase 2 進出 6-10 候補確定           │
        │  出力: docs/proposals/REVIEW_SUMMARY.md     │
        └────────────────────────────────────────────┘
                          ↓ (人間 = ユーザー判断)
        ┌────────────────────────────────────────────┐
        │  Phase 2: 精査 BT (WFA/OOS/Deflated Sharpe)│
        │  ├─ 上位候補ごとに本格 BT                 │
        │  ├─ パラメータ感度分析                    │
        │  ├─ スプレッド/スリッページ厳密評価       │
        │  └─ Black Swan ストレステスト             │
        └────────────────────────────────────────────┘
                          ↓
        ┌────────────────────────────────────────────┐
        │  Phase 3: 採用判断 + SPEC v3 起草          │
        │  └─ 1 戦略 or 並列複数戦略を採用          │
        └────────────────────────────────────────────┘
                          ↓
        ┌────────────────────────────────────────────┐
        │  Phase 4: PoC 再起動                       │
        │  └─ デモ口座 → 経済性 Gate 通過 → 本番  │
        └────────────────────────────────────────────┘
```

---

## Phase 0 詳細

### 並列起草エージェント

| エージェント | subagent_type | ソース | 目標候補数 |
|---|---|---|---|
| phase0-memory | analyst | `memory/` の実践者知見、過去BT、亡き者DB | 5-10 |
| phase0-research | researcher | 2024-2026 の論文/GitHub/ブログ | 5-10 |
| phase0-internal | analyst | `src/` 既存コード、SPEC v2 遺産、データ | 5-10 |

### 各候補の必須要件 (PROPOSAL_TEMPLATE.md §「Gate 0」)

- **G0-A**: PF 0.95 を上回る成果根拠 (実BT or 理論的論証)
- **G0-B**: 放置してても自己改善ができる仕組み (擬似コード + トリガ + フォールバック)

### 出力配置
```
docs/proposals/phase0/
├── memory_<name>.md       (8件想定)
├── research_<name>.md     (9件想定)
├── internal_<name>.md     (8件想定)
├── MECE_AUDIT.md          (MECE 監査結果)
└── INDEX.md               (一覧 + 自己採点)
```

---

## MECE 監査詳細

### 検証軸 (8軸)
A. 戦略タイプ
B. シグナル源
C. 自己改善方式
D. 通貨・タイムフレーム
E. 既存資産再利用度
F. リスク管理レベル
G. 経済性ベンチマーク
H. 反論屋教訓の継承度

### 判定タイプ
- **M 違反 (重複)**: 統合 / 差分残し / 全く違う で分類
- **C 違反 (欠落)**: Phase 0 で補強起草 or 意図的除外
- **粒度の不揃い**: ポートフォリオ層 / ルーター層 / 単一戦略 を階層分離

### 統合提案の扱い
**集計フェーズで参照** (査読は全件並列で実施)。MECE で「実質同じ」とされた組も、6視点で違う評価が出る可能性があるため、査読をスキップしない。

---

## Phase 1 詳細

### 6評価委員の運用

各委員は **標準 subagent_type** で起動 (新規 subagent type は現セッションで認識されないため):

| 評価委員役割 | 標準 subagent_type マッピング | 必読役割定義 |
|---|---|---|
| economics | code-quality-pragmatist | `.claude/agents/proposal-reviewer-economics.md` |
| structure | ultrathink-debugger | `.claude/agents/proposal-reviewer-structure.md` |
| history | karen | `.claude/agents/proposal-reviewer-history.md` |
| implementation | analyst | `.claude/agents/proposal-reviewer-implementation.md` |
| risk | analyst | `.claude/agents/proposal-reviewer-risk.md` |
| meta | general-purpose | `.claude/agents/proposal-reviewer-meta.md` |

### 各委員の必読
1. `docs/PROPOSAL_TEMPLATE.md` (採点フレーム)
2. `docs/RETREAT_2026-05-26.md` (撤退教訓)
3. `docs/proposals/phase0/MECE_AUDIT.md` (構造監査)
4. 自分の役割定義 `.claude/agents/proposal-reviewer-<role>.md`
5. 関連反論屋分析 `docs/analysis/CONTRARIAN_<karen|ultra|pragmatist>.md`

### 出力配置
```
docs/proposals/reviews/
├── REVIEW_economics.md
├── REVIEW_structure.md
├── REVIEW_history.md
├── REVIEW_implementation.md
├── REVIEW_risk.md
└── REVIEW_meta.md
```

各 REVIEW は:
- 査読サマリ (スコア分布、即却下数、TOP 5)
- 全候補スコア表
- 即却下リスト
- TOP 5 推奨 (詳細)
- 全候補レビュー (簡易、各3-5行)
- 視点の総括

---

## 集計フェーズ詳細

### 集計の出力 (`docs/proposals/REVIEW_SUMMARY.md`)

#### 1. 6視点合算スコア表
```
| 候補 | econ | struct | hist | impl | risk | meta | 合計 | 中央値 | 分散 |
|---|---|---|---|---|---|---|---|---|---|
| ... | 8/10 | 9/10 | 7/10 | 9/10 | 8/10 | 8/10 | 49/60 | 8.0 | 0.6 |
```

#### 2. 全委員 PASS 候補
- 6委員すべてが「採用候補」or「条件付き」と判定したもの
- これが Phase 2 進出の **最強の信号**

#### 3. 即却下統合
- いずれかの委員が「即却下基準該当」とした候補
- どの基準に該当したか明示

#### 4. 委員間意見対立検出
- 分散大の候補 (例: economics 9 / risk 3) は何かの構造が見えている
- 高い委員 vs 低い委員の論点を抽出して人間判断材料に

#### 5. MECE 統合提案の反映
- 重複候補は委員評価を比較してどちらを残すか判断
- Phase 4 ラベル候補 (ポートフォリオ層) は本フェーズから分離

#### 6. Phase 2 進出推奨
- 6-10 候補に絞る
- 戦略タイプ多様性も考慮 (平均回帰一極集中を避ける)

---

## 設計選好

### 「全案通す」原則
ユーザー判断 (2026-05-26): 全候補を6視点で査読する。MECE 監査の「統合してから査読」案を採用しない。理由:
- 統合判断は委員意見を見てから人間が下す
- 査読フェーズで「同じ手法でも別視点での違い」が現れる可能性
- 視点別の独立性を最大化

### 「観点漏れ防止のため評価する側を先に固める」原則
ユーザー判断 (2026-05-26): Phase 0 候補が揃う前に評価委員を定義する。理由:
- 候補を見てから採点項目を作ると、候補に合わせて項目を調整するバイアス
- effort heuristic 罠の制度的回避

### 撤退・却下条件の事前明文化原則
PROPOSAL_TEMPLATE.md G0-B の必答項目として明文化。撤退原因 (90日放置) の制度的再発防止。

---

## SPEC v3 以降の運用

このプロセスは **戦略採用判断の汎用フレーム** として残す。将来:
- SPEC v3 が Phase 2 から進む際にこの PROCESS.md を再利用
- 採用候補が変わるたびに `docs/proposals/phaseN/` で新サイクル
- 評価委員定義 (`.claude/agents/proposal-reviewer-*.md`) は基本固定、必要に応じ追加項目

---

## 関連
- 採点項目: `docs/PROPOSAL_TEMPLATE.md`
- 撤退記録: `docs/RETREAT_2026-05-26.md`
- 各委員役割定義: `.claude/agents/proposal-reviewer-*.md`
- 反論屋分析: `docs/analysis/CONTRARIAN_*.md`
