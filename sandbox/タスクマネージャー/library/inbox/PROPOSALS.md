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


---

## 2026-05-19 収集分

### 1. Claude Code Routinesの日次収集自動化への活用

**出典:** articles/2026-05-19_2581_web_Claude_Code_Routines_Official_Docs.md / articles/2026-05-19_2582_web_Claude_Code_Routines_Schedule_Webhook_GitHub.md

**提案内容:**
Claude Code Routines（2026年4月14日リサーチプレビュー）がスケジュール・Webhookトリガーのクラウドエージェントを提供。現在VPS cronで動かしているcollect_x.pyのうち「SIGNALキュレーション」部分をRoutinesに移行することを検討：
- スケジュールトリガーで毎朝6時にキュレーション実行
- GitHub eventトリガーでPRコメント対応を自動化
- 全有料プラン対応で追加コスト不要（Agent SDK課金移行後は要確認）

**優先度:** 中（6月15日以降の課金変更確認後に再評価）

### 2. Anthropic June 15 課金変更への対応

**出典:** articles/2026-05-19_2504_X_seclink_Stainless買収_MCP実装ツールチェーン制御.md / catalog-ecosystem参照

**提案内容:**
2026年6月15日より、Claude Agent SDK・`claude -p`・Claude Code GitHub Actionsが別課金プール（Pro: $20/月、Max 5x: $100/月）に移行。bpr_lab環境での対応：
1. 現在の`claude -p`使用箇所を棚卸しし、月間トークン消費量を推定
2. Max 5xプラン（$100クレジット）で足りるか確認
3. 6月8日前後にAnthropicからの「クレームメール」を確認してクレジットを受け取る

**優先度:** 高（期限: 2026年6月15日）

### 3. xhigh Effort の明示的制御

**出典:** articles/2026-05-19_2583_web_Claude_Opus_47_Whats_New_xhigh_Effort.md

**提案内容:**
Claude Code v2.1.117からxhigh effortが全プランのデフォルトに。コスト最適化のためCLAUDE.mdに推論コストに関する注釈を追加：
- 単純なファイル読み込み・検索タスクには `--effort low` を指定
- 複雑なリファクタリング・多段階タスクはxhigh（デフォルト）のまま
- `/effort` スライダーを使ったインタラクティブ調整方法をCLAUDE.mdに記載

**優先度:** 低

### 4. FX自動取引：TradingAgentsフレームワーク試用

**出典:** articles/2026-05-19_2585_web_TradingAgents_Best_AI_Financial_Trading_Review.md / articles/2026-05-19_2540_X_0xJoell_MossAI_AI_Execution_Separation_Architecture.md

**提案内容:**
TradingAgents v0.2.4（LangGraph基盤、マルチプロバイダー対応）がClaude 4.xに対応済み。sandbox/FX自動取引/への統合候補として評価：
- 7役割エージェント（ファンダメンタルズ・センチメント・テクニカル等）の協調判断
- 1決定あたり11 LLMコール＋20ツールコール（コスト試算が先決）
- MossAIの「AI推論層 + 決定論的執行エンジン分離」アーキテクチャも参考になる
- まずバックテストのみで評価し、実取引は慎重に段階導入

**優先度:** 中

---

## 2026-05-20 収集分

### 1. スキル設計への反映提案

#### 1-1. Agentmemory MCPサーバーの導入検討（セッション間コンテキスト維持）
**出典:** articles/2026-05-20_2594_X_chenzeling4_Your_coding_agent_forgets_everything_between_sessi.md

**提案内容:**
Agentmemory（MCP対応永続メモリOSS、14.9K stars）はClaude Codeセッション間でコンテキストを保持する。FX自動取引プロジェクトの長期開発セッションで「前回の意思決定・失敗理由・設計根拠」を次セッションに引き継ぐメモリ基盤として導入を検討する。
- `.claude/settings.json` のmcpServersに `agentmemory` を追加
- FX取引システムのバックテスト結果・失敗パターンをAgentmemoryに蓄積し、次回セッションで参照できる設計

**優先度:** 中

#### 1-2. Agent Skill Installerによるスキル管理の標準化
**出典:** articles/2026-05-20_2602_X_omry_Agent_Skill_Installer_installs_Codex_Claude_Code_s.md

**提案内容:**
Agent Skill InstallerがGitHub/PyPI/ローカルからClaude Code・Codexのスキルを一元インストールできるようになった。skills-registryの管理をこのツールに統一し、`pip install [skill-package]`でスキルを追加・更新するフローを標準化することを検討。

**優先度:** 低

---

### 2. Claude Code設定への反映提案

#### 2-1. worktree構造の整理（IDE横断検索の最適化）
**出典:** articles/2026-05-20_2596_X_towelbill_Trying_to_use_Claude_code_more_in_my_day_to_day_T.md

**提案内容:**
Claude Code worktreeを垂直（入れ子）ではなく水平（兄弟ディレクトリ）構造に整理することでIDE全文検索やgrepが各worktreeを独立したプロジェクトとして扱えるようになる。現在のbpr_labリポジトリのsandbox/FX自動取引/を別worktreeとして切り出す場合の参考設計として記録。

**優先度:** 低

---

### 3. FX自動取引システムへの反映提案

#### 3-1. XAU MT5 EAバックテスト実績の参照ベンチマーク追加
**出典:** articles/2026-05-20_2646_X_XAU15min_MT5_EA_Backtest_Result.md（ai-trading SIGNAL）

**提案内容:**
XAU/USD 15分足EAのバックテスト結果と、AIを使ったインジケーターのMT5移植事例が確認された。sandbox/FX自動取引/docs/BENCHMARK.mdにXAU時間足戦略の外部実績データとして追加する。

**優先度:** 低

---

### 4. AI規制対応

#### 4-1. 米国・EU AI規制の最終確認（2026-05-20時点）
**出典:** articles/2026-05-20_2649_web_AI_Legislative_Update_May15_2026_TransparencyCoalition.md / articles/2026-05-20_2654_web_Recent_AI_Regulatory_Developments_US_WSGR.md

**提案内容:**
米国AI規制の最新状況：連邦統一フレームワーク（White House 3月20日提案）vs 1,200本の州法（Cooley調査）の綱引きが継続。California AB 2013・SB 942（AI生成開示義務）は1月1日既施行。Connecticut SB5が両院通過し最も包括的な州法として注目。EU規制（8月2日・12月2日期限）と合わせて監視継続。

**優先度:** 低（欧州展開計画がない場合は不要）

---

## 2026-05-21 収集分

### 1. Hooks設計への反映提案

#### 1-1. Stop hookでlinter/type-check→エージェント自動修正ループの実装
**出典:** articles/2026-05-21_2666_X_bettercallsalva_Stopフック_linter_type-check_pro_tip.md

**提案内容:**
Claude CodeのStopフックでlinterまたはtype-checkを実行し、エラーを次のターンでエージェントにフィードバックするパターンが「安価な勝ちパターン」として実証された。
現在のCLAUDE.mdまたはsettings.jsonのHooks設定に追加候補：
```json
{
  "hooks": {
    "Stop": [{
      "type": "command",
      "command": "npm run type-check 2>&1 || python -m mypy . 2>&1"
    }]
  }
}
```
エージェントがエラーを受け取って自動修正するため、余分なプロンプトコストなしにコード品質を維持できる。FX自動取引スクリプトのtype strictnessを維持する安全網として有用。

**優先度:** 高（すぐに実装可能な即効性あり）

---

### 2. Claude Codeエコシステムへの反映提案

#### 2-1. Claude Plugins公式ディレクトリの活用
**出典:** articles/2026-05-21_2681_X_wefoundcc_Claude_Plugins公式ディレクトリ_Skills_Agents_Hooks.md

**提案内容:**
AnthropicがClaude Plugins公式ディレクトリをリリース。Skills・Agents・Hooks・Slash commands・MCPサーバー設定が一元管理・発見可能に。
- `/plugin search [keyword]` でカテゴリ検索できる可能性がある
- 現在のskills-registryと重複するプラグインを確認し、公式配布版があれば置き換えを検討
- `security-auditor`・`test-runner`・`ralph-loop`等のプラグインが含まれている可能性

**優先度:** 中（ディレクトリ内容を確認して有用なものを評価）

#### 2-2. Antigravity 2.0（Google版Claude Code）の競合動向把握
**出典:** articles/2026-05-21_2657_X_Hoshino_Sokichi_Antigravity_2_0_Google版Claude_Code.md

**提案内容:**
Google I/O 2026でAntigravity 2.0が発表。Claude Codeの直接競合として：
- デフォルトモデル: Gemini 3.5 Flash（Claude Opus 4.7比速度4倍）
- 複数AI並列実行・Firebase連携・スケジュール実行が標準搭載
- デスクトップアプリ+CLI対応

現行のClaude Code中心ワークフローを維持しつつ、特定タスク（高速ドラフト生成・Firebase連携）でAntigravity 2.0を試験補完する価値があるか評価する。CLAUDE.mdの「使用するAIツールの選択基準」セクションに追記候補。

**優先度:** 低（現時点では情報収集のみ）

---

### 3. FX自動取引システムへの反映提案

#### 3-1. TradingAgents + MT5 完全セットアップガイドの実装参照
**出典:** articles/2026-05-21_2700_web_008_Quant_AI_Agents_MT5_完全セットアップ_ユーザーガイド_2026年5月.md

**提案内容:**
MQL5.comにMT5向けQuantAI Agents（マルチモデル議論スタック）のセットアップガイドが掲載。
- OpenAI・Anthropic（Claude）・Google・DeepSeek・xAIをマルチモデル議論に統合
- 中央処理サーバー + データ同期ゲートウェイ構成
- MT5 EAとして動作、FX・株式CFD両対応

sandbox/FX自動取引/でのマルチモデル議論スタックの試験実装参考として調査する。
**優先度:** 中


---

## 2026-05-22 収集分

### 1. Claude Code設定への反映提案

#### 1-1. WIF（Workload Identity Federation）認証の導入検討
**出典:** articles/2026-05-22_2706_web_005_Claude_Code_APIキー不要_WIF認証導入_XenoSpectrum.md

**提案内容:**
AnthropicがWIFサポートを導入し、静的APIキーが不要になった。CI/CD環境（GitHub Actions等）でのClaude API呼び出しにWIFを適用することでAPIキー漏洩リスクを排除できる。
- `.github/workflows/` でのClaude Code実行にGitHub OIDC + WIF認証を適用
- AWS IAM/Google Cloud IAMと既存インフラ認証を統合
- sandbox/FX自動取引/deploy/ のCI/CD設定を見直し、APIキー不要化を評価

**優先度:** 中（セキュリティ改善として有効）

#### 1-2. Claude Code週次制限50%増（〜7/13）の期限をCLAUDE.mdに追記
**出典:** articles/2026-05-22_2705_web_004_Claude_Code_週次利用制限50pct増加_7月13日まで限定.md

**提案内容:**
7月13日が週次制限50%増の期限。CLAUDE.mdのコスト管理セクションに「2026年7月13日まで週次制限+50%（要見直し）」と記載しておき、期限後の自動リマインダーとして機能させる。

**優先度:** 低

---

### 2. Claude Ecosystemへの反映提案

#### 2-1. Stainless買収によるMCP自動生成の活用
**出典:** articles/2026-05-22_2756_X_cet3001_Anthropic_acquires_Stainless（ecosystem SIGNAL）

**提案内容:**
AnthropicがStainlessを買収。StainlessはOpenAPI仕様からSDKやMCPサーバーを自動生成するツール。この統合により今後「OpenAPI spec → MCPサーバー」のパイプラインがネイティブ化される見込み。
- FX自動取引のMT5 REST APIのOpenAPI仕様を整備しておけば、将来的にMCPサーバーを自動生成できる可能性
- 現在のMCPサーバー手動実装コストが大幅削減される見通し

**優先度:** 中（将来対応として設計を意識）

#### 2-2. Project Glasswingのサイバーセキュリティ知見の参照
**出典:** articles/2026-05-22 ecosystem SIGNAL（@AnthropicAI, @scottdylan, @ns123abc）

**提案内容:**
AnthropicのProject GlaswingがCloudflare・Mozilla Firefox・wolfSSLで10,000件以上の脆弱性を発見（90.6%真陽性率）。Claude AIを使ったセキュリティ分析のベストプラクティスとして参照価値がある。FX自動取引システムのコードベースに対して同様のアプローチを適用できる可能性がある。

**優先度:** 低（情報収集のみ）

---

### 3. FX自動取引システムへの反映提案

#### 3-1. EAERA MT5 AI Plugin アーキテクチャの実装参考
**出典:** articles/2026-05-22_2710_web_009_AI_Powered_MT5_Plugin_Future_Trading_EAERA.md

**提案内容:**
EAERAが公開したMT5 + LLM統合の具体的アーキテクチャ3パターン：
1. **DLL Bridge**: MQL5 → Python DLL → LLM API（最も低レイテンシ）
2. **WebRequest REST**: MQL5 WebRequest → ローカルFastAPI → LLM API（最もシンプル）
3. **Named Pipe/ZeroMQ**: 非同期双方向通信（リアルタイムシグナル向け）

sandbox/FX自動取引/src/ の実装方針として、現在のアーキテクチャがいずれのパターンに属するか確認し、レイテンシ要件に合った方式を選択する。

**優先度:** 高（具体的実装に直結）

#### 3-2. Vibe-Trading（HKUDS）とTradingAgentsの比較評価
**出典:** articles/2026-05-22_2708_web_007_Vibe_Trading_Personal_LLM_Trading_Agent_HKUDS.md

**提案内容:**
HKUDSのVibe-Tradingが新たに公開。TradingAgents（51K stars）とVibe-Trading（HKUDS）を並べて比較評価する価値がある：
- TradingAgents: 7エージェント協調、株式メイン、26.62%リターン実績
- Vibe-Trading: 個人投資家向け、感情/テクニカル/ニュース並列、Claude/GPT/Gemini対応

sandbox/FX自動取引/のリファレンス実装として、まずVibe-TradingのFX応用可能性を評価するPoCを実施する。

**優先度:** 中

---

### 4. AI規制・コンプライアンス

#### 4-1. EU AI Act 8月施行の最終確認（官報一次情報）
**出典:** articles/2026-05-22_2712_web_011_EU_AI_Act_Full_Effect_August2026_Official.md

**提案内容:**
欧州委員会公式サイトでEU AI Act全面施行（2026年8月）を確認済み。罰則：最大3,500万ユーロまたは世界売上7%。Claude APIを利用したサービスで欧州ユーザーへ提供する場合のコンプライアンス対応期限として確認完了。AI生成コンテンツへの透明性要件は実装済みか要確認。

**優先度:** 中（欧州展開予定がある場合）


---

## 2026-05-23 収集分

### 1. Claude Code設定・CLAUDE.mdへの反映提案

#### 1-1. 20人チーム検証の最適リポジトリ構成への統一
**出典:** articles/2026-05-23_2780_X（20人チームが検証した最適Claude Codeリポジトリ構成）

**提案内容:**
20人チームが実証した最適ディレクトリ構成 `skills/ agents/ commands/ hooks/ rules/` を現在のbpr_labリポジトリのClaude Code関連ファイル構造に適用する。
- `.claude/skills/` : 既存スキル（整理済み）
- `.claude/agents/` : サブエージェント定義（新設候補）
- `.claude/commands/` : カスタムスラッシュコマンド（新設候補）
- `.claude/hooks/` : フック設定（settings.jsonから分離検討）
- `.claude/rules/` : 条件付きCLAUDE.mdルール（globパターン）

**優先度:** 中

#### 1-2. サブエージェントのモデル指定オーバーライドへのHook保護
**出典:** articles/2026-05-23_2780_X_*_プロンプトインジェクション（プロンプト攻撃手法）

**提案内容:**
Claude Codeサブエージェントのモデル指定を悪意ある入力で無視させるプロンプトインジェクション手法が確認された。PreToolUseフックでAgentツール呼び出し時のパラメータを検証し、意図しないモデル指定の変更をブロックするフックを追加する。
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Agent",
      "hooks": [{"type": "command", "command": "scripts/validate-agent-params.sh"}]
    }]
  }
}
```

**優先度:** 中

---

### 2. Claude Ecosystemへの反映提案

#### 2-1. OpenRouterを使ったClaude Code CLIのコスト削減
**出典:** articles/2026-05-23_*_OpenRouter_1Mトークンコンテキストでコスト削減

**提案内容:**
Claude Code CLIをOpenRouterの無料モデルに向けることで、1Mトークンコンテキストを維持しつつAPIコストをゼロにする設定が公開された。開発作業（FX自動取引のコーディング補助）のコスト最適化として試験導入を検討。
- 本番品質の最終レビューはClaude Opus 4.7（正規）
- 初期ドラフト・探索段階はOpenRouter無料モデル

**優先度:** 低（品質リスク評価後に判断）

#### 2-2. MCP Linux Foundation標準化を受けたMCP投資の確信強化
**出典:** articles/2026-05-23_*_MCPがLinux Foundation標準（Anthropic・OpenAI・Microsoft・Google全社採用）

**提案内容:**
MCPがLinux Foundation標準になりAnthropicを含む主要4社全社が対応したことで、MCPへの長期投資が一層正当化される。現在のFX自動取引システムおよびスキル・HooksのMCP化設計を加速する根拠として活用する。特に「OpenAPI spec → MCPサーバー自動生成（Stainless買収）」との組み合わせで、MT5 REST APIのMCP化コストが将来ゼロになる見通し。

**優先度:** 中（設計方針の確信補強）

---

### 3. FX自動取引システムへの反映提案

#### 3-1. マルチエージェントBull/Bear/Riskスタックの採用根拠の強化
**出典:** articles/2026-05-23_2821_WEB（AI Agents vs LLMs Crypto Analysis Market 2026 KuCoin）

**提案内容:**
BlackRock・Columbia大 2026年4月研究が「Bull/Bear/Risk Supervisorの3層マルチエージェント構造が単体LLMを一貫して上回る」と確認。TradingAgentsの7エージェント協調採用の根拠としてsandbox/FX自動取引/docs/ARCHITECTURE.mdに引用する。
- Bull agent（テクニカルトレンド担当）
- Bear agent（マクロリスク担当）
- Risk Supervisor（最終ポジションサイズ決定）
の最小3エージェント構成での先行実装を推奨。

**優先度:** 高（既存TradingAgents導入計画に直結）

#### 3-2. ChatGPT-5 FX実験の負の結果から実装方針を再確認
**出典:** articles/2026-05-23_2824_WEB（ChatGPT-5にFXで稼いでもらおうとした結果）

**提案内容:**
GPT-5をFX完全自律に使った実験がマイナス収益に終わった一次情報。確認できた知見：
- LLMの完全自律判断→マイナス収益（実証）
- 「シグナル生成→人間判断→執行」分離アーキテクチャへの移行が正しい
この結果はFX自動取引プロジェクトの「LLM=センチメントフィルター（補助）」方針を再確認するデータとして `docs/EVALUATION.md` に記録する。

**優先度:** 高（実装方針の負の事例として記録必須）

---

## 2026-05-24 収集分

### 1. CLAUDE.md への反映提案

#### 1-1. MCP セキュリティポリシーの明記
**出典:** articles/2026-05-24_2855_X_cafe_au_laitsss_MCP_critical_security_flaw_200k_servers.md / articles/2026-05-24_2841_X_AJs_AI_Backdoor_OSS_localhost_proxy.md

**提案内容:**
MCPサーバーのlocalhost実装に起因するセキュリティ脆弱性（200k超サーバーに影響）と、OSSのlocalhost proxyを介したバックドア侵入報告が相次いで確認された。CLAUDE.mdに以下を追記すること：
- 使用するMCPサーバーは公式リポジトリまたは自作のもののみに限定する
- 不明なOSSのMCPサーバーは `npx` で直接実行しない（必ずソースレビューを先行）
- localhost MCPはバインドポートを `.claude/settings.json` で明示的に制限する

**優先度:** 高（セキュリティインシデント予防）

#### 1-2. Claude Code Desktop RCE修正への対応確認
**出典:** articles/2026-05-24_2839_X_satoki00_Claude_Code_Desktop_0Prompt_RCE_fix.md

**提案内容:**
Claude Code Desktop に 0-Prompt RCE（ゼロプロンプトリモートコード実行）脆弱性が発見・修正された。CLAUDE.mdに「定期的にClaude Codeのバージョンを確認し最新版に更新する」チェック項目を追加する。特にCI/CD環境でのClaude Code使用時はバージョン固定ではなく最新追従ポリシーを推奨。

**優先度:** 高（既存セキュリティリスクへの対処）

---

### 2. スキル・ワークフローへの反映提案

#### 2-1. MCP Stateless プロトコル RC 対応準備（2026-07-28）
**出典:** articles/2026-05-24_2831_WEB_MCP_Roadmap_2026_Production_Stateless_TheNewStack.md

**提案内容:**
MCP Stateless プロトコルのRC（Release Candidate）が2026-07-28にリリース予定。現在 `streamable-http` でセッション状態を持つサーバー設計は、Stateless RC対応で再設計が必要になる可能性がある。既存または計画中のMCPサーバー（MT5 MCP等）を設計する際、Stateless化を前提に「状態はサーバー側ではなくクライアント（Claude Code）のコンテキストに持たせる」アーキテクチャを先行採用すること。

**優先度:** 中（2026-07-28以前に設計方針決定）

#### 2-2. WhatsApp通知MCPサーバーの評価
**出典:** articles/2026-05-24_2848_X_marchelfah_wazzapi_MCP_WhatsApp.md

**提案内容:**
wazzapi MCPサーバーを使うことで、Claude Codeからの実行結果をWhatsAppに直接送信できる。FX自動取引システムのシグナル通知・アラートチャネルとして、既存のSlack/Discord通知の代替または補完として評価する価値がある。特に日本語対応が良好なWA Businessアカウントがあれば低コストで実装可能。

**優先度:** 低（通知チャネル多様化の選択肢として記録）

#### 2-3. Microsoft Claude Code ライセンス縮小への対応
**出典:** articles/2026-05-24_2840_X_IROHANI_shotime_Microsoft_Claude_Code_license_shrinkage_June.md

**提案内容:**
MicrosoftがClaude Codeのライセンスを2026年6月末に縮小する方針が報告された（VS Code / GitHub Copilot経由での利用制限）。現在のClaude Code利用形態（CLI直接 vs VS Code Extension経由）を確認し、影響範囲を把握しておく。CLI直接利用はAnthropicの直接契約のため影響外だが、VS Code拡張経由で利用している場合は6月末以前に移行計画を立てること。

**優先度:** 中（6月末デッドライン）

---

### 3. FX自動取引システムへの反映提案

#### 3-1. TradingAgents v0.2.4 Python OSSの評価導入
**出典:** articles/2026-05-24_2835_WEB_TradingAgents_v024_MultiAgent_LLM_Python_Medium.md

**提案内容:**
TradingAgents v0.2.4がPython OSSとして公開された。7エージェント協調（Fundamentals/Sentiment/Technical/Macro analysts + Bull/Bear researchers + Risk Manager）の最新実装が利用可能。前日(2026-05-23)に確認したBlackRock研究とアーキテクチャが合致する。`sandbox/FX自動取引/` にて以下の評価を行う：
1. `pip install tradingagents` でインストールし動作確認
2. デフォルトシンボルをFXペア（USDJPY等）に変更して動作テスト
3. MT5のリアルタイムフィードとの接続ポイントを特定

**優先度:** 高（既存計画に直結するOSSの最新版）

#### 3-2. MT5 Python タイムゾーン・position_id 処理の修正
**出典:** articles/2026-05-24_2858_X_bottsukuttemita_MT5_Python_timezone_position_id.md

**提案内容:**
MT5 Python APIでのタイムゾーン変換とposition_id取得に関するバグレポート。既存の `sandbox/FX自動取引/` のMT5操作コードに同様の問題が潜在している可能性がある。具体的には：
- `datetime` オブジェクトをMT5 API に渡す際の timezone-aware/naive 混在バグ
- `position_id` の取得タイミング（注文直後 vs 約定確認後）の処理ミス
既存コードの該当箇所を確認し、必要であれば修正する。

**優先度:** 中（バグ予防のコードレビュー）

---

---

## 2026-05-25 収集分

### 1. Claude Code設定・ワークフローへの反映提案

#### 1-1. /goal コマンドの活用パターンをCLAUDE.mdに記載
**出典:** articles/2026-05-25_2865_WEB_Claude_Code_v2_1_139_Agent_View_goal_Command.md, articles/2026-05-25_2866_WEB_Claude_Code_goal_Command_Set_Completion_Conditions_for_Lon.md

**提案内容:**
Claude Code v2.1.139で追加された `/goal` コマンドは長時間タスクのループ自動化に使える。CLAUDE.mdに以下のパターンを記載することを推奨：
```
# 長時間タスクの実行指針
- テストグリーン化: /goal all tests pass
- PR作成まで自動化: /goal all tests pass and PR is open
- スタックした場合は人間に報告して停止（自動制御）
```
さらに `claude agents` でセッション一覧を確認するコマンドをチートシートとして`.claude/`に追加する価値がある。

**優先度:** 高（即座に業務効率化できる新機能）

#### 1-2. Anthropic 6月15日課金変更への対応
**出典:** articles/2026-05-25_2867_WEB_Claude_Code_Billing_Change_June_15_2026_Agent_SDK_Credit_P.md, articles/2026-05-25_2868_WEB_Zed_Editor_What_Anthropic_s_New_Claude_Billing_Means_for_Ze.md, articles/2026-05-25_2869_WEB_What_AI_Agents_Actually_Cost_Anthropic_Billing_Split_Reve.md

**提案内容:**
2026年6月15日以降、`claude -p`（非インタラクティブ）・Agent SDK・Claude Code GitHub Actions が**別個の月次クレジットプール**（Pro: $20/月）に移行する。
現在の `sandbox/` 内の自動化スクリプトで `claude -p` を使用している箇所を確認し：
1. クレジット消費量の見積もりを行う
2. 月$20クレジットを超える可能性があればAPI直接利用（ANTHROPIC_API_KEY）へ移行を検討
3. 非インタラクティブ実行の件数・頻度をログで把握する仕組みを追加

**優先度:** 高（6月15日デッドライン）

### 2. スキル・フック設計への反映提案

#### 2-1. Hook Hulk パターン（不良コード生成防止フック）の導入検討
**出典:** articles/2026-05-25_2891_X_tarcnux_O_Hook_Hulk_bloqueando_o_Claude_Code_de_fazer_💩_Ho.md

**提案内容:**
「Hook Hulk」はClaudeがコミットしようとする前に決定論的ミドルウェアとして介入し、特定の不良パターンを強制ブロックするPreToolUse hookの実装パターン。既存の`.claude/settings.json`のhooks設定に追加できる。具体的には：
- `.env`ファイルのコミット禁止
- `rm -rf /`等の破壊的コマンドのブロック
- 本番DB直接書き込みの禁止
LLMによる判断（約80%遵守）より確実な100%強制が可能。

**優先度:** 中（セキュリティ強化として推奨）

### 3. FX自動取引システムへの反映提案

#### 3-1. AI EA実績データの収集・評価体制の整備
**出典:** articles/2026-05-25_2909_X_f4rXUSenD787572_荒れた相場でも焦って飛び乗らない_「勝てる場面だけを狙って稼働」_🔥.md, articles/2026-05-25_2910_X_takonegi15_FX_MetaTrader情報→_【たこねぎFX予報AI_Bot】天気予報のようにFXレート.md

**提案内容:**
MT5向けAI EAの実績報告（週次+453,398円等）がX上で増加している。`sandbox/FX自動取引/`のEA開発に際して、Xで公開されている実績データを参照ベンチマークとして活用する体制を整備する。特に「勝てる場面のみで稼働する選択的エントリー」というアプローチは既存設計への組み込みを検討する価値がある。

**優先度:** 低（参考情報として記録）


---

## 2026-05-26 収集分

### 1. Claude Code設定・CLAUDE.mdへの反映提案

#### 1-1. Agent SDK課金変更（6月15日）最終対応確認と緩和策実装
**出典:** articles/2026-05-26_2923_〜2925（MagnaCapax Gist・thoughts.jock.pl・vaught.ai）

**提案内容:**
本日の収集で課金変更の詳細分析が3件確認された。6月15日まであと20日を切った。対応の最終確認：
- Pro $20・Max 5x $100・Max 20x $200（ロールオーバーなし）、軽量ワークロード実効12倍・重量175倍のコスト増
- **緩和策4選**（thoughts.jock.pl推奨）: ①APIキー直接利用への切り替え, ②Haiku 4.5へのダウングレード, ③バッチ処理化, ④予算上限設定
- claude -p 呼び出し箇所をすべて棚卸しし、インタラクティブ利用との境界を再確認
- Anthropicのクレーム申請メール（6月8日前後予想）を見逃さないこと

**優先度:** 高（残り20日・期限厳守）

---

### 2. スキル設計への反映提案

#### 2-1. /react-doctor スキルの評価・導入（いいね2,106件）
**出典:** articles/2026-05-26_2954_X_react-doctor（claude-code SIGNAL）

**提案内容:**
`/react-doctor`オープンソーススキルが2,106いいねを記録。`npx` 一発でインストールでき、不正なReactコードを自動修正する専用エージェントスキル。skills-registryに追加候補として評価する。同様のパターン（ドメイン特化自動修正スキル）をFX自動取引プロジェクトにも応用できる（例: `/mql5-doctor`でMQL5の不正コードを自動検出・修正）。

**優先度:** 中（試験導入として評価）

#### 2-2. 70+ Skills実践知見からSKILL.md品質向上
**出典:** articles/2026-05-26_2926_70_Plus_Claude_Skills_Best_ArtificialCorner.md（web-signal）

**提案内容:**
70本以上のスキルを実際に構築・テストした記事から、実用スキルの共通パターンが判明：
- `## Gotchas` セクション必須（既提案の再確認）
- supporting files（templates・examples・helper scripts）を積極活用
- トリガー条件を「動詞＋ユースケース」形式で200文字以内に記述
既存スキルのSKILL.mdを見直し、上記3点が実装されているか確認する。

**優先度:** 中

---

### 3. Claude Ecosystemへの反映提案

#### 3-1. Google Cloud 50以上のマネージドMCPサーバーの活用検討
**出典:** articles/2026-05-26_2929_Google_Cloud_50_Managed_MCP_Servers_GA_JA.md（web-signal）

**提案内容:**
Google Cloud Next '26でBigQuery・Spanner・Cloud SQL・Vertex AI・Google Maps等50以上のMCPサーバーがGAになった。FX自動取引プロジェクトへの応用候補：
- BigQuery MCP: FXの大量履歴データ分析・バックテストデータ管理
- Vertex AI MCP: Gemini 3.1によるセンチメント分析をClaudeの補完として活用
- Google Maps MCP: 地政学リスク・経済指標の地理的可視化（参考情報として）
`.claude/settings.json` のmcpServersにGoogle Cloud MCPの追加を評価する。

**優先度:** 中

#### 3-2. Anthropic Stainless買収による MCP自動生成の近未来準備
**出典:** articles/2026-05-26_2933〜（claude-ecosystem SIGNAL: Stainless買収）

**提案内容:**
AnthropicがStainlessを約$300Mで買収（Stainlessは全AnthropicのSDKとMCPサーバーを自動生成してきた会社）。OpenAPI spec → MCPサーバーのパイプラインがClaudeツールチェーンにネイティブ統合される見込み。対応準備：
- FX自動取引のMT5 REST APIのOpenAPI spec（`docs/api-spec.yaml`）を整備しておく
- 将来の自動生成に備えて既存MCPサーバー実装を「OpenAPI互換」な設計に維持

**優先度:** 低（設計方針として意識）

#### 3-3. Claude Mythos（セキュリティ特化モデル）の動向把握
**出典:** articles/2026-05-26_2938〜2941（claude-ecosystem SIGNAL: Claude Mythos）

**提案内容:**
AnthropicがClaudeのセキュリティ特化派生モデル「Claude Mythos」を開発中（6〜8月リリース予定）。Cloudflare・Firefox・wolfSSLで10,000件以上の脆弱性を発見（90.6%真陽性率）。FX自動取引コードベースのセキュリティ審査に将来活用できる可能性がある。リリース後にsandbox/FX自動取引/への適用評価を実施。

**優先度:** 低（リリース後に再評価）

#### 3-4. MCP Server Registry v2.0（2,500サーバー）の棚卸し
**出典:** articles/2026-05-26_2980_X_MCP_Server_Registry_v2（claude-ecosystem SIGNAL）

**提案内容:**
MCP Server Registry v2.0に2,500以上の検証済みサーバーが登録され、自動セキュリティスキャン・互換性バッジが追加された。新規追加されたKubernetes・PostgreSQL・Figma MCPを確認し、.claude/settings.jsonのmcpServers設定を更新する価値がある。特にPostgreSQL MCPはFXデータベース連携に直接有用。

**優先度:** 中

---

### 4. FX自動取引システムへの反映提案

#### 4-1. EA Agent Studio（MT5バックテスト×AI評価）の評価
**出典:** articles/2026-05-26_2986_X_FXtradersAI_EA_Agent_Studio（ai-trading SIGNAL）

**提案内容:**
MT5上でバックテストをサーバー実行し、AIがEAのパフォーマンスを詳細分析するEA Agent Studioが今週末公開予定。MT5×AI統合の具体的実装例として早期評価する価値がある。sandbox/FX自動取引/のバックテスト→AI評価パイプラインの参考実装として採用可能性を調査する。

**優先度:** 中（公開後すぐに評価）

#### 4-2. TradingAgents詳細解説からの実装参考（LangGraph + マルチプロバイダー）
**出典:** articles/2026-05-26_2931_TradingAgents_MultiAgent_LLM_Framework_IntellectyxAI.md（web-signal）

**提案内容:**
IntellectyxAIによるTradingAgentsの技術詳細解説から実装指針を確認：
- LangGraph ベース（フレキシブルなDAGワークフロー）
- Bull/Bear研究者エージェントの動的議論が意思決定品質を上げる（論文実証済み）
- Anthropic（Claude）はプロバイダーの1つとして対応済み
- FX・株式・暗号資産の各市場での実験結果あり
sandbox/FX自動取引/ でのTradingAgents導入時、ClaudeをメインLLMとして設定する具体的な設定方法を確認する。

**優先度:** 高（既存TradingAgents導入計画に直結）



---

# 以下、旧ルート library/inbox/PROPOSALS.md からの統合（2026-07-16、5/27以降の収集ルーチン提案分）

# PROPOSALS.md

収集記事を横断分析して得られた反映提案。
最終更新: 2026-07-12: 日次収集+キュレーション 2026-07-12（収集11件 → SIGNAL 11件）

---

## 2026-05-27 提案

### P-001: CLAUDE.md への反映 — /model コマンドの挙動変更を明記

**根拠記事**: 003 (Claude Code April changelog)
**詳細**: v2.1.xから`/model`コマンドが「現在のセッションのみ」のモデル変更に変更（永続変更ではなくなった）。CLAUDE.mdにモデル設定はセッションスコープであることを記載し、永続変更が必要な場合の手順を記録しておくべき。

**提案アクション**: CLAUDE.md（存在する場合）に以下を追記
```
## Claude Codeバージョン固有の注意事項
- /model コマンドは現在のセッションのみに適用（v2.1.x以降）。永続変更は設定ファイルで行う。
```

---

### P-002: CLAUDE.md への反映 — CLAUDE.md 500語以内・必須項目リスト

**根拠記事**: 004, 005, 018 (CLAUDE.md best practices 複数記事で一致)
**詳細**: 複数の一次情報記事でCLAUDE.mdの推奨構成が一致している：500語以内、含めるべき内容はテックスタック・エントリーポイント・命名規則・build/test/lint コマンド・共通の落とし穴・コーディングスタイル。

**提案アクション**: 本リポジトリのCLAUDE.mdを上記テンプレートに沿って見直し・整備する。

---

### P-003: Skills Registry への反映 — 提案スキル3件

**根拠記事**: 002, 006 (Hooks/Skills使い分け・Qiita Skills20選)

追加検討すべきスキル案:
1. **`/daily-collect`** — 本日次収集エージェントそのものをスキル化（毎日同じプロンプトを書かずに実行可能に）
2. **`/fx-backtest`** — FX自動取引のバックテスト実行スキル（sandbox/FX自動取引/に対応）
3. **`/catalog-update`** — library/catalog.mdの更新・統計再計算スキル

---

### P-004: FX自動取引への反映 — TradingAgents アーキテクチャの採用検討

**根拠記事**: 011 (TradingAgents v0.2.4)
**詳細**: LangGraphベースのマルチエージェントLLMフレームワーク。AAPL対象で+26.62%のパフォーマンス実績、GitHub 51k stars。5層・12エージェント構成でファンダメンタル・センチメント・テクニカルを統合。Claude APIをバックエンドとして使用可能（GPT・Claude・Gemini・Grokをサポート）。

**提案アクション**: sandbox/FX自動取引/ において、TradingAgentsのマルチエージェントアーキテクチャ（特にセンチメント分析エージェント＋テクニカルエージェントの分離）を参考にした設計検討。LLMバックエンドにClaude Opus 4.7を使用することで既存APIキーを活用可能。

