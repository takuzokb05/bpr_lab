# STATUS — bpr_lab リポジトリ全体マップ

> **「いま」のスナップショット。** ふわっと指示を受けたAI／未来の自分が **最初に見る** ファイル。
> このファイルは `sandbox/` 配下サブプロジェクトの INDEX を兼ねる。個別の恒久ルールは各PJの CLAUDE.md を参照。
> 最終更新: 2026-07-07（新規作成）／ 更新方法: 手動編集

---

## 30秒サマリ

- **bpr_lab は「実験場（sandbox）リポジトリ」**。単一プロダクトではなく、業務効率化ツール・調査・個人アプリなど **30個の独立サブプロジェクト**が `sandbox/` 配下に並ぶ。
- 各サブPJは基本的に **self-contained**（自前の CLAUDE.md / docs / .claude を持つものが多い）。作業時はそのPJディレクトリを作業ディレクトリにする。
- **統合ハブは `sandbox/タスクマネージャー`**。蔵書管理（library/、記事2700件超）・情報収集スキル群・session-review 運用がここに集約されている（詳細はそちらの STATUS.md）。
- ルート直下の `src/` `web/` `library/` `data/` `node_modules/` 等はリポジトリ初期の足場。**現在の活動はほぼ全て `sandbox/` 配下**（要確認: ルート足場の現用途は未精査）。

---

## sandbox サブプロジェクト一覧（INDEX 兼）

状態の定義: **稼働中**=直近（2026-06以降）に開発/運用あり ／ **休眠**=開発停止中だが資産あり（ツール完成・調査済含む、再開可能） ／ **空**=中身なし。
状態の細分（完了/継続）は推測を含むため、稼働中/休眠/空の3段で表記し、成果物の性質は説明欄に記す。

