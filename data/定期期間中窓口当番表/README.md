## 1. 全体概要

- **解決している業務課題**  
  定期期間中（例: 1/5〜2/28）の窓口当番を自動編成し、祝日除外・グループ分散・新人配置・勤務可否など複雑なビジネスルールを網羅的に満たしたスケジュールを作成します。人手で行うと手戻りが発生しがちな調整作業を CP-SAT による制約最適化で機械化します。
- **CP-SAT で解いている問題**  
  変数 `assign[(staff_id, date, period)] ∈ {0,1}` を用いた 0-1 整数計画。各スロットの割当可否・人数制限をハード制約として追加し、目的関数で「欠員 → 総回数差 → 金曜差 → AM/PM 差」の順に重み付きで最小化します。
- **処理フロー**
  ```
  CSV読込 (staff / schedule_config / special_constraints)
       │
       ├─データ正規化・例外上書き
       │
       ├─制約モデル生成 (CP-SAT)
       │
       ├─最適化 (Solve)
       │
       └─結果整形 → schedule.xlsx → 窓口当番表_完成版.xlsx
  ```

## 2. ファイル構成

| ファイル | 役割 |
|----------|------|
| `scheduler.py` | OR-Tools CP-SAT を使ったメインスクリプト。データ読込・制約構築・目的関数定義・結果出力を一括で行う。 |
| `data/staff.csv` | 職員基本情報。所属グループ、曜日可否、AM/PM 可否、年次区分などの恒常データ。 |
| `data/schedule_config.csv` | 各営業日の必要窓数（AM/PM）と繁忙フラグ。祝日・休日はスクリプト側で除外。 |
| `data/special_constraints.csv` | 個別例外（研修・年休など）。日付単位で AM/PM 可否を上書き。空でも実行可。 |
| `output/schedule.xlsx` | CP-SAT の解をデータフレーム形式で保存。`date, weekday, period, staff_id, name, group, busy` が列。 |
| `output/窓口当番表_完成版.xlsx` | schedule.xlsx を所定フォーマット（午前1〜4/午後1〜4）へ転記した成果物。Excel マクロや別スクリプトで生成。 |

## 3. 入力 CSV 仕様（必須）

### staff.csv
| 列名 | 型 | 意味 |
|------|----|------|
| `staff_id` | int | 社員ID（ユニーク、1始まり推奨） |
| `name` | string | 氏名。出力時もこの値を使う。 |
| `group` | string | 当番配置グループ（A〜E 想定）。同時間帯の上限制御に使用。 |
| `wed_off` | bool(0/1) | 水曜固定休など週次制約に利用（現在は将来拡張用）。 |
| `am_ok` | bool | 午前帯の恒常的な勤務可否。0 の場合、AM 割当変数は作成されない。 |
| `pm_ok` | bool | 午後帯の恒常的な勤務可否。同上。 |
| `year1` | bool | 新人フラグ。新人制約で使用。 |

### schedule_config.csv
| 列名 | 型 | 意味 |
|------|----|------|
| `date` | ISO 日付 (YYYY-MM-DD) | 期間内の各日。脚注で祝日は自動除外。 |
| `am_slots` | int | 午前の必要枠数（通常2、繁忙3〜4など）。 |
| `pm_slots` | int | 午後の必要枠数。 |
| `busy` | int(0/1) | 繁忙マーク。目的関数には直接使っていないが集計で活用可能。 |

### special_constraints.csv
| 列名 | 型 | 意味 |
|------|----|------|
| `staff_id` | int | 対象職員 |
| `date` | string | `2026-01-15` または `1月15日` など柔軟な表記に対応 |
| `am_ok` | {0,1,""} | 当日の AM 上書き（空欄なら変更なし） |
| `pm_ok` | {0,1,""} | 当日の PM 上書き |
| `note` | string | 備考。ログ出力などで参照。 |

> **例外日の扱い**: `special_constraints` に該当する日付・職員組み合わせがある場合、staff.csv の `am_ok/pm_ok` を当日だけ置換します。複数行ある場合は後勝ち（CSV内の下の行が優先）。

## 4. 最適化モデルの制約一覧

| 制約 | 内容 / 意図 | 数式イメージ |
|------|-------------|---------------|
| **可否制約** | 祝日・土日を対象外とし、`am_ok/pm_ok` や `special_constraints` を元に `assign[s,d,p]=0` を強制。午後NG の職員は PM 変数自体を作成しません。 | `assign[s,d,p] ≤ availability[s,d,p]` |
| **間隔制約** | 同一職員が連続して稼働しないよう、当番後は 2 営業日空ける。AM/PM いずれか1枠に入ったらその日を `day_var[s,d]=1` とし、`day_var[s,d] + day_var[s,d+1] ≤ 1` を 2日分適用。 | `day_var[s,d] + day_var[s,d+1] ≤ 1` |
| **1日1回** | 同一日 AM/PM での二重割当禁止。 | `∑_{p∈{AM,PM}} assign[s,d,p] ≤ 1` |
| **グループ制約** | 同時間帯で同グループが上限数（標準1名、Dグループのみ2名）を超えない。| `∑_{s∈group g} assign[s,d,p] ≤ limit_g` |
| **新人制約** | 新人 (`year1=1`) の同時間帯数をスロット数に応じて制限。slots=2→新人≤1、slots=3/4→新人≤2。経験者が不足しそうな場合は警告ログを出す。| `∑_{s∈rookie} assign[s,d,p] ≤ cap(slots)` |
| **金曜均等化** | 金曜日の `day_var` を集計し、最大回数と最小回数の差を補助変数 `friday_gap` で表現。目的関数で小さくする（ソフト制約）。| `max_fri - min_fri = friday_gap` |
| **AM/PM バランス** | AM/PM 両方可能な Flex 職員について、AM 回数と PM 回数の差の絶対値 `diff_s` を最小化。| `diff_s ≥ am_total_s - pm_total_s` など |
| **午後NG回数** | `pm_ok=0` の職員は総割当が 7〜8 回になるようハード制約。| `7 ≤ totals_s ≤ 8` |
| **水曜休み (wed_off)** | 現状はデータ保持のみ。将来 `wed_off=1` の日を完全除外する際には `availability` 計算に組み込む。 |

