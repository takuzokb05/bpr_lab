# 蔵書目録

## 分類タグ一覧

| タグ | 説明 |
|------|------|
| agent設計 | エージェントの組織設計・専門分化・協調パターン |
| ガバナンス | 権限管理・安全運用・Permission Mode |
| CLAUDE.md | CLAUDE.mdの書き方・構成・ベストプラクティス |
| スキル | スキル設計・自己改善・命名規約 |
| UX/デザイン | UI品質・デザインシステム・アクセシビリティ |
| ワークフロー | 作業手順・自動化・プロンプト技法 |
| 非エンジニア | 非技術者の活用パターン・段階的学習 |
| アーキテクチャ | Claude全体の設計思想・SDK・MCP・CI/CD |
| 読書 | 書籍の読書ノート（/readingスキルで生成。実践ガイド付き） |

## 蔵書一覧

| # | タイトル | ファイル | 分類 | 要点（1行） | 反映先 | 状態 |
|---|---------|---------|------|-----------|--------|------|
| 1 | Self improving skills for agents | `articles/Self improving skills for agents.txt` | スキル | スキルのObserve→Inspect→Amend→Evaluateサイクルで自動進化 | catalog.yaml known_issuesフィールド | 反映済 |
| 2 | PRマネージャー32人チーム | `articles/PRマネージャー1人の中に、32人のチームがいる話。.txt` | agent設計 | 司令塔(CLAUDE.md)→8部門32エージェント→8スキルの3層組織 | 未反映（中長期: 専門分化エージェント検討） | 読了 |
| 3 | Claude Codeでyes連打してる人 | `articles/Claude Codeでとりあえずyes連打してる人.txt` | ガバナンス | 権限確認時にリスク4軸（漏洩・外部送信・破壊・設定変更）を%表示 | agent-governance.md リスク分類 + base.md ツール許可ルール（リスク%表示） | 反映済 |
| 4 | Auto Mode完全解説 | `articles/Claude Code新機能「Auto Mode」完全解説.txt` | ガバナンス | AI判断ベースの中間Permission Mode。隔離環境推奨 | docs/agent-governance.md Permission Mode段階化 | 反映済 |
| 5 | Most people treat CLAUDE.md like a prompt file | `articles/Most people treat CLAUDE.md like a prompt file..txt` | CLAUDE.md | WHY/WHAT/HOW/WORKFLOWSの4要素構成。短さが精度を上げる | base.md + タスクマネージャーCLAUDE.md全面リファクタ | 反映済 |
| 6 | デザインシステムを作って工夫したこと（melta UI） | `articles/Claude Codeに特化したデザインシステムを作って工夫したこと.txt` | UX/デザイン, スキル | 禁止パターン76項目明示化。tokens.jsonでAI用SSOT | base.md 禁止パターンセクション | 反映済 |
| 7 | UIがダサい問題を解決するskill | `articles/Claude Codeの「UIがダサい問題」を解決するskill見つけたの巻.txt` | UX/デザイン | 公式/frontend-design（LP向け）vs コミュニティskill（ダッシュボード向け）の使い分け | 未反映（参考情報として保持） | 読了 |
| 8 | Claude architect full course | `articles/I want to become a Claude architect (full course)..txt` | アーキテクチャ | Claude Code / Agent SDK / API / MCPの4軸。Production-gradeの実装パターン | 未反映（参考情報として保持） | 読了 |
| 9 | ask_user_inputスタイル | `articles/もう長いプロンプト不要！Claudeのとチート級呪文「ask_user_inputスタイルでお願い」って入力してみて.txt` | ワークフロー, 非エンジニア | 「ask_user_inputスタイルでお願い」で選択肢カード型の対話に変換 | scaffolder SKILL.md インタラクティブモード + settings-local.json作成時にテスト実施 | 反映済 |
| 10 | プロンプトプレビュー | `articles/プロンプトプレビュー.url` | ワークフロー | （URLブックマーク。内容未確認） | — | 未読 |
| 11 | 5 Agent Skill design patterns (ADK) | `articles/5 Agent Skill design patterns every ADK developer should know.txt` | スキル | 5パターン: Tool Wrapper / Generator / Reviewer / Inversion / Pipeline。パターンは合成可能 | 未反映（スキル設計ガイドとして中期検討） | 読了 |
| 12 | Lessons from Building Claude Code: How We Use Skills | `articles/Lessons from Building Claude Code How We Use Skills.txt` | スキル | Anthropic社内の9カテゴリ分類。Progressive Disclosure・On Demand Hooks・Gotchasセクション・descriptionはモデル向け | 全6スキルにGotchasセクション追加 + catalog.yaml description書き直し | 反映済 |
| 13 | 非エンジニアの2つのファイル設定 | `articles/Claude Codeを使い始めた非エンジニアが、最初にやるべき「たった2つのファイル設定」.txt` | 非エンジニア, ガバナンス | settings.local.json（鍵）+ CLAUDE.md（ルール表）の二重ロック。両方必要な理由を解説 | agent-governance.md 二重ロック概念 + templates/settings-local.json テンプレート | 反映済 |
| 14 | チームのCLAUDE.mdが勝手に育つ — Hook自動化 | `articles/チームのCLAUDE.mdが勝手に育つ - Hook機能での自動化.txt` | CLAUDE.md, スキル | SessionEnd + PreCompact Hookで会話履歴→CLAUDE.md更新提案を自動化。Self-improving CLAUDEmd | 未反映（Self-improving skillsと合わせて中期検討） | 読了 |

## 日次収集（2026-03-27〜）