| プロジェクト | 一行説明 | 状態 | 主要ファイル / entry |
|---|---|---|---|
| **タスクマネージャー** | sandbox統合ハブ。蔵書管理・情報収集パイプライン・スキル群を集約 | 稼働中 | `CLAUDE.md` / `library/` / `.claude/skills/`（8個） |
| **ai-teams** | AI Council（AI評議会）。討論番組スタイルの意思決定支援ツール。VPSデプロイ済・OSS(ai-council)同期 | 稼働中 | `README.md` / `web/` |
| **FX自動取引** | AI活用のFX自動取引システム。ConoHa VPS + MT5デモで稼働構成あり | 稼働中 | `STATUS.md` / `.claude/CLAUDE.md` / `src/` |
| **自作LLM** | 学習しながらLLMを内製しai-councilへ組込む。G検定対策(2026-07-04目標)兼 | 稼働中 | `CLAUDE.md`（現状ほぼ計画のみ） |
| **flash-study** | 資格試験向け学習ツール。RSVPフラッシュ読み＋4択クイズ。Phase2までprototype完成 | 稼働中 | `CLAUDE.md` / `prototype/index.html` |
| **よかちょ一覧** | 横浜市 固定資産税(償却資産)業務のブラウザ完結ツール群。外部通信なし | 休眠 | `CLAUDE.md` / `一品一覧化/` / `index.html` |
| **償却資産RAG提案** | 償却資産税部署へのRAG導入提案資料（引継ぎ用） | 休眠 | `CLAUDE.md` / `*.pdf`（成果物） |
| **マニュアル更新** | 共用部分代行管理のAIチャットボット構想。調査・構想段階 | 休眠 | `CLAUDE.md` / `research/` |
| **4象限マトリクス管理** | 緊急/重要マトリクスでタスク管理するHTMLツール | 休眠 | `DESIGN.md` / `app/` / `タスク管理.html` |
| **当番表作成ツール** | 当番表を生成するツール（src+tests構成） | 休眠 | `src/` / `tests/` |
| **当番表作成** | 当番表作成の初期版（職員一覧.xlsx ベース） | 休眠 | `職員一覧.xlsx` |
| **slack_ai_news** | Grok→Gemini→Slack の自律リサーチパイプライン＋Deepdive Bot | 休眠 | `README.md` / `deepdive_bot.py` |
| **SNSコンテンツ自動生成** | SNS投稿コンテンツの自動生成（SPEC/PLANS駆動） | 休眠 | `SPEC.md` / `PLANS.md` / `docs/` |
| **スライド作成ツール** | スライド生成ツール（SPEC/PLANS駆動） | 休眠 | `SPEC.md` / `PLANS.md` |
| **スライド作成** | スライド作成の調査・試作 | 休眠 | `PLANS.md` / `docs/` |
| **NotebookLM_pptx** | PDF/画像を高品質PPTXに変換（Gemini 3 Pro、クライアント側完結） | 休眠 | `README.md` / `素晴らしき修正ツール.html` |
| **PDFをOCR** | Gemini APIによるステートフルOCR（スライディングウィンドウ→Markdown） | 休眠 | `README.md` / `Nanobanana/` |
| **Kindle** | Kindle for PC 自動撮影→PDF変換ツール | 休眠 | `README.md` / `config.json` |
| **chrome拡張機能** | Chrome拡張（Kindleスクショ等） | 休眠 | `Kindleスクショ/` |
| **HTML直す君** | 壊れたHTMLを修正するツール | 休眠 | `index.html` / `出力例.txt` |
| **ganbarulist** | 妻向けToDoアプリ（心理学ベースの動機づけ設計、Vite） | 休眠 | `README.md` / `vite.config.js` |
| **task_kanri** | タスク管理Webアプリ（Vite+TS） | 休眠 | `README.md` / `vite.config.ts` |
| **資産プルーフ作成** | 資産証明の作成ツール（HTML） | 休眠 | `index.html` / `参照/` |
| **評価調書一覧** | 評価調書一覧（xlsx＋アイデアメモ） | 休眠 | `アイデア/評価調書一覧.xlsx` |
| **住宅比較** | 住宅購入の予算・品質・土地条件を総合検討（面談ログ分析） | 休眠 | `PROGRESS.md` / `run_analysis_trans.py` |
| **空き家問題** | 空き家問題の調査（PLANS/docs＋チャットログ） | 休眠 | `PLANS.md` / `docs/` |
| **リモートワーク調査** | リモートワークの調査ドキュメント（統合分析済） | 休眠 | `docs/04_統合分析.md` |
| **リモート開発コントロール** | リモート開発環境(ConoHa VPS)構築の調査ドキュメント | 休眠 | `docs/02_conoha_vps.md` |
| **Google研修** | Google研修のレポート／要約成果物 | 休眠 | `output/*.pdf` / `docs/` |
| **壁打ちのもう一人の自分** | 空ディレクトリ（要確認: タスクマネージャーの alter-ego/壁打ちへ統合済みか） | 空 | （中身なし） |

**内訳: 稼働中 5 / 休眠 24 / 空 1 = 30 ディレクトリ。** 別途アーカイブzip 2本（`よかちょ一覧.zip` / `償却資産RAG提案.zip`）がルートに存在。

---

## 直近の変更（git log）

直近20コミットは **すべて ai-teams（AI Council）** に集中。主な流れ:

- 惹きつけUI（開演前の議場・進行アーク・おかえりカード）、裁定(verdict)フェーズ＋収束の立場更新
- 問題再定義ゲート＋発散→収束の議事録構成、env変数を `AI_COUNCIL_` に統一（後方互換で `AI_TEAMS_` も読む）
- 実LLM e2e合格・ConoHa VPSデプロイ・OSS(ai-council)同期完了（`ssh -n` の罠を記録）
- 反論屋監査の確定18欠陥を全修正（復帰/データ消失/堅牢性/セキュリティ）

最新: `e6950c9 docs(ai-teams): OSS(ai-council 070e366)同期完了を記録`

---

## 補足（要確認事項）

- 各PJの「休眠/完了」の別は最終更新日と成果物有無から推定したもの。業務で継続利用中のツール（よかちょ一覧など）も開発が止まっていれば「休眠」表記とした。
- ルート直下の `src/` `web/` `library/` `data/` `新しいフォルダー/` の現用途は未精査（要確認）。
- リポジトリ全体を横断する README/CLAUDE.md はルートに無い（本 STATUS.md が実質のエントリ）。
