# Google研修 越境DX支援制度レポート

## プロジェクト概要

- **目的**: Google研修を起点に、横浜市のDXリーダー100人向けに「越境DX支援制度」の提案レポートをHTMLで作成・共有する
- **対象**: DXリーダー100人（職員8割、係長1.5割、課長0.5割）
- **主要な価値**: i-share制度をDX支援に拡張する具体的提案と、段階的参加パスの設計

## 調査の問い

| # | 問い | 出力ドキュメント | 依存 | 手法 |
|---|------|-----------------|------|------|
| Q1 | i-share制度のDX活用実態と課題は何か | docs/01_i-share-dx.md | なし | evidence_collection |
| Q2 | 横浜市のDX推進体制・兼務発令の現状と課題は何か | docs/02_yokohama-dx-structure.md | なし | evidence_collection |
| -- | 統合（既存素材の検証・再構成に活用） | docs/03_synthesis.md | Q1, Q2 | synthesis |

## ディレクトリ構造

```
Google研修/
├── docs/               # 検証済みドキュメント
├── references/         # 既存素材（チャット、設計戦略、20%ルール分析、GWS事例等）
├── output/             # 最終HTML成果物
├── .claude/
│   ├── claude.md       # このファイル
│   ├── settings.json   # WebSearch/WebFetch自動承認
│   ├── whiteboard.md   # エージェント間情報共有（追記のみ）
│   ├── agents/         # エージェント定義
│   │   ├── researcher.md
│   │   ├── fact-checker.md
│   │   └── devils-advocate.md
│   └── skills/
│       └── anti-ai-slop-frontend/  # HTMLデザインスキル
├── PLANS.md            # 進捗・意思決定の記録
└── .gitignore
```

## フェーズ構成

```
Phase A: 検証
  1. fact-checker → references/ 内の既存レポート2本を事実検証
  2. 修正を久保さんと確認 → 反映
  3. devils-advocate → 修正後の設計戦略を論理攻撃
  4. 久保さんと対話 → 4タイプ再設計・i-share接続・コンテンツ確定

Phase B: レポート作成
  1. anti-ai-slop-frontend スキルに基づいてHTMLレポート作成
  2. Teams共有前提 → CDN非依存、完全自己完結HTML
  3. output/report.html に出力
```

## 調査ルール

### ソースと信頼性

- **全ての主張にソース（URL・出典）を必ず付ける**
- 一次ソース（公式ドキュメント・学術論文・政府資料）を優先する
- 同じ情報を異なるソースでクロスチェックする
- 情報の鮮度（年度）に注意し、古いデータには明示する
- **横浜市の一次情報を優先**: 横浜市公式サイト、横浜市デジタル統括本部note、人材成長戦略PDF、横浜DX戦略
- **自治体DX一次情報**: 総務省、デジタル庁、各自治体公式発表
- **学術・研究**: エドモンドソン（心理的安全性）、ロジャーズ（普及理論）等の原著・原論文

### 分析姿勢

- 主張を無批判に受け入れない（批判的検証を徹底する）
- 具体的な数字・データを優先する（定性的な印象より定量的な根拠）
- 反例や不利なデータも公平に扱う
- **行政組織の実態**: 制度上の建前と運用上の実態を区別する

### 品質チェック

- 各ドキュメントは fact-checker で事実検証を実施
- 統合ドキュメントは devils-advocate で論理攻撃を実施
- fact-checker → 修正反映 → devils-advocate の順序を守る（並列不可）

## サブエージェントのWebSearch権限

`.claude/settings.json` の2層構成でWebSearch/WebFetchを自動承認する:

1. **`permissions.allow`**（静的許可）: バックグラウンドサブエージェント起動前の事前承認ステージで評価される
2. **`PreToolUse` フック**（動的許可）: ツール使用時に評価されるバックアップ

## レビューワークフロー

```
Phase A-1: fact-checker → references/ 内の2本を検証 → docs/fact-check-report.md
Phase A-2: 修正反映（久保さんと確認）
Phase A-3: devils-advocate → 修正後の設計戦略を論理攻撃 → docs/devils-advocate-report.md
Phase A-4: 久保さんと対話 → 方向性確定
Phase B:   HTMLレポート作成 → output/report.html
```

**whiteboard.md**: `.claude/whiteboard.md` はエージェント間の情報共有ファイル。各エージェントが作業開始時に読み、完了時にサマリーを追記する。追記のみ（削除・上書き禁止）。

## Git規約

- コミットメッセージ: `<type>(<scope>): <subject>`
  - type: docs / fix / refactor
  - scope: doc名（01, 02等）
  - 日本語OK

## 利用可能なスキル

- skills/anti-ai-slop-frontend/ - AI臭のないHTMLレポートデザイン（6軸制約: タイポグラフィ・カラー・レイアウト・モーション・背景・コンポーネント）

## 利用可能なエージェント

- agents/researcher.md - Web調査（i-share制度、横浜市DX体制の補強調査）
- agents/fact-checker.md - 事実検証（既存レポートの数値・引用・事例の正確性検証）
- agents/devils-advocate.md - 反論・論理攻撃（提案の弱点・暗黙の前提の指摘）

<!-- 重要: 各エージェント定義の「起動方法」セクションに記載された subagent_type と mode を使うこと。
     Explore タイプでは Write/Edit が使えず、ファイル出力が空になる。
     全エージェントは subagent_type: general-purpose, mode: bypassPermissions で起動する。 -->

## プロジェクト固有のルール

- **名義**: 財政局償却資産課 久保
- **読者**: DXリーダー100人（職員8割、係長1.5割、課長0.5割）。専門家だけでなく幅広い理解度の人が対象
- **配布方法**: Teams共有（HTMLファイル直接）
- **HTMLの制約**: CDN非依存、完全自己完結（CSS/JSインライン）。Google Fontsのみ外部読み込み許可
- **i-share制度との関係**: 新制度を作るのではなく、既存のi-share制度をDX支援に拡張する提案として位置づける
- **4タイプ分類の注意**: 「スキルあり・意志弱い」ではなく「DXスキル高い・越境スキル未経験」。DXスキルと越境スキルは別軸。「意志弱い」という表現は使わない
- **トーン**: コンサルの報告書ではなく、同じ立場の職員からの問いかけ。当事者性を前面に出す
- **既存素材の活用**: references/ 内のファイルは検証済みの素材として活用。ただしファクトチェック・反論レビューで修正が必要な箇所は更新する
