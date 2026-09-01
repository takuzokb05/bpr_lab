# 当番表作成ツール

## WHY

- **目的**: 庁内の当番表作成を自動化する単一HTMLファイルツール
- **対象ユーザー**: 200人規模の部署の庶務担当者（初めて使う職員でも説明なしで使えることが目標）
- **主要な価値**: 職員の制約条件（時短・公休・ペア研修等）を考慮した自動割り当て + Excel/印刷/デスクネッツNEO連携

## WHAT

### 技術スタック

- 単一HTMLファイル（CSS・JSをインラインに含む）
- 外部依存なし（CDN不使用、完全オフライン動作）
- データ保存: localStorage
- 動作確認: Chrome / Edge

### ディレクトリ構造

```
当番表作成ツール/
├── .claude/
│   ├── CLAUDE.md          # このファイル
│   ├── settings.json      # 権限・フック設定
│   ├── settings.local.json
│   ├── whiteboard.md      # エージェント間情報共有（追記のみ）
│   ├── skills/            # レビュースキル群
│   └── agents/            # レビューエージェント群
├── docs/
│   └── 当番表ツール_要件定義書.md  # 実装仕様書（SPEC）
├── src/                   # 単一HTMLファイル
├── tests/
│   ├── screenshots/       # Puppeteerスクショ出力先
│   └── take-screenshots.js
├── PLANS.md               # 進捗・意思決定の記録
└── .gitignore
```

### 要件定義書

`docs/当番表ツール_要件定義書.md` が本プロジェクトのSPEC。実装はこの文書に従う。

## HOW

### コーディング規約
- コメントは日本語、変数名・関数名は意味が明確な英語
- 1関数は1つの責務。マジックナンバーは定数として定義
- 機能追加の提案時は、まず既存コードに類似機能がないかGrepで確認する。「新規実装」と思い込んで既存の実装を見落とさない

### Git規約
- コミットメッセージ: `<type>(<scope>): <subject>`（type: feat/fix/docs/refactor/test、日本語OK）
- コミット前に動作確認を実施

### セキュリティ（IMPORTANT）

要件定義書に明記されたセキュリティルール。**厳守**:

| 場面 | NGパターン | 代替手段 |
|---|---|---|
| 職員名・ユーザー入力の表示 | `element.innerHTML = val` | `element.textContent = val` |
| イベント登録 | `<button onclick="fn()">` | `addEventListener('click', fn)` |
| 任意コード実行 | `eval()` / `new Function(str)` | 使わない |
| タイマーコールバック | `setTimeout("fn()", t)` | `setTimeout(() => fn(), t)` |
| DOM全体の書き換え | `document.write()` | 使わない |
| 変数宣言 | `var` | `const` / `let` |
| DOM要素生成 | `container.innerHTML = ...` | `createElement` + `textContent` |

### エラーハンドリング
- 例外を握りつぶさない
- ユーザー向けエラーメッセージは日本語で分かりやすく
- localStorageの読み書きは必ずtry-catchで囲む

```javascript
// localStorage読み込みパターン
try {
  const data = JSON.parse(localStorage.getItem('key') ?? 'null');
} catch (e) {
  // 破損データのフォールバック処理
}
```

### 禁止パターン

以下は明示的に禁止する:
- 空のexcept / catchブロック
- `git add .` / `git add -A`（対象ファイルを明示的に指定する）
- マジックナンバーの直接使用
- 未使用のimport・変数の放置
- 定数・変数・関数を参照箇所をGrepで確認せずに削除する（`WEEKDAY_NAMES_SHORT`削除でJSエラーを引き起こした前例あり）
- 過度な装飾（不要な絵文字、過剰なコメント、不要なdocstring）
- `Bash(cat ...)` でファイルを読む（Read ツールを使う）
- `Bash(find ...)` や `Bash(ls ...)` でファイルを探す（Glob ツールを使う）
- `Bash(grep ...)` や `Bash(rg ...)` でコード検索する（Grep ツールを使う）
- `Bash(sed ...)` や `Bash(awk ...)` でファイルを編集する（Edit ツールを使う）
- 外部URL（CDN / API / フォント / 画像）への通信
- グローバル変数の乱用（名前空間を分離すること）

