# 競合ベンチマーク — 4象限マトリクスに効く機能の輸入候補

調査日: 2026-04-17
対象プロダクト: `タスク管理.html`（単一HTML / LocalStorage / 4象限 / Survivalモード / 完了履歴 / Undo）
調査者: 競合調査担当

## 調査サマリ

- 「4象限に native 対応」しているのはほぼ **TickTick だけ**。他ツールは原則「フィルタ/タグ/スコアで疑似 Eisenhower を実現」している。自プロダクトは既にこの一等地を占めているので、輸入すべきは「4象限に入れる前後の摩擦を下げる機能」と「入れた後の腐敗（古いタスクの堆積）を防ぐ機能」。
- ADHD 観点で効きが強いのは次の 4 系統:
  1. **入力摩擦を下げる**: Todoist の自然言語クイック入力、Things 3 の Magic Plus、Bullet Journal の Rapid Logging 記号
  2. **開始摩擦を下げる**: TickTick / Super Productivity のポモドーロ内蔵、Sunsama の timeboxing
  3. **選択麻痺を減らす**: Amplenote の Task Score（自動ソート）、Things 3 の Today 抽出、Notion ADHD テンプレの「今日やる 1 件」
  4. **堆積を防ぐ**: OmniFocus の Review サイクル、Bullet Journal の Migration、Sunsama の Shutdown Ritual
- 逆に **輸入すべきでない** のは Motion 系の AI 自動スケジューリング（単一HTML・オフラインでは成立しない）、Trello の Butler（象限思想と衝突）、Notion のブロック編集（シンプルさを殺す）。

---

## ツール別 — 輸入候補機能リスト

### Todoist
- **機能名: 自然言語クイック入力（Quick Add）**
  - 何が良いか: `レポート提出 tomorrow 5pm p1 @work` のような 1 行入力で、タイトル・期限・優先度・ラベルを同時に確定できる。ADHD の「項目ごとにフォームを埋める」摩擦を劇的に下げる。
  - 4象限ツールへの落とし込み案: 追加ダイアログの title 入力欄をパーサに差し替え。`!` または `p1/p2` で象限を即指定（p1→Q1, p2→Q2, p3→Q3, p4→Q4）、`@tag`、`by 金曜` で dueDate をパース。パース結果はチップでプレビュー表示し、誤認識を視認可能にする。
  - 実装難度: **M**（日本語日付パーサは簡易版で `今日/明日/明後日/月曜/来週/N日後/MM/DD` に絞れば軽量）
  - 整合性リスク: 低。現状の「象限に入れる」という動作と両立する。上級者モードとしてオプションで有効化も可。

- **機能名: Recurring タスク（自然言語）**
  - 何が良いか: 「毎週月曜」「毎月1日」「平日」で定期タスクを表現。完了時に次回が自動生成。
  - 4象限ツールへの落とし込み案: task オブジェクトに `recurrence: "weekly:mon"` のような文字列を追加。完了時に `baseTask()` で複製＋ dueDate を次回に進める。象限は元と同じ（Q2に吸収されやすい）。
  - 実装難度: **M**
  - 整合性リスク: 中。完了履歴に「同じタイトル」が大量に並びノイズ化する恐れ→ 完了履歴は「最終完了日時＋カウント」で集約表示すべき。

### TickTick
- **機能名: ポモドーロ内蔵 + 集中モード**
  - 何が良いか: カード上の再生ボタンで 25 分タイマが開始、タスクと時間の紐付けが自然に成立。アプリ内で完結するため「時間を測るぞ」と意識せずに始められる。
  - 4象限ツールへの落とし込み案: カードに `▶` アイコン追加 → クリックで全画面フォーカスオーバーレイ（現タスクのみ表示・他象限を暗転）＋ 25/5 分カウントダウン。終了時にアクティビティログへ `focus_session` を記録。LocalStorage に累積 focus 秒を持たせ、カードに小さく累積バー表示。
  - 実装難度: **M**（Web Audio API のチーン音、Page Visibility API で他タブ時も正確に計測）
  - 整合性リスク: 低。Survivalモードと排他にすればUIが混雑しない。

