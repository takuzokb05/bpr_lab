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

## 2026-04-09 収集分

### 1. CLAUDE.md / skills への反映提案

#### 1-1. SKILL.md「ルーティングテーブル」パターンの適用
**出典:** articles/2026-04-09_006_Anthropic_Official_33Page_Skills_Design_Patterns_smartscope.md

**提案内容:**
Anthropic公式ガイドが推奨する「ルーティングテーブル型SKILL.md」を既存スキルに適用する。現行のSKILL.mdが100行を超えているものはすべてリファクタリング対象。
- SKILL.md本体: 100行以内（frontmatter + ルーティングロジックのみ）
- 詳細参照: `references/` ディレクトリ以下に分割ファイルを配置
- キーワードベースで該当ファイルのみ読み込む設計
- `model: haiku` 指定で軽量タスクのコスト削減

対象スキル候補: curate, session-start-hook, claude-api（いずれも現状100行超の可能性あり）

#### 1-2. CLAUDE.md に AGENTS.md サポートを追加検討
**出典:** articles/2026-04-09_007_CLAUDE_md_AGENTS_md_Team_Design_Patterns_homula.md

**提案内容:**
AGENTS.md（OpenAI Agents SDK / Google ADK互換の標準）が2026年に事実上の標準として普及しつつある。Claude Code以外のLLMエージェントからも本プロジェクトを参照できるよう、AGENTS.mdをCLAUDE.mdの内容と同期した形で追加することを検討する。

---

### 2. Hooks への反映提案

#### 2-1. PermissionDenied フックの実装
**出典:** articles/2026-04-09_008_Claude_Code_217_Update_New_Hooks_issoh.md / articles/2026-04-09_009_Claude_Code_Hooks_All_12_Events_CI_CD_pixelmojo.md

**提案内容:**
v2.1.7で追加された`PermissionDenied`フックイベントを活用する。
- Auto Modeで分類器が拒否した操作を捕捉し、ログに記録する
- 特定の操作（FX取引システムの本番環境書き込み等）については `{retry: true}` ではなく `{exit: true}` を返してセッションを安全に終了させる
- 拒否されたツール呼び出しをSlack通知する監視パターンを実装

また、`TeammateIdle`・`TaskCompleted`フックによるマルチエージェント協調の実装が可能になった。並列エージェントが完了したタイミングでの集約処理に活用できる。

---

### 3. FX自動取引システムへの反映提案

#### 3-1. Claude Agent SDK の 1M コンテキスト移行（期限あり）
**出典:** articles/2026-04-09_013_Claude_Agent_SDK_Deep_Dive_Library_Mode_jidonglab.md

**提案内容（重要：期限 2026-04-30）:**
`context-1m-2025-08-07` ベータヘッダーが **2026年4月30日** に廃止される。FX自動取引システムでClaude APIを使用している箇所でこのベータヘッダーを使用している場合は、**4月30日までに** Claude Sonnet 4.6 または Claude Opus 4.6 へ移行する必要がある（これらのモデルは1Mコンテキストを標準サポート）。

#### 3-2. MCP v2.1 Server Cards の導入検討
**出典:** articles/2026-04-09_011_MCP_Technical_Deep_Dive_v21_Server_Cards_dasroot.md

**提案内容:**
FX自動取引システムのMCPサーバー（市場データ取得・MT5連携等）にServer Cardsを実装する。`/.well-known/mcp.json`を設置することで、クライアントがサーバー接続前にCapabilities・認証要件を自動検出できる。特に複数のClaude Codeセッションや将来的なマルチエージェント環境でサーバー自動検出が有効になる。

---

## 2026-04-10 収集分の提案

### 1. CLAUDE.md への反映提案

#### 1-1. CLAUDE.md の @import モジュール化 + 200行ルール適用
**出典:** articles/2026-04-10_003_CLAUDE_md_Writing_Complete_Guide_Templates_2026_Uravation.md

