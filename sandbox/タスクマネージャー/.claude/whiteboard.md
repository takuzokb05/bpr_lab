# Whiteboard

<!-- エージェント間の情報共有ファイル。追記のみ（Append-only） -->

## [ブリーフィング] メインClaude
- articles/ に保存する際、取得した原文を改変しない
- catalog.md の既存エントリは削除・変更しない（追記のみ）
- skills-registry/ はプロジェクト外。直接編集しない
- #4（trq212/2033949937936085378）は catalog.md #12 に既存。重複注意
- ユーザーメモ付きリンクあり:
  - `coreyganim` → 「Cowork」
  - `oikon48` → 「要検証」
  - `HiTw93` → 「一連のツイート掘り下げて」
  - `SuguruKun_ai` → 「macだからWindowsにするなら、の観点」

## [2026-03-21 00:00] Fetcher
### 取得済み記事
| # | ファイル | 元URL | 著者 |
|---|---------|-------|------|
| 1 | articles/Lessons from Building Claude Code Skills（公式・Thariq）.txt | https://x.com/trq212/status/2033949937936085378 | @trq212 |
| 2 | articles/非エンジニア向け2つのファイル設定（tetumemo）.txt | https://x.com/tetumemo/status/2026616269836099678 | @tetumemo |
| 3 | articles/5つのAgent Skillデザインパターン（GoogleCloudTech）.txt | https://x.com/GoogleCloudTech/status/2033953579824758855 | @GoogleCloudTech |
| 4 | articles/Autoresearchでスキル自動改善（Ole Lehmann）.txt | https://x.com/itsolelehmann/status/2033919415771713715 | @itsolelehmann |
| 5 | articles/Claude Cowork完全入門（Corey Ganim）.txt | https://x.com/coreyganim/status/2028470330247803361 | @coreyganim |
| 6 | articles/CLAUDE.mdをちゃんと読ませるimportantタグ（oikon48）.txt | https://x.com/oikon48/status/2034146114220499396 | @oikon48 |
| 7 | articles/Paperclip AIエージェント会社運営ツール（Nick Spisak）.txt | https://x.com/NickSpisak_/status/2033518072724705437 | @NickSpisak_ |
| 8 | articles/Claude Codeシステム設計問題（Tw93 claude-health）.txt | https://x.com/HiTw93/status/2033911478466843115 | @HiTw93 |
| 9 | articles/Shorthand Guide to Everything Claude Code（affaanmustafa）.txt | https://x.com/affaanmustafa/status/2012378465664745795 | @affaanmustafa |
| 10 | articles/Claude Code Channels Telegram Discord（公式・Thariq）.txt | https://x.com/trq212/status/2034761016320696565 | @trq212 |
| 11 | articles/Seeing like an Agent ツール設計の教訓（公式・Thariq）.txt | https://x.com/trq212/status/2027463795355095314 | @trq212 |
| 12 | articles/Claude Code使用率ステータスライン表示（逆瀬川）.txt | https://x.com/gyakuse/status/2034797426285162911 | @gyakuse |
| 13 | articles/Longform Guide to Everything Claude Code（affaanmustafa）.txt | https://x.com/affaanmustafa/status/2014040193557471352 | @affaanmustafa |
| 14 | articles/コピペで使えるClaude スキル50選（Hoshino）.txt | https://x.com/Hoshino_AISales/status/2034880613606727932 | @Hoshino_AISales |
| 15 | articles/Browser Use CLI 2.0リリース.txt | https://x.com/browser_use/status/2035081807209931153 | @browser_use |
| 16 | articles/非エンジニアのためのSkills完全入門（長谷川taichi_we）.txt | https://x.com/taichi_we/status/2034901282750935177 | @taichi_we |
| 17 | articles/frontend-slidesスキルでスライド作成（SuguruKun_ai）.txt | https://x.com/SuguruKun_ai/status/2034972820040819101 | @SuguruKun_ai |
| 18 | articles/Skill Graphsでスキルをネットワーク化（arscontexta）.txt | https://x.com/arscontexta/status/2023957499183829467 | @arscontexta |