- **機能名: Eisenhower Matrix の「ルール編集」**
  - 何が良いか: 「urgent = due within 3 days」「important = tag:priority」のようにユーザが象限判定ルールを編集できる。
  - 4象限ツールへの落とし込み案: 今はドラッグで手動配置。`設定 > 自動象限判定` に「dueDate が N 日以内なら緊急扱い」トグルを追加。タスクにはユーザが手動で置いた場合の `manualQuadrant` フラグを持たせ、手動優先。
  - 実装難度: **S**
  - 整合性リスク: 中。自動判定と手動の整合が崩れると混乱する。デフォルトは OFF が安全。

### Things 3
- **機能名: Magic Plus（任意位置への追加）**
  - 何が良いか: ＋ボタンをドラッグして挿入位置を決める。象限内の並び順＝優先度、という運用が可能に。
  - 4象限ツールへの落とし込み案: 現在のカード並びは新しい順。各象限ヘッダの＋ボタンを「ドラッグ可」にし、ドロップ位置で `order` フィールドを決定。既に D&D 実装があるため拡張コスト低。
  - 実装難度: **S**
  - 整合性リスク: 低。

- **機能名: Today ビュー（今日やる抽出）**
  - 何が良いか: プロジェクト横断で「今日着手」だけ集める。毎朝この 1 画面を見ればよい、という選択麻痺解消装置。
  - 4象限ツールへの落とし込み案: ヘッダに `🎯 Today` トグル。ONで `dueDate==today || isInSurvivalSlot || starred` のカードだけを 1 カラムリスト表示（象限色は左ボーダーに退避）。OFF で4象限へ戻る。
  - 実装難度: **S**
  - 整合性リスク: 低。既存の Survival とは別レイヤ（Survival は締切圧、Today は意図）。

- **機能名: Quick Entry with Autofill**
  - 何が良いか: グローバルショートカットで最前面にキャプチャ窓。
  - 4象限ツールへの落とし込み案: 単一HTMLではOSグローバルは無理。代替として `n` キー（どこでも）で追加ダイアログ、`Ctrl+Enter` で即保存。PWA化すれば Share Target API でモバイルの共有シートから追加可能（将来案）。
  - 実装難度: **S**（キーバインドのみ）/ **L**（PWA 化）
  - 整合性リスク: 低。

### Notion / Amplenote
- **機能名: Amplenote の Task Score（自動スコアリング）**
  - 何が良いか: 「urgent」「important」「due today」「何日放置されたか」から自動で点数を出し、毎日少しずつスコアが上がっていく。放置タスクが勝手に頭に上がってくる。
  - 4象限ツールへの落とし込み案: 各象限内の並び順に score を導入。`score = quadrantWeight + daysSinceCreated*k + (isOverdue?20:0)`。象限の並びは `order` または `score` をトグル切替。古くて放置された Q2 タスクが自動で目に入るようになる → ADHD の「忘却による埋没」対策。
  - 実装難度: **S**
  - 整合性リスク: 低。デフォルトを「作成日降順」のままに、オプションで有効化。

- **機能名: Notion ADHD テンプレの「1 タスク DB + トリアージ」思想**
  - 何が良いか: 「DBは1つ、毎朝3分でトリアージ」。カラムや複雑なビューを足さない。
  - 4象限ツールへの落とし込み案: 新機能ではなく **設計思想の確認**。この原則があることで「プロジェクト機能」「サブタスク」「カスタムフィールド」の追加要望を蹴る根拠になる。
  - 実装難度: **S**（意思決定）
  - 整合性リスク: 該当せず。

- **機能名: Notion / Amplenote 共通のノート融合**
  - 何が良いか: タスクに長文メモ・チェックリストを紐付け。
  - 4象限ツールへの落とし込み案: 現状 note フィールドはあるはず。Markdown (最小: 改行・箇条書き `- `・チェックボックス `[ ]`) の軽量レンダリングだけ追加。サブタスクの代用になる。
  - 実装難度: **S**
  - 整合性リスク: 低。フル Markdown は入れない（シンプルさ死守）。

