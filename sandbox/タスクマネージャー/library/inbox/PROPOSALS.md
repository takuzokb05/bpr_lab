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