| No. | タイトル | 言語 | 状態 | タグ | ファイル |
|-----|---------|------|------|-----|--------|
| 001 | Claude Code March 2026: All Updates from /loop to Voice Mode | en | 読了 | #update | articles/2026-03-27_001_Claude_Code_March_2026_Updates.md |
| 002 | Claude Code Tips & Tricks | en | 読了 | #workflow #best-practices | articles/2026-03-27_002_Claude_Code_Tips_and_Tricks.md |
| 003 | 50 Claude Code Tips and Best Practices For Daily Use | en | 読了 | #best-practices #hooks #mcp #claude-md | articles/2026-03-27_003_50_Claude_Code_Tips_Best_Practices.md |
| 004 | awesome-claude-code: A curated list of skills, hooks, slash-commands | en | 読了 | #skills #hooks #mcp | articles/2026-03-27_004_awesome-claude-code_curated_list.md |
| 005 | Claude Code Setup Guide: MCP Servers, Hooks, Skills (2026) | en | 読了 | #mcp #hooks #skills | articles/2026-03-27_005_Claude_Code_Setup_MCP_Hooks_Skills_2026.md |
| 006 | Claude Code Hooks Guide 2026: Automate Your Workflow | en | 読了 | #hooks #automation | articles/2026-03-27_006_Claude_Code_Hooks_Guide_2026.md |
| 007 | Claude Code Complete Guide 2026: From Zero to Hero | en | 読了 | #workflow #best-practices #automation | articles/2026-03-27_007_Claude_Code_Complete_Guide_2026.md |
| 008 | Common workflows - Claude Code Docs (Official) | en | 読了 | #workflow #official #automation | articles/2026-03-27_008_Claude_Code_Common_Workflows_Official.md |
| 009 | Claude Codeスキル活用術｜作り方から「育てる運用」まで実践解説 | ja | 読了 | #skills #team | articles/2026-03-27_009_Claude_Code_スキル活用術.md |
| 010 | Claude Codeですべての日常業務を爆速化しよう！ | ja | 読了 | #workflow #automation | articles/2026-03-27_010_Claude_Code_日常業務を爆速化.md |
| 011 | Claude Codeを使った業務自動化の実践 | ja | 読了 | #automation #workflow | articles/2026-03-27_011_Claude_Code_業務自動化の実践.md |
| 012 | バイブコーディングチュートリアル：Claude Code でカンバンアプリケーション | ja | 読了 | #tutorial #claude-md | articles/2026-03-27_012_バイブコーディングチュートリアル.md |
| 013 | 効果的なCLAUDE.mdの書き方 | ja | 読了 | #claude-md #best-practices | articles/2026-03-27_013_効果的なCLAUDE_md書き方.md |
| 014 | 【2026年版】Claude Codeのアップデート・最新情報まとめ | ja | 読了 | #update | articles/2026-03-27_014_Claude_Code_アップデート最新情報2026.md |
| 015 | Claude Code 最新アップデートまとめ（2026年2月時点） | ja | 読了 | #update | articles/2026-03-27_015_Claude_Code_アップデート2026年2月.md |
| 016 | おすすめ Claude Code 設定・運用まとめ | ja | 読了 | #best-practices #team | articles/2026-03-27_016_Claude_Code_設定運用まとめ_Wantedly.md |
| 017 | Claude CodeのAgent Skillsとは？使い方・設計・活用パターン | ja | 読了 | #skills | articles/2026-03-27_017_Claude_Code_Agent_Skills解説.md |
| 018 | Claude Code を使いこなすために意識している 5つのこと | ja | 読了 | #workflow #best-practices | articles/2026-03-27_018_Claude_Code_を使いこなすための5つのこと.md |
| 019 | 【2026年最新】Claude Codeで非エンジニアが業務を自動化する方法10選 | ja | 読了 | #automation #tutorial | articles/2026-03-27_019_Claude_Code_非エンジニア業務自動化.md |
| 020 | Claude Code and Cowork Can Now Use Your Computer (Engadget) | en | 読了 | #update #automation | articles/2026-03-27_049_Claude_Code_Computer_Use_Engadget.md |
| 021 | Claude Code Best Practices: Inside the Creator's 100-Line Workflow | en | 読了 | #claude-md #best-practices #workflow | articles/2026-03-27_050_Claude_Code_Creator_Workflow_Boris_Cherny.md |
| 022 | Extend Claude with Skills — Official Claude Code Docs | en | 読了 | #skills #official | articles/2026-03-27_051_Claude_Code_Skills_Official_Docs.md |
| 023 | How to Build a Production-Ready Claude Code Skill (TDS) | en | 読了 | #skills #tutorial | articles/2026-03-27_052_Production_Ready_Claude_Code_Skill_Tutorial.md |
| 024 | Getting Started with MCP: Automating Terraform Security with Claude Code | en | 読了 | #mcp #tutorial #automation | articles/2026-03-27_053_MCP_Terraform_Security_Tutorial.md |
| 025 | Claude Code MCP Server: Complete Setup Guide | en | 読了 | #mcp #automation | articles/2026-03-27_054_Claude_Code_as_MCP_Server.md |
| 026 | Hooks Reference — Official Claude Code Docs | en | 読了 | #hooks #official | articles/2026-03-27_055_Claude_Code_Hooks_Official_Reference.md |
| 027 | Claude Code Hooks Complete Guide (March 2026 Edition) | en | 読了 | #hooks #automation | articles/2026-03-27_056_Claude_Code_Hooks_21_Events_Guide.md |
| 028 | Claude Code Hooks: Complete Guide with 20+ Ready-to-Use Examples | en | 読了 | #hooks #tutorial | articles/2026-03-27_057_Claude_Code_Hooks_20_Examples.md |
| 029 | Best Practices for Claude Code — Official Claude Code Docs | en | 読了 | #best-practices #official #claude-md | articles/2026-03-27_058_Claude_Code_Best_Practices_Official.md |
| 030 | CLAUDE.md Best Practices — 10 Sections to Include (UX Planet) | en | 読了 | #claude-md #best-practices | articles/2026-03-27_059_CLAUDE_md_10_Sections_UX_Planet.md |
| 031 | Writing a Good CLAUDE.md (HumanLayer) | en | 読了 | #claude-md #best-practices | articles/2026-03-27_060_Writing_Good_CLAUDE_md_HumanLayer.md |
| 032 | How Should You Configure CLAUDE.md for Better AI Coding? (BSWEN) | en | 読了 | #claude-md #best-practices | articles/2026-03-27_061_CLAUDE_md_Best_Practices_BSWEN.md |
| 033 | How Anthropic Teams Use Claude Code (Official PDF) | en | 読了 | #team #official #workflow | articles/2026-03-27_062_Anthropic_Teams_Use_Claude_Code_PDF.md |
| 034 | Anthropic Says Claude Can Now Use Your Computer (CNBC) | en | 読了 | #update #automation | articles/2026-03-27_063_CNBC_Claude_Computer_Use.md |
| 035 | Everyone Should Be Using Claude Code More (Lenny's Newsletter) | en | 読了 | #workflow #tutorial | articles/2026-03-27_064_Lenny_Newsletter_Claude_Code_NonEngineers.md |
| 036 | Anthropic Hands Claude Code More Control, But Keeps It on a Leash (TechCrunch) | en | 読了 | #update #automation | articles/2026-03-27_065_TechCrunch_Auto_Mode_Safety_Classifier.md |
| 037 | 【2026/2/6最新アプデ】Claude Code新機能『エージェントチーム』が革新的だった | ja | 読了 | #update #team #automation | articles/2026-03-27_068_Claude_Code_Agent_Teams_Feature.md |
| 038 | Claude Code に Auto Mode が登場 ── 第三の道 | ja | 読了 | #update #automation | articles/2026-03-27_069_Claude_Code_Auto_Mode_ja.md |
| 039 | 【2026年3月最新】Claude Code v2.1.74〜v2.1.84 アップデートまとめ | ja | 読了 | #update | articles/2026-03-27_070_Claude_Code_v2174_v2184_March_2026.md |
| 040 | Claude Code のスキル機能完全ガイド（3層アーキテクチャ） | ja | 読了 | #skills | articles/2026-03-27_071_Claude_Code_Skills_3Layer_Architecture.md |
| 041 | Claude Codeの真価は運用設計にある（Skills/Hooks/MCPの使い分け） | ja | 読了 | #skills #hooks #mcp | articles/2026-03-27_072_Claude_Code_Skills_MCP_Design_Philosophy.md |
| 042 | CLAUDE.mdに本当は何を書くべきなのか（CureApp） | ja | 読了 | #claude-md #best-practices | articles/2026-03-27_073_CLAUDE_md_What_NOT_to_Write_CureApp.md |
| 043 | 【保存版】claude.mdに本当に書くべきこと ― 良い例・悪い例で徹底解説 | ja | 読了 | #claude-md #best-practices | articles/2026-03-27_074_CLAUDE_md_Good_Bad_Examples_200lines.md |
| 044 | Anthropicの10部門が実践するClaude Code活用術 | ja | 読了 | #team #official | articles/2026-03-27_075_Anthropic_10_Departments_Use_Cases.md |
| 045 | 月間400件以上のプルリクエストを生産したClaude Code活用事例 | ja | 読了 | #automation #workflow | articles/2026-03-27_076_Claude_Code_400_PRs_Per_Month.md |
| 046 | Claude Code による技術的特異点を見届けろ（mizchi） | ja | 読了 | #workflow | articles/2026-03-27_077_Claude_Code_Singularity_Essay.md |
| 047 | 地味だけど毎日使うAI自動化を11個作った話（非エンジニアCPO） | ja | 読了 | #automation | articles/2026-03-27_078_CPO_11_AI_Automation_Daily_Jobs.md |
| 048 | Claudeの全てのCHANGELOGを追ってきて | ja | 読了 | #update | articles/2026-03-27_079_All_Claude_Code_CHANGELOG.md |
| 049 | 【衝撃】Claude Code 2.1.0が神アプデすぎる｜1096コミットで16の革命的新機能 | ja | 読了 | #update | articles/2026-03-27_080_Claude_Code_v210_1096_Commits.md |
| 050 | 楽天テック：Claude Codeの更新情報を作業中に流し読みする仕組み | ja | 読了 | #hooks #automation | articles/2026-03-27_081_Rakuten_Claude_Code_Spinner_Hooks.md |
| 051 | Claude Codeで開発ワークフローを自動化：Hooks・Commands・Skillsの実践 | ja | 読了 | #hooks #skills #automation | articles/2026-03-27_082_Claude_Code_Full_Workflow_Hooks_Skills.md |
| 052 | ClaudeCodeのサブエージェントでテスト修正を自動化してみた | ja | 読了 | #automation #hooks | articles/2026-03-27_083_Claude_Code_Subagent_Auto_Test_Fix.md |
| 053 | Claude Code Action はじめの一歩：GitHubで使うAI自動化の革命 | ja | 読了 | #automation | articles/2026-03-27_084_Claude_Code_Action_GitHub_Integration.md |
| 054 | Claude Code by Anthropic – Release Notes (Releasebot) | en | 読了 | #update | articles/2026-03-28_113_Claude_Code_Release_Notes_Releasebot.md |
| 055 | Claude Code Changelog: Complete Version History (ClaudeFast) | en | 読了 | #update | articles/2026-03-28_114_Claude_Code_Changelog_ClaudeFast.md |
| 056 | Claude Code Changelog: Complete Update History 2026 (Get AI Perks) | en | 読了 | #update | articles/2026-03-28_115_Claude_Code_Update_History_GetAIPerks.md |
| 057 | How I Use Claude Code (+ My Best Tips) (Builder.io) | en | 読了 | #workflow #tutorial | articles/2026-03-28_116_How_I_Use_Claude_Code_Builder_io.md |
| 058 | GitHub – ykdojo/claude-code-tips (45 tips) | en | 読了 | #tutorial #best-practices | articles/2026-03-28_117_Claude_Code_Tips_GitHub_ykdojo.md |
| 059 | My Claude Code Setup & Workflow (psantanna.com) | en | 読了 | #workflow #tutorial | articles/2026-03-28_118_My_Claude_Code_Setup_psantanna.md |
| 060 | Every Claude Code Update From March 2026, Explained (Builder.io) | en | 読了 | #update | articles/2026-03-28_132_Claude_Code_March2026_Updates_Builder_io.md |
| 061 | Claude Code Internals Part 10: MCP Integration (Medium / Kotrotsos) | en | 読了 | #mcp | articles/2026-03-28_133_Claude_Code_Internals_Part10_MCP.md |
| 062 | Configuring MCP Tools in Claude Code — The Better Way (Scott Spence) | en | 読了 | #mcp | articles/2026-03-28_134_Configuring_MCP_Tools_Claude_Code_Scott_Spence.md |
| 063 | Claude Code + FastMCP Integration (FastMCP Official) | en | 読了 | #mcp | articles/2026-03-28_135_Claude_Code_FastMCP_Integration.md |
| 064 | Claude Code Hooks Tutorial: 5 Production Hooks From Scratch (Blake Crosley) | en | 読了 | #hooks | articles/2026-03-28_136_Claude_Code_Hooks_5_Production_Blake_Crosley.md |
| 065 | Claude Code Hooks: A Practical Guide to Workflow Automation (DataCamp) | en | 読了 | #hooks | articles/2026-03-28_137_Claude_Code_Hooks_DataCamp_Tutorial.md |
| 066 | claude-code-hooks-mastery (GitHub / disler) | en | 読了 | #hooks | articles/2026-03-28_138_claude_code_hooks_mastery_GitHub_disler.md |
| 067 | How to Write a Good CLAUDE.md File (Builder.io) | en | 読了 | #claude-md #best-practices | articles/2026-03-28_139_How_to_Write_Good_CLAUDE_md_Builder_io.md |
| 068 | CLAUDE.md Best Practices — From Basic to Adaptive (DEV Community) | en | 読了 | #claude-md #best-practices | articles/2026-03-28_140_CLAUDE_md_Best_Practices_Basic_Adaptive_DEV.md |
| 069 | How to Make Claude Code Skills Activate Reliably (Scott Spence) | en | 読了 | #skills | articles/2026-03-28_141_Claude_Code_Skills_Activate_Reliably_Scott_Spence.md |
| 070 | How We Use Claude Code Skills to Run 1,000+ ML Experiments a Day (Sionic AI / HuggingFace) | en | 読了 | #skills #automation | articles/2026-03-28_142_Claude_Code_Skills_1000_ML_Experiments_Sionic_HuggingFace.md |
| 071 | claude-code-spec-workflow (GitHub / Pimzino) | en | 読了 | #workflow #automation | articles/2026-03-28_143_claude_code_spec_workflow_GitHub_Pimzino.md |
| 072 | 前提知識ゼロでもAIで乗り切った！大規模プロジェクトでのClaude Code活用術 (TVer Tech Blog) | ja | 読了 | #workflow | articles/2026-03-28_144_TVer_Tech_Blog_Claude_Code_Large_Project.md |
| 073 | 【2026年版】Claude Codeのアップデート・最新情報まとめ (AI総合研究所) | ja | 読了 | #update | articles/2026-03-28_145_AI_Souken_Claude_Code_Updates_2026.md |
| 074 | Claude Codeスキル設定を使いこなす (note / ひで) | ja | 読了 | #skills | articles/2026-03-28_146_Claude_Code_Skills_Settings_Note_Tothinks.md |
| 075 | Claude Codeの機能が足りなかったらSkillを作ってもらおう (Classmethod DevelopersIO) | ja | 読了 | #skills | articles/2026-03-28_147_Classmethod_Claude_Code_Create_Skills_Itself.md |
| 076 | 効果的なCLAUDE.mdの書き方 (Zenn / farstep) | ja | 読了 | #claude-md #best-practices | articles/2026-03-28_148_Zenn_Effective_CLAUDE_md_Farstep.md |
| 077 | CLAUDE.mdやAGENTS.mdのベストプラクティスな書き方 (izanami.dev) | ja | 読了 | #claude-md #best-practices | articles/2026-03-28_149_Izanami_CLAUDE_md_AGENTS_md_Best_Practices.md |
| 078 | SKILL.mdの書き方完全ガイド — 87%削減の実践 (playpark.co.jp) | ja | 読了 | #skills #best-practices | articles/2026-03-28_150_Playpark_SKILL_md_Complete_Guide.md |
| 079 | 【2026年最新】Claude Codeでできること20選 (Uravation) | ja | 読了 | #workflow | articles/2026-03-28_151_Uravation_Claude_Code_20_Features.md |
| 080 | The 2026 MCP Roadmap (Official MCP Blog) | en | 読了 | #mcp | articles/2026-03-28_152_MCP_2026_Roadmap_Official.md |
| 081 | MCP's Biggest Growing Pains for Production Use (The New Stack) | en | 読了 | #mcp | articles/2026-03-28_153_MCP_Production_Growing_Pains_NewStack.md |
| 082 | Thirteen New MCP Servers from Cloudflare (Cloudflare Blog) | en | 読了 | #mcp | articles/2026-03-28_154_Cloudflare_13_MCP_Servers.md |
| 083 | エンジニアが入れるべきMCPサーバー厳選まとめ (Zenn / imohuke) | ja | 読了 | #mcp | articles/2026-03-28_155_MCP_Servers_Curated_Zenn_2026.md |
| 084 | Claude Agent SDK Overview (Anthropic Official Docs) | en | 読了 | #sdk | articles/2026-03-28_156_Claude_Agent_SDK_Overview_Official.md |
| 085 | Getting Started with the Claude Agent SDK (KDnuggets) | en | 読了 | #sdk | articles/2026-03-28_157_Claude_Agent_SDK_KDnuggets_Getting_Started.md |
| 086 | Claude Agent SDK Tutorial — Session Resume & Remote Workspace (DataCamp) | en | 読了 | #sdk | articles/2026-03-28_158_Claude_Agent_SDK_Tutorial_DataCamp.md |
| 087 | Anthropic Deprecation Updates — Opus 3 (Jan) & Haiku 3 (Apr 19) (Anthropic Official) | en | 読了 | #update | articles/2026-03-28_159_Anthropic_Deprecation_Opus3_Haiku3.md |
| 088 | Claude Code SDKとは？CI/CDへの組み込み方 (株式会社一創) | ja | 読了 | #sdk | articles/2026-03-28_160_Claude_Code_SDK_Issoh_Japanese.md |
| 089 | Claude Code SDK活用：CI連携・SaaS UI・サブエージェント委譲 (AGIラボ) | ja | 読了 | #sdk | articles/2026-03-28_161_Claude_Code_SDK_AGILab_Note.md |
| 090 | Every Claude Code Update From March 2026, Explained | en | 未読 | #update #web-signal | articles/2026-03-29_179_claude_code_march_2026_updates.md |
| 091 | 10 Claude Code Tips You Didn't Know | en | 未読 | #best-practices #web-signal | articles/2026-03-29_180_claude_code_tips_trigger_dev.md |
| 092 | Claude Code 追加機能タイムライン（2025/07〜2026/03） | ja | 未読 | #web-signal | articles/2026-03-29_181_claude_code_2026_features_timeline.md |
| 093 | Claude Code CLAUDE.md運用のベストプラクティス：失敗しないための7つの原則 | ja | 未読 | #best-practices #claude-md #web-signal | articles/2026-03-29_182_claude_code_best_practices_zenn.md |
| 094 | Claude Code 全社導入までの意思決定と歴史 | ja | 未読 | #web-signal | articles/2026-03-29_183_claude_code_company_wide_adoption.md |
| 095 | Claude Code Skills完全ガイド｜カスタムスキルの作り方と活用法【2026年版】 | ja | 未読 | #skills #web-signal | articles/2026-03-29_184_claude_code_skills_complete_guide.md |
| 096 | CLAUDE.mdの正しい書き方：AIエージェントを思い通りに動かす設定ファイル完全解説 | ja | 未読 | #claude-md #web-signal | articles/2026-03-29_185_claude_md_writing_guide.md |
| 097 | 【決定版】Claude Code新機能まとめ！開発を一変させる9つの神アプデ完全解説 | ja | 未読 | #web-signal | articles/2026-03-29_186_claude_code_new_features_note.md |
| 098 | CLAUDE.mdベストプラクティスを調べてみた | ja | 未読 | #best-practices #claude-md #web-signal | articles/2026-03-29_187_claude_md_best_practices_qiita.md |
| 099 | Claude Code入門 #2: CLAUDE.mdの書き方と育て方 | ja | 未読 | #claude-md #web-signal | articles/2026-03-29_188_claude_code_claude_md_intro_qiita.md |
| 100 | Claude Agent SDK for Python | en | 未読 | #sdk #web-signal | articles/2026-03-29_189_claude_agent_sdk_python_github.md |
| 101 | The Complete Guide to Building Agents with the Claude Agent  | en | 未読 | #sdk #tutorial #web-signal | articles/2026-03-29_190_claude_agent_sdk_guide.md |
| 102 | Complete Guide to MCP Servers in 2026: What They Are, How Th | en | 未読 | #mcp #tutorial #web-signal | articles/2026-03-29_191_mcp_servers_2026_complete_guide.md |
| 103 | MCP活用事例：企業に広がる業務適用パターンと導入効果 | ja | 未読 | #mcp #web-signal | articles/2026-03-29_192_mcp_use_cases_enterprise.md |
| 104 | MCPは死んでない？ MCPの2026年ロードマップ公開「AIツール接続」から「AI自律連携インフラ」へ | ja | 未読 | #mcp #web-signal | articles/2026-03-29_193_mcp_2026_roadmap_atmarkit.md |
| 105 | The Complete Guide to Model Context Protocol (MCP): Building | en | 未読 | #mcp #tutorial #web-signal | articles/2026-03-29_194_mcp_complete_guide_dev_to.md |
| 106 | 10 Must-Have Skills for Claude (and Any Coding Agent) in 202 | en | 未読 | #skills #web-signal | articles/2026-03-29_205_claude_code_10_must_have_skills.md |
| 107 | MCP Servers: The New Shadow IT for AI in 2026 | en | 未読 | #mcp #security #web-signal | articles/2026-03-29_206_mcp_shadow_it_security.md |
| 108 | Azure MCP Server Now Built-In with Visual Studio 2026: A New | en | 未読 | #mcp #microsoft #web-signal | articles/2026-03-29_207_azure_mcp_visual_studio_2026.md |
| 109 | 製造業におけるMCP活用事例5選：品質管理から設計開発まで広がるリアルタイム最適化の全貌 | ja | 未読 | #mcp #web-signal | articles/2026-03-29_208_manufacturing_mcp_use_cases.md |
| 110 | Claude API Pricing 2026: Full Anthropic Cost Breakdown | en | 未読 | #api #web-signal | articles/2026-03-29_210_anthropic_api_claude_latest_2026.md |
| 111 | Getting started with Anthropic Claude Agent SDK — Python | en | 未読 | #sdk #tutorial #web-signal | articles/2026-03-29_212_claude_agent_sdk_getting_started.md |
| 112 | How to Build an MCP Server with Python, Docker, and Claude C | en | 未読 | #mcp #web-signal | articles/2026-03-29_213_build_mcp_server_python_docker.md |
| 113 | Code execution with MCP: building more efficient AI agents | en | 未読 | #mcp #web-signal | articles/2026-03-29_215_anthropic_mcp_code_execution.md |
| 114 | Claude Code /loop コマンド：セッションレベルのスケジューラ完全ガイド | en | 未読 | #workflow #automation #web-signal | articles/2026-03-30_216_claude_code_loop_command_recurring_tasks.md |
| 115 | Claude Code /voice：スペースバーPTT方式の音声入力モード完全ガイド | en | 未読 | #update #workflow #web-signal | articles/2026-03-30_217_claude_code_voice_mode_push_to_talk_2026.md |
| 116 | Claude Code Remote Control：スマートフォンからローカルセッションを操作 | en | 未読 | #workflow #automation #web-signal | articles/2026-03-30_218_claude_code_remote_control_mobile_guide.md |
| 117 | Claude Code 2026年3月全12新機能：/loop・Computer Use・Remote Control | en | 未読 | #update #web-signal | articles/2026-03-30_219_claude_code_march_2026_12_features_loop_computer_use.md |
| 118 | Claude Agent SDK：カスタムAIエージェント構築ガイド（2026年3月リリース） | en | 未読 | #sdk #tutorial #web-signal | articles/2026-03-30_220_claude_agent_sdk_custom_agents_2026.md |
| 119 | Claude Opus 4.6：SWE-Bench 80.8%・1Mトークン・アジェンティックコーディング | en | 未読 | #api #update #web-signal | articles/2026-03-30_221_claude_opus_46_benchmark_1m_context_coding.md |
| 120 | Claude Code完全初心者ガイド：スキル・エージェント・フック・MCP・Cowork | en | 未読 | #skills #hooks #mcp #tutorial #web-signal | articles/2026-03-30_224_claude_code_beginners_guide_skills_hooks_mcp_cowork.md |
| 121 | MCPサーバー全54種カテゴリ別ガイド：8,600以上のエコシステム解説 | ja | 未読 | #mcp #web-signal | articles/2026-03-30_225_mcp_server_54_categories_8600_servers_guide.md |
| 122 | Claude Codeスキル作り方チュートリアル：freeCodeCamp 実践ガイド | en | 未読 | #skills #tutorial #web-signal | articles/2026-03-30_227_build_claude_code_skill_freecodecamp_tutorial.md |
| 123 | claude-code-workflows：本番対応ワークフロー集・並列git worktree運用 | en | 未読 | #workflow #best-practices #web-signal | articles/2026-03-30_228_claude_code_workflows_github_parallel_worktree.md |
| 124 | Claude Code 生産性を高める10の実践ワークフロー 2026 | en | 未読 | #workflow #best-practices #web-signal | articles/2026-03-30_230_claude_code_10_productivity_workflows_2026.md |
| 125 | claude-code-ultimate-guide：30本番フック・24CVE脆弱性DB・完全リファレンス | en | 未読 | #hooks #best-practices #web-signal | articles/2026-03-30_231_claude_code_ultimate_guide_github_30_hooks_security.md |
| 126 | Claude Codeベストプラクティス7選：実プロジェクトから学ぶCLAUDE.md設計 | en | 未読 | #claude-md #best-practices #web-signal | articles/2026-03-30_232_claude_code_best_practices_7_real_projects_eesel.md |
| 127 | Claude Codeスキルエコシステム完全解説：設計・互換性・277K+インストール | en | 未読 | #skills #web-signal | articles/2026-03-30_233_claude_code_skills_ecosystem_design_corpwaters.md |
| 128 | AIエージェントフレームワーク使い分けガイド：LangChain vs Claude Agent SDK | ja | 未読 | #sdk #framework #web-signal | articles/2026-03-30_235_ai_agent_frameworks_langchain_claude_sdk_comparison_ja.md |
| 129 | Claude Code プロンプト集30選：100社研修実績のコピペ可能テンプレート | ja | 未読 | #workflow #best-practices #web-signal | articles/2026-03-30_236_claude_code_prompts_30_templates_copypaste.md |
| 130 | Claude Code Auto Mode — Official Anthropic Announcement | en | 未読 | #update #automation #official #web-signal | articles/2026-04-01_239_claude_code_auto_mode_official_anthropic.md |
| 131 | Claude Code Auto Mode, Desktop Control & Channels: Technical Analysis | en | 未読 | #update #automation #mcp #web-signal | articles/2026-04-01_240_claude_code_auto_mode_channels_desktop_control_analysis.md |
| 132 | Claude Code March 2026: Multi-Agent Review, Auto Mode & Channels | en | 未読 | #update #workflow #web-signal | articles/2026-04-01_241_claude_code_march_2026_automode_channels_geeky_gadgets.md |
| 133 | MCP 2026 Roadmap: Production Growing Pains Will Soon Be Solved | en | 未読 | #mcp #web-signal | articles/2026-04-01_242_mcp_2026_roadmap_production_gaps_newstack.md |
| 134 | Claude Agent SDK 完全ガイド【2026年最新】Python・TypeScriptでAIエージェント構築 | ja | 未読 | #sdk #tutorial #mcp #web-signal | articles/2026-04-01_243_claude_agent_sdk_complete_guide_2026_aqua_ja.md |
| 135 | Claude Code × MCP 実践活用ガイド【2026年最新】導入・設定・自作・セキュリティ | ja | 未読 | #mcp #hooks #web-signal | articles/2026-04-01_244_claude_code_mcp_practical_guide_2026_aqua_ja.md |
| 136 | Claude Code更新 Channels・使用量2倍・サブエージェント強化【2026/3/15〜21】 | ja | 未読 | #update #automation #web-signal | articles/2026-04-01_246_claude_code_channels_usage_x2_serverworks_ja.md |
| 137 | [2026年版] Claude Code を知る。活用する。— DevelopersIO | ja | 未読 | #workflow #best-practices #update #web-signal | articles/2026-04-01_249_claude_code_2026_complete_guide_devio_ja.md |
| 138 | Claude Code Auto Mode and Full Cowork Computer Use — The Zvi | en | 未読 | #update #automation #web-signal | articles/2026-04-01_250_claude_code_auto_mode_thezvi_deep_analysis.md |
| 139 | 【2026年3月版】Claude Codeがどれだけ進化したか（3/3〜28 13バージョン） | ja | 未読 | #update #workflow #web-signal | articles/2026-04-01_252_claude_code_march_2026_evolution_13versions_kazu_ja.md |
| 140 | Claude Code New Features: Auto Mode, Channels, Voice, /loop & 60+ Prompts | en | 未読 | #update #workflow #automation #web-signal | articles/2026-04-01_253_claude_code_auto_mode_60prompts_complete_setup.md |
| 141 | Claude Code Q1 2026 Update Roundup: Every Feature That Actually Matters (MindStudio) | en | 未読 | #update #web-signal | articles/2026-04-07_179_Claude_Code_Q1_2026_Update_Roundup_MindStudio.md |
| 142 | Claude Code April 2026 Update: /powerup, MCP 500K, Session Stability | en | 未読 | #update #hooks #mcp #web-signal | articles/2026-04-07_180_Claude_Code_April_2026_Update_powerup_MCP500K.md |
| 143 | Leveraging Claude Code: A Senior Engineer's Guide to Maximizing AI in Development | en | 未読 | #workflow #best-practices #web-signal | articles/2026-04-07_181_Claude_Code_Senior_Engineers_Guide_FranksWorld.md |
| 144 | MCP vs Skills vs Hooks in Claude Code: Which Extension Do You Need? (DEV) | en | 未読 | #mcp #skills #hooks #web-signal | articles/2026-04-07_182_MCP_vs_Skills_vs_Hooks_Which_Extension_DEV.md |
| 145 | Claude Code v2.1.90 Release Notes: /powerup Interactive Tutorial Launches (ClaudeWorld) | en | 未読 | #update #web-signal | articles/2026-04-07_183_Claude_Code_v2190_Release_Notes_ClaudeWorld.md |
| 146 | I mastered the Claude Code workflow — Workflow that changed everything (Medium) | en | 未読 | #workflow #web-signal | articles/2026-04-07_184_Mastered_Claude_Code_Workflow_Medium.md |
| 147 | Claude Code 全社導入までの意思決定と歴史 (Gemcook / Zenn) | ja | 未読 | #workflow #team #web-signal | articles/2026-04-07_185_Claude_Code_Company_Wide_Gemcook_Zenn.md |
| 148 | Claude Codeを使い倒すための69のTipsとワークフロー10選 (note) | ja | 未読 | #workflow #skills #hooks #web-signal | articles/2026-04-07_186_Claude_Code_69_Tips_Workflows_Note.md |
| 149 | Claude Code Skills完全ガイド｜カスタムスキルの作り方と活用法【2026年版】 (Nexa) | ja | 未読 | #skills #best-practices #web-signal | articles/2026-04-07_187_Claude_Code_Skills_Complete_Guide_Nexa.md |
| 150 | Claude Code Skillsの使い方と汎用テンプレート公開 (SIOS Tech Lab) | ja | 未読 | #skills #best-practices #web-signal | articles/2026-04-07_188_Claude_Code_Skills_Template_SIOS.md |
| 151 | Claude Code /powerup: 10 Built-In Lessons That Teach You Features You Are Already Missing (Medium) | en | 未読 | #update #tutorial #web-signal | articles/2026-04-07_189_Claude_Code_powerup_10_Lessons_Medium.md |
| 152 | How to Run Claude Code in Parallel (2026): 5 Methods, Step-by-Step (Morphllm) | en | 未読 | #workflow #automation #web-signal | articles/2026-04-07_190_Claude_Code_Parallel_Sessions_5_Methods_Morphllm.md |
| 153 | Building agents with the Claude Agent SDK（Anthropic公式ブログ） | en | 未読 | #sdk #official #web-signal | articles/2026-04-07_191_Building_Agents_Claude_Agent_SDK_Official_Blog.md |
| 154 | The Complete Guide to Building Agents with the Claude Agent SDK (Nader Substack) | en | 未読 | #sdk #web-signal | articles/2026-04-07_192_Claude_Agent_SDK_Complete_Guide_Nader_Substack.md |
| 155 | 【2026年4月最新】AWSが公開するオープンソースMCPサーバー カテゴリ別早見表 | ja | 未読 | #mcp #web-signal | articles/2026-04-07_193_AWS_MCP_Server_54_List_April_2026.md |
| 156 | AI Agent Frameworks in 2026: 8 SDKs, ACP, and the Trade-offs Nobody Talks About (Morphllm) | en | 未読 | #sdk #mcp #web-signal | articles/2026-04-07_194_AI_Agent_Frameworks_8_SDKs_ACP_Morphllm.md |
## 発見パターン（記事横断の傾向）

蔵書を横断して繰り返し出現するテーマ。出現回数が多いほど普遍的な知見。

| パターン | 出現記事 | 知見 | 反映状況 |
|---------|---------|------|---------|
| **禁止パターンの明示化** | #5, #6, #13, #26 | AIは「やるな」の暗黙理解が苦手。明示的リスト化が最も効果的 | base.md + browser-tool.md に反映済 |
| **Progressive Disclosure** | #5, #11, #12, #32, #35, #42 | CLAUDE.mdに全部書かず、詳細はファイル参照で渡す。コンテキスト節約。Skill Graphsは究極形 | base.md + CLAUDE.md構成に反映済 |
| **二重ロック（仕組み+理由）** | #3, #4, #13, #26 | settings.json（物理的制限）+ CLAUDE.md（理由の理解）の両方が必要 | agent-governance.md に反映済 |
| **段階的アプローチ** | #9, #13, 非エンジニア調査 | 型1→型2→型3。調査→計画→実行→確認。いきなり複雑なことをしない | base.md 4ステップWF + scaffolder型分類に反映済 |
| **Gotchasセクション** | #1, #12 | スキルで最も価値が高いのは「よくあるハマりポイント」。運用しながら育てる | 全6スキルに追加済 |
| **Self-improving ループ** | #1, #14, #28, #37 | 実行→失敗記録→改善→再評価のサイクル。Autoresearchで56%→92%の定量改善実績 | skill-design-patterns.md にAutoresearchパターン追加済 |
| **descriptionはトリガー条件** | #12, #38, #40 | スキルのdescriptionは人間向け説明ではなく、モデルの発動判定用。キーワード5つ以上が目安 | catalog.yaml description書き直し済 |
| **allowリスト充実 = 放置に近づく** | #3, #13, #15, #16, #17, #18 | settings.jsonのallowを充実させれば確認頻度が下がる。dangerouslySkipはコンテナ限定の最終手段 | settings.jsonテンプレート3層化 + agent-governance.md自律実行モード |
| **タスク定義の質が全て** | #15, #17 | 放置運用では「何をするか」の明確さが成否を決める。task-queue.yaml + 完了条件の事前定義 | agent-governance.md 3ファイル構成 |
| **検証ループの必須化** | #28, #32, #37 | 「no verifier = no engineering agent」。成果物の検証手段を事前定義しないタスクは信頼できない | base.md 4ステップWF に acceptance criteria 追加済 |
| **コンテキストは有限資源** | #32, #33, #37, #42 | MCP定義で12.5%消費。CLAUDE.md肥大化警告。必要な部分だけ読み込む設計が必須 | base.md CLAUDE.md運用ガイドライン追加済 |
| **スキル設計パターンは収束中** | #11, #12, #27, #32, #40 | エコシステム全体で5パターン+9カテゴリ+3タイプに収束。skill-design-patterns.mdの信頼性は高い | skill-design-patterns.md 判断ツリー追加済 |

| 15 | 24時間動かす3つの設定ファイル | `articles/24時間動かす3つの設定ファイル.txt` | ワークフロー, ガバナンス | task-queue.yaml + 判断ルール表 + mission.md。idle停止防止と状態復元 | agent-governance.md 自律実行モード | 反映済 |
| 16 | 寝ながら開発（GMO） | `articles/寝ながら開発GMO.txt` | ワークフロー | caffeinate + Linear MCP + AppleScript自動入力。力技だが実用的 | agent-governance.md 注意事項 | 反映済 |
| 17 | 放置しても止まらない長期駆動（108時間） | `articles/放置しても止まらない長期駆動.txt` | ワークフロー, agent設計 | task-dispatch→execute→checkerのループ。「タスクの質が全て」 | agent-governance.md 自律実行モード | 反映済 |
| 18 | dangerously-skip-permissions完全ガイド | `articles/dangerously-skip-permissions完全ガイド.txt` | ガバナンス | コンテナ必須。AllowedToolsで制限。小スコープ→スケール | agent-governance.md Permission Mode全段階 | 反映済 |

| 19 | 非エンジニアが1ヶ月でできたこと | `articles/非エンジニア1ヶ月の成果.txt` | 非エンジニア | Flutterアプリ公開+OSS PR11本+Kaggle4本。「動くものを作りながら学ぶ」 | 参考情報（型3成功事例） | 読了 |
| 20 | ひとりマーケチーム | `articles/ひとりマーケチーム.txt` | 非エンジニア, ワークフロー | Vibe Marketing。1時間で市場調査→LP→広告戦略一式 | 検討中（マーケ型テンプレート候補） | 読了 |
| 21 | 諦めてきた自動化を実現する3つのアプローチ | `articles/諦めてきた自動化.txt` | 非エンジニア, ワークフロー | メルマガ翻訳・自動返信・日程調整。GAS/ノーコードで挫折→CC で実現 | 検討中（型2スキルテンプレート候補） | 読了 |

| 22 | 非エンジニアが黒い画面に飛び込んで2ヶ月 | `articles/黒い画面に飛び込んで2ヶ月.txt` | 非エンジニア | 「言語化が最強スキル」「ver.1は雑でいい」「小さな部署を1人で回す」の3つの成長 | 検討中 | 読了 |
| 23 | Claude Codeはエンジニア以外も全員使うべき | `articles/エンジニア以外も全員使うべき.txt` | 非エンジニア | 勝負の決め手が技術力→「明確な思考・構造化・AI協働設計」に変化 | 検討中 | 読了 |

| 24 | 並列Claudeで10万行Cコンパイラ構築（Anthropic公式） | `articles/並列CコンパイラAnthropic公式.txt` | agent設計, アーキテクチャ | 16並列Claude、Git lockで排他制御、テストの質が全て、$20K/2週間 | 検討中（Agent Teams並列パターンの参考） | 読了 |

| 25 | 構想メモ: もう一人の自分エージェント | `articles/構想メモ_もう一人の自分エージェント.txt` | agent設計 | 会話履歴→判断パターン・価値観抽出→エージェント定義。#14 Hook + 久保さん構想の統合 | 未着手（Hook実装後に開始） | 構想 |
| 26 | 非エンジニア向け2つのファイル設定（tetumemo） | `articles/非エンジニア向け2つのファイル設定（tetumemo）.txt` | 非エンジニア, ガバナンス | settings.local.json（鍵）+ CLAUDE.md（ルール表）の二重ロック。一行ずつ解説付き | 検討中 | 読了 |
| 27 | 5つのAgent Skillデザインパターン（GoogleCloudTech） | `articles/5つのAgent Skillデザインパターン（GoogleCloudTech）.txt` | スキル | Tool Wrapper/Generator/Reviewer/Inversion/Pipelineの5パターン。合成可能 | skill-design-patterns.md 判断ツリー | 反映済 |
| 28 | Autoresearchでスキル自動改善（Ole Lehmann） | `articles/Autoresearchでスキル自動改善（Ole Lehmann）.txt` | スキル | Karpathy発autoresearchをスキルに適用。チェックリスト評価→小変更→keep/revertループで56%→92% | skill-design-patterns.md Autoresearchパターン | 反映済 |
| 29 | Claude Cowork完全入門（Corey Ganim） | `articles/Claude Cowork完全入門（Corey Ganim）.txt` | ワークフロー, 非エンジニア | Cowork=自律型デスクトップ社員。コンテキストファイル設計が鍵。プロンプト工学→システム工学への転換 | 検討中 | 読了 |
| 30 | CLAUDE.mdをちゃんと読ませるimportantタグ（oikon48） | `articles/CLAUDE.mdをちゃんと読ませるimportantタグ（oikon48）.txt` | CLAUDE.md | `<important if="condition">`タグでCLAUDE.mdの重要箇所を強調。HumanLayer独自手法、公式裏付けなし。タグ自体に魔法はなく、ルール整理のメタ効果。新モデルでは過剰反応リスクも | 見送り（検証済み） | 読了 |
| 31 | Paperclip AIエージェント会社運営ツール（Nick Spisak） | `articles/Paperclip AIエージェント会社運営ツール（Nick Spisak）.txt` | agent設計 | 複数AIエージェントを組織図・予算・チケットで管理するOSSツール。Heartbeats機能でスケジュール実行 | 検討中 | 読了 |
| 32 | Claude Codeシステム設計問題（Tw93 claude-health） | `articles/Claude Codeシステム設計問題（Tw93 claude-health）.txt` | アーキテクチャ, CLAUDE.md | 6層フレームワーク。3段階進化（機能探索→生産性→自律運用）。`/health`で設定診断 | base.md CLAUDE.md運用ガイドライン + 検証ループ | 反映済 |
| 33 | Shorthand Guide to Everything Claude Code（affaanmustafa） | `articles/Shorthand Guide to Everything Claude Code（affaanmustafa）.txt` | アーキテクチャ, ワークフロー | Skills/Hooks/Subagents/MCPs/Plugins全体像。MCP 80ツール上限。コンテキスト窓は貴重資源 | 検討中 | 読了 |
| 34 | Claude Code Channels — Telegram/Discord連携（公式・Thariq） | `articles/Claude Code Channels Telegram Discord（公式・Thariq）.txt` | アーキテクチャ | Telegram/DiscordからClaude Codeセッションを操作可能。モバイルからの遠隔制御 | 検討中 | 読了 |
| 35 | Seeing like an Agent — ツール設計の教訓（公式・Thariq） | `articles/Seeing like an Agent ツール設計の教訓（公式・Thariq）.txt` | アーキテクチャ, スキル | AskUserQuestion誕生経緯。TodoWrite→Task進化。モデル能力向上に合わせてツールも再設計すべし | skill-design-patterns.md ツール定期見直し | 反映済 |
| 36 | Claude Code使用率ステータスライン表示（逆瀬川） | `articles/Claude Code使用率ステータスライン表示（逆瀬川）.txt` | ワークフロー | v2.1.80のrate_limitsフィールドで5h/7d使用量をステータスラインに表示する4パターン | 検討中 | 読了 |
| 37 | Longform Guide to Everything Claude Code（affaanmustafa） | `articles/Longform Guide to Everything Claude Code（affaanmustafa）.txt` | アーキテクチャ, ワークフロー | トークン経済学・メモリ永続化・検証ループ・並列化戦略。Haiku+Opus組合せでコスト最適化 | base.md コンテキスト管理 + agent-governance.md 反復取得 | 反映済 |
| 38 | コピペで使えるClaude スキル50選（Hoshino） | `articles/コピペで使えるClaude スキル50選（Hoshino）.txt` | スキル, 非エンジニア | 営業・ライティング・バックオフィス等50スキルテンプレ。descriptionの書き方で自動起動率9割決まる | 検討中 | 読了 |
| 39 | Browser Use CLI 2.0リリース | `articles/Browser Use CLI 2.0リリース.txt` | アーキテクチャ | Browser Use CLI 2.0: 2倍速・半額コスト・CDP直接接続。ブラウザ自動化CLIツール | 検討中 | 読了 |
| 40 | 非エンジニアのためのSkills完全入門（長谷川taichi_we） | `articles/非エンジニアのためのSkills完全入門（長谷川taichi_we）.txt` | スキル, 非エンジニア | SKILL.md=日本語の作業マニュアル。3タイプ分類。descriptionが発動判定の鍵。社員9割が非エンジニア | 検討中 | 読了 |
| 41 | frontend-slidesスキルでスライド作成（SuguruKun_ai） | `articles/frontend-slidesスキルでスライド作成（SuguruKun_ai）.txt` | スキル | frontend-slidesスキルでスライド自動生成。スキルの作り込みがアウトプット品質を左右する時代 | 検討中 | 読了 |
| 42 | Skill Graphsでスキルをネットワーク化（arscontexta） | `articles/Skill Graphsでスキルをネットワーク化（arscontexta）.txt` | スキル, アーキテクチャ | wikilink+YAML frontmatterで250+ファイルのスキルグラフ構築。Progressive Disclosureの究極形 | 検討中 | 読了 |

| 43 | frontend-slides スキル導入 | — | スキル | HTMLスライド生成スキル。10.7kスター。依存ゼロ。12テーマ。ブラウザ表示向き | `~/.claude/skills/frontend-slides/` + catalog.yaml | 反映済 |
| 44 | pptx-from-layouts スキル導入 | — | スキル | テンプレート準拠pptx生成スキル。95/100点。提案書・研修資料向き | `~/.claude/skills/pptx-from-layouts/` + catalog.yaml | 反映済 |

| 45 | バズってるX記事を全自動で収集する方法 | `articles/バズってるX記事を全自動で収集する方法（beku_AI）.txt` | ワークフロー | SocialData API + `url:x.com/i/article` で545件25円。Claude Codeスキル化で全自動リサーチ | 検討中（蔵書一括収集の手段として活用可能性あり） | 読了 |
| 46 | イシューからはじめよ | `books/イシューからはじめよ.md` | 読書 | イシュー度×解の質=バリュー。解く前に見極める。仮説→ストーリーライン→メッセージの構造化 | — | 読了 |
| 47 | 解像度が高い人がすべてを手に入れる | `books/解像度が高い人がすべてを手に入れる.md` | 読書 | 解像度=思考のピクセル密度。具体化×抽象化×往復の3層構造。51問のクイズで「ってことは？」の瞬発力を鍛える | — | 読了 |
| 48 | 最強リーダーの「話す力」 | `books/最強リーダーの話す力.md` | 読書 | セルフ・パペットで「素の自分」と「リーダーの自分」を切り分け。レトリカル・クエスチョン+沈黙で問いを投げる型。語彙精度は「定義する」「能動態で言い切る」 | — | 読了 |
| 49 | 自分の小さな「箱」から脱出する方法 | `books/自分の小さな箱から脱出する方法.md` | 読書 | 箱=自己欺瞞。相手を「人」でなく「物」として見る状態。テクニックの前提となるマインドセット。3冊のテクニック本が機能する土台 | — | 読了 |

| 50 | SessionStart Hook実装パターン調査（GitHub実例集） | `articles/SessionStart Hook実装パターン調査（GitHub実例集）.txt` | ワークフロー, アーキテクチャ | SessionStart/UserPromptSubmit Hookの実装パターン8種。Issue #10373バグ。krzemienski/cc-setupが最高峰 | session-start.py実装 | 反映済 |

## 統計

- 蔵書数: 48（記事44 + 書籍4）
- 反映済: 16
- 読了（未反映）: 28
- 未読: 1
- 構想: 1
- 書籍: 4