### Trello
- **機能名: Butler のカード自動移動ルール**
  - 何が良いか: 「due が 24 時間以内になったら 'Urgent' リストへ」などの自動化。
  - 4象限ツールへの落とし込み案: 「dueDate が N 日以内になったら自動で Q1 へ昇格」「放置 30 日で Q4 に降格」のルールを 2 本だけ固定実装。ユーザが編集可能な DSL は入れない（シンプルさ維持）。
  - 実装難度: **S**
  - 整合性リスク: 中。ユーザが手動で置いた象限を上書きするため、`manualQuadrant` フラグで保護必須。

- **機能名: カンバン D&D**
  - 何が良いか: 自プロダクトで既に実装済み。
  - 落とし込み案: 学ぶべきは「ドロップ時のアニメーション（ゴム紐）」と「空象限のゴースト表示」。微差だが ADHD は視覚フィードバックに強く反応。
  - 実装難度: **S**
  - 整合性リスク: なし。

### Sunsama
- **機能名: Daily Planning ritual（朝5〜10分のガイド付き計画）**
  - 何が良いか: 「昨日のやり残しを見る → 今日やるものを選ぶ → 時間見積り → カレンダーに置く」を誘導。自分で考えずとも手順に従えば計画が完成する。
  - 4象限ツールへの落とし込み案: `☀️ 朝の3分プラン` ボタン。モーダルが 3 ステップで順に開く:
    1. 昨日完了/未完了サマリ表示
    2. Q1/Q2 から今日やる 3 件を選ぶ（チェックボックス）→ Today リストへ
    3. 「開始予定時刻」だけ入力（カレンダー連携は無し）
  - 実装難度: **M**
  - 整合性リスク: 低。やらない日はスキップできる。

- **機能名: Shutdown Ritual（夕方の振り返り）**
  - 何が良いか: 翌日の自分への引き継ぎを明示化。心理的な「仕事を閉じる」儀式。
  - 4象限ツールへの落とし込み案: `🌙 夜の1分振り返り` ボタン。完了数・未完了数を表示し、「明日やる 1 件」をピン留め。翌朝の Daily Planning モーダルがそれを先頭提示。
  - 実装難度: **S**
  - 整合性リスク: 低。

- **機能名: Timeboxing（タスクに予定時間を置く）**
  - 何が良いか: 「14:00-15:00 この Q2 タスク」と決める。開始時刻プレッシャが走る。
  - 4象限ツールへの落とし込み案: dueDate と別に `plannedStart: HH:MM`, `estimateMinutes: N` を追加。Today ビューでタイムライン風に縦並べ。これは Survival モードと相性が良い。
  - 実装難度: **M**
  - 整合性リスク: 中。全タスクに時刻を持たせると再び摩擦が増える → Today 選抜済みのものだけに UI を出す。

### OmniFocus
- **機能名: Review サイクル（プロジェクト再点検）**
  - 何が良いか: 全タスクに「次回レビュー日」を持ち、期日が来たら強制的に再点検させる。放置の炙り出し。
  - 4象限ツールへの落とし込み案: Q2 のタスクだけに `lastReviewedAt` を持たせ、14 日経過で「再点検」バッジ表示。クリックで「続ける / 削除 / Q4 に送る」を選べるダイアログ。Q2 の腐敗防止に直接効く。
  - 実装難度: **S**
  - 整合性リスク: 低。バッジだけなので無視もできる。

- **機能名: Defer Date（開始可能日）**
  - 何が良いか: `dueDate` とは別に「この日が来るまで非表示」。未来のタスクでマトリクスが渋滞するのを防ぐ。
  - 4象限ツールへの落とし込み案: `deferUntil: YYYY-MM-DD`。その日までカードは薄くグレーアウト（完全非表示は危険、存在は見える方がよい）。
  - 実装難度: **S**
  - 整合性リスク: 中。ADHD は「見えないと忘れる」ため **非表示ではなく薄化** にする点が重要。

