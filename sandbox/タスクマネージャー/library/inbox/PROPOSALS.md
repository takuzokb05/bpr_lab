# 反映提案ログ

記事収集から得た知見をCLAUDE.md・skills-registry・設定等に反映すべき提案をまとめます。

---

## 2026-03-27 収集分

### 1. CLAUDE.md への反映提案

#### 1-1. Progressive Disclosure パターンの採用
**出典:** articles/2026-03-27_013_効果的なCLAUDE_md書き方.md / articles/2026-03-27_003_50_Claude_Code_Tips_Best_Practices.md

**提案内容:**
CLAUDE.md に書く情報を「常に必要な情報」と「特定状況でのみ必要な情報」に分離する。

```
CLAUDE.md          … 常に必要なプロジェクト概要・必須コマンド・絶対的禁止事項
.claude/rules/*.md … 特定のファイル種別・タスク種別にのみ適用されるルール
```

YAMLフロントマターのglobパターンで条件付きルールを設定することで、コンテキスト消費を抑えつつ必要なルールだけを読み込める。

#### 1-2. CLAUDE.md の「禁止パターン」明記
**出典:** articles/2026-03-27_006_Claude_Code_Hooks_Guide_2026.md

**提案内容:**
CLAUDE.md は約80%の遵守率。**絶対に守らせたいルール（秘密情報コミット禁止・本番DBへの直接書き込み禁止等）はCLAUDE.mdではなくフックで実装する**ことを明記すべき。CLAUDE.mdには「このルールはフックで強制されている」とコメントを入れると読者への注意喚起になる。

#### 1-3. コンテキスト管理の閾値をCLAUDE.mdに記載
**出典:** articles/2026-03-27_007_Claude_Code_Complete_Guide_2026.md / articles/2026-03-27_002_Claude_Code_Tips_and_Tricks.md

**提案内容:**
コンテキスト管理の運用ガイドとして以下を記載：
- 0〜50%: 自由に作業
- 50〜70%: コンテキスト使用量に注意
- 70〜90%: `/compact` を使用
- 90%+: `/clear` 必須（この状態で作業継続するとハルシネーションが著しく増加）

#### 1-4. Auto Memory ディレクトリの設定
**出典:** articles/2026-03-27_001_Claude_Code_March_2026_Updates.md

**提案内容:**
`autoMemoryDirectory` 設定を `.claude/settings.json` に追加し、Claude が自動記録するメモリの保存先をプロジェクト管理下に含める（.gitignoreへの追加も検討）。

---

### 2. スキル設計への反映提案

#### 2-1. スキルの YAML フロントマター活用
**出典:** articles/2026-03-27_017_Claude_Code_Agent_Skills解説.md / articles/2026-03-27_009_Claude_Code_スキル活用術.md

**提案内容:**
既存スキルの SKILL.md に以下のフロントマターフィールドを追加・整備する：

```yaml
---
name: skill-name
description: Claude が自動判定に使う説明（詳細に書くほど自動呼び出し精度が上がる）
disable-model-invocation: true  # スクリプトのみのスキルの場合
allowed-tools: Read, Grep, Edit  # 必要なツールのみに限定
---
```

特に `description` の充実が自動呼び出し精度に直結するため、「どんなときに使うか」を具体的に記述する。

#### 2-2. スキルのオープンスタンダード対応
**出典:** articles/2026-03-27_017_Claude_Code_Agent_Skills解説.md

**提案内容:**
Agent Skills は GitHub Copilot Coding Agent や OpenAI Codex CLI とも SKILL.md フォーマットを共有可能。チームに複数のAIツール利用者がいる場合、共通スキルリポジトリとして管理する価値がある。

#### 2-3. スキルの「育てる」運用フロー整備
**出典:** articles/2026-03-27_009_Claude_Code_スキル活用術.md

**提案内容:**
スキル作成時は最小構成（SKILL.mdのみ）からスタートし、実際の使用を通じて段階的に育てるフローを標準化する：
1. Claude に「今やった作業をスキルにして」と依頼 → SKILL.md を自動生成
2. 2週間実際に使って不足を洗い出す
3. references/ に詳細ドキュメントを追加
4. 必要に応じて allowed-tools・disable-model-invocation を調整

---

### 3. フック設計への反映提案

#### 3-1. MCP ツール呼び出しへのフック適用
**出典:** articles/2026-03-27_006_Claude_Code_Hooks_Guide_2026.md / articles/2026-03-27_005_Claude_Code_Setup_MCP_Hooks_Skills_2026.md