**提案内容:**
現在の CLAUDE.md が200行を超えているプロジェクトでは、過剰な記述が Claude の追従率を低下させる（70%程度）。以下の対策を適用する：
- CLAUDE.md 本体を200行以内に抑え、詳細ルールを `.claude/rules/` 以下の個別ファイルに分割
- `@import .claude/rules/fx-trading.md` のような @import 記法でモジュール化
- フックを活用して「守らせたいルール」（CLAUDE.md 追従率70%では不足）を100%強制する

---

### 2. FX自動取引システムへの反映提案

#### 2-1. metatrader-mcp-server の導入検討（Claude Code → MT5 直接制御）
**出典:** articles/2026-04-10_010_MetaTrader_MCP_Server_GitHub_Ariadng.md

**提案内容（優先度: 高）:**
`ariadng/metatrader-mcp-server` は MCP サーバーとして MT5 に接続し、Claude Code から直接注文発注・ポジション管理・市場データ取得が可能になるツール。現在の FX自動取引システムで Python ブリッジ経由で MT5 を制御している場合、このMCPサーバーに置き換えることで Claude Code エージェントが直接 MT5 と対話できる。
- CLAUDE.md に `mt5-trading` MCP サーバーとして設定追加
- バックテスト・フォワードテストの自動化ループに活用できる
- 検証手順: Docker or local で MCP サーバーを起動 → Claude Code の settings.json に追加 → 口座情報取得ツールで疎通確認

#### 2-2. MT5 LLM 統合アーキテクチャ標準化（Ollama / DeepSeek R1）
**出典:** articles/2026-04-10_011_MT5_LLM_Integration_Choosing_Right_AI_MQL5.md / articles/2026-04-10_012_AI_Trading_Agents_vs_Expert_Advisors_2026_Guide.md

**提案内容:**
MQL5 の実践ブログ（2026年2月）で示された推奨アーキテクチャに基づき、FX 自動取引システムの LLM 統合方針を標準化する：
- **高タイムフレーム方向性フィルター専用**: LLM は HFT 不可・スキャルピング不可（1〜3秒 API レイテンシあり）。H1〜D1 の方向性判断に限定する
- **コスト最適化**: ローカル Ollama（DeepSeek R1）を繰り返しロジック判断に使用し、外部 API コストを削減
- **EA との役割分担**: EA は板読み・エントリーの実行、LLM はレジーム判断・戦略切り替え判断に特化

---

### 3. skills-registry への反映提案

#### 3-1. Memento-Skills パターンの curate スキルへの応用検討
**出典:** articles/2026-04-10_019_Memento_Skills_AI_Agents_Rewrite_Own_Skills_VentureBeat.md

**提案内容:**
Memento-Skills（VentureBeat 2026-04-09）は、AI エージェントが経験から学んで自身のスキルを自律的に書き換えるフレームワーク。本プロジェクトの curate スキルに応用できるパターン：
- curate スキルが収集・キュレーション実行後に SIGNAL/NOISE 判断精度を自己評価し、SKILL.md の SIGNAL基準を自動更新する Post-execution フックパターン
- SessionEnd Hook + curate スキルを組み合わせて「今日の収集で新たに発見した NOISE パターン」を SKILL.md に追記する自己改善ループ

---

## 2026-04-11 収集分の提案

### 1. CLAUDE.md への反映提案

#### 1-1. CLAUDE.md コンテキスト汚染防止：7原則の適用
**出典:** articles/2026-04-11_004_CLAUDE_md_Best_Practices_7_Principles_Zenn.md / articles/2026-04-11_007_Claude_Code_Best_Practices_Real_Projects_Ranthebuilder.md

**提案内容:**
「ルール数の上限超え → コンテキスト汚染 → 遵守率低下」という失敗パターンを防ぐため、以下の原則を CLAUDE.md 運用方針に追記する：
- 各ルールに「これがなければ Claude がミスするか？」テストを適用し、不要なルールを削除する
- WHY（なぜ）を記述し、WHAT（何）や HOW（どう）はスキルに委譲する
- 実行前に「1000行超のCLAUDE.mdが逆効果になった経験」の教訓として、毎月1回 Claude 自身にCLAUDE.mdをレビューさせるルーチンを設ける

---

### 2. skills-registry への反映提案