### ツール実行時の許可ルール

- ツール実行（Bash、ファイル操作など）の許可を求めるときは、必ず日本語で説明・確認を行うこと
- 許可を求める際、以下のセキュリティリスクをパーセンテージ(%)で提示すること
  - パスワードや秘密鍵が外に漏れる可能性
  - 外部サーバーにデータが送られる可能性
  - 悪意あるコードが勝手に動く可能性
  - PCの設定が書き換わる可能性

### CLAUDE.md の運用ガイドライン

- CLAUDE.md は短く保つ。長すぎるとコンテキストを圧迫し、指示の遵守率が下がる
- 詳細は別ファイル（docs/、スキル定義等）に分離し、CLAUDE.md からリンクで参照する（Progressive Disclosure）

### エージェント共通ルール
- `.claude/whiteboard.md` はエージェント間の情報共有ファイル（Subagent・Agent Teams 共通）
- Agent Teams テームメイトは whiteboard.md のステータステーブルを必ず更新する

## WORKFLOWS

### 作業の基本ステップ

全タスクは以下の4ステップで進める:

1. **調査** — 現状を把握する。「フォルダ内容を確認して。**まだ何も変更しないで**」
2. **計画** — 方針を立てる。「計画を立てて。**実装はまだしないで**」
3. **実行** — 計画確認後に実装する
4. **確認** — 結果を検証する。「処理結果のサマリーを出して。元データとの整合性を確認して」

**IMPORTANT**: ステップ1・2で「まだ実行しないで」を明示すること。省略するとClaudeが即座に実装を始めるリスクがある。

### 検証ルール

出力に数値・固有名詞・日付が含まれる場合、以下を必ず実施する:
- 数値は元データと合計・件数を照合
- ファイル操作後は処理結果のサマリーを出力
- 2回修正しても正しくならない場合は `/rewind` で巻き戻すか新セッションで最初からやり直す

### レビューフロー（9割品質を担保する多層構成）

```
1. コード静的チェック
   ├── code-review（セキュリティ: innerHTML禁止等）
   └── error-handling-audit（localStorage破損・制約違反）
       |
2. ビジュアルレビュー（Puppeteerスクショベース）
   ├── ux-review（アクセシビリティ・ユーザビリティ・マイクロコピー）
   └── ui-design-review（ビジュアル品質・AI生成感の検出）
       |
3. 実データ結合テスト
   └── 既存「当番表作成/」の職員データで自動割り当てを実行し、制約違反がないか検証
       |
4. 最終レビュー
   ├── fact-checker（実装と要件定義書の突合）
   └── devils-advocate（反論レビュー）
```

### スクショ撮影

```bash
# Puppeteerで複数状態のスクリーンショットを撮影
node tests/take-screenshots.js
# 出力: tests/screenshots/ 配下に PNG ファイル
```

### Puppeteerテスト安定化ルール

- このマシンでは `protocolTimeout` が頻発する。複数ページ・複数ブラウザの同時起動は避ける
- 単一ブラウザインスタンスを使い回し、`protocolTimeout: 120000` 以上を設定
- `--no-sandbox` フラグを付与すること
- JSDOM方式は不採用（localStorage/イベント周りの制約で当番表ツールのテストには不向き）

### 利用可能なスキル

| スキル | パス | 用途 |
|--------|------|------|
| code-review | .claude/skills/code-review/ | 多角的コードレビュー（堅牢性・効率性・セキュリティ・保守性） |
| error-handling-audit | .claude/skills/error-handling-audit/ | エラーハンドリング監査・改善 |
| ux-review | .claude/skills/ux-review/ | UXレビュー（WCAG 2.2 AA・ニールセン・マイクロコピー） |
| ui-design-review | .claude/skills/ui-design-review/ | UIビジュアル収束監査（AI生成感の検出・修正コード付き） |