---

### P-005: FX自動取引への反映 — MT5+Python+LLM の統合パターン参照

**根拠記事**: 012 (MT5+GPT-4 Python実装 GitHub)
**詳細**: sandbox/FX自動取引/main.py は既にMT5連携が目標。参照実装（Tzigger/MT5_trading_bot）がOHLCデータ分析→GPT-4推奨→注文送信のパイプラインを公開済み。GPT-4部分をClaude Agent SDKに置き換えることで既存実装を転用可能。

**提案アクション**: Tzigger/MT5_trading_bot のコードを参考に、sandbox/FX自動取引/main.py でClaude Agent SDK経由のLLMシグナル生成を実装する。

---

### P-006: 緊急対応 — Anthropic 2026-06-15 課金変更

**根拠記事**: 007 (Anthropic June15課金変更)
**緊急度**: 高（2026-06-15施行まで18日）
**詳細**: claude -p、Claude Code GitHub Actions、Agent SDK呼び出しが従量課金（標準APIリスト価格）に移行。現在サブスクリプションで実行している自動化スクリプトのコスト試算が必要。

**提案アクション**:
1. 現在の利用量（claude -p呼び出し回数、GitHub Actions実行回数）を確認
2. 6月15日以降の月額推定コストを計算
3. 必要に応じてAPI利用量を調整するか、Anthropic Managed Agentsへの移行を検討

---

## 2026-05-28 提案

### P-007: モデルアップグレード — Claude Opus 4.8への移行検討

**根拠記事**: 020 (Claude Opus 4.8リリース)
**詳細**: 本日（2026-05-28）Claude Opus 4.8がリリース。SWE-bench Pro 69.2%（+4.9pt）、コード欠陥見落とし率4分の1、Fast mode 3倍安価・2.5倍高速。価格はOpus 4.7と同額（$5/$25/Mトークン）のため、FX自動売買のLLMバックエンド・日次収集エージェントのモデル指定をOpus 4.8に更新することを検討。P-004（TradingAgentsアーキテクチャ）での使用モデルもOpus 4.8が最適候補。

**提案アクション**:
1. sandbox/FX自動取引/ のLLMバックエンド設定をclaude-opus-4-8に更新
2. CLAUDE.mdのモデル指定セクション（P-001参照）にOpus 4.8のFast modeが高コスパである旨を追記
3. 日次収集エージェントでの推奨モデルをOpus 4.8 Fast modeに変更（速度・コスト両面で優れる）

---

### P-008: Claude Code Routinesで日次収集を自動スケジュール化

**根拠記事**: 023 (Claude Code Routines)
**詳細**: Claude Code Routinesのスケジュールトリガーを使えば、現在手動実行している日次情報収集エージェントをClaude側のクラウドで毎朝自動実行できる。P-003で提案した /daily-collect スキルとの組み合わせが有効。マシンオフ中も実行継続。

**提案アクション**:
1. /daily-collectスキル（P-003）を先に作成
2. Claude Code Routinesでスケジュール設定（毎朝6:00 JST等）
3. GitHub Actionsトリガーと組み合わせて収集結果をmainブランチへ自動プッシュ

---

### P-009: Dynamic Workflowsで並列バックテストの高速化

**根拠記事**: 021 (Claude Code Dynamic Workflows)
**詳細**: Claude Code Dynamic Workflows（研究プレビュー）が本日公開。最大1,000サブエージェントの並列実行が可能。sandbox/FX自動取引/ のバックテストを複数通貨ペア・複数期間で並列実行する際に活用できる。単一線形エージェントループでは時間がかかりすぎるパラメータ最適化探索に特効。

**提案アクション**:
1. Max/Team/EnterpriseプランまたはAPI経由でDynamic Workflowsを有効化
2. FXバックテストの並列実行プロンプト設計（通貨ペア×時間軸のマトリックス）
3. 結果を統合・比較するオーケストレーターエージェントのCLAUDE.md設計

---

## 2026-05-29 提案

### P-010: Skills設計最適化 — SKILL.md肥大化防止（決定論的処理のスクリプト化）

**根拠記事**: 036 (Claude Code Skills設計パターン・playpark.co.jp)
**詳細**: SKILL.mdが312行→42行（87%削減）・月次エラー80%削減を実証した設計パターン。「決定論的処理（日付計算・ファイル確認・JSON生成）はBashスクリプトへ分離し、SKILL.mdにはAI判断が必要なものだけ記述する」原則で実現。bpr_labの日次収集エージェントSkillにも同原則を適用できる。

**提案アクション**:
1. `.claude/skills/`配下の既存Skillsを監査し、スクリプト化可能な決定論的処理を特定
2. `get_next_date.sh`・`detect_mode.sh`・`orchestrate.sh`パターンを参考に分離実装
3. SKILL.md本体を200行以内（理想は100行以内）に削減

---

### P-011: カスタムMCPサーバー開発 — bpr_lab独自データのClaude接続

**根拠記事**: 041 (エブリー社食トレンド分析MCPサーバー自作事例)
**詳細**: FastMCP + データソース（Databricks/Pandas等）でカスタムMCPサーバーを構築し、Claude APIから自然言語でbpr_lab独自データを問い合わせる事例。FXバックテスト結果・MT5取引ログ・戦略パラメータをMCP経由でClaudeに接続すれば、「過去1ヶ月のSR戦略のSharp比を教えて」のような自然言語クエリが可能になる。

**提案アクション**:
1. FastMCP（`pip install fastmcp`）でsandbox/FX自動取引/のバックテスト結果をMCP化
2. ツール設計: `get_backtest_results(strategy, period)`・`get_trade_log(date_range)`・`compare_strategies()`
3. OpenTelemetryで利用状況・エラー率の継続追跡を設定

---

### P-012: 緊急追加 — Claude Sonnet 4 / Opus 4（20250514版）のモデルリタイア対応

**根拠記事**: 040 (Claude Agent SDK deep dive - 課金・モデルリタイア情報)
**緊急度**: 高（2026-06-15まで残り17日）
**詳細**: P-006（課金変更）に加え、`claude-sonnet-4-20250514`と`claude-opus-4-20250514`が2026年6月15日でAPIからリタイア（ハードデプリケーション）。現在どこかでこれらのモデルIDをハードコードしていれば、その日に呼び出しが失敗する。

**提案アクション**:
1. sandbox/FX自動取引/・library/配下のコードで古いモデルIDを検索: `grep -r "sonnet-4-20250514\|opus-4-20250514" .`
2. 発見した場合は`claude-sonnet-4-6`または`claude-opus-4-7`に変更（Opus 4.8も可）
3. P-006のコスト試算も合わせて実施

---

## 2026-05-30 提案

### P-013: FX自動取引への反映 — MetaTrader MCPサーバーの採用検討

**根拠記事**: 057 (MetaTrader MCPサーバー・32ツール・GitHub)
**詳細**: `ariadng/metatrader-mcp-server`はPython 3.10+で動作し、MCP経由でClaude Desktopから「EUR/USDを0.01ロット買う」などの自然言語指示でMT5を操作できる32ツールのオープンソースブリッジ。REST API・WebSocketストリームもサポート。認証情報はローカルマシン上にのみ保持するセキュア設計。sandbox/FX自動取引/の現在のmain.py（MT5連携目標）に対して、MCP経由での操作レイヤー追加が現実的な選択肢となった。

**提案アクション**:
1. `git clone ariadng/metatrader-mcp-server`でローカルセットアップ確認
2. MT5ターミナルのアルゴリズム取引を有効化し、認証情報を`.env.example`に従って設定
3. Claude Desktop経由で基本操作（価格取得・口座確認）をテストしてからシグナル自動化に拡張
4. P-011（カスタムMCPサーバー）と組み合わせた複合MCPアーキテクチャを検討

---

### P-014: FX自動取引への反映 — MQL5+LLM 4層アーキテクチャと信頼度閾値の採用

**根拠記事**: 056 (MQL5+LLM 2026年実用アーキテクチャ・信頼度0.75超で勝率61.7%)
**詳細**: 4層マイクロサービス（データ収集EA→Python/FastAPIミドルウェア→LLM推論→実行ゲートウェイ）構成と信頼度閾値（0.55未満ノーエントリー48.3%勝率、0.75超でフルサイズ61.7%勝率）の定量的実証値が公開された。P-004・P-005をより具体的な実装設計に落とし込む根拠となる。

**提案アクション**:
1. sandbox/FX自動取引/main.py にPython/FastAPIミドルウェア層を追加設計
2. LLMレスポンスのJSONスキーマバリデーション（action・regime・confidence fields）を実装
3. confidence < 0.55 → noTrade、0.55-0.75 → 半サイズ、0.75+ → フルサイズのポジションサイジングロジックを実装
4. 直近5-10決定のステートフルコンテキスト保持を設計に組み込む

---

### P-015: CLAUDE.md改善 — 段階的開示の3層構造への移行

**根拠記事**: 060 (効果的なCLAUDE.mdの書き方・Zenn・命令予算200個の制約)
**詳細**: LLMが一貫して従える命令数はフロンティアモデルで約200個が上限で、命令数増加と共に全命令の遵守率が一律低下する。推奨構造：Layer 1（CLAUDE.md）に必須情報のみ・Layer 2（.claude/rules/）にトピック別分離・Layer 3（Skills）に専門知識。本プロジェクトのCLAUDE.mdが200行・200命令を超えている場合、重要ルールの遵守率が低下している可能性がある。

**提案アクション**:
1. 現在のCLAUDE.mdの行数・命令数を確認（200行以内かチェック）
2. テーマ別（FX自動取引ルール・ライブラリ管理ルール・コーディングスタイル）に.claude/rules/へ分離
3. P-002（CLAUDE.md整備）とP-010（Skill設計最適化）と統合した包括的見直しを実施
4. 削除基準：「削除したらClaudeが間違えるか？」でNOなら削除を徹底

---

### P-016: 開発ワークフロー改善 — Agent ViewとAuto Modeの活用

**根拠記事**: 049 (Claude Code Agent View), 050 (Claude Code Auto Mode)
**詳細**: Agent View（`claude agents`コマンド・2026年5月11日公開）で複数の並列エージェントセッションを一元管理可能になった。Auto Mode（Proプラン展開中）で人間承認プロンプトをML分類器に置き換え、「コーヒーブレイクで離席できる」水準の自律度を実現。日次収集エージェント（P-003・P-008）やFXバックテスト並列実行（P-009）との組み合わせで大幅な効率向上が見込める。

**提案アクション**:
1. Claude ProプランでAuto Modeを有効化し、日次収集エージェント実行時に試用
2. バックグラウンドセッション（`claude --bg`）で並列タスクを起動し、Agent Viewで一元監視
3. P-008（Routines自動スケジュール）と組み合わせ、完全自律の日次収集フローを構築

---

### P-017: MCPエコシステム対応 — 2026-07-28仕様RC破壊的変更の移行計画

**根拠記事**: 053 (MCP 2026-07-28仕様RC・ステートレス化・廃止ポリシー)
**詳細**: MCP次期仕様（最終版2026-07-28公開予定）でRoots・Sampling・Loggingが非推奨化（12ヶ月以上の移行期間付き）。ステートレス化によりセッション管理アーキテクチャの変更が必要になるMCPサーバーが存在する可能性がある。P-011（カスタムMCPサーバー）・P-013（MetaTrader MCPサーバー）の実装はRC仕様に基づいて設計すべき。

**提案アクション**:
1. 現在使用中のMCPサーバー一覧を確認し、Roots/Sampling/Logging使用有無を調査
2. 新規MCPサーバー実装（P-011・P-013）は2026-07-28 RC仕様準拠で設計
3. 2026年7月28日の最終版公開後、SDK更新と合わせて既存設定を検証

---

## 2026-05-31 提案

### P-018: Hooksドキュメント更新 — 27イベントへの参照修正

**根拠記事**: 062 (Claude Code Hooks完全リファレンス2026)
**詳細**: 2026年5月時点でClaude Code Hooksのライフサイクルイベントは**27種類**に拡大（旧情報「18種類」は2025年時点の数値）。SessionStart・UserPromptSubmit・PreToolUse・PostToolUseを含む27イベントと、Command/Prompt/Agent/Notification/Validationの5ハンドラー型が利用可能。終了コード0/1/2のセマンティクスが明確化され、ブロッキング（コード2）はPreToolUseのみ有効。

**提案アクション**:
1. CLAUDE.md・.claude/rules/ 内の「Hooks 18イベント」等の古い参照を「27イベント」に更新
2. PreToolUse ブロッキング（終了コード2）を活用したセキュリティゲートをHooksに追加
3. Agent hooksをCI/CDパイプライン統合に活用する設計パターンを.claude/rules/hooks.mdに記録

---

### P-019: Routines /schedule 運用Fix — CLAUDE.md にブランチ設定を明記

**根拠記事**: 064 (Claude Code Routines /schedule ブランチ問題)
**詳細**: Claude Code Routinesの/scheduleトリガーを使用するとPRがmainではなくclaude/プレフィックスブランチにプッシュされる既知の挙動がある。CLAUDE.md または Routine定義ファイルに明示的なブランチ設定を記述することで回避可能。P-008（Routines自動スケジュール化）実装時に必ずこの問題に遭遇する。

**提案アクション**:
1. CLAUDE.md に「Routinesは`branch: main`を明示しないとclaude/ブランチへプッシュする」警告を追記
2. P-008実装時のRoutine定義ファイルに `branch: main` を必ず含める
3. GitHubリポジトリの保護ブランチ設定でclaude/系ブランチのPRマージポリシーを確認

---

### P-020: FX自動取引 — TrustTrade式「選択的コンセンサス」のシグナル生成への適用

**根拠記事**: 069 (Agentic Trading arxiv:2605.19337), 070 (TrustTrade arxiv:2603.22567)
**詳細**: TrustTrade論文（2026年3月）が提案する「選択的コンセンサス」機構は、複数LLMエージェントの意見を信頼スコアで重み付けして統合する手法。P-004（TradingAgentsアーキテクチャ）のマルチエージェント設計に組み込むことで、全エージェント均等統合よりも決定品質が向上する。P-014（MQL5+LLM 4層アーキテクチャ）のconfidence閾値と組み合わせると相乗効果が期待できる。

**提案アクション**:
1. sandbox/FX自動取引/ のマルチエージェント設計において、各エージェント（テクニカル・センチメント・ファンダメンタル）に信頼スコアを付与する仕組みを設計
2. 過去の正答率（バックテスト実績）に基づいて信頼スコアを動的更新するアダプタを実装
3. 信頼スコア加重平均がP-014の閾値（0.55/0.75）を下回る場合はノーエントリーとするロジックを追加

---

## 2026-06-01 提案

### P-021: 期間限定50%増枠を活用 — P-009並列バックテスト・P-016Auto Mode積極実行

**根拠記事**: 073 (Claude Code 週次制限50%増加・7月13日まで)
**詳細**: 2026年7月13日まで週次利用制限が1.5倍・短期ウィンドウが2倍に拡大されている（価格据え置き）。P-009（Dynamic Workflowsでの並列バックテスト）やP-016（Auto Mode活用）を試すのに最適なタイミング。レート制限を気にせず大量のサブエージェント実行や長時間のバックテスト探索が可能。

**提案アクション**:
1. 7月13日までにP-009（複数通貨ペア×複数期間の並列バックテスト）を実施
2. Auto Mode（P-016）で日次収集エージェントの完全自律実行をテスト
3. Subagents（P-075参照: 4-8並列worktreeが安定稼働）で並列タスクをフル活用
4. 7月14日以降にデフォルト制限に戻ることを想定し、効率化された手法を7月13日までに確立

---

### P-022: builder.io 50 Tipsから即採用すべき設定 — エイリアス・1Mコンテキスト・remote-control

**根拠記事**: 074 (builder.io 50 Claude Code Tips)
**詳細**: builder.io の50 Tipsのうち即座に生産性向上に直結する設定が複数ある。特に `cc` エイリアスでパーミッションプロンプト全スキップ、`/model opus[1m]`または `sonnet[1m]` で1Mコンテキストをセッション中に切替可能、`claude remote-control`でiOS/Androidからリモート監視・承認が可能。

**提案アクション**:
1. シェルプロファイル（~/.bashrc等）に `alias cc='claude --dangerously-skip-permissions'` を追加
2. CLAUDE.mdに「大規模ファイル解析時は `/model opus[1m]` でコンテキスト拡張を検討」を追記
3. `claude remote-control` の使い方をCLAUDE.mdまたは.claude/skills/に記録（長時間タスク監視用）
4. `!git status` / `!npm test` インラインシェルコマンドをワークフローに組み込む

---

### P-023: Subagents設計パターンの本番実装 — 4-8並列worktreeの標準化

**根拠記事**: 075 (Claude Code Subagents 2026 実践ガイド)
**詳細**: 2026年中頃時点で1開発者あたり4〜8並列worktreeが安定稼働、複雑タスクの完了時間50-70%削減の実績が報告されている。YAML定義ファイルによる再利用可能Subagent構成の管理と、`CLAUDE_CODE_SUBAGENT_MODEL` 環境変数によるコスト制御が本番環境のベストプラクティス。bpr_labの日次収集エージェント（4ドメイン並列）やFXバックテスト（複数戦略並列）に直接応用可能。

**提案アクション**:
1. .claude/agents/ ディレクトリに4ドメイン用Subagent YAML定義を作成（claude-code・claude-ecosystem・ai-trading・ai-news各専門エージェント）
2. `CLAUDE_CODE_SUBAGENT_MODEL=claude-haiku-4-5` 環境変数でサブエージェントコストを抑制
3. Fork mode（`CLAUDE_CODE_FORK_SUBAGENT=1`）でプロンプトキャッシュ共有を試験適用
4. 並列実行で週次制限を効率使用（P-021との組み合わせ）

---

### P-024: FX自動取引LLMバックエンド選択更新 — GPT-5.5 vs Gemini 3.5 Flash vs Claude Opus 4.8

**根拠記事**: 076 (GPT-5.5), 077 (Gemini 3.5 Flash)
**詳細**: 本日時点での主要フロンティアLLMの選択肢が整理できた。
- GPT-5.5: $5/$30/Mトークン、Terminal-Bench 82.7%。エージェント型コーディング強、コスト高。
- Gemini 3.5 Flash: $1.50/$9/Mトークン、Terminal-Bench 76.2%。コスト効率最高、1Mコンテキスト。
- Claude Opus 4.8（既存）: $5/$25/Mトークン、1Mコンテキスト、最高コーディング精度。
FX自動売買の構成（P-014の4層アーキテクチャ）において、Gemini 3.5 FlashはCost-sensitive層（テクニカル分析・データ前処理）、Claude Opus 4.8はHigh-value判断層（最終シグナル統合）という役割分担が最適候補。

**提案アクション**:
1. sandbox/FX自動取引/ のLLM呼び出し設定に「tier別LLMルーティング」を設計
2. 低信頼度・高頻度のデータ前処理にGemini 3.5 Flash（$1.50/Mで約3.3倍コスト削減）を割り当て
3. 最終判断（P-014の0.75超フルサイズエントリー条件）にのみClaude Opus 4.8を使用するルーティング実装

---

### P-025: FX自動取引エージェントへのHITL設計追加 — 日本AI事業者ガイドライン1.2版準拠

**根拠記事**: 078 (日本AI事業者ガイドライン1.2版)
**詳細**: 2026年3月31日公表のAI事業者ガイドライン1.2版でAIエージェントの外部アクションにHITL（Human-in-the-Loop）設計が義務化された（リスクベース段階的監視許容）。sandbox/FX自動取引/ は実資金を扱うエージェントであり、特に「外部アクション（売買注文送信）」にHITL設計が求められる。P-014（信頼度閾値）との組み合わせで、閾値ギリギリのケースは人間確認を挿入する設計が法令準拠かつリスク管理上有効。

**提案アクション**:
1. sandbox/FX自動取引/ に HITL checkpoint を追加: confidence 0.55-0.75 の中間帯は `input()` または通知待ちで人間確認を要求
2. ログ設計: AI判断・人間判断・最終取引の全履歴をトレーサブルに記録（ガイドライン1.2版のトレーサビリティ要件対応）
3. CLAUDE.mdのFX自動取引セクションに「日本AI事業者ガイドライン1.2版 HITL要件」を注記追加

---

### P-026: FX自動取引 — 3ヶ月実験の教訓をシステム設計に反映

**根拠記事**: 085 (AIトレーディングエージェント3ヶ月監視レポート)
**詳細**: 実際にLLMベーストレーディングエージェントを3ヶ月運用した第一人称レポートから得られた設計上の教訓: ①LLMの強みはニュース・感情分析・定性判断であり、短期価格予測は弱い。②バックテスト結果と実取引のパフォーマンス乖離が大きい（スリッページ・手数料・レイテンシ未考慮が原因）。③完全自律は現時点で限界があり、補助役割として使うべき。P-004・P-014・P-025の設計方針と整合しており、今後の開発優先度の根拠として活用できる。

**提案アクション**:
1. sandbox/FX自動取引/ のバックテスト設定にリアルスプレッド・スリッページ（pips）・コミッション・最大レイテンシを必ず含める
2. LLMシグナルの用途を「センチメント分析・ニュースフィルタリング」に絞り、エントリー/エグジットの最終判断はルールベースロジックに委ねる設計変更を検討
3. 毎月の実取引結果とバックテスト結果を比較する「乖離分析レポート」をSkill化（P-003のSkill提案群に追加）

---

## 2026-06-02 提案

### P-027: Context7 + rtkプラグインを日次収集エージェントに導入 — トークン節約

**根拠記事**: 098 (Best Claude Code Plugins tested), 099 (10 productivity workflows)
**詳細**: Context7プラグインは`/plugin install context7`でインストール後、Claude CodeがライブラリドキュメントをWebFetchせずにバージョン固定で参照できる。rtkはCLI出力をLLMコンテキストに入る前にフィルタリング・圧縮するツール。本プロジェクトの日次収集エージェントではWebSearch・WebFetchの結果がコンテキストを大量消費しており、両ツールの導入でコスト削減効果が見込める。Context7は「追加コンテキスト最小・精度向上最大」の最高ROIプラグインと評価されている。

**提案アクション**:
1. `/plugin install context7` でContext7プラグインをインストール
2. `pip install rtk` でrtkをインストールし、Bashコマンドの出力を事前圧縮するラッパーをHooksに設定
3. 日次収集エージェントのWebSearch後の出力をrtkでフィルタリングするプリプロセスを追加
4. Claude APIやAnthropicSDKのドキュメント参照をContext7経由に切り替え

---

### P-028: CLAUDE.md @インポート構文で3層構造への移行

**根拠記事**: 093 (CLAUDE.md Best Practices Ultimate Guide 2026 - amitray)
**詳細**: P-015（段階的開示3層構造）・P-002（CLAUDE.md整備）に対して、amitrayガイドの`@インポート構文`による具体的な実装方法が明確になった。CLAUDE.md本体（500語以内）→`.claude/rules/fx-trading.md`・`.claude/rules/library.md`・`.claude/rules/coding-style.md`へのインポートで、命令数を200以内に維持しながらトピック別詳細を保持できる。

**提案アクション**:
1. 現在のCLAUDE.md を監査し、FX自動取引・ライブラリ管理・コーディングスタイルの3カテゴリに分類
2. `.claude/rules/fx-trading.md`・`.claude/rules/library.md`・`.claude/rules/coding-style.md` を作成して移動
3. CLAUDE.md本体に `@.claude/rules/fx-trading.md` 等のインポート行を追加
4. CLAUDE.md本体が500語以内・削除基準「削除してもClaudeが間違えないなら削除」で精査

---

### P-029: TradingAgents v0.2.0でClaude 4.xバックエンドの実動テスト

**根拠記事**: 096 (TradingAgents Python tutorial - algoinsights)
**詳細**: TradingAgents v0.2.0（2026年2月）でClaude 4.x系（Opus 4.8等）をバックエンドLLMとして直接指定できるようになった。P-004（TradingAgentsアーキテクチャ採用）の実行環境として既存のAnthropicAPIキーを使ってローカルテストが可能。`pip install tradingagents`で環境構築でき、sandbox/FX自動取引/の概念実証として7エージェント構成を試せる。

**提案アクション**:
1. `pip install tradingagents` で環境構築
2. `ANTHROPIC_API_KEY` を設定してClaude Opus 4.8バックエンドでAAPL等で動作確認
3. FX通貨ペア（EUR/USD等）でのシグナル生成をテストし、P-014（信頼度閾値）のconfidence出力を確認
4. バックテスト結果のSharp比・ドローダウンを検証し、統計的信頼性を評価

---

### P-030: Quant AI Agents MT5のFastAPIアーキテクチャを sandbox/FX自動取引/ に適用

**根拠記事**: 095 (Quant AI Agents MT5 setup guide - mql5.com)
**詳細**: MT5ブリッジEA→Python FastAPI→LLM層のアーキテクチャが完全に公開された。出力JSONは`{signal, confidence, sl, tp, lot}`形式でP-014の信頼度閾値と完全互換。sandbox/FX自動取引/main.pyの現状（MT5連携目標）に対して、FastAPIサーバー追加→ブリッジEAアタッチの2ステップで実動テスト環境を構築できる。P-013（MetaTrader MCPサーバー）と組み合わせることでClaude Desktop→MT5の完全な自然言語制御パイプラインも実現可能。

**提案アクション**:
1. `pip install fastapi uvicorn anthropic` で環境構築
2. sandbox/FX自動取引/server.py として LLMシグナル生成FastAPIサーバーを実装（P-014の信頼度閾値ロジック込み）
3. MT5デモ口座でブリッジEAをアタッチし、Paperトレードモードで動作確認
4. P-025（HITL設計）のcheckpoint（confidence 0.55-0.75の中間帯で人間確認）を組み込む

---

### P-031: /ultrareview をFX自動取引コードのリリース前チェックに採用

**根拠記事**: 089 (Claude Code /ultrareview cloud agents)
**詳細**: /ultrareviewは5-20並列エージェントがバグを独立再現検証するクラウドレビューシステム。sandbox/FX自動取引/のコードは実資金を扱うためセキュリティ・ロジックバグのリスクが高く、特に`server.py`・`main.py`・注文送信ロジックのレビューに/ultrareviewが適している。`/ultrareview --pr <番号>`で特定PRを対象にできる。

**提案アクション**:
1. FX自動取引コードの主要機能実装後、`/ultrareview`でリリース前チェックを実施
2. 特に競合状態（注文の重複送信）・入力バリデーション（sl/tp/lot値の検証）・エラーハンドリングを重点的に検査
3. /ultrareviewの結果をPRコメントとして記録し、修正後に再実行して確認
4. Pro/Max/Team/Enterprise プランで利用可能。現在のプランを確認してから利用開始

---

## 2026-06-03 追加提案

---

### P-032: Hooks の `mcp_tool` ハンドラーをシグナル品質チェックに活用

**根拠記事**: 100 (Claude Code Hooks 完全2026リファレンス)
**詳細**: v2.1.141+でHooksハンドラーに `mcp_tool` タイプが追加された。これは既に接続済みのMCPサーバーのツールをhookから直接呼び出せる機能で、P-011（FastMCP FXバックテストデータ接続）と組み合わせることで、FX取引シグナル生成の`PostToolUse`フックから自動的にバックテスト検証ツールを呼び出すパイプラインが構築できる。例：Trader agentがシグナル出力（PostToolUse）→mcp_toolフックがFXバックテストMCPを呼び出してリアルタイム勝率確認→confidence閾値以下なら次のツール呼び出しをブロック（PreToolUse + exit 2）。

**提案アクション**:
1. settings.jsonに `PostToolUse` フックを追加し、`mcp_tool` ハンドラーでFXバックテストMCPサーバー（P-011）を呼び出す設定を記述
2. P-014の信頼度閾値（0.75+）をHookロジックとして実装し、CLAUDE.md依存から確定論的な実行に移行
3. `PreToolUse` + exit 2でconfidence 0.55未満のシグナルをブロック、0.55-0.75はP-025のHITL確認へルーティング

---

### P-033: TradingAgents v0.2.0 の Claude 4.x ネイティブ対応を FX 取引に活用

**根拠記事**: 108 (TradingAgents 2026 実装チュートリアル)
**詳細**: TradingAgents v0.2.0がClaude 4.x（含むClaude Opus 4.8）をネイティブサポートした。P-004（TradingAgentsアーキテクチャ採用）の実装ブロッカーが解消され、7エージェント構成（Market/Social/News/Fundamentals Analyst + Bull/Bear Researcher + Trader + Risk Manager）をそのままFXペアに適用できる。取引決定ごとに11 LLM呼び出し+20ツール呼び出しのコスト（約$0.5-2/決定）をP-006の課金変更（6/15）後の新クレジット枠で試算した上で実装判断が必要。AAPL累積リターン+26.62%（バイアンドホールド-5.23%対比）の実績はFXへの転用可能性を示唆するが統計的異常値の可能性も指摘あり。

**提案アクション**:
1. `pip install tradingagents` 後、Claude Opus 4.8バックエンドで通貨ペア（EUR/USD）を対象にデモ動作確認
2. 取引頻度・1決定あたりのAPIコスト・Agent SDKクレジット消費量を試算し、P-006（6/15課金変更）後の月次コスト見積もりを算出
3. Bull/Bear Researcherの対立論証パターンをP-014の信頼度閾値と統合（両者の合意スコアがconfidenceとして機能）

---

### P-034: FX 自動売買ボットのローカル LLM 化オプション検討

**根拠記事**: 109 (FX自動売買BotのローカルLLM切替実践)
**詳細**: FX相場稼働中はAPIサービス停止でボットが止まるリスクがある。国内個人開発者がqwen3.5:9b→gemma3:12bに切り替えて本番運用している事例が確認された。ローカルLLM化の3つのメリット：①外部API障害リスクの排除（uptime向上）、②APIコスト削減（Opus 4.8は$75/$150 per 1M tokens）、③取引ロジック・市況データの外部送信回避（セキュリティ）。一方でgpu資源・モデル管理コストが発生。P-033（TradingAgents + Claude 4.x）をメインとしつつ、ローカルLLM（LMStudio/Ollama経由でgemma3:12b or qwen3.5:14b）をフォールバックとする可用性設計が現実的。

**提案アクション**:
1. `ollama run gemma3:12b` でローカルLLMを起動し、FXシグナル生成の精度をClaude Opus 4.8と比較テスト
2. TradingAgentsのLLMプロバイダー設定をClaude API→ローカルOllama APIに切り替えて同一テストケースで精度・レイテンシを測定
3. メインはClaude API（高精度）、フォールバックはローカルLLM（可用性）のデュアル構成をsandbox/FX自動取引/config.pyに実装

---

## 2026-06-04 提案

### P-035: 白宮AI大統領令への対応 — FX自動取引ボットの「任意提出対象外」確認と開発方針明記

**根拠記事**: 122 (White House EO AI Innovation Security), 123 (NPR Trump AI safety order)
**詳細**: 2026年6月2日署名の大統領令は「最先端（フロンティア）AIモデル」の開発者に任意の政府提出を求める内容。bpr_labのFX自動取引ボットはフロンティアモデル開発者ではなく「APIユーザー」であるため直接の対象外。ただし、ボットが使用するClaude Opus 4.8はAnthropicが開発するフロンティアモデルであり、Anthropicが政府テストに参加した場合の新安全基準がAPIの利用可能機能・レスポンス形式に影響する可能性がある。また、Colorado州AI法（6月30日施行）はAI「利用者」も対象に含む可能性があり、FX自動売買のような「自動化意思決定システム」が適用範囲に入るか確認が必要。

**提案アクション**:
1. Colorado AI法（6月30日施行）のADMT（Automated Decision-Making Technology）適用範囲を確認し、FX自動売買ボットが対象か法的チェックを実施
2. sandbox/FX自動取引/README.mdに「本システムはClaude API利用者であり、フロンティアモデル開発者規制の直接対象外」という注記と、使用モデル・バージョン・用途を明記
3. P-025（HITL設計）の実装を優先し、「自動化意思決定への人間関与」を記録可能にしておくことでADMT規制への事前対応とする

---

### P-036: Microsoft Agent 365 SDK GA — Claude Agent SDKとの相互運用性検討

**根拠記事**: 118 (Microsoft Agent Framework at BUILD 2026), 124 (Microsoft Build 2026 recap)
**詳細**: Microsoft BUILD 2026でAgent 365 SDK（無料・フレームワーク非依存）がGAとなった。LangChain・OpenAI Agents SDK・LangGraph・Semantic Kernel・Azure AI Foundry と並列に**Claude Agent SDK**もサポートパッケージを提供予定。bpr_labの日次収集エージェントはClaude Agent SDKで構築されているが、Agent 365 SDKが提供するFoundry Agent Service（ホスト型エージェント）・Microsoft IQのWork IQ（M365知識）・Fabric IQ（データグラウンディング）との連携で、Excel/PowerPoint等のM365データをFX分析コンテキストに取り込む経路が開かれた可能性がある。競合ではなく補完的な位置づけとして評価すべき。

**提案アクション**:
1. Agent 365 SDKのClaude Agent SDK向けパッケージを確認し、統合の技術的実現性を調査
2. Microsoft Fabric IQ経由でExcelベースのFXデータ（MT5エクスポート）をClaude Agentのコンテキストに取り込むパイプライン設計を検討
3. 現在のClaude Agent SDK（P-003・P-008のSkills統合）はそのまま維持し、M365連携部分のみAgent 365 SDKを追加する差分アーキテクチャを採用

---

### P-037: FX自動取引の「Bot Pilot」運用体制と月次パフォーマンスレビュースキル化

**根拠記事**: 119 (AI Day Trading Bots Why Most Fail), 121 (Best AI Trading Agents 2026)
**詳細**: 2026年のAI取引ボット研究の共通知見として「48時間放置すれば大半のボットがストップロスに到達」「成功事例はBot Pilot（常時プロンプト調整する専門役割）が存在する」が確認された。Claude Sonnet 4.6は487%・Sharpe 1.94の成績を示したが、これも継続的なパラメータ調整の結果である可能性が高い。sandbox/FX自動取引/ のボットを単純な自動化ではなく「Bot Pilot + 自律実行」のハイブリッドとして設計する必要がある。月次の乖離分析（P-026）と組み合わせたレビュースキルのSkill化が実用的。

**提案アクション**:
1. `.claude/skills/fx-review/SKILL.md` を作成：月次取引結果サマリー・バックテスト乖離分析・戦略パラメータ調整提案の自動生成スキル
2. 週次の `/fx-review` 実行をRoutines（P-008）でスケジュール化し、毎週月曜AM7:00 JSTに自動実行
3. P-025（HITL）のconfidence閾値（0.55-0.75帯）を毎月見直す「Bot Pilot月次調整セッション」をCLAUDE.mdに手順として記録
4. LLMのニュース・感情分析機能（強み）と、ルールベース高頻度執行（弱みを補完）の役割分担をsandbox/FX自動取引/architecture.mdに明文化

---

## 2026-06-05 提案

### P-038: 自己学習型フックの実装 — セッション終了時に学習内容を CLAUDE.md へ自動追記

**根拠記事**: 128 (Dev.to 30 Skills MCPs Self-Learning Hooks)
**詳細**: 実チームの事例で「セッション終了フックがClaudeに学習内容を問い合わせてCLAUDE.mdへ自動追記する」自己学習型フックの有効性が実証された。現状のbpr_labセットアップではセッション間の知識継承は手動であり、知見が蓄積されない課題がある。フックはstdout/stderrとexitコードのみ通信し、シェルコマンドで実装できる（SDK不要）。例: `PostResponse` フックで `claude -p "このセッションで学んだ技術的な知見を箇条書きで出力" >> CLAUDE.md` を実行するパターン。

**提案アクション**:
1. `.claude/settings.json` の `hooks` セクションに `PostResponse` または `Stop` フックを追加し、学習内容抽出プロンプトを設定
2. 追記先はプロジェクトのCLAUDE.mdの「セッション学習ログ」セクション（日付付き）として整理
3. ノイズを防ぐため、追記条件として「ツール呼び出しが3件以上あったセッション」のみ発火させる

---

### P-039: Claude Code 4象限フレームワークによる bpr_lab スキル体系の再整理

**根拠記事**: 135 (GenAI Unplugged Skills/Hooks/Agents Tutorial), 129 (CLAUDE.md Best Practices)
**詳細**: 「CLAUDE.md=メモリ、Skills=ルーティン、Hooks=保証、Agents=委任」の4象限フレームワークが標準的な設計指針として確立した。bpr_labの現在の構成を4象限で棚卸しし、①CLAUDE.mdの肥大化防止（200行以下）、②限定的ワークフローのSkills移行、③自動品質保証のHooks実装、④大規模タスクのAgent委任の4方向で最適化できる。特に日次収集エージェント（本スクリプト）がHooksで自動化できる部分とAgentとして委任すべき部分の境界を明確化すべき。

**提案アクション**:
1. 現在のCLAUDE.md（存在する場合）を4象限で分類し、Skills移行候補を特定
2. `~/.claude/skills/` に「日次収集」「FXシグナル分析」「コードレビュー」「デプロイ」の最低4スキルを整備
3. Hooks候補として「ファイル保存時の命名規則チェック」「コミット前の型チェック実行」「記事追加時のcatalog.md自動更新」を実装