### 備考
- #1（trq212/2033949937936085378）は catalog.md #12 に既存の記事と重複。ただし既存記事のファイル名は「Lessons from Building Claude Code How We Use Skills.txt」で、今回は公式の最新版として別ファイルで保存した
- #8（HiTw93）は引用ツイート元の長文記事（2033181380432339045）も取得して本文に含めた
- エラー: なし（18本すべて正常取得）
- ユーザーメモ: #5=Cowork, #6=要検証, #8=一連のツイート掘り下げて, #17=macだからWindowsにするなら

## [2026-03-21 00:30] Cataloger
### 目録追加完了
- Fetcher #1（Lessons from Building Claude Code Skills）→ **スキップ（既存catalog #12と重複）**
- 17本を #26〜#42 として追加（状態=読了、反映先=検討中）

| # | タイトル | 分類 | 要点 |
|---|---------|------|------|
| 26 | 非エンジニア向け2つのファイル設定（tetumemo） | 非エンジニア, ガバナンス | settings.local.json + CLAUDE.mdの二重ロック。一行ずつ解説付き |
| 27 | 5つのAgent Skillデザインパターン（GoogleCloudTech） | スキル | Tool Wrapper/Generator/Reviewer/Inversion/Pipelineの5パターン |
| 28 | Autoresearchでスキル自動改善（Ole Lehmann） | スキル | autoresearchでスキルを自動改善。チェックリスト評価ループで56%→92% |
| 29 | Claude Cowork完全入門（Corey Ganim） | ワークフロー, 非エンジニア | Cowork=自律型デスクトップ社員。システム工学への転換 |
| 30 | CLAUDE.mdをちゃんと読ませるimportantタグ（oikon48） | CLAUDE.md | `<important if="condition">`タグで重要箇所強調。要検証 |
| 31 | Paperclip AIエージェント会社運営ツール（Nick Spisak） | agent設計 | 複数AIエージェントを組織図・予算・チケットで管理するOSS |
| 32 | Claude Codeシステム設計問題（Tw93 claude-health） | アーキテクチャ, CLAUDE.md | 6層フレームワーク。3段階進化。`/health`で設定診断 |
| 33 | Shorthand Guide to Everything Claude Code（affaanmustafa） | アーキテクチャ, ワークフロー | Skills/Hooks/Subagents/MCPs/Plugins全体像 |
| 34 | Claude Code Channels — Telegram/Discord連携（公式・Thariq） | アーキテクチャ | モバイルからClaude Codeセッションを遠隔操作 |
| 35 | Seeing like an Agent — ツール設計の教訓（公式・Thariq） | アーキテクチャ, スキル | AskUserQuestion誕生経緯。ツールはモデル能力に合わせて再設計すべし |
| 36 | Claude Code使用率ステータスライン表示（逆瀬川） | ワークフロー | rate_limitsフィールドで使用量をステータスライン表示 |
| 37 | Longform Guide to Everything Claude Code（affaanmustafa） | アーキテクチャ, ワークフロー | トークン経済学・メモリ永続化・検証ループ・並列化戦略 |
| 38 | コピペで使えるClaude スキル50選（Hoshino） | スキル, 非エンジニア | 50スキルテンプレ。descriptionの書き方で自動起動率9割決まる |
| 39 | Browser Use CLI 2.0リリース | アーキテクチャ | 2倍速・半額コスト・CDP直接接続のブラウザ自動化CLI |
| 40 | 非エンジニアのためのSkills完全入門（長谷川taichi_we） | スキル, 非エンジニア | SKILL.md=日本語の作業マニュアル。descriptionが発動判定の鍵 |
| 41 | frontend-slidesスキルでスライド作成（SuguruKun_ai） | スキル | スキルの作り込みがアウトプット品質を左右する時代 |
| 42 | Skill Graphsでスキルをネットワーク化（arscontexta） | スキル, アーキテクチャ | wikilink+YAMLで250+ファイルのスキルグラフ。Progressive Disclosure究極形 |

