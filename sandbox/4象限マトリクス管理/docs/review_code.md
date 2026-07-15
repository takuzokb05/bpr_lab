# コードレビュー & Why深堀り

対象: `タスク管理.html` (1292行、単一ファイルSPA / v6)
レビュー観点: 設計意図の読み解き、リスク分類、単一HTML起因の課題、テスト戦略、後方互換ポリシー

---

## 総評

「消す」と「終わる」を分離した概念（status: active / completed、削除は5秒Undoトースト）は良設計。マイグレーション専用関数（`migrateLegacyIfNeeded` 608-637）、`safeParse`（529-531）、`baseTask` による正規化（591-606）など、データ堅牢性への配慮が一貫している。

一方で、**「1文字入力するたびに全タスクJSON.stringify + renderAll」という課金構造**（767-773, 844-849, 834, 1020）が最大の潜在的リスク。タスクが数十件を超えると体感遅延が発生する可能性があり、アクティビティログも入力のたびに `updated` で埋まる副作用を生む。

D&Dの `pointercancel`／イベント解除は比較的丁寧に実装されているが、`moveTask` 後の `cleanupDrag` 未呼び出し（1171行）は隠れバグ源として注視すべき。

---

## 設計の読み解き（Why）

### 1. なぜ `normalZone` と `zone` を分離？

**箇所**: 598行（baseTask）、1034行（completeTask）、1048行（reopenTask）、1098-1099行（moveTask）、1208-1210行（enterSurvival）、1221-1222行（exitSurvival）

**意図**: Survivalモード遷移や完了→復元時に「元の象限」へ戻すための座標記憶。`zone` は現在の表示位置（q1〜q4 / survival-picker / slot-must / slot-should）、`normalZone` は "非Survival時のデフォルト位置" という役割分担。

```js
// 1208-1210 enterSurvival
if (NORMAL_ZONES.includes(task.zone)) task.normalZone = task.zone;
task.zone = 'survival-picker';
// 1222 exitSurvival
task.zone = task.normalZone && NORMAL_ZONES.includes(task.normalZone) ? task.normalZone : 'q4';
```

**確度**: high。コメントはないが、enter/exitの対称性と `reopenTask`（1048）・`completeTask`（1034）の両方で一貫して使われている。

**懸念**: Survival中に `moveTask` で slot-must / slot-should に振り分けた場合、1099行 `if (NORMAL_ZONES.includes(targetZone)) task.normalZone = targetZone;` により `normalZone` は**更新されない**ため、ABORTするとSurvival前のq1〜q4に戻る。これは意図通りだが、ユーザーがSurvival中に「この仕事はq1だ」と気づいて振り直したい導線は現状ない。

---

### 2. なぜ `activityLog` を30件でスライスするか（586行）

**意図**: 履歴無限成長による localStorage 肥大と、`createHistoryNode`（702-752）のDOM生成コスト抑制。`unshift` で先頭挿入 → `slice(0, 30)` で末尾切り捨てという単純なリングバッファ代替。

**確度**: high。

**懸念**: **30件はすぐ埋まる**。なぜなら `title` 入力ごとに `logEvent(task, 'updated')` が走り（769行）、「Foo」と3文字打てば3件消費する。ユーザーが意図的に残したい `moved`・`due_updated`・`completed` などの**意味のある履歴が、テキスト編集ノイズで押し流される**。

**対策案**: `updated`・`note_updated` はデバウンスするか、そもそもログに積まない。あるいは `type: updated` は最新1件のみ残す圧縮を入れる。

---

### 3. なぜ `pointerdown` の `stopPropagation` が散らばっているか（774, 828, 843行）

**箇所**: `title.addEventListener('pointerdown', e => e.stopPropagation());`（774）、`dueInput`（828）、`noteInput`（843）

**意図**: カード全体が `startDrag`（866行）で pointerdown を拾ってD&Dを開始するため、子要素のインタラクティブ要素（textarea / input）で操作中に D&D が始まらないよう、個別にイベント伝播を止めている。

**確度**: high。`startDrag` 内にも `if (interactive) return;`（1107-1108）というガードがあるが、念のため二重に防御している形。

**懸念**: `completeBtn` / `detailBtn` / `deleteBtn` には `stopPropagation` が `click` 時にのみ付与されている（795, 803, 811）。`click` は D&D 判定より後に発火するため問題にはならないが、コード全体のイベント伝播ポリシーが「一部は子で止める／一部は親で弾く」と統一されておらず、将来の保守で混乱を呼ぶ。

---

### 4. なぜ legacy migration が必要か（608-637行）