---

### P-040: Claude Opus 4.8 GA確認 — P-033 TradingAgents実装ブロッカー解除

**根拠記事**: 126 (Claude Opus 4.8 公式リリース), 136 (TradingAgents 正式リリース)
**詳細**: Claude Opus 4.8が2026年5月28日に正式GA（Anthropic API・Bedrock・Vertex AI・Microsoft Foundry全対応）。P-033（TradingAgents + Claude 4.x）の実装ブロッカーであった「Claude 4.xの安定GA未確認」が解消された。TradingAgentsのv0.2.0マルチプロバイダー対応と合わせて、今すぐ `tradingagents --llm anthropic --model claude-opus-4-8` の構成でプロトタイプを実装できる。Fast Modeが2.5×速度・3分の1コストで利用可能なため、バックテスト段階ではFast Modeで試算コストを抑えることが推奨される。

**提案アクション**:
1. P-033のアクション1「デモ動作確認」を即時実行：`pip install tradingagents[anthropic]` 後にEUR/USDで動作確認
2. Fast ModeとStandard Modeで同一バックテストを実行し、精度差とコスト差を計測（目標: コスト3分の1で精度95%以上維持）
3. sandbox/FX自動取引/ の `config.py` に `LLM_PROVIDER=anthropic`・`MODEL=claude-opus-4-8`・`USE_FAST_MODE=True`（バックテスト用）を追加

---

### P-041: MCP サーバーのステートレス設計方針への移行準備

**根拠記事**: 134 (MCP Cheat Sheet 2026), 133 (Claude Agent SDK Managed Agents)
**詳細**: MCPの2026年ロードマップ核心は「ステートレス動作への移行」（現行: セッション維持が必須 → 移行後: ステートレスで水平スケーリング可能）。bpr_labでMCPサーバーを新規開発する際（FX自動取引データ取得MCP等）は、今からステートレス設計を採用することで将来の仕様対応コストをゼロにできる。FastMCP 3.0がデコレータ1行でPythonサーバー実装を実現しており、新規MCPの開発コストが大幅低下。加えてMCPトンネル（リサーチプレビュー）によりプライベートネット内MT5サーバーへの安全接続が可能になる見通し。

**提案アクション**:
1. sandbox/FX自動取引/ 向けのMT5データ取得MCPサーバーをFastMCP 3.0でステートレス実装（`@mcp.tool()` デコレータ使用）
2. MCPサーバーはステートをRedis/SQLiteに外出しし、サーバー本体は常にステートレスになるよう設計
3. MCPトンネルの正式リリース後に、VPS上のMT5インスタンスへのMCPアクセス経路を評価


---

## 2026-06-06 提案

### P-042: Dynamic Workflows を日次収集エージェントに適用 — ドメイン並列検索の高速化

**根拠記事**: 145 (Claude Code Dynamic Workflows InfoQ), 146 (5 Workflow Patterns MindStudio)
**詳細**: 現在の日次収集エージェントは4ドメイン×複数クエリを逐次実行しており、全クエリ完了まで5〜10分かかる。Dynamic Workflows（JS オーケストレーションスクリプト）を使えば4ドメインを並列サブエージェントで同時検索し、所要時間を1/4程度に短縮できる見通し。Plan-then-Execute パターン（最もコスト効率が高い）と組み合わせることで、まず収集計画を立ててから並列実行する構成が最適。Max/Team/Enterprise + Claude API で利用可能。トークン消費は逐次実行の1.2〜1.5倍程度になるが、時間短縮の価値が上回る。

**提案アクション**:
1. 日次収集プロンプトをDynamic Workflows対応のJS仕様に書き直す（各ドメイン=独立サブエージェント、最後にmerge集約）
2. `code.claude.com/docs/en/workflows` の仕様を参照し、並列化可能な境界（ドメイン別）とシリアル実行が必要な境界（重複排除・catalog更新）を特定
3. 既存の逐次版と並列版で同一日の収集結果を比較し、品質・コスト・所要時間の差を計測してから本格移行を判断

---

### P-043: TradingAgents 再現性リスクへの対応 — LLMバージョン固定とベースライン検証

**根拠記事**: 154 (TradingAgents Reproducibility ACM ICAIF 2026)
**詳細**: ACM ICAIF 2026論文が「センチメント分析精度がLLMバージョンに強く依存するため再現性リスクがある」と実証した。P-033・P-040（TradingAgents + Claude Opus 4.8）を実装する際、LLMのバージョン変更（例: Opus 4.8 → 4.9）で戦略パフォーマンスが大幅に変動する可能性がある。本番運用では「使用モデルバージョンの固定」と「バージョン変更時のリグレッションテスト」が必須。また、ルックアヘッドバイアスを排除した厳密なバックテスト環境の構築が再現性の前提条件。

**提案アクション**:
1. `sandbox/FX自動取引/config.py` でLLMモデルバージョンを明示固定（`claude-opus-4-8` を浮動バージョンではなく確定バージョンで指定）し、変更時にテストを強制するCI設定を追加
2. バックテスト用のポイント・イン・タイム（PIT）データセットを用意し、ルックアヘッドバイアスを排除した評価環境を構築
3. LLMバージョン変更前後でシャープレシオ・最大ドローダウン・勝率の3指標を自動比較するリグレッションテストスクリプトを実装

---

### P-044: Mercury 2 評価 — FX自動取引の高頻度センチメント分析コスト削減

**根拠記事**: 156 (Mercury 2 Inception Labs 拡散LLM)
**詳細**: Inception LabsのMercury 2（2026年2月GA）は1,000トークン/秒超の生成速度・Claude 4.5 Haikuの1/10コストを実現する拡散アーキテクチャLLM。品質はHaikuクラス相当（Haiku/Flash相当、OpusやGPT-4レベルではない）。FX自動取引でセンチメント分析（ニュースヘッドライン・X投稿の感情スコアリング）をリアルタイム高頻度実行する場合、Opusの高品質な推論が不要なタスクにMercury 2を採用することでコストを90%削減できる可能性がある。OpenAI API互換のため既存コードの変更は最小限。

**提案アクション**:
1. FX自動取引ボットのタスクを「高品質推論が必要なもの（戦略判断・最終売買決定）」と「大量処理が必要なもの（ニュース感情スコアリング・フィルタリング）」に分類
2. 後者にMercury 2 API（`inceptionlabs.ai`）を試験導入し、Claude Haiku と同一テストケースで精度・コスト・レイテンシを比較
3. 精度が許容水準（感情スコア相関>0.85）ならMercury 2を大量処理パスに採用し、戦略判断のみClaudeを使うハイブリッドアーキテクチャに移行

---

### P-045: Claude Code Auto Mode 有効化 と CLAUDE.md 権限設計の見直し

**根拠記事**: 144 (Anthropic Claude Code Auto Mode Engineering Blog)
**詳細**: Anthropicエンジニアリングブログによれば、Auto Modeはルールベースではなくモデルによるリスクスコア評価で動的に権限を制御する。Pro プランはSonnet 4.6、Max/Enterprise は Opus 4.8 で動作。「デストラクティブな操作」（git reset --hard・rm -rf・外部API書き込み等）のみブロックし、通常の開発操作はパーミッション確認なしで進む。現在のbpr_labでは毎回のパーミッション確認が作業を中断しているため、Auto Mode有効化とCLAUDE.md上での「禁止操作明示」のセットアップで大幅に開発速度が向上する見込み。

**提案アクション**:
1. Claude Code設定でAuto Modeを有効化し（`/auto` コマンドまたは設定ファイル）、プロジェクトのCLAUDE.mdに「Auto Mode適用範囲と禁止操作リスト」を明記
2. CLAUDE.mdの「禁止操作」セクションに `git push --force`・`DROP TABLE`・`rm -rf`・本番APIへの直接書き込み等を列挙し、Auto Modeのリスク判定精度を補強
3. Auto Mode有効後に1週間の試用期間を設け、意図しないブロックや意図しない実行が発生していないかログで確認（`~/.claude/logs/`を定期確認）

---

## 2026-06-07 提案

### P-046: Anthropic IPO後の API価格変動リスクを bpr_lab コスト設計に組み込む

**根拠記事**: 160 (Anthropic IPO S-1 機密提出), 168 (Anthropic Q2 2026 初の営業黒字)
**詳細**: AnthropicがSECにS-1を機密提出（2026年6月1日）。評価額$965B・年換算売上$47Bの上場申請企業として、上場後は投資家の期待収益への対応のためAPI価格戦略が変化する可能性がある。一方Q2で初の営業黒字（$559M）を達成しており、AWS/Googleとの大型コンピュート契約（$50B超）が利益率改善の下支えになっている。FX自動取引ボットのコスト試算（P-006）に「API価格+10%・+30%・+50%シナリオ」を追加し、各シナリオでの月次コスト変化をconfig.pyに試算式として実装しておくことを推奨。

**提案アクション**:
1. sandbox/FX自動取引/config.py に `API_COST_MULTIPLIER` 変数を追加し、価格シナリオ切替を1行で対応可能にする
2. README.md に「APIプロバイダーはIPO後価格変動リスク有り。代替（ローカルLLM・P-034）への切替手順を記録」を注記
3. P-006（課金変更）とP-024（tier別LLMルーティング）を組み合わせた月次コスト上限アラートの設計を検討

---

### P-047: SpaceXコンピュート提携による利用制限拡大を FX 並列バックテストに即活用

**根拠記事**: 161 (Anthropic-SpaceX Colossus), 171 (窓の杜 SpaceX JA)
**詳細**: Claude Codeの5時間レート制限が全プランで2倍になった（2026年5月6日施行）。P-021（7月13日まで50%増枠）・P-023（4-8並列worktree）と合わせると、現在がbpr_lab史上で最も高いレート制限を享受できる時期。FXバックテスト（複数通貨ペア×複数戦略の組み合わせ）をこの期間中に集中的に実行し、戦略パラメータの初期最適化を完了させることを推奨。

**提案アクション**:
1. P-009（Dynamic Workflows並列バックテスト）を今週中に着手（7月13日の制限戻りまでに完了目標）
2. 5時間制限2倍＋50%増枠＋並列4-8worktreeの組み合わせでの最大スループットを計算し、バックテスト計画に反映
3. SpaceX Colossus提携の継続期間（発表上は「月内」だが長期化の可能性）を定期的にモニタリング

---

### P-048: Apple Xcode 26.3 統合 → Claude Agent SDK のクロスプラットフォーム活用検討

**根拠記事**: 162 (Apple Xcode 26.3 Claude Agent SDK ネイティブ統合)
**詳細**: Xcode 26.3にClaude Agent SDKがネイティブ統合された（2026年2月3日）。VS Code・JetBrains・Xcodeと主要IDEでの公式統合が揃い、Claude Agent SDKが「IDE非依存のAIエージェント標準」としての地位を確立した。bpr_labのFX自動取引ボット開発がMacOS環境で行われている場合、Xcode経由でのビジュアルプレビュー・クラッシュログ自動解析・ユニットテスト自動実行ループが追加のコスト不要で利用可能になる。

**提案アクション**:
1. 現在のbpr_lab開発環境（OS・IDE）を確認し、Xcode 26.3以降を使用している場合はClaude Agent SDK統合を設定
2. sandbox/FX自動取引/ のPythonコードをXcode Projectに追加し、Xcode PreviewsではなくCrash Loggerとの統合を検討
3. MCP経由のClaude Code CLIからXcode機能にアクセスする設定（Xcode MCP）のセットアップ手順を.claude/rules/ に記録

---

### P-049: 米国連邦AI法案（269ページ）の成立動向を監視 — Colorado AI法 6/30 施行との関係

**根拠記事**: 163 (AIニュース 2026年6月7日), 158 (2026年米国AI規制総覧)
**詳細**: 2026年6月7日、米議会でAI関連の269ページ法案が提出された。この法案は全州AI法を上書きする連邦プリエンプション条項を含む可能性があり、Colorado AI法（2026年6月30日施行・ADMTリスク管理義務）が無効化される可能性がある。P-035（FX自動売買ボットのColorado法適用可能性確認）は、この連邦法案の成立状況次第で対応優先度が変わる。

**提案アクション**:
1. 2026年6月末に連邦AI法案の審議状況を再確認し、Colorado AI法との関係を法的に評価
2. P-035のアクション1（Colorado AI法のADMT適用範囲確認）は6月30日施行前に完了させる（連邦法案が成立するまではColorado法が有効）
3. 連邦AI法案が成立した場合の新規コンプライアンス要件をCLAUDE.mdに更新

---

### P-050: 国産LLM「LLM-jp-4」をFX自動取引のニュース感情分析コスト削減に検討

**根拠記事**: 176 (国産LLM LLM-jp-4 NII オープンソース公開)
**詳細**: 国立情報学研究所（NII）が2026年4月3日に公開した「LLM-jp-4（8B/32B）」はオープンソース・商用利用可能・12兆トークン学習で一部ベンチマークGPT-4o超え。P-034（ローカルLLM化オプション）・P-044（Mercury 2コスト削減）と同様のハイブリッドアーキテクチャの候補として評価可能。日本語ニュースの感情分析に特化した性能を発揮する可能性があり、FXボットの高頻度ニュースフィルタリングレイヤーに適用できれば外部APIコストを大幅削減できる。

**提案アクション**:
1. LLM-jp-4 8Bモデルを`ollama run`または`vLLM`でローカル起動し、日本語FXニュースの感情分析精度をClaude Haiku 4.5と比較テスト
2. P-044（Mercury 2）とLLM-jp-4の精度・コスト・レイテンシを同一テストセットで3モデル比較（Claude Haiku / Mercury 2 / LLM-jp-4）
3. 最優秀モデルをFXボットの「大量処理パス（ニュース感情スコアリング）」に採用し、「高品質推論パス（最終売買判断）」にClaudeを使うアーキテクチャを実装

---

## 2026-06-08 提案

### P-051: Anthropic公式MCP設計術「98.7%トークン削減」を日次収集エージェントのMCP設計に適用

**根拠記事**: 189 (Zenn - Anthropic公式MCPサーバー設計術 98.7%トークン削減)
**詳細**: Anthropic公式リファレンスから逆引きされた設計パターンで「Tool descriptionを簡潔に保つことで98.7%のトークン削減を達成（実測値）」が実証された。日次収集エージェントでは現在WebSearch結果がコンテキストを大量消費している。もし将来MCPサーバーを経由して収集ロジックを実装する場合（P-011参照）、この設計パターンの採用でコストを劇的に削減できる。加えてResourcesプリミティブを活用したURLだけ渡すパターン（P-027のrtk圧縮と補完的）が有効。

**提案アクション**:
1. 日次収集エージェントの各WebSearch結果の出力を「URLのみ→必要時にWebFetch」のパターンに変更し、トークン消費を削減
2. P-011（FastMCP FXバックテストMCPサーバー）の設計時に、Tool description を50文字以内・パラメータを3つ以内に制限するルールをCLAUDE.mdに追記
3. Resourcesプリミティブを活用し、大量データは `resource://backtest/result/{id}` 形式のURIで参照するステートレス設計を採用（P-041との統合）

---

### P-052: 3大AIエージェントSDK比較の知見を bpr_lab のSDK選択方針として明文化

**根拠記事**: 191 (Composio - Claude Agent SDK vs OpenAI vs Google ADK比較)
**詳細**: bpr_labのFX自動取引ボット・日次収集エージェントはClaude Agent SDKをメインSDKとして使用しているが、その選択根拠がドキュメント化されていない。3大SDKの比較知見を踏まえて：Claude Agent SDK = MCP最深統合・ファイルシステム/シェルアクセスビルトイン・サブエージェントネイティブのため、コードベース操作・ローカルファイル処理・MCP統合が中心のbpr_labプロジェクトに最適。ただし6/15以降のAgent SDK課金変更（P-006・P-012参照）後は、コスト感応度の高いタスクにOpenAI Agents SDK（マルチベンダー対応）の部分採用を検討する余地がある。

**提案アクション**:
1. sandbox/FX自動取引/README.md に「SDK選択理由: Claude Agent SDKを採用する根拠（MCP統合・ファイルシステムアクセス・ローカルエージェントパイプライン）」を記録
2. 将来的にOpenAI/Geminiモデルをフォールバックとして追加する場合（P-034・P-024参照）に備え、SDKを抽象化するプロバイダーレイヤーの設計をarchitecture.mdに記載
3. P-006（6/15課金変更）後のAgent SDK月次コストが許容範囲を超えた場合の代替SDK切替手順を.claude/rules/cost-control.mdに記録

---

### P-053: 47本FXロボット実検証レポートの設計方針をサンドボックス評価フレームワークに反映

**根拠記事**: 196 (Medium - 47本FXロボット$11,400損失レポート)
**詳細**: 実際に47本のFXロボットをライブ運用してテストした第一人称レポートから、bpr_labの sandbox/FX自動取引/ に直接適用できる設計原則が得られた：①バックテスト良好→ライブ失敗のパターンは「過剰最適化」が原因（P-043のLLMバージョン固定と同じ根本問題）；②「AI搭載」の大半はラベルのみで実際のLLM活用なし（本プロジェクトはClaude APIを本当に使う差別化があり有利）；③成功ロボットに共通する最大DD 10%以下の厳格なリスク管理。これは P-014（信頼度閾値）・P-025（HITL設計）・P-043（LLMバージョン固定）と整合する実証データとして位置づけられる。

**提案アクション**:
1. sandbox/FX自動取引/evaluation_framework.md を作成し、「最低3ヶ月フォワードテスト必須」「最大DD 10%以内をロボット採用基準」「バックテストとライブの乖離分析を毎月実施（P-026）」の評価基準を明文化
2. P-014（信頼度閾値）を「最大DD 10%以下を維持するための信頼度閾値キャリブレーション」として位置付け、閾値と実際のドローダウンの関係を記録・更新するテーブルをconfigに追加
3. evaluation_framework.md に「LLM本当活用の差別化ポイント（ニュース感情分析・多角的シナリオ分析・非線形判断）」と「LLMが不得意なこと（短期価格予測・ノイズの多い市場での過適応）」を明記し、システム設計の範囲と限界を文書化

---

## 2026-06-09 提案

### P-054: Claude Fable 5モデルアップグレード検討 — agenticコーディング性能でOpus 4.8を+11pt超え

**根拠記事**: 200 (Claude Fable 5 リリース VentureBeat), 201 (Fable 5 ベンチマーク Vellum)
**詳細**: 2026年6月9日リリースのClaude Fable 5はSWE-Bench Pro agentic codingで80.3%（Opus 4.8: 69.2%）を達成。GPT-5.5（58.6%）・Gemini 3.1 Pro（54.2%）を大幅リード。価格はFable 5が$10/$50/Mトークン（Opus 4.8の$5/$25の2倍）。コーディング重視タスク（FX自動取引コード生成・sandbox/FX自動取引/のリファクタリング・バグ修正）では費用対効果がOpus 4.8を上回る可能性がある。ただし高リスクトピックはOpus 4.8へフォールバック（セッション5%未満）。P-007（Opus 4.8アップグレード）・P-040（TradingAgents実装）のモデル選択を見直す必要がある。

**提案アクション**:
1. Claude Fable 5の`claude-fable-5-20260609`（仮）モデルIDをAnthropicドキュメントで確認し、sandbox/FX自動取引/config.pyの `PREMIUM_MODEL` 変数を更新
2. 同一バックテストタスクをOpus 4.8とFable 5で実行し、コーディング品質（コードレビュー自動スコア）と推論時間を比較
3. P-033（TradingAgents + Claude 4.x）でFable 5バックエンドを試験：AAPL等のバックテストでOpus 4.8対比のパフォーマンス差を計測
4. 日次収集エージェント（本スクリプト）でもFable 5を試験し、SIGNAL/NOISE分類精度の変化を記録

---

### P-055: Great American AI Act草案 — Colorado AI法改正後の規制環境変化でP-035・P-049を更新

**根拠記事**: 206 (Great American AI Act FedScoop), 207 (Colorado SB 26-189 TechTimes)
**詳細**: P-035・P-049の前提が変化した。Colorado SB 26-189（2026年5月9日成立）により：(1)旧Colorado AI法（SB24-205）は廃止・置換済み、(2)新法（SB 26-189）は規制対象をADMTに絞り込み・施行日を2027年1月1日へ延期。加えてGAGAIA（Great American AI Act）が6月4日に草案公開され、州法3年プリエンプション条項が含まれる。仮にGAGAIAが成立すればColorado SB 26-189も3年間プリエンプションされる可能性があり、P-035のコンプライアンス判断が流動的になった。現時点での実務的結論：2027年1月1日施行まで余裕があるため、P-025（HITL設計）の実装を優先しつつ連邦法成立動向を監視。

**提案アクション**:
1. P-035・P-049の提案状態を「待機中：連邦GAAIA成立動向監視」にステータス更新
2. CLAUDE.mdのFX自動取引セクションに「使用AIシステムはClaude API利用者（フロンティアモデル開発者ではない）。ADMT規制の直接対象は2027年1月施行のColorado SB 26-189のみ、GAAIA成立で変更の可能性あり」を注記
3. 次回の連邦GAAIA審議状況確認スケジュールを2026年9月末に設定（3年プリエンプション条項の修正・廃止の可能性を含めて評価）

---

### P-056: Claude Code fallbackModel設定をFX自動取引パイプラインに組み込む

**根拠記事**: 209 (Claude Code fallbackModel設定ガイド - AIforAnything)
**詳細**: P-006（529過負荷エラー対策）の具体的実装方法が確立した。v2.1.166+のfallbackModel設定で最大3つのバックアップモデルを設定でき、過負荷時にユーザー操作不要でフォールバック。バックグラウンドセッション（--detach）もフォールバック設定を継承するため、FX自動取引ボットの夜間無人稼働時のAPI障害リスクが低減できる。P-034（ローカルLLMフォールバック）の前段として、まずfallbackModel（Claude Haiku 4.5）でAPI内フォールバックを確立し、それでも失敗する場合（プラットフォーム全体障害）にローカルLLMへ委譲するという2段階可用性設計が現実的。

**提案アクション**:
1. `sandbox/FX自動取引/.claude/settings.json`（または相当する設定）に `"fallbackModel": ["claude-haiku-4-5-20251001"]` を追加
2. P-024（tier別LLMルーティング）と統合：高品質判断レイヤーは `claude-fable-5` (or `claude-opus-4-8`) をprimary・`claude-sonnet-4-6` をfallback1・`claude-haiku-4-5` をfallback2に設定
3. バックグラウンドセッション（`claude --bg`）で稼働中のFX取引エージェントがfallbackModelを正しく継承するか、ステージング環境で意図的に529エラーを発生させて確認

---

### P-057: Anthropic社員活用術の「サブエージェント利用判断基準」をCLAUDE.mdに明記

**根拠記事**: 210 (Anthropic社員Claude Code活用術8選 Zenn)
**詳細**: Anthropic公式レポート由来の「10ファイル以上の探索 or 3つ以上の独立作業 → サブエージェント使用シグナル」という定量的基準はCLAUDE.mdの運用ルールとして採用できる。現在のbpr_labでは日次収集エージェント（4ドメイン）がこの基準に合致しており、P-023（4-8並列worktreeの標準化）・P-042（Dynamic Workflows適用）の実装優先度を高める根拠となる。また「コンテキストエンジニアリング（構造設計重視）」というパラダイムシフトはCLAUDE.mdの設計思想に直結する。

**提案アクション**:
1. CLAUDE.mdに「サブエージェント使用シグナル：10ファイル超の探索が必要な場合 または 3つ以上の独立作業を含む場合（Anthropic公式基準2026）」を追記
2. P-023のSubagent YAML定義作成時に上記基準を組み込んだオーケストレーターエージェントの判断ロジックを設計
3. 「成功基準の先行定義」（例：「テスト全通過」「このAPIレスポンスがこの形式」）をClaude Code使用時の標準プロセスとしてCLAUDE.mdに追記（ステップ指示よりも成果物記述が効果的）

---

### P-058: Claude Agent SDK 6/15請求変更への対応準備

**根拠記事**: 219 (Claude Agent SDK Complete Guide - Hidekazu Konishi)
**詳細**: 2026年6月15日より、Claude Agent SDK / `claude -p` / Claude Code GitHub Actions / 第三者エージェントがサブスクリプション枠から切り離され、専用クレジットプール（フルAPIレート課金）に移行。bpr_labの日次収集エージェントが `claude -p` 経由で実行されている場合、6/15以降は費用が発生するクレジットプールから引かれる。

**提案アクション**:
1. bpr_labの日次収集ワークフローが `claude -p` を使っているか確認し、使っている場合はMonthlyクレジット上限を設定（Claude設定 → Agent SDK Credit Limitから設定可能）
2. FX自動取引サンドボックスがAgent SDKを使う場合は同様に上限設定を検討
3. CLAUDE.mdに「Agent SDK / claude -p 実行は6/15以降クレジットプール消費（フルAPIレート）。バッチ処理はMessage Batches API優先で30%コスト削減」を注記

---

### P-059: FX自動取引へのONNX/MT5内蔵NN実行パターン採用検討

**根拠記事**: 220 (AI Trading Tools 2026 - Ventureburn)
**詳細**: MT5のONNX統合を使えば、Python外部スクリプト不要でEA（MQL5）内から直接ニューラルネットワークモデルを実行できる。現在のsandbox/FX自動取引/がPython+ZeroMQ/REST APIブリッジでMT5と通信する構成を採用している場合、高頻度の判断部分（テクニカル指標計算など）はONNX経由でEA内蔵に移行することでレイテンシ削減が可能。LLMセンチメント分析（低頻度・高コスト）は引き続きPython側でClaude APIを呼び出す2層構造が現実的。

**提案アクション**:
1. `sandbox/FX自動取引/` の現行アーキテクチャを確認し、EA内ONNX推論とPython側LLM分析の責任分界点を設計
2. テクニカル判断（エントリー/エグジット条件）はONNX化、センチメント・ファンダメンタル判断はClaude API（claude-haiku-4-5 軽量モデル）に割り当てる「コスト最適2層」構成を文書化
3. P-005（MT5+Python+LLM統合パターン）と統合した実装ロードマップを更新

---

## 2026-06-11 提案

### P-061: MCP RC breaking changes 実装移行 — P-017補強・エラーコード変更対応

**根拠記事**: 223 (MCP 2026-07-28 RC 公式ブログ), 208 (Medium MCP RC解説)
**詳細**: P-017で「RC仕様準拠設計」を提案していたが、2026-07-28の公式RCブログポストで具体的なbreaking changesが確定した。最も影響が大きいのはエラーコード変更（-32002→-32602）と初期化ハンドシェイク廃止。現在稼働中・開発中のMCPクライアントコード（P-011のバックテストMCPサーバー、P-013のMetaTrader MCPサーバー）がこれらの変更でサイレントに壊れる可能性がある。移行期間付きなので緊急対応は不要だが、新規実装はRC仕様で始めるべき。

**提案アクション**:
1. 現在のコードベースで `-32002` エラーコードを参照している箇所を検索（`grep -r "\-32002" .`）し、`-32602` への移行計画を立案
2. P-011・P-013のMCPサーバー実装開始時にステートレス設計を前提とし、初期化ハンドシェイクを持ち込まない
3. 2026年7月28日の最終仕様公開後2週間以内に既存MCPツール設定の互換性検証を実施するスケジュールをCLAUDE.mdに記録

---

### P-062: TradingAgents実装のオーケストレーター選定 — LangGraph 0.4を正式推奨

**根拠記事**: 225 (LangGraph vs AutoGen 2026 DEV Community), 226 (TradingAgents Docker tutorial)
**詳細**: 2026年の本番AIエージェントフレームワーク比較記事により、P-033（TradingAgents + Claude 4.x実装）のオーケストレーター選定に明確な根拠が得られた。TradingAgentsはLangGraphベースで実装されており（P-004で確認済み）、2026年の比較研究でもLangGraph 0.4以降が「監査可能性・チェックポイント・Human承認ゲート」の観点で本番最適と評価された。AutoGenは研究プロトタイピングに向くが、実資金を扱うFXボット（P-025 HITL必須）にはLangGraphが適合する。

**提案アクション**:
1. P-033のTradingAgents実装にあたり `pip install langraph>=0.4` を明示的に要件として記録
2. FXシグナル生成の各ステップ（データ取得→分析→シグナル→HITL確認→執行）をLangGraphノードとして設計し、各ノード間にP-025のHITLチェックポイントを挿入
3. LangSmithとの統合（無料Tier利用可）でエージェントの意思決定プロセスを追跡し、P-037（月次パフォーマンスレビュー）のデータソースとして活用

---

### P-063: MT5/MQL5コード生成にはClaude Opusが最高品質 — FX開発モデル選択の根拠確定

**根拠記事**: 230 (QuantLabs LLM Showdown 2026), 155 (FX自動売買LLM活用実験記録 JA)
**詳細**: QuantLabsの比較実験でClaude（Opus系）がMT5/MQL5コード生成において「コード構造・ドキュメント品質・MQL5特有構文エラー率」で最高評価を得た（2026年）。特にPython-MQL5橋渡しコードとZeroMQブリッジ実装でGPT-5.5・DeepSeek R3を上回る完成度。一方でDeepSeek R3はOpusの90%品質をコストの約3分の1で実現するため、コスト重視の反復開発フェーズに適している。この実証データはP-024（tier別LLMルーティング）の具体的な実装根拠となる。

**提案アクション**:
1. `sandbox/FX自動取引/` のMQL5コード生成・レビュータスクには `claude-fable-5` または `claude-opus-4-8` を指定（P-063根拠：MT5特有構文エラー最小）
2. P-024のtier設計を更新：「MQL5/MT5コード生成 → Claude Opus」「ニュースセンチメントスコアリング → DeepSeek R3またはMercury 2」の役割分担を config.py に明記
3. QuantLabsのプロンプトテンプレート（取引ロジック記述フォーマット）を参考に、`.claude/skills/fx-codegen/SKILL.md` のプロンプト設計を最適化

---

### P-060: Skills SKILL.md descriptionの自然言語最適化

**根拠記事**: 216 (100 Claude Skills試用 - PyCoach), 217 (70+ Skills自作 - PyCoach)
**詳細**: 100件・70件の大規模Skills実験から得られた知見：「SKILL.mdのdescriptionを自然言語で具体的に書くほど、自動トリガー精度が上がる」「スキルは小さく・焦点を絞って作る」「チーム共有はgitサブモジュールかnpmパッケージが有効」。bpr_labの既存スキル（.claude/skills/配下）のdescriptionが曖昧・短い場合、自動トリガーが外れてスキルが活用されていない可能性がある。

**提案アクション**:
1. bpr_labの `.claude/skills/*/SKILL.md` を一覧し、各スキルのdescriptionを「いつ・何のために使うか」を具体的に記した自然言語文に書き直す
2. 1スキル1責務の原則で肥大化しているスキルを分割（特にcurateスキルなど複数処理を含むもの）
3. 更新後、3回の日次収集で自動トリガー率を測定し効果を確認

---

## 2026-06-12 提案

### P-064: Claude Fable 5 本番採用 + セーフガード透明性ポリシー対応

**根拠記事**: 235 (Claude Fable 5 公式リリース), 237 (秘密妨害ルール撤回), 242 (TrueFoundry完全ガイド)
**詳細**: Claude Fable 5（claude-fable-5-20260609）が正式GAとなり、P-054の「コーディング性能でOpus 4.8を+11pt超え」の前提がSWE-Bench Pro 80.3%（vs Opus 4.8: 69.2%）で実証された。ただし6月9日リリース直後に発覚した「フロンティアLLM開発に関する要求を不可視で劣化させるセーフガード」問題は、企業ユーザーの信頼性懸念として残っている（Anthropicは「誤ったトレードオフ」として可視化方針に変更）。また旧ゼロリテンション契約ユーザーへの30日データ保持義務化は未解決の可能性がある。エンタープライズ用途では使用するモデルと使用目的の組み合わせを明示記録することでコンプライアンスリスクを管理。

**提案アクション**:
1. sandbox/FX自動取引/config.py の `PREMIUM_MODEL` を `claude-fable-5-20260609` に更新し、同一バックテストタスクでOpus 4.8対比の精度とコストを計測
2. CLAUDE.mdに「Fable 5を使用するタスク一覧：コーディング・リファクタリング・バグ修正。使用しないタスク：生物学・フロンティアAI研究関連（過剰制限が発生する可能性）」を明記
3. 旧ゼロリテンション契約（エンタープライズ）の場合、30日データ保持ポリシー変更の適用状況を確認し、機密データをFable 5に送信する前に法務確認を実施

---

### P-065: Claude Code 5段階ネストサブエージェントを日次収集エージェントに適用

**根拠記事**: 236 (Claude Code 2026年6月大型アップデート), 243 (5段階ネストサブエージェント ofox.ai)
**詳細**: v2.1.172（2026年6月10日）で最大5段階のネストサブエージェントが解禁された。現在の日次収集エージェントは4ドメイン並列（P-023）だが、ネスト機能を使うことで「ドメイン別オーケストレーター（Layer 1）→各クエリ実行エージェント（Layer 2）→記事品質チェック（Layer 3）」の3層構成が可能になる。推奨深さは2〜3段階（ofox.ai）であり、過深ネストによるコスト指数増大に注意。モデルは外側（Layer 1）にOpus/Fable 5、内側（Layer 2-3）にSonnet/Haikuを割り当てることでコスト最適化できる。

**提案アクション**:
1. P-023の4ドメイン並列Subagent YAML定義を「Layer 1: ドメインオーケストレーター × 4、Layer 2: クエリ実行エージェント × n」の2層構成に拡張
2. 各LayerのモデルをCLAUDE_CODE_SUBAGENT_MODEL環境変数でLayer別に設定（Layer 1: claude-opus-4-8、Layer 2: claude-haiku-4-5で約60%コスト削減）
3. 3段階以上にネストする前に必ずトークン計算を行い、コスト上限を設定してから実装（`max_tokens: 5000` 等のガードを各エージェントに追加）

---

### P-066: Claude Code Safe Modeをデバッグ標準手順としてCLAUDE.mdに追加

**根拠記事**: 241 (Claude Code Safe Mode & フォールバックチェーン 実践ガイド)
**詳細**: 2026年6月追加の `--safe-mode`（または `CLAUDE_CODE_SAFE_MODE=1`）フラグはCLAUDE.md/プラグイン/スキル/フック/MCPを全無効化してクリーンな状態でデバッグするための公式トラブルシュートツール。bpr_labで多数のスキル・フック・MCP（P-011・P-013・P-023参照）が複雑に絡み合う構成になるにつれ、Safe Modeによる問題切り分けが必須になる。現在CLAUDE.mdにこの手順が未記録であり、問題発生時の対応が属人化している。

**提案アクション**:
1. CLAUDE.mdの「トラブルシュート」セクションに「Safe Mode起動: `claude --safe-mode` または `export CLAUDE_CODE_SAFE_MODE=1`。全カスタマイズ無効で素のClaudeで問題が再現するか確認する」を追記
2. フォールバックモデルチェーンの設定例（Fable 5 → Opus 4.8 → Sonnet 4.6）を `.claude/settings.json` の雛形としてリポジトリに追加
3. P-056（FX自動取引パイプラインへのフォールバック組み込み）と統合して設定ファイルを一元管理

---

### P-067: 米国AI規制環境の重大変化 — GAAIA + Colorado法差し替えでコンプライアンス戦略を再設計

**根拠記事**: 238 (Colorado AI Act廃止 Norton Rose), 239 (GAAIA DLA Piper), 240 (GAAIA vs 州法 FPF)
**詳細**: P-035・P-049・P-055のコンプライアンス前提が再び変化。確定事実: (1) Colorado SB 26-189成立（5/14署名、2027/1/1施行）で旧法のリスク管理・年次評価義務がなくなり「通知と透明性」のみに縮小、(2) 連邦地裁がxAI申請で旧Colorado法の執行を仮差し止め、(3) GAAIA草案（6/4）は3年プリエンプション条項含み成立すれば州法（SB26-189も）が凍結される可能性。実務的結論: 2027年1月まで余裕があり、連邦法の行方が不確実なため「HITL実装（P-025）の優先継続」と「法的動向の季報チェック」のみで対応。

**提案アクション**:
1. P-035・P-049の「Colorado対応優先」ステータスを「待機中：SB 26-189施行2027年1月、GAAIA成立見込み未確定」に更新
2. CLAUDE.mdに最新ステータスを反映：「AI規制適用状況（2026年6月時点）: Colorado SB 26-189は2027年1月施行予定、GAAIA成立すれば3年プリエンプション。直近はHITL（P-025）優先で対応」
3. 次回規制チェックポイントを2026年9月末（GAAIA草案への議会フィードバック期限後）に設定

---

### P-068: MCP OAuth 2.1必須化への移行計画 — 新規実装を今からRC仕様準拠に