#### 2-1. /skillify コマンドの活用（スキル自動生成）
**出典:** articles/2026-04-11_002_Claude_Code_Skillify_Internal_Skill_Medium.md

**提案内容（優先度: 中）:**
Claude Code の内部スキル `/skillify` は、セッション履歴から繰り返しパターンを分析し SKILL.md を自動生成する。本プロジェクトのスキル整備に以下のように活用できる：
- curate スキルの定期的な `/skillify` 実行で「暗黙的なキュレーション判断」をスキルに抽出・形式化する
- FX自動取引ワークフローで頻出するバックテスト実行パターンを `/skillify` でスキル化する
- 公式ドキュメント未記載の隠し機能のため、動作確認してから本番スキルに取り込む

#### 2-2. スキルの「育てる運用」プロセスの導入
**出典:** articles/2026-04-11_020_Claude_Code_Skills_Zerolichi_Lab_Guide_JA.md

**提案内容:**
スキルを「作って終わり」ではなく「育て続ける」視点でプロセス化する：
- 使用頻度の低いスキルを月次でアーカイブし肥大化を防止する
- Claude 自身にスキルを評価させ description を改善することでトリガー精度を向上させる（Autoresearch 的運用）
- 各スキルに「最終更新日」と「使用回数（推定）」をコメントで記録する

---

### 3. FX自動取引システムへの反映提案

#### 3-1. Monitor tool の FX エージェント監視への活用
**出典:** articles/2026-04-11_019_Claude_Code_April_Week2_Update_Team_Onboarding_Monitor.md

**提案内容（優先度: 高）:**
Claude Code April Week 2 で追加された Monitor tool は、バックグラウンドスクリプトからのイベントをストリーミング監視できる。FX自動取引エージェントへの応用：
- MT5 EA の stdout/stderr を Monitor tool でリアルタイム監視し、異常シグナルを即時検知するフック設計
- バックグラウンドで動作する収集 + キュレーション + FX判断ループを Monitor で可視化する
- Linux 環境での PID ネームスペース分離サンドボックスと組み合わせて安全なエージェント実行を実現

#### 3-2. TradingAgents v0.2.0 マルチプロバイダー対応の FX 応用検討
**出典:** articles/2026-04-11_011_TradingAgents_Guide_DigitalOcean.md

**提案内容:**
TradingAgents v0.2.0（2026年2月）は Claude 4.x を含むマルチプロバイダー対応になっており、7役割エージェント（Fundamentals・Sentiment・News・Technical Analyst・Researcher・Trader・Risk Manager）をLangGraphで構成する。FX自動取引システムへの応用検討ポイント：
- Risk Manager → Trader の承認フローが現行のポジション管理ロジックに直接適用可能
- Bull/Bear 研究者の議論パターンを円ドルの方向性フィルターに応用する
- DigitalOcean ガイドの GPU Droplet セットアップを参考に VPS 上でのマルチエージェント構成を検討する

#### 3-3. LLM-jp-4（国産オープン LLM）の低コスト日本語処理への活用
**出典:** articles/2026-04-11_017_1bit_LLM_Bonsai_LLM-jp-4_TechnoEdge.md

**提案内容:**
国立情報学研究所が公開した LLM-jp-4 8B（Apache 2.0）は、日本語MT-BenchでGPT-4oを上回るスコアを達成しており、オープンソースで商用利用可能。FX取引エージェントへの応用：
- 日本語ニュースヘッドラインのセンチメント分析を LLM-jp-4 8B でローカル実行し、外部 API コストをゼロに
- Ollama 経由でローカル VPS で動作させ、TradingAgents の Sentiment Analyst ロールに組み込む
- Bonsai 8B（1ビット）と組み合わせたメモリ効率化も検討（VPS の RAM 制約が厳しい環境向け）

---

## 2026-04-12 収集分

### 1. CLAUDE.md への反映提案

#### 1-1. CLAUDE.md クロスツール互換設計の導入
**出典:** articles/2026-04-12_010_CLAUDE_md_AGENTS_md_Best_Practices_Izanami.md