- **機能名: Perspectives（保存済みフィルタビュー）**
  - 何が良いか: 「仕事」「家」などタグで切り替え可能。
  - 落とし込み案: ヘッダに `タグで絞る` ドロップダウン 1 つだけ。複数ビュー保存までは過剰。
  - 実装難度: **S**
  - 整合性リスク: 低。

### Motion / Reclaim.ai
- **機能名: AI 自動スケジューリング**
  - 何が良いか: カレンダー空き時間に自動でタスクを配置。
  - 4象限ツールへの落とし込み案: **原則採用しない**。オフライン・単一HTMLでは外部カレンダーも AI もない。ただし「自動配置の思想」だけ拝借し、Today ビューで estimateMinutes 合計が現在時刻〜終業までを超えたら赤字で警告（オーバーコミット検知）。
  - 実装難度: **S**（警告のみ）
  - 整合性リスク: 低。

### Super Productivity
- **機能名: Focus Mode（他を消して1タスクだけ表示）**
  - 何が良いか: オープンソースで実装パターンが参考になる。ADHD に強く効く。
  - 4象限ツールへの落とし込み案: TickTick ポモドーロと統合。`▶` で「全象限暗転 + 中央に現タスク大表示 + 25 分タイマ」。完了で `Q2 から次の1件` を自動抽出。
  - 実装難度: **M**
  - 整合性リスク: 低。Survivalモードと排他。

- **機能名: 手動タイムトラッキング**
  - 何が良いか: タスクごとに累積作業時間を記録。
  - 4象限ツールへの落とし込み案: ポモドーロのついでに `timeSpentSec` を加算。完了時に「今回の合計時間」をカードに残す → 次回の見積り精度に効く。
  - 実装難度: **S**
  - 整合性リスク: 低。

- **機能名: CBT プロンプト（先延ばし対策）**
  - 何が良いか: 先延ばしを検出したら「この作業で最悪何が起きる？」を問いかける。
  - 4象限ツールへの落とし込み案: Q1 に 3 日以上留まっているカードに「なぜ手をつけられない？」ワンクリックメモ欄を展開。書くだけで動ける、は ADHD の鉄則。
  - 実装難度: **S**
  - 整合性リスク: 低。

### Bullet Journal
- **機能名: Rapid Logging 記号（`・` task, `○` event, `-` note, `×` done, `>` migrated）**
  - 何が良いか: 記号で瞬時に種別を表現。思考を止めない。
  - 4象限ツールへの落とし込み案: Quick Add 入力欄で冒頭記号をショートカット解釈。`! 〜` で緊急フラグ、`* 〜` で重要フラグ、`? 〜` で Q4（判断保留）。アイコン UI と併用で視覚統一。
  - 実装難度: **S**
  - 整合性リスク: 低。

- **機能名: Migration（月末に次へ持ち越すか判断）**
  - 何が良いか: 月単位で全タスクを一度見直し、`>`（持ち越し）or `x`（破棄）を判定。自然に削除が進む。
  - 4象限ツールへの落とし込み案: 月初に「先月の未完了 N 件を一気にトリアージ」モーダル。カード1枚ずつ `続ける / 削除 / Q4 へ` の 3 択。OmniFocus の Review と思想は同じ。Q2 腐敗防止の決定版。
  - 実装難度: **M**
  - 整合性リスク: 低。月 1 回だけ。

---

## 横断 — 高優先の輸入候補 Top 10

