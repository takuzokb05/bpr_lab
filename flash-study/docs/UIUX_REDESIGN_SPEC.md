# flash-study UI/UX リデザイン仕様書（本実装版）

> 対象: `prototype/index.html`（単一HTML SPA）/ 想定読者: 日本の公務員（介護保険・行政・税務の学習）
> 本書は実装者がこれ単独で本実装に着手できる粒度で記述する。行番号はリデザイン前 `prototype/index.html`（全1105行）を指す。
> 主軸方向: **「静明朝（Quiet Editorial, Systematized）」** をベースに、**「明窓 / 静書」のリーダー再設計・記憶永続化・クイズ信頼ガード**を全面取り込み。

---

## 0. 設計のスタンス（なぜこの統合か）

3案（静明朝 / 明窓 / 静書）はいずれも「温かいダーク＋アンバー＋明朝×ゴシックの方向性は壊さない」「ORP固定・キーボード・記憶永続化・クイズ信頼が4本柱」という点で一致している。差は強調点だけ。よって本書は **連続性を主軸（静明朝）に据えつつ、明窓/静書が強く打ち出す「核体験の再設計（ORP・記憶・クイズ信頼）」を blocker 解消として全面採用** する。全面リデザインはしない。理由:

- 現状の視覚方向は脱AI-slopできており（青グラデ系の凡庸さから一歩抜けている）、公務員の静かな学習に合致。**捨てるのは「美的体系の欠如」と「核体験の科学的破綻」であって「見た目の方向」ではない。**
- 不変項（9フィールドJSON背骨 / callLLM単一窓口 / 既存機能 / 単一HTML）を壊さず、トークン・操作性・記憶レイヤを「上に薄く載せる」ことで本実装品質に到達できる。

診断の **blocker（4件）** = ①ORP破綻 ②キーボード皆無 ③SPA遷移のフォーカス/ライブリージョン皆無 ④記憶が一切残らない（使い捨てビューア） は、本書ですべて正面解消する。**high** も全て設計に織り込む。

---

## 1. デザイン原則（5）

1. **静けさは引き算でつくる（Quiet by subtraction）**
   少色・余白・明朝の没入面を守る。装飾を足すのではなく、意味のないアンバーの兼務・中途半端な余白・OS依存の絵文字を引く。「押せるアンバー」は画面に1〜2点だけ。

2. **明朝は没入、ゴシックは黒子（Roles, not vibes）**
   明朝（Shippori Mincho）= フラッシュ本文・カウントダウン・大スコア・リードの「没入面」専用。ゴシック（Zen Kaku Gothic New）= それ以外すべての機能UI。役割境界を体系ルールに昇格させ、場当たりの serif 混入を排除する。

3. **一点を凝視させる（One fixed point）**
   RSVPの価値はサッカード（眼球運動）抑制。焦点文字(ORP)を**画面上の絶対固定点**にピン留めし、全チャンクで固視点が動かないことを最優先の不変条件にする。視線ガイドも焦点に追従させる。

4. **能動的想起が本命（Recall over speed）**
   フラッシュは入口のフック。学習の記憶を永続化し、誤答だけを再フラッシュ→再出題するループを回す。**もっともらしい誤クイズ**を生成→即保存させず、レビュー1画面と本文根拠で信頼を担保する（CLAUDE.md 最大リスクへの正面対応）。

5. **どの操作系でも止められる・現在地が分かる（Operable & locatable）**
   キーボード（Space/矢印/Esc）・スワイプ・可視フォーカス・画面遷移後のフォーカス移動・ライブリージョンを全画面に通す。OS素のダイアログは使わず、破壊的操作はUndo可能にする。WCAG 2.1 AA を満たす。

---

## 2. デザイントークン（:root に追加。全CSSをこれへ機械置換）

> 現状 `:root`（L11-17）は **色9個 + フォント2個のみ**。以下を追加し、生のリテラル（font-size 約65箇所・border-radius 7段階・transition 4種・影の直値）を全て変数参照に置換する。色は既存パレットを温存し「階層化」と「muted明度UP」だけ行う。

### 2.1 色（既存温存 + 2点改修 + アクセント階層化）

```css
:root{
  /* 面（既存維持） */
  --bg:#171310; --bg2:#1f1a15; --surface:#241e18; --line:#3a3128;
  --text:#f1e9dd;

  /* muted: 本文級で4.5:1割れ(#b8ad9e≒4.0:1)のため明度UP。12px以下用に強muted新設 */
  --muted:#c8bdac;          /* 旧 #b8ad9e。本文・補助テキスト */
  --muted-strong:#cabfae;   /* 12px以下のラベル/カウンタ用 */

  /* アクセント階層化: 塗りのアンバーは「押せる主役CTA」と「焦点文字」だけに限定 */
  --accent:#e0823f;         /* 主役CTA塗り・ORP焦点文字 */
  --accent-600:#eb9152;     /* hover */
  --accent-700:#c96d2e;     /* pressed */
  --accent-weak:#e0823f29;  /* 進捗バー・シーク・選択背景・補助線（≈16%）。旧 --accent-soft 統合 */
  --on-accent:#1a1006;      /* アンバー上の文字（既存の #1a1006 を変数化） */

  /* 状態色（既存維持。正誤は色＋✓/✗の二重符号化を必須に） */
  --good:#6fb98f; --bad:#d9686a;
  --good-line:#3c5546; --bad-line:#6b3b3c;

  --serif:'Shippori Mincho',"Hiragino Mincho ProN","Yu Mincho",serif;
  --sans:'Zen Kaku Gothic New',"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;
}
```

### 2.2 タイポスケール（6段の整数。0.5px刻み撤廃。rem基盤）