**提案内容（優先度: 中）:**
CLAUDE.md（Claude Code）と AGENTS.md（OpenAI Codex 等）は同じ「AIへの永続的プロジェクト指示メカニズム」。今後のツール多様化に備えて以下の設計を採用する：
- ツール固有の記法（Claude Code の `ALWAYS`/`NEVER` 強調等）を最小化し、汎用 Markdown で記述する部分を増やす
- コアルール（禁止パターン・コマンド・アーキテクチャ）をツール非依存セクションとして分離する
- CLAUDE.md に `# Claude Code specific` セクションを作り、Claude Code 固有の設定（スキル参照・Hooks 設定等）のみをそこに集約する

#### 1-2. PreToolUse フックによる安全ゲートの実装
**出典:** articles/2026-04-12_003_Claude_Code_HTTP_Hooks_GitHub_Actions_CICD.md, articles/2026-04-12_004_Claude_Code_Hooks_Production_Patterns_Async.md

**提案内容（優先度: 高）:**
Async Hooks（2026年1月リリース）と HTTP Hooks を活用し、現在 CLAUDE.md に記述しているルールをより確実に強制する：
- PreToolUse フック: 本番ファイル（CLAUDE.md, settings.json 等）への書き込みをブロックする設定を追加
- Async PostToolUse フック: コード変更後に自動テストをバックグラウンド実行（Claudeをブロックしない）
- CLAUDE.md の「NEVER」制約のうち、テスト可能なものから順に Hook 化し遵守率を 80% → 100% に引き上げる
- `/hooks` コマンドで設定確認し、既存の Hook 設定を棚卸しする

### 2. skills-registry への反映提案

#### 2-3. Skills vs MCP 判断基準の skills-registry への記載
**出典:** articles/2026-04-12_006_Claude_Code_Skills_vs_MCP_Servers_DEV.md

**提案内容（優先度: 中）:**
Skills（繰り返しワークフローのカプセル化）と MCP（外部ツール・API接続）の役割の違いを skills-registry に明記する：
- 現在の skills-registry に `## Skills vs MCP 判断基準` セクションを追加する
- 「何度も繰り返す手順 → スキル、外部サービスに接続 → MCP」という判断木を記載
- 現在 CLAUDE.md に書いている MCP 接続設定を整理し、適切な配置場所に移動する

### 3. FX自動取引システムへの反映提案

#### 3-4. マルチエージェント FX ボットのアーキテクチャ改善
**出典:** articles/2026-04-12_015_Comparing_LLM_Trading_Bots_Comprehensive_FlowHunt.md, articles/2026-04-12_017_AI_Hyperautomation_Algorithmic_Trading_Academic.md

**提案内容（優先度: 高）:**
2026年の比較研究（FlowHunt + 査読論文）により「マルチエージェント型 LLM ボットが単一 LLM より高 Sharpe 比を達成」が定量的に確認された：
- 現在の FX ボット設計をレビューし、シングル LLM 判断 → 役割分担型マルチエージェント化の検討を優先タスクに追加
- LLM + 従来 ML（XGBoost・LightGBM）のハイブリッドアプローチが論文で最高性能。戦略収益性予測に ML 分類を追加する
- TradingAgents v0.2.0 の Risk Manager → Trader 承認フローを参考に「リスクゲート」をマルチエージェント構成に追加する
- バックテスト vs ライブ取引の性能差・スリッページ対処をシステム設計ドキュメントに明示的に記載する

#### 3-5. Backtest → Risk → Live パイプラインの整備
**出典:** articles/2026-04-12_016_Build_AI_Quant_Trading_Bot_Backtest_Risk_Markaicode.md

**提案内容（優先度: 中）:**
Markaicode のフルスタックガイドを参考に、FX自動取引システムの「開発 → 検証 → 本番」パイプラインを整備する：
- ML 分類（ロジスティック回帰/XGBoost/LightGBM/LSTM）で「この戦略が儲かるか」を事前予測するモジュールの追加
- ベクトル DB（ChromaDB 等）でトレードログを永続化し、失敗パターンの自動学習ループを構築する
- 経済カレンダー監視エージェントによるイベント駆動シグナル生成を既存戦略のサブコンポーネントとして追加する

---

## 2026-04-13 収集分

### 1. CLAUDE.md への反映提案