**提案内容:**
MCP ツールの呼び出しにもフックが適用可能。マッチャーパターン `mcp__<server>__<tool>` を活用して特定 MCP 操作を傍受できる。例：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__github__push_files",
        "hooks": [{ "type": "command", "command": "scripts/pre-push-check.sh" }]
      }
    ]
  }
}
```

#### 3-2. 無人実行（Unattended）向けフック安全網の整備
**出典:** articles/2026-03-27_006_Claude_Code_Hooks_Guide_2026.md

**提案内容:**
Claude Code を無人実行（ヘッドレスモード・GitHub Actions等）で使う場合、以下のフックを必須とする：
- `PreToolUse` で `.env`・`.pem`・`credentials` 等を含むファイルのコミットをブロック
- `PreToolUse` で本番ブランチ（main/master）への直接pushをブロック
- `PostToolUse` でコードフォーマッターを自動実行

---

### 4. MCP 設定への反映提案

#### 4-1. MCP ツール検索（遅延ロード）の活用
**出典:** articles/2026-03-27_005_Claude_Code_Setup_MCP_Hooks_Skills_2026.md / articles/2026-03-27_003_50_Claude_Code_Tips_Best_Practices.md

**提案内容:**
MCP の Tool Search 機能（自動モード）を有効化することでコンテキスト使用量を最大 95% 削減できる。多数の MCP サーバーを登録している場合、この設定が必須。2026年1月のアップデートでデフォルト有効化済みだが、古い設定ファイルを持つ環境では明示的に確認する。

---

*以上の提案は優先度順ではなく、重要度に応じて実装タイミングを判断してください。*

---

## 2026-03-28 収集分

### 1. CLAUDE.md への反映提案

#### 1-1. 150〜200命令の上限とProgressive Disclosureパターン
**出典:** articles/2026-03-28_139_How_to_Write_Good_CLAUDE_md_Builder_io.md / articles/2026-03-28_148_Zenn_Effective_CLAUDE_md_Farstep.md

**提案内容:**
CLAUDE.mdの命令数が150〜200を超えると全命令の遵守率が一様に低下するという実測データが報告されている。

- CLAUDE.md は「インデックス」として機能させ、詳細情報はSkillsや`.claude/rules/*.md`に移動する
- 「コメントは英語で書け」→ 「コメントは英語で書け（理由: 多国籍チームのレビュー容易化のため）」のように理由を付記することで遵守率が向上
- 現在のCLAUDE.mdの行数を確認し、200行を超えている場合はSkillsへの移行を優先する

#### 1-2. CLAUDE.md と AGENTS.md のクロスツール互換
**出典:** articles/2026-03-28_149_Izanami_CLAUDE_md_AGENTS_md_Best_Practices.md

**提案内容:**
CLAUDE.mdはMarkdown自由形式、OpenAI CodexのAGENTS.mdは構造化YAML推奨という差異がある。複数のAIコーディングツールを使うチームでは、共通ルールをどちらにも対応できる形式で書く戦略が有効。

---

### 2. スキル設計への反映提案

#### 2-1. スキルdescriptionの自動発動率改善
**出典:** articles/2026-03-28_141_Claude_Code_Skills_Activate_Reliably_Scott_Spence.md

**提案内容:**
スキルの自律発動率はデフォルトで約50%。以下2つの改善で80-84%まで向上：
1. descriptionに「when user asks about X」「triggered by Y」などの明示的トリガー文言を含める
2. スコープを絞った具体的な名前を付ける（「code-review」より「python-code-review」）

既存のSKILL.mdのdescriptionフィールドを見直し、トリガー条件を明示化することを推奨。

#### 2-2. スキルの自動生成メタワークフロー
**出典:** articles/2026-03-28_147_Classmethod_Claude_Code_Create_Skills_Itself.md

**提案内容:**
「今やった作業をスキルにして」というプロンプト一言でClaude Codeが自動でSKILL.mdを生成できる。新しいスキルが必要になったときはこのメタワークフローを活用し、人間によるSKILL.md初期作成コストをゼロにする。

---

### 3. MCP設定への反映提案

#### 3-1. CloudflareのContainer MCPサーバーの活用
**出典:** articles/2026-03-28_154_Cloudflare_13_MCP_Servers.md

**提案内容:**
Cloudflare Container MCPサーバーを使うと、実行環境を持たないClaudeクライアント（claude.ai等）にサンドボックス実行環境を提供できる。FX自動取引システムのバックテスト実行・コード検証をclaude.ai経由で行う場合に活用できる可能性がある。

#### 3-2. MCP 2026ロードマップ対応の準備
**出典:** articles/2026-03-28_152_MCP_2026_Roadmap_Official.md

**提案内容:**
MCPの2026年最優先事項は「Streamable HTTP（ステートレス水平スケール）」と「Enterprise認証・監査」。現在のSSE方式のMCPサーバーは将来的にStreamable HTTPへの移行が推奨される方向。新規MCPサーバーを実装する際はStreamable HTTP対応を意識した設計にすることを推奨。

---

### 4. FX自動取引システムへの反映提案

#### 4-1. LLMをエントリーフィルターとして使うパターン
**出典:** articles/2026-03-28_167_FX_Prime_Bot_LLM_Hybrid_Note_Yo_Hide.md

**提案内容:**
LLMを「完全自律判断」ではなく「センチメントフィルター」として使うアーキテクチャが現実的。
- 60秒間隔でGemini/Claude APIを呼び出し「強気/弱気/中立」を取得
- 既存テクニカル指標シグナルと組み合わせて最終エントリー判断
- LLM推論遅延（200-2000ms）のため高頻度取引には不適、スイングトレードに適用

現在のFX自動取引システムにLLMセンチメントフィルターを追加する場合の実装参考として活用。

#### 4-2. ライブトレードベンチマークの参照
**出典:** articles/2026-03-28_164_AI_Trader_HKUDS_Live_Benchmark.md

**提案内容:**
HKUDSのAI-Traderプロジェクト（ai4trade.ai）がLLMトレーディングエージェントのライブ取引成績を公開中。バックテストではなく実環境での実績データとして参照し、自社システムのベンチマーク比較に活用できる。


---

## 2026-03-29 収集分

### 1. CLAUDE.md への反映提案

#### 1-1. CLAUDE.mdの指示数上限の明示
**出典:** articles/2026-03-29_182_claude_code_best_practices_zenn.md / articles/2026-03-29_187_claude_md_best_practices_qiita.md

**提案内容:**
フロンティアLLMが確実に従える指示数の上限は150〜200。Claude Codeのシステムプロンプトで約50を消費するため、CLAUDE.mdで使える実質枠は100〜150。「指示を追加するより削除する」原則をCLAUDE.mdの運用ガイドラインに明記する。セクションごとに指示数をカウントする習慣を推奨。

#### 1-2. Plan Modeワークフローの標準化
**出典:** articles/2026-03-29_180_claude_code_tips_trigger_dev.md

**提案内容:**
`Shift+Tab`でPlan Mode（読み取り専用）に移行→人間が計画承認→実装というワークフローを、大規模変更時の標準フローとしてCLAUDE.mdに明記。誤った方向での実装を防ぎ、コンテキスト消費を節約できる。`Double Esc`（巻き戻しメニュー）の活用もセットで記載推奨。

### 2. skills-registry への反映提案

#### 2-1. セキュリティレビュースキルの追加
**出典:** articles/2026-03-29_205_claude_code_10_must_have_skills.md

**提案内容:**
2026年推奨スキルとして`security-review`（依存関係スキャン・脆弱性検出）・`code-review`（PR diff分析）・`docs-sync`（コードとドキュメントの同期チェック）が挙げられている。特に`security-review`スキルはOSSプロジェクトでの実績が多く、skills-registryへの追加を検討。

### 3. MCPセキュリティ対応

#### 3-1. MCPサーバーのシャドーIT化リスク対策
**出典:** articles/2026-03-29_206_mcp_shadow_it_security.md

**提案内容:**
MCPサーバーはローカルホストバインド・ランダム高ポート・開発ツール内部組み込みにより、従来のIT可視化ツールで検出困難。企業でMCPを利用する際は①使用中のMCPサーバーを一覧管理するリスト、②最小権限原則（必要なツールのみ公開）、③定期的なMCPサーバー棚卸しの仕組みが必要。

### 4. FX自動取引システムへの反映提案

#### 4-3. MCP経由コード実行によるバックテスト自動化
**出典:** articles/2026-03-29_215_anthropic_mcp_code_execution.md

**提案内容:**
AnthropicエンジニアリングブログによるMCP経由コード実行機能（WebSearch/WebFetchとの組み合わせで無料提供）。FX自動取引システムのバックテストをMCPサーバー経由でClaude Codeから直接実行できる可能性がある。サンドボックス化・リソース制限の課題はあるが、実験的な実装を検討する価値あり。

---

## 2026-03-30 収集分

### 1. CLAUDE.md への反映提案

#### 1-1. Timestamp付き指示の追加
**出典:** articles/2026-03-30_232_claude_code_best_practices_7_real_projects_eesel.md

**提案内容:**
CLAUDE.md の各セクション冒頭に「最終更新：YYYY-MM」のTimestampを追加する。Claudeに時間的コンテキストを与え、陳腐化した指示を認識させ、定期レビュー時の変化点の特定が容易になる。

#### 1-2. CLAUDE.md の定期セルフレビュー手順を追加
**出典:** articles/2026-03-30_232_claude_code_best_practices_7_real_projects_eesel.md

**提案内容:**
数週間ごとに「このCLAUDE.mdを読んで冗長・矛盾・陳腐化した指示を提案してください」とClaudeに依頼するレビューサイクルを確立する。CLAUDE.md自体にこの手順（例：`/review-claude-md`スキル）を記述しておくと忘れ防止になる。

#### 1-3. /loop コマンドの活用例をCLAUDE.mdに追加
**出典:** articles/2026-03-30_216_claude_code_loop_command_recurring_tasks.md

**提案内容:**
このリポジトリで有効な `/loop` の使い方として「デプロイ状態監視（hourly）」「PRレビュー待ちチェック（daily）」などをCLAUDE.mdに記載する。推奨インターバルは毎時以上とし、コスト見積もり（`/cost`で1サイクル計測してから設定）の手順も添える。

### 2. skills-registry への反映提案

#### 2-1. /simplify スキルの導入検討
**出典:** articles/2026-03-30_233_claude_code_skills_ecosystem_design_corpwaters.md

**提案内容:**
Anthropic公式の `/simplify` スキル（コード変更後に3並行エージェントで自動コードレビュー＋修正）を導入する。実装後のコード品質向上に直結し、手動コードレビューコストを削減できる。インストール：`~/.claude/skills/simplify/` にSKILL.mdを配置。

#### 2-2. スキルdescription設計の標準を確立
**出典:** articles/2026-03-30_227_build_claude_code_skill_freecodecamp_tutorial.md / articles/2026-03-30_233_claude_code_skills_ecosystem_design_corpwaters.md

**提案内容:**
既存スキルのdescription が曖昧な場合は「動詞＋具体的ユースケース」パターンに統一する（例：「×コードを改善する」→「○コード変更後に品質・効率・再利用性を自動レビューして修正する」）。発火率の改善が期待できる。

### 3. FX自動取引システムへの反映提案

#### 3-1. MT5 × Claude Agent SDK 統合アーキテクチャの検討
**出典:** articles/2026-03-30_237_mt5_llm_integration_webhook_trading_2026.md / articles/2026-03-30_220_claude_agent_sdk_custom_agents_2026.md

**提案内容:**
MT5 EA（実行のみ・トレードロジックゼロ）＋ローカルPythonサーバー（Claude Agent SDK）＋MQL5 Webhookのアーキテクチャが実証済みの設計パターンとして確立されている。Claude Agent SDK（2026年3月27日リリース）を使えばClaude Codeと同じエージェントループをPythonで制御できるため、FX戦略判断レイヤーをClaude Agent SDKで実装する選択肢が現実的になった。

#### 3-2. 2段階判断ロジックの採用
**出典:** articles/2026-03-30_237_mt5_llm_integration_webhook_trading_2026.md

**提案内容:**
LLMベースFX取引において「①取引するか否か（IF）を先に判断→②どのように取引するか（HOW）を決定」という2段階判断ロジックが有効とされる。過剰取引リスクを抑えるフィルタリング層として機能し、単純なOHLCデータ入力によるシグナル生成よりも精度が改善される可能性がある。

#### 3-3. /loop を使った定期的な市場モニタリング
**出典:** articles/2026-03-30_216_claude_code_loop_command_recurring_tasks.md

**提案内容:**
FX自動売買の補助ツールとして `/loop` コマンドを活用し、定期的な市場状況サマリー生成やポジション確認を自動化できる。コスト管理に注意しつつ、hourlyインターバルでの使用が現実的。

#### 4-4. AI金融サービス活用の定量指標
**出典:** articles/2026-03-29_211_nvidia_ai_financial_services_2026.md

**提案内容:**
NVIDIA調査（800名以上の金融業界関係者）：89%がAI活用で年間収益増加またはコスト削減を実現。AI積極活用企業は65%（前年比+15%）。アルゴリズム取引市場は2026年に$250億規模（CAGR 14.4%）。FX自動取引システムの事業計画・説明資料に活用できる定量ベンチマーク。

---

## 2026-04-01 収集分

### 1. CLAUDE.md への反映提案

#### 1-1. Auto Modeの推論非参照設計をセキュリティフック設計の参考に
**出典:** articles/2026-04-01_239_claude_code_auto_mode_official_anthropic.md / articles/2026-04-01_250_claude_code_auto_mode_thezvi_deep_analysis.md

**提案内容:**
Auto Modeの分類器は「Claudeのメッセージ・思考チェーンを参照しない」推論非参照設計を採用している。これはClaudeが分類器を論理的に説得してアクション承認を通すことを防ぐためのセキュリティ設計パターン。CLAUDE.mdの安全指示設計において「なぜこのルールが存在するか」の理由をClaudeに見せすぎると、回避策を生み出すリスクがある。重要なセキュリティ制約はhookで実装し、理由付けの可視性を意図的に制限する設計が推奨される。

#### 1-2. --bare フラグ活用による自動化スクリプトの高速化
**出典:** articles/2026-04-01_253_claude_code_auto_mode_60prompts_complete_setup.md

**提案内容:**
`claude --bare -p` パターンはhook/LSP/プラグイン同期/スキルディレクトリウォークを省略し、APIリクエストまでの速度を~14%改善する。CLAUDE.mdに「ヘッドレス実行時のデフォルトフラグ」として `--bare` の使用を明記しておくと、自動化スクリプト実装時の参照コストが下がる。

### 2. skills-registry への反映提案

#### 2-1. Channels権限リレーを活用したリモート承認スキルの設計
**出典:** articles/2026-04-01_240_claude_code_auto_mode_channels_desktop_control_analysis.md / articles/2026-04-01_015_claude_code_channels_setup_60prompts_sidsaladi.md

**提案内容:**
Channels機能（Telegram/Discord経由の権限リレー）を活用し、Claude Codeが本番環境への書き込みや削除操作の承認プロンプトで停止した際にスマートフォンから承認/拒否できるワークフローを構築できる。`disable-model-invocation: true`（手動起動スキル）として設計し、本番系操作の承認フローを`.claude/skills/prod-approval/SKILL.md`にまとめることで、誤操作防止と可読性を両立できる。

### 3. FX自動取引システムへの反映提案

#### 3-1. Channels機能を使ったFXトレードシグナル通知・承認フローの構築
**出典:** articles/2026-04-01_241_claude_code_march_2026_automode_channels_geeky_gadgets.md / articles/2026-04-01_008_claude_code_channels_usage_x2_serverworks_ja.md

**提案内容:**
Channels機能（MCPサーバーとして実装）を使い、FX自動取引システムのトレードシグナルをTelegram/Discordへリアルタイム通知する仕組みが構築できる。Claude Codeセッションが市場データを監視しシグナルを検出→Channels経由でスマートフォンに通知→人間がTelegramで承認（permission relay）→実際にMT5の注文を実行、というSEMI自動化フローが実現可能。完全自動化に踏み切る前の段階的なリスク管理として有効。

#### 3-2. マルチエージェントFX取引システムの設計知見（3ヶ月実験から）
**出典:** articles/2026-04-01_248_ai_trading_agent_3months_experiment_quantitative.md

**提案内容:**
3ヶ月実運用実験から得られた実装指針：(1)LLMトレーディングは高頻度取引（HFT）には不向き（推論レイテンシが障壁）→中長期判断に特化する設計が有効。(2)テクニカル分析・センチメント分析・ニュース分析を分業する複数LLMエージェント協調が単一エージェントよりSharpe比が高い→現行FXシステムにエージェント分業レイヤーを追加する価値あり。(3)Chain-of-Thoughtにより「なぜそのトレードをしたか」をログ記録→事後分析・改善サイクルの基盤として活用可能。(4)階層型メモリ（FinMem型）によるトレード記憶の蓄積がシステム改善に寄与。

#### 3-3. MCP Agent-to-Agent Communication（Q3 2026）への備え
**出典:** articles/2026-04-01_242_mcp_2026_roadmap_production_gaps_newstack.md

**提案内容:**
MCP Roadmapの優先領域3（Q3 2026）でエージェント間呼び出し（Agent-to-Agent Communication）が実装予定。一方のエージェントが他方をMCPツールサーバーとして呼び出す階層アーキテクチャが標準化される。FX取引システムへの影響：オーケストレーターエージェント（全体戦略）→サブエージェント（テクニカル分析担当/センチメント分析担当/リスク管理担当）という明示的な分業アーキテクチャをMCP標準で実装できるようになる。Q3 2026に向けた設計準備として、サブエージェントのAPI境界を今から意識した設計が推奨される。
---

## 2026-04-07 収集分

### 1. Hooks設計への反映提案

#### 1-1. PreToolUseフックへの「defer」第3選択肢の活用
**出典:** articles/2026-04-07_180_Claude_Code_April_2026_Update_powerup_MCP500K.md

**提案内容:**
Claude Code v2.1.89でPreToolUseフックに「defer」選択肢が追加された（allow/deny/deferの3択）。「defer」はツール実行を一時停止し、外部シグナルが届くまで待機する。これにより以下のパターンが実現可能に：
- FX自動取引で「本番取引前に人間の承認を待つ」フローを実装
- Slack/Telegram経由でモバイルから承認する自動化ワークフロー
- 高リスク操作（mainnetへの注文送信等）へのゲートキーパー実装

Hooksのdeferパターンを本プロジェクトのFX自動取引システムの「確認フロー」に組み込むことを検討する。

---

### 2. スキル設計への反映提案

#### 2-1. 全スキルにGotchasセクション追加（SIOS テンプレートパターン）
**出典:** articles/2026-04-07_188_Claude_Code_Skills_Template_SIOS.md / articles/2026-04-07_187_Claude_Code_Skills_Complete_Guide_Nexa.md

**提案内容:**
Anthropic社内ガイドラインに倣い、すべてのSKILL.mdに`## Gotchas`セクションを追加する。記述内容：
- スキルが誤発火・未発火する典型的な状況
- よくあるエラーパターンと対処法
- 初回実行時の注意点

既存の全スキルファイルを見直し、Gotchasセクションを追記することで自動発動の信頼性が向上する。

#### 2-2. SKILL.md descriptionに「スキルが発火しない状況」を明記
**出典:** articles/2026-04-07_182_MCP_vs_Skills_vs_Hooks_Which_Extension_DEV.md

**提案内容:**
3層モデルの明確化に伴い、各スキルのdescriptionに「このスキルが使われるべき状況」だけでなく「このスキルを使うべきでない状況」も記述する。Claude はすべてのスキルのdescriptionを読んでどれをロードするか判断するため、否定条件の明示が誤発動を防ぐ。

---

### 3. FX自動取引システムへの反映提案

#### 3-1. docs/STATUS.md による長期セッション状態管理パターン
**出典:** articles/2026-04-07_195_Claude_Code_Trading_Bot_961_Calls_Case_Study.md

**提案内容:**
14セッション・961ツール呼び出しのトレーディングボット構築ケーススタディから得た重要知見：
`docs/STATUS.md` に以下を継続的に書き込むことでセッション断絶からの高速復帰が可能：
- 現在の実装状況
- 完了済みタスク・次のタスク
- 重要な設計決定と理由
- 未解決の問題

FX自動取引プロジェクトの長期開発セッションにこのパターンを導入する。既存の `docs/` ディレクトリに `STATUS.md` を作成し、Claude Codeが毎回セッション開始時に読み込むよう CLAUDE.md に追記する。

#### 3-2. aiomqlによる非同期MT5接続の採用検討
**出典:** articles/2026-04-07_197_aiomql_MT5_Async_Python_Trading_Guide.md

**提案内容:**
aiomqlフレームワーク（MT5をasyncioでラップ）を検討する。現在の実装が同期的なら、複数シンボル同時監視・バックテスト並列実行において非同期化で大幅な性能改善が見込める。具体的には：
- Strategy基底クラスを継承して戦略を独立したコルーチンとして定義
- RAM（リスク・資金管理）モジュールで複数戦略間のリスクを一元管理
- MT5 EA側は軽量な「ローカルアプリのポーリング器」に限定

#### 3-3. LLM推論レイテンシの制約確認（1時間足以上を推奨）
**出典:** articles/2026-04-07_198_AI_Trading_Agent_3months_Monitoring_Medium.md

**提案内容:**
3か月間のAIトレーディングエージェント追跡実験から、LLM推論レイテンシ（200〜2000ms）により高頻度取引は不適であることが定量的に確認された。現在のFX自動取引プロジェクトの設計方針確認：
- **推奨**: 1時間足・4時間足・日足の中低頻度戦略
- **非推奨**: 1分足・5分足（LLMセンチメント判断では遅延が致命的）
- LLMは「完全自律判断」ではなく「センチメントフィルター（60秒以上の間隔）」として使用する現在の方針を維持

---

## 2026-04-08 収集分

### 1. APIへの緊急対応事項

#### 1-1. 【緊急】Claude Sonnet 4.5/4の1Mトークンβが2026年4月30日廃止
**出典:** articles/2026-04-08_013_Anthropic_API_2026_Guide_MarketingScoop.md

**提案内容:**
`context-1m-2025-08-07`ベータヘッダーによる100万トークンコンテキストが2026年4月30日に廃止される。FX自動取引システムやClaude Agent SDK経由で`context-1m`ヘッダーを使用している場合は、Sonnet 4.6（1Mネイティブ対応）への移行または128Kコンテキスト設計への変更が必要。**期限: 2026-04-30。**

---

### 2. CLAUDE.md / スキル設計への反映提案

#### 2-1. CLAUDE.md advisory（80%）vs. Hooks deterministic（100%）の三層ガイドを強化
**出典:** articles/2026-04-08_005_Claude_Code_Best_Practices_SkillsPlayground.md / articles/2026-04-08_004_Claude_Code_50_Tips_GeekyGadgets.md

**提案内容:**
複数の独立した記事が「CLAUDE.md遵守率約80%、Hooks100%」を確認した。スキルが一覧に揃ってきた今、各スキルのSKILL.mdに「このルールはHookで強制されている場合はスキル側の記述を削除」という注記を加え、三層（CLAUDE.md/Skills/Hooks）の役割分担を明確化する。特に副作用のあるワークフロー（コミット・PR・本番デプロイ）は`disable-model-invocation: true`+手動起動スキルとして整理する。

#### 2-2. CLAUDE.mdの「削除テスト」定期実施
**出典:** articles/2026-04-08_005_Claude_Code_Best_Practices_SkillsPlayground.md / articles/2026-04-08_003_Claude_Code_10_Productivity_Tips_F22Labs.md

**提案内容:**
「この行を削除するとClaudeが間違いを犯すか？」テストをCLAUDE.mdの定期メンテナンス時（月1回）に全行に対して実施する。Claudeが既にデフォルトで正しくやることは書かない。フィードバックループとして、Claudeがミスした際はその場でCLAUDE.mdにルールを追記してから次のセッションに進む習慣を確立する。

---

### 3. MCP設定への反映提案

#### 3-1. MCP v2.1.91 500K文字上限に設定更新
**出典:** articles/2026-04-08_007_Claude_Code_MCP_Integration_Markaicode.md / articles/2026-04-08_025_Releasebot_Anthropic_April2026_All_Updates.md

**提案内容:**
Claude Code v2.1.91でMCPツール結果サイズ上限が500,000文字に拡張された。FX自動取引で市場データ・ニュースフィードをMCP経由で取得する際、大量のデータをMCPサーバーから一括返却できるようになった。必要に応じてMCPサーバーのレスポンスサイズ上限設定を見直す（旧デフォルトは制限的だったため）。

#### 3-2. MCPサーバー認証の本番実装指針
**出典:** articles/2026-04-08_008_MCP_Auth_Claude_Code_TrueFoundry.md

**提案内容:**
FX自動取引のMCPサーバー（市場データ取得・MT5連携）で認証が必要な場合、シークレットはCLAUDE.mdに書かず環境変数（`.env`）で管理する。HTTP transport使用時のOAuth 2.0 / APIキー認証フローをドキュメント化し、`~/.claude/settings.json`のMCPサーバー設定とは切り離して管理する。

---

### 4. FX自動取引システムへの反映提案

#### 4-1. LLM×マクロシグナル合議制アーキテクチャの採用検討
**出典:** articles/2026-04-08_015_LLM_Macro_Signal_Trading_System_Design_JA.md / articles/2026-04-08_016_TradingAgents_MultiAgent_LLM_Framework_AIToolly.md

**提案内容:**
複数のLLMエージェントがBull/Bear立場から議論して最終判断を下す「合議制（Consensus-based）」アーキテクチャが、単一LLMの確証バイアスを避ける有効な設計パターンとして実証されている（TradingAgents: 7エージェント協調）。現行FXシステムへの適用案：
- 強気エージェント（テクニカル分析担当） vs. 弱気エージェント（マクロリスク担当）が議論
- リスク管理エージェントが最終ポジションサイズを決定
- MCP経由で金利・CPI・雇用統計をリアルタイム取得してファンダメンタルズ判断に活用

#### 4-2. Claude + MT5 LLM判定実験の知見活用
**出典:** articles/2026-04-08_023_AI_LLM_Stock_Trading_Experiment_Report_JA.md

**提案内容:**
AI Native JPの実験報告から現実的な課題が整理されている：
- 推論コスト・レイテンシ：Claude APIコールを1判断あたりの最小化設計（バッチ処理・キャッシュ活用）
- 過学習対策：バックテスト期間のサンプル外（OOS）検証を必須化
- ハルシネーション対策：「買い/売り/静観」の3択回答フォーマットを強制、自由記述を排除
- マルチモーダル活用：チャート画像をClaude Visionに渡したテクニカル分析の精度検証

---
---

## 2026-05-09 収集分

### 1. FX自動取引システムへの反映提案

#### 1-1. OSS マルチエージェント取引フレームワーク参照実装
**出典:** articles/2026-05-09_1623_X_gaoren7716_QuantDinger (GitHub ⭐4k) / articles/2026-05-09_1624_X_gaoren7716_Vibe-Trading (GitHub ⭐6.2k)

**提案内容:**
QuantDinger（4k stars）とVibe-Trading（HKU・29エージェント・6.2k stars）は、今週X上でバズった OSS マルチエージェント定量取引フレームワーク。sandbox/FX自動取引/ のリファレンスとして調査対象に追加する。特に Vibe-Trading の29エージェント構成（ファンダメンタルズ・テクニカル・センチメント・リスク等）は TradingAgents と競合するアーキテクチャ比較として有益。

#### 1-2. Claude Code+MCP+OpenRouter取引自動化パイプライン
**出典:** articles/2026-05-09_1627_X_LaboNft_Claude_Code+MCP+OpenRouterによるAI取引自動化パイプライン

**提案内容:**
Claude Code × MCP × OpenRouter を組み合わせたAI取引自動化パイプラインの実装事例。sandbox/FX自動取引/ の主制御エージェントとして Claude Code を使いつつ、OpenRouter 経由でコスト最適化する設計パターンとして参照する。

### 2. Claude Code設定への反映提案

#### 2-1. レート制限2倍化（SpaceX提携）の活用
**出典:** articles/2026-05-09_1617_X_latdayo_Anthropic×SpaceX / articles/2026-05-09_1650_WEB_Mythos_Anthropic_SpaceX

**提案内容:**
AnthropicがSpaceXの22万GPU・300MWを借り受け、Claude Codeのレート制限を2倍に拡大。Pro/Max/Teamプランで長期セッションやバックグラウンドエージェントを以前より多く走らせることが可能になった。CLAUDE.mdの「コスト管理」セクションに制限2倍の旨を記載し、並列サブエージェント数の推奨値を見直す。

#### 2-2. PDF-MCP サーバーの導入検討
**出典:** articles/2026-05-09_1646_WEB_GitHub_jztan_pdf-mcp

**提案内容:**
大規模PDFをコンテキスト制限に引っかからず読み込めるMCPサーバー（chunked reading・ハイブリッド検索・OCR・テーブル・画像抽出対応）。研究論文・規制文書・取引マニュアルPDFをClaude Codeから直接参照するワークフローに有用。settings.jsonのMCP設定に追加候補。

### 3. スキル・エコシステムへの反映提案

#### 3-1. Microsoft Waza フレームワークの参照
**出典:** articles/2026-05-09_1631_X_L_go_mrk_Microsoft_Waza / articles/2026-05-09_1669_WEB_The_Future_of_Agentic_AI_Inside_Microsoft_Agent_Framework

**提案内容:**
MicrosoftがリリースしたWazaフレームワークはAIエージェントのSkillsを「作成→テスト→評価」する工程を体系化。Claude CodeのSkills設計・評価方法論と比較し、skills-registryの品質評価基準に取り入れられる要素がある。具体的には：Skillの入力/出力スキーマ検証・ゴールデンテストセット・品質スコアリングの仕組み。

---

## 2026-05-12 収集分

### 1. セキュリティ緊急対応

#### 1-1. 【緊急】CVE-2026-26268：git hookがAIコーディングツールを通じて実行される脆弱性
**出典:** articles/2026-05-12_1832_X_musiol_martin_CVE_2026_26268...

**提案内容:**
リポジトリをクローンしてEnterを押すだけで`.git/hooks/`内の攻撃者仕込みスクリプトが実行されるCVE-2026-26268が報告された。Claude Code・Gemini CLI・GitHub Copilotの全てで同形状の脆弱性が確認済み。対応策：
- `--no-local-hooks`相当の設定確認またはgit cloneの事前フック無効化
- 信頼できないリポジトリのクローン時は`GIT_ALLOW_PROTOCOL`制限を使用
- CLAUDE.mdに「untrustedリポジトリのクローン前は .git/hooks/ を確認する」ルールを追加

#### 1-2. 【緊急】npmサプライチェーン攻撃：TanStack・Mistral AI・UiPath等が被害
**出典:** articles/2026-05-12_1859_X_notjazii_npmサプライチェーン攻撃...

**提案内容:**
主要npmパッケージ（TanStack・Mistral AI SDK・UiPath・OpenSearch）が侵害されたサプライチェーン攻撃が確認。Claude Agent SDK等のAnthropicパッケージの更新時は公式Githubのrelease hashと照合する習慣を確立する。特にMistral AIのSDKが被害を受けたため、multi-LLM構成のFX取引システムでMistral APIを使用している場合は依存関係バージョンの固定・検証を実施。

---

### 2. Claude Code設定への反映提案

#### 2-1. Fast mode Opus 4.7 対応：/fastコマンドと2.5倍速の活用
**出典:** articles/2026-05-12_1841_X_nukonuko_Claude_Code_Fast_modeがOpus_4_7対応...

**提案内容:**
Claude Code Fast modeがOpus 4.7でも利用可能になった（2.5倍高速化、$30/$150 per MTok）。`/fast`コマンドで切り替え可能、または環境変数`CLAUDE_CODE_ENABLE_OPUS_4_7_FAST_MODE=1`で有効化。CLAUDE.mdまたはsettings.jsonに以下を追加検討：
- 長時間バックグラウンドエージェントにはFast modeを使い、コスト・速度を最適化
- Cursor・WindsurfからAPI経由で使用する場合はbeta登録要（zylos.ai/research参照）

#### 2-2. Claude Architect Certification取得の検討
**出典:** articles/2026-05-12_1844_X_smratitiwa86867_Claude_Architect_Certification...

**提案内容:**
AnthropicがClaude Architect Certificationを発表（60問・5分野・一発勝負）。Claude Code・Agent SDK・Managed Agentsを本格活用するエンジニアの専門性証明手段として注目。スキルセットの公式認証として、チームメンバーの学習目標として設定する価値がある。

---

### 3. スキル設計への反映提案

#### 3-1. Claude Design ↔ Claude Code Bridge Skillの作成
**出典:** articles/2026-05-12_1834_X_anajuliabit_Claude_DesignとClaude_Codeを繋ぐSkillを自作...

**提案内容:**
AnthropicのClaude DesignとClaude Codeが独立しており相互連携しない問題を解決するBridge Skillが公開された。Claude Designからのデザイントークン・UIコンポーネント仕様をClaude Codeが直接読み込んで実装するワークフローを実現。参考として公開Skillのソースコードを調査し、UIコンポーネント開発ワークフローへの導入を検討する。

#### 3-2. review skillへのpersona sub-agent手法の適用
**出典:** articles/2026-05-12_1835_X_Kev_InDev_review_skillでpersonaごとのsub_agentを実行...

**提案内容:**
review skillの中でレビュー視点をpersonaとして定義し（セキュリティ専門家・パフォーマンスエンジニア・可読性レビュアー等）、Claude Codeにそのpersonaごとのサブエージェントを並列実行させる手法。FX取引システムのコードレビューに適用する場合：「セキュリティ（APIキー漏洩・注文送信エラー）」「パフォーマンス（レイテンシ最適化）」「ビジネスロジック（取引ロジックの整合性）」の3ペルソナでレビューする仕組みを構築できる。

#### 3-3. marketing-skills（マーケティング業務特化スキル集）の参照
**出典:** articles/2026-05-12_1861_X_L_go_mrk_marketing_skills...

**提案内容:**
LP作成→A/Bテスト→SEO→CRO→メール自動化を一括処理するmarketing-skillsが公開。skills-registryのマーケティング・コンテンツ作成カテゴリに追加候補。スキル構造（複数の専門スキルをオーケストレーションする設計）はFX取引システムの複数エージェント協調パターンの参考にもなる。

---

### 4. FX自動取引システムへの反映提案

#### 4-1. ハイブリッドAI取引システム（135%リターン/24ヶ月）のアーキテクチャ参照
**出典:** articles/2026-05-12_1867_WEB_ハイブリッドAI駆動取引システム_テクニカル_ML_センチメントの体制適応型戦略.md

**提案内容:**
ComSIA 2026（Springer LNNS）採択論文。テクニカル指標（トレンドフォロー・モメンタム）＋平均回帰＋FinBERTセンチメント分析＋XGBoostシグナル生成＋市場レジームフィルタリングのハイブリッドフレームワークが24ヶ月で+135.49%を達成（S&P500・NASDAQ-100を上回る）。現行FXシステムへの適用検討：
- Dual-agent DRL（強気・弱気）が動的に市場レジームを判断して戦略を切り替える設計
- FinBERTの代わりにClaude APIによる日本語FXニュースのセンチメント分析
- XGBoostの役割をLLM推論に置き換えることによる精度比較実験

#### 4-2. TraderClaw（OpenClaw上の自律AIトレーディングエージェント）の調査
**出典:** articles/2026-05-12_1845_X_MCGlive_TraderClaw_OpenClawベースの完全自律AIトレーディングエージェ.md

**提案内容:**
OpenClawフレームワーク（210K GitHub stars）上に構築されたTraderClawが公開。完全自律で相場を監視・取引するエージェント。OpenClawはSam Altmanが公的支持を表明した注目フレームワークで、Claude Agent SDKとの比較対象として有益。sandbox/FX自動取引/のリファレンス実装として調査対象に追加。

---

### 5. AI規制・コンプライアンス動向

#### 5-1. EU AI Act：2026年8月2日コンプライアンス期限への対応確認
**出典:** articles/2026-05-12_1862_WEB_EU_AI_Act__欧州委員会_AIの透明性に関するドラフトガイドライン_10の要点.md

**提案内容:**
EU AI ActのAI Omnibus改正が5月7日に議会合意し、8月2日が主要コンプライアンス期限として確定。2026年12月2日までにAI生成コンテンツの透明性ソリューション実装が必要（猶予期間が6ヶ月→3ヶ月に短縮）。Claude APIを使用したサービスで欧州ユーザーに展開する場合は合成コンテンツのラベリング要件を確認する必要がある。SMCへの規制例外拡大は中規模企業（従業員250-750名）に適用。

---

## 2026-05-14 収集分

### 6. Claude Agent SDK・FX自動取引への反映提案

#### 6-1. Agent SDK課金分離（6月15日）へのFX自動取引プロジェクト対応
**出典:** articles/2026-05-14_2082_WEB_Anthropic_Agent_SDK_課金分離_6月15日_Pro20ドル_Max200ドル.md

**提案内容:**
2026年6月15日より `claude -p`・Claude Agent SDK・GitHub Actionsがサブスク使用枠から切り離され、月額クレジット制（Pro $20、Max 20x $200）へ移行する。FX自動取引プロジェクトでClaude APIをプログラム的に呼び出している場合は以下を確認すること：
- `sandbox/FX自動取引/main.py` でのAPI呼び出し方式（claude -p 経由か直接APIか）を確認し、6月15日以降のコスト影響を試算する
- 月次クレジット超過時の動作（停止 or 従量課金）を設定しておく
- 初回のオプトイン登録（1回限り）を忘れずに実施

#### 6-2. SKILL.mdのdescriptionフィールド最適化
**出典:** articles/2026-05-14_2065_*（ar-aca.tech SKILL.mdガイド）

**提案内容:**
Claude Codeのスキルトリガー判定はname + descriptionのみで行われる（本文は必要時のみロード）。既存のSKILL.mdを見直し、descriptionを最大200文字でトリガー条件を具体的に記述する。特に日次キュレーションスキル（`/curate`）のdescriptionが曖昧な場合、自動トリガーされないリスクがある。推奨フォーマット：「いつ使うか + 何をするか + 前提条件」を200文字以内で記述。

#### 6-3. 自然言語→ブローカーAPI実行パターン（Moomoo API Skill参考）
**出典:** articles/2026-05-14_2157_WEB_moomoo_APIスキル_チャットのみで米国株自動売買_日本初_PRTimes.md

**提案内容:**
moomoo証券が「自然言語→コード生成→バックテスト→注文執行」のパイプラインをClaude Codeスキルで実現。FX自動取引プロジェクトでも同様のアーキテクチャが応用可能：
- MT5 Python APIとClaude Codeスキルを組み合わせ、自然言語でEA（Expert Advisor）を生成・バックテストするスキルを作成する
- `sandbox/FX自動取引/main.py` をベースに、スキル化のための SKILL.md を設計する

---

## 2026-05-15 収集分

### 1. FX自動取引プロジェクトへの反映提案

#### 1-1. Claude Agent SDK 課金変更対応（緊急: 6月15日期限）
**出典:** articles/2026-05-15_2222_Anthropic_Agent_SDK_課金分離... / articles/2026-05-15_2223_AgentSDK_June15...

**提案内容:**
2026年6月15日から Agent SDK・claude -p コマンドの課金が分離される。
FX自動取引で claude -p や Agent SDK を使っているスクリプトがあれば、今月中にクレジット消費量を試算し、上限設定を追加すること。

対応アクション:
- `claude mcp list` で依存を確認
- 月間トークン消費量を計測（Pro枠: $20/月）
- クレジット枯渇時のフォールバック処理を実装

#### 1-2. FreqtradeとClaude Code連携パターンの採用検討
**出典:** articles/2026-05-15_2185_FreqtradeとClaude_Code...

**提案内容:**
@lliu54827の事例: PineScriptで書いた指標をClaude Codeに会話で投げるだけでFreqtrade向け検証が数分で完結。
FX自動取引プロジェクトのバックテスト検証ワークフローにClaude Code統合を検討すべき。

具体的実装例:
```
Claude Code → Freqtrade設定生成 → バックテスト実行 → 結果評価 → 改善提案
```

### 2. Claude Code スキル設計への反映提案

#### 2-1. Codex adversarial-review + Claude Code 相互レビューパターン
**出典:** articles/2026-05-15_2188_codex_adversarial-review...

**提案内容:**
`/codex:adversarial-review`スキルとClaude Codeを組み合わせた相互レビューアーキテクチャが実用化されている。
curate スキルや他の複雑なスキルに品質チェック用の adversarial-review ステップを追加することを検討。

パターン:
1. Claude Codeで実装
2. Codex（adversarial-review）でレビュー
3. Claude Codeで再修正
注意: 800Kトークン上限でのコンテキスト管理が必要。

#### 2-2. ツール非依存スキル設計（Claude Code/Codex共用）
**出典:** articles/2026-05-15_2197_STEP_to_STL変換スキル... / articles/2026-05-15_2194_Claude_Code_CLI_vs_Codex_CLI...

**提案内容:**
Claude CodeとCodexはスキル名・ショートカット・built-inに差異があるが、SKILL.mdのコアロジックは両者で共用できる。
既存スキルを「エージェント非依存」設計にリファクタリングし、どちらのCLIからも呼び出せるようにすることで保守性が向上する。

### 3. CLAUDE.md への反映提案

#### 3-1. /goal コマンドの活用をCLAUDE.mdに記載
**出典:** articles/2026-05-15_2190_Claude_Code_macOS__goal__loop...

**提案内容:**
Claude Code macOSで /goal と /loop コマンドが利用可能になった。
CLAUDE.mdに「長期タスクは /goal で完了条件を設定してから開始する」というワークフロー指針を追加することで、途中中断リスクを減らせる。

#### 3-2. Agent Viewを使ったマルチセッション管理の標準化
**出典:** articles/2026-05-15_2186_Claude_Code_Agent_View... / articles/2026-05-15_2001_...

**提案内容:**
Agent View（全セッション一覧UI）が利用可能になり、並列エージェント管理が実用的になった。
大規模タスクを複数のサブタスクに分割してAgent Viewで管理する運用パターンをCLAUDE.mdに記載することを検討。


---

## 2026-05-16 収集分

### 1. CLAUDE.md への反映提案

#### 1-1. Agent SDK Billing変更（6月15日）の運用ルール追記
**出典:** articles/2026-05-16_2241〜2246（Anthropic Agent SDK課金分離）

**提案内容:**
6月15日以降のclaude -p / GitHub Actions / OpenClaw等サードパーティエージェントはAgent SDKクレジットから消費される（Pro $20・Max 5x $100・Max 20x $200/月・繰り越し不可）。CLAUDE.mdに以下を追記：

```markdown
## Agent SDK利用ポリシー（2026年6月15日以降）
- claude -pはAgent SDKクレジット（$X/月）から消費
- デフォルトモデル: Haiku 4.5（コスト最適化）
- 高品質タスクのみOpus 4.7を使用
- プロンプトキャッシュ最大化（system prompt固定化）
- 月次利用量は claude.ai → 設定 → Agent SDK で確認
```

#### 1-2. CLAUDE.md ブロート防止ルールの強化
**出典:** articles/2026-05-16_2236（CLAUDE.md 9 Rules）、2235（Self-Learning Hook実践）

**提案内容:**
Self-Learning Hook（セッション終了後にCLAUDE.mdへ自動追記）を導入すると3ヶ月で600行超になる事例がある。現在のCLAUDE.mdに「月1回のトリミングルール」を追加し、不要になったルールの削除を明示的に運用化する。

---

### 2. スキル設計への反映提案

#### 2-1. Claude Code Pluginsエコシステムの調査・対応
**出典:** articles/2026-05-16_2237〜2239（Claude Code Plugins 9000+）

**提案内容:**
2026年2月時点で9,000+プラグインが存在するが本当に使えるのは50-100本。以下のプラグインを試験導入すべきか検討：
- `security-auditor`: OWASP準拠の脆弱性スキャン（サブエージェント型）
- `test-runner`: テスト生成・実行・失敗分析の自動化
- `ralph-loop`: 長時間タスクの自動継続（daily収集ループに有用）

インストール: `/plugin install [name]@claude-plugins-official`

#### 2-2. MCP vs Skills vs Hooks の選択基準をスキルドキュメント化
**出典:** articles/2026-05-16_2239（Geeky Gadgets選択ガイド）

**提案内容:**
現在のスキルは「何をするか」の説明はあるが「なぜMCPではなくSkillか」の理由がない。各スキルのヘッダーに以下を追記：

```markdown
<!-- 拡張ポイント選択理由: Skills（定型フロー・モデル主導）vs MCP（外部データ接続）vs Hooks（強制実行） -->
```

---

### 3. FX自動取引への反映提案

#### 3-1. MT5 AI EAの動向把握とコードパターン調査
**出典:** 今回収集x/ai-trading SIGNAL記事

**提案内容:**
今回のX収集でMT5向けAI搭載EAの具体的な実装パターンが複数確認された：
- **AIへの1行指示でMT5 EAコード生成パターン**：自然言語→MQL5コード変換フロー
- **GPTでMT5バックテスト結果を時間帯別解析**：バックテストCSV→AI解析→戦略最適化
- **WWA概念のEA自動化**：概念→TradingViewインジケーター→MT5 EA化フロー

sandbox/FX自動取引/main.pyにこれらのパターンを実験実装するためのissue/タスクを作成することを提案。

#### 3-2. SageMaster FX方式（自己口座内AI運用）の参考実装調査
**出典:** ai-trading SIGNAL記事（SageMaster FX）

**提案内容:**
「自己口座内でのAI運用プラットフォーム」というアーキテクチャが出現しつつある。外部サービスに資金を預けず、自己ブローカー口座内でAIエージェントが判断・発注する形態。Claude Codeから直接MT5 APIを叩く構成の実現可能性を調査する価値がある。

---

## 2026-05-17 収集分

### 1. Claude Code設定・CLAUDE.mdへの反映提案

#### 1-1. Routines機能・Dreaming processをワークフローに組み込む
**出典:** articles/2026-05-17_2312_WEB_Claude_Code_WhatsNew_Official_May2026.md

**提案内容:**
Routines（スケジュール/GitHub event/API callでテンプレートエージェントを自動起動）とDreaming process（過去セッションをレビューしてパターン抽出・メモリキュレーション）が一般提供開始。CLAUDE.mdに以下を追記する価値がある：
- 日次収集ルーティン（本スクリプト）をRoutinesとして設定し、VPS依存を排除する可能性
- Dreaming processとsandbox/タスクマネージャー/library/のメモリ管理を連携させる実験

#### 1-2. xhigh effortレベルをコスト計画に反映
**出典:** articles/2026-05-17_2312_WEB_Claude_Code_WhatsNew_Official_May2026.md / 2026-05-17_2313

**提案内容:**
Opus 4.7のxhigh effortが「ほとんどのコーディング作業に推奨」として追加された。CLAUDE.mdの「モデル選択ガイドライン」セクションに「複雑なリファクタリング・新機能実装はOpus 4.7 xhigh・ルーティン修正はHaiku 4.5」という使い分け基準を記載すると、claude -p呼び出し時のデフォルトモデル選択の根拠になる。

---

### 2. FX自動取引システムへの反映提案

#### 2-1. TradingAgents + MT5 VPS デプロイメントの実装参照
**出典:** articles/2026-05-17_2320_WEB_TradingAgents_MT5_VPS_Forex_Deployment_LightNode.md / articles/2026-05-17_2321_WEB_TradingAgents_Python_OpenSource_AlgoInsights_Medium.md

**提案内容:**
TradingAgents v0.2.0（pip install tradingagents）+ VPS + MT5 Python APIによる24時間FX自動売買ボット構築チュートリアルが公開された。sandbox/FX自動取引/への直接応用ステップ：
1. `pip install tradingagents` でフレームワークを導入
2. Claude 4.xをLLMプロバイダーとして設定（GPT-5.x代替）
3. 7役割エージェント（ファンダメンタル/センチメント/ニュース/テクニカル/リスク/トレーダー）のロール定義を既存ロジックに合わせてカスタマイズ
4. MT5 Python APIとのブリッジ実装（注文送信のみMT5側）

#### 2-2. MQL × ChatGPT/Claude APIによるFX EA連携パターン
**出典:** articles/2026-05-17_2323_WEB_ChatGPT_FX_EA_Integration_Japan_Sayama.md

**提案内容:**
MQL5コード内でChatGPT/Claude APIを直接呼び出し、売買判断をAIに委ねるテンプレートが日本語で公開された。現行FX自動取引プロジェクトの設計選択として：
- 軽量：MQL5内でHTTP呼び出し（APIキー管理が必要だがEA完結）
- 分離：Python仲介サーバー経由（既存アーキテクチャに適合）
両パターンの比較実験をsandbox/FX自動取引/tests/に追加する価値がある。

#### 2-3. LLM別アルゴトレーディングボット生成能力の定量比較
**出典:** articles/2026-05-17_2322_WEB_LLM_Trading_Bot_Python_Comparison_QuantLabs.md

**提案内容:**
Claude 4.x系がアルゴトレード専門的概念（ボラティリティ調整ポジションサイジング・相関ヘッジ・レジーム検出）において8LLM比較で高評価。FX EA生成・改善のメインLLMとしてClaudeを使う根拠として活用できる。プロンプトキャッシュを活用したコスト最適化（市場データのsystem prompt固定化）と組み合わせること。

---

### 3. MCP設定への反映提案

#### 3-1. 2026年5月最新MCPサーバー選定の反映
**出典:** articles/2026-05-17_2318_WEB_Claude_MCP_15_Servers_Recommendation_2026_Jinrai.md / articles/2026-05-17_2319_WEB_Claude_Code_MCP_15_Servers_May2026_AICareerJapan.md

**提案内容:**
2026年5月時点の新規MCPサーバー（AWS 54本一括・Google Cloud BigQuery/Vertex AI）が追加された。現在の.claude/settings.jsonのmcpServersを見直し、以下を追加候補として検討：
- Exa（AI最適化検索、Brave/Fetchより高品質）
- BigQuery MCP（FXデータ大量処理に有用）
- ant CLI（Claude API CLIクライアント、claudeコマンドとの統合）

---

### 4. AI規制対応

#### 4-1. EU AI Act 2026年8月2日施行の最終確認
**出典:** articles/2026-05-17_2325_WEB_EU_AI_Act_Council_Parliament_Simplify_May2026.md

**提案内容:**
2026年5月7日にEU議会・理事会が合意。8月2日（高リスクAI・透明性ルール施行）と12月2日（AI生成コンテンツ透明性措置、猶予期間3ヶ月）が確定期限。Claude APIを使った欧州向けサービス展開を計画する場合は、これらの期限に合わせた合成コンテンツラベリング実装の準備が必要。

---

## 2026-05-18 収集分

### 1. Claude Code設定への反映提案

#### 1-1. 週間制限50%増（〜7/13）期間の並列エージェント活用拡大
**出典:** articles/2026-05-18_2461_web_Claude_Code_Increases_Weekly_Limits_by_50__Thr.md

**提案内容:**
2026年5月13日〜7月13日の期間限定でClaude Code週間利用制限が50%増加。この期間を活用し、以下の試験的な運用を推奨：
- 日次収集スクリプトのサブエージェント並列数を現在より1〜2増やして実行時間を短縮
- FX自動取引のバックテスト並列化（複数シンボル同時分析）の実験
- CLAUDE.mdの「コスト管理」セクションに7月13日期限の旨を追記して自動的に見直しリマインダーとして機能させる

#### 1-2. Agent View・新フラグ群のワークフロー統合
**出典:** articles/2026-05-18_2463_web_Code_with_Claude_SF_2026_What_Anthropic_Actua.md

**提案内容:**
Code with Claude SF 2026で発表されたAgent View（複数セッションのCLI一画面管理）と新フラグ群（--add-dir, --settings, --model, --effort等）が実用段階に。
- claude agents フラグの--add-dirを使い、FX自動取引のデータディレクトリをサブエージェントに安全に渡す設計を実装
- Mobile Push通知（長時間タスク完了時にスマホ通知）を日次収集スクリプトの完了通知として設定

---

### 2. スキル設計への反映提案

#### 2-1. claude-code-setupプラグインの評価・導入検討
**出典:** articles/2026-05-18_2380_X_ingridiasdesou1_claude_code_setupプラグインの機能紹介.md / articles/2026-05-18_2434_X_ingridiasdesou1_claude_code_setup公式プラグイン機能紹介.md

**提案内容:**
claude-code-setupという公式プラグインがhooks/skills/MCP/subagentsの最適設定を自動推薦する機能を持つ。新規プロジェクト（FX自動取引プロジェクト等）のセットアップ時間短縮に有用な可能性がある。まず`/plugin install claude-code-setup`で試験導入し、推薦結果を既存のCLAUDE.mdと照合して有用な差分があれば取り込む。

#### 2-2. spec.md駆動のアーキテクト→実装ワークフローの標準化
**出典:** articles/2026-05-18_2394_X_username_spec_md駆動のアーキテクトワークフロー実践.md

**提案内容:**
「spec.md（仕様書）をアーキテクト的に書いてからClaude Codeに実装させる」パターンが実践的効果を上げているという報告が複数確認された。FX自動取引プロジェクトの新機能実装フローに導入提案：
1. `docs/spec/FEATURE_NAME.md` に機能仕様を人間が書く（入力・出力・制約・エッジケース）
2. Claude Codeに「spec.mdを読んで実装して」と指示（実装のみ・仕様変更禁止）
3. 完了後spec.mdをdocs/に保存してCLAUDE.mdのリファレンスとして活用

---

### 3. FX自動取引システムへの反映提案

#### 3-1. SMC AI MLモデルの定量指標を参考ベンチマークとして記録
**出典:** articles/2026-05-18_2407_X_username_SMC_AI_FVGリテスト戦略ML_p_0_54_EV__1_41.md / articles/2026-05-18_2410_X_username_SMC_AI_Liquidity_Sweep戦略_p_0_52_EV__0_16.md

**提案内容:**
SMC（スマートマネーコンセプト）AIアカウントがFVGリテスト戦略（ML確率p=0.54・期待値EV=+1.41）とLiquidity Sweep戦略（p=0.52・EV=+0.16）の定量データを継続公開。
- sandbox/FX自動取引/docs/BENCHMARK.md に外部比較ベンチマークとして記録
- 自社実装のML分類モデルとの比較指標として活用（p値・EV・シャープレシオ）
- FVGリテスト戦略はスーパー収益の可能性があるため、TradingAgents実装での優先検証対象とする

#### 3-2. AI Trading Botの「実取引記録の重要性」を戦略評価基準に追加
**出典:** articles/2026-05-18_2406_X_username_AIトレードボット実取引記録の重要性を警告.md / articles/2026-05-18_2454_web_I_Built_an_AI_Trading_Bot_and_Let_It_Trade_for_9_D.md

**提案内容:**
「バックテスト良好≠実取引良好」という警告が複数の独立した情報源から確認された（9日間実験ではバックテスト487%→実運用で大幅乖離）。sandbox/FX自動取引/docs/EVALUATION.md に以下の評価基準を追加：
- バックテスト段階（In-sample / Out-of-sample分割必須）
- フォワードテスト段階（デモ口座30日以上）
- ライブ取引段階（小額から開始・P&Lログ必須）
- 各段階の最低ハードル（シャープ比・最大ドローダウン・勝率）を数値で設定

---

### 4. AI規制対応

#### 4-1. 米国AI規制転換リスクの監視体制確立
**出典:** articles/2026-05-18_2456_web_White_House_Considers_AI_Vetting__Sparks_Tech_In.md / articles/2026-05-18_2459_web_Trump_Administration_Embraces_AI_Oversight_Polici.md

**提案内容:**
トランプ政権がAnthropicのMythosモデルのサイバー能力を懸念し、先進AIモデルへの審査義務化を検討している。EU規制（8月2日・12月2日期限）に加え、米国規制の動向も注視が必要：
- Claude APIを利用したサービスで米国ユーザーに提供している場合、行政命令（Executive Order）の内容を監視
- 特に「サイバーセキュリティ用途への制限」が規制された場合のフォールバックモデル（他プロバイダー・オープンソース）の準備
- Anthropic自身が規制形成プロセスに関与しているため、同社公式ブログの定期確認を推奨