`html{font-size:100%}` を入れ rem 基盤化（OS文字拡大/ズームに追従、WCAG 1.4.4）。表示用（フラッシュ・リード・スコア）は clamp で別管理。

```css
:root{
  --fs-xs:0.6875rem;  /* 11px: ピル・ティック */
  --fs-sm:0.75rem;    /* 12px: ラベル・補助。これを最小本文の床にする */
  --fs-base:0.8125rem;/* 13px: メタ・サブ本文 */
  --fs-md:0.875rem;   /* 14px: 本文・ボタン小・チェック本文 */
  --fs-lg:0.9375rem;  /* 15px: CTA・カード見出し */
  --fs-xl:1.125rem;   /* 18px: 設問・セクション見出し */
  --fw-reg:400; --fw-med:500; --fw-bold:700;  /* 3段に圧縮。800/900は表示面のみ */
  --ls-label:.08em;   /* ラベル系 */
  --ls-head:.02em;    /* 見出し系 */
}
```

旧→新 対応（丸め規約）: 11→xs / 11.5→sm / 12→sm / 12.5→base / 13→base / 13.5→base / 14→md / 14.5→md / 15→lg / 15.5→lg / 16.5→lg(PCのカードはmd→lg) / 17/18→xl。**13.5/14.5/16.5 等の小数は全廃。** 表示用 clamp は §2.6 に別記。

### 2.3 余白（4pxグリッド。中途半端値を一掃）

```css
:root{
  --sp-1:4px; --sp-2:8px; --sp-3:12px; --sp-4:16px; --sp-5:24px; --sp-6:32px;
}
```

規約: 面コンポーネント（`.card`/`.box2`/`.speedwrap`/`.opt`）の内側 padding は **`--sp-4`（16px）に統一**、横をやや広げたい場合のみ `16px 20px` の2値だけ許可。フォーム縦リズムは `.label` を `margin:var(--sp-5) 0 var(--sp-2)`、ブロック間 `--sp-3`。6/9/10/13/15/17/18/22px は撲滅。

### 2.4 角丸（7段階→4段に集約）

```css
:root{
  --r-sm:9px;       /* chk box・seg内ボタン・summary（旧 7/9 を統合） */
  --r-md:13px;      /* btn・inp・box2・opt・rctrl（旧 12/13/14 を統合） */
  --r-lg:16px;      /* card・speedwrap */
  --r-pill:999px;   /* pill・range track */
}
```

### 2.5 影（elevation 3段。枠線のっぺりを解消）

```css
:root{
  --shadow-1:0 1px 2px rgba(0,0,0,.30);                 /* カード/box2/opt 常設・ごく弱く */
  --shadow-2:0 4px 12px rgba(0,0,0,.35);                /* hover時の浮き */
  --shadow-cta:0 4px 14px rgba(224,130,63,.18);         /* CTA着色影。旧 .26 を弱める */
  --shadow-inset:inset 0 1px 0 rgba(255,255,255,.03);   /* 面の上ハイライト（ダークの質感） */
}
```

### 2.6 モーション（2-3段に集約 + 表示用clamp）

```css
:root{
  --t-fast:.15s;  /* hover/press/トグル */
  --t-base:.2s;   /* 一般 */
  --t-slow:.3s;   /* 画面fade */
  /* 表示用フォントサイズ（rem化しない没入面。clampはそのまま維持・上限のみ調整） */
  --flash-fs:clamp(34px,11vw,56px);       /* スマホ */
  --flash-fs-pc:clamp(56px,8.5vw,108px);  /* PC ≥880px */
  --lead-fs:clamp(24px,6.5vw,32px);
  --score-fs:64px;
}
```

`.12/.18/.4s` の散在は `--t-fast/base/slow` に置換。**`@media (prefers-reduced-motion:reduce)` で fade/pop/spin を全無効化**（§7）。

---

## 3. コンポーネント仕様

### 3.0 グローバル（最優先で追加）

```css
html{font-size:100%;}
/* キーボード可視フォーカス（WCAG 2.4.7）。マウス時は抑制 */
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:inherit;}
:focus:not(:focus-visible){outline:none;}
/* 視覚的に隠すがSRには読ませる（正誤の二重符号化等） */
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;
  clip:rect(0 0 0 0);white-space:nowrap;border:0;}
```

`.inp:focus{outline:none}`（L65）・`textarea:focus{outline:none}`（L93）は border-color変化を残しつつ `:focus-visible` で可視リングを補う（`box-shadow:0 0 0 2px var(--accent)` でも可）。**`outline:none` を裸で残さない。**

### 3.1 ボタン `.btn`（体系維持 + hover/階層追加）

- 既存規約維持: `.block`（横いっぱい主役CTA）/`.sm`（44px補助）/`.icon`（44px正方）/`.ghost`/`.danger`。高さ `.btn 48px / .sm/.icon 44px`。
- 変更: `background:var(--accent)` → hover `var(--accent-600)`、`:active` `var(--accent-700)`。`box-shadow` を `var(--shadow-cta)` に。`color:var(--on-accent)`。`:disabled{opacity:.45}` は維持。
- **塗りのアンバーは `.btn`（=主役CTA）専用。** 進捗・シーク・アイコン文字・ピルは `--accent-weak`/`--muted` に降格。

### 3.2 カード `.card`

- `border-radius:var(--r-lg)`、`padding:var(--sp-4)`、`box-shadow:var(--shadow-1)`、hover で `--shadow-2`。
- `.card.sel` はグラデ（L39）をやめ `border-color:var(--accent); background:var(--accent-weak)` に統一（選択メタファを全画面で一本化）。
- アイコン `.ic` は明朝のまま色は `--accent` 維持可（焦点と並立する装飾の例外）。ただし量を増やさない。
- **新: 学習状態 pill**（§記憶レイヤ）。`未学習`（muted枠）/ `N問`（既存 .uns 相当）/ `3/3・3日前`（.rdy相当 good）/ `復習`（accent-weak背景）。