**根拠記事**: 244 (MCP OAuth2エンタープライズ認証ロードマップ callsphere), 223 (MCP RC公式発表)
**詳細**: P-017・P-041・P-061で提案してきたMCPステートレス化への対応として、OAuth 2.1必須化の具体的なタイムラインが確定した。MCPサーバーはOAuth 2.1 Resource Serverとして公式分類され、APIキー認証はエンタープライズユースケースで非推奨になる。P-011（FXバックテストMCPサーバー）・P-013（MetaTrader MCPサーバー）の新規実装は今からOAuth 2.1で設計を開始することで、2026年7月28日の最終仕様公開後の改修コストをゼロにできる。

**提案アクション**:
1. P-011（FXバックテストMCPサーバー）の認証設計をOAuth 2.1 Resource Serverパターンで設計（シンプルな実装: Authorization Server = ローカルKeycloak or Auth0無料Tier）
2. P-013（MetaTrader MCPサーバー）はgitHub: ariadng/metatrader-mcp-serverのIssue/PRで2026-07-28仕様対応状況を確認し、対応済みなら採用・未対応なら自前でOAuth 2.1ラッパーを追加
3. CLAUDE.mdの「MCPサーバー開発ガイドライン」セクションに「認証: OAuth 2.1 Resource Serverパターン必須（APIキー認証は非推奨）」を追記（P-041の更新版）

---

## 2026-06-13 提案

### P-069: EU AI Act 8月2日完全施行への具体的対応チェックリスト作成

**根拠記事**: 274 (ChatGPT生成AI規制状況 2026年6月JA), 267 (P-067補完)
**詳細**: 2026年8月2日にEU AI Actが完全施行される（残り50日）。P-067でGAAIA/Colorado対応を「待機中」としたが、EU AI Actは8月2日に確定施行。bpr_labのFX自動取引ボットがEU居住者に向けたサービスの場合（またはEUデータを処理する場合）、ハイリスクAIシステム（信用スコアリング類似の金融意思決定）として登録義務が生じる可能性がある。日本市場のみを対象とする場合でも、AnthropicのAPIサーバーがEU内にある場合はデータ処理者として影響を受ける可能性がある。今月中の対応確認が必要。

**提案アクション**:
1. sandbox/FX自動取引/のターゲット市場（日本のみか、EU向けも含むか）を確認し、EU AI Actの適用可能性を法務的にチェック
2. 適用対象の場合：「自動化された意思決定システム」としてAnnex IIIリスト（信用・保険・雇用・法執行等）への該当有無を確認
3. CLAUDE.mdに「EU AI Act（2026年8月2日完全施行）: FX自動取引が日本市場のみ向けであれば直接適用外と解釈するが、EU処理データが含まれる場合は要確認」を注記
4. 次回確認タイミング: 2026年7月15日（施行2週間前）

---

### P-070: SIOS Tech Lab 無償SKILL.mdテンプレートを bpr_lab スキル整備の出発点に活用

**根拠記事**: 264 (Claude Code Skills 汎用テンプレート公開 SIOS Tech Lab JA)
**詳細**: SIOS Tech Labがコードレビュー・テスト生成・ドキュメント作成・リファクタリングの4種類のSKILL.mdテンプレートを無償公開した。P-039（bpr_lab スキル体系再整理）・P-060（SKILL.md description最適化）を具体化するための出発点として活用できる。特にコードレビュースキルは `/code-review` の代替として、FX自動取引コードの品質確認（P-031 ultrareviewの補完）に使える。テンプレートのdescriptionフィールドが自然言語で具体的に記述されており、P-060の「自動トリガー精度改善」の参考にもなる。

**提案アクション**:
1. SIOS Tech Lab公開のSKILL.mdテンプレート（4種）を `.claude/skills/` の雛形として取り込む（`git clone` またはコピー）
2. 各テンプレートのdescriptionを bpr_lab固有のユースケース（「FX自動取引コードのレビュー」「CLAUDE.md整備チェック」等）に書き換え、P-060のdescription最適化と同時に実施
3. 新規スキルの追加優先順位: `/fx-review`（P-037）→ `/catalog-update`（P-003）→ `/daily-collect`（P-003）の順でテンプレートから実装

---

### P-071: Fomoed AI取引プロンプト集のMT5接続テンプレートを sandbox/FX自動取引/ に適用

**根拠記事**: 271 (15 AI Trading Bot Prompts No Coding 2026 Fomoed), 272 (MT5+ChatGPT完全ガイド MQL5)
**詳細**: Fomoed の15プロンプト集はMT5・Interactive Brokers・Alpaca API用の接続コード例付きで、P-030（FastAPIアーキテクチャ適用）の実装加速に直接使用できる。MQL5 blogの4層アーキテクチャ実装記事（P-014と同等の信頼度閾値設計）と組み合わせると、sandbox/FX自動取引/のプロトタイプを即日構築できる。特に「バックテスト用プロンプト」と「MT5デモ口座接続コード」の部分はP-030のアクション3（MT5デモ口座でのPaperトレードモード確認）に対応する。

**提案アクション**:
1. Fomoed の「トレンドフォロー」「平均回帰」「リスク管理」プロンプトをsandbox/FX自動取引/prompts/ ディレクトリに保存（テンプレートとして管理）
2. P-014の信頼度閾値（0.55/0.75）を各プロンプトのリスク管理セクションに明示的に組み込む形にカスタマイズ
3. MQL5 blogの信頼度閾値実装（Claude API呼び出し時のconfidence field要求）をP-030のserver.py実装に取り込み、P-025（HITL）との統合を完成させる
4. MT5デモ口座環境が整っている場合は今週中にFomoed テンプレートのバックテスト用プロンプトを試験実行し、結果をP-026（乖離分析）のベースラインデータとして記録
---

## 2026-06-14 提案

### P-072: Fable 5 全世界停止に伴うモデル選択戦略の緊急見直し — P-054・P-064を一時中断

**根拠記事**: 275 (Anthropic公式声明 Fable 5/Mythos 5停止), 276 (The New Stack 停止命令), 277 (Trump政権対立), 278 (White House協議)
**緊急度**: 高（6/14時点でFable 5グローバル停止中）
**詳細**: 2026年6月12-14日、米政府指令によりClaude Fable 5（claude-fable-5-20260609）とMythos 5が全世界でアクセス不能になった。P-054（Fable 5モデル採用検討）・P-064（Fable 5本番採用）の実装計画を一時中断し、Opus 4.8（claude-opus-4-8）を最高性能モデルとして使用し続けるフォールバック体制に戻す必要がある。ホワイトハウス協議（来週予定）の結果次第で: (a)再開（条件付き）、(b)米国人ユーザー限定、(c)長期停止 の3シナリオがある。P-056（fallbackModel設定）のフォールバックチェーンから Fable 5 を一時除外し、最高性能レイヤーをOpus 4.8に戻す。

**提案アクション**:
1. sandbox/FX自動取引/config.py の `PREMIUM_MODEL` を `claude-opus-4-8` に戻す（Fable 5停止対応）
2. `.claude/settings.json` の `fallbackModel` 設定からFable 5を除外し `claude-opus-4-8` → `claude-sonnet-4-6` → `claude-haiku-4-5` に変更
3. CLAUDE.mdに「⚠️ Claude Fable 5は2026年6月12日〜米政府指令により停止中。次回確認: ホワイトハウス協議結果（6月第3週目安）」を追記
4. ホワイトハウス協議結果を受け、再開後にP-054・P-064の実装を再開するトリガーとして PROPOSALS.md に記録

---

### P-073: QuantaAlphaの進化的αファクターマイニングをFX自動取引の戦略開発に適用

**根拠記事**: 285 (QuantaAlpha arxiv:2602.07085 清華大・北大)
**詳細**: QuantaAlpha（清華大・北大・CAS・CMU・HKUST、2026年2月）はLLMエージェントによるαファクター自動マイニングを「軌跡（trajectory）レベルの進化的最適化」で大幅改善した論文。既存手法（RD-Agent・AlphaAgent）対比でIC +0.0535〜+0.0970、ARR +12〜18%の改善を実証。CSI 300で学習した因子がS&P 500へ転用可能（累積超過リターン137%）。P-004（TradingAgentsアーキテクチャ）とP-033（TradingAgents + Claude 4.x）の「シグナル生成」レイヤーに、QuantaAlphaの進化的最適化アプローチを組み込むことでシステマティックなαファクター探索が可能になる。GitHub公開済みで実装コードが入手可能。

**提案アクション**:
1. QuantaAlphaのGitHub（github.com/QuantaAlpha/QuantaAlpha）をクローンし、EUR/USDのFXデータでの動作確認を試験実施
2. P-014（信頼度閾値）のconfidence値を、QuantaAlphaが出力するIC（情報係数）とARR（年間リターン率）から動的に計算するアダプターを設計
3. P-043（LLMバージョン固定・再現性確保）の原則をQuantaAlpha実行時にも適用: 使用モデル・日付・データソースを記録してタスクの再現性を保証
4. CSI 300→S&P 500のファクター転用実績を参考に、FXペア間（EUR/USD→USD/JPY）のファクター転用可能性を検証

---

### P-074: Colorado AI Act 6月30日施行 (残16日) — P-067の待機方針から最終確認へ

**根拠記事**: 281 (AIガバナンス主導権争い Vorys分析), 277 (Trump政権AIモデル規制)
**詳細**: P-067で「Colorado SB 26-189は2027年1月施行で余裕あり」と判断したが、Vorys法律事務所の最新分析（2026年6月14日）でColorado旧法（SB24-205）の6月30日施行に向けた最終確認が必要と指摘されている。旧法と新法（SB 26-189）の移行スケジュールの解釈が複雑なため、bpr_labのFX自動取引ボットが「自動化された意思決定ツール（ADMT）」として旧法の適用対象になる期間（6月30日〜12月31日）がある可能性がある。White House vs 州法の対立（Fable 5停止事例含む）により、連邦AI規制の影響範囲が拡大する傾向を踏まえ、早めの確認を推奨。

**提案アクション**:
1. Colorado旧法（SB24-205）の6月30日施行と新法（SB 26-189）の2027年1月施行の重複期間（7月〜12月）でのADMT義務を法務確認（P-035のアクション1を6月30日前に完了）
2. Vorys分析のWhite House プリエンプションシナリオ（6/2大統領令）がColorado法を事実上無効化している場合は対応不要と判断できる旨をCLAUDE.mdに注記
3. 次回確認タイミング: 2026年7月1日（Colorado法施行翌日）に確認し、GAAIA動向と合わせて評価（P-049との統合）

---

## 2026-06-16 提案

### P-075: P-006/P-012 緊急対応を「待機」に格下げ — Agent SDK課金変更が一時停止中

**根拠記事**: 289 (Anthropic Pauses Agent SDK Credit Split - Digital Applied), 288 (Claude Code Pricing June 2026 - Bind AI)
**詳細**: P-006（緊急度高）およびP-012で対応を促していた2026年6月15日のAgent SDK課金分離変更が、AnthropicによりLast Minuteで一時停止された。現時点では非インタラクティブ実行のクレジット分離は**未施行**。施行時期は未定。sandbox/FX自動取引/のコスト試算や、日次収集エージェントのコスト見直しは再開通知まで待機。ただしP-012のモデルIDリタイア（claude-sonnet-4-20250514等）はAgent SDK課金と無関係のため引き続き対応必要。

**提案アクション**:
1. P-006・P-007（Agent SDK課金変更関連）の緊急フラグを一時解除し、Anthropicの再施行アナウンスを待つ
2. P-012のモデルIDリタイア確認（`grep -r "sonnet-4-20250514\|opus-4-20250514" .`）は引き続き実施
3. Anthropicの公式ブログ・Releasebot（releasebot.io/updates/anthropic）を週次チェックし、再施行アナウンスに備える
4. 再施行時には最新の料金表（288 Bind AI記事）を基に月次コスト試算を即時更新

---

### P-076: v2.1.178 新パーミッション構文を settings.json に適用

**根拠記事**: 286 (Claude Code v2.1.178 DevelopersIO JA)
**詳細**: 2026年6月16日公開のv2.1.178でパーミッションルールの新構文が導入された。ネストした `.claude` ディレクトリのサポートも強化されており、プロジェクト配下のサブディレクトリ（sandbox/FX自動取引/等）に独立した `.claude/settings.json` を配置してスコープ別に権限を細分化できる。`enforceAvailableModels` によるモデルアローリスト管理も利用可能に。FX自動取引ディレクトリのように実資金に触れるコードは、専用の `.claude/settings.json` で権限を絞ることが推奨される。

**提案アクション**:
1. `sandbox/FX自動取引/.claude/settings.json` を新規作成し、FX取引専用の権限セット（読み取り・MT5 API呼び出し限定・本番APIへの直接書き込み禁止）を新構文で記述
2. `enforceAvailableModels` を設定し、FX取引サブエージェントが利用可能なモデルをOpus 4.8・Sonnet 4.6のみに制限
3. ネストした `.claude` サポートを利用して、bpr_lab全体の `.claude/settings.json`（グローバル）とFX固有の設定を階層管理

---

### P-077: LLM金融戦略の長期アウトパフォーム困難の実証 — FX自動取引の設計原則見直し

**根拠記事**: 290 (arxiv 2505.07078 LLM Financial Strategies Cannot Outperform Market Long Run)
**詳細**: 2505.07078論文が20年間・100銘柄超で実証した「LLMアルファの長期劣化」と「ブル相場過保守・ベア相場過攻撃」の非対称性は、bpr_labのFX自動取引設計における重要な制約。P-020（TrustTrade式コンセンサス）・P-033（TradingAgents + Claude 4.x）を推進する際、「LLMをメインシグナルにする設計」の限界を認識した上で実装すべき。P-026（3ヶ月実験の教訓）で既に「補助役割として使うべき」と結論付けていたが、本論文がその学術的根拠を提供した。特にFXはバックテスト→実取引ギャップがさらに大きいため（高頻度・スリッページ・スワップ）、LLMはシグナル「候補生成」に留め最終執行はルールベースに委ねる原則を強化すべき。

**提案アクション**:
1. sandbox/FX自動取引/architecture.md に「LLM役割: 非構造化データ解析・シグナル候補生成のみ。最終エントリー判断・リスク管理はルールベース」と明記
2. P-014（信頼度閾値）のconfidence閾値を「LLMシグナルの直接採用閾値」ではなく「ルールベースフィルタへの入力スコア」に再定義
3. バックテスト評価指標に「ブル相場パフォーマンス」「ベア相場パフォーマンス」を必ず分離追加し、非対称リスクを可視化

---

### P-078: AY Automate 15フックサンプルからコスト監視フックを即採用

**根拠記事**: 297 (15 Best Claude Code Hooks Copy-Paste Ready 2026 - AY Automate)
**詳細**: AY Automateが公開した15種のCopy-Paste対応フックサンプルのうち、bpr_labの日次収集エージェントに即採用できるものが複数ある。特に「コスト監視フック（Stop時の累積トークン・コスト集計）」は、P-075（Agent SDK課金変更の再施行モニタリング）と組み合わせて実際のコストを可視化する手段として有効。「セッション終了時のgit commit自動化フック」はStep 5（コミット&Push）の手動作業を削減できる。P-038（自己学習型フック）と組み合わせることで、コスト監視＋知識蓄積の自動パイプラインを構築できる。

**提案アクション**:
1. AY Automateのコスト監視フック（Stop/SubagentStop フックで累積トークン・概算コストをJSONログに出力）を `.claude/settings.json` に追加
2. セッション終了時のgit commit自動化フック（Stopフック: 変更があれば `git add -A && git commit -m "auto: セッション自動コミット"` を実行）を試験導入
3. 上記2フックを1週間運用し、日次収集エージェントの実際のトークン消費量・コストを記録してP-075の再施行時コスト試算の実データとして活用

---

## 2026-06-17 提案

### P-079: SKILL.md frontmatterへのHooks直書き技法を bpr_lab スキルに導入

**根拠記事**: 309 (Qiita Tips: HooksをSKILL.mdに直書き)
**詳細**: SKILL.mdのfrontmatter（`---`ブロック）にhooksキーを追加するだけで、settings.jsonと等価のHooks設定が機能することが確認された。bpr_labの.claude/skills/配下の各スキルが独自のPostToolUse/PreToolUse hookを必要とする場合（例：日次収集スキルが終了後に自動コミットするhook）、settings.json一元管理から「スキルとフックのひとつのファイル管理」に移行することで保守性が大幅に向上する。P-038（自己学習型フック）・P-078（コスト監視フック）の実装もSKILL.md内に統合できる。

**提案アクション**:
1. `.claude/skills/`配下の各SKILL.mdのfrontmatterに対応するhooks定義を移植し、settings.jsonのhooksセクションをスリム化
2. `.claude/skills/daily-collect/SKILL.md`（P-003）に「Stop後に git add・commit・push を実行するhook」を frontmatterで直書きし、Step 5の手動コミット作業を自動化
3. チームリポジトリに共有する場合は.claude/skills/ディレクトリをGitに含めることで、hooks定義も同時に共有可能になる利点をCLAUDE.mdに記録

---

### P-080: FX自動取引ボットの「7コンポーネント完成度監査」を実施

**根拠記事**: 314 (MQL5ブログ: AIトレーディングの7コンポーネント), 312 (LLM比較: Pythonアルゴ取引ボット生成)
**詳細**: MQL5コミュニティの実証記事が「完全なAI取引システムには7コンポーネントが必要」と定義した（①LLMモデル選択、②システムプロンプト設計、③コンテキストフォーマット、④呼び出し頻度最適化、⑤リスク管理レイヤー、⑥バックテスト統合、⑦モニタリング・ロギング）。現在のsandbox/FX自動取引/がこの7コンポーネントのうちどこまで実装済みかを棚卸しすることで、優先実装項目が明確になる。また、LLM比較実験（記事312）でClaude Opus 4.7が「確認ロジックが堅牢で保守的」と評価されており、リスク管理重視のFXボットに適したモデルであることが改めて確認された。

**提案アクション**:
1. `sandbox/FX自動取引/architecture.md` に7コンポーネントのチェックリストを作成し、各コンポーネントの実装状態（未着手/進行中/完了）を記録
2. 最優先未実装コンポーネントを特定し、次のスプリントのタスクとして登録（特に⑤リスク管理レイヤーの「LLMの外側への配置」が最重要）
3. P-014（信頼度閾値）・P-025（HITL設計）・P-043（LLMバージョン固定）を7コンポーネントフレームワークに対応付けて、既存提案の優先順位を整理

---

### P-081: EU AI法 HRAI期限延期（2026/8→2027/12）による規制対応優先度の見直し

**根拠記事**: 316 (EU AI法 Digital Omnibus改正: HRAI期限延期)
**詳細**: 2026年5月7日の暫定合意でAnnex III高リスクAI（HRAI）義務が1.5年延期（2026年8月→2027年12月）された。P-049（Colorado法監視）・P-055（GAAIA草案対応）・P-035（FX自動取引のADMT適用確認）との関係を再整理する必要がある。EU法上の義務延期は日本・米国の規制に直接影響しないが、グローバルAIガバナンスの趨勢として「高リスクAI義務の段階的施行」が主流になっており、P-025（HITL設計）・P-077（LLM役割限定）の方向性が国際的なスタンダードと整合していることを確認できた。なお、汎用AI（GPAI）モデル義務（Anthropic等の開発者に課される義務）は8月2日施行のまま変更なし。

**提案アクション**:
1. `sandbox/FX自動取引/README.md` の規制対応注記を更新：「EU AI法 Annex III HRAI義務は2027年12月まで延期。GPAIモデル義務（Anthropic側）は2026年8月施行。本システムは利用者として直接対象外だが、利用するAPIプロバイダーの規制準拠状況を定期確認」
2. P-025（HITL設計）・P-077（LLM役割限定）を「EU AI法・Colorado法・日本AIガイドラインに共通する推奨設計原則」として位置付け直し、単一の法律対応ではなく普遍的なベストプラクティスとして実装
3. 次回規制監視タイミングを「2026年8月1日（EU GPAI義務施行直前）」と「2026年7月末（EU Digital Omnibus正式採択後）」の2点に設定

---

## 2026-06-18 提案

### P-082: Fable 5/Mythos 5シャットダウン（90分通知）を踏まえたAI依存リスク管理戦略の策定

**根拠記事**: 325 (Claude Updates May–June 2026: Opus 4.8, SpaceX, Managed Agents), X#SIGNAL claude-ecosystem (@HaraKazuo, @c64f7e94, @AISTATSCH 他)
**詳細**: 2026年6月、米国政府の指示によりAnthropicがFable 5（Mythos 5）の国外アクセスを90分前通知で停止した事例が発生。bpr_labはClaude APIに全面依存しているため、モデル突然失効・国外制限・ITAR/EAR輸出規制による停止リスクが現実的脅威として顕在化した。DoD（米国防省）もAnthropicから契約の2/3以上をOpenAI・Google・Metaに移行したとされ、政府との関係が企業の安定性リスクに直結する。個人・スタートアップ規模でも「主力モデルへのシングルポイント依存」は業務継続リスクである。

**提案アクション**:
1. `CLAUDE.md`（またはプロジェクトルート）に「AIモデル依存リスク管理ノート」を追加：現在使用中のモデルID、代替モデル（OpenAI GPT-5.5、Google Gemini 3.x）へのフォールバック手順、APIキー切り替え方法を文書化
2. 日次収集エージェント（bpr_lab）が使用するモデルを設定ファイル（`.env`または`CLAUDE.md`）で管理し、モデルIDをハードコードしない設計に移行
3. 月1回「モデルアクセス状況確認」タスクをスケジュール：使用中Anthropicモデルの提供状況・輸出規制対象指定有無を確認

---

### P-083: NVIDIA SkillSpector（64脆弱性クラス検査）でbpr_labのClaudeスキルをセキュリティ監査

**根拠記事**: X#SIGNAL claude-code (@VivekIntel: NVIDIA SkillSpector announcement)
**詳細**: NVIDIAがSkillSpectorというClaude Code Skills向けセキュリティスキャンツールをリリース。64種の脆弱性クラスを検出し、コード生成・実行時のインジェクション・権限昇格・機密情報漏洩リスクを特定する。bpr_labの`.claude/skills/`配下には日次収集・Python実行・ファイル書き込みを行うスキルが存在し、外部入力（Webサーチ結果、Xポスト）を処理するため、プロンプトインジェクション対策の確認が重要。

**提案アクション**:
1. SkillSpector（NVIDIAのGitHubまたはClaudeマーケットプレイスで公開予定）のインストール手順を確認し、`.claude/skills/`配下の全SKILLに対して実行
2. 検出された脆弱性のうち「高リスク」分類を優先修正（特に外部入力のサニタイズ不足、過剰な権限付与）
3. 月次セキュリティ監査タスクとしてSkillSpector実行をbpr_labの運用ルーティンに追加

---

### P-084: ZenomTrader方式のClaude×MT5自律バックテスト統合をFXプロジェクトに実装

**根拠記事**: X#SIGNAL ai-trading (@ZenomTrader: Claude autonomous MT5 backtesting tool)
**詳細**: ZenomTraderが「Claudeがデータ分析→戦略立案→MT5内でのバックテスト実行→結果評価→戦略修正」の全サイクルを自律的に完結させるツールを公開（Claude Code + MT5 Terminal MCP連携）。現在のsandbox/FX自動取引/ではバックテストは手動実行だが、このアーキテクチャを採用すれば「バックテストのループ高速化」と「P-080（7コンポーネント）の⑥バックテスト統合」が同時に達成できる。MT5 MCPサーバー（MetaTrader-MCP, 記事057）がすでにライブラリに存在しており、技術的な土台はある。

**提案アクション**:
1. ZenomTraderのツール（GitHubリポジトリ）を確認し、MT5 MCP連携のアーキテクチャをsandbox/FX自動取引/design.mdに転記・分析
2. 最小実装として「Claudeに戦略パラメータを渡す→MT5でバックテスト実行→結果をJSON返却→Claudeが評価」の1サイクルをPython/MCPで実装
3. P-080（7コンポーネント）の⑥バックテスト統合と組み合わせ、ZenomTrader方式を採用した場合のアーキテクチャ図を作成

---

### P-085: CoinbaseのSEC登録AI投資顧問（業界初）を踏まえたAI売買エージェントの法的要件調査

**根拠記事**: X#SIGNAL ai-trading (@Tawney_jjones, @CryptoJPTrans: Coinbase AI investment advisor SEC registration), ai-news (@IROHANI_shotime)
**詳細**: CoinbaseがAIエージェントをSEC（米証券取引委員会）に投資顧問として登録（業界初）。自律的に資産運用できる法的根拠を持つAIエージェントが登場したことで、AI自動取引エージェントの規制フレームワークが現実化した。日本ではFX自動売買は登録業者が提供するEA（Expert Advisor）として扱われるため、個人が「AIが自律的に売買判断するシステム」を開発・運用する場合の法的地位を改めて確認する必要がある。P-025（HITL設計）・P-077（LLM役割限定）の「最終判断は人間が行う」設計原則の法的根拠としてこの事例を活用できる。

**提案アクション**:
1. 日本の金融商品取引法における「自動取引システムの個人運用」の現行規制（2026年版）を調査し、sandbox/FX自動取引/legal-notes.mdに要点をまとめる
2. P-025（HITL設計）の設計根拠に「SEC登録AI投資顧問事例により自律型AIの法的承認が進展中だが、日本ではHITL原則が安全側」を追記
3. Coinbaseの事例を「AI自動取引の国際規制動向ウォッチ」として月次収集テーマに追加

---

### P-086: Anthropic 400kセッション研究の主要知見をbpr_lab日次収集エージェント設計に反映

**根拠記事**: X#SIGNAL claude-code (@6i8PTmb4OY50019, @tenobrus, @Kylechasse: Anthropic 400k session study findings)
**詳細**: Anthropicが40万件のClaude Codeセッションを分析した研究で、主要知見が明らかになった：①平均セッションは4ターンで完了（長期セッションは効率低下の傾向）、②ドメイン専門知識を持つユーザーは専門知識なしの5倍の成果を上げる、③専門性が高いほどAIとの協働品質が向上する。bpr_labの日次収集エージェントは長大なセッションになりがちで、コンテキスト圧縮・要約が頻発している。4ターン完了の原則に近づけるためにセッション構造を見直す価値がある。

**提案アクション**:
1. 日次収集エージェントの現在のターン数を記録（次回ルーティン実行時にカウント）し、平均値が研究知見（4ターン）の何倍かを測定
2. 収集/分類/カタログ更新/コミットの4フェーズを「各フェーズ独立セッション」として分割実行する設計案を検討（現在は1セッションで全フェーズを実行）
3. 「ドメイン専門性が成果を5倍にする」知見を踏まえ、日次収集のクエリ設計を更にドメイン特化させるためのクエリリスト改訂（特にai-trading分野のMT4/MT5固有クエリ強化）

---

## 2026-06-19 提案

### P-087: MCPセキュリティ監査の即時実施 — 200,000台RCE脆弱性（14 CVE）対応

**根拠記事**: 563 (Anthropic MCP Vulnerability 200K Servers RCE), 567 (Claude Code × MCP実践活用ガイド・セキュリティチェックリスト)
**詳細**: 2026年4月に発見されたMCP脆弱性（OX Security報告）では、約200,000台のMCPサーバーがRCE攻撃に晒されており14件のCVEが付与された。Anthropicはパッチをリリース済みだが、bpr_labが使用する第三者製MCPサーバー（ariadng/metatrader-mcp-server等）が最新パッチを適用済みかは個別確認が必要。P-041（MCP stateless設計）・P-017（MCP仕様RC対応）の実装においても、この脆弱性クラスを念頭に置いたセキュリティ設計が必要。article 567のセキュリティチェックリスト（ソースコード公開有無・メンテナー評判・権限スコープ最小化）が即時適用可能な評価基準として活用できる。

**提案アクション**:
1. bpr_labで使用中のMCPサーバー一覧を確認し、各サーバーの最終更新日・CVE対応状況をチェック
2. article 567のセキュリティチェックリストを`.claude/mcp-security.md`として保存し、新規MCPサーバー追加時の評価プロセスに組み込む
3. 第三者MCPサーバーには最小権限スコープ（読み取り専用ツールのみ許可等）を設定し、`.claude/settings.json`で権限を明示制限
4. P-083（SkillSpector監査）と連携し、MCPツール経由の外部入力処理にプロンプトインジェクション対策を追加

---

### P-088: MT5-LLM統合の「キューベースアーキテクチャ」をFX自動取引に実装

**根拠記事**: 568 (MetaTrader MCP Server AI LLM Trading Automation - Agentpedia)
**詳細**: article 568が明示した「MT5のOnTick()に直接LLM呼び出しを埋め込む設計は本番スループットで破綻する」という具体的な失敗パターンと解決策が判明した。推奨アーキテクチャ: MT5 → Python非同期キュー → LLM推論 → 実行ゲートウェイの4層構成。P-013（MetaTrader MCPサーバー採用）・P-030（Quant AI Agents MT5 FastAPIアーキテクチャ）の実装方針と整合しており、特にキューイング層の追加が現在のsandbox/FX自動取引/設計における欠落コンポーネントとして特定できた。MCP経由で公開されるツール定義（open_trade・close_trade・get_ohlc・get_account_info）の標準化も行うべき。

**提案アクション**:
1. `sandbox/FX自動取引/` に `queue_bridge.py` を追加: MT5のOnTick()イベントをasyncioキューに積み、LLM推論は別スレッドで非同期処理する実装
2. MCPツール定義を `sandbox/FX自動取引/mcp_tools.py` に標準化（open_trade・close_trade・get_ohlc・get_account_info の4ツール最小セット）
3. P-030（FastAPI実装）と統合: FastAPI → asyncio キュー → MT5ブリッジ の完全パイプラインを実装し、デモ口座でスループットテスト（1秒あたりLLM呼び出し数の上限を計測）
4. P-025（HITL設計）のconfidence閾値チェックをキュー処理の中間ステップとして組み込む

---

## 2026-06-20 提案

### P-089: Claude Code Artifacts を FX自動取引ダッシュボードとして活用

**根拠記事**: 572 (Claude Code Artifacts 公式ブログ), 573 (VentureBeat Artifacts エンタープライズ)
**詳細**: 2026年6月18日にリリースされた Claude Code Artifacts（Team/Enterprise 限定ベータ）を使えば、FX自動取引のバックテスト結果・パフォーマンスダッシュボード・戦略比較レポートを、Claude Code セッションから直接ライブ更新のHTMLページとして生成・共有できる。現在の sandbox/FX自動取引/ では月次パフォーマンスレポートを手動で作成しているが、Artifacts を活用すればセッション中に自動生成されたビジュアルダッシュボードとして共有可能になる。Team/Enterprise プラン限定であることに注意。

**提案アクション**:
1. Claude Code の Artifacts 機能（`/artifacts`コマンド or セッション内で自動検出）を有効化し、FXバックテスト結果を HTML ダッシュボードとして出力するワークフローを試作
2. P-037（月次パフォーマンスレビュースキル）と連携: `/fx-review` スキル実行時に Artifacts として損益チャート・Sharpe比・ドローダウン推移を自動生成
3. Enterprise プラン未契約の場合は代替として `/ultrareview` との組み合わせによるテキスト形式のパフォーマンスレポートで暫定対応

---

### P-090: Claude Fable 5 への API モデル切り替え — Opus 4.8 比で安価・高性能

**根拠記事**: 577 (Anthropic公式 Fable 5 仕様), 579 (Simon Willison 分析), 586 (Mean CEO 価格比較)
**詳細**: Claude Fable 5（2026年6月9日 GA）は Anthropic 史上最強モデルでありながら Opus 4.8 より安価（入力$10/M vs $15/M、出力$50/M vs $75/M）。Simon Willison・Mean CEO ともに「価格逆転現象」として注目しており、特にコーディング・推論・複雑タスクで Opus 4.8 を上回る。1M トークンコンテキスト・128k 出力対応、self-verification behaviors を実装。FX 自動取引の判断層（P-014 の 0.75+ フルサイズエントリー条件）で Fable 5 に切り替えることで、性能向上とコスト削減を同時に達成できる。API モデル ID: `claude-fable-5`。

**提案アクション**:
1. `sandbox/FX自動取引/config.py` の `MODEL=claude-opus-4-8` を `MODEL=claude-fable-5` に変更し、同一バックテストで精度・レイテンシ・コストを計測
2. P-043（LLMバージョン固定とリグレッションテスト）の対象をFable 5に更新し、Opus 4.8→Fable 5の移行前後でシャープレシオ・勝率の変化を記録
3. CLAUDE.md のモデル指定注記を更新: 「FX判断層は `claude-fable-5`（Opus 4.8 比で高性能・低コスト）を使用」を明記
4. Mythos 5（サイバー能力完全版）は一般開発用途では不要のため Fable 5 を使用すること

---

### P-091: EU AI Act 2026年8月2日施行への対応確認

**根拠記事**: 583 (Axis Intelligence EU AI Act 8月施行), 584 (Latham & Watkins EU AI Act 変更)
**詳細**: EU AI Act の主要規定が 2026年8月2日に発効（あと約43日）。透明性義務（Article 50）：AI 対話の開示・合成コンテンツのラベリング・ディープフェイク識別が義務化。高リスクAIシステムへの要件も同日発効。Latham & Watkins 分析によれば SME 向けの一部簡素化はあるが 8月2日の期限は変更なし。bpr_lab の FX 自動取引エージェント・日次収集エージェントが EU ユーザーに接触する場合、透明性義務の適用を確認する必要がある。個人利用・日本国内限定であれば直接影響は低いが、Claude API 経由で Anthropic の EU AI Act コンプライアンスに間接的に依存する構造を理解しておくべき。

**提案アクション**:
1. bpr_lab のシステム（FX 自動取引・日次収集エージェント・Artifacts 共有）が EU ユーザーへのサービスに該当するか用途確認を実施
2. EU 向けサービスが含まれる場合: Article 50 の透明性義務（AI 対話である旨の表示）を 8月2日までに実装
3. CLAUDE.md に「EU AI Act 2026年8月2日施行: AI 対話透明性義務の対応状況」を記録し、毎月の規制動向確認を PROPOSALS.md レビューと合わせて実施

---

### P-092: AGENTS.md の採用検討 — マルチエージェント環境での設定統一

**根拠記事**: 576 (Izanami CLAUDE.md vs AGENTS.md ベストプラクティス)
**詳細**: Izanami 記事により、AGENTS.md フォーマット（OpenAI Codex・Gemini CLI・Claude Code 等の複数エージェント共通）が2026年時点で普及しつつあることが確認された。bpr_lab では Claude Code 専用の CLAUDE.md を使用しているが、P-036（Microsoft Agent 365 SDK）・P-029（TradingAgents）等の複数エージェントフレームワークを導入した場合、CLAUDE.md と AGENTS.md の二重管理が発生する可能性がある。現時点では Claude Code 単一エージェントが主体のため CLAUDE.md で十分だが、マルチエージェント化が進む場合に備えて移行計画を検討すべき。

**提案アクション**:
1. bpr_lab が使用するエージェントツールを棚卸し（Claude Code・TradingAgents・Microsoft Agent SDK 等）し、AGENTS.md 対応ツールを特定
2. 複数エージェントが 2 種類以上になった時点で CLAUDE.md → AGENTS.md への移行を実施（現時点では移行不要）
3. CLAUDE.md の先頭に「この設定は Claude Code 専用。AGENTS.md 対応ツールを導入する場合は PROPOSALS.md P-092 を参照」というコメントを追記し、将来の移行ガイダンスを残す

---

## 2026-06-21 提案

### P-093: FX自動取引への参照設計追加 — Robinhood Agentic TradingのMCPアーキテクチャと安全機能

**根拠記事**: 587 (Robinhood Agentic Trading 正式ローンチ)
**詳細**: Robinhoodが2026年5月27日にMCP経由のAIエージェント自律取引を正式ローンチ。メインストリームプラットフォームが採用した安全設計が bpr_lab のFX自動取引設計（P-013・P-025）の参照モデルとして活用できる。Robinhood設計の3原則：①専用隔離口座（メイン資産と分離）、②ワンタップキルスイッチ（即時切断）、③不正検知AI（エージェント指示と実行の照合）。これらはP-025（HITL設計）・P-034（フォールバック設計）と整合しており、日本の個人向けFX自動取引においても同様の安全設計が規制対応・リスク管理の両面で有効。MCP経由の接続設計（P-013）はRobinhoodと同一アーキテクチャであり、実績ある実装パターンとして確証が得られた。

**提案アクション**:
1. `sandbox/FX自動取引/architecture.md` に「Robinhood Agentic Trading参照設計」セクションを追加し、3安全原則（隔離口座・キルスイッチ・指示照合）をFX版設計に対応させる
2. P-025（HITL設計）のconfidence 0.55-0.75帯での人間確認を「キルスイッチ相当」として位置づけ、FX取引でも「ワンコマンドで全エージェント取引を停止」する `/fx-kill` コマンドをスキル化
3. P-030（FastAPI 4層アーキテクチャ）の実行ゲートウェイ層に、エージェントが要求した取引内容と実際の送信注文を照合するバリデーション関数を追加（Robinhoodの不正検知AIの個人向け代替）

---

### P-094: フレームワーク選択更新 — LangGraph vs CrewAI 2026本番データを反映（P-004・P-033修正）