## 5. 目的関数

```
Minimize(
    1000 * total_shortfall        # 欠員の最優先削減
  +   10 * fairness_gap           # 全期間の最大割当と最小割当の差
  +    3 * friday_gap             # 金曜の割当差
  +    1 * sum(ampm_diff_s)       # Flex職員のAM/PM差
)
```

- **短欠 (total_shortfall)**: `required_slots - 実際の割当` を `slack` で吸収し、不足を最小化。
- **総回数差 (fairness_gap)**: `max_total - min_total`。職員間で総当番回数を揃える。
- **金曜差 (friday_gap)**: 金曜日のみを対象とした `max_fri - min_fri`。
- **AM/PM 差 (ampm_diff)**: Flex 職員ごとの AM/PM 不均衡。絶対値表現に補助変数 `diff_s` を使用。
- 重みは業務優先度を反映。欠員ゼロ > 全体均等 > 金曜調整 > AM/PM の微調整という順序を担保します。

## 6. 実行方法

1. 依存ライブラリをインストール  
   ```bash
   pip install ortools pandas openpyxl jpholiday
   ```
2. `scheduler.py` と同じディレクトリで実行  
   ```bash
   python scheduler.py
   ```
3. 出力  
   - `output/schedule.xlsx` に DataFrame 形式の割当表が生成されます。  
   - Excel を開いたままだと書き込みに失敗する場合、タイムスタンプ付きファイルへフォールバック保存します。

> **Windows 例**  
> `C:\Users\xxx\...\定期期間中窓口当番表> python scheduler.py`

## 7. フォーマットへの書き出し処理

- `schedule.xlsx` は 1 行 1 割当のロング形式。列: `date / weekday / period / staff_id / name / group / busy`。
- 転記スクリプト（別途用意）で以下のように配置  
  - AM → 「午前1〜4」列へ順番に書き込み  
  - PM → 「午後1〜4」列へ書き込み  
  - 1日に必要枠が2の場合は午前1〜2のみ使用
- 転記後に `output/窓口当番表_完成版.xlsx` を生成し、提出用フォーマットを完成させます。同ファイルは Excel の数式・Conditional Formatting に対応。

## 8. 仕様変更の方法

- **新人制約の変更**  
  `rookie_limit()` の戻り値を修正（例：最大新人数を slots-1 にするなど）。
- **金曜均等化を無効化**  
  `FRIDAY_WEIGHT` を 0 に設定、もしくは `friday_gap` 関連の約束をスキップ。
- **午後NG 下限の調整**  
  `model.Add(total_var >= 7)` の定数を変更。上限が不要ならコメントアウト可能。
- **新ルール追加**  
  1. `assignment_vars` 作成後〜目的関数前が拡張ポイント  
  2. 例: 週次上限 → `for week in weeks: model.Add(sum(assign in week) ≤ cap)`  
  3. ソフト制約化したい場合は補助変数を導入し目的関数に重みを付ける。

## 9. 想定されるエラーと対処

| 症状 | 原因 | 対処 |
|------|------|------|
| `Solver failed (INFEASIBLE)` | 午後NG 7回以上が満たせない / 新人制約で経験者不足 / 特定日で可用人数 < 必要枠 | ログに対象日・期間が出力されるので、`staff.csv` の可否や `schedule_config` の枠を見直す。 |
| CSV 読込エラー | 列不足・フォーマット違い | README の列仕様を確認し、Excel の自動変換（例: 1月5日→2025/1/5）を注意。 |
| `PermissionError: schedule.xlsx` | ファイルを開いたまま | Excel を閉じるか、自動で生成される `_YYYYMMDD_HHMMSS` ファイルを使用。 |
| 金曜偏り | 祝日で金曜が少ないなど数学的に均等不可 | `FRIDAY_WEIGHT` を下げる / 祝日でも枠を確保する等で調整。 |

## 10. 今後の拡張案

- **Power Automate / バッチ化**  
  SharePoint 等に配置し、CSV をアップロードしたら自動で scheduler を起動→結果を Teams 通知。
- **職場PC向け簡易モード**  
  GUI (Tkinter / PySimpleGUI) を作成し、期間やCSVパスを選択してボタン一つで実行。
- **デバッグログ拡張**  
  `--verbose` オプションを追加し、制約ごとの統計や Slack 変数値、未割当日の詳細を CSV で出力。
- **週次レポート生成**  
  pandas で AM/PM 回数集計 → PowerPoint/Excel テンプレに差し込み、自動報告資料を作成。

---

この README だけでスケジューラの構造・制約・実行方法を把握できるよう、各項目に具体的な列仕様や数式イメージを掲載しています。疑問点があれば `scheduler.py` の該当セクションを参照しながら調整してください。