### 3.3 フォルダツリー `.fold`

- `summary` に `min-height:44px`（タップ領域、WCAG 2.5.8）。`padding:var(--sp-3) var(--sp-2)`。
- `[open]` の **ハードコード（L592）を撤廃**。開閉状態を `openFolders`（`Set<path>`）に保持し、`renderTree` 描画時に復元（部分更新でも details が勝手に開かない）。
- 三角 `.tw` の色は `--muted`。アンバーにしない。
- フォルダ見出し `b` クリックで rename（`prompt` ではなくインライン input か小モーダル）→ 配下 deck の `category` を `joinCat` で一括更新。

### 3.4 入力 `.inp` / `textarea`

- `border-radius:var(--r-md)`、`font-size:var(--fs-md)`、`padding:var(--sp-3) var(--sp-4)`。
- focus 可視リングは §3.0 準拠。`autocomplete="off"` 維持（APIキー欄）。
- **BYOKキー欄**: 復元時はマスク表示（先頭4 + `●●●` + 末尾4）。フル値はトグル（目アイコン）で一時表示のみ（共有PC対策）。

### 3.5 セグメント `.seg` / チェック `.chk` / ピル `.pill`（状態表現を統一）

- 選択メタファを **「accent塗り」に統一**（`.seg .on` 既存 + `.chk.on` 既存はOK。`.card.sel` を §3.2 で塗りに寄せて全画面一致）。
- `.seg button` に `min-height:44px`、非選択に hover: `color:var(--text); background:rgba(255,255,255,.03)`（PCでクリック可能性を可視化）。
- `.chk .box` の `font-weight:900`（L102）は表示面例外として許容、または 700 に。`border-radius:var(--r-sm)`。
- ピルは枠依存（`.rdy`/`.uns`）にアイコンを併記し色のみ依存を回避（§6）。

### 3.6 トースト（新規・Undo の器）

```css
.toast{position:fixed;left:50%;bottom:calc(20px + env(safe-area-inset-bottom));
  transform:translateX(-50%);max-width:520px;width:calc(100% - 40px);
  background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);
  box-shadow:var(--shadow-2);padding:var(--sp-3) var(--sp-4);display:flex;
  align-items:center;gap:var(--sp-3);font-size:var(--fs-md);z-index:50;
  animation:toastin var(--t-slow) ease both;}
.toast .act{margin-left:auto;color:var(--accent);background:none;border:none;
  font-weight:var(--fw-bold);cursor:pointer;min-height:44px;padding:0 var(--sp-2);}
@keyframes toastin{from{opacity:0;transform:translate(-50%,8px);}to{opacity:1;transform:translateX(-50%);}}
```

`role="status" aria-live="polite"`。削除のUndo・「1件読み込みました」等に使う。reduced-motion でアニメ無効。

### 3.7 モーダル（新規・native confirm/alert の置換）

```css
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;
  align-items:center;justify-content:center;padding:20px;z-index:60;}
.modal{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);
  box-shadow:var(--shadow-2);max-width:420px;width:100%;padding:var(--sp-5);}
.modal .mt{font-weight:var(--fw-bold);font-size:var(--fs-lg);margin-bottom:var(--sp-2);}
.modal .mp{color:var(--muted);font-size:var(--fs-md);line-height:1.7;margin-bottom:var(--sp-4);}
.modal .row{display:flex;gap:var(--sp-3);}
```

`role="dialog" aria-modal="true" aria-labelledby`。**破壊的操作はデフォルトフォーカスを安全側（キャンセル）に。** 開く前のフォーカス要素を記憶し、閉じたら戻す。Esc で閉じる。文言に「この操作は取り消せません」を明示。

### 3.8 ローダー（中断可能 + 世界観）

- `.loading` に **常時表示の「中断」ボタン**（`.btn.ghost`）を追加。`AbortController` を `callLLM→postJSON` に通し `fetch({signal})` で実中断。
- 複数デッキ生成は「3 / 12 完了 ・ 残り推定◯秒」 + 「ここまで保存して中断」。
- 汎用 `.spin`（L117）は維持しつつ、reduced-motion で静止 border + 「処理中…」テキストに。可能なら「中央に明朝一文字が淡く脈打つ」演出に差し替え（slop除去・任意）。

---

## 4. 画面別レッドライン（before → after）

> 凡例: 【B】= blocker解消 / 【H】= high解消 / 【M/L】= medium/low

### 4.1 ライブラリ（library, L612-630）

**before**: lead「デッキを選んで／パッと読む」+ sub説明 + `[＋教材から新規][⤓読込][⚙]` + `renderTree()`（全 details open固定）。学習状態の表示なし。検索/ソートなし。`<details>` は常に open。

**after**:
- 【H】**先頭に学習サマリ帯**（1行）: `今日の復習 N件 ・ 連続 D日 ・ 直近正答率 X%` + `[復習をはじめる]` CTA。`flashstudy.progress` から集計（§記憶レイヤ）。即断即決型に数字3つで。
- 【H】**検索1本**（title/category/source 部分一致・即時フィルタ）+ **ソート**（最近学習 / 復習が近い / 名前順）。
- 【H】**details の open 固定撤廃**（L592）。`openFolders:Set<path>` で保持・復元。件数の多い大項目は既定で閉じる。
- 【B/H】カード pill を学習状態に拡張（§3.2）。
- 【M】サンプルの大項目を実分野（行政 / 税務）に変え、サンプル識別はカードの「見本」バッジで（フォルダIA汚染回避）。
- 【M】**初回オンボーディング**（localStorageに既存判定が無い時のみ）: 3ステップ図（貼る→読む→解く）+「サンプルで体験」→ s1 リーダー直行。完了後フラグ保存。
- 【L】空状態の文言をボタン文言と完全一致（§5）。アクセントはサマリ帯CTAのみ、三角/pillは muted/weak へ降格。