| #  | 機能                                     | 元ネタ                 | 効果                                               | 実装案                                                                                        | 難度 |
| -- | ---------------------------------------- | ---------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---- |
| 1  | 自然言語 Quick Add                       | Todoist / BulletJournal | 入力摩擦 -70%。ADHD の「面倒で追加しない」を潰す | 追加ダイアログの単一入力欄 + チップでプレビュー。`!` `*` `p1` `明日` `@tag` を解釈            | M    |
| 2  | Today ビュー                             | Things 3               | 毎朝これだけ見れば決まる。選択麻痺を潰す           | `🎯 Today` トグル。dueToday / starred / survivalSlot のみを 1 カラム表示                      | S    |
| 3  | ポモドーロ + Focus Mode                  | TickTick / Super Prod. | 開始摩擦を潰す。仕事に潜れる                       | カードの `▶` → 全画面オーバーレイ + 25/5 分カウント。Survivalと排他                          | M    |
| 4  | Monthly Migration                        | Bullet Journal / OmniFocus | Q2 の腐敗・Q4 の堆積を月1で一掃                | 月初に未完了全件を 1 枚ずつ `続/削/Q4` 判定モーダル                                          | M    |
| 5  | Daily / Shutdown ritual                  | Sunsama                | 朝: 今日やる3件を確定 / 夜: 翌日へ引き継ぎ         | 2 本のガイド付きモーダル。スキップ可                                                          | M    |
| 6  | Task Score 自動ソート                    | Amplenote              | 放置タスクが自然に頭に上がる                      | `score = 経過日数 * w + overdue * 20 + quadrant基礎点` で並び替えトグル                      | S    |
| 7  | Review バッジ（Q2限定）                  | OmniFocus              | 14日触れないQ2タスクに「再点検」バッジ            | `lastReviewedAt` で判定。クリックで3択ダイアログ                                              | S    |
| 8  | Magic Plus / 任意位置挿入                | Things 3               | 象限内で手動優先順位をつけられる                  | 既存 D&D に `order` フィールド追加                                                            | S    |
| 9  | CBT 先延ばし問いかけ                     | Super Productivity     | Q1 塩漬けカードを言語化で動かす                   | 72h Q1滞留で「なぜ動けない？」インライン欄表示                                                | S    |
| 10 | 軽量 Markdown ノート                     | Notion / Amplenote     | サブタスク代用 / 文脈を一緒に置ける               | note フィールドで改行・`- ` リスト・`[ ]` チェックボックスのみレンダリング                    | S    |

---

## 取り入れるべきでないもの（アンチパターン）

- **Motion 系 AI 自動スケジューリング**: オフライン・単一HTMLでは成立しない。AI を入れた瞬間にサーバ/APIキー/課金が発生し、プロダクトの前提が崩れる。
- **Trello Butler のフル DSL 自動化**: ルール定義UIが複雑。ADHD には「設定画面で迷子」になるのが最大の敵。自動昇格ルールは 2 本固定で十分。
- **Notion ブロックエディタ**: タスクに任意構造を入れられる自由度はシンプルさを破壊する。軽量 Markdown で止める。
- **OmniFocus のパースペクティブフル機能**: 保存ビューを複数作れる設計は個人1名運用では過剰。タグフィルタ 1 つで足りる。
- **プロジェクト階層 / サブタスク階層**: これを入れると 4 象限の「1 画面で全部見える」が崩壊する。サブタスクは Markdown チェックボックスで擬似実現する線で止める。
- **チーム機能 / アサイン / コメント**: 個人利用前提に反する。絶対に入れない。
- **ハビットトラッカー（TickTick）**: タスク管理とは文脈が違う。別プロダクトで作る方が健全（推測: 後述の「習慣は Q2 の recurring で代替できる」）。
- **Sunsama Timeboxing 2.0 のカレンダー連携**: Google Calendar API 必須。単一HTMLには合わない。「予定時刻フィールド」だけ輸入し、外部同期は切る。
- **完了タスクの Streak / バッジゲーミフィケーション**: ADHD は初期は効くが数週で飽き、達成していない時の罪悪感装置に変わる（推測: よくある失敗パターン）。Survivalモードの締切圧で十分。

---

## 出典