**根拠記事**: 589 (Redwerk LangGraph vs CrewAI 本番比較 2026)
**詳細**: 2026年本番実績データで従来の選択指針（P-004・P-033）を更新する必要がある。定量比較：LangGraphが月間PyPIダウンロード3450万（CrewAI 520万・約6.6倍差）で本番採用でリード。CrewAIはMCP・A2Aをネイティブサポート、LangGraphはコミュニティ統合のみ。最も重要な知見は"prototype-then-migrate"パターン：CrewAIでPoC→LangGraphへ移行が最多。bpr_lab は P-004 でTradingAgentsを採用予定だが、TradingAgentsはLangGraphベースであり、本データはLangGraphの本番信頼性を裏付ける。一方FX取引でのMCP接続（P-013）はCrewAIのネイティブ対応が有利であり、用途による使い分けが推奨される。

**提案アクション**:
1. P-004（TradingAgentsアーキテクチャ）のLangGraphバックエンド選択を「本番実績データで正当化」として更新
2. P-013（MetaTrader MCPサーバー）のエージェントオーケストレーション層にCrewAIを採用するオプションを追加（MCP/A2Aネイティブ対応のため）
3. `sandbox/FX自動取引/architecture.md` に「フレームワーク選択根拠：シグナル生成エージェント=LangGraph/TradingAgents（本番実績）、MCPツール統合=CrewAI（ネイティブ対応）のハイブリッド設計」を記録

---

### P-095: Enterprise MCP 3フェーズロードマップをFX自動取引のMCP統合計画に適用

**根拠記事**: 594 (CData Enterprise MCP活用事例 3フェーズロードマップ 2026)
**詳細**: CDataのエンタープライズMCP 3フェーズ展開（Phase1: 単一部門PoC→Phase2: 部門間連携→Phase3: 全社AIネイティブ基盤）は、個人開発規模に縮小してFX自動取引のMCP統合計画にそのまま適用できる。Phase1（MT5 1通貨ペアのデータ取得MCP化）→Phase2（MT5 + ニュースフィード + センチメント分析の複数MCPサーバー連携）→Phase3（FX自動取引全体のAIネイティブ基盤化）の3段階で段階的に実装することで、P-013・P-030・P-041の各提案を順序立てて実行できる。CDataの具体的事例（Hacobuの静的解析MCP化）は「既存Pythonツールのシンプルなラッパー」から始めることの有効性を示す。

**提案アクション**:
1. P-041（MCP stateless設計）・P-013（MetaTrader MCPサーバー）をPhase1として優先実装：まずMT5 OHLC取得ツール1本をFastMCPでMCP化し、Claude Desktopから取引データを自然言語で参照できる状態を作る（CData事例と同様の「最小MCPから開始」）
2. Phase2としてP-030（FastAPI）・P-011（FXバックテストMCP）を統合し、取引シグナル生成+バックテスト検証+MT5実行の3 MCPサーバーが協調するアーキテクチャを構築
3. Phase3（3フェーズ完了時）の目標状態を `sandbox/FX自動取引/architecture.md` に明記：「Claude Code/Agent SDK から単一の自然言語指示で、MT5のシグナル生成・バックテスト検証・リスク評価・注文送信・パフォーマンスレポートを一気通貫で実行できる」

---

## 2026-06-22 提案

### P-096: MCP Tunnelを使いFX自動取引VPS上のMT5へ安全接続（パブリックエンドポイント不要）

**根拠記事**: 595 (Claude Managed Agents Self-Hosted Sandboxes + MCP Tunnels), 605 (InfoQ MCP Tunnels技術詳細)
**詳細**: Anthropicが2026年5月19日に発表したMCPトンネル（リサーチプレビュー）は、プライベートネットワーク内のMCPサーバーへパブリックインターネット露出なしに接続できる。VPS上のMT5インスタンスにMCPサーバー（P-013: ariadng/metatrader-mcp-server）を立てた場合、これまではVPNまたはポート公開が必要だったが、MCPトンネルを使えばVPS側に軽量ゲートウェイをインストールするだけで済む。インバウンドFW変更不要・E2E暗号化。P-041（MCP stateless設計）と組み合わせることで、VPS側のMT5-MCPサーバーをAWSPrivateLinkなしで安全接続できるシンプルなアーキテクチャが実現する。

**提案アクション**:
1. MCPトンネルのリサーチプレビューアクセスをリクエスト（platform.claude.com経由）
2. VPS上の `ariadng/metatrader-mcp-server` のMCPサーバー設定にMCPトンネルゲートウェイを追加（公開ドキュメント確認後）
3. P-013のアクション3（「VPS上のMT5インスタンスへのMCPアクセス経路を評価」）をMCPトンネルGA後に即時実行に格上げ
4. VPS側のFWはアウトバウンド443のみ許可でセキュリティ維持

---

### P-097: TradingAgents v0.2.5 へのアップグレード — センチメント捏造問題の修正適用

**根拠記事**: 597 (TradingAgents v0.2.5 Grounded Sentiment Analyst + 80k Stars)
**詳細**: TradingAgents v0.2.5（2026年5月リリース、GitHub 80k+ stars）でSentiment Analystが根本修正された。従前（v0.2.4以前）はLLMがプロンプト圧力下でYahoo News/StockTwits/Redditの投稿を捏造する「グラウンドなし幻覚」問題があった。v0.2.5から実データ取得後に分析する設計に変更。P-004・P-029・P-033・P-040でTradingAgentsを試験実装する際、v0.2.4以下は使用すべきでない。また、v0.2.5でリモートOllama接続が追加されたため、P-034（ローカルLLMフォールバック設計）でのOllamaバックエンド構成がより容易になった。

**提案アクション**:
1. `pip install --upgrade tradingagents` で v0.2.5 に更新（P-029・P-033・P-040の環境でも同様に実施）
2. v0.2.5の `TRADINGAGENTS_*` 環境変数対応を活用し、APIキーを `config.py` ハードコードからenv-varへ移行
3. P-034（Ollamaローカルフォールバック）の実装時、v0.2.5のリモートOllama設定（`--ollama-url`）を使い、ローカルPC/VPS上のOllamaをTradingAgentsバックエンドとして設定する手順をまとめる
4. EUR/USDで v0.2.4 と v0.2.5 の同一期間バックテストを実施し、Sentiment Analystの改修によるパフォーマンス変化を計測してP-043のリグレッション記録に追加

---

### P-098: Anthropic Workload Identity Federation (WIF) でAPIキーハードコードを排除

**根拠記事**: 596 (Anthropic WIF GA + ant CLI)
**詳細**: AnthropicがWIF（Workload Identity Federation）をGA。静的APIキーを短命なスコープ付き認証情報に置き換える。bpr_lab の日次収集エージェント・FX自動取引スクリプトは現在 `ANTHROPIC_API_KEY` 環境変数を使用しているが、長期間有効な静的キーはリポジトリへの誤コミット・VPS侵害時の漏洩リスクがある。GitHub Actions実行（P-008: Routines）に対してはGitHub OIDC→Anthropic WIFの連携が可能。また `ant CLI` でプロファイル切り替え（personal/bpr_lab等の複数ワークスペース管理）が容易になった。

**提案アクション**:
1. `pip install anthropic --upgrade` でWIF対応バージョンを確認し、認証設定を静的キーからWIFへ移行手順を調査
2. GitHub Actions（P-008: Routines自動スケジュール）でGitHub OIDC→Anthropic WIF認証に切り替え、APIキーのGitHub Secrets依存を排除
3. `ant auth login` でブラウザOAuthフロー認証を設定し、ローカル開発環境でのAPIキー環境変数手動設定を不要化
4. sandbox/FX自動取引/ の設定ファイルに「APIキーは環境変数・WIF・ant CLI経由のいずれかで取得、ハードコード禁止」をREADMEに明記

---

### P-100: FX自動売買バックテストへのPIT（Point-in-Time）データ管理実装

**根拠記事**: 613 (ArXiv 2601.11958: Agentic AI Nowcasting)
**詳細**: arXiv論文（2601.11958）が実証したエージェント型ナウキャスティング（シャープレシオ0.87、ベースライン0.31比）の鍵はPoint-in-Time（PIT）データ管理によるデータリーク防止設計にある。bpr_labのFX自動取引バックテストでは、現時点で将来の価格データがバックテスト時刻以前に参照可能になっている可能性があり、過剰に楽観的なバックテスト結果が出る恐れがある。PITラッパーとconfidence加重ポジションサイジングを導入することで、実運用に近い精度のバックテストが実現できる。

**提案アクション**:
1. `sandbox/FX自動取引/` にPITデータラッパークラスを実装: `as_of_date`パラメータを受け取り、指定日時以前のデータのみ返すAPIを設計
2. LLMシグナルのconfidenceスコアに基づくポジションサイジングを実装: `position_size = base_size * confidence_score`（論文記載の手法）
3. マルチモーダル入力（チャート画像+テキストデータ）の組み合わせをバックテストパイプラインに追加（単一モダリティより有意に優秀）
4. CIパイプラインにデータリーク検出テストを追加: バックテスト日より未来のデータ参照を自動検出するアサーションを実装

---

### P-101: ECCフレームワーク参考によるSkills/Instincts設計の強化

**根拠記事**: 608 (GitHub affaan-m/ECC: Everything Claude Code)
**詳細**: GitHub公開OSSのECC（Everything Claude Code）フレームワークは、Claude Code/Codex/Cursor横断でSkills・Instincts・Memory・Security・Research-Firstの5機能を統合したエージェントハーネス設計を実装している。特に「Instincts」（反射的行動ルール）と「processed_urls.txt」（重複収集防止）の設計はbpr_labの日次収集エージェントとCLAUDE.mdのSkills設計に直接応用できる。

**提案アクション**:
1. `CLAUDE.md` に `instincts.md` セクションを追加: 「URL重複チェック→スキップ」「信頼度0.5未満のシグナル→NOISE自動分類」等の反射的ルールを宣言的に記述
2. `library/inbox/processed_urls.txt` を作成し、収集済みURLを永続管理: 日次収集スクリプトが起動時に参照し重複収集をスキップする仕組みを実装
3. `CLAUDE.md` の PreToolUse フックに「WebFetch前にprocessed_urls.txtを確認」ルールを追加
4. ECCリポジトリ（affaan-m/ECC）をフォークしてbpr_lab固有のSkills/Instinctsセットをカスタマイズする実験的ブランチを作成

---

### P-099: 日本AI促進法（2026年6月施行）HITL義務化への緊急対応確認

**根拠記事**: 603 (Didit LLM AI規制コンプライアンス 2026 JA)
**詳細**: 日本AI促進法が2026年6月に施行。特にAIエージェントの外部アクション（売買注文送信・システム変更等）にHITL（Human-in-the-Loop）義務化条件と学習データトレーサビリティ要件が明記された。bpr_labのFX自動取引エージェントは日本国内での運用であり、直接の規制対象となる可能性がある。P-025（HITL設計：confidence 0.55-0.75帯での人間確認）は既に提案済みだが、**同実装が法令施行前に完了しているか**を緊急確認する必要がある。AI促進法のHITL要件は「ハイリスク用途での最終承認が人間によること」を義務付けており、完全自律売買は法令上問題になる可能性がある。

**提案アクション**:
1. **緊急確認**: P-025（HITL設計）の実装状況を即時確認。未実装の場合は、confidence 0.55-0.75帯の人間確認ステップを最優先で実装
2. `sandbox/FX自動取引/` の注文送信ロジックに「人間承認フラグ（`require_human_approval=True`）」をデフォルトONで追加し、完全自律実行はユーザー明示設定でのみ有効化する設計に変更
3. トレーサビリティ要件対応: 全取引決定の入力データ（シグナル・confidence・モデルバージョン）をログとして永続保存する設計を `sandbox/FX自動取引/trade_log.py` に実装
4. CLAUDE.md に「日本AI促進法2026年6月施行: FX自動取引エージェントのHITL要件対応状況」を記録し、法令アップデートを毎月確認するルーティンをP-008のRoutinesに追加

---

## 2026-06-24 提案

### P-102: MCP 2026-07-28 RC仕様への移行計画を即時開始（10週間カウントダウン開始）

**根拠記事**: 622 (ByteIota MCP RC詳解), 624 (AgentWars Sampling非推奨化), 626 (TokenMix 9変更点チェンジログ)
**詳細**: MCP 2026-07-28リリース候補が公開され、最終仕様公開まで残り約5週間（6/24時点）。P-017で「計画を立てるべき」と提案していたが、RCが実際に公開されたため「即時移行開始」フェーズに入った。9つの破壊的変更のうち対応必須のものは①ハンドシェイク廃止（initialize/initializedフローなし）、②セッションIDヘッダー削除。新規MCPサーバー開発（P-011・P-013・P-041）は今すぐRC仕様で設計すべき。また、Sampling非推奨化（Agent Wars解説）により、サーバーからLLMに判断を委ねるパターンは非推奨。

**提案アクション**:
1. 現在使用中または開発予定のMCPサーバーでSampling/Roots/Logging使用箇所を検索: `grep -r "sampling\|roots\|logging" sandbox/FX自動取引/ .claude/`
2. P-041（MCP stateless設計）をRC仕様準拠に更新：セッションIDなし・_metaフィールド対応・ハンドシェイクなし
3. P-013（MetaTrader MCPサーバー）のFastMCP実装時に、ステートをSQLiteに外出しし_metaでハンドルを渡す新仕様パターンで設計
4. 7月28日（最終仕様公開）後2週間以内にSDK更新対応を完了するスケジュールをCLAUDE.mdに記録

---

### P-103: Claude Code 5段階Agentネスト・/cdコマンドをFXバックテスト並列化に活用

**根拠記事**: 620 (Qiita Claude Code 6月新機能), 621 (CodeZine 動的ワークフロー・ワークツリー)
**詳細**: Claude Code 2026年6月新機能「Agentツール5段階ネスト」と「/cdコマンド（セッション維持ディレクトリ切替）」が確認された。5段階ネストを使えば、FXバックテスト全体のオーケストレーターエージェント（Level 1）→通貨ペア別エージェント（Level 2）→期間別バックテストエージェント（Level 3）→シグナル生成エージェント（Level 4）→パフォーマンス評価エージェント（Level 5）という完全階層型自律パイプラインが実現できる。/cdコマンドはmonorepoでのsandbox/FX自動取引/←→library/間の移動をセッション継続のまま行える。P-009（Dynamic Workflowsでの並列バックテスト）と組み合わせてさらに強力に。

**提案アクション**:
1. sandbox/FX自動取引/ にLevel 1オーケストレーターのプロンプトを設計：「複数通貨ペア×複数期間のバックテストをLevel 2エージェントに分散し、Level 5評価エージェントが比較レポートを生成」
2. /cdコマンドを使い、バックテスト結果の集計後に`library/`ディレクトリへ移動してcatalog更新作業を同セッション内で継続する標準ワークフローをCLAUDE.mdに記録
3. worktree isolation（`isolation: 'worktree'`）と組み合わせて並列バックテストのファイル競合を防止（P-009との統合）

---

### P-104: Claude Code Artifacts機能でFX取引パフォーマンスレポートを自動ライブページ化

**根拠記事**: 619 (Chaen Claude Code 6月アップデート全まとめ)
**詳細**: Claude Code 6月新機能のArtifacts機能（セッション成果物をライブWebページとして共有）が確認された。FX自動取引のパフォーマンスレポート（月次収益・ドローダウン・シャープレシオ等）をArtifactsとして生成すれば、ブラウザで直接確認できるインタラクティブなダッシュボードとして共有可能になる。Team/Enterpriseプランでは組織内限定共有とバージョン履歴も利用可能（ベータ）。P-037（月次パフォーマンスレビュースキル化）の成果物をArtifactsで提供することで、Bot Pilot向けの視認性が大幅に向上する。

**提案アクション**:
1. `.claude/skills/fx-review/SKILL.md`（P-037）の成果物出力形式をArtifacts対応（HTMLライブページ）に変更
2. Artifacts出力要素：チャート（収益推移・ドローダウン）、統計テーブル（シャープレシオ・最大DD・勝率）、最新シグナル一覧
3. Team/Enterpriseプランの場合、組織限定共有設定でArtifactsをチームメンバーと共有（バージョン履歴付き）

---

### P-105: FX自動売買×LLM記憶の3層構造をbpr_labに実装

**根拠記事**: 631 (note・nic9nic9 FX自動売買+LLM記憶ツール自作体験談)
**詳細**: 国内個人開発者（nic9nic9氏）がFX自動売買ボットにLLM記憶システム（Python+Claude API+SQLite）を組み込んだ実体験レポートが公開された。3層記憶構造：①短期記憶（直近トレード結果・エントリー理由）、②長期記憶（戦略別パフォーマンス・通貨ペア別傾向）、③失敗記録（ドローダウン原因・同じミスの繰り返し防止）。重要な教訓：コンテキスト長制限により長期記憶全体をLLMに渡せないため、ベクトル検索で関連記憶を取得する方式に移行。また、スキャルピングはLLM応答速度で不可→スイングトレード中心に転換。bpr_labのsandbox/FX自動取引/に同様の記憶システムを統合することで、過去の失敗を繰り返さない自律改善型ボットが実現できる。

**提案アクション**:
1. `sandbox/FX自動取引/memory/` ディレクトリを作成し、3層記憶SQLiteスキーマを設計（short_term_trades、long_term_performance、failure_records の3テーブル）
2. Claude API経由の記憶検索：各トレード判断前に関連記憶をベクトル検索（`pip install chromadb`）でコンテキストに追加するラッパーを実装
3. 失敗記録の自動更新：ストップロス発動後にPostToolUseフックが失敗原因分析プロンプトをClaude APIに送信し、failure_recordsに自動追記
4. P-043（LLMバージョン固定）との統合：記憶DBにはLLMバージョンも記録し、モデル切り替え時のパフォーマンス変化を追跡

---

### P-106: MDN MCP Serverを日次収集エージェントのWeb標準参照に追加

**根拠記事**: 627 (gihyo.jp MDN公式MCPサーバーリリース), 628 (Zenn MCPサーバー厳選まとめ)
**詳細**: MDN Web DocsがMCP互換クライアント向けに公式MCPサーバーをリリース（2026年6月15日）。Claude CodeからHTML/CSS/JavaScript/WebAPIの最新ドキュメント、ブラウザ互換性テーブル（Baseline状況）にリアルタイム直接アクセスが可能に。bpr_labのsandbox配下にフロントエンドプロジェクト（ganbarulist、NotebookLM_pptxなど）があり、これらの開発セッションでのWeb標準参照に有用。Zennの厳選まとめでもSerena（LSP統合・コードベース依存関係理解）が紹介されており、合わせて導入を検討すべき。

**提案アクション**:
1. `.claude/settings.json` の `mcpServers` に MDN MCPサーバーを追加（`claude mcp add mdn-docs @modelcontextprotocol/server-mdn`）
2. Serena MCPサーバー（`npm install @sernaic/serena-mcp-server`）を評価：大規模コードベース（sandbox/FX自動取引/）のLSP統合によるコンテキスト改善効果を確認
3. Draw.io MCPサーバーをFX自動取引アーキテクチャ図の作成に活用（architecture.mdの視覚化、P-103・P-105の設計図を自動生成）

---

### P-107: Claude Code /rewindコマンドをbpr_lab長時間セッションの標準チェックポイント運用に追加

**根拠記事**: 642 (MindStudio Claude Code /rewind解説)
**取得日**: 2026-06-25
**詳細**: 2026年6月24日のClaude CodeアップデートでClaude Code CLIに`/rewind`コマンドが追加された。`/clear`実行前の状態（会話コンテキスト＋コード変更の両方）に巻き戻せる機能で、長時間セッションでの安全性が大幅向上。bpr_labでの活用場面：①daily-collect実行中に途中でNOISE判定を変更したくなった場合に、SIGNALとして保存した内容以前に戻れる、②FXバックテストセッションでパラメータ変更が失敗した時に変更前の状態に復元、③catalog.md更新中に誤った連番を付けた場合の修正。現在はセッション開始前の`git stash`に頼っているが、/rewindにより軽量なチェックポイントが増える。

**提案アクション**:
1. CLAUDE.md の「長時間セッション作業時の注意」セクションに `/rewind` の活用パターンを追記（例：「重要な判断前に `/rewind` でチェックポイントを確認してから実行」）
2. `.claude/skills/daily-collect/SKILL.md` の手順に「Step 4-2完了後、articles/保存前に `/rewind` 確認ポイント」を明示
3. /rewindとgit commitの使い分け基準をCLAUDE.mdに記載：/rewind→セッション内の短期巻き戻し、git commit→長期保存・他セッションへの引き継ぎ

---

### P-108: SKILL.md明示起動型（disable-model-invocation: true）をbpr_labスキルに適用

**根拠記事**: 644 (ar-aca.tech Claude Code SKILL.md完全ガイド2026)
**取得日**: 2026-06-25
**詳細**: Claude Code Skills には2タイプある。①常時ロード型：descriptionをClaudeが読んで自動判断でロード（誤発火リスクあり）、②明示起動型（`disable-model-invocation: true`）：ユーザーが`/name`で明示起動・Claudeはスキルの存在を認識しない（副作用を伴うワークフローに推奨）。bpr_labの既存スキル（/daily-collect, /fx-backtest, /catalog-update等）はコミット・ファイル作成・push等の副作用を伴うため、明示起動型への移行が安全性向上に直結。現在のSKILL.md設定が常時ロード型になっているスキルは誤発火で意図せずarticlesが追加される危険がある。

**提案アクション**:
1. `.claude/skills/` 配下の各SKILL.mdを監査し、副作用を伴うスキル（commit/push/write/delete操作を含む）を特定
2. 対象スキルに `disable-model-invocation: true` を追加し、明示起動型に変更
3. 変更後は起動方法を `/{skill-name}` コマンドに統一し、CLAUDE.mdのスキル一覧セクションも更新
4. 常時ロード型として残すべきスキル（参照のみ、読み取り専用の補助スキル）の判断基準をCLAUDE.mdに記載

---

## 2026-06-26 提案

### P-109: wshobson/agents マルチハーネスマーケットプレイスの評価 — Claude Code Skills の横断再利用

**根拠記事**: 651 (GitHub wshobson/agents Multi-Harness Agent Plugin Marketplace)
**取得日**: 2026-06-26
**詳細**: wshobson氏がClaude Code・Codex CLI・Cursor・OpenCode・GitHub Copilot・Gemini CLI向けの統一プラグインマーケットプレイスをOSSで公開した。チームが複数のAIコーディングツールを使い分ける場合に、SKILL.md定義・MCPサーバー設定・フック定義を一元管理できる。bpr_labのClaude Code Skillsを同フォーマットで管理することで、将来の別ツール移行コストを最小化できる可能性がある。またClaude Codeコミュニティマーケットプレイス構想（2026年6月のSitePoint記事に言及）が実現した際に、bpr_labのSkillsをコントリビュートする基盤にもなる。

**提案アクション**:
1. wshobson/agentsリポジトリの構造を確認し、bpr_labの`.claude/skills/`配下の既存SkillsをGitHubにマーケットプレイスフォーマットで公開可能か評価
2. 特に汎用性の高いスキル（/daily-collect・/fx-review等）をClaude Code公式マーケットプレイス候補としてパッケージ化し、再利用可能なフォーマットで整備
3. 異なるAIツール（Cursor等）を使い始める場合の移行コストゼロを目標に、ツール非依存な設計でSKILL.mdを整備

---

### P-110: FX自動取引ボットへのWalk-Forward Test導入 — LSTMとGradient Boostの精度比較

**根拠記事**: 656 (MacawDigital ML replacing rule-based trading 2026), 654 (Nurp Future of Algorithmic Trading 2026-2030)
**取得日**: 2026-06-26
**詳細**: 2026年時点でのアルゴリズム取引MLのベストプラクティスとして「walk-forward testing・out-of-sample検証・ルックアヘッドバイアス排除」の3セットが必須と明確化された。現在sandbox/FX自動取引/ のバックテスト（P-009・P-043）はルックアヘッドバイアス排除の仕組みが未実装の可能性がある。また、LSTM（逐次パターン・長期依存）と勾配ブースティング（高頻度データ・解釈可能性）の2系統が現在のMLトレーディングのベンチマーク。P-014（信頼度閾値）・P-043（再現性リスク）と組み合わせることで、より堅牢なバックテスト評価体系が構築できる。

**提案アクション**:
1. sandbox/FX自動取引/backtest/ にwalk-forward testing実装を追加（訓練ウィンドウ=過去12ヶ月、検証ウィンドウ=1ヶ月、1ヶ月ずつスライド）
2. LSTMベースのシグナル生成（PyTorch/Kerasで実装）と既存のLLMシグナル生成を並列実行し、同一バックテスト期間でシャープレシオ・最大ドローダウン・勝率を比較
3. P-043（LLMバージョン固定）のCI設定にwalk-forward test結果の統計的等価性チェックを追加し、モデル変更時に性能が有意に劣化していないことを自動検証
4. ルックアヘッドバイアス排除チェックリストをsandbox/FX自動取引/BACKTEST_RULES.mdに作成（特徴量エンジニアリングでの未来データ使用・スプレッド/スリッページ未考慮・スケーラー学習データリークの3大リスクを対象）


## 2026-06-27 提案

### P-111: FX自動取引への反映 — MT5 + Python + ONNX統合パターン（+57%利益改善実証）

**根拠記事**: 663 (MQL5 MetaTrader5 Python ONNX AI Trading Platform June 22)
**取得日**: 2026-06-27
**詳細**: MQL5公式記事（2026年6月22日）がMT5プラットフォーム上でのPython→ONNX→MQL5統合の完全ワークフローを実証。MACD指標にONNXフィルターを追加した実例では取引数209件→152件（27%削減）・利益$884→$1,388（+57%）という具体的な成果が示された。外部LLMへのWebRequest統合も可能で、MT5内からClaude API等を直接呼び出せる。Pythonでモデル訓練→ONNX形式エクスポート→MQL5でインポートして使用というパイプラインは、sandbox/FX自動取引/で現在検討中のLLMシグナル生成に直接応用可能。

**提案アクション**:
1. sandbox/FX自動取引/ にONNX統合レイヤーを追加（Python側でscikit-learn/PyTorchモデル訓練→`skl2onnx`または`torch.onnx.export`でONNX変換→MT5側でONNXモデルとして読み込み）
2. MQL5のWebRequest機能を使ってClaude APIをMT5内から直接呼び出す実装を試験（シグナル生成・センチメント分析をLLMに委譲）
3. P-043（LLMバージョン固定）・P-110（walk-forward test）と組み合わせて、ONNX静的モデル（再現性高）とLLM動的判断（適応性高）のハイブリッドアーキテクチャを設計

---

### P-112: CLAUDE.md・skills-registry への反映 — Fable 5停止事案を受けたfallbackModel設定の標準化

**根拠記事**: 658, 659, 660 (Fortune Fable5停止、Snyk教訓、TrueFoundry マルチプロバイダーゲートウェイ)
**取得日**: 2026-06-27
**詳細**: Fable 5/Mythos 5の全世界ゼロ通告停止は、AIモデルへの単一依存がビジネス継続リスクになることを実証した。Claude Code v2.1.185で`fallbackModel`設定が追加されており、主モデルが利用不能の場合に自動フォールバックが可能。Snykの推奨事項（モデル冗長性の確保・AI資産の可視化・段階的制御戦略）はbpr_labの日次収集エージェントにも適用できる。

**提案アクション**:
1. CLAUDE.mdに以下を追記:
   ```
   ## モデルフォールバック設定
   - 主モデル: claude-sonnet-4-6（または最新sonnet）
   - fallbackModel: claude-haiku-4-5-20251001（規制・停止時の軽量フォールバック）
   - Fable 5/Mythos 5は2026年6月13日以降利用不可（輸出管理規制）
   ```
2. `.claude/settings.json`に`fallbackModel`設定を追加し、モデル停止時でも日次収集エージェントが継続稼働できる体制を整備
3. sandbox/FX自動取引/のLLMバックエンド設定にもフォールバックロジックを追加（例：FableModel → Opus 4.8 → Sonnet 4.6の順でフォールバック）

---

### P-113: Claude Code Skills への反映 — `/agent-teams`スキル作成（4役割並列開発パターン）

**根拠記事**: 664 (Medium KargarIsaac Agent Teams Claude Code SDK 実装)
**取得日**: 2026-06-27
**詳細**: Agent Teamsは`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`で有効化し、`TeamCreate`・`SendMessage`・`TeamDelete`ツールでマルチエージェント協調が実装できる。実例（アーキテクト・実装者・テスター・ドキュメント作成者の4エージェント）はbpr_labの複合タスク（FX戦略設計・コードレビュー・テスト・ドキュメント同時作業）に直接応用可能。P-009（Dynamic Workflows並列バックテスト）・P-003（/agent-teamsスキル化）との組み合わせが有効。

**提案アクション**:
1. `.claude/skills/agent-teams/SKILL.md`を作成し、以下のパターンを定義:
   - `architect`（設計検討・分割計画）
   - `implementer`（コード実装）
   - `tester`（テスト実行・品質確認）
   - `documenter`（README・コメント更新）
2. sandbox/FX自動取引/ の新機能開発時にAgent Teams（4エージェント）で並列開発する運用フローをCLAUDE.mdに記載
3. Dynamic Workflowsとの違い（Claude Code内チームvs外部Agent SDK）を理解した上で、用途別の使い分けガイドをCLAUDE.mdに追記

---

### P-114: FX自動取引への反映 — Claude 4.5 Sonnetの明示的BUY/SELL拒否問題と代替モデル選定

**根拠記事**: 677 (MQL5 MT5 LLM Selection GPT-4o DeepSeek-V3 Claude Comparison)
**取得日**: 2026-06-28
**詳細**: MQL5公式ブログが2026年版のMT5向けLLM比較を実施。重大な発見: Claude 4.5 Sonnetは明示的な「BUY」「SELL」という取引指示プロンプトに対して拒否（refusal）が発生し、MT5との直接統合では設計上の課題となる。GPT-4oはネイティブJSON Modeでマルチタイムフレームレジーム分析に最適。DeepSeek-V3はOpenAI比5〜17倍安価で数学的パターン認識に優秀。sandbox/FX自動取引/ のLLMバックエンドにClaudeを使用する場合は、BUY/SELLの直接指示ではなく間接的な「市場分析→人間の解釈→実行」という分離アーキテクチャが必要。

**提案アクション**:
1. sandbox/FX自動取引/ のLLMプロンプト設計を見直し: 「BUY/SELLを推奨せよ」ではなく「市場状況を分析し、主要なリスク・機会を説明せよ」という形式に変更し、最終売買判断はルールベースエンジンで実施
2. 代替モデルとしてDeepSeek-V3（コスト効率）またはGPT-4o（JSON Mode安定）を評価対象に追加
3. P-111（MT5 ONNX統合）と組み合わせ: Claude → 定性的な市場分析・センチメント解説、DeepSeek/GPT → 構造化されたBUY/SELL判断という役割分担ハイブリッドアーキテクチャを設計

---

### P-115: Claude Code MCPセットアップへの反映 — MCPトンネルでプライベートネットワーク内サーバーに接続

**根拠記事**: 671 (Releasebot Anthropic June 2026 Release Notes - MCP Tunnels)
**取得日**: 2026-06-28
**詳細**: AnthropicがMCPトンネル（リサーチプレビュー）を2026年6月リリースに含めた。これによりVPNなしにファイアウォール内部のMCPサーバーにClaudeからアクセスできるようになる。bpr_labでVPS上のcronジョブ（collect_x.py）と連携したMCPサーバーを設置し、X投稿収集データをClaudeから直接取得するワークフローの実現可能性が高まった。

**提案アクション**:
1. VPS上にシンプルなMCP SSEサーバーを設置し、`library/inbox/x/` の最新データをClaudeに提供するエンドポイントを構築
2. MCPトンネルを使ってリサーチプレビューで接続テスト（セキュリティモデルの確認が必要）
3. X投稿収集フローを強化: 現在のGitHub push経由ではなく、VPS MCPサーバー経由でリアルタイムデータ取得が可能になる

---

## 2026-06-29 提案

### P-116: Claude Code ワークフローへの反映 — /rewind コマンドとMCP認証自動再接続の活用

**根拠記事**: 696 (Claude Code 2.1.191: /rewind・MCP認証修正)
**取得日**: 2026-06-29
**詳細**: v2.1.191で追加された `/rewind` コマンドは、誤って `/clear` を実行してコンテキストを失った場合に直前の状態に戻ることができる重要な操作。現在のbpr_labでの日次収集エージェント実行中に `/clear` を誤実行するとコンテキストが失われていたが、`/rewind` で即時復旧可能になった。また、MCP headersHelper認証改善（401/403時の自動再接続）でMCPサーバー接続が不安定になった場合の手動対応が不要になる。

**提案アクション**:
1. CLAUDE.mdの「緊急時の操作」セクションに `/rewind` を追記（`/clear` 誤実行時の復旧手順）
2. `.claude/skills/daily-collect/SKILL.md` に「MCPサーバー接続エラー時は自動再接続を待つ（v2.1.191以降は手動リスタート不要）」を記載
3. CPU負荷が問題になっていた場合（ストリーミング中のCPU高負荷）、v2.1.191にアップデートすることで37%削減される——`claude --version` で確認

---

### P-117: FX自動取引への反映 — MCPMarket Trader Server の評価・ariadng版との比較

**根拠記事**: 701 (MCPMarket Trader MCP Server), P-013 (MetaTrader MCP Server ariadng版)
**取得日**: 2026-06-29
**詳細**: MCPMarketに掲載されている商用Trader MCP Serverは、P-013で検討したOSS版（ariadng/metatrader-mcp-server、32ツール）に対して以下の追加機能を持つ可能性がある: OCO注文・ポジション一括決済・EA制御・口座マージン計算。両者ともWebhookブリッジアーキテクチャを採用しているが、商用版はサポートとドキュメントが充実している可能性がある。Claude Code + MCP + MT5の統合を本格検討する段階でOSS vs 商用の比較評価が必要。

**提案アクション**:
1. ariadng/metatrader-mcp-server（無料・OSSsss・Apache 2.0）とMCPMarket Trader Server（商用）の機能比較表を作成
2. 評価基準: ①サポート注文タイプの種類、②スリッページ・複数ブローカー対応、③Claude Codeとの設定容易性、④価格・ライセンス
3. P-013のアクション1（git cloneでのローカルセットアップ確認）を先に実施し、OSS版で実現できない機能があれば商用版を追加評価
4. 選定後は P-030（FastAPI アーキテクチャ）・P-032（Hooksとの統合）と組み合わせた完全パイプラインを設計

---

### P-119: Claude Sonnet 5（6/30リリース）をエージェント設定に反映する

**根拠記事**: 720 (Claude Sonnet 5 Official Launch), 721 (TechCrunch), 723 (VentureBeat)
**取得日**: 2026-06-30
**詳細**: 本日2026年6月30日、Anthropicがclaude-sonnet-5をリリース。Opus 4.8に迫るエージェント性能（推論・ツール使用・コーディング・複数ステップ自律実行）を$2/$10/Mトークン（導入期、8月31日まで）で提供。Opus 4.8（$5/$25）の6割以下。Claude CodeではFree/Proプランのデフォルトモデルに。CLAUDE.mdやagent設定で`claude-sonnet-4-6`を指定している箇所は`claude-sonnet-5`への移行を検討する価値がある。特に多数のサブエージェントを並列実行するFX自動取引エージェントでは、コスト削減効果が大きい。

**提案アクション**:
1. `sandbox/FX自動取引/.claude/CLAUDE.md` 等でモデル指定があれば`claude-sonnet-5`への移行を検討（エージェント的作業はSonnet 5でOpus水準を期待可能）
2. skills-registry等のskillでモデルをハードコードしている場合は最新デフォルトを使う形に見直し
3. claude-sonnet-5の導入価格期間（〜8月31日）を活用した集中的なPoCを実施
4. `library/catalog.md`の「今週のモデル状況」欄があれば更新（現在のデフォルト: Free/Proプランがclaude-sonnet-5）

---

### P-120: Claude Code Checkpoints機能をFX自動取引の安全設計に組み込む

**根拠記事**: 722 (GitHub Changelog: Claude Sonnet 5 + Checkpoints)
**取得日**: 2026-06-30
**詳細**: 本日リリースのClaude Code新機能「Checkpoints」は、最もリクエストの多かった機能として追加されたもので、作業途中の進捗を自動保存し、任意の時点に即時ロールバックできる。FX自動取引エージェントでClaude Codeを使って取引ロジックを開発・修正する際、破壊的な変更前にCheckpointを活用することで、誤ったコード変更による損失を防止できる。

**提案アクション**:
1. `sandbox/FX自動取引/CLAUDE.md`（または`.claude/CLAUDE.md`）に「危険な変更前に必ずCheckpointを作成する（/checkpoint）」を手順として追記
2. ネイティブVS Code拡張（本日リリース）をFX取引開発環境にインストールし、IDE内でのClaude Code連携を強化

---

### P-121: MCP × FX自動取引のセキュリティ設計を厳格化する