### 4.2 作成（create / make, L737-842）

**before**: PDFボタン + textarea + 分割seg + 大項目input + フラッシュ扱いseg + クイズ生成chk + 「作成する」。生成は `loading()` で中断不能。複数生成は `confirm`（L813）。失敗は一般化メッセージ（L837）。

**after**:
- 【B/H】`loading()` に **「中断」ボタン + AbortController 実中断**。`postJSON` に `AbortSignal.timeout(60000)` を付与（L249 に timeout 無し）。
- 【H】複数デッキ生成は「3 / 12 完了 ・ 残り推定◯秒」進捗 + 途中保存。**最初の1件で auth エラーなら残りを即中止**（無駄な課金防止、L820 ループ）。
- 【H】`confirm`（L813）を `.modal` に置換。AI呼び出し回数と実費目安を落ち着いた日本語で。
- 【L】分割seg に結果予告の補助1行（§5）。原文モード&生成OFF時（`useAI=false`, L795/802）はセグメントを淡色化 + 「AIを使う設定で有効」注記。本文長から「約◯個に分割予定」プレビュー。
- 【H】生成失敗を `e.code` 別に出し分け（auth/model/通信）。auth時はバナーに「⚙設定を開く」リンク（§5・L835 catch の握り潰しを是正）。
- 【M】単一デッキでもタイトルだけ短文生成（`categorize` 同様 callLLM 1コール、失敗時のみ頭18字フォールバック・助詞始まり回避。L831-832）。
- 【B】生成成功後に **クイズレビュー1画面**を挟む（§4.4 新規）。

### 4.3 リーダー（reader, L993-1056）★最重要改修

**before**: `renderFlash`（焦点=幅35%相対, L556）+ `.flash{text-align:center}`（L141）→ 焦点が毎フレーム左右に踊る。視線ガイドは固定px（L140, font追従せず）。操作はボタン + `.stage.onclick`（L1020）のみ。keydown/swipe/wakeLock 皆無。速度は文字数線形（L554）。pos「語 n/N」（L1035, チャンク実態と乖離）。

**after**:
- 【B】**ORPを画面絶対固定点にピン留め**。`.flash` を `pre / focus / post` の3部構成にし、focus span の水平中心をステージ中央に固定（focus より前の `pre` 幅ぶん `transform:translateX` で左へずらす、または focus を絶対配置アンカーにして pre 右寄せ/post 左寄せの3カラム）。**全チャンクで固視点が1点に定まる**。focus位置は文節長で可変（1字=先頭 / 2-5字=2文字目 / 長文=中央寄り）。`renderFlash`（L556 の35%固定）を作り直す。
  - 構造例: `<span class="pre">…</span><span class="focus">字</span><span class="post">…</span>`、`.flash{display:inline-block;white-space:nowrap}`、`.focus{color:var(--accent)}`、ステージは焦点中心が中央に来るよう配置。
- 【H】**視線ガイドを焦点に追従**。固定px上下2本（L140）をやめ、focus 直下の細い三角マーカー1個（em/ch基準）に集約。PC 108px でもズレない。
- 【B】**キーボード操作**: `startReading` で `document` に名前付き `keydown` を登録（`stop()`/画面遷移で `removeEventListener`、多重登録防止）。`Space`=togglePlay / `←→`=navSentence(∓1) / `↑↓`=速度±1 / `Home`=restartReading / `Esc`=退出(deckDetail)。`e.preventDefault()` でスクロール抑止。textarea/input フォーカス中は無効化。
- 【H】`.stage` を `tabindex="0" role="button" aria-label="タップまたはSpaceで一時停止・再開"`、`cursor:pointer`。**横スワイプ**（touchstart/end, 閾値>40px）で文移動・タップ（移動<10px）で停止。`button/input/summary` は除外。
- 【H】一時停止中は `.flash` を僅かに減光 + 中央に控えめオーバーレイ「❙❙ タップ/Spaceで再開」（状態を本文側に反映）。
- 【M】**速度モデルを認知律速へ**。`delayFor`（L554, 文字数線形）を漢字含有率重み（漢字1字≒ひらがな1.5字）+ 数値/英字チャンク下駄 + 句末保持 + 停留に床（220ms）。`buildChunks` でチャンクに種別タグ（熟語/助詞列/数値/句末）を付与し `delayFor` が参照（チャンカーのロジック自体は不変、タグ付与のみ追加）。
- 【M】カウントダウン整流: 初フレーム停留を `delayFor(chunks[0])` ぶん確保、`idx++` を `tick` に一本化（L1038/1042 の二重 idx++ 是正）。間隔を速度に緩く連動。Space/タップで skip 可。
- 【M/L】`.flash` 1行固定（`white-space:nowrap`）+ 焦点だけ微小 opacity フェード（L1031 の毎フレーム fade をやめレイアウトを動かさない＝縦ジッター/疲労抑制）。
- 【H】再生中 `navigator.wakeLock?.request('screen')` を try/catch で取得、停止/離脱/visibilitychange で release・再取得（非対応は握りつぶし）。
- 【L】pos「語 n/N」→「`${idx+1}/${n}`（コマ）」（チャンク実態に整合）。シークバーに sentStarts の文境界ティック（datalist）+ 残り推定秒（ΣdelayFor）。
- 【B/H】`role` 付き + `aria-live="polite"` でステージ更新を任意で読み上げ。画面遷移後に主要操作（pp ボタン）へ `focus({preventScroll:true})`。hint を2行・平易化（「シーク」→「好きな位置へ」、PC時「Space で一時停止」明記、初回のみ）。
- 【M】**「全文を静的に読む」トグル**を追加（RSVPを任意化・読字/認知配慮）。reduced-motion 時は自動進行オフ（手動送り既定）。
- 【M】読了位置 `lastReadIdx` を `progress` に保存→ deckDetail に「続きから（コマ12/40）」。