**意図**: v5 のキー（`neuro_matrix_v5_data`、`neuro_matrix_v5_state`）に `text` フィールドだったものを、v6 の `title` / `activityLog` 付き構造へ一度だけ変換する。`existing` が v6 キーに既にあれば何もしない（610行）ので冪等。

**確度**: high。

**懸念**:
- 612行: `legacyDataJson` がパース失敗（壊れたJSON）だと `safeParse` で `[]` フォールバック → 結果として空の `tasks` が v6 キーに保存される（636行 `saveAll()`）。**v5のデータは残るが v6側は空扱い**。以後 `existing` が作られて再マイグレートは走らない。**ユーザーの全タスクが消えたように見える**データ喪失リスク。
- 614行: `if (!legacyDataJson) return;` の後、`legacyStateJson` の空きは safeParse で吸収されているので OK。

**対策案**: 616行で `safeParse` の fallback が使われたか（＝元JSONが壊れていたか）を検知し、v6キーへは書かず、localStorageに `migration_error` フラグを残してユーザーに通知する。

---

### 5. なぜ `safeParse` で catch しているか（529-531行）

**意図**: 壊れた localStorage、別バージョンのフォーマット、手動編集後の型不一致などに対する耐性。

**確度**: high。

**懸念**: **サイレント失敗**。`console.error` も `console.warn` も出ず、ユーザーは「なぜか空になった」としか認識できない。開発者ツールを開いても手がかりが残らない。

---

## リスク分類

### High（データ損失・不可逆的挙動）

#### H1. マイグレーション失敗時の v5 データ消失リスク

**箇所**: 608-637行
**現象**: v5 の localStorage が JSON として壊れている場合、`safeParse(legacyDataJson, [])` が `[]` を返し、そのまま `saveAll()` で v6 キーに空配列が書き込まれる。以後マイグレーションは走らず、v5キー自体は残るもののユーザーには空に見える。
**再現手順**:
1. devtools で `neuro_matrix_v5_data` の末尾を破壊（例: `]` を削除）
2. v6キーをクリアしてリロード
3. タスクが消える
**対策案**: `safeParse` にフォールバック使用を示すフラグを追加し、マイグレーション関数内でフォールバック起因の空配列は書き込まない。ユーザーに復旧ダイアログを出す。

#### H2. Undoトーストの5秒タイムアウトと renderAll の競合

**箇所**: 1059-1068行（showUndo）、1082-1092行（undoDelete）
**現象**: 削除 → 5秒以内に別タスクを削除すると、最初のスナップショットが上書きされる（`lastDeletedSnapshot = taskSnapshot;`）。最初のタスクは復元不能になる。
**再現手順**: タスクA削除 → 3秒後にタスクB削除 → 「元に戻す」 → タスクBだけ復元、Aは失われる
**対策案**: スナップショットを配列にしてスタック管理するか、トーストを連続削除時に前のものを即確定（保存）する。

### Medium（体験低下）

#### M1. `title` 入力1文字ごとに `logEvent(updated)` + `saveAll`

**箇所**: 767-773行、843-849行
**現象**:
- 30件の activityLog がすぐ `updated` で埋まり、意味のある履歴（moved / completed / due_updated）が押し流される
- タスクが100件あると、1キー入力で `JSON.stringify(tasks)` を毎回実行（数KB〜数十KB）
**対策案**:
- `input` イベントを300msデバウンス
- `updated` 系は `task.updatedAt` の更新だけ行い、`activityLog` には積まない。積むのは`moved`・`due_updated`・`note_updated`（note はまとまり単位）・`completed`・`deleted`・`restored` に限定

#### M2. renderAll() の全面再描画コスト

**箇所**: 834行（dueDate change）、1003-1009行（renderAll）、1039行（completeTask）、1077行（deleteTask）、1090行（undoDelete）、1102行（moveTask）、1215行（enterSurvival）、1227行（exitSurvival）
**仮説**: 100タスク × 履歴30件 × 7ゾーンのクエリセレクタ × DOM生成で、**1描画あたり15〜30ms 程度**（chromium中級機）。D&D後やSurvival切替で体感できるレベル。
**対策案**: zone単位の差分更新関数を導入（`renderZone(zoneId)`）。現在は `moveTask` 後も `renderAll` しているが、from/to の2ゾーンだけ再描画すれば十分。

#### M3. `endDrag` 成功パスで `cleanupDrag` が呼ばれていない

**箇所**: 1170-1171行
**現象**:
```js
if (droppable) {
  moveTask(dragState.taskId, droppable.id);
}
```
`moveTask` 内 `renderAll()` で新しいカードDOMが作られ、古い `dragState.card`（body直下に移動中）はDOMから浮いた状態になる（親を失う）。実用上は renderAll が全zoneをクリアするので見た目は正しくなるが、`dragState` はリセットされず、`.drop-hover` クラスも残る可能性がある。
**再現手順**: D&D直後にF12で `dragState` を確認、`.drop-hover` が残っているか確認。
**対策案**: `moveTask` の呼び出し後にも `cleanupDrag()` を呼ぶ。