**根拠記事**: 713 (aurant-technologies: Claude Code × MCP Security 2026)
**取得日**: 2026-06-30
**詳細**: 2026年4月にOX SecurityがMCPのSTDIO実行モデルに起因するRCE（任意コマンド実行）脆弱性を公表。Claude CodeでMCPサーバーを使ってMT5・証券会社API・データフィードに接続するFX自動取引システムは、この脆弱性の影響を受けるリスクが高い。リスク資産を扱うシステムでは厳格なセキュリティ設計が必須。

**提案アクション**:
1. `sandbox/FX自動取引/architecture.md`に「MCPセキュリティ原則」セクションを追加：信頼できるソースのMCPサーバーのみ使用・最小権限（--allow-list）・ネットワーク隔離・監査ログ取得
2. FX自動取引で使用するMCPサーバー（Trader MCP Server等）のソースコードを必ず検証してから使用
3. MT5接続MCPサーバーのアクセス権限を取引実行のみに限定し、システム管理コマンドへのアクセスを禁止

---

### P-118: FX自動取引設計方針の強化 — LLM単体FX実験の否定的データを根拠に

**根拠記事**: 702 (LLM-Driven MT5 Trading実験: GPT-4o/Claude/DeepSeek全モデル統計的優位なし)
**取得日**: 2026-06-29
**詳細**: 2026年1月の独立実験（実装付き）でGPT-4o・Claude 3.5・DeepSeek V3の3モデルがMT5でFX（EUR/USD・USD/JPY）取引を実施した結果、全モデルでランダムウォーク仮説を棄却できなかった（シャープレシオ0.3〜0.5）。スプレッドコストが利益を全額侵食したことが主因。これはP-026（3ヶ月運用レポートからの教訓）・P-114（Claude BUY/SELL拒否問題）と三重に整合する証拠となり、「LLM単体での短期FX取引は現時点で困難」という設計方針の根拠が一段と強まった。実験者の結論: マルチエージェント構成＋中長期タイムフレーム（日足以上）への移行が有望。

**提案アクション**:
1. `sandbox/FX自動取引/architecture.md`（P-037参照）に「LLM単体短期取引の限界: 3件の独立実験でランダムウォーク以上の統計的優位なし（P-026・P-114・P-118参照）」を追記し、設計原則を文書化
2. LLMの役割を「短期価格予測」から「ファンダメンタルズ解析・ニュースフィルタリング・中長期トレンド判断」に明示的に限定
3. 実験コード（FastAPI Webhookブリッジ実装）を参考に、sandbox/FX自動取引/ のブリッジアーキテクチャ設計を精緻化（P-030・P-032との統合）
4. 「日足以上の中長期タイムフレーム×マルチエージェント（センチメント＋テクニカル＋ファンダ）」をPoCの最優先実装パスとしてbacklog.mdに登録

---

## 2026-07-01 提案

### P-119: Claude Sonnet 5 への日次収集エージェントモデル移行 — Opus比コスト50-80%削減

**根拠記事**: 726 (BuildFastWithAI Sonnet 5ベンチマークレビュー), 728 (wmedia Sonnet 5 Claude Code実践), 724 (Claude Code v2.1.197)
**取得日**: 2026-07-01
**詳細**: Claude Sonnet 5（2026-06-30 GA）はTerminal-Bench 2.1でOpus 4.8（74.6%）を超える80.4%を達成し、GDPval-AA v2知識労働でも1618 Elo（Opus 4.8: 1615 Elo）を上回る。日次収集・キュレーションエージェントのような「知識労働＋Web検索・要約」タスクではOpus 4.8との性能差がほぼない一方、コストは$2/$10（vs Opus $5/$25）と60-80%削減できる。ただし注意点：新トークナイザーはSonnet 4.6比で最大35%多くトークンを消費するため、実効コストはレートカード差（60%削減）より小さい可能性がある。opusplanモード（/model opusplan）を使えばプランニングにOpus 4.8・実行にSonnet 5のハイブリッドも選択可能（2026-07-01現在）。

**提案アクション**:
1. 日次収集エージェント（本スクリプト）のセッションモデルを`/model sonnet`（Sonnet 5）に変更し、1週間の出力品質を評価
2. トークン消費量をBashで計測し、旧Sonnet 4.6比35%増を加味した実効コストを算出
3. FX自動取引のシグナル生成（P-033・P-040）では精度重視のOpus 4.8を維持し、テクニカルデータ前処理・ニュース要約のみSonnet 5に切り替えるティア別ルーティングを実装（P-024参照）
4. 2026年8月31日のプロモーション価格終了後（$3/$15に移行）にコスト試算を再実施

---

### P-120: Sonnet 5の新トークナイザーによるコスト影響をCLAUDE.mdに警告追記

**根拠記事**: 726 (BuildFastWithAI Sonnet 5ベンチマーク), 724 (Claude Code v2.1.197 changelog)
**取得日**: 2026-07-01
**詳細**: Claude Sonnet 5は新しいトークナイザーを採用しており、同一テキスト入力がSonnet 4.6比で最大35%多いトークンを生成する。既存のコードや日次収集プロンプトでSonnet 4.6ベースのトークン使用量を想定した予算設定をしていた場合、Sonnet 5移行後にコストが予想を上回る可能性がある。APIレートカードが安くなっても（$2 vs $3/Mトークン入力）、実トークン消費が35%増えるとネット削減効果が小さくなる。P-119のコスト試算で必ず実測が必要。

**提案アクション**:
1. CLAUDE.mdのモデル設定セクション（P-001参照）に「Sonnet 5はSonnet 4.6比最大35%多いトークンを消費するためコスト試算時に要注意」の警告を追記
2. `claude --output-format json`等でトークン使用量を記録するラッパーを日次収集エージェントのHookに追加し、週次でSonnet 4.6時代の実績と比較
3. P-021（使用量上限設定）と組み合わせて月次トークン消費量のアラート閾値を再設定

---

### P-121: FundaPod型「人間中心LLMリサーチ」をFX自動取引ウォッチリスト分析に適用

**根拠記事**: 732 (FundaPod arxiv 2605.27864 — LLMマルチペルソナ投資リサーチ)
**取得日**: 2026-07-01
**詳細**: FundaPodの設計哲学「エージェントは独立したペルソナを持ち、合意を強制せず対立意見を保存、人間が事後判断する」はP-118（LLM単体短期取引の限界）・P-026（LLM補助役割の有効性）と整合する。FundaPodの知識グラフ「第二の脳」（ティッカー・メモ・アナリスト・投資テーマを接続）は、sandbox/FX自動取引/ における通貨ペア×マクロイベント×ニュースソースの関係性を蓄積するデータ構造として参考になる。特にPeルソナ蒸留パイプライン（公開資料からエージェント化）はトレーダー有名人・著名アナリストの投資哲学をエージェントに組み込む応用が可能。

**提案アクション**:
1. sandbox/FX自動取引/ のマルチエージェント設計（P-004・P-020参照）において、「ファンダ重視派」「テクニカル重視派」「マクロ重視派」の3ペルソナエージェントが独立分析して対立意見を保存する構成を採用
2. FundaPodの「根拠証拠モデル」（分析→ソース直リンク）を参考に、各LLMシグナルがどのデータ（ニュース記事URL・経済指標値）に基づくかを必ず記録するロギング設計を実装
3. arxiv 2605.27864 の実装コード（リポジトリ公開有無を確認後）をベースにしたPoC構築を検討

---

## 2026-07-02 提案

### P-122: FX自動取引への反映 — AlgoEvolve/MadEvolve式LLM進化的最適化の戦略パラメータ探索への適用

**根拠記事**: 742 (AIHerald: AlgoEvolve 2026), 745 (arXiv 2605.23007: MadEvolve)
**取得日**: 2026-07-02
**詳細**: AlgoEvolve（AIHerald）とMadEvolve（arXiv 2605.23007）の両フレームワークが「LLMをセマンティック突然変異演算子として使う進化的取引戦略生成」の有効性を実証した。AlgoEvolveは従来手法比23%改善を達成。ただし規制リスクがあり、LLM進化システムが明示的指示なしにレイテンシーアービトラージ的行動を自生的に生成した事例が報告されている。sandbox/FX自動取引/のパラメータ最適化（P-009参照）に、人間監視下での制限付き進化探索として適用できる。P-043（TradingAgents再現性リスク対応）で確立したLLMバージョン固定・リグレッションテストの仕組みと必ずセットで実装すること。

**提案アクション**:
1. `sandbox/FX自動取引/evolve/` ディレクトリを作成し、既存戦略コードをLLMに渡す→バックテストで評価→上位案を次世代のベースにするMadEvolveパターンの簡易実装を試作
2. 進化ループの停止条件を明示（世代数上限・コスト上限・改善率閾値）し、無制限の自律最適化を防止
3. 生成された戦略コードを必ず人間レビューしてから本番適用する承認ゲートを設計（P-025 HITL設計と同原則）
4. レイテンシーアービトラージ的行動を事前にブラックリスト化したプロンプトガードを追加し、規制リスクを軽減

---

### P-123: Claude Code Hooksを「決定論的強制」として徹底活用——CLAUDE.md依存から脱却

**根拠記事**: 737 (Penligent: Inside Claude Code Architecture), 738 (iwoszapar: 8 Rules Hard Way)
**取得日**: 2026-07-02
**詳細**: 今日収集した2記事が独立して同じ結論に到達した：「CLAUDE.mdは勧告的（モデルが従わない可能性がある）、Hooksは決定論的（必ず実行される）」。bpr_labで重要なルール（catalog.md自動更新・命名規則チェック・article番号の重複防止）が現在CLAUDE.md記述に依存しているため、稀にルール違反が発生している。これらをHooksで実装することで100%の遵守率を保証できる。P-039（4象限フレームワーク）・P-038（自己学習フック）と統合した包括的なHooks体系を構築すべきタイミングが来た。

**提案アクション**:
1. `.claude/settings.json` の `hooks` セクションに以下を追加：`PreToolUse`（WriteツールでArticle番号の重複チェック）・`PostToolUse`（ファイル作成後にcatalog.md自動更新トリガー）・`Stop`（セッション終了後の学習サマリー自動追記）
2. CLAUDE.mdから「必ず守るべきルール」と「Claudeに理解させる文脈」を分離し、前者をHooksへ移行
3. Hooksのテストスクリプトを作成し、各Hookが意図通りに動作することを検証してから本番適用

---

### P-124: EU AI Act 2026-08-02 施行に向けたFX自動取引ボットの透明性開示対応

**根拠記事**: 748 (LegalNodes: EU AI Act 2026 Compliance), 749 (KennedysLaw: EU AI Act Timeline)
**取得日**: 2026-07-02
**詳細**: EU AI Act Phase 3（2026-08-02施行）では透明性規則（Article 50）が適用される。EU在住ユーザー向けにFX自動取引ツールをサービスとして提供する場合、AIが意思決定に関与していることを明示する義務が生じる可能性がある。現在の`sandbox/FX自動取引/`は個人利用研究目的であり直接対象外の可能性が高いが、将来のサービス化・商用展開を見据えた設計上の事前準備が重要。P-035（Colorado AI法対応）と合わせて国際対応の設計方針を整備する。

**提案アクション**:
1. `sandbox/FX自動取引/README.md`に「本システムの利用者向け開示」セクションを追加: AIが売買シグナル生成に関与していること・使用モデル・限界・人間による最終判断の有無を明記
2. P-025（HITL設計）の実装ログをトレーサビリティ要件（Article 13/14）対応のフォーマットで記録
3. EU AI Act Article 50の透明性義務（AIコンテンツ開示・ユーザー通知）の自動チェックをCI/CDに組み込む構成を将来的に検討

---

### P-125: MCP Server 15選（nuco・capy-tech）から bpr_lab 優先導入サーバーを選定

**根拠記事**: 739 (CapyTechLog: MCPサーバー完全ガイド2026), 740 (nuco: 業務効率化MCPサーバー15選)
**取得日**: 2026-07-02
**詳細**: 独立した2記事が共通して推薦するMCPサーバーが特定できた：GitHub MCP・Sequential Thinking・Memory・Context7・Brave Search・Playwright。bpr_labの日次収集エージェントにとって最も直接的な価値があるのは①Brave Search（WebSearch代替・コスト削減）②Sequential Thinking（複雑な収集計画の立案品質向上）③Memory（セッション間の記事記憶共有）④GitHub MCP（catalog.md・articles/ファイルの自動更新）の4サーバー。P-041（MCPステートレス設計方針）に従い、新規サーバーは将来の仕様変更対応を考慮して実装すること。

**提案アクション**:
1. `.claude/settings.json` の `mcpServers` に Brave Search MCP を追加し、日次収集のWebSearch呼び出しをBrave Search経由に移行（コスト削減・レート制限緩和）
2. Sequential Thinking MCP を導入し、多クエリ検索計画の立案・重複排除判断に活用
3. Memory MCP でセッション間の「既収集URL記録」を共有し、Bash grep代替の高速重複チェックを実現
4. 4サーバーの段階的導入計画（Week 1: Brave Search → Week 2: Sequential Thinking → Week 3: Memory → Week 4: GitHub MCP）を`.claude/rules/mcp-setup.md`に記録

---

## 2026-07-03 提案

### P-126: Claude Sonnet 5 への移行検討 — 新トークナイザーによるコスト再試算が必要

**根拠記事**: 751 (Anthropic Claude Sonnet 5 公式), 752 (TechCrunch), 753 (Simon Willison分析)
**取得日**: 2026-07-03
**詳細**: 2026年6月30日にClaude Sonnet 5がリリースされ、Opus 4.8に近い性能・1Mコンテキスト・アダプティブシンキングデフォルト有効を提供する最もアジェンティックなSonnetとなった。ただし**新トークナイザーが同テキストで約30%多くトークンを生成**するため、入門価格$2/$10（8月末まで）は見かけ上のコスト削減であり、実際の消費コストは検証が必要（Simon Willison分析）。日次収集エージェントやFX自動取引バックエンドにSonnet 5を採用する場合、事前に実際のトークン消費量を計測してコスト試算を再計算することが必須。アダプティブシンキングのデフォルト有効化も出力トークン増加要因となる点に注意。

**提案アクション**:
1. 現在の日次収集エージェントのトークン消費量をベースラインとして記録
2. Sonnet 4.6 → Sonnet 5 切替後のトークン消費量を同一プロンプトで計測し、実コスト比較を実施
3. アダプティブシンキングを無効化するオプション（`thinking: {enabled: false}`）の検討
4. 8月31日の入門価格終了前に本番移行判断を確定（$2/$10 → $3/$15の価格変更タイムライン管理）

---

### P-127: Robinhood Agentic TradingのMCPアーキテクチャをFX自動取引に参考採用

**根拠記事**: 755 (Robinhood Agentic Trading newsroom), 756 (CNBC CEO interview)
**取得日**: 2026-07-03
**詳細**: Robinhoodが2026年5月27日に発表したAgentic TradingはMCP（Model Context Protocol）経由でサードパーティAIエージェントをブローカーアカウントに接続する設計。設定はMCP設定ファイルに1URLを追記するだけで完了。これはP-013（MetaTrader MCPサーバー）・P-041（ステートレスMCP設計）で検討してきた「MT5+MCP+Claude」の統合アーキテクチャと完全に一致する。Robinhoodの実装がMCP経由でエージェントに「ポートフォリオ構築・取引戦略自動化・市場データ分析・注文執行」を許可している事実は、同様のアーキテクチャでMT5を接続する正当性を強く示す事例。CEO発言「AIエージェントは近く人間トレーダーに匹敵する」は業界の方向性を示唆。

**提案アクション**:
1. Robinhood Agentic Trading のMCP URLスキームを調査し、P-013（MetaTrader MCPサーバー）の実装設計に参考採用
2. P-025（HITL設計）の要件をRobinhoodのリスク注記（「AIドライブ戦略のリアルタイム監視・停止困難」）に照らして再評価し、緊急停止機構を設計に明示追加
3. MCP経由のアクション権限スコープ（読み取り専用か注文執行かの段階分け）をRobinhoodの実装を参考に設計

---

### P-128: EU AI Act Article 50 透明性義務（2026年8月2日施行）への対応確認

**根拠記事**: 754 (Sidley Austin実務ガイド), 763 (artificialintelligenceact.eu条文)
**取得日**: 2026-07-03
**詳細**: EU AI Act Article 50の透明性義務が2026年8月2日から施行される。EU域内ユーザーに対してAIシステムを提供・展開する場合：①チャットボット・仮想アシスタントはAIであることの開示、②生成AIの出力は機械可読マーキングが必要。bpr_labがEUユーザー向けにAI生成コンテンツを公開している場合は対応が必要。猶予規定：2026年8月2日以前に市場投入済みの合成コンテンツ生成AIのマーキング義務は12月2日まで延期。FX自動取引ボットが欧州リテール投資家に対してトレードシグナルを提供する場合は本条文の対象になりうる（AIである旨の開示義務）。

**提案アクション**:
1. bpr_labの各サービス（日次収集ライブラリ・FX自動取引ボット）のEU域内ユーザーへの公開範囲を確認
2. EU向けに公開するAI生成コンテンツ（ライブラリ記事・FXシグナル等）にAI生成表示の追加を検討
3. FX自動取引ボットが欧州規制対象金融商品のシグナルを提供する場合は法務確認を優先実施（2026年8月2日の施行日に注意）

---

### P-129: MQL5最新知見を踏まえたFX自動取引のLLM統合アーキテクチャ更新

**根拠記事**: 757 (MQL5 AI EA Complete Guide July 2026), 758 (MQL5 AI Replacing Algos)
**取得日**: 2026-07-03
**詳細**: MQL5公式ブログ2本（2026年6月28日・7月1日）から得られた2026年7月時点の最新知見：①リテールAIトレーダーの大多数はまだルールベース静的最適化EAで運用中——アーリーアダプターには優位性がある；②MARL（マルチエージェント強化学習）+LLMセンチメント分析のハイブリッドが現在の主流アーキテクチャ；③MT5 Python Packageがリリースされており、LLMとEAの連携が大幅に容易化；④LLMはライブ市場データから継続学習する強化学習EAと組み合わせて使うのが最高効率。P-014（4層アーキテクチャ・信頼度閾値）・P-033（TradingAgents）を2026年7月時点の知見で補強する機会。特に「LLMは定性分析・センチメント」「ルールベース・MARLは高頻度実行判断」の役割分担原則が再確認された。

**提案アクション**:
1. sandbox/FX自動取引/ の設計ドキュメントを更新し、「MARL+LLMハイブリッド」アーキテクチャを採用方針として明記（P-014の4層に対して第3.5層としてMARLを追加検討）
2. MT5 Python Package（`MetaTrader5`）の最新バージョンを確認し、LLM→MT5シグナル送信パイプラインの実装難易度を再評価
3. P-114（Claudeの直接BUY/SELL拒否問題）に関連して：Claude Sonnet 5（P-126）では拒否ポリシーが変更された可能性があるため、最新モデルで再テスト実施

---

## 2026-07-04 提案

### P-130: Claude Code v2.1.200-201 仕様変更への日次収集エージェント対応

**根拠記事**: 764 (DevelopersIO: v2.1.200-201 アップデート), 770 (GetAIPerks: Claude Code Updates 2026 Tracker)
**取得日**: 2026-07-04
**詳細**: 2026年7月3日リリースの v2.1.200-201 で2件の重要な仕様変更が入った。(1) `AskUserQuestion` ダイアログが既定で**自動継続しなくなった**（`askUserQuestionTimeout` で設定変更可能）。(2) デフォルトパーミッションモード「default」が「**Manual**」に表示変更。bpr_labの日次収集エージェント（本スクリプト）はバックグラウンドセッションで無人実行しているため、エージェント内で `AskUserQuestion` が呼び出された場合に処理が止まるリスクが生じた。P-008（Routines自動スケジュール化）実装時は特に影響を確認する必要がある。また Manual モードの表示変更により、設定確認コマンドの出力パーサーが壊れている可能性がある。

**提案アクション**:
1. CLAUDE.md または `.claude/settings.json` に `askUserQuestionTimeout: 30` を追加し、無人実行でタイムアウト自動継続を保証
2. 日次収集エージェントのプロンプト内に「人間への質問は行わず、不明点は合理的なデフォルトで判断せよ」の指示を追加（AskUserQuestion 呼び出しを回避）
3. P-008（Routines自動スケジュール化）実装時に、スケジュール実行環境の `askUserQuestionTimeout` 設定を確認してから本番投入

---

### P-131: スラッシュスキル5件連続呼び出しを日次収集ワークフローに活用

**根拠記事**: 765 (DevelopersIO: v2.1.199 アップデート)
**取得日**: 2026-07-04
**詳細**: v2.1.199 からスラッシュスキルを `/skill-a /skill-b /skill-c do XYZ` のように並べて呼び出すと、先頭から最大5件のスキルを同時に読み込んでから実行するようになった（従来は1件のみ）。P-003（`/daily-collect` スキル化）と組み合わせて、日次収集の各フェーズ（Web検索・X取り込み・キュレーション・コミット）を独立したスキルとして設計し、1行のコマンドで全フェーズを順次実行できるようになる。例: `/daily-web /daily-x /daily-curate /daily-commit run daily pipeline`。

**提案アクション**:
1. 日次収集エージェントの4フェーズを独立Skillとして設計：`/daily-web`（Web検索収集）・`/daily-curate`（SIGNAL/NOISE分類）・`/daily-catalog`（catalog更新）・`/daily-commit`（コミット＆プッシュ）
2. `.claude/skills/` に各Skillの `SKILL.md` を作成し、description をP-131の5原則（Qiita記事#768）に従って最適化
3. メインの実行コマンドを `/daily-web /daily-curate /daily-catalog /daily-commit run` の1行に集約し、P-008（Routines）のトリガーとして設定

---

## 2026-07-05 提案

### P-132: Nested Sub-Agents (depth=5) を日次収集エージェントに適用——4ドメイン並列の更新

**根拠記事**: 772 (ChatForest: Claude Code v2.1.172 Nested Sub-Agents depth=5), 773 (AIForAnything: 完全ガイド)
**取得日**: 2026-07-05
**詳細**: v2.1.172（2026年6月10日）で5階層ネストサブエージェントが利用可能になった。P-042（Dynamic Workflows並列化）と同様の効果を、Claude Agent SDKではなくClaude Code Skillsの文脈で実現できる。日次収集エージェントにおいて：①親エージェントが4ドメインに対してdepth=1のサブエージェントを生成（並列実行）、②各ドメインサブエージェントが複数クエリを独立コンテキストで実行、③親が結果を集約・重複排除・catalog更新という3階層構成が可能。「セーフモード」でサブエージェントの権限をread/searchのみに制限することで、情報収集フェーズの安全性を高められる。

**提案アクション**:
1. 日次収集エージェントのStep 1（WebSearch）を4ドメイン別サブエージェント（depth=1）で並列化し、所要時間の短縮効果を測定
2. 各サブエージェントに「セーフモード」（WebSearch・WebFetchのみ許可、ファイル書き込み不可）を適用し、誤ったファイル操作を防止
3. P-131（スラッシュスキル連続呼び出し）と組み合わせ、`/daily-web`スキル内でサブエージェント並列実行を実装

---

### P-133: MCP SDK Betas 2026-07-28 RC の検証——bpr_lab 既存 MCP 設定の動作確認

**根拠記事**: 771 (MCP SDK Betas for 2026-07-28 RC公式ブログ), 777 (MCP Stateless Spec Breaking Changes)
**取得日**: 2026-07-05
**詳細**: MCP SDK Betas（Python/TypeScript/Java/C#）が2026-07-28仕様RC対応で公開された。P-017（MCPステートレス化移行計画）・P-041（ステートレス設計準備）で予告済みの仕様変更が実際のSDKベータとして利用可能になった。6つの破壊的変更（initialize/initialized廃止・Mcp-Session-Id削除等）に対してTier 1 SDKは10週間ウィンドウ内で対応予定。bpr_labで現在使用中のMCPサーバー（GitHub MCP・WebSearch MCP等）がベータSDK上で正常動作するか、最終版（2026-07-28）前に検証すべき。

**提案アクション**:
1. `.claude/settings.json` の `mcpServers` 一覧を確認し、各サーバーが使用するSDKバージョンを特定
2. 2026-07-28までに各MCPサーバーのTier 1 SDK対応版がリリースされるかを追跡（GitHub releaseを監視）
3. P-011（カスタムMCPサーバー開発）・P-013（MetaTrader MCP）の新規実装は2026-07-28 RC仕様準拠で設計し、最終版公開後に本番適用

---

## 2026-07-06 提案

### P-134: CLAUDE.md への反映 — 7つの指示面（Steering Surface）設計フレームワーク導入

**根拠記事**: 782 (Claude Code の指示をどこに書くか — 7つの指示面とコンテキスト負債の設計)
**詳細**: 指示の記述場所を7種（CLAUDE.md / SKILL.md / hooks / MCP ツール説明 / インラインコメント / セッション内プロンプト / 環境変数）に分類し、それぞれのライフタイム・コスト・適用範囲を最適化する設計フレームワーク。CLAUDE.md が200行超で遵守率が下がる定量的根拠あり。

**提案アクション**:
1. 本プロジェクトの CLAUDE.md が200行以内に収まっているか確認（超過なら整理）
2. SKILL.md・hooks・MCP ツール説明への指示分散を検討し、CLAUDE.md はプロジェクト全般ルールのみに絞る
3. コンテキスト負債（古い・重複した指示の蓄積）を定期的に監査するフックを追加検討

---

### P-135: Claude Sonnet 5 デフォルトモデル変更への対応

**根拠記事**: 785 (Claude Sonnet 5 Deep Dive)、793 (Sonnet 5 Default Model)
**詳細**: 2026年7月1日より Claude Sonnet 5 が Free/Pro のデフォルトモデルに変更。モデルID: `claude-sonnet-5`。1Mトークンのネイティブコンテキストウィンドウ。プロモーション価格 $2/$10 per Mtok（8月31日まで）→ $3/$15。Claude Code v2.1.197+ で利用可能。

**提案アクション**:
1. CLAUDE.md / skills-registry の「推奨モデル」記述を `claude-sonnet-5` に更新
2. 日次収集エージェントのサブエージェント設定でも Sonnet 5 が使われるように確認
3. プロモーション価格が8月31日で終了するため、コスト計算を再確認（$3/$15 で再試算）

---

### P-136: Claude Fable 5 再提供 — モデル選択指針の更新

**根拠記事**: 783 (Claude Fable 5 情報整理)、784 (Fable 5 + ローカルLLM CLI)
**詳細**: Fable 5 が2026年7月7日（PT）に再提供。創造的タスク・長文生成・コード補助に特化。Pro/Max プランで週次上限の一定割合まで追加コストなし。Claude Code での使い分け：創造的タスク→Fable 5、コード・エージェント→Sonnet 5、複雑推論→Opus 4.8。

**提案アクション**:
1. CLAUDE.md にモデル選択ガイド（タスク種別別）を追記
2. FX自動取引のシグナル生成ロジックで「ニュースセンチメント分析」などの自然言語処理タスクに Fable 5 活用を検討
3. skills-registry にモデル使い分けスキルを追加（`/model-picker` スキル案）

---

### P-137: MCP 2026-07-28 RC セキュリティ対応 — bpr_lab の MCP 設定審査

**根拠記事**: 780 (MCP New Spec Opens Three New Attack Surfaces)、778-779, 790-791 (MCP RC 各種ガイド)
**詳細**: MCP ステートレス化で3つの新攻撃面（_meta インジェクション・MCP Apps iframe サンドボックス回避・Multi Round-Trip Requests payload 改ざん）が生じる。エンタープライズ・本番運用では署名検証と入力バリデーション強化が推奨。

**提案アクション**:
1. `.claude/settings.json` の `mcpServers` を確認し、外部ネットワーク公開している MCP サーバーがあればセキュリティ設定を見直す
2. P-133 の動作確認作業にセキュリティチェックリストを追加（_meta フィールド検証・認証ヘッダ確認）
3. カスタム MCP サーバー開発時（P-011）は OAuth 2.1 認証 + リクエスト署名を設計段階から組み込む

---

### P-138: VSCode 拡張機能 — Claude Code サブスク使用量可視化の導入検討

**根拠記事**: 792 (Claude Code のサブスク使用状況を VSCode で常時可視化する拡張機能)
**詳細**: Claude Code の週次使用量・残量をリアルタイムで VSCode ステータスバーに表示する OSS 拡張機能。/usage コマンドの JSON をポーリングして残りトークン・コスト・リセット時刻を可視化。6月の料金変更（Agent SDK 分離課金）後の予算管理に有用。

**提案アクション**:
1. GitHub でリポジトリを確認し、信頼性・メンテ状況を検証
2. Claude Code ヘビーユーザーの環境に試験導入して予算超過の早期検知に活用
3. 類似機能を hooks（PreCompact や SessionStop ライフサイクル）で自前実装することも検討

---

## 2026-07-07 提案

### P-139: Claude Cowork Mobile — FX自動取引ボット稼働状況のモバイル監視

**根拠記事**: 800 (Claude Cowork expands to mobile/web - TechCrunch)
**詳細**: 2026年7月7日、Claude CoworkがMaxサブスクライバー向けにウェブ・モバイルで利用可能になった。「デスクで作業開始・スマートフォンで進捗確認・ラップトップを閉じていてもアウトプットを受取」というユースケースは、FX自動取引ボットの稼働監視と親和性が高い。現在P-008（Routines）で自動化を検討しているエージェントの進捗確認をモバイル経由で行えるようになる。

**提案アクション**:
1. Maxサブスクリプションへのアップグレードを確認し、Claude Cowork on Mobileを試験利用
2. FX自動取引エージェントの稼働レポートをCowork経由で非同期確認できるワークフローを設計（P-008との組み合わせ）
3. `/fx-status` スキルをCoworkで実行し、スマートフォンでシグナル品質・残高・オープンポジションを確認できるようにする

---

### P-140: AI規制コンプライアンス対応 — Illinois AISMA + FTC AI精度ポリシー + UN AI Governance

**根拠記事**: 801 (Illinois AI Safety Measures Act), 802 (UN AI Governance), 803 (FTC AI Accuracy)
**詳細**: 2026年7月6-7日に3つの重要な規制動向が同時に発生した。(1)Illinois AI Safety Measures Act署名（72h報告義務・フレームワーク公開必須）、(2)UN Global Dialogue on AI Governance（法的義務化への国際的コンセンサス形成）、(3)FTC AIの精度ポリシーステートメント草案（コメント7月31日締切）。bpr_labのFX自動取引ボットは「自動化意思決定システム」として今後の規制射程に入る可能性がある（特にP-035参照のColorado ADMTとの整合）。

**提案アクション**:
1. FTCのパブリックコメント（7月31日締切）を確認し、FX自動売買ボットが「AI Accuracy」の要件対象かどうかを調査
2. sandbox/FX自動取引/COMPLIANCE.md を作成し、各規制（Illinois AISMA・FTC・EU AI Act・日本ガイドライン1.2版）への対応状況を整理
3. P-025（HITL設計）・P-035（Colorado ADMT確認）の優先度を「必須」に引き上げ、規制対応の実装を2026年7月中に完了させる

---

### P-141: Anthropic API コスト最適化の実装 — Prompt Cache 90% + Batch API 50% の組み合わせ

**根拠記事**: 809 (Finout.io Anthropic API Pricing 2026 Complete Guide)
**詳細**: finout.ioの包括的コストガイドにより、2026年時点での主要な最適化手段が定量化された：(1)**Prompt Caching**——同一プレフィックス繰り返し呼び出しで90%コスト削減（5分間TTL）、(2)**Batch API**——24時間遅延許容タスクで50%削減。日次収集エージェント・FXシグナル分析では、同一系統のプロンプトプレフィックス（システムプロンプト・ドメイン別インストラクション）をキャッシュ活用することで現在のAPI費用を大幅に削減できる可能性がある。

**提案アクション**:
1. 日次収集エージェントのWebSearch後の分類ステップ（4ドメイン判定）にPrompt Cachingを適用——システムプロンプト（SIGNAL基準・NOISE基準）をキャッシュプレフィックスとして固定化
2. FXシグナル生成のうちセンチメント分析（高頻度・低優先度）をBatch API経由に切り替え（翌日集計で問題ない場合）
3. 月次APIコストをfinout.ioのコスト計算式で試算し、最適化前後のROIを測定・記録

---

## 2026-07-08 提案

### P-142: EU AI Act Article 50 2026-08-02発効（25日後）— 緊急コンプライアンス確認

**根拠記事**: 818 (AI Governance Weekly July 3 2026), 824 (TLT AI Brief July 2026)
**緊急度**: 高（2026-08-02まで25日）
**詳細**: EU AI Act Article 50（透明性義務）が2026年8月2日に発効する。具体的な義務：(1)AI生成コンテンツの開示（AI生成であることの表示）、(2)AIとのインタラクションであることの通知、(3)深層フェイクコンテンツへの明示的ラベリング。bpr_labのFX自動取引ボットがEU在住ユーザーに提供される場合、またはAnthropicのEU APIエンドポイントを使用する場合に適用される可能性がある。TLT AIブリーフは「企業の準備期間が極めて短い」と警告しており、Digital Omnibusでハイリスクシステムの一部は延期されたが、Article 50は予定通り施行。

**提案アクション**:
1. sandbox/FX自動取引/ のユーザーインターフェース（通知・ログ出力）にAI生成コンテンツである旨の開示文を追加（例: "このシグナルはAI（Claude Sonnet 5）により生成されました"）
2. sandbox/FX自動取引/COMPLIANCE.md（P-140で作成予定）にEU AI Act Article 50への対応状況を記録
3. P-025（HITL設計）のHuman-in-the-loop記録が、AI判断の透明性要件を満たす記録として機能するか確認

---

### P-143: FX自動取引バックエンドLLM更新 — Claude Sonnet 5を評価モデルに採用

**根拠記事**: 825 (Claude Sonnet 5 Features June 30 2026), 819 (Best AI Models July 2026)
**詳細**: Claude Sonnet 5（2026年6月30日リリース）がSWE-bench Pro 63.2%・Terminal-Bench 2.1で80.4%を達成しOpus 4.8（74.6%）を上回った。料金は$2/$10/Mトークン（プロモ価格、8月31日まで）でOpus 4.8（$5/$25）の40%コストで同等以上のコーディング・推論能力を提供。P-024・P-040（TradingAgentsのLLMバックエンド選定）の最有力候補として評価すべき段階に到達。加えてFable 5（$10/$50）が輸出規制解除で利用可能となり、最高精度が必要なリスク管理エージェントに使用する選択肢も生まれた。

**提案アクション**:
1. P-033（TradingAgents + Claude）の実装で使用するモデルをClaude Sonnet 5（プロモ期間中はclaude-sonnet-5）に切り替え、Opus 4.8と同一バックテストで精度・コスト・レイテンシを比較
2. 役割別最適モデル試案を更新：Sonnet 5=テクニカル・センチメント分析エージェント（コスト効率）、Fable 5=最終判断・リスク管理エージェント（最高精度）
3. 8月31日のSonnet 5プロモ終了を想定し、9月以降のコスト試算を$3/$15/Mで実施しROI確認

---

### P-144: 中国LLMモデル急台頭（30-46%）への対応 — マルチプロバイダー設計とリスク管理

**根拠記事**: 816 (AI News July 8 2026), 819 (Best AI Models July 2026)
**詳細**: CNBCが確認した米国企業APIトークン使用量の30-46%を中国モデル（GLM-5.2、DeepSeek等）が占めるという事実は重要な業界シフトを示す。GLM-5.2（Z.ai）は初週でVercel上の顧客数80倍・日次トークン量27倍を達成。コスト面では中国モデルが圧倒的に有利だが、(1)データプライバシー（取引戦略・市況データの外部送信先）、(2)サービス継続性リスク（米中関係による輸出規制リスク、Fable 5の事例に類似）、(3)Japan FX規制（金融データの取り扱い）の観点から、FX自動取引ボットへの直接採用は慎重に評価すべき。

**提案アクション**:
1. P-034（ローカルLLMフォールバック）の実装を優先し、中国モデルは「コスト比較ベンチマーク対象」として評価するが本番への採用は当面保留
2. GLM-5.2をローカルOllamaで実行できるか確認し、データがローカルに留まる構成でのみ評価テスト
3. sandbox/FX自動取引/COMPLIANCE.md に「使用LLMプロバイダーと理由」を記録するセクションを追加し、データ主権・規制リスク観点での選定根拠を明文化


---

## 2026-07-09 提案

### P-145: GPT-5.6 Sol/Terra/Luna一般公開（7/9）— FX自動取引バックエンドLLM選択肢の更新

**根拠記事**: 833 (AI News July 9 2026), 834 (Neowin GPT-5.6 GA), 835 (GPT-5.6 Pricing Ultra Mode)
**詳細**: OpenAIがGPT-5.6 Sol（$5/$30）・Terra（$2.50/$15）・Luna（$1/$6）を本日一般公開。P-143（Sonnet 5 評価）に加えて新たな比較対象が追加された。特にTerraNow（$2.50/$15）はSonnet 5（$2/$10プロモ・$3/$15通常）と価格帯が近接する中での直接競合。Speculative Branching技術（並列推論ブランチ後に最適解選択）はFX取引の複数シナリオ評価に適合する可能性がある。一方、SolのCerebrasハードウェアによる750トークン/秒の高速推論は、リアルタイム高頻度取引には魅力的だが現時点では選択ユーザー限定。