### 4.4 クイズ生成レビュー（新規画面）+ クイズ（quiz, L1073-1088）

**before（クイズ）**: 選択肢タップで進む。正誤は色クラスのみ（L1083）。誤答は「おしい」固定（L1085）。feed/next は opts の下に追加描画（モバイルで画面外）。進捗はテキストのみ。生成→即保存（検証ゼロ、`a` 範囲外サイレント0クランプ L320）。

**after**:
- 【B】**クイズ生成レビュー1画面（新規）**: 生成直後に4択+正解+解説を一覧し、1問ずつ「採用/除外」（チェック/スワイプ）。`normalizeQuiz` で空・重複選択肢を drop（現状 while で空補完=無意味選択肢）。`a` 範囲外は黙ってクランプ（L320）せず**可視警告**して除外候補に。
- 【B】**callLLM 自己検証パス**: 別 prompt で各設問を「本文だけで正解が一意に定まるか / 他選択肢は明確に誤りか」をバッチ1回で判定し NG を除外（サブスク二重課金回避でバッチ1回・コストは生成画面で「検証に約1回 追加」明示）。
- 【H】各問に source 由来の**根拠スニペット**を別フィールドで保持し、クイズ画面で「本文の根拠」タップ展開（NotebookLM的引用で誤り抑止）。※背骨9フィールドは不変→根拠は in-memory/別レイヤで保持。
- 【M】誤答コピー「おしい」固定（L1085）を中立な「**正解はこちら**」+ 正しい選択肢の要点提示に（全く違う選択肢に「惜しい」は事実誤認）。
- 【H】正誤を色だけでなく **✓/✗アイコン + `.sr-only` テキスト**で二重符号化（WCAG 1.4.1）。`role="alert"` で読み上げ。
- 【M】解答後 `feed`/`next` へ `scrollIntoView({block:'nearest'})`（モバイル画面外回避）。`qcount` 下に進捗バー（解答済み/総数）。PC で数字キー 1-4 選択。回答後の選択肢は `disabled`/`aria-disabled`。
- 【B】**誤答 index を配列で保持**し結果画面へ受け渡し（能動的想起ループの素材）。

### 4.5 結果（result, L1089-1098）

**before**: score表示 + 2段階メッセージ（満点/.5以上/未満, L1090）+ 「もう一度学習（全文）/ライブラリへ」の2ボタン。スコアを**保存しない**（使い捨て）。

**after**:
- 【B】**「間違えた◯問だけ復習」ボタンを最優先で追加** → 該当設問の根拠文節だけ再フラッシュ → 誤答のみ再出題（プロダクト原則=能動的想起ループ）。
- 【B】score / lastStudiedAt / 問題別誤答を `flashstudy.progress` に保存。Leitner風の簡易 due（誤答→翌日 / 正答→3日後）で次回「今日の復習」に反映。
- 【L】達成段階を**満点 / 8割 / 5割 / それ未満の4段**に細分しメッセージ温度を実スコアに整合。低スコア時は外した論点を1-2件名指し。
- 【M】「デッキへ戻る」を追加（戻る導線補完）。`role="status" aria-live="polite"` で score 読み上げ。score の明朝大数字は没入要素として維持。

### 4.6 設定（settings, L633-722）+ 読込（importMenu, L940-976）

**before**: 既定スピード + BYOK（provider/key/test）+ 「未分類をAIで分類」+ サンプル復元。キー復元時 `apikey.value=...`（平文露見, L695）。「アーティファクト内ではキー無し動作」露出（L698）。「デッキ整理」「職場モード」等の用語揺れ。ヘッダ「Phase 1」。

**after**:
- 【M】BYOKキー欄をマスク表示（§3.4）。文言を本実装向けに「キー未設定時は動作しません。⚙でキーを登録してください」に統一（デモ専用キーレス代理の内部事情露出を整理）。
- 【L/M】用語統一: 「デッキ整理」→「**フォルダの自動整理**」、画面露出語「デッキ」→「**教材**」（背骨JSONキー `deck`/`category` は不変、§5）。「カテゴリ/フォルダ/項目/分類」→「フォルダ（大/中/小）」+ 動詞「分類する」。
- 【H】ヘッダ「**Phase 1**」（L6 title / L225 h1）を全削除し正式名称に統一。設定隅に控えめな `v1.0`。
- 【H】削除した教材の「ゴミ箱から復元」（`flashstudy.trash` 退避から）。全教材/フォルダ単位の**一括書き出し**（import は配列対応済み L969 で往復が閉じる）。
- 【M】読込: 存在しない概念「**職場モード**」（L908/946）を撤去し機能説明へ。ボタン「読込」↔ 画面タイトル「教材を読み込む」を一致（§5）。JSON parse 失敗を平易化（§5）。`alert`/`confirm`（L726/916）を `.modal`/`.banner` に統一。
- 【L】880px+ の `#app` padding（L180）に `env(safe-area-inset)` を復活（`padding:max(30px,env(...))...`）。

---