### 統計更新
- 蔵書数: 25 → 42（+17）
- 読了（未反映）: 10 → 27（+17）
- 注目: #26は既存#13（非エンジニアの2つのファイル設定）と同テーマだが別著者・別記事のため重複ではない

## [2026-03-21 00:30] Advisor

### 分析サマリー

18本中 #1 は既存 #12 と重複のため分析対象外。残り17本を分析した。
（以下、記事番号はCatalogerが採番した #26〜#42 を使用）

### 反映提案

| 記事 | 提案 | 反映先 | 優先度 |
|------|------|--------|--------|
| #32 Tw93 claude-health | **CLAUDE.md肥大化防止ルール追加**: 「CLAUDE.mdが長すぎるとcontext汚染する」「短く運用的に保て」。6層フレームワーク概念整理。Compact Instructionsの記載推奨 | base.md に「Compact Instructions」セクション追加 + CLAUDE.md長さ上限ガイドライン | 高 |
| #32 Tw93 claude-health | **検証ループの必須化**: 「no verifier = no engineering agent」「acceptance criteriaを事前定義」。base.mdの4ステップWFに検証ステップ強化が必要 | base.md 4ステップWF の「確認」ステップに acceptance criteria 事前定義を追記 | 高 |
| #35 Seeing like an Agent | **ツール設計の進化原則**: モデル能力向上に伴いツールを見直すべき（TodoWrite→Task Tool の事例）。skills-registryのスキルも定期的に「モデルを制約していないか」点検すべき | skill-design-patterns.md に「ツール/スキルの定期見直し」セクション追加 | 中 |
| #28 Autoresearch | **スキル自動改善の具体手法**: チェックリスト3-6問→ループ実行→スコア改善。既存のSelf-improvingループパターンの具体的実装方法 | skill-design-patterns.md に autoresearch パターン（チェックリスト評価ループ）を追記 | 中 |
| #27 5つのAgent Skillデザインパターン | **既存 #11 ADKパターンの補強**: GoogleCloudTech版は同じ5パターンだがより明確な判断ツリー付き。Inversionパターン（エージェントが面接官）はask_user_inputスタイルと直結 | skill-design-patterns.md の既存5パターン説明を補強（判断ツリー追加） | 中 |
| #30 importantタグ | **要検証**: `<important if="condition">` でCLAUDE.mdの重要箇所を強調できるという情報。HumanLayer Blog記事が元ネタ。効果確認できればbase.mdテンプレートに採用 | 検証後、base.md テンプレートの重要セクションに `<important>` タグ導入 | 中（要検証） |
| #37 Longform Guide | **コンテキスト管理の体系化**: 動的システムプロンプト注入の優先順位（--system-prompt > user message > tool results）、戦略的compact、セッションログパターン | base.md または docs/ に「コンテキスト管理ガイド」追加 | 中 |
| #37 Longform Guide | **サブエージェントのIterative Retrieval Pattern**: サマリーだけでは重要詳細が欠落→最大3サイクルの反復取得。サブエージェント運用ガイドに追加すべき | agent-governance.md サブエージェント節に反復取得パターン追記 | 中 |
| #42 Skill Graphs | **スキルのネットワーク化構想**: wikilink + YAML frontmatter + MOCでスキルをグラフ化。skills-registryスケーリング手法として中長期検討 | skills-registry 中長期ロードマップとして記録（即時反映不要） | 低 |
| #29 Cowork完全入門 | **Coworkのコンテキストアーキテクチャ**: about-me.md / brand-voice.md / working-preferences.md の3ファイル構成。非エンジニア向けテンプレート参考 | 非エンジニア向けテンプレート検討時の参考資料として保持 | 低 |
| #31 Paperclip | **エージェント組織管理ツール**: 予算管理・Heartbeat・Governance機能のOSS。既存#2 PRマネージャー32人チームの実装手段として参考 | 参考情報として保持（即時反映不要） | 低 |
| #38 スキル50選 | **descriptionの書き方補強**: 「具体的キーワード5つ以上」「単一職責原則」「最初は60点で育てる」。既存の「descriptionはトリガー条件」パターンの実践的補足 | catalog.yaml の description 運用ガイドに「キーワード5つ以上」追記検討 | 低 |
| #33 Shorthand Guide | **MCP過剰搭載の警告**: 20-30 MCPあっても有効10以下・ツール80以下に抑えるべき。コンテキストウィンドウ管理の知見 | base.md の MCP 利用ガイドラインに上限目安追記 | 低 |