### 利用可能なエージェント

| エージェント | パス | 用途 |
|-------------|------|------|
| fact-checker | .claude/agents/fact-checker.md | 事実検証（実装と要件定義書の突合） |
| devils-advocate | .claude/agents/devils-advocate.md | 反論レビュー（設計判断の弱点指摘） |

## プロジェクト固有のルール

### 当番表ドメイン

- 自動割り当てアルゴリズムは要件定義書の「優先ルール」を厳守する（ハード制約 → 同日重複禁止 → 連続回避 → 回数分散）
- 自動割り当ては `runAutoAssign` 冒頭で職員リストをシャッフルし、全処理でそのリストを使うこと（登録順バイアス防止）
- 候補ソートキー: 全体回数 → 枠別回数(`slotAssignCount`) → 同曜日回数(`dowAssignCount`) → ランダム
- 枠の処理順は `workDayIndex % スロット数` でローテーションする（偶数人での午前午後固定化防止）
- 当番枠は `applyMode`（'workdays' | 'specific'）と `specificDays` を持ち、`isSlotActiveForDay` がセル単位の有効/無効を判定する（日単位スキップは禁止）
- ペア処理は `countFilledSlots()` で実効枠数を計算し、`requiredCount` との比較に使う。`assignments.length` を直接使わない（ペアモードで人数≠枠数になるため）
- `pairSlotMode` は `'single'`（2人で1枠）/ `'double'`（2人で2枠、デフォルト）。ペア相手にも `syncTrainingPair` で自動同期する
- 職員編集モーダルのステータスチェックは `draft._show*` 一時フラグで再描画後もチェック状態を保持する。保存時に `_` 始まりのフラグは自動除去
- 職員ステータスの組み合わせ（時短+曜日固定+公休日あり等）を正しく処理すること
- タグは自動ロジックに影響しない（視覚的識別のみ）

### UI/UX方針

- 「分かりやすさ」を最優先。初めて使う職員でも説明なしで使えること
- 設定項目は段階的に開示（最初に全部出さない）
- エラーは即座にわかりやすく（赤ハイライト等）
- モバイル対応は不要（庁内PC使用前提）
- 専門用語を避ける（「ハード制約」「アサイン」等は使わず日本語で平易に）
- A4印刷を考慮したレイアウト
- 設定値は庶務担当者の言葉に合わせる。内部的な数値（倍率・閾値）はUIに出さず、段階ラベル（「少なめ」「多め」等）で表現する
- Min/Max両方の入力、数値の直接入力など「エンジニア的に柔軟」な設計より、選択肢を絞って迷わない設計を優先する

### セッション終了時

セッション終了時（ユーザーが `/suggest-claude-md` を実行、または明示的に終了を伝えた場合）:

1. **PLANS.md を更新**: 完了タスクにチェックを入れ、Surprises & Discoveries / Decision Log に記録する
2. **メモリを更新**: 重要な知見・判断があれば `project_toban_tool.md` に追記する
3. **session-review.md をタスマネに書く**: `C:\Users\takuz\プロジェクト\bpr_lab\sandbox\タスクマネージャー\.claude\session-review.md` にCLAUDE.md改善提案・ユーザープロファイル更新提案を出力する（タスマネの次セッションで自動提示される）

### デスクネッツNEO連携

- CSV出力はV8.0ベースの列構成に準拠（ID系の列は空欄で出力）
- 文字コードはBOM付きUTF-8で出力
- **インポート先はNEO側のインポート画面で選択する仕様**（CSV内のID列では振り分け不可・1ファイル=1登録先）。IDマッピングUIは2026-09-01に廃止済み
- 出力は2系統: 「まとめて1枚」（共有アカウント/組織用・予定欄=枠名（職員名））と「個人別ZIP」（1人1CSV・ファイル名に職員名・無圧縮ZIP自前実装）