## 5. マイクロコピー改善表（現行→改善）

| 箇所(行) | 現行 | 改善 | 理由 |
|---|---|---|---|
| L6 title / L225 h1 | 「フラッシュ学習 — Phase 1」/「FLASH STUDY · Phase 1」 | 両方「フラッシュ学習」に統一（英字副題は小さく任意） | 開発フェーズ語の露出・製品名の二重定義 |
| L616,610,742,945,1062 ほか | 「デッキ」（UI露出） | 「教材」（学習セット） | 想定読者の語彙にない内部語。JSONキーは不変 |
| L619 / L742 | 「＋ 教材から新規」/ 画面「教材から作成」 | ボタン「教材から作成」↔画面「教材から作成」 | ラベルと遷移先タイトルの不一致 |
| L620 / L945 | 「⤓ 読込」/ 画面「デッキを読み込む」 | ボタン「読み込む」↔画面「教材を読み込む」 | 同上（動詞/名詞の不揃い） |
| L1085 | 「おしい」（誤答固定） | 「正解はこちら」+ 正答の要点 | 全く違う選択肢に「惜しい」は事実誤認・学習信頼に直結 |
| L1035 | 「語 n/N ・ 文 s/S」 | 「n/N（コマ）・ 文 s/S」 | 文字種チャンクは「語」でない（L490 コメントと乖離） |
| L908/946 | 「職場モード」「職場のCopilot等で作った配列」 | 「JSONを貼り付けて取り込めます。社内の生成AI（Copilot等）が出力した問題データもそのまま使えます」 | アプリ内に存在しない概念名 |
| L668/669 | 「デッキ整理」「未分類をAIで分類」 | 「フォルダの自動整理」「未分類の教材を分類する」 | カテゴリ/フォルダ/項目/分類の四つ巴を一本化 |
| L253 | 「API 401 / {生txt}」 | auth: 「APIキーが正しくないようです。⚙設定でキーを確認してください」 | 英語生例外の混在（IT非専門の不安） |
| L250 | 「通信に失敗: {生}」 | 「ネットに接続できませんでした。通信環境をご確認ください」 | 同上 |
| L258/968 | 「応答がJSONではない」「JSONとして読めません({生})」 | 「データの形式が読み取れませんでした。コピー範囲をご確認ください」（生は折りたたみ「詳細」へ） | 同上 |
| L837 | 「生成に失敗しました。本文を短く…」 | e.code別: auth/model/通信で出し分け + 「⚙設定を開く」 | 原因不明で次の一手が立たない |
| L1012 | 「画面タップで一時停止／再開・◀◀▶▶で文単位移動・バーでシーク」 | 「画面タップで一時停止／再開。◀◀▶▶ は文の頭出し、下のバーで好きな位置へ。」（2行・初回のみ） | 情報過多・カタカナ専門語 |
| L1090 | 2段（満点/5割以上/未満） | 4段（満点/8割/5割/未満）+ 低スコアは論点名指し | 段階が粗く半分正解で「あと一歩」は楽観的 |
| L752-754 | 「なるべくまとめる/なるべく分ける/AIにおまかせ」 | 「なるべくまとめる（1〜3個）/細かく分ける（最大12個）/おまかせ（自動）」 | 結果（生成個数）が文言から読めない |
| L610 | 空状態「…『＋ 教材から新規』または『⤓ 読込』で…」 | ボタン文言と完全一致 + 初回は「まず1本読んでみる」 | オンボーディング欠如 |

---

## 6. アクセシビリティ要件（WCAG 2.1 AA・具体）

| WCAG | 要件 | 実装 |
|---|---|---|
| 2.1.1 操作可能 | リーダーをキーボードで全操作 | §4.3 keydown（Space/←→/↑↓/Home/Esc）。`.stage` を tabindex=0 role=button で Enter/Space 起動 |
| 2.4.3 フォーカス順序 | SPA遷移でフォーカスを失わない | 共通遷移関数で `screen.innerHTML` 差し替え後、各画面の見出し（`.dtitle`/`.lead`/`.qhead` に `tabindex="-1"`）へ `focus()` |
| 2.4.7 フォーカス可視 | 全インタラクティブ要素に可視リング | §3.0 グローバル `:focus-visible`。`:focus{outline:none}`（L65,93）の裸残し撤去 |
| 4.1.3 ステータスメッセージ | ローディング/正誤/結果をSRに通知 | ローディング・結果・トーストを `role="status" aria-live="polite"`、クイズ正誤を `role="alert"` |
| 1.1.1 / 4.1.2 名前・役割 | アイコン/絵文字ボタンに名前 | `aria-label`（✕→「リーダーを閉じる」/◀◀→「前の文へ」/送り→「次の文へ」/⚙→「設定」）。装飾絵文字は `<span aria-hidden="true">` |
| 1.4.1 色の使用 | 正誤を色のみで示さない | 正解✓/誤答✗アイコン + `.sr-only`「正解」/「不正解」。pill にもアイコン併記 |
| 1.4.3 コントラスト | 本文4.5:1以上 | `--muted` を #c8bdac へ（各面で実測4.5:1）。解説 `.feed` は `--text` に格上げ。12px以下は `--muted-strong` |
| 1.4.11 非テキスト | UIコンポーネント3:1 | ボーダー依存の状態（pill/seg/chk）を塗り or アイコンで二重符号化 |
| 2.3.3 / 2.2.2 動きの低減 | reduced-motion・自動更新の停止 | §7。fade/pop/spin 無効化、RSVP自動進行を reduce 時は手動送り既定。「全文静的表示」モード |
| 1.4.4 / 1.4.10 拡大・リフロー | 200%拡大・320px幅で破綻しない | rem基盤化（§2.2）。最小本文12px床。400%/320px を実機確認 |
| 2.5.8 ターゲット | 最小24px（AAは44px推奨） | `.seg button`/`.fold>summary` に `min-height:44px`、range thumb 24→28px |

