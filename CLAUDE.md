# bpr_lab

`sandbox/` 配下に複数の独立プロジェクトを持つ実験リポジトリ。統合ハブは `sandbox/タスクマネージャー/`（運用ルールはそこの CLAUDE.md 参照）。

## クラウドセッション（スマホ/Web起動）向けの前提

- このセッションがクラウドVM上で動いている場合、ユーザーのPCのローカル状態は見えない。PCへの反映経路は「**mainへマージ → PC側が15分毎に自動pull**」（GitAutoSyncスキーム）。
- したがって、**PCに届けたい変更は PR 作成→main へのマージまでセッション内で完了させること**。作業ブランチ（claude/...）止まりだと PC には fetch されるだけで自動反映されない。
- claude.ai のコネクタ（Gmail / Slack 等）は Anthropic サーバー経由でクラウドセッションからも利用できる（ユーザーは Gmail 接続済み）。

## 用語「drop」（スマホからの情報投げ込み運用）

「drop」= ユーザーが外出先から情報を投げ込む運用のこと。**Gmail の自分宛てメールで件名に `[drop]` を含めて送る**（本文に URL やメモ）。UI へのドラッグ&ドロップのことではない。

ユーザーが「dropした」「gmailにdropした」「drop拾って」と言ったら:

1. `sandbox/タスクマネージャー/.claude/skills/drop-pickup/SKILL.md` を Read し、その手順に従う
   （要点: Gmail コネクタで `subject:[drop] newer_than:30d` を検索 → `get_thread` で本文取得 →
   `drop-processed` ラベルで既読管理 → URL とメモを抽出）
2. `sandbox/タスクマネージャー/library/inbox/drop.md` の**末尾に追記**する（既存内容は絶対に消さない）
3. クラウドセッションの場合は、コミット→PR→main へのマージまで完了させる（PC に自動反映させるため）

スキルとして認識されていなくても、上記 1 のファイルを明示的に Read すれば手順は全て書いてある。