**提案アクション**:
1. sandbox/FX自動取引/ のLLMベンチマーク設定にGPT-5.6 Terra（$2.50/$15）を追加し、Sonnet 5との同一バックテストで精度・コスト・レイテンシを比較
2. 役割別最適モデル試案を更新: Luna（$1/$6）=高頻度ニュースフィルタリング候補、Terra=テクニカル分析、Fable 5/Sol=最終判断・リスク管理
3. P-143の8月31日以降コスト試算にTerra $2.50/$15を追加し、Anthropic vs OpenAI の年間コスト比較表を作成

---

### P-146: Senate AI AGENT Act（草案）— Claude Codeエージェント自動化のコンプライアンス対応準備

**根拠記事**: 836 (Ctrl+AI+Reg July 7), 837 (WebProNews AI AGENT Act), 838 (CIO Enterprise Governance)
**詳細**: Sen. Warner（D-VA）のAI AGENT Act草案（6/29公開・パブコメ中）は、月間5000万ユーザー超の大規模プラットフォームへのエージェントアクセスにFTC登録を義務付ける。bpr_labのClaude Codeベース自動化ツール（日次収集エージェント・FX取引エージェント）が「custodial user agent」定義に該当するかは成立時の最終条文次第だが、現時点でも透明性・制御性・ログ記録の観点から早期対応が望ましい。成立すれば各エージェントは人間オペレーターIDとのリンク・ユーザーによる許可/取消制御が必須要件となる見込み。

**提案アクション**:
1. 全エージェント設計にオペレーター情報（takuzokb@gmail.com）と目的・スコープを明記するメタデータフィールドを追加
2. sandbox/FX自動取引/COMPLIANCE.md の「AIエージェント設計」セクションを新設し、AI AGENT Act草案の主要要件（透明性・ユーザー制御・NIST標準準拠）に対する自己評価を記録
3. P-025（HITL設計）の実装を最優先とし、「ユーザーが許可・取消できる制御機能」の技術的実装記録を残す

---

### P-147: Multi-Agent Orchestration 5 Patterns → FX自動取引のアーキテクチャ設計指針として採用

**根拠記事**: 832 (Multi-Agent Orchestration 5 Patterns 2026)
**詳細**: DigitalAppliedの整理した5パターン（Supervisor・Pipeline・Parallel・Hierarchical・Event-Driven）は、P-004（TradingAgentsアーキテクチャ）の具体的設計指針として直接活用できる。現在のFX自動取引では「単一エージェントがすべてを実行」となっているが、5パターンの観点から再設計することで障害耐性と拡張性が向上する。特に「Hierarchical（最大3階層）」パターンはFX取引の意思決定階層（戦略エージェント→テクニカル/センチメント分析エージェント→注文執行エージェント）と自然にマッピングできる。Event-Driven（Webhook起動）はMT5からのティックデータイベントに対応可能。

**提案アクション**:
1. sandbox/FX自動取引/architecture.md にMulti-Agent 5パターンとFX取引の対応表を作成（例: Hierarchical=3層LLM階層、Event-Driven=MT5ティックWebhook）
2. 現状の単一エージェント設計をHierarchicalパターンに移行する際のリファクタリング計画を立案
3. P-014（4層MQL5+LLMアーキテクチャ）との統合: 下位2層（データ収集・執行）はPipeline/Event-Driven、上位2層（LLM推論・最終判断）はHierarchicalで設計

---

## 2026-07-10 提案

### P-148: /doctor コマンドによる CLAUDE.md 肥大化の定期チェック自動化

**根拠記事**: 840 (Claude Code v2.1.206 Changelog)
**詳細**: v2.1.206（2026-07-09）で追加された `/doctor` チェックが、CLAUDE.mdのうちコードベースから自動導出可能なコンテンツを検出してトリム提案する機能を持つようになった。P-015・P-028・P-039で提案してきたCLAUDE.md段階的開示（200行以下・@インポート構造）の実践に、定量的チェックの仕組みが加わった形。定期的に `/doctor` を実行することでCLAUDE.mdの肥大化をサイクルで防止できる。

**提案アクション**:
1. `.claude/settings.json` の hooks セクションに `SessionStart` フックを追加し、`claude /doctor` の結果をログに残す（週次ベースでもよい）
2. P-028（@インポート構造）の整備後に `/doctor` を実行し、残存する冗長コンテンツを特定・削除
3. `EnterWorktree` のプロジェクト外ワークツリー確認ダイアログ（v2.1.206追加）もセキュリティ観点で積極活用

---

### P-149: TradingAgents v0.3.1 の Claude Sonnet 5 対応を FX 取引評価環境に反映

**根拠記事**: 842 (TradingAgents v0.3.1 July 2026)
**詳細**: TradingAgents v0.3.1（2026年7月5日）でClaude Sonnet 5とFable 5が正式サポートされた。P-143（Claude Sonnet 5をFX自動取引評価モデルに採用）の実装ブロッカーが解消された。v0.3.1はAWS Bedrock APIキー認証も追加されており、既存のAnthropicキーと並列でBedrock経由のモデルアクセスも選択可能になった。Alpha Vantageフィルタリングバグ・ルータークラッシュ・チェックポイント問題の修正も含み、実運用安定性が向上。P-033（TradingAgents + Claude 4.x実動テスト）の実行環境をSonnet 5に更新することで、コスト$2/$10/Mのプロモ料金（〜8/31）で評価できる好機。

**提案アクション**:
1. `pip install tradingagents --upgrade` でv0.3.1に更新し、Claude Sonnet 5バックエンドで動作確認（`--model claude-sonnet-5` / `--provider anthropic`）
2. Opus 4.8 vs Sonnet 5のFXシグナル品質・API呼び出しコスト・レイテンシを同一テストケースで比較計測（プロモ料金8/31まで）
3. v0.3.0で追加されたFREDマクロ指標・Polymarketデータをセンチメント補完情報として活用するパイプラインを設計

---

### P-150: Google Cloud フルマネージド MCP サーバー — FX 取引データパイプラインへの活用評価

**根拠記事**: 841 (Google Cloud Managed MCP Servers GA)
**詳細**: Google Cloudが50以上のフルマネージドMCPサーバーをGA公開（2026年5月21日）。BigQuery・Spanner・Cloud SQL・Pub/Sub・Cloud Storage等のデータ分析インフラがMCP経由でClaude Codeから直接アクセス可能になった。P-011（カスタムMCPサーバー開発）の代替として、GCPネイティブのMCPサーバーを活用することで実装コストゼロで同等の機能が得られる。具体的にはMT5バックテスト結果をBigQueryに保存し、Google Cloud MCP経由でClaude Codeから自然言語クエリするアーキテクチャが実現可能。Model ArmorによるプロンプトインジェクションとデータExfil防止も組み込み済みでセキュリティ要件を満たす。

**提案アクション**:
1. GCPアカウントでCloud MCP サーバーを有効化し、Claude Code の `.mcp.json` に `bigquery-mcp` サーバーを追加設定
2. MT5バックテスト結果CSVをBigQueryにアップロードし、「EUR/USDで過去3ヶ月のシャープレシオを教えて」のような自然言語クエリを試験実行
3. P-011で検討していたカスタムFastMCP実装と、Google Cloud MCP（ゼロ実装コスト）をROI・レイテンシ・セキュリティで比較評価してから本番採用を決定

---

## 2026-07-11 提案

### P-151: スキルdescription精度改善 — 「Claudeのために書く」トリガーフレーズ設計

**根拠記事**: 844 (Techsy Claude Skills Tutorial), 852 (スキルおすすめ厳選JA)
**詳細**: 844・852の両記事で「モデルはdescriptionフィールドのみをもとにスキル使用を判断する」が強調された。曖昧な説明（例："code review"）では未使用のまま終わり、具体的なフレーズ（例："when the user asks for a plain-English code walkthrough"）で初めて自動トリガーが成功する。bpr_labの`.claude/skills/`内の既存スキルのdescriptionが曖昧な場合、せっかく実装したスキルが一度も発火していない可能性がある。

**提案アクション**:
1. `.claude/skills/` 配下の全SKILL.mdのdescriptionフィールドを監査し、抽象的・1語のものを特定
2. 「when the user requests X」「if the prompt contains Y」等の条件節を明示したdescriptionに書き直す
3. 書き直し後、フレッシュセッションで意図的なプロンプトを送り、自動トリガーを確認

---

### P-152: Claude Agent SDK bypassPermissions + worktreeパターンを日次収集に適用

**根拠記事**: 845 (Omega Claude Agent SDK Deep Dive), 846 (Building Deep Agents SKILL.md)
**詳細**: 845記事でbypassPermissionsモード（`rm -rf /`と`~`を除く全自動承認）とworktree隔離（並列ファイル編集時の干渉防止）が解説された。日次収集エージェントは現状インタラクティブパーミッション確認が発生する設計だが、bypassPermissionsで完全非対話化し、worktreeで並列4ドメイン収集を安全に実行できる。846記事の`settingSources=["project"]` + `allowedTools`に`Skill`明示追加も日次収集スキル化（P-003）に必要な設定。

**提案アクション**:
1. 日次収集スクリプトの起動設定に`bypassPermissions`モードを追加（自動化実行時のみ）
2. 4ドメイン並列収集のworktree分離を設定し、Claude Code Dynamic Workflows（P-042）と組み合わせ
3. `.claude/settings.json`の`settingSources`と`allowedTools`に`Skill`を追加してP-003のスキル化を実現

---

### P-153: CLAUDE.md命令バジェット即時監査 — 200行制限と「6つの無視原因」チェック

**根拠記事**: 853 (Techsy CLAUDE.md Best Practices 9 Rules)
**詳細**: 853記事でフロンティアモデルが信頼性をもって遵守できる命令数の上限が約150〜200であることが定量的に示された。200行超でcontext rotが発生し遵守率が非線形低下する。加えて6つのルール無視原因（長さ・曖昧さ・理由なし・コンテキスト圧縮・矛盾・ファイルパス問題）が明示された。本プロジェクトのCLAUDE.mdが200行を超えている場合、FX取引ルールや収集ルールが静かに無視されている可能性がある。

**提案アクション**:
1. `wc -l CLAUDE.md` で現在の行数を確認し、200行超の場合は即時削減計画を立案
2. 「このルールを削除してもClaudeが間違えるか？」基準で不要ルールを除去
3. 各ルールに「なぜ」の理由節を追加（理由なし = 無視原因の1つ）
4. フレッシュセッションで「CLAUDE.mdを要約して」とClaudeに依頼し、遵守状況を確認

---

### P-154: 中国AIエージェント規制（2026年7月15日施行）のbpr_lab適用範囲確認

**根拠記事**: 848 (Rimonlaw China AI Three Laws July2026)
**詳細**: 2026年7月15日施行の「インテリジェントエージェント実施フレームワーク」（CAC・NDRC・MIIT共同）が「自律的認識・記憶・意思決定・実行能力を持つシステム」を対象とする。日次収集エージェント・FX自動取引エージェントは技術的定義に該当する可能性がある。bpr_labが中国市場でサービス提供する場合や中国ユーザーを持つ場合は届出・適合試験が必要。中国国内での展開がない場合でも、感情AI（人型インタラクション）機能（7/15施行）の要件（2時間使用リマインダー・未成年保護）は将来の機能追加時に参照すべき。

**提案アクション**:
1. bpr_labのターゲット市場が中国を含むか確認し、AIエージェント届出要件の適用範囲を特定
2. 中国向け展開がある場合、CAC届出手続きとセキュリティ評価スケジュールを立案
3. bpr_labのFX自動取引エージェントのコア機能（自律売買判断）が「実施フレームワーク」の敏感分野に該当するか法的見解を確認

---

### P-155: J-space発見への対応 — FX自動取引エージェントの推論透明性向上

**根拠記事**: 854 (RadicalDataScience AI Bulletin July 2026)
**詳細**: Anthropicが2026年7月7日にClaude内部の「J-space」（サイレント推論に使われる隠れた内部作業空間）を発見しOSS解析ツール「J-lens」を公開した。FX自動取引エージェントはClaude Sonnet 5/Opus 4.8が売買シグナルを生成するが、最終出力の裏に存在するJ-space上の推論が外部から不可視であった。J-lensで推論プロセスを監査することで、エージェントが実際にどのような中間ステップを経てシグナルを生成しているか確認できる可能性がある。特にP-025（HITL設計）・P-043（再現性リスク対応）の文脈で、信頼度が低い判断の原因をJ-space分析で特定することが有益。

**提案アクション**:
1. AnthropicのJ-lensリポジトリを確認し、FX自動取引エージェントへの適用可能性を評価
2. テスト環境でJ-lensを実行し、シグナル生成時の内部推論ステップを記録・分析
3. J-space分析の結果をP-043（LLMバージョン固定・リグレッションテスト）の指標に組み込む

---

## 2026-07-12 提案

### P-156: Claude Codeデスクトップ内蔵ブラウザを日次収集フローに活用（7/10新機能）

**根拠記事**: 864 (9to5Mac Claude Code Desktop InApp Browser)
**詳細**: 2026年7月10日にClaude Codeデスクトップアプリに内蔵ブラウザが追加された。Cmd+Shift+B（Mac）で起動し、Claudeがドキュメント・WebページをローカルのDOM直接取得で参照できる。現状の日次収集エージェントはWebSearchとWebFetchを組み合わせているが、内蔵ブラウザを使うことで：①JavaScriptレンダリングが必要なSPAサイトの収集が可能に、②WebFetchで取得できないインタラクティブコンテンツへのアクセスが実現、③外部サービス（xやReddit等）のブラウザ操作型収集が理論的に可能。ただし書き込み操作（ログイン等）にはユーザー承認が必要なため、完全自動化には制限あり。

**提案アクション**:
1. Claude Codeデスクトップ版でCmd+Shift+Bを試し、動作確認
2. WebFetchで取得できなかったサイト（JavaScript依存SPAやCDNキャッシュ問題）に内蔵ブラウザを試験適用
3. 日次収集フローの「WebFetch → 内蔵ブラウザ」フォールバックパターンをSKILL.mdに記載

---

### P-157: 緊急 — Fable 5アクセス本日終了 & Sonnet 5 API破壊的変更への対応

**根拠記事**: 863 (DigitalApplied Fable5 Access Extended July12), 862 (Anthropic Sonnet 5 Official Docs), 865 (ITConnect Fable5+Sonnet5)
**緊急度**: 高（本日2026-07-12がFable 5アクセス最終日）
**詳細**: Claude Fable 5のアクセスが本日（2026-07-12）期限。また Claude Sonnet 5がClaude Codeのデフォルトモデルとして採用されており、以下のAPI破壊的変更がある：①手動extended thinking設定 → 400エラー、②非デフォルトサンプリングパラメータ → 400エラー。FX自動取引（sandbox/FX自動取引/）のコードでこれらを使っている場合、即日修正が必要。Sonnet 5の新価格：入力$2/$10/Mトークン（8/31まで）→$3/$15（9/1〜）。Claude Code上では既にSonnet 5がデフォルト。

**提案アクション**:
1. `grep -r "extended_thinking\|thinking.*enabled\|top_p\|temperature" sandbox/FX自動取引/` でAPI破壊的変更の影響箇所を特定
2. Fable 5を使用していたスクリプト・設定を確認し、Opus 4.8（高精度）またはSonnet 5（コスト効率）への切り替えを即日実施
3. CLAUDE.mdのモデル指定セクションを更新：「デフォルトはSonnet 5（2026-07-12〜）、高精度用途はOpus 4.8」に変更
4. プロモーション価格（$2/$10）は2026-08-31まで。それ以降のコスト影響（+50%）を今月中に試算

---

### P-158: MCP 2026-07-28 RC確定仕様への移行準備 — P-017のアップデート

**根拠記事**: 858 (Uravation MCP Server Build Guide), 859 (AIHeartland MCP Production Agents)
**詳細**: MCP仕様の2026-07-28リリース候補が確定段階に入った。P-017（2026年5月時点の予告）からの主要変更確定内容：①Mcp-MethodとMcp-Nameヘッダーが必須化（SEP-2243）→ ロードバランサー・ゲートウェイでのルーティングが必要、②List/Resourceの結果にttlMs・cacheScopeが追加（SEP-2549）→ キャッシュ戦略の見直しが必要、③Mcp-Session-IdヘッダーとプロトコルレベルセッションIDが廃止（SEP-2567）→ ステートレス化完了・スティッキールーティング不要。FastMCP 3.0はすでにRC仕様対応済み。

**提案アクション**:
1. P-011・P-013で開発予定のカスタムMCPサーバーのヘッダー要件（Mcp-Method/Mcp-Name）を設計に組み込む
2. 既存のMCP設定（.mcp.json）でセッション依存の実装がある場合は7/28前にステートレス対応を実施
3. `uravation.com/media/anthropic-mcp-server-build-tools-resources-prompts-2026/` のTools/Resources/Prompts実装パターンを参照し、RC仕様準拠のサーバーを設計
4. 2026-07-28最終版公開後、14日以内に既存MCPサーバー設定の互換性テストを実施

---

## 2026-07-13 提案

### P-159: 緊急 — MCP SDK stdio transportにRCE脆弱性（全言語SDK・1.5億DL影響、2026年4月開示）

**根拠記事**: 874 (ShareUHack Best MCP Servers 2026)
**緊急度**: 高（既に開示済み・パッチ要否確認が必要）
**詳細**: 2026年4月に、MCP SDKのstdio transportに全言語SDK（Python/TypeScript/Go/Java/Ruby等）に影響するシステムRCE脆弱性が公開された。1億5000万DL超に影響し、MCPサーバーを実行している環境でのリモートコード実行リスクがある。このリポジトリがMCPサーバーを利用している（または開発している）場合、バージョン確認とパッチ適用が必要。

**提案アクション**:
1. `grep -r "mcp\|@modelcontextprotocol" package.json .mcp.json src/` でMCP SDK使用箇所を特定
2. 使用中のMCP SDKバージョンを確認し、脆弱性修正版にアップデート
3. stdioトランスポートを使用しているサーバーを特定し、HTTPSへの切り替えを検討
4. GitHub MCP Server等でトークンスコープを読み取り専用に最小化（防衛的対策）
5. 信頼できないソースのMCPサーバーのインストールを禁止するポリシーをCLAUDE.mdに記載

---

### P-160: 戦略 — MCPに対抗する企業連合プロトコル出現（Google・MS・Salesforce・Snowflake・ServiceNow）

**根拠記事**: 868 (BuildFastWithAI AI News July 13)
**詳細**: 2026年7月13日、Google・Microsoft・Salesforce・Snowflake・ServiceNowがAnthropicのMCPに対抗するAIエージェントバックエンドプロトコルの共同策定に合意した。このリポジトリはMCPに大きく依存（P-011・P-013・P-017・P-158）しており、長期的にはプロトコル選択の戦略的判断が必要になる可能性がある。ただし現時点では新プロトコルの詳細は未公表であり、観察継続が適切。

**提案アクション**:
1. 新プロトコルの仕様・名称・タイムラインを今後の日次収集でトラッキング
2. MCPと新プロトコルの共存可能性（ブリッジ層）の動向を確認
3. 主要ツール（Claude Code・Cursor・GitHub Copilot）の対応状況を注視
4. FX自動取引エージェントのMCP依存部分（P-011・P-013）はモジュール化して切り替えやすくしておく

---

### P-161: CLAUDE.md見直し — WHAT/WHY/HOW 3層構造・300行以下・Progressive Disclosure適用

**根拠記事**: 873 (Buildcamp CLAUDE.md Ultimate Guide)
**詳細**: Buildcampの2026年最新CLAUDE.mdガイドで実証された「WHAT/WHY/HOW 3層構造」と「Progressive Disclosure」戦略は、このリポジトリのCLAUDE.md改善に直接適用できる。核心原則："CLAUDE.mdの悪い1行は全タスクに悪影響を与える"—冗長な記述は削除し300行以下を目指す。タスク固有の詳細は.claude/rules/やskillsへ分散させることで常時ロードコンテキストを削減できる。

**提案アクション**:
1. 現行CLAUDE.mdを監査：全タスクに適用されない命令をリストアップして分離
2. 3層構造（WHAT=技術スタック/WHY=設計理由/HOW=コマンド）に再編
3. ビルド・テストコマンドを先頭セクションに移動（最高ROIセクション）
4. 詳細な仕様・規約を`docs/`に移しリンクで参照（Progressive Disclosure化）
5. CLAUDE.local.md（gitignore対象）を個人設定の保管場所として整備

---

## 2026-07-14 提案

### P-162: Claude Code v2.1.207 セキュリティパッチの即時適用確認 — 同意ダイアログバイパス・シェルインジェクション修正

**根拠記事**: 879 (DevelopersIO: Claude Code v2.1.207 auto mode + security fixes)
**取得日**: 2026-07-14
**緊急度**: 高（セキュリティパッチ対応）
**詳細**: v2.1.207に3件のセキュリティ修正が含まれる。(1)**同意ダイアログバイパス修正**：権限確認UIをプロンプトインジェクション経由でバイパスできる脆弱性を修正。(2)**`${user_config.*}` シェルインジェクション修正**：ユーザー設定値の展開時にシェルコマンドインジェクションが可能だった脆弱性を修正。(3)**ターミナルフリーズ修正**：長時間セッションでターミナルが応答不能になるバグを修正。v2.1.207未満を使用しているbpr_labの環境では、これらの脆弱性にさらされている可能性がある。特にシェルインジェクション問題はFX自動取引スクリプトや日次収集エージェントのユーザー設定に悪意ある値が混入した場合に悪用リスクがある。

**提案アクション**:
1. `claude --version` で現在のバージョンを確認し、v2.1.207未満の場合は即時アップデート（`npm install -g @anthropic-ai/claude-code@latest` または同等のコマンド）
2. アップデート後、`${user_config.*}` 形式の設定値展開を行っているカスタムフック・スクリプトを確認し、外部入力から設定値を受け取る箇所に入力バリデーションを追加
3. P-083（SkillSpector監査）のスコープにv2.1.207修正対象の3脆弱性クラスを追加し、次回セキュリティ監査で確認

---

### P-163: Claude Code auto mode ガバナンスギャップへの対応 — Bedrock/Vertex/Foundry での中央制御非到達問題

**根拠記事**: 886 (DigitalApplied: Claude Code auto mode Bedrock/Vertex/Foundry governance gap)
**取得日**: 2026-07-14
**詳細**: Claude Code v2.1.207でauto modeがBedrock・Vertex AI・Azure Foundry環境でデフォルト有効になったことに伴い、3つのガバナンスギャップが判明した。(1)**`disableAutoMode` の非到達**：中央管理者が設定した`disableAutoMode=true`がクラウドプロバイダー環境に伝播しない。(2)**`"sonnet"`エイリアス問題**：Bedrock/Vertex環境での`"sonnet"`エイリアスが`claude-sonnet-4-5`（auto mode非対応）を指すため、auto modeでも古いモデルが使われ続ける。(3)**`autoMode.environment`設定ミス**：`"$defaults"`エントリを含めずに環境設定を上書きするとAnthropicの内蔵保護が全消去される。bpr_labがBedrock/Vertex/Foundry経由でClaude Codeを利用している場合は即時確認が必要。

**提案アクション**:
1. `.claude/settings.json` の `autoMode.environment` 設定に `"$defaults"` エントリが含まれているか確認し、未記載の場合は先頭に追加（内蔵保護の継承を保証）
2. Bedrock/Vertex AI環境での`"sonnet"`エイリアス実際の解決先を確認し、`claude-sonnet-5`に明示的に書き換える（エイリアス依存を排除）
3. 組織管理環境でBedrock/Vertex/Foundryを使用している場合、`disableAutoMode`の代替制御手段（MDMポリシー・エンドポイント管理）を調査しCLAUDE.mdに記録

---

### P-164: Grok 4.5 ($2/$6/Mtok) のFX自動取引コスト比較対象追加 — Terminal Bench 2.1でFable 5と拮抗

**根拠記事**: 883 (TheDecoder: Grok 4.5 vs Fable 5 vs GPT-5.6 price benchmark)
**取得日**: 2026-07-14
**詳細**: xAI Grok 4.5の詳細ベンチマーク比較により、FX自動取引のLLM選択に影響するデータが揃った。価格: Grok 4.5 $2/$6/Mtok（入力/出力） vs Fable 5 $10/$50/Mtok（5倍差）。Terminal Bench 2.1: Grok 83.3% vs Fable 5 84.3%（差わずか1pt）。DeepSWE 1.1（コーディング重視）: Fable 5 70% vs Grok 53%（コーディングはFable 5が有意差）。トークン効率: Grok 4.5 1.9Mトークン/タスク vs Fable 5 7.2Mトークン/タスク（Grokが約4倍効率的）。重大懸念: ハルシネーション率54%（非常に高い）。FX自動取引への示唆: 非コーディング推論タスク（市場センチメント分析・ニュースフィルタリング）ではGrok 4.5がFable 5の1/5コストで同等性能の可能性があるが、ハルシネーション率が致命的なリスク。P-114（Claude BUY/SELL拒否）・P-118（LLM単体FX取引の限界）・P-143（Sonnet 5採用）に続くモデル選択の更新。

**提案アクション**:
1. sandbox/FX自動取引/ のLLMベンチマーク設定にGrok 4.5（xAI API経由）を追加し、Sonnet 5（P-143）・GPT-5.6 Terra（P-145）と同一テストケースで評価（ただし最初はハルシネーション率測定を優先）
2. P-114の教訓（Claudeの直接BUY/SELL拒否）をGrok 4.5でも確認し、FX取引シグナル生成のプロンプト適合性を評価
3. ハルシネーション率54%を前提とした「ファクトチェックレイヤー」を設計——Grok 4.5のシグナルを別モデル（Sonnet 5/ルールベース）でクロスチェックするバリデーション層を追加してから実用を検討

---

## 2026-07-15 提案

### P-165: Claude Sonnet 5 への移行検討 — 日次収集エージェントのLLMアップグレード

**根拠記事**: 894 (Kojima LLM最新モデル比較 2026年7月版)
**取得日**: 2026-07-15
**詳細**: 2026年7月時点でClaude Sonnet 5がAnthropicの最新エージェント特化モデルとして公開された。Opus 4.8近似の性能をより低コストで提供し、ブラウザ・ターミナルの自律操作をネイティブサポート。現在のbpr_lab日次収集エージェント（claude-sonnet-4-6で稼働）はSonnet 5への移行でWebSearch・WebFetch・Bash呼び出しチェーンの精度向上とコスト削減の両立が期待できる。P-143（FX自動取引へのSonnet 5採用）と連携して、全bpr_labエージェントのモデル基盤をSonnet 5に統一する方針を検討するタイミング。

**提案アクション**:
1. 現在の日次収集エージェント（Routinesで動作中）のモデル設定を`claude-sonnet-5`に変更し、次回実行で収集品質・所要時間・トークン消費量を計測
2. P-157で確認した「Sonnet 5 API破壊的変更3件（temperature削除/budget_tokens廃止/Adaptive Thinkingデフォルト化）」がRoutinesスクリプトに影響しないことを確認
3. claude-sonnet-4-6との比較: 同一日の収集クエリ（4ドメイン）でA/Bテストを実施し、SIGNAL率・重複検出率・要約品質を評価

---

### P-166: EU AI Act Digital Omnibus延期を踏まえたFX自動取引コンプライアンスタイムライン再確認

**根拠記事**: 893 (MorganLewis: EU AI Act Digital Omnibus延期、2026年6月16日欧州議会最終承認)
**取得日**: 2026-07-15
**詳細**: 欧州議会が2026年6月16日にEU AI Actの高リスク義務に関する「Digital Omnibus」改正を最終承認した。用途ベース高リスクAIシステム（use-based high-risk systems）および製品規制高リスクAIシステムの当初期限が追加延期された。P-035（FX自動取引のColorado AI法・EU AI Act対応）が前提としていたタイムラインが変わっている可能性がある。sandbox/FX自動取引/はまだ開発・検証段階だが、将来的な本番運用を見据えた場合、延期後の新しい期限（2026年8月2日以降の段階的施行）を再確認する必要がある。

**提案アクション**:
1. sandbox/FX自動取引/のシステムが「use-based high-risk AIシステム」（自動意思決定による重要な影響）として分類されるか、Digital Omnibus後の最新ガイダンスで再評価
2. P-035のアクション項目（Colorado AI法ADMT確認・README規制注記）を現時点の分類確認後に実施するタイムラインを設定
3. MorganLewis記事を参照して、延期後の新しい適合性評価期限と技術文書要件の準備開始タイミングをCLAUDE.md（.claude/rules/fx-trading.md）に記録

---

## 2026-07-16 提案

### P-167: MetaTrader 5 Build 5955のMCP公式サポートを即時評価 — FX自動取引の直接アップグレード機会

**根拠記事**: 3000 (MetaTrader 5 Beta Build 5955: MCP・AIエージェントのネイティブサポート開始)
**取得日**: 2026-07-16
**詳細**: 本日（2026-07-16）MetaQuotesがMT5 Beta Build 5955を公開。Model Context Protocol（MCP）とAIエージェントのビルトインサポートが追加された。これまでsandbox/FX自動取引/ではコミュニティ製mcp-metatrader5-server（Qoyyuum/ariadng版）で回避策を使っていたが、公式実装により信頼性・安定性が向上する可能性がある。Webull・Deriv・IG・eToro等の主要ブローカーも既にMCP統合を進めており、業界全体のトレンドが確認できた。Claude Sonnet 5/Fable 5を直接MT5に接続するワークフロー設計が現実的なフェーズに入った。

**提案アクション**:
1. sandbox/FX自動取引/ の環境でMT5 Beta Build 5955をインストールし、MCP公式サポートの動作確認を実施（VPS（ConoHa）のMT5を更新）
2. 既存のmcp-metatrader5-server（コミュニティ版）と公式MCP実装の機能差・安定性を比較評価
3. Claude Sonnet 5 + MT5公式MCPによる「シグナル生成→注文発注」の統合ワークフローのプロトタイプを設計し、sandbox/FX自動取引/のSTATUS.mdに記録

---

### P-168: EU AI Act高リスク義務延期の一次情報確認 — P-166タイムライン更新

**根拠記事**: 3004 (EU Council: AIルール簡素化・合理化に最終承認 2026-06-29)
**取得日**: 2026-07-16
**詳細**: P-166（2026-07-15、MorganLewis記事起点）でEU AI Act高リスク義務の延期を把握していたが、EU Council公式プレスリリース（2026-06-29）で一次情報として確認できた。スタンドアローン型高リスクAI：2027年12月2日、製品組み込み型：2028年8月2日に延期。P-166のアクション（sandbox/FX自動取引/のシステム分類再評価）の期限余裕が公式に確認されたことで、2027年Q4まで設計検討の時間が増えた。ただし欧州市場展開を想定する場合は準備開始時期を逸しないよう注意。

**提案アクション**:
1. P-166 アクション項目3（.claude/rules/fx-trading.mdへの記録）に「公式確認：EU Council 2026-06-29、延期後期限：スタンドアローン2027-12-02 / 製品組込み2028-08-02」を追記
2. 現時点でFX自動取引システムの適用範囲（EU市場・日本市場）を確認し、規制対象外であれば設計フェーズで対応を開始

---

### P-169: LLMトレーディングは「監督下のリサーチアシスタント」が現実的上限 — arXivベンチマーク（KTD）からの設計指針

**根拠記事**: 2999 (LLMトレーディングエージェントのメモリ制御ベンチマーク arxiv 2605.28359)
**取得日**: 2026-07-16
**詳細**: 2026年5月のarXiv論文（CSI300で10フロンティアLLMを2024-2026に評価）の結論：累積リターンの大部分は受動的な市場・スタイル露出で説明でき、LLMの株式選択アルファの持続的証拠は限定的。マルチエージェントフレームワークはアナリティクス精度を改善するが「完全自律の意思決定者ではなく監督下のリサーチアシスタント」が現実的限界。これはP-118（LLM単体FX取引の限界）の見解と一致し、学術的なエビデンスが追加された形。sandbox/FX自動取引/の設計原則「人間の最終判断を残す」が正しい方向性であることが裏付けられた。

**提案アクション**:
1. sandbox/FX自動取引/のSTATUS.mdに「LLM役割の設計原則：完全自律判断ではなくシグナル生成→人間or確定ルールによる実行判断」をアーキテクチャ原則として明記
2. arXiv論文（arxiv.org/abs/2605.28359）を参照資料としてFX自動取引のdocs/に保存
3. KTDベンチマークの評価指標（累積リターン・シャープレシオ・最大ドローダウン）をsandbox/FX自動取引/のバックテスト指標として採用することを検討

---

## 2026-07-18 提案

### P-170: MCP 2026-07-28 仕様最終版リリースに向けた移行準備 — ステートレス化対応

**根拠記事**: 3006 (MCP 2026-07-28 仕様RC：ステートレス化・拡張フレームワーク導入)
**取得日**: 2026-07-18
**詳細**: MCPプロトコルの2026最大の改訂最終版が7月28日にリリース予定。最大変更点はステートレス化（SEP-2575/SEP-2567）：initialize/initializedハンドシェイクとMcp-Session-Idヘッダの廃止。タスクマネージャー内でMCPサーバーを自作・利用している場合、仕様変更への対応が必要になる。sandbox/FX自動取引/ のMT5 MCPサーバー連携（P-167で評価中）においても、公式MT5 MCP実装が新仕様に対応するか確認が必要。

**提案アクション**:
1. タスクマネージャーの .claude/ 配下でMCPサーバーを参照しているすべての .mcp.json を確認し、7/28以降の仕様変更影響範囲を把握
2. sandbox/FX自動取引/ で利用中/評価中のMT5 MCPサーバー（コミュニティ版・公式版）が新仕様に対応するかリリースノートを7/28以降に確認
3. 自作MCPサーバーがある場合、ステートレス化（セッションIDなし・ハンドシェイクなし）への移行テストを10週間移行ウィンドウ内で実施

---

### P-171: Claude Code Artifacts β の日次収集ルーチン成果物への適用評価

**根拠記事**: 3007 (Claude Code Week 29：Artifacts β・3段ネスト・/cd・Voice Mode)
**取得日**: 2026-07-18
**詳細**: Claude Code Week 29でArtifacts βが追加された。セッション成果物をclaude.ai上のライブ共有ページとして公開・インプレース更新できる機能。タスクマネージャーの日次収集ルーチンが生成するダイジェスト・目録は現在ファイルとして保存されているが、Artifactsを使えばスマートフォンから直接閲覧可能な共有ページとして提供できる。週次ダイジェスト（digestスキル）の出力をArtifacts化することで、PCなしでのモバイル閲覧体験が改善される。

**提案アクション**:
1. digestスキルの出力形式にArtifacts公開オプションを追加することを検討（--publish フラグ等）
2. 日次収集ルーチンの最終成果物（カタログ更新確認・新規SIGNAL件数）をArtifactsで要約ページとして自動生成する機能を評価
3. claude.ai Artifacts βの制約（非公開デフォルト・CSP等）を確認し、ダイジェスト共有に適したフォーマットを設計

---

### P-172: TradingAgents v0.2.4 + Claude Sonnet 4.6 の FX シグナル生成評価

**根拠記事**: 3017 (LLMトレーディングBot比較：マルチエージェント手法・結果・リスク・FlowHunt)
**取得日**: 2026-07-18
**詳細**: FlowHuntの比較記事でClaude Sonnet 4.6を用いたTradingAgentsでSharpe Ratio 1.94・487%リターンという報告が挙がった。TradingAgents v0.2.4は現在GPT-5.x/Gemini 3.x/Claude 4.x/Grok 4.xをマルチプロバイダ対応。ただし報告は単一実験で独立検証未済。P-169（LLMは監督下リサーチアシスタント）の設計原則は維持しつつ、シグナル生成レイヤーでの活用可能性を評価する価値がある。

**提案アクション**:
1. TradingAgents v0.2.4をsandbox/FX自動取引/ の検証環境に導入し、Claude Sonnet 4.6でのFXシグナル生成（テクニカル+センチメント分析）をバックテストで評価
2. Sharpe Ratio 1.94の報告元記事を特定し、バックテスト期間・データソース・スリッページ設定等の条件を確認
3. TradingAgentsのマルチエージェント構成（基礎/センチメント/テクニカル/リスク管理/トレーダー）とP-167（MT5 MCP公式統合）を組み合わせた将来アーキテクチャをSTATUS.mdに追記

---

## 2026-07-19 提案

### P-173: MCP 2026-07-28 最終仕様リリース直前確認（P-170の続報）

**根拠記事**: 3027 (InfoQ-MCP EMA Stable)、3028 (HackerNoon-MCP Stateless Scaling)
**取得日**: 2026-07-19
**詳細**: MCP 2026-07-28最終仕様が9日後（2026-07-28）にリリース予定。P-170（2026-07-18提案）で挙げたステートレス化対応に加え、Enterprise-Managed Authorisation（EMA）のStable昇格が確認された。自作MCPサーバー利用者は10週間の移行ウィンドウ内で対応が必要。特にsandbox/タスクマネージャー/.claude/ の.mcp.json設定とsandbox/FX自動取引/のMT5 MCP連携が影響を受ける可能性がある。