---

## 7. モーション設計

- **トランジション**: `--t-fast(.15s)` hover/press/トグル / `--t-base(.2s)` 一般 / `--t-slow(.3s)` 画面fade。`.12/.18/.4s` の散在を撲滅。
- **画面遷移**: `.screen{animation:fade var(--t-slow) ease both}`（L27 維持）。
- **フラッシュ更新**: 毎フレームの `fade .12s` 再適用（L1031）をやめ、**焦点文字だけの微小 opacity フェード**に。レイアウト（pre/focus/post）は動かさない＝縦ジッター/疲労抑制。
- **カウントダウン**: `pop`（L144）維持・間隔を速度連動・Space/タップで skip 可。reduce 時は省略。
- **ローダー**: `spin`（L118）。reduce 時は静止 border + 「処理中…」テキスト。
- **トースト/モーダル**: §3.6/3.7。reduce 時はフェードのみ（移動なし）。
- **reduced-motion（必須）**:
```css
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;
    transition-duration:.001ms!important;}
}
```
  加えて JS 側で `matchMedia('(prefers-reduced-motion:reduce)').matches` を見て **RSVP自動進行を既定オフ（手動送り）** にし、カウントダウンを省略する。

---

## 8. 不変項を壊さない実装上の注意

1. **9フィールドJSON背骨は不変**: `{id,title,source,flashMode,flashText,quiz[{q,o[4],a,e}],quizStatus,category,createdAt}`。`normalizeDeck`/`toDeckJSON`（L328-351）を変えない。**進捗・誤答・続き位置・根拠スニペット・ゴミ箱は別キー**（`flashstudy.progress` / `flashstudy.trash`）に保持し `toDeckJSON` に**絶対に混ぜない**（`icon`/`desc` と同じ扱い）。
2. **category は「大 / 中 / 小」のパス1本**: `catParts`/`catLevel`/`joinCat`（L562-564）を維持。フォルダ rename も `joinCat` 経由で配下一括更新。
3. **callLLM 単一窓口**: `genQuiz`/`reconstruct`/`categorize`/`planDecks` は `callLLM` 経由のまま。**自己検証パスも `callLLM` 経由のバッチ1回**（サブスク二重課金回避＝CLAUDE.md規約。検証段階のコストは起動前に明示）。BYOKキーはブラウザ内のみ・ログ/コミット禁止。
4. **チャンカーは描画と分離**: `buildChunks`（L491-551, 文字種境界判定）のロジックは触らない。ORP改修は `renderFlash`（L556）の**描画層だけ**作り直す。速度モデル用の種別タグは `buildChunks` 出力に**追加**するのみ（既存の `chunks`/`sentStarts` 形は維持）。
5. **既存機能の全維持**: フォルダ折りたたみツリー / localStorage永続化 / PDF取込（pdf.js）/ 複数デッキ生成（planDecks/buildSections）/ 文字種チャンカー / JSON貼付import（配列対応）/ 安全側フォールバック（1件失敗継続・プラン全滅で単一デッキ）。
6. **単一の自己完結HTML**: SVG・トークン・モーダル・トースト・SW は全てインライン/Blob URL で完結。CDN（fonts/pdf.js）以外の外部依存を増やさない。最小PWA化（任意）は `http(s)` 判定時のみ register、`file://`/アーティファクト環境では握りつぶす。BYOK の CORS のため http 配信前提を維持。
7. **`const screen` の罠**: L486 の `const screen = document.getElementById('screen')` は `window.screen` をシャドウ。本実装で `screenEl` にリネーム（reduced-motion 判定で `window.screen` を踏む前に）。
8. **リスナーのライフサイクル**: keydown/touch/wakeLock は SPA の `innerHTML` 全置換と相性が悪い。**名前付き関数 + `stop()`/遷移時 `removeEventListener`** を厳守（多重登録・リーク防止）。wakeLock は `visibilitychange` で再取得。
9. **タイマー再入**: `countdown`/`tick`（L1037-1056）の単一グローバル `timer` 二重起動に注意。`idx++` を `tick` に一本化し、countdown 中の操作は無効化 or 単一 timer に統合。可能なら start/pause/seek/destroy を持つ reader コントローラに封じる。
10. **XSS**: テンプレートは手動 `esc()`（L559）依存。LLM生成テキスト（クイズ文・解説・根拠・カテゴリ名）を表示する経路が増えるため、補間は必ず `esc()` を通す。属性補間（`data-id`）は uid 生成（L972/987）に依存するので import 時の uid 上書きを維持。

---

## 9. 実装手順（優先度順チェックリスト）

> **Step 1-4 = blocker（最優先）。Step 5-8 = high。Step 9-11 = medium/低。** 各 Step 後に `reviewer`、クイズ関連は `quiz-evaluator` を回す（CLAUDE.md）。