#### 1-1. lessons.md 自動蓄積フローの導入
**出典:** articles/2026-04-13_009_CLAUDE_md_Writing_育て方_Qiita_Daichi.md, articles/2026-04-13_002_Claude_Code_2026_Daily_OS_Top_Developers_Medium.md

**提案内容（優先度: 高）:**
Claudeがミスをして修正が入った際に、同じミスを防ぐルールを自動的に lessons.md に追記するフローを設ける：
- CLAUDE.md に「Claudeがミスをした場合、そのミスを防ぐルールを lessons.md に追記すること」という指示を追加する
- 数週間ごとに「このCLAUDE.mdをレビューして改善提案してください」というセッションを設け、冗長・矛盾した指示を整理する
- CLAUDE.md の 300 行上限を意識し、肥大化した場合は domain-specific なルールを skills-registry へ移管するルールを明記する
- これにより「Claude が自己改善する CLAUDE.md」の運用サイクルが確立できる

#### 1-2. hooks.md 設定テンプレートの整備
**出典:** articles/2026-04-13_003_Claude_Code_Hooks_Tutorial_Lifecycle_Events_Supalaunch.md

**提案内容（優先度: 中）:**
CLAUDE.md の「NEVER」制約のうち決定論的に強制すべきものを hooks 化する設計を追加する：
- `.claude/settings.json` に PreToolUse フックを追加し、CLAUDE.md/settings.json 等の重要ファイルへの直接書き込みをブロックする
- PostToolUse フックでコード変更後の自動テスト実行を設定し、テスト漏れを防止する
- MCPサーバーのツール（`mcp__<server>__<tool>` パターン）も hooks でマッチングできる点を CLAUDE.md に明記する

### 2. skills-registry への反映提案

#### 2-1. Skills vs Subagents 判断基準の skills-registry への追加
**出典:** articles/2026-04-13_005_Claude_Code_Skills_vs_Subagents_When_To_Use_DEV.md, articles/2026-04-13_006_Awesome_Claude_Code_Subagents_100plus_GitHub.md

**提案内容（優先度: 中）:**
Skills（ポータブルな専門知識）とSubagents（独立コンテキストで動くエージェント）の使い分け判断基準を skills-registry に明記する：
- `skills-registry/README.md` に `## Skills vs Subagents 判断フロー` セクションを追加する
- 判断基準: ①冗長な出力を本文に入れたくない → Subagent、②複数箇所で同じ専門知識が必要 → Skill、③自己完結してサマリーだけ返せる → Subagent
- VoltAgent/awesome-claude-code-subagents (GitHub) の 100+ サブエージェント定義を参照して、現在 SKILL.md 化しているものをサブエージェント化すべきか棚卸しする

#### 2-2. Skills の Progressive Disclosure 設計見直し（87%削減実績参照）
**出典:** articles/2026-04-13_007_Claude_Code_Skills_Thorough_Understanding_Zenn_Acntechjp.md

**提案内容（優先度: 中）:**
現在の SKILL.md のうち肥大化しているものを Progressive Disclosure 原則でリファクタリングする：
- SKILL.md の YAMLフロントマター（name/description）を適切に記述してClaudeの自動起動判断精度を上げる
- 大きなスキルを「コアロジック」と「詳細手順ファイル（参照渡し）」に分割し、必要時だけ詳細を読み込む設計に変更する
- acntechjp の事例（87%削減）を参考に、スキルサイズの目標上限（例: 200行以内）を設定する

### 3. FX自動取引システムへの反映提案

#### 3-1. Claude Managed Agents による FX ボット本番化の検討
**出典:** articles/2026-04-13_013_Claude_Managed_Agents_Official_Blog_Anthropic.md, articles/2026-04-13_014_Claude_Managed_Agents_Complete_Guide_The_AI_Corner.md

**提案内容（優先度: 中）:**
2026年4月8日に公開ベータとなった Claude Managed Agents を FX自動取引システムのエージェント実行環境として評価する：
- 現状: ローカル環境でのエージェント実行（VPS or ローカルPC）
- 検討: Managed Agents のセキュアサンドボックス + 長時間自律セッション + 自動チェックポイントを活用した本番化
- 料金試算: $0.08/セッション時間。24時間稼働なら月 $57.6 + トークン料金。VPS コストとの比較が必要
- メリット: クレデンシャル管理・状態永続化・セッショントレースのデバッグが容易。プロトタイプから数日で本番化可能