- [TickTick: Eisenhower Matrix How-to](https://help.ticktick.com/articles/7055782055577124864)
- [TickTick: Eisenhower Matrix feature](https://help.ticktick.com/articles/7055782071033135104)
- [TickTick: Edit Rules for Eisenhower Matrix](https://help.ticktick.com/articles/7055782040439881728)
- [Why the Eisenhower Matrix Keeps Failing You — and How to Fix It in 2026](https://www.shareuhack.com/en/posts/use-time-matrix-to-make-life-easier)
- [Todoist: Use Task Quick Add](https://www.todoist.com/help/articles/use-task-quick-add-in-todoist-va4Lhpzz)
- [Todoist: Introduction to recurring dates](https://www.todoist.com/help/articles/introduction-to-recurring-dates-YUYVJJAV)
- [Using Natural Language with Todoist – The Sweet Setup](https://thesweetsetup.com/using-natural-language-with-todoist/)
- [Todoist Tutorial 2026 - Geeky Gadgets](https://www.geeky-gadgets.com/organize-tasks-todoist/)
- [Things 3: Quick Entry guide - The Sweet Setup](https://thesweetsetup.com/a-guide-to-capturing-tasks-in-things-3-for-ipad-and-iphone/)
- [Things 3 Review: Features 2026](https://www.techrepublic.com/article/things-3-review/)
- [Things 3 - ToolGuide 2026](https://toolguide.io/en/tool/things-3/)
- [Sunsama Daily Planning docs](https://help.sunsama.com/docs/daily-planning)
- [Sunsama Review 2026 - Calmevo](https://calmevo.com/sunsama-review/)
- [An Unfiltered Sunsama Review 2026](https://thebusinessdive.com/sunsama-review)
- [Sunsama main site](https://www.sunsama.com/)
- [OmniFocus 4 Reference: Perspectives](https://support.omnigroup.com/documentation/omnifocus/universal/4.8.5/en/perspectives/)
- [Learn OmniFocus: Custom Perspectives](https://learnomnifocus.com/custom-perspectives/)
- [OmniFocus Review 2026 - Merazoo](https://merazoo.com/omnifocus-review-2026/)
- [Motion vs Reclaim 2026 - Morgen](https://www.morgen.so/blog-posts/motion-vs-reclaim)
- [Motion vs Reclaim AI 2026 - Calmevo](https://calmevo.com/motion-vs-reclaim-ai/)
- [Super Productivity - official](https://super-productivity.com/)
- [Super Productivity: Pomodoro use case](https://super-productivity.com/use-cases/pomodoro/)
- [Super Productivity on opensource.com](https://opensource.com/article/20/12/super-productivity)
- [Tiimo: Eisenhower Matrix for ADHD](https://www.tiimoapp.com/resource-hub/how-to-prioritize-tasks-eisenhower-matrix)
- [Summit Psychology: Eisenhower Matrix ADHD](https://www.thesummitpsychology.com/blog/the-eisenhower-matrix-prioritizing-tasks-with-adhd)
- [Honestly ADHD: ADHD Priority Matrix](https://honestlyadhd.com/adhd-priority-matrix/)
- [getInflow: Priority matrix ADHD-tested](https://www.getinflow.io/post/eisenhower-matrix-adhd-prioritization-hack)
- [Trello Butler automation - official](https://trello.com/butler-automation)
- [Trello Butler Automation Guide - Hevo](https://hevodata.com/learn/trello-butler-automation/)
- [Amplenote: How Task Score Works](https://www.amplenote.com/help/tasks_and_todos_task_score)
- [Amplenote: Create a task from a jot](https://www.amplenote.com/help/create_a_task_from_a_jot)
- [Amplenote: Task Commands Menu](https://www.amplenote.com/help/task_commands_menu)
- [Bullet Journal: Rapid Logging FAQ](https://bulletjournal.com/blogs/faq/what-is-rapid-logging-understand-rapid-logging-bullets-and-signifiers)
- [BuJoing: Rapid Log & Migration](https://bujoing.com/bujo-rapid-log-migration/)
- [RocketLog: Digital bullet journal](https://rocketlog.app/)
- [Notion: ADHD Daily Planner template](https://www.notion.com/templates/adhd-daily-planner)
- [Producing Paradise: ADHD-friendly Notion dashboard](https://www.producingparadise.com/articles/tools/how-to-create-an-adhd-friendly-task-dashboard-in-notion)
- [Todoist: Avoid the Urgency Trap](https://www.todoist.com/productivity-methods/eisenhower-matrix)
- [MakeUseOf: 6 Apps for Eisenhower Matrix](https://www.makeuseof.com/apps-use-eisenhower-matrix-organizing-tasks/)