#### M4. Survivalモード中に `targetTimeInput.value` が空/不正形式

**箇所**: 1237-1242行
**現象**: `targetVal.split(':')` → `hh=undefined`, `mm=undefined` → `Number(undefined)=NaN` → `target.setHours(NaN, NaN, 0, 0)` でtargetがInvalid Date → `diff=NaN` → `diff<0` が false で落ちて、`Math.floor(NaN/...)=NaN` → `padStart` で "NaN" 表示。
**再現手順**: devtools で `targetTimeInput.value = ''` 設定後、Survival発動
**対策案**: 1238行のデフォルト適用（`'17:30'`）後に正規表現検証、失敗したら `17:30` に強制。

### Low（小さな穴）

#### L1. `todayString` と `dueDate` の比較（560-563行）

`'9999-99-99'` をセンチネル値として使っているが、`localeCompare` の辞書順で "99-99" は有効な日付より大きいので結果は正しい（682行）。ただし**意図が読みづらい**。コメントで「なぜ `9999-99-99` か」を残す価値あり。

#### L2. `navigator.vibrate` 未対応ブラウザ（1028, 1040, 1052, 1079, 1091行）

iOS Safari は `navigator.vibrate` を持たないので `if (navigator.vibrate)` で暗黙にno-op。これは仕様通りだが、「触覚フィードバックが出るはず」と期待するUXが片方のプラットフォームで失われる。意図的に許容なら OK。

#### L3. XSS面

ユーザー入力は `textContent` や `.value`（textarea）で挿入しており、`innerHTML` に混入する箇所は**テンプレートリテラル（782-785, 854-858, 964-969行）に限定**され、その中身は自前の定数／`formatDateTime`の出力（ロケール文字列）のみ。安全に見える。
ただし 855-857行 `formatDateTime(task.createdAt)` は `Intl.DateTimeFormat` の結果でエスケープが保証されるが、**将来ユーザー入力由来の日付文字列を直接 innerHTML に挟むと壊れる**。将来の守り方として、`innerHTML` テンプレートは極力なくし `createElement` で統一する方針を推奨。

#### L4. `addTask` の `tasks.unshift` + 並び替えの挙動

1018行で `tasks.unshift(task);` 先頭挿入 → その後 `sortTasks`（679行）で「締切 → 更新日時降順」に並び替わるため、**先頭挿入のメリットは表示上ほぼない**。空タスク（締切なし＆updatedAt=今）は先頭に来るが、並びロジックが別で効いているので `push` でも同じ結果。不要な最適化。

#### L5. Undoトースト連打時のタイマーリーク

1063行で `if (undoTimer) clearTimeout(undoTimer);` しているので OK。ただし showUndo → タスク復元 → 再度showUndo という流れで、`lastDeletedSnapshot` だけクリアされトーストは表示のままになる潜在パス。`undoDelete` 内では `undoToast.classList.remove('visible');`（1088）で閉じているのでOKだが、コード追跡は難しい。

---

## パフォーマンス実測仮説

（実測ではなく仮説として提示）

| シナリオ | コスト仮説 |
|---|---|
| `renderAll()` 全体（100タスク、各履歴30件） | 15〜30ms（DOM生成、`innerHTML` 数百回） |
| `saveAll()`（100タスク、各履歴30件） | 2〜5ms（JSON.stringify）。ただし localStorage 書き込みは **同期I/O**で別途数ms |
| D&D中の `onDrag`（1145-1158） | 1msオーダー。`elementFromPoint` + visibility切替で強制レイアウト1回 |
| `title` に1文字入力 | `logEvent`（～0.1ms）+ `saveAll`（~3ms）+ `refreshMeta`（~1ms）= 合計5ms前後 |
| `title` を3秒連続入力（30文字） | 30回 × 5ms = 150ms、`activityLog` に30件の `updated` が積まれて他履歴を全消し |

**localStorage容量**: 100タスク × 履歴30件 × 平均200バイト/件 ≈ 600KB。5MB上限には余裕があるが、**履歴上限を上げると一気に危険域**。

---

## 単一HTML起因の課題