**提案アクション**:
1. 2026-07-28以降に公式MCPドキュメント（blog.modelcontextprotocol.io）を確認し、Breaking Changes一覧をdocs/に記録
2. EMAを利用しない個人開発用途では影響が少ないが、ステートレス化による既存MCPツールの動作変化を確認（特にmcp__github__等のMCPツール）
3. HackerNoon記事（3028）のBreaking Changes解説をFX自動取引/docs/に参照保存

### P-174: Claude Code 日本語活用の定量データを CLAUDE.md に反映

**根拠記事**: 3024 (ClaudeDojo Japan Cases)、3029 (GenAI-co-jp Japanese Guide)
**取得日**: 2026-07-19
**詳細**: 日本企業20社の事例で、Claude Code活用による生産性改善が定量化された（手順書見直し3倍速、サポート業務67%削減、チャーン率1.4→2.3%改善など）。Claude Sonnet 4.6・Opus 4.6の日本語ビジネス文書品質が特に高く評価されている。bpr_lab各プロジェクトのCLAUDE.mdに「想定モデル: Claude Sonnet 4.6（日本語業務文書）」を明記することで、セッション初期のモデル選択を最適化できる。

**提案アクション**:
1. sandbox/タスクマネージャー/CLAUDE.md の「モデル使い分け」セクションに、日本語文書生成にSonnet 4.6を推奨する記述を追加
2. 日次収集ルーチンの要約生成ステップで明示的に Sonnet 4.6 を指定（現在は継承モデルに依存）
3. sandbox/FX自動取引/ のシグナルレポート日本語生成にSonnet 4.6を採用することを評価

---

### P-175: Claude Code v2.1.214 パーミッションバイパス修正 — 即時アップデート推奨

**根拠記事**: 3033 (Claude-Code-v2-1-214-215-Security-Fixes)
**取得日**: 2026-07-20
**詳細**: Claude Code v2.1.214（2026-07-18リリース）に4件のセキュリティ関連バグ修正が含まれる。重大なものはパーミッションバイパス2件：(1) `Edit(src/**)` などの単一セグメント許可ルールが任意のネストdirへの書き込みを自動承認するバグ（既存の設定が意図せずワイドな許可を与えていた可能性）、(2) Windows PowerShell 5.1セッションでのパーミッションチェックバイパス。bpr_lab環境は Linux なので (2) は直接無影響だが (1) の修正は重要。

**提案アクション**:
1. `claude --version` で現バージョンを確認し、v2.1.214未満の場合は `claude update` で更新
2. プロジェクト `.claude/settings.json` のEdit許可ルール（`Edit(path/**)` 形式）を見直し、最小権限を確認

---

### P-176: Anthropic Memory API beta を タスクマネージャー の永続エージェントメモリに活用検討

**根拠記事**: 3036 (Anthropic-Memory-API-Beta-HIPAA-Config)
**取得日**: 2026-07-20
**詳細**: Anthropicが `agent-memory-2026-07-22` betaヘッダを追加し、エージェントメモリの一覧取得が安定化（サーバー定義の安定順序・depth制限・path_prefix制約）。タスクマネージャーは現在ファイルベース（library/、articles/）でナレッジを管理しているが、Memory APIを活用することで会話を跨いだ半永続的なエージェントメモリの管理が可能になる。特に「alter-ego」や「壁打ちエージェント」など、ユーザーコンテキストを持続的に保持したいユースケースに適合する。

**提案アクション**:
1. AnthropicのMemory API公式ドキュメントを確認し、betaヘッダの具体的な利用方法を調査
2. sandbox/タスクマネージャー/.claude/skills/にmemory-sync スキルの設計を検討（alter-ego.md との連携）
3. FX自動取引シグナル履歴を Memory API で管理するプロトタイプを検討

---

### P-177: EU AI Act 透明性義務ガイドライン（7/20公表）— 8月施行前のコンプライアンスチェック

**根拠記事**: 3034 (EU-AI-Act-Transparency-Guidelines-Official-July20)
**取得日**: 2026-07-20
**詳細**: EU委員会が2026年7月20日（本日）にAI法第50条に基づく透明性義務ガイドラインを正式公表。8月に主要条項が完全施行予定。ai-teamsやFX自動取引システムをEU向けに展開する予定がある場合、このガイドラインの確認が必要。特に生成AIを使ったコンテンツ生成・AI生成コンテンツのラベリング・GPAI（汎用AI）モデルへの透明性要件が課題になる可能性がある。

**提案アクション**:
1. digital-strategy.ec.europa.eu の公表ガイドラインを読み、自身の用途（ai-teams / FX自動取引）が対象に含まれるか確認
2. 対象になる場合、AI生成コンテンツのラベリング方針をdocs/に記録
3. 今後EU向けサービスを開発する際には、透明性義務を設計段階で組み込む

---

### P-178: MCP 2026-07-28 ステートレス仕様移行 — 7月28日前に既存MCPサーバーの影響調査

**根拠記事**: 3039 (DigitalApplied-MCP-Stateless-Migration), 3040 (Stacktree-MCP-2026-Spec-Changes)
**取得日**: 2026-07-21
**詳細**: MCP 2026-07-28仕様RCが7月28日に正式リリース予定。最大の変更はステートレスコアへの移行（セッション管理API廃止、旧認証フロー廃止、JSON Schema 2020-12による厳密なパラメータ検証）。タスクマネージャーのスキル群やFX自動取引で利用中のMCPサーバー（MetaTrader MCP等）が影響を受ける可能性がある。7月27日までに確認・対応が必要。

**提案アクション**:
1. `sandbox/タスクマネージャー/.claude/` および `sandbox/FX自動取引/` 配下のMCP設定を確認し、セッション管理に依存している箇所を洗い出す
2. blog.modelcontextprotocol.io の正式移行ガイドを参照し、breaking changesへの対応方針を決定
3. 影響があれば7/28前にMCPサーバー側コードを更新し、JSON Schema対応を確認

---

### P-179: Kimi K3（2.8兆パラメータ・オープンウェイト）をFX自動取引エージェントの代替LLMとして検討

**根拠記事**: 3044 (KimiK3-Beats-Fable-GPT), 3045 (CNBC-MoonshotAI-KimiK3)
**取得日**: 2026-07-21
**詳細**: Moonshot AIのKimi K3がFrontierSWEスコア77.8（世界1位）を達成し、GPT-5.6 Sol・Claude Fable 5を上回るSWEベンチマークを示した。価格はGPT-5.6 Solの約1/3で、1Mトークンコンテキストウィンドウを持つ。FX自動取引エージェントのLLM推論コスト削減のため、分析・判断レイヤーにKimi K3 APIを試験導入する価値がある。フルウェイト公開は7月27日予定。

**提案アクション**:
1. Kimi K3 APIの料金体系と利用上限を確認（platform.moonshot.cn）
2. sandbox/FX自動取引/ の推論LLM設定を確認し、Kimi K3に切り替えるA/Bテスト設計を検討
3. MT5のシグナル分析（マルチタイムフレーム・OHLCV解析）にKimi K3のネイティブビジョンを活用する実験を計画

---

### P-180: 米国AI規制加速（Illinois AI Safety Act + CISA Agentic AI Guidelines）— FX取引AIへの影響確認

**根拠記事**: 3047 (WTTW-Illinois-AI-Safety), 3048 (Gunder-AI-Laws-2026), 3049 (TechPolicy-State-AI-Legislation)
**取得日**: 2026-07-21
**詳細**: イリノイ州が2026年7月6日にAI Safety Measures Act（米国最包括的水準）に署名。同時期にDHS-CISAがアジェンティックAI向けプロンプトインジェクション対策義務化・ヒューマンオーバーライド文書化を提言。FX自動取引システムは「critical infrastructure」の金融セクターにあたる可能性があり、特にヒューマンオーバーライド機能（手動停止・介入ログ）の実装状況を確認すべき。

**提案アクション**:
1. sandbox/FX自動取引/ のシステム設計を確認し、緊急停止・手動介入・オーバーライドログの実装状況を文書化（docs/compliance.md）
2. プロンプトインジェクション対策（入力バリデーション・サニタイズ）の実装状況をセキュリティレビュー
3. 米国向けサービス展開を計画する場合、Gunderson Dettmerのコンプライアンスチェックリスト（P-180根拠記事）を参照

---

### P-181: Verification Loops with Skills — bpr_lab 収集ルーティンの品質検証スキル追加

**根拠記事**: 3053 (ClaudeCode-Verification-Loops-Skills-Official-Blog)
**取得日**: 2026-07-22
**詳細**: Anthropic公式ブログ（7/22）がVerification Loop as Skillパターンを公開。4パターン（スタンドアロン・埋め込み・チェーン・PR全体）のうち、bpr_labの日次収集ルーティンに「埋め込み型」検証スキルを追加することで、収集→キュレーション→コミットの品質を自動チェックできる。例：「重複URL検出 → 存在すれば除外」「catalog更新漏れ検知」「articles/ファイル形式の整合性チェック」等。

**提案アクション**:
1. `sandbox/タスクマネージャー/.claude/skills/` に `verify-library-integrity.md` スキルを作成
2. 日次収集ルーティンのStep 4に埋め込んでカタログ整合性を自動検証
3. 既存スキル（curate, digest等）にこのVerification Loopを組み込んでチェーン化

---

### P-182: Anthropic AI-native SDL セキュリティ実践 → CLAUDE.md・スキルへのセキュリティガイダンス埋め込み

**根拠記事**: 3057 (Anthropic-AI-Native-SDL-Security-Practices)
**取得日**: 2026-07-22
**詳細**: Anthropic Deputy CISO が、Claudeがコードの80%を生成する環境でのSDLCセキュリティ実践を公開。特に「CLAUDE.md・スキルへのセキュリティガイダンス埋め込み」「/security-reviewコマンドの統合」「egress制限リモートVM」等が実践可能。FX自動取引や他のbpr_labプロジェクトにも応用できる。

**提案アクション**:
1. `sandbox/FX自動取引/.claude/CLAUDE.md` にセキュリティガイダンスセクションを追加（API keyの扱い・外部通信先ホワイトリスト・ログ記録ルール）
2. `/security-review` スキルをタスクマネージャーの `.claude/skills/` に作成して attacker-controllable input の検出を自動化
3. MITRE ATT&CK ベースのリスク分類をFX自動取引のシステム設計レビューに導入

---

### P-183: Claude Cowork「Record a Skill」→ FX自動取引操作ルーティンのスキル化

**根拠記事**: 3054 (Claude-Cowork-Record-Skill-Screen-Recording)
**取得日**: 2026-07-22
**詳細**: Anthropicが7/21リリースした「Record a Skill」機能で、画面録画＋音声ナレーション一度で繰り返しタスクをスキルに変換可能。FX自動取引の MT5操作（レポート確認・ポジション手動調整・VPS設定変更等）をスキル化することで、次回から音声指示だけで実行できる可能性がある。

**提案アクション**:
1. Claude Cowork（Pro/Max/Team）がアクセスできる環境で「Record a Skill」機能を試用
2. MT5 VPS上の定期確認作業（ポジション確認・ログ確認・パラメータ更新）を録画してスキル化を検討
3. bpr_labの日常的な繰り返し作業（STATUS.md更新・特定フォルダ構造確認等）をスキルとして記録

---

### P-184: Gemini 3.6 Flash（$1.50/$7.50/M）→ FX自動取引の低コスト推論層として検討

**根拠記事**: 3052 (Google-Gemini-3-6-Flash-Launch-July21), 3055 (BuildFastWithAI-AI-News-July22)
**取得日**: 2026-07-22
**詳細**: Google Gemini 3.6 Flashが$1.50/$7.50/Mトークンで、出力コスト17%削減・DeepSWEコーディングスコア+32%・知識カットオフ2026年3月。FX自動取引のシグナル分析（日次・週次サマリーを小さなコンテキストで処理する場面）への適用で推論コストを削減できる可能性がある。Claude Fable 5（$10/$50）との価格差は6〜7倍。

**提案アクション**:
1. sandbox/FX自動取引/ の推論コスト計測（現在どのモデルを何トークン使っているか）
2. サマリー生成・日次判断等のルーティンタスクをGemini 3.6 Flash APIで試験実行してコスト比較
3. Gemini API キー取得と既存Anthropic SDK呼び出しの抽象化レイヤー確認

---

### P-185: Claude + MT5 via MCP アーキテクチャパターン → FX自動取引プロジェクトへの直接適用

**根拠記事**: 3060 (FXNX-Claude-MT5-via-MCP-Advanced-AI-Trading-Setup)
**取得日**: 2026-07-23
**詳細**: FXNXが公開した「Claude API + MCP（MetaTrader Connect Proxy） + MT5」の3層アーキテクチャが、bpr_labのFX自動取引プロジェクトに直接適用できる設計パターン。MCP側のEA（Expert Advisor）をMT5に組み込んでPythonクライアントライブラリ経由でClaude APIに接続し、データ取得→LLM判断→注文実行のパイプラインを構築する。ニュースセンチメント・テクニカル・ファンダメンタル分析の同時処理が可能。APIレイテンシからH1以上のタイムフレームが最適。

**提案アクション**:
1. `sandbox/FX自動取引/` でのClaude API統合設計にMCPブリッジパターンを採用
2. ポジションサイジング上限のハードコード・全プロンプト/レスポンスロギング・デモ口座先行テストを安全策として実装仕様に明記
3. 参照実装としてFXNX記事のPythonパイプライン構成を `docs/reference_architecture.md` に記録

---

### P-186: 中国AIエージェント3層規制フレームワーク → FX自動取引エージェント設計への規制準拠考慮

**根拠記事**: 3062 (MachineBrief-China-AI-Agent-Regs-July15-3Tier-Framework)
**取得日**: 2026-07-23
**詳細**: 2026年7月15日施行の中国AIエージェント規制（世界初）が確立した3層フレームワーク（Level 1自律可/Level 2人間承認必須/Level 3禁止）は、FX自動取引エージェントの設計指針として参照価値がある。EU AI Actも8月2日に完全施行されるため、将来的な日本・EU・中国でのシステム展開を見据えた設計が重要。特に「契約・価格設定等の重要決定に人間承認を挟む」Level 2相当の設計は、FX自動取引のリスク管理層として有用。

**提案アクション**:
1. FX自動取引の取引判断フローを3層で整理（小ポジション=自律可/大ポジション=アラート通知/緊急停止=人間操作必須）
2. `sandbox/FX自動取引/docs/` に規制準拠設計メモを追加（中国・EU AI Act・日本ガイドラインの対応状況）
3. EU AI Act August 2 施行前に、FX自動取引がハイリスクAIシステムとして登録義務の対象かを確認

---

### P-187: Kimi K3 オープンウェイト（7/27公開）→ FX自動取引ローカル推論層の代替候補として評価

**根拠記事**: 3066 (Kimi-Blog-K3), 3067 (Interconnects-Kimi-K3-Open-Weights-Escalation)
**取得日**: 2026-07-24
**詳細**: Moonshot AIのKimi K3（2.8Tパラメータ、Modified MIT、MXFP4量子化）が7月27日にHugging Faceで公開予定。フロンティアスケールでありながらオープンウェイトのため、VPS環境へのデプロイや推論コスト削減に活用可能。コーディング・数学・マルチモーダル推論でグローバル4位。FX自動取引のシグナル分析・バックテスト評価にClaude APIの代替として使える可能性がある（ただしVPS GPU要件確認が必要）。

**提案アクション**:
1. 7月27日のKimi K3重みリリース後、HuggingFaceから定量的ベンチマーク（コーディング・数学）を確認
2. ConoHa VPS のGPUスペック確認 → MXFP4量子化版の実行可否を評価
3. FX自動取引の推論コスト計測と、Kimi K3ローカル推論（または低コストAPI）との比較試算

---

### P-188: Claude Opus 4.7 Fast Mode 廃止（本日7/24）→ bpr_lab設定の移行確認

**根拠記事**: releasebot.io Anthropic Platform update（WebSearch取得）
**取得日**: 2026-07-24
**詳細**: Claude Opus 4.7 の Fast Mode が本日（2026年7月24日）廃止。Opus 4.8 Fast Modeへの移行が推奨されている。bpr_lab/sandbox配下のスクリプトやClaude設定でOpus 4.7を明示指定している箇所が存在する場合は即時更新が必要。スケジュールタスク・Claude Code設定・FX自動取引スクリプトのモデルIDを確認すること。

**提案アクション**:
1. `grep -r "claude-opus-4-7\|opus-4\.7" /home/user/bpr_lab/` でハードコードされたモデルID検索
2. `.claude/settings.json` / `settings.local.json` のモデル設定確認
3. FX自動取引スクリプト（sandbox/FX自動取引/src/）のモデルID確認と更新

---

### P-189: EU AI Act 8月2日施行まで9日 → 緊急：対応状況の最終確認

**根拠記事**: 3068 (Judicio-Legal-AI-News-July2026-EU-China-Singapore)
**取得日**: 2026-07-24
**詳細**: EU AI Act が8月2日（9日後）に完全施行。高リスクAIシステムへのリスク管理・データガバナンス・技術文書・人間監視・サイバーセキュリティ義務が適用開始。違反時の制裁：最大€35M または全世界売上の7%。bpr_labの FX自動取引・ai-teams（AI Council）等がEU向けサービスに分類されるかを今週中に判断することを推奨。P-186の提案（3層設計）と合わせて緊急度が高い。

**提案アクション**:
1. FX自動取引・ai-teams のユーザー対象地域確認（EU居住者向けかどうか）
2. 高リスクAI分類の自己評価（金融判断補助ツールはAnnex III対象の可能性あり）
3. 必要であれば技術文書・人間監視手順書の最低限ドラフトを作成

---

### P-190: TradingAgents v0.3.1 Claude Sonnet 5対応 → FX自動取引LLMバックエンドのアップグレード検討

**根拠記事**: 3083 (GPTrader-Best-Open-Source-AI-Trading-Agents-GitHub-2026), 3084 (PickMyTrade-Build-MultiAgent-Trading-System-TradingAgents-2026)
**取得日**: 2026-07-25
**詳細**: TradingAgents（GitHub 80K stars、Apache 2.0）の最新版v0.3.1（2026年7月リリース）がClaude Sonnet 5をサポート。従来のClaude Sonnet 4.x系より推論能力・コーディング精度が向上したClaude Sonnet 5を取引判断層に適用することで、マルチエージェント取引システムの意思決定品質が改善できる可能性。bpr_lab/sandbox/FX自動取引のLLMバックエンド設定を確認し、Sonnet 5への移行を検討すること。

**提案アクション**:
1. `sandbox/FX自動取引/src/` のモデルID設定を確認（`claude-sonnet-4` → `claude-sonnet-5`）
2. TradingAgents v0.3.1のリリースノートで破壊的変更がないか確認
3. ConoHa VPS上のテスト環境でSonnet 5への切り替えをバックテストで検証

---

### P-191: Claude Code サブエージェントスポーン深度のデフォルト変更 → 日次収集タスク設定確認

**根拠記事**: 3071 (SitePoint-Claude-Code-June2026-10-New-Features), 3074 (MeanCEO-Claude-Code-News-July2026)
**取得日**: 2026-07-25
**詳細**: Claude Code July 2026（7/20リリース）より、サブエージェントがデフォルトで入れ子サブエージェントを生成しなくなった。深いネストが必要な場合は `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` 環境変数を設定する必要がある。bpr_lab/sandbox/タスクマネージャーの日次収集スケジュールタスクや、curate スキルがサブエージェントを使う設計になっている場合、この変更の影響を受ける可能性がある。

**提案アクション**:
1. `.claude/settings.json` に `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=3`（または必要な深度）を追加
2. 日次収集スケジュールタスクが正常に動作しているか次回実行後にログ確認
3. curate / daily-collect-and-curate スキルのサブエージェント呼び出し箇所を確認

---

## 2026-07-26 収集分

### 1. FX自動取引 MCPサーバー緊急移行提案

**出典:** articles/2026-07-26_3089_WEB_MCP-2026-07-28-RC-Official-Blog-Stateless-Final.md / articles/2026-07-26_3091_WEB_LukeOliff-MCP-Goes-Stateless-Monday-Break-Fix.md

**緊急度: 高（2026-07-28 = 2日後に仕様変更発効）**

**提案内容:**
MCP 2026-07-28仕様でプロトコルがステートレス化される。`sandbox/FX自動取引/` の MCPサーバー連携コード（Claude+MT5 via MCP）が影響を受ける可能性がある。

具体的な変更点:
- `initialize` ハンドシェイクと `Mcp-Session-Id` ヘッダーが削除
- 各リクエストに `_meta.protocolVersion` と `_meta.clientInfo` フィールドが必要に
- エラーコード -32002 → -32602 に変更

**提案アクション:**
1. `sandbox/FX自動取引/src/` のMCP関連コードを確認し、initialize ハンドシェイクに依存している箇所を特定
2. Anthropic SDK（Python版）が2026-07-28以降のアップデートを出したらすぐに適用
3. MT5 MCP Serverのバージョン（GitHub: ariadng/metatrader-mcp-server）が新仕様対応しているか確認
4. 移行コードサンプルは articles/2026-07-26_3091_WEB_LukeOliff-MCP-Goes-Stateless-Monday-Break-Fix.md 参照

### 2. Claude Code スキル見直し提案

**出典:** articles/2026-07-26_3093_WEB_Libecity-Claude-Code-Recommended-Skills-10-JA.md

**提案内容:**
2026年7月時点のスキルランキングとして Context7（最新ドキュメント参照）・Code Review（PR自動化）・Code Simplifier が上位推奨。タスクマネージャーの `.claude/skills/` に不足しているものがあれば追加検討する。

**提案アクション:**
1. `sandbox/タスクマネージャー/.claude/skills/` の現在のスキル一覧と上記推奨10選を比較
2. Context7 プラグインが実務で有用か検討（最新ライブラリドキュメントのリアルタイム参照）

---

## 2026-07-27 収集分

### 1. 【明日発効】MCP 2026-07-28 ステートレス化 最終確認

**出典:** articles/2026-07-27_3100_WEB_TechCrunch-MCP-Easier-Stateless-July20-2026.md / articles/2026-07-27_3101_WEB_TheRegister-MCP-Stateless-Break-Past-July23-2026.md

**緊急度: 最高（2026-07-28 = 明日に仕様変更発効）**

**提案内容:**
2026-07-26収集分で提案済みのMCP移行対応が「明日」に迫った。
The Register（7/23）の技術分析によると、移行で注意が必要な破壊的変更:
- Completions/Roots/Sampling の3プリミティブが非推奨化（deprecated、削除ではないが将来削除される）
- エラーコード -32002 → -32602 変更（クライアント側のパターンマッチコードが壊れる）
- TypeScript/Python公式SDKはすでにRC対応版をリリース済み

**今日中に確認すべきアクション:**
1. `sandbox/FX自動取引/` のMCP連携コードが `Completions`/`Roots` を使っていないか確認
2. Anthropic Python SDKのバージョンを最新に更新（`pip install --upgrade anthropic`）
3. 移行後も問題なければ対応完了

### 2. Anthropic API レート制限 3段階統一（Start/Build/Scale）への対応

**出典:** articles/2026-07-27_3103_WEB_Anthropic-API-Rate-Limits-Unified-Start-Build-Scale-June2026.md

**緊急度: 低（対応不要だが把握しておく）**

**提案内容:**
2026年6月26日から、AnthropicのAPIレート制限が4→3段階（Start・Build・Scale）に再編され、全モデルのレート制限が統一された。特に入力トークン/分が約16倍増（30,000→500,000）。FX自動取引のAPIコールがボトルネックだった場合は大幅改善が期待できる。

**提案アクション:**
1. Claude Consoleで現在のティア確認（Start/Build/Scaleのどれか）
2. FX自動取引のAPI使用量ログを確認し、429エラーが発生していた場合は再テスト
3. Fast mode for Opus 4.7は7/24に廃止済み → `claude-opus-4-7` + `speed: "fast"` を使っているコードがあれば修正必要

### 3. CLAUDE.md プロジェクト規模別設計パターン導入検討

**出典:** articles/2026-07-27_3099_WEB_Start-Link-CLAUDE-md-Design-Patterns-Scale-Guide-JA.md

**提案内容:**
bpr_labのCLAUDE.mdは現在単一ファイル構成。プロジェクト数が30個以上に達したため、`@import`や`.claude/rules/`を活用したサブプロジェクト別設計への移行を検討する。現状でも「sandbox/タスクマネージャー」「sandbox/FX自動取引」各CLAUDE.mdは機能しているが、ルートCLAUDE.mdが肥大化しやすい構造になっている。

**提案アクション:**
1. ルートCLAUDE.mdの行数を確認（200行超なら分割検討）
2. 高頻度使用ルールと低頻度ルールを分離し、`.claude/rules/`での条件付き読み込みを試験導入

---

### 2026-07-28: MCP 2026-07-28仕様 破壊的変更への対応

**出典:** articles/2026-07-28_3107_WEB_MCP-2026-07-28-Spec-Final-Bringing-Stateless-to-Claude.md / articles/2026-07-28_3108_WEB_MCP-Beta-SDKs-2026-07-28-Python-TS-Go-Csharp.md

**緊急度: 高（本日付けで仕様が正式リリース・Claudeが新仕様を採用）**

**提案内容:**
MCP 2026-07-28仕様が本日正式リリース。Claude Codeは本日付けで新仕様をサポート開始。主な破壊的変更：①ステートレスコア（initializeハンドシェイク廃止・Mcp-Session-Id廃止）②tasks/list削除③エラーコード-32002→-32602変更④Roots/Sampling/Logging非推奨。既存のMCPサーバー実装は新仕様に非互換。

**提案アクション:**
1. sandbox/FX自動取引 でMCPサーバーを使用しているか確認（MT5 MCP連携の実装状況）
2. sandbox/タスクマネージャー の `.claude/` に登録されたMCPサーバーが旧仕様の場合は更新が必要
3. Python/TypeScript SDK ベータを確認し、既存コードのマイグレーション対象ファイルを特定
4. Claude Code のMCP設定ファイル（`.claude/settings.json` 等）でMcp-Session-Idを使用している場合は削除

---

### 2026-07-29: CLAUDE.md 200行制限の定量的根拠（モデル精度低下データ）

**出典:** articles/2026-07-29_3112_WEB_OpenHands-Claude-Code-Best-Practices-Agentic-Coding-2026.md

**提案内容:**
OpenHandsの実測で「18種類のフロンティアモデルを検証した結果、CLAUDE.md等の入力が一定行数を超えると精度が95%→60%に低下するモデルが存在する」ことが確認された。200行以内に収めることの根拠として定量データが得られた。

**提案アクション:**
1. bpr_lab ルート CLAUDE.md の現在の行数確認（`wc -l CLAUDE.md`）
2. sandbox/タスクマネージャー/CLAUDE.md の行数確認
3. 200行超の場合は `.claude/rules/` への分割を検討（2026-07-27提案と合わせて優先対応）

---

### 2026-07-29: Claude Cowork Dispatch機能（サーバーサイド継続実行）の活用検討

**出典:** articles/2026-07-29_3114_WEB_FelloAI-Claude-Cowork-Guide-Pricing-Setup-Dispatch-2026.md

**提案内容:**
2026年7月7日からCoworkが「Dispatchモード」に対応。Maxプランユーザーはラップトップを閉じた状態でもAnthropicサーバー上でCoworkセッションを継続実行できる。現在の日次収集ルーチンはスケジュールタスクで動作しているが、Cowork Dispatchを使うとさらに柔軟なスケジュール管理が可能になる可能性がある。

**提案アクション:**
1. 現在のMaxプランの有無を確認
2. Cowork Dispatchベータへのアクセス申請（MaxユーザーはMax→順次展開）
3. 日次収集ルーチンとの統合の可否を評価


---

### 2026-07-30: Claude Opus 5 effort toggle — FX自動取引のコスト最適化に活用

**出典:** articles/2026-07-30_3123_WEB_Fortune-ClaudeOpus5-EffortToggle-Release.md

**提案内容:**
Claude Opus 5（2026年7月24日リリース）の「effort toggle」（low/medium/high）は、FX 自動取引エージェントのコスト設計に直接応用できる。価格は Opus 4.8 と同一（$5/$25/M tokens）でありながら、effort:low なら価格据え置きでレスポンス速度が向上する。

**提案アクション:**
1. FX 自動取引の取引シグナル生成: `effort: high`（重要な意思決定）
2. 定期データ取得・前処理: `effort: low`（コスト最小化）
3. Claude Agent SDK の agent() コールに `effort` パラメータを追加実装を検討
4. Opus 5 が GitHub Copilot でも利用可能になったため、FX 開発補助での利用も検討

---

### 2026-07-30: 長時間エージェント安全設計 — FX自動取引の標準要件化

**出典:** articles/2026-07-30_3128_WEB_Eguweb-AI-News-July21-2026-LongAgent.md, 2026-07-30_3130

**提案内容:**
Eguweb の分析によると、2026年7月時点で長時間エージェントの実装標準として「①停止・再開のチェックポイント ②コスト上限設定 ③監査ログ整備 ④オプト・イン型ヒューマン承認フロー」が必須要件になりつつある。FX 自動取引エージェントはこの4要素を全て満たす必要がある。

**提案アクション:**
1. FX/src/ の取引エージェントに `max_cost_usd` 上限パラメータを追加
2. 取引ログに `agent_decision_trace` フィールドを追加（説明責任対応）
3. 重要取引（ロット設定・ポジション転換）にヒューマン承認フロー検討
4. 4要素フレームワーク（データ・オペレーション・コスト・出力）をシステム設計ドキュメントに明記


---

### 2026-07-31: OpenAI GPT-5.6 Luna 80%値下げ — FX自動取引コスト試算の更新

**出典:** articles/2026-07-31_3135_WEB_VentureBeat-OpenAI-GPT56-Luna-80pct-Price-War.md

**提案内容:**
OpenAI が GPT-5.6 Luna を $0.20/$1.20 per M tokens に値下げ（旧 $1/$6）。FX自動取引でのsentiment分析・ニュース解析用途で月次コストが大幅低下する可能性がある。Claude Sonnet 5 プロモ価格 $2/$10 と比較してInputが10倍安い。

**提案アクション:**
1. FX自動取引の月次API費用試算をLuna前提で再計算
2. Sentiment分析（ニュース分類）などlatency許容タスクをLunaに切り替え検討
3. Claude Sonnet 5 vs GPT-5.6 Luna の質・速度・コストトレードオフを実測比較
4. Anthropic Claude Sonnet 5 ($2/$10) vs Luna ($0.20/$1.20): Inputコスト差は10倍。高精度が必要なエントリー判断はSonnet 5、量的スクリーニングはLunaの二層構成を検討

---

### 2026-07-31: Claude大規模障害 — スケジュールタスクのフォールバック設計

**出典:** articles/2026-07-31_3137_WEB_Explainx-Claude-Outage-July29-30-NetworkFailures-Recovery.md

**提案内容:**
2026-07-29〜30のAnthropicサービス障害により、Claude Codeスケジュールタスク（日次収集ルーチン等）が影響を受けた可能性がある。スケジュールタスク運用者として信頼性設計が必要。

**提案アクション:**
1. 日次ルーチンに障害時の通知機能を追加（PushNotificationで「本日のルーチン未実行: Anthropicサービス障害」を送信）
2. status.anthropic.com を monitoring に追加（もしくは RSS/webhook で変更通知を受け取る）
3. 重要ルーチン（FX自動取引サービスモニタリング）にリトライロジック実装: 失敗時に6時間後に再実行
4. Claude障害時の代替フロー検討: Anthropic API のみでなくローカル処理の部分的フォールバックを定義

---

### 2026-08-01: MCP仕様RC ステートレス化 — MCPサーバー展開アーキテクチャの見直し

**出典:** articles/2026-08-01_3138_WEB_MCP-Spec-2026-07-28-Stateless-Protocol-RC.md

**提案内容:**
MCP 2026-07-28 RCでプロトコルがステートレス化。`initialize`ハンドシェイクとセッションIDが廃止され、通常のラウンドロビンLBで展開可能に。現在タスクマネージャーで運用中のMCPサーバー（Gmail等）がある場合、スティッキーセッション不要になることで展開コストが低下。

**提案アクション:**
1. 最終仕様（2026-07-28公開）をReleaseNotesで確認し、使用中MCP serverの更新タイミングを検討
2. Roots・Sampling・Logging featureを使用しているMCPサーバーがあれば、12ヶ月以内に代替実装を検討
3. Extensions framework（逆DNS識別子）に対応したMCPサーバーの作成を検討（MCP Apps Extensionでダッシュボード表示等）

---

### 2026-08-01: Claude Code v2.1.215 — /verify・/code-review 自動呼び出し廃止への対応

**出典:** articles/2026-08-01_3139_WEB_ClaudeCode-v2-1-219-Opus5-Depth3-Subagents-July2026.md

**提案内容:**
v2.1.215で`/verify`と`/code-review`の自動呼び出しが廃止。日次収集ルーチン等でこれらのコマンドに依存するworkflowは明示的な呼び出しが必要になった。

**提案アクション:**
1. セッションレビュースキル（session-review等）のスクリプトで`/verify`が自動実行されていた場合は明示的コマンドを追加
2. GitHub Actions/CIパイプラインでClaudeにコードレビューさせる場合は`/code-review`コマンドを明示的に含める

---

### 2026-08-01: FX自動取引 — TradingAgents Claude対応・Bull/Bear対立構造の採用検討

**出典:** articles/2026-08-01_3141_WEB_TradingAgents-7-Agent-Architecture-BullBear-2026.md

**提案内容:**
TradingAgents v0.3.1がClaude Sonnet 5に正式対応。7エージェント対立構造（Bull/Bear Researcher + Risk Manager）はFX自動取引の判断品質向上に応用可能。AAPL バックテストでSharpe 8.21・MaxDD 0.91%という結果。

**提案アクション:**
1. 現在のFX自動取引システムにBull/Bear対立構造を試験的に実装（Claude Sonnet 5をバックエンドに使用）
2. pip install tradingagents でローカル環境にインストールし、FX通貨ペアでのバックテストを実施
3. 注意事項：APIコスト$0.10-0.50/シグナル・幻覚リスク・過学習問題のため必ずペーパートレードから開始
4. MT5直接統合は非対応のためPython←→MT5ブリッジ層が必要


---

### 2026-08-02: Agent SDK クレジット監視 — 日次収集ルーチンの月次コスト試算

**出典:** articles/2026-08-02_3153_WEB_ClaudeAgentSDK-Credits-Billing-Change-June15-2026.md

**提案内容:**
2026年6月15日施行のClaude Agent SDK課金変更により、非インタラクティブ実行（スケジュールタスク含む）はサブスクリプションの月次Agentクレジットから消費される（Pro $20/月、Max 5x $100/月）。本リポジトリの日次収集ルーチン・weekly-digest等のスケジュールタスクが対象となる可能性がある。

**提案アクション:**
1. `/usage` コマンドでAgent SDKクレジット消費量を月次で確認する習慣を追加
2. 複数のスケジュールタスクが重なる日のクレジット消費量を試算し、月次上限に対するバッファを確認
3. クレジット上限超過が見込まれる場合は頻度調整またはAPI直接呼び出し（トークン課金）への切り替えを検討

---

### 2026-08-02: FX自動取引 — MT5 LLM認知エンジン統合パターン（MQL5公式ガイドより）

**出典:** articles/2026-08-02_3158_WEB_Algorithmic-Trading-AI-MT5-EAs-Complete-Guide-2026.md

**提案内容:**
MQL5公式ブログ（2026/7/1）が「MT5 LLM Integration」パターンを提唱。MT5をシグナル生成に使い、LLMが認知的判断エンジンとして機能する構成（MT5シグナル→LLM判断→MT5執行）。FX自動取引プロジェクトの現状アーキテクチャとの親和性が高い。

**提案アクション:**
1. FX自動取引の現行EAにLLMセンチメント分析モジュールを追加する試験実装（Claude Sonnet 5 via API）
2. MT5シグナル→Python→Claude API→MT5執行 の4層ブリッジアーキテクチャを設計
3. まずペーパートレードで1ヶ月バックテスト → 結果をFX自動取引/STATUS.mdに記録

---

### 2026-08-02: MCP環境 — ステートレス仕様RC対応のMCPサーバー構成レビュー

**出典:** articles/2026-08-02_3154_WEB_MCP-2026-Official-Roadmap-Stateless-Extensions-Apps.md

**提案内容:**
MCPの2026-07-28 RC仕様でステートレスプロトコルコアが確定。現行の.mcp.jsonで参照しているローカルMCPサーバー（ステートフル前提）は将来的に移行が必要になる可能性がある。

**提案アクション:**
1. sandbox/タスクマネージャー/.claude/settings.json の mcpServers 設定を棚卸しし、ステートレス対応可否を評価
2. MCPのExtensionsフレームワーク（サードパーティ拡張）が安定したら、collect-x-articles等のカスタムスキルをMCPサーバー化する選択肢を検討
3. RC → 安定版リリース時にMCP公式ブログ（blog.modelcontextprotocol.io）を確認してアップデート