#### 3-2. MQL5 から LLM API を直接呼び出す EA 設計パターンの検討
**出典:** articles/2026-04-13_018_FX_AI_EA_Autotrade_Guide_Shadowdia.md

**提案内容（優先度: 低）:**
MQL5 の HTTP リクエスト機能を使って EA 内から Claude/GPT API を直接呼び出す軽量アーキテクチャの実装可能性を検討する：
- 現状の Python 仲介アーキテクチャとの比較: EA から直接 LLM API 呼び出し → レイテンシ低減・Python サーバー不要
- 課題: MT5 のネットワークアクセス制限・レート制限・API キー管理の安全性
- 参考実装: GPT API 連携 EA 開発 (sayama_ocha/note) のパターンを Claude API 向けに変換する

---

## 2026-04-14 収集分

### 1. FX自動取引への反映提案

#### 1-1. AI事業者ガイドラインv1.2 対応：FX自動取引システムへのHITL設計
**出典:** articles/2026-04-14_006_Japan_AI_Governance_Guideline_v12_Agent_Regulation.md

**提案内容（優先度: 高）:**
経済産業省・総務省の「AI事業者ガイドラインv1.2」（2026年3月31日）でAIエージェントが外部システムに影響するアクション（取引実行・データ更新）に人間の確認・承認プロセスが必要と明示。FX自動取引システムへの影響を検討する：
- 高リスクアクション（実際の注文執行）には事前承認フロー or 上限ルールの実装を検討
- 現在の「確信度スコア + ロット数制限」設計はリスク段階別監視の精神と整合している
- 自動取引ログの完全記録と事後監査可能な設計の確認・強化
- 参考: `sandbox/FX自動取引/` の設計文書に「AI事業者ガイドライン v1.2 対応状況」セクション追加を検討

#### 1-2. マイメイト「リピートAI」のトレンド/レンジ自動切替パターンをEAに応用
**出典:** articles/2026-04-14_009_FX_MyMate_RepeatAI_Range_Strategy_New_Feature.md

**提案内容（優先度: 中）:**
マイメイトのリピートAIがトレンド判定→最適戦略自動切替を実装。現在のFX EAに同様の市場レジーム判定→戦略切替ロジックを追加する価値があるか検討：
- 現在の Phase 3 でレジーム検出機能は実装済み（`sandbox/FX自動取引/`）
- リピート系（レンジ）vs 方向性（トレンド）の自動切替がリテール向けサービスでも採用される標準になりつつある
- EAの戦略選択ロジックを拡充し、「レンジ→グリッドまたはリピート系」「トレンド→モメンタム系」の切替条件を明確化する

### 2. Claude Code運用への反映提案

#### 2-1. Claude Code Routines の /collect スキルへの適用検討
**出典:** articles/2026-04-14_001_Claude_Code_Routines_New_Feature_9to5Mac.md

**提案内容（優先度: 中）:**
本日リリースのClaude Code Routinesはスケジュール設定した自律タスクをAnthropicインフラ上で実行（Macオフラインでも継続）。現在VPS cronで実行している日次情報収集フローをRoutinesに移行できる可能性を検討する：
- 現状: VPS上のcollect_x.pyがX投稿を収集→GitHub push
- Routines化: GitHub連携+WebスクレイピングをClaude Codeが直接担当→VPS不要に
- 制限: Max=1日15ルーチン、Team/Enterprise=1日25ルーチン
- 課題: Routinesの実際のツールアクセス範囲（現在ベータ）の確認が必要



---

## 2026-04-15 収集分

### 1. Claude Code Routines 本番活用への昇格

#### 1-1. 日次情報収集フローのRoutines移行（前回提案のアップデート）
**出典:** articles/2026-04-15_001_Claude_Code_Routines_Official_Anthropic_Blog.md / articles/2026-04-15_008_Claude_Code_Routines_AI_Autotask_While_Sleeping_Jinrai.md