- [ ] **Step 0 / 土台**: トークン3系統（タイポ/余白/角丸/影/モーション）を `:root` に追加。`html{font-size:100%}`。生のリテラル（font-size約65・radius7段・transition4種・影直値）を変数へ機械置換。`:focus-visible` グローバル + `.sr-only`。muted明度UP。`const screen`→`screenEl`。**【トークン/A11y基盤】**
- [ ] **Step 1 / 【B】ORP固定**: `renderFlash`（L556）を pre/focus/post 3構成へ作り直し、焦点中心=ステージ中央に固定。視線ガイドを焦点追従の三角1個に。`.flash` 1行固定 + 焦点のみ微小フェード。reader起動前に `document.fonts.load` await（書体揃え）。**最も検証コストが高い。スマホ/PC/フォント未ロードで固視点ズレを実機確認。**
- [ ] **Step 2 / 【B】キーボード+フォーカス+ライブリージョン**: reader に keydown（Space/←→/↑↓/Home/Esc, removeで多重防止）。`.stage` tabindex/role/aria。SPA遷移共通関数で見出しへ focus()。loading/結果/正誤に role=status/alert。
- [ ] **Step 3 / 【B】記憶の永続化レイヤ**: `flashstudy.progress` 新設（lastScore/bestScore/attempts/lastStudiedAt/wrongIdx/lastReadIdx/due）。result()で保存。誤答 index 保持→「間違えた問だけ復習→誤答のみ再出題」。library 先頭にサマリ帯。カード pill 拡張。deck削除/import時に progress 整合（孤児掃除）。
- [ ] **Step 4 / 【B】クイズ信頼ガード**: 生成直後のレビュー1画面（採用/除外）。callLLM 自己検証パス（バッチ1回）。本文根拠スニペット表示。`normalizeQuiz` で空/重複drop・`a`範囲外を可視警告（L320 サイレントクランプ是正）。
- [ ] **Step 5 / 【H】中断可能性 + エラー**: `loading()` に中断ボタン + AbortController 実中断。`postJSON` に timeout。複数生成の進捗+途中保存+auth時即中止。e.code別エラー文言 + 「⚙設定を開く」導線。
- [ ] **Step 6 / 【H】ダイアログ統一 + Undo**: native confirm/alert（L726/813/898/916/989）を `.modal`/`.toast` に置換。削除は Undo トースト + `flashstudy.trash` 退避。破壊的操作は安全側デフォルトフォーカス。
- [ ] **Step 7 / 【H】コントラスト + 二重符号化**: 正誤を ✓/✗ + sr-only。pill にアイコン。解説 `.feed` を `--text` に。`.card.sel` をグラデ→塗りに統一。
- [ ] **Step 8 / 【H】reduced-motion + wakeLock + 静的表示**: `@media (prefers-reduced-motion:reduce)` + JS判定で自動進行オフ。再生中 wakeLock。「全文を静的に読む」トグル。
- [ ] **Step 9 / 【M】速度モデル + カウントダウン整流**: delayFor を認知律速へ（漢字含有率/数値/句末/床220ms）。buildChunks に種別タグ追加。idx++ を tick に一本化。シークに文境界ティック+残り推定秒。
- [ ] **Step 10 / 【M】コピー/IA一括**: 用語統一（デッキ→教材/フォルダ一本化）。Phase 1 削除。ラベル↔タイトル一致。職場モード撤去。誤答「おしい」中立化。結果4段。BYOKマスク。検索+ソート+details open撤廃+フォルダrename。
- [ ] **Step 11 / 【L】仕上げ**: 絵文字→インラインSVG（line icon）。spinローダー差し替え。初回オンボーディング。タップ領域44px（seg/summary/thumb）。880px+ safe-area復活。中間BP 640px（カードグリッド2列）。サンプル大項目を実分野+見本バッジ。任意で最小PWA化（theme-color/インラインmanifest/Blob URL SW）。

---

## 10. 却下した案と理由

- **【全面リデザイン（方向ごと刷新）】却下**: 現状の温かいダーク+明朝×ゴシックは脱AI-slopできており用途適合。問題は「美的体系の欠如」と「核体験の破綻」であって見た目の方向ではない。連続性を保ったまま体系化する方が低リスクで本実装品質に届く（→ 静明朝を主軸に採用）。
- **【フレームワーク（React/Vue等）導入】却下**: 不変項「単一の自己完結HTML（ビルド無し）」に反する。代わりに「シェルは一度構築・可変部のみ部分更新 + 自動エスケープ html`` タグ + data-action 委譲」の薄い抽象化に留める（アーキ負債は本実装の足場整備として段階対応）。
- **【ORP の対症療法（35%相対のまま色だけ強調）】却下**: 焦点が動けば固視点として機能せずRSVP最大の利点（サッカード抑制）を自壊。blocker。描画層の根本作り直し（pre/focus/post 固定）が必須。
- **【native confirm/alert を文言改善だけで温存】却下**: ダーク明朝トーンから浮き、モバイルの「繰り返し確認」抑制で削除確認が出ず誤削除/操作不能のリスク。アプリ内モーダルへ全面置換。
- **【進捗を背骨JSONに追加（lastScore等を9フィールドに混ぜる）】却下**: エクスポート不変項（正準9フィールド）を破壊し、`icon`/`desc` を除外している原則と矛盾。別キー `flashstudy.progress` で完全分離（Phase 3 IndexedDB 移行時もアクセサ1本で局所差し替え可能に）。
- **【クイズ自己検証を生成のたびにAPI直叩き】却下**: CLAUDE.md「サブスク中の API キー直叩き=二重課金」禁止に抵触し、生成1件ごとの追加呼び出しはコスト/レイテンシも悪化。**バッチ1回**に集約し、コストを生成画面で明示。
- **【RSVP速度モデルを据え置き（文字数線形のまま）】保留→Step 9へ**: blocker/high ではないが「速いのに頭に入る」体感に直結。床220ms と既存スケール整合を取りつつ段階導入（急な体感変化を避ける）。
- **【諮問機関的な多エージェント・クイズ生成の作り込み】却下**: 本書の範囲（UI/UX）外であり、まずは単一 callLLM + レビュー画面 + 自己検証で「AIを信じすぎない」導線を最小実装する。多段化は効果実測後に検討。