反映不要と判断した記事:
- #26 tetumemo — 既存#13と同じ二重ロック概念。新規知見少ない（パターン補強のみ）
- #34 Channels — 新機能告知のみ
- #36 ステータスライン — 運用Tips。反映対象外
- #39 Browser Use CLI 2.0 — ツールリリース告知。内容が薄い
- #40 Skills完全入門（長谷川）— 既存パターンの範囲内
- #41 frontend-slides — スキル具体例としての参考のみ

### 発見パターン更新案

| パターン | 更新内容 |
|---------|---------|
| **禁止パターンの明示化** | #26（tetumemo）を追加 → 計4本（#5, #6, #13, #26）。denyリストの具体例（rm, del, rmdir, Remove-Item）が充実 |
| **Progressive Disclosure** | #32（Tw93）, #42（Skill Graphs）, #35（Seeing like an Agent）を追加 → 計6本。Skill Graphsの再帰的Progressive Disclosureは発展形 |
| **二重ロック（仕組み+理由）** | #26（tetumemo）を追加 → 計4本（#3, #4, #13, #26）。「包丁の安全カバー＋注意喚起」の比喩が秀逸 |
| **Self-improving ループ** | #28（Autoresearch）, #37（Longform Guide learned skills）を追加 → 計4本。Autoresearchの定量的改善ループ（56%→92%）は具体実装例。**3本超えにつき反映推奨** |
| **descriptionはトリガー条件** | #38（スキル50選）, #40（Skills完全入門）を追加 → 計3本。「キーワード5つ以上」「発動タイミングを書く」で一致。**3本到達につき反映推奨** |
| **Gotchasセクション** | Fetcher#1（Thariq公式最新版、catalog既存#12の最新版）を補強材料として確認 → 引き続き3本級。公式が繰り返し強調 |
| **検証ループの必須化**（新規パターン提案） | 出現記事: #32（Tw93: no verifier = no engineering agent）, #37（Longform: Checkpoint-Based Evals）, #28（Autoresearch: チェックリスト評価）。3本で独立パターン形成。「成果物の検証手段を事前定義しないエージェントは信頼できない」 |
| **コンテキストは有限資源**（新規パターン提案） | 出現記事: #32（Tw93: MCP定義だけで12.5%消費, CLAUDE.md肥大化警告）, #33（Shorthand: MCP 10以下・ツール80以下）, #37（Longform: System Prompt Slimming 18k→10k）, #42（Skill Graphs: 必要な部分だけ読み込む）。4本で強パターン。「Progressive Disclosure」と関連するが、こちらは「無駄を削る」方向 |
| **スキル設計パターンは収束中**（新規パターン提案） | 出現記事: #27（GoogleCloudTech 5パターン）, 既存#11（ADK 5パターン）, #32（Tw93: 3タイプ）, #40（長谷川: 3タイプ）, 既存#12/Fetcher#1（Thariq: 9カテゴリ）。5本。エコシステム全体でパターンが収束しつつあり、skill-design-patterns.md の信頼性は高い |

### 優先アクション（メインClaude向けサマリー）

1. **高優先**: #32 Tw93 の知見を base.md に反映（Compact Instructions + 検証ループ強化 + CLAUDE.md肥大化防止）
2. **中優先**: skill-design-patterns.md に autoresearch パターンと判断ツリーを追加（#28, #27）
3. **中優先**: #30 importantタグの効果を検証（HumanLayer Blog記事を読んで判断）
4. **中優先**: agent-governance.md にサブエージェント反復取得パターンを追記（#37）
5. **低優先**: 新規発見パターン3つ（検証ループ / コンテキスト有限資源 / スキル分類収束）を catalog.md に追加