**提案内容（優先度: 高）:**
Claude Code Routinesが2026年4月14日に正式リサーチプレビューとして公開。本日（4/15）時点でAnthropicインフラ上でスケジュール・API・GitHubイベントトリガーが利用可能。前回提案（VPS→Routines移行）を具体化する段階に入った：
- **実験1:** curate スキルをRoutinesのスケジュールトリガー（毎朝9時）で実行するテスト
- **制限:** Pro=5件/日、Max=15件/日 → 日次収集+キュレーション+コミットで3件程度消費見込み
- **注意:** Routinesはリサーチプレビュー段階。安定性確認が必要
- **アクション:** 来週以降、まず1ルーティン（WebSearch収集のみ）を試験的に設定してみる

#### 1-2. サブエージェントからSkillが呼び出せない制約への対応
**出典:** articles/2026-04-15_002_Claude_Code_Subagents_Official_How_When_To_Use.md / articles/2026-04-15_005_Claude_Code_Agent_Teams_Parallel_Shared_Task_List_MindStudio.md

**提案内容（優先度: 中）:**
公式ブログが確認：サブエージェントはSkillツールを呼び出せない（issue #38719で改善議論中）。現在の日次収集エージェントでサブエージェントを使う場合、skillベースの処理はメインエージェント経由にする必要がある：
- curate スキルはメインエージェントで実行し、並列化は「WebSearch×ドメイン」レベルにとどめる
- Agent Teamsは「ファイル非依存の大規模並列処理」が最適用途であり、curate処理には向かない
- 並列WebSearch（4ドメイン同時）は現行設計のまま継続可

### 2. CLAUDE.md設計の見直し提案

#### 2-1. プロジェクト規模別パターンの適用
**出典:** articles/2026-04-15_012_CLAUDE_md_Design_Patterns_Project_Scale_Best_Practices_StartLink.md

**提案内容（優先度: 中）:**
start-link.jpの設計パターン集によると、現状のタスクマネージャーは「Modular（@import活用）」パターンに近い。以下の改善を検討：
- rules/ サブディレクトリへの条件付きルール分離（YAMLフロントマターのglobパターン活用）
- CLAUDE.md本体は200行以内に圧縮し、スキル固有のルールはスキル内に移動
- Enterprise パターン要素（governance・compliance記述）は必要性が低いので不要

### 3. FX自動取引への反映提案

#### 3-1. Routinesによる夜間FXシグナル生成の自動化
**出典:** articles/2026-04-15_001_Claude_Code_Routines_Official_Anthropic_Blog.md / articles/2026-04-15_016_Best_AI_Trading_Agent_Forex_MT4_MT5_Integration_2026_GPTrader.md

**提案内容（優先度: 中）:**
Claude Code Routinesのスケジュールトリガーで、夜間にFXシグナル生成（テクニカル分析+LLM判断）を自動実行し、結果をGitHub Issueまたは通知で受け取るフローの設計を検討：
- Routines → MT5 Python API → シグナル生成 → GitHub Issue作成 のフローが理論上可能
- GPTrader 2026比較でAgentTradeX（LangChain+GPT-4o）がボラティリティ相場で25%超過収益という事例
- ただしRoutinesはリサーチプレビュー段階。先にペーパートレードで検証を

### 4. AI規制モニタリングの強化

#### 4-1. 経産省AI民事責任手引きの自社システムへの適用確認
**出典:** articles/2026-04-15_020_METI_AI_Civil_Liability_Interpretation_Guide_v1_April2026.md

**提案内容（優先度: 高）:**
経産省が2026年4月9日公表の「AI民事責任手引き（第1.0版）」で補助型AI/代替型AIの2類型を定義：
- FX自動取引AIは「代替型AI」（人間の判断を代替する取引実行）に該当する可能性
- 代替型AIの場合、事業者の責任範囲が広くなる
- **アクション:** sandbox/FX自動取引/ の設計文書に「補助型/代替型の分類と責任設計」セクションを追加検討
- EU AI Act（2026年8月施行予定、高リスクシステム適合義務）との整合性も確認