- **ユニットテスト不可**: `logEvent` / `migrateLegacyIfNeeded` / `dueBadge` / `sortTasks` など純粋関数が IIFE 内に閉じ込められ外部から呼べない。JSDOM + Puppeteerでしかテストできない。
- **CSP導入不可**: `inline script` / `inline style` の前提。`Content-Security-Policy: script-src 'self'` を付けた瞬間全滅。
- **キャッシュ粒度**: CSSを1行直しただけでHTML全体（~50KB）を再配布。
- **diff可読性**: JS/CSS/HTML混在で `git diff` がノイジー。レビュー時のコンテキスト把握が遅い。
- **バージョン共存困難**: v6 と v7 を並行デプロイしたい場合、ファイルを丸ごと複製するしかない（モジュール単位の差し替えができない）。

**分割の閾値提案**: 
- CSS → `styles.css` に分離（もっとも副作用が少ない）
- JS → `app.js` に分離 + エクスポート明示
- HTML → テンプレート部分のみ残す
最低限CSS分離だけで保守性とテスト可能性が大幅に上がる。

---

## テスト戦略提案

### 単体テスト化すべき（JS分離後）
- `migrateLegacyIfNeeded`: v5→v6データ変換の入出力テーブルテスト（v5が壊れている／空／正常の3ケース）
- `baseTask`: zoneが不正値／undefined／活性ゾーンのそれぞれで期待通り正規化されるか
- `dueBadge`: 過去日 / 今日 / 未来日 / 空で4分岐
- `sortTasks`: 締切あり／なし混在、updatedAt同値
- `logEvent`: 31件目が押し出されるか、updatedAtが更新されるか

### E2E（Playwright想定）で守るべき
- **D&D**: q1→q2、q4→slot-must（Survival中）、slot-should→survival-picker の往復
- **Survival遷移**: タスクがnormalZoneに正しく戻るか、cancel中止後のzoneが元通りか
- **削除Undo**: 5秒以内・5秒後の境界
- **マイグレーション**: v5 localStorage をセット → リロード → v6で正しく見える
- **LocalStorage破損耐性**: 壊れたJSON をセット → 空画面で起動する（クラッシュしない）
- **連続削除**: 3件削除→Undo → 最新のみ復元（既知動作）をテストで固定化する

### 回帰防止として最低限
- 現状IIFEのまま守るなら、`window.neuroMatrixDebug` を通じて import/export できる（1285-1288）ので、Playwrightで `evaluate` 経由で状態を注入してスナップショット比較。

---

## 後方互換ポリシー提案

### v6 → v7 への進化に備えて

1. **バージョン文字列をデータに埋め込む**
   現状はキー名（`neuro_matrix_v6_data`）でバージョンを区別している。`tasks` 配列にラップして `{ schemaVersion: 6, tasks: [...] }` の形式にすると、**単一キーで多段マイグレーション**が書ける。

2. **マイグレーション関数をチェーン化**
   ```js
   function migrate(data, from, to) {
     if (from === 5 && to === 6) return migrateV5toV6(data);
     if (from === 6 && to === 7) return migrateV6toV7(data);
     // ...
   }
   ```
   現状の「キー2つ並行して legacy 比較」は v5→v6 用の特殊解。v7以降は上記の汎用パイプラインに統一。

3. **`window.neuroMatrixDebug` の保全**（1285-1288）
   - `export()` / `import(json)` は debug名のままだと本番で無効化されるかもしれない。**運用機能に昇格**させ、バックアップUIをheaderに追加するのが安全。
   - import の際に `schemaVersion` をチェックし、古ければマイグレーション経由で取り込む。

4. **壊れたlocalStorageの検疫ポリシー**
   上記H1への対処として、`safeParse` のフォールバック発動時に、**旧データを別キーに退避**（例: `neuro_matrix_v6_data.backup.{timestamp}`）してから空で起動。ユーザーがdevtoolsで救出できる余地を残す。

5. **セッションまたぎのバージョン検証**
   起動時に `KEY_DATA` の schemaVersion と定数の `CURRENT_SCHEMA` を比較し、未来バージョン（将来のアプリで作ったデータを古いアプリで開いた）なら起動を止め、破壊を防ぐ。

---

## まとめ（重要度トップ5）

1. **H1**: マイグレーション失敗時のデータ消失。`safeParse` にフォールバック使用シグナル追加 + v6キー書き込み前にバックアップ。
2. **M1**: 1文字入力ごとの `logEvent(updated)` + `saveAll`。デバウンス & `updated` は activityLog に積まない。
3. **H2**: 連続削除時のUndoスナップショット上書き。スタック化。
4. **M2**: `renderAll` の全面再描画コスト。`moveTask` 時の部分再描画化。
5. **M3**: `endDrag` 成功パスで `cleanupDrag` 未呼び出し。1ライン追加で解決。

以上、重要度順に対応すれば v6 の安定性は十分高まる。v7 への進化タイミングでスキーマにバージョンを埋め込むのが次の大きな一歩。
